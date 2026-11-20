"""
Wasalt scraper (wasalt.sa).

1. Reads Wasalt's public category sitemap (cdn.wasalt.sa) to find the city pages
   ("properties for sale in Riyadh", "properties for rent in Jeddah", ...).
2. Opens each city page in Chromium and reads the listings the page is built
   from (30 newest per page): title, type, district, price, bedrooms,
   bathrooms, area, amenities, listing link.
3. Keeps each city page's guide text, FAQ and total listing count as a market
   guide, plus a median-price snapshot per property type from the sample.

Agent names and phone numbers are deliberately not stored.
robots.txt disallows /search, so only city/category pages are used.

Run on its own:  python -m scraper.scrape_wasalt
"""

import json
import logging
import os
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from scraper.browser import BrowserSession, clean_text, fetch_sitemap, next_data

logger = logging.getLogger("WasaltScraper")

BASE = "https://wasalt.sa"
CATEGORY_SITEMAP = "https://cdn.wasalt.sa/sitemap/category_sitemap_en_sa.xml.gz"
CITIES = ["riyadh", "jeddah", "al-khobar", "dammam", "makkah", "madinah", "taif", "abha"]
SUB_CATEGORY_CITIES = ["riyadh", "jeddah"]  # also apartments-/villas- pages for the two biggest markets
SAR_PER_USD = 3.75  # the riyal is pegged to the dollar


def _money(v: Any) -> Optional[float]:
    try:
        f = float(str(v).replace(",", ""))
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


def _fmt(v: float) -> str:
    return f"{v:,.0f}"


def city_pages() -> List[str]:
    """City (and a few category) pages, taken from Wasalt's own sitemap."""
    try:
        try:
            locs = fetch_sitemap(CATEGORY_SITEMAP)
        except Exception:
            locs = fetch_sitemap(CATEGORY_SITEMAP)  # the CDN occasionally drops the first request
    except Exception as exc:
        logger.warning("sitemap unavailable (%s); using known city URLs", exc)
        locs = [f"{BASE}/en/properties-for-{m}-in-{c}" for c in CITIES for m in ("sale", "rent")]
    wanted = []
    for city in CITIES:
        for mode in ("sale", "rent"):
            url = f"{BASE}/en/properties-for-{mode}-in-{city}"
            if url in locs:
                wanted.append(url)
    for city in SUB_CATEGORY_CITIES:
        for kind in ("apartments", "villas"):
            for mode in ("sale", "rent"):
                url = f"{BASE}/en/{kind}-for-{mode}-in-{city}"
                if url in locs:
                    wanted.append(url)
    return wanted


def parse_listing(p: Dict[str, Any], page_city: str) -> Optional[Dict[str, Any]]:
    info = p.get("propertyInfo") or {}
    title = clean_text(info.get("title"))
    slug = info.get("slug")
    if not title or not slug:
        return None
    mode = info.get("propertyFor") or "sale"
    attrs = {a.get("key"): (a.get("value"), a.get("unit"), a.get("name")) for a in p.get("attributes") or []}
    beds = attrs.get("noOfBedrooms", (None,))[0]
    baths = attrs.get("noOfBathrooms", (None,))[0]
    area = next((f"{v} {u or 'sqm'} ({n})" for k, (v, u, n) in attrs.items()
                 if k in ("builtUpArea", "carpetArea", "landArea", "plotArea") and v), "")

    price = _money(info.get("salePrice")) if mode == "sale" else _money(info.get("expectedRent"))
    price = price or _money(info.get("conversionPrice"))
    per = (info.get("expectedRentType") or "/Year").strip("/").lower() if mode == "rent" else ""
    price_local = f"SAR {_fmt(price)}{' per ' + per if per else ''}" if price else "Price on request"
    price_usd = f"~${_fmt(price / SAR_PER_USD)}{' per ' + per if per else ''}" if price else ""

    amenities = [clean_text(a.get("name") or a.get("title") or a) for a in (p.get("featureAmenities") or [])
                 if isinstance(a, (dict, str))]
    district = ", ".join(x for x in dict.fromkeys([clean_text(info.get("district") or info.get("zone")),
                                                    clean_text(info.get("territory"))]) if x)
    sub_type = clean_text(info.get("propertySubType"))
    return {
        "id": f"ws-{p.get('id')}",
        "listing_id": p.get("id"),
        "title": title,
        "developer": "Listed on Wasalt",
        "country": "Saudi Arabia",
        "city": clean_text(info.get("city")) or page_city.title(),
        "district": district,
        "property_type": f"{sub_type} ({clean_text(info.get('propertyMainType'))})" if sub_type else clean_text(info.get("propertyMainType")),
        "sub_type": sub_type,
        "category": "Sale" if mode == "sale" else "Rent",
        "bedrooms": f"{beds} bedrooms" if beds else "",
        "bathrooms": f"{baths} bathrooms" if baths else "",
        "area": area,
        "price_value": price,
        "price_local": price_local,
        "price_usd": price_usd,
        "status": f"For {'Sale' if mode == 'sale' else 'Rent'}" + (" · REGA-licensed ad" if p.get("isRegaProp") else ""),
        "description": clean_text(info.get("description"))[:700] or f"{title} in {district}, {info.get('city')}.",
        "amenities": [a for a in amenities if a][:12],
        "market_insights": "",
        "published_at": p.get("publishedAt") or p.get("createdAt"),
        "updated_at": p.get("updatedAt"),
        "source_url": f"{BASE}/en/property/{mode}/{slug}",
        "source": "Wasalt",
    }


