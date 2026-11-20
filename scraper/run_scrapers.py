"""
Ingestion pipeline: scrape DarGlobal + Wasalt live, normalise, and write the
knowledge base the chatbot searches.

    python -m scraper.run_scrapers              # live scrape of both sites
    python -m scraper.run_scrapers --cached     # rebuild from the last snapshot only
    python -m scraper.run_scrapers --only darglobal

If one site cannot be scraped (no browser installed, bot check not cleared,
network error), that site's last good snapshot in data/raw/ is reused and the
reason is recorded in data/scrape_meta.json, so the app never loses its data.
"""

import argparse
import json
import logging
import os
import sys
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from scraper.scrape_darglobal import scrape_darglobal_portfolio
from scraper.scrape_wasalt import scrape_wasalt_listings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("PipelineRunner")

RAW_DIR = os.path.join(parent_dir, "data", "raw")
PROCESSED_DIR = os.path.join(parent_dir, "data", "processed")
KB_PATH = os.path.join(parent_dir, "data", "knowledge_base.json")
META_PATH = os.path.join(parent_dir, "data", "scrape_meta.json")
LISTING_RETENTION_DAYS = int(os.getenv("LISTING_RETENTION_DAYS", "30"))  # keep a listing this long after last seen
MAX_WASALT_LISTINGS = int(os.getenv("MAX_WASALT_LISTINGS", "5000"))
_PIPELINE_LOCK = threading.Lock()


def _faq_text(faqs: List[Dict[str, str]]) -> str:
    return " ".join(f"Q: {f['q']} A: {f['a']}" for f in faqs or [])


def build_search_text(item: dict) -> str:
    """Consolidated text block for retrieval and for the LLM context."""
    parts = [
        f"Title: {item.get('title', '')}",
        f"Source: {item.get('source', '')}",
        f"Brand Partner: {item.get('brand_partner', 'N/A')}",
        f"Location: {item.get('city', '')}, {item.get('country', '')} ({item.get('district', '')})",
        f"Property Type: {item.get('property_type', '')}",
        f"Bedrooms / Units: {item.get('bedrooms', '')}",
        f"Area: {item.get('area', '')}",
        f"Price: {item.get('price_local', '')} {item.get('price_usd', '')}".strip(),
        f"Status: {item.get('status', '')}",
        f"Description: {item.get('description', '')}",
        f"Amenities: {', '.join(item.get('amenities', []))}",
        f"Investment / Market Insights: {item.get('investment_highlights', '')}",
        f"FAQ: {_faq_text(item.get('faqs'))}",
        f"Page text: {item.get('details', '')}",
        f"URL: {item.get('source_url', '')}",
    ]
    return "\n".join(p for p in parts if not p.endswith(": ") and not p.endswith(":"))


