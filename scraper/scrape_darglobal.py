"""
DarGlobal scraper (darglobal.co.uk).

1. Opens https://darglobal.co.uk/projects in Chromium and reads the project
   catalogue the page itself is built from (title, location, type, completion
   date, link for every project).
2. Fetches each project page and reads its structured content: key facts
   (property type, status, unit types, area), description, amenities,
   "why invest" notes and the project FAQ.
3. Fetches the company pages (about, investor relations, why invest, FAQ,
   hospitality, partners) for general questions.

Run on its own:  python -m scraper.scrape_darglobal
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from scraper.browser import BrowserSession, clean_text, next_data, rich_text

logger = logging.getLogger("DarGlobalScraper")

BASE = "https://darglobal.co.uk"
COMPANY_PAGES = ["/about", "/investor", "/why-invest", "/faq", "/hospitality", "/commercial",
                 "/partners", "/luxury-golf-communities", "/development-management", "/tokenization"]

COUNTRY_BY_URL = {
    "properties-in-uae": "United Arab Emirates", "properties-in-uk": "United Kingdom",
    "properties-in-spain": "Spain", "properties-in-oman": "Oman", "properties-in-qatar": "Qatar",
    "properties-in-saudi-arabia": "Saudi Arabia",
}
COUNTRY_WORDS = {"uae", "united arab emirates", "oman", "ksa", "saudi arabia", "qatar", "spain",
                 "uk", "united kingdom", "england", "maldives"}
CITY_FIX = {"Rak": "Ras Al Khaimah", "Jeddha": "Jeddah"}
# Only brands that DarGlobal itself lists as partners; matched against the scraped text.
BRANDS = [("Trump", "The Trump Organization"), ("Aston Martin", "Aston Martin"),
          ("Lamborghini", "Automobili Lamborghini"), ("Pagani", "Pagani Automobili"),
          ("Missoni", "Missoni"), ("Elie Saab", "ELIE SAAB"), ("Fendi", "Fendi Casa"),
          ("Mouawad", "Mouawad"), ("Marriott", "Marriott Residences"), ("W Residences", "W Hotels"),
          ("Nickelodeon", "Paramount (Nickelodeon)")]
SKIP_KEYS = {"url", "hash", "ext", "mime", "provider", "provider_metadata", "previewUrl", "formats",
             "createdAt", "updatedAt", "publishedAt", "locale", "vuid", "slug", "Link", "link",
             "cta_link", "projectTypeUrl", "locationUrl", "iconClass", "image", "icon", "value_icon",
             "localizations", "versions", "SEO", "seo", "structuredData", "metaSocial", "canonicalURL",
             "HeroBanner", "HeroBannerMobile", "PhotoGallery", "newGallery", "gallery", "Gallery",
             "contentPosition", "imagePosition", "fieldId", "ButtonTheme", "target", "event", "events"}
RICH_TEXT_MARKERS = {"paragraph", "text", "heading", "list", "list-item", "link", "left", "right",
                     "center", "primary", "secondary", "ordered", "unordered"}


# --------------------------------------------------------------------- helpers
def _strings(node: Any, out: List[str], key: str = "") -> None:
    """Collect human-readable strings from a CMS object, skipping media and ids."""
    if key in SKIP_KEYS:
        return
    if isinstance(node, dict):
        if "mime" in node or ("data" in node and len(node) == 1 and isinstance(node["data"], (dict, type(None)))
                              and (node["data"] or {}).get("attributes", {}).get("mime")):
            return  # an image / video entry
        for k, v in node.items():
            _strings(v, out, k)
    elif isinstance(node, list):
        for item in node:
            _strings(item, out, key)
    elif isinstance(node, str):
        text = clean_text(node)
        if key == "type" or text.lower() in RICH_TEXT_MARKERS:
            return
        if len(text) >= 3 and not text.startswith(("http", "/", "#")) and not re.fullmatch(r"[\w-]+\.(webp|jpg|png|mp4|svg)", text):
            out.append(text)


def _dedupe(parts: List[str]) -> List[str]:
    seen, out = set(), []
    for p in parts:
        k = p.lower()
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


def _find_all(node: Any, pred, found: Optional[List[Any]] = None) -> List[Any]:
    found = [] if found is None else found
    if isinstance(node, dict):
        if pred(node):
            found.append(node)
        for v in node.values():
            _find_all(v, pred, found)
    elif isinstance(node, list):
        for v in node:
            _find_all(v, pred, found)
    return found


def _split_location(location: str, country: str) -> Tuple[str, str]:
    parts = [p.strip() for p in re.split(r"[,|]", location or "") if p.strip()]
    places = [p for p in parts if p.lower() not in COUNTRY_WORDS] or parts
    city = places[-1].title() if places else ""
    city = CITY_FIX.get(city, city)
    district = ", ".join(p.title() for p in places[:-1])  # empty when the location is just the city
    return city, district


def _brand(text: str) -> str:
    hits = [name for key, name in BRANDS if key.lower() in text.lower()]
    return ", ".join(dict.fromkeys(hits)) or "N/A"


# ------------------------------------------------------------- catalogue
def read_catalogue(session: BrowserSession) -> List[Dict[str, Any]]:
    """Every project card on /projects, de-duplicated by link."""
    props = next_data(session.get(f"{BASE}/projects"))
    cards: Dict[str, Dict[str, Any]] = {}
    for tab in props.get("pageData", {}).get("attributes", {}).get("Tabs", []) or []:
        for card in tab.get("TabData", []) or []:
            link = (card.get("Link") or "").strip()
            if not link.startswith("/") or link in cards:
                continue
            cards[link] = {
                "title": clean_text(card.get("ProjectTitle")),
                "location": clean_text(card.get("Location")),
                "type": clean_text(card.get("ProjectType")),
                "country": COUNTRY_BY_URL.get(card.get("locationUrl") or "", ""),
                "completion": clean_text(card.get("completionDate")),
                "bedrooms": clean_text(card.get("Bedrooms")),
                "summary": rich_text(card.get("ProjectDescription")),
                "link": link,
            }
    logger.info("catalogue: %d projects", len(cards))
    return list(cards.values())


# ------------------------------------------------------------- project page
def parse_project(html: str, card: Dict[str, Any]) -> Dict[str, Any]:
    props = next_data(html)
    page = {k: v for k, v in props.items() if k not in ("globalData", "thankyouPageData", "thankyouData", "otherProjectData")}

    # "One of One" pages ship the whole collection; keep only this page's property.
    collection = props.get("collectionsData")
    if isinstance(collection, list) and collection:
        want = card["link"].rstrip("/").rsplit("/", 1)[-1].lower()
        words = set(re.findall(r"[a-z]{4,}", card["title"].lower()))
        def match(c):
            a = c.get("attributes") or {}
            if str(a.get("slug", "")).lower() == want:
                return 100
            return len(words & set(re.findall(r"[a-z]{4,}", str(a.get("title", "")).lower())))
        best = max(collection, key=match)
        page = {"collection_item": best}

    # Key facts: [{name: "Status", value: "Under Development"}, ...]
    facts: Dict[str, str] = {}
    for row in _find_all(page, lambda d: isinstance(d.get("name"), str) and isinstance(d.get("value"), str)
                         and "AboutDetails" not in d and len(d.get("value", "")) < 120):
        name, value = clean_text(row["name"]), clean_text(row["value"])
        if name and value and not re.fullmatch(r"[a-z0-9-]+", value):  # skip icon slugs
            facts.setdefault(name, value)

    amenities: List[str] = []
    for block in _find_all(page, lambda d: any("amenit" in k.lower() for k in d.keys())):
        for k, v in block.items():
            if "amenit" in k.lower() and isinstance(v, (list, dict)):
                for item in _find_all(v, lambda d: isinstance(d.get("name"), str)):
                    amenities.append(clean_text(item["name"]))
    amenities = [a for a in _dedupe(amenities)
                 if a and a not in facts and not re.search(r"\.(webp|jpe?g|png|svg|mp4|gif)$", a, re.I)][:20]

    faqs = []
    for q in _find_all(page, lambda d: isinstance(d.get("question"), str) and "answer" in d):
        answer = rich_text(q.get("answer"))
        if answer:
            faqs.append({"q": clean_text(q["question"]), "a": answer})

    description = ""
    for block in _find_all(page, lambda d: "description" in d and any(k.lower() in ("aboutproject", "title", "heading") for k in d)):
        text = rich_text(block.get("description"))
        if len(text) > len(description) and len(text) > 60:
            description = text
            break
    if not description:
        description = card.get("summary") or (faqs[0]["a"] if faqs else "")

    why = []
    for block in _find_all(page, lambda d: any(k.lower() == "whyinvest" for k in d)):
        for k, v in block.items():
            if k.lower() == "whyinvest":
                _strings(v, why)
    # Facts outside the core ones are the "why invest" bullets (visa, tax, location).
    core = re.compile(r"property type|status|unit|bedroom|area|size|location|branded|featuring", re.I)
    extra = [f"{k.rstrip(':')}: {v}" for k, v in facts.items() if not core.search(k)]
    investment = " ".join(_dedupe(why + extra))[:1800]
    facts = {k: v for k, v in facts.items() if core.search(k)}

    everything: List[str] = []
    _strings(page, everything)
    full_text = " ".join(_dedupe(everything))[:8000]

    banner = (_find_all(page, lambda d: "StartingPrice" in d) or [{}])[0]
    price = clean_text(banner.get("StartingPrice")) or "Price on request"
    title = card["title"] or clean_text(banner.get("Heading"))
    location = card["location"] or clean_text(banner.get("Location"))
    city, district = _split_location(location, card["country"])
    units = next((v for k, v in facts.items() if re.search(r"unit|bedroom", k, re.I)), card.get("bedrooms") or "")
    status = facts.get("Status") or facts.get("STATUS") or ""
    if card.get("completion"):
        status = f"{status} (completion {card['completion']})".strip()
    area = next((f"{v} ({k})" for k, v in facts.items() if re.search(r"area|size", k, re.I)), "")

    slug = card["link"].strip("/").replace("/", "-").lower()
    return {
        "id": f"dg-{slug}",
        "title": title,
        "developer": "DarGlobal",
        "brand_partner": _brand(f"{title} {description[:400]}"),
        "country": card["country"],
        "city": city,
        "district": district,
        "property_type": facts.get("Property Type") or facts.get("PROPERTY TYPE") or card["type"],
        "bedrooms": units,
        "area": area,
        "starting_price_local": price,
        "starting_price_usd": "",
        "status": status or "See project page",
        "description": description[:1500],
        "key_facts": facts,
        "amenities": amenities,
        "investment_highlights": investment,
        "faqs": faqs[:12],
        "page_text": full_text,
        "source_url": BASE + card["link"],
        "source": "DarGlobal",
    }


def _is_legal(block: Any) -> bool:
    """Privacy / cookie / terms text that the site ships with every page."""
    title = ""
    if isinstance(block, dict):
        title = str((block.get("attributes") or {}).get("title") or block.get("title") or "")
    return bool(re.search(r"privacy|cookie|terms", title, re.I))


def parse_company_page(html: str, path: str) -> Dict[str, Any]:
    props = next_data(html)
    page = {k: v for k, v in props.items()
            if k not in ("globalData", "thankyouPageData", "thankyouData") and not _is_legal(v)}
    parts: List[str] = []
    _strings(page, parts)
    text = " ".join(_dedupe(parts))
    title = {"/about": "About DarGlobal", "/investor": "DarGlobal Investor Relations",
             "/why-invest": "Why Invest with DarGlobal (visas and tax by country)", "/faq": "DarGlobal FAQ",
             "/hospitality": "DarGlobal Hospitality (hotels and clubs)", "/commercial": "DarGlobal Commercial",
             "/partners": "DarGlobal Brand Partners", "/luxury-golf-communities": "DarGlobal Golf Communities",
             "/development-management": "DarGlobal Development Management",
             "/tokenization": "DarGlobal Tokenization"}.get(path, path.strip("/").title())
    faqs = [{"q": clean_text(q["question"]), "a": rich_text(q.get("answer"))}
            for q in _find_all(page, lambda d: isinstance(d.get("question"), str) and "answer" in d)]
    countries = [c for c in ("Saudi Arabia", "United Arab Emirates", "Oman", "Qatar", "Spain", "United Kingdom",
                             "Greece", "Maldives", "Dubai", "Riyadh", "Jeddah", "Muscat", "Doha", "London")
                 if c.lower() in text.lower()]
    return {
        "id": f"dg-page-{path.strip('/')}",
        "title": title,
        "developer": "DarGlobal",
        "brand_partner": "N/A",
        "country": "International",
        "city": "",
        "district": ", ".join(countries),  # markets this page talks about, so location questions find it
        "property_type": "Company information",
        "bedrooms": "",
        "starting_price_local": "",
        "starting_price_usd": "",
        "status": "",
        "description": text[:2500],
        "amenities": [],
        "investment_highlights": text[2500:5000],
        "faqs": faqs[:15],
        "page_text": text[:8000],
        "source_url": BASE + path,
        "source": "DarGlobal",
    }


# ------------------------------------------------------------------ entry point
def scrape_darglobal_portfolio(output_dir: str = "data/raw", headless: Optional[bool] = True,
                               max_projects: Optional[int] = None) -> List[Dict[str, Any]]:
    """Scrape darglobal.co.uk live and save data/raw/darglobal_scraped.json."""
    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records: List[Dict[str, Any]] = []
    with BrowserSession(BASE, headless=headless) as session:
        catalogue = read_catalogue(session)[: max_projects or None]
        for card in catalogue:
            try:
                rec = parse_project(session.get(BASE + card["link"]), card)
                rec["scraped_at"] = scraped_at
                records.append(rec)
                logger.info("project ok: %s", rec["title"])
            except Exception as exc:
                logger.warning("project failed %s: %s", card["link"], exc)
        for path in COMPANY_PAGES:
            try:
                rec = parse_company_page(session.get(BASE + path), path)
                rec["scraped_at"] = scraped_at
                records.append(rec)
            except Exception as exc:
                logger.warning("page failed %s: %s", path, exc)

    if not any(r["property_type"] != "Company information" for r in records):
        raise RuntimeError("DarGlobal scrape returned no projects")
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "darglobal_scraped.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.info("DarGlobal: %d records saved", len(records))
    return records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    scrape_darglobal_portfolio()