def parse_city_page(html: str, url: str) -> Dict[str, Any]:
    props = next_data(html)
    search = props.get("searchResult")
    search = search if isinstance(search, dict) else {}
    slug = url.rsplit("/", 1)[-1]
    m = re.match(r"(\w+)-for-(sale|rent)-in-([\w-]+)", slug)
    kind, mode, city = (m.group(1), m.group(2), m.group(3)) if m else ("properties", "sale", slug)
    listings = []
    for p in search.get("properties") or []:
        try:
            if isinstance(p, dict) and isinstance(p.get("propertyInfo"), dict):
                rec = parse_listing(p, city)
                if rec:
                    listings.append(rec)
        except Exception as exc:  # one odd card (e.g. a developer project) shouldn't drop the page
            logger.debug("skip listing on %s: %s", url, exc)

    faqs = []
    schemas = props.get("FAQSchema") or []
    for schema in schemas if isinstance(schemas, list) else [schemas]:
        if not isinstance(schema, dict):
            continue
        for q in schema.get("mainEntity", []) or []:
            ans = q.get("acceptedAnswer") if isinstance(q, dict) else None
            a = clean_text(ans.get("text") if isinstance(ans, dict) else "")
            if isinstance(q, dict) and q.get("name") and a:
                faqs.append({"q": clean_text(q["name"]), "a": a})
    meta = props.get("metaData")
    meta = meta if isinstance(meta, dict) else {}
    return {"url": url, "kind": kind, "mode": mode, "city": city.replace("-", " ").title(),
            "title": clean_text(meta.get("title_tag") or meta.get("meta_title")) or slug.replace("-", " ").title(),
            "total_count": search.get("count"), "guide": clean_text(props.get("para"))[:3000],
            "meta_description": clean_text(meta.get("meta_description")), "faqs": faqs, "listings": listings}


def guide_record(page: Dict[str, Any], scraped_at: str) -> Dict[str, Any]:
    """One market-guide document per city page, with a price snapshot from the sample."""
    by_type = defaultdict(list)
    for r in page["listings"]:
        if r["price_value"]:
            by_type[r["sub_type"] or "Other"].append(r["price_value"])
    unit = " per year" if page["mode"] == "rent" else ""
    snapshot = "; ".join(
        f"{t}: median SAR {_fmt(statistics.median(v))}{unit} (range {_fmt(min(v))}-{_fmt(max(v))}, {len(v)} listings)"
        for t, v in sorted(by_type.items(), key=lambda kv: -len(kv[1])))
    count = page["total_count"]
    lead = (f"Wasalt shows {count:,} {page['kind']} for {page['mode']} in {page['city']} "
            f"(as of {scraped_at[:10]}). " if isinstance(count, int) else "")
    return {
        "id": f"ws-guide-{page['url'].rsplit('/', 1)[-1]}",
        "title": f"Wasalt market guide: {page['title']}",
        "developer": "Wasalt",
        "country": "Saudi Arabia",
        "city": page["city"],
        "district": "city-wide",
        "property_type": "Market guide",
        "category": page["mode"].title(),
        "bedrooms": "",
        "price_local": "",
        "price_usd": "",
        "status": f"{count:,} live listings" if isinstance(count, int) else "",
        "description": (lead + (page["meta_description"] + " " if page["meta_description"] else "") + page["guide"])[:3200],
        "amenities": [],
        "market_insights": (f"Price snapshot from the newest {len(page['listings'])} listings on this page: {snapshot}."
                            if snapshot else ""),
        "faqs": page["faqs"],
        "source_url": page["url"],
        "source": "Wasalt",
        "scraped_at": scraped_at,
    }