def _load_snapshot(name: str) -> List[Dict[str, Any]]:
    path = os.path.join(RAW_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Only real scraped records carry scraped_at; older hand-written seed data is ignored.
    return [r for r in data if r.get("scraped_at")]


def write_json_atomic(path: str, data: Any, indent: Optional[int] = 2) -> None:
    """Write to a temp file then rename, so a reader (the running chatbot) never sees half a file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp-{os.getpid()}-{threading.get_ident()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    os.replace(tmp, path)


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def merge_records(new: List[Dict[str, Any]], previous: List[Dict[str, Any]],
                  keep_unseen: Callable[[Dict[str, Any]], bool]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Incremental update: records in `new` replace their previous version (keeping first_seen),
    brand-new ids are added, and previous records missing from this scrape are kept if
    `keep_unseen(record)` says so (e.g. a Wasalt listing seen in the last 30 days).
    """
    prev = {r["id"]: r for r in previous}
    out, added, updated = [], 0, 0
    for r in new:
        old = prev.get(r["id"])
        r["first_seen"] = (old or {}).get("first_seen") or (old or {}).get("scraped_at") or r.get("scraped_at")
        r["last_seen"] = r.get("scraped_at")
        out.append(r)
        if old:
            updated += 1
        else:
            added += 1
    new_ids = {r["id"] for r in new}
    kept = 0
    for r in previous:
        if r["id"] not in new_ids and keep_unseen(r):
            r.setdefault("first_seen", r.get("scraped_at"))
            r.setdefault("last_seen", r.get("scraped_at"))
            out.append(r)
            kept += 1
    return out, {"added": added, "updated": updated, "kept_from_earlier": kept}


def _keep_unseen_darglobal(r: Dict[str, Any]) -> bool:
    # The project catalogue is authoritative: a project missing from it is gone.
    # Company pages are kept if one failed to load this time.
    return r.get("property_type") == "Company information"


def _keep_unseen_wasalt(r: Dict[str, Any]) -> bool:
    if r.get("property_type") == "Market guide":
        return True  # a city page that failed this run keeps its last guide
    seen = _parse_time(r.get("last_seen") or r.get("scraped_at"))
    return bool(seen and datetime.now(timezone.utc) - seen < timedelta(days=LISTING_RETENTION_DAYS))


def _run_source(name: str, live: bool, scrape: Callable[[], List[Dict[str, Any]]], snapshot: str,
                keep_unseen: Callable[[Dict[str, Any]], bool]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    previous = _load_snapshot(snapshot)  # read before the scraper overwrites the raw file
    if live:
        try:
            fresh = scrape()
            merged, stats = merge_records(fresh, previous, keep_unseen)
            if name == "Wasalt":  # cap growth: keep the most recently seen listings
                guides = [r for r in merged if r.get("property_type") == "Market guide"]
                listings = sorted((r for r in merged if r.get("property_type") != "Market guide"),
                                  key=lambda r: r.get("last_seen") or "", reverse=True)[:MAX_WASALT_LISTINGS]
                merged = guides + listings
            write_json_atomic(os.path.join(RAW_DIR, snapshot), merged)
            return merged, {"status": "live", "records": len(merged), **stats,
                            "scraped_at": fresh[0].get("scraped_at") if fresh else None}
        except Exception as exc:
            logger.warning("%s live scrape failed (%s); using last snapshot", name, exc)
            if previous:
                write_json_atomic(os.path.join(RAW_DIR, snapshot), previous)  # undo a partial overwrite
            error = f"{type(exc).__name__}: {exc}"[:300]
    else:
        error = "live scrape not requested"
    latest = max((r.get("last_seen") or r.get("scraped_at") or "" for r in previous), default=None)
    return previous, {"status": "snapshot" if previous else "empty", "records": len(previous),
                      "scraped_at": latest, "note": error}


def _normalise(item: Dict[str, Any], synced: str) -> Dict[str, Any]:
    is_dg = item.get("source") == "DarGlobal"
    norm = {
        "id": item["id"],
        "title": item["title"],
        "source": item["source"],
        "developer": item.get("developer", ""),
        "brand_partner": item.get("brand_partner", "N/A") or "N/A",
        "country": item.get("country", ""),
        "city": item.get("city", ""),
        "district": item.get("district", ""),
        "property_type": item.get("property_type", ""),
        "category": item.get("category", "Project" if is_dg else ""),
        "bedrooms": item.get("bedrooms", ""),
        "area": item.get("area", ""),
        "price_local": item.get("starting_price_local" if is_dg else "price_local", "") or "Price on request",
        "price_usd": item.get("starting_price_usd" if is_dg else "price_usd", ""),
        "status": item.get("status", ""),
        "description": item.get("description", ""),
        "amenities": item.get("amenities", []),
        "investment_highlights": item.get("investment_highlights" if is_dg else "market_insights", ""),
        "faqs": item.get("faqs", []),
        "details": item.get("page_text", "")[:3000],
        "source_url": item["source_url"],
        "scraped_at": item.get("scraped_at"),
        "first_seen": item.get("first_seen") or item.get("scraped_at"),
        "last_seen": item.get("last_seen") or item.get("scraped_at"),
        "last_synced": synced,
    }
    if norm["property_type"] in ("Company information", "Market guide"):
        norm["price_local"] = ""
    norm["search_text"] = build_search_text(norm)
    return norm


def run_pipeline(live: bool = True, only: str = "all") -> str:
    """Scrape (or reuse snapshots), merge with what we already had, and atomically publish the knowledge base."""
    with _PIPELINE_LOCK:  # one refresh at a time (background thread + Sync button)
        now = datetime.now(timezone.utc)
        built_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        synced = now.strftime("%Y-%m-%d %H:%M UTC")
        logger.info("==> Phase 1: DarGlobal (%s)", "live" if live and only in ("all", "darglobal") else "snapshot")
        dg_items, dg_meta = _run_source("DarGlobal", live and only in ("all", "darglobal"),
                                        lambda: scrape_darglobal_portfolio(output_dir=RAW_DIR),
                                        "darglobal_scraped.json", _keep_unseen_darglobal)
        logger.info("==> Phase 2: Wasalt (%s)", "live" if live and only in ("all", "wasalt") else "snapshot")
        ws_items, ws_meta = _run_source("Wasalt", live and only in ("all", "wasalt"),
                                        lambda: scrape_wasalt_listings(output_dir=RAW_DIR),
                                        "wasalt_scraped.json", _keep_unseen_wasalt)
        if not dg_items and not ws_items:
            raise RuntimeError("No data: live scraping failed and there is no snapshot in data/raw/")

        logger.info("==> Phase 3: normalising and publishing the knowledge base")
        corpus = [_normalise(i, synced) for i in dg_items + ws_items]
        write_json_atomic(os.path.join(PROCESSED_DIR, "darglobal_projects.json"),
                          [c for c in corpus if c["source"] == "DarGlobal"])
        write_json_atomic(os.path.join(PROCESSED_DIR, "wasalt_listings.json"),
                          [c for c in corpus if c["source"] == "Wasalt"])
        write_json_atomic(KB_PATH, corpus)
        write_json_atomic(META_PATH, {"built_at": built_at, "darglobal": dg_meta, "wasalt": ws_meta,
                                      "total_records": len(corpus)})
        logger.info("==> Done: %d records (DarGlobal %d [%s], Wasalt %d [%s]) -> %s", len(corpus),
                    len(dg_items), dg_meta["status"], len(ws_items), ws_meta["status"], KB_PATH)
        return KB_PATH


def last_scrape_info() -> Dict[str, Any]:
    """What the app shows as 'last synced'."""
    try:
        with open(META_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cached", action="store_true", help="skip live scraping, rebuild from data/raw/")
    ap.add_argument("--only", choices=["all", "darglobal", "wasalt"], default="all")
    args = ap.parse_args()
    run_pipeline(live=not args.cached, only=args.only)
