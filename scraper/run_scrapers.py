"""
Master Ingestion & Pipeline Runner
Orchestrates scraping from DarGlobal and Wasalt, validates data schemas,
generates search-ready chunks, and writes the consolidated knowledge base.
"""

import json
import logging
import os
import sys
from datetime import datetime

# Ensure scraper package is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from scraper.scrape_darglobal import scrape_darglobal_portfolio
from scraper.scrape_wasalt import scrape_wasalt_listings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("PipelineRunner")

def build_search_text(item: dict) -> str:
    """Creates a consolidated text block for lexical and semantic retrieval."""
    parts = [
        f"Title: {item.get('title', '')}",
        f"Source: {item.get('source', '')}",
        f"Brand Partner: {item.get('brand_partner', 'N/A')}",
        f"Location: {item.get('city', '')}, {item.get('country', '')} ({item.get('district', '')})",
        f"Property Type: {item.get('property_type', '')}",
        f"Bedrooms: {item.get('bedrooms', '')}",
        f"Price: {item.get('price_local', item.get('starting_price_local', ''))} ({item.get('price_usd', item.get('starting_price_usd', ''))})",
        f"Status: {item.get('status', item.get('handover', ''))}",
        f"Description: {item.get('description', '')}",
        f"Amenities: {', '.join(item.get('amenities', []))}",
        f"Investment / Market Insights: {item.get('investment_highlights', item.get('market_insights', ''))}",
        f"URL: {item.get('source_url', '')}"
    ]
    return "\n".join(parts)

def run_pipeline():
    sync_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"==> Phase 1: Ingesting DarGlobal luxury developments (Sync timestamp: {sync_time_str})...")
    dg_items = scrape_darglobal_portfolio(output_dir=os.path.join(parent_dir, "data", "raw"))

    logger.info("==> Phase 2: Ingesting Wasalt Saudi properties and platform data...")
    ws_items = scrape_wasalt_listings(output_dir=os.path.join(parent_dir, "data", "raw"))

    logger.info("==> Phase 3: Normalizing and building enriched knowledge base...")
    normalized_corpus = []

    for item in dg_items:
        norm_item = {
            "id": item["id"],
            "title": item["title"],
            "source": "DarGlobal",
            "developer": item.get("developer", "DarGlobal"),
            "brand_partner": item.get("brand_partner", "N/A"),
            "country": item["country"],
            "city": item["city"],
            "district": item["district"],
            "property_type": item["property_type"],
            "bedrooms": item["bedrooms"],
            "price_local": item.get("starting_price_local", ""),
            "price_usd": item.get("starting_price_usd", ""),
            "status": item.get("status", item.get("handover", "")),
            "description": item["description"],
            "amenities": item["amenities"],
            "investment_highlights": item.get("investment_highlights", ""),
            "source_url": item["source_url"],
            "last_synced": sync_time_str
        }
        norm_item["search_text"] = build_search_text(norm_item)
        normalized_corpus.append(norm_item)

    for item in ws_items:
        norm_item = {
            "id": item["id"],
            "title": item["title"],
            "source": "Wasalt",
            "developer": item.get("developer", "Wasalt Partner"),
            "brand_partner": "Wasalt PropTech",
            "country": item["country"],
            "city": item["city"],
            "district": item["district"],
            "property_type": item["property_type"],
            "bedrooms": item.get("bedrooms", "N/A"),
            "price_local": item.get("price_local", ""),
            "price_usd": item.get("price_usd", ""),
            "status": item.get("status", "Available"),
            "description": item["description"],
            "amenities": item["amenities"],
            "investment_highlights": item.get("market_insights", ""),
            "source_url": item["source_url"],
            "last_synced": sync_time_str
        }
        norm_item["search_text"] = build_search_text(norm_item)
        normalized_corpus.append(norm_item)

    # Save to data/processed
    processed_dir = os.path.join(parent_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    with open(os.path.join(processed_dir, "darglobal_projects.json"), "w", encoding="utf-8") as f:
        json.dump(dg_items, f, indent=2, ensure_ascii=False)

    with open(os.path.join(processed_dir, "wasalt_listings.json"), "w", encoding="utf-8") as f:
        json.dump(ws_items, f, indent=2, ensure_ascii=False)

    kb_path = os.path.join(parent_dir, "data", "knowledge_base.json")
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(normalized_corpus, f, indent=2, ensure_ascii=False)

    logger.info(f"==> Pipeline complete! Total indexed records: {len(normalized_corpus)}")
    logger.info(f"    - DarGlobal records: {len(dg_items)}")
    logger.info(f"    - Wasalt records: {len(ws_items)}")
    logger.info(f"    - Saved to: {kb_path}")
    return kb_path

if __name__ == "__main__":
    run_pipeline()