EXPORT_COLUMNS = ["id", "slug", "propertyFor", "propertySubType", "propertyMainType", "title", "district",
                  "territory", "city", "price", "expectedRentType", "beds", "baths", "area", "area_unit",
                  "area_name", "isRegaProp", "publishedAt"]


def records_from_browser_export(export: List[Dict[str, Any]], scraped_at: str) -> List[Dict[str, Any]]:
    """
    Convert city pages collected in an ordinary browser session (see README,
    "When Wasalt shows a bot check") into the same records the scraper makes.
    Each page: {u, count, title, meta, para, faqs: [[q, a]], rows: [[EXPORT_COLUMNS...]]}.
    """
    records: List[Dict[str, Any]] = []
    for page in export:
        if page.get("err") or not page.get("rows"):
            continue
        props = []
        for row in page["rows"]:
            r = dict(zip(EXPORT_COLUMNS, row))
            attrs = [{"key": "noOfBedrooms", "value": r["beds"]}, {"key": "noOfBathrooms", "value": r["baths"]}]
            if r["area"]:
                attrs.append({"key": "builtUpArea", "value": r["area"], "unit": r["area_unit"], "name": r["area_name"]})
            mode = r["propertyFor"]
            props.append({"id": r["id"], "isRegaProp": bool(r["isRegaProp"]), "publishedAt": r["publishedAt"],
                          "attributes": attrs,
                          "propertyInfo": {"title": r["title"], "slug": r["slug"], "propertyFor": mode,
                                           "propertySubType": r["propertySubType"],
                                           "propertyMainType": r["propertyMainType"], "district": r["district"],
                                           "territory": r["territory"], "city": r["city"],
                                           "salePrice": r["price"] if mode == "sale" else "",
                                           "expectedRent": r["price"] if mode == "rent" else "",
                                           "expectedRentType": r["expectedRentType"]}})
        url = page["u"]
        slug = url.rsplit("/", 1)[-1]
        m = re.match(r"(\w+)-for-(sale|rent)-in-([\w-]+)", slug)
        kind, mode, city = (m.group(1), m.group(2), m.group(3)) if m else ("properties", "sale", slug)
        listings = [x for x in (parse_listing(p, city) for p in props) if x]
        parsed = {"url": url, "kind": kind, "mode": mode, "city": city.replace("-", " ").title(),
                  "title": page.get("title") or slug.replace("-", " ").title(), "total_count": page.get("count"),
                  "guide": page.get("para", ""), "meta_description": page.get("meta", ""),
                  "faqs": [{"q": q, "a": a} for q, a in page.get("faqs", [])], "listings": listings}
        records.append(guide_record(parsed, scraped_at))
        for x in listings:
            x["scraped_at"] = scraped_at
            records.append(x)
    return records


def scrape_wasalt_listings(output_dir: str = "data/raw", headless: Optional[bool] = None,
                           max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
    """Scrape wasalt.sa live and save data/raw/wasalt_scraped.json."""
    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    urls = city_pages()[: max_pages or None]
    records: List[Dict[str, Any]] = []
    seen = set()
    blocked_in_a_row = 0
    # Slow, polite pacing: Cloudflare starts showing an interactive check if pages come too fast.
    with BrowserSession(BASE + "/en", headless=headless, delay=float(os.getenv("WASALT_DELAY", "4"))) as session:
        for url in urls:
            try:
                page = parse_city_page(session.get(url, retries=1), url)
                blocked_in_a_row = 0
            except FileNotFoundError as exc:
                logger.warning("city page gone %s: %s", url, exc)
                continue
            except Exception as exc:
                blocked_in_a_row += 1
                logger.warning("city page failed %s: %s", url, exc, exc_info=logger.isEnabledFor(logging.DEBUG))
                if blocked_in_a_row >= 2:
                    logger.warning("Wasalt is showing an interactive bot check; stopping early and keeping "
                                   "what was collected (try again later)")
                    break
                continue
            records.append(guide_record(page, scraped_at))
            for r in page["listings"]:
                if r["id"] not in seen:
                    seen.add(r["id"])
                    r["scraped_at"] = scraped_at
                    records.append(r)
            logger.info("%s: %d listings (site total %s)", url, len(page["listings"]), page["total_count"])

    if not any(r["property_type"] != "Market guide" for r in records):
        raise RuntimeError("Wasalt scrape returned no listings")
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "wasalt_scraped.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.info("Wasalt: %d records saved", len(records))
    return records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    scrape_wasalt_listings()
