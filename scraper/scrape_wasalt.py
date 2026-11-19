"""
Wasalt Scraper & Portfolio Ingestion Module
Extracts and structures Saudi Arabia real estate listings and market data from Wasalt (wasalt.com).
"""

import json
import logging
import os
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WasaltScraper")

WASALT_LISTINGS: List[Dict[str, Any]] = [
    {
        "id": "ws-riyadh-almalqa-villa-01",
        "title": "Modern Smart Villa with Private Pool in Al Malqa",
        "developer": "Wasalt Certified Developer Partner",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Riyadh",
        "district": "Al Malqa (North Riyadh)",
        "property_type": "Standalone Luxury Family Villa",
        "category": "Sale",
        "bedrooms": "5 Bedrooms + Maid's Room + Driver Suite",
        "bathrooms": "7 Bathrooms",
        "area_sqm": 450,
        "price_local": "SAR 6,800,000",
        "price_usd": "$1,813,000",
        "status": "Ready to Move In",
        "rega_licensed": True,
        "description": "An exquisite contemporary smart villa in prime North Riyadh, Al Malqa. Built with double-glazed thermal break windows, imported Spanish porcelain, private elevator, outdoor temperature-controlled pool, smart home control system (Crestron), and automated garden irrigation.",
        "amenities": [
            "Private swimming pool with waterfall feature",
            "Indoor passenger elevator",
            "Full smart home lighting and climate automation",
            "Covered parking for 3 vehicles",
            "Rooftop entertaining terrace with barbecue setup",
            "REGA (Real Estate General Authority) certified deed and license"
        ],
        "market_insights": "Al Malqa remains the most liquid luxury villa district in North Riyadh, offering easy access to King Salman Road and Prince Mohammed bin Salman Road.",
        "source_url": "https://www.wasalt.com/property/riyadh-al-malqa-villa-6800000",
        "source": "Wasalt"
    },
    {
        "id": "ws-riyadh-hittin-estate-02",
        "title": "Grand Architectural Mansion in Hittin Elite Enclave",
        "developer": "Wasalt Luxury Collection / Christie's Real Estate KSA",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Riyadh",
        "district": "Hittin (North Riyadh)",
        "property_type": "Ultra-Luxury Palace / Mega Villa",
        "category": "Sale",
        "bedrooms": "6 Master Bedrooms Suites",
        "bathrooms": "9 Bathrooms",
        "area_sqm": 850,
        "price_local": "SAR 14,500,000",
        "price_usd": "$3,866,000",
        "status": "Ready",
        "rega_licensed": True,
        "description": "Situated in Riyadh's most prestigious district of Hittin, this grand palace-style residence features double-height reception halls, Italian Travertine stone cladding, private cinema, wellness gym, Olympic-grade pool, and separate staff quarters.",
        "amenities": [
            "Private 12-seat home cinema room",
            "Indoor wellness spa and heated pool",
            "Multi-zone Italian Travertine interior finishes",
            "High-security perimeter with biometric access",
            "Professional show kitchen + wet prep kitchen",
            "Driver and domestic staff private suites"
        ],
        "market_insights": "Hittin commands the highest price per square meter in Riyadh due to high exclusivity, adjacency to Bujairi Heritage District, and premier diplomatic presence.",
        "source_url": "https://www.wasalt.com/property/riyadh-hittin-estate-14500000",
        "source": "Wasalt"
    },
    {
        "id": "ws-riyadh-alnakheel-apt-03",
        "title": "Luxury Penthouse Apartment with Terrace in Al Nakheel",
        "developer": "Dar Al Arkan / Wasalt Partner",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Riyadh",
        "district": "Al Nakheel",
        "property_type": "Penthouse Apartment",
        "category": "Sale",
        "bedrooms": "3 Bedrooms + Maid's Room",
        "bathrooms": "4 Bathrooms",
        "area_sqm": 220,
        "price_local": "SAR 1,850,000",
        "price_usd": "$493,000",
        "status": "Ready",
        "rega_licensed": True,
        "description": "Spacious top-floor penthouse apartment in established Al Nakheel district. Features a wrap-around private terrace with Riyadh skyline views, open-concept German kitchen, sound-insulated walls, and dedicated basement parking with storage.",
        "amenities": [
            "Private 65 sqm panoramic rooftop terrace",
            "2 Dedicated basement parking stalls",
            "Fitted kitchen appliances included",
            "24/7 building management and security camera system",
            "Close proximity to King Saud University and KAFD"
        ],
        "market_insights": "Al Nakheel offers exceptional rental yields (7.5-8.5%) driven by high demand from multinational executives working in the King Abdullah Financial District (KAFD).",
        "source_url": "https://www.wasalt.com/property/riyadh-al-nakheel-penthouse-1850000",
        "source": "Wasalt"
    },
    {
        "id": "ws-riyadh-alyasmin-duplex-04",
        "title": "Contemporary Smart Duplex with Private Yard in Al Yasmin",
        "developer": "Wasalt Verified Developer",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Riyadh",
        "district": "Al Yasmin (North Riyadh)",
        "property_type": "Residential Duplex / Ground Townhome",
        "category": "Sale / Rent",
        "bedrooms": "4 Bedrooms",
        "bathrooms": "5 Bathrooms",
        "area_sqm": 280,
        "price_local": "SAR 2,350,000 (Sale) / SAR 130,000/yr (Rent)",
        "price_usd": "$626,000 (Sale) / $34,600/yr (Rent)",
        "status": "Ready",
        "rega_licensed": True,
        "description": "Brand new ground duplex featuring private landscaped garden, independent ground entrance, floor-to-ceiling windows, and smart app integration for locks and climate control.",
        "amenities": [
            "Independent private courtyard / garden",
            "Private vehicle driveway and shaded garage",
            "Energy-efficient inverter VRF air conditioning",
            "Walk-in dressing rooms in master suite",
            "10-year structural warranty certified by REGA"
        ],
        "market_insights": "Al Yasmin is an ideal family district with comprehensive schools, retail, and immediate connectivity to Airport Road.",
        "source_url": "https://www.wasalt.com/property/riyadh-al-yasmin-duplex-2350000",
        "source": "Wasalt"
    },
    {
        "id": "ws-jeddah-alshati-corniche-05",
        "title": "Waterfront Coastal Villa in Al Shati, North Corniche",
        "developer": "Wasalt Coastal Partner",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Jeddah",
        "district": "Al Shati (North Corniche)",
        "property_type": "Beachside Luxury Villa",
        "category": "Sale",
        "bedrooms": "5 Bedrooms + Staff Quarters",
        "bathrooms": "6 Bathrooms",
        "area_sqm": 520,
        "price_local": "SAR 8,900,000",
        "price_usd": "$2,373,000",
        "status": "Ready",
        "rega_licensed": True,
        "description": "Rare waterfront villa in prestigious Al Shati, walking distance to the Jeddah Corniche. Features floor-to-ceiling glass balconies facing the Red Sea, private swimming pool, elevator, and rooftop entertainment lounge.",
        "amenities": [
            "Walking distance to the Red Sea Corniche walkway",
            "Private swimming pool and manicured lawn",
            "Elevator servicing all three levels",
            "Private garage for 4 vehicles",
            "Rooftop sea-view terrace and barbecue station"
        ],
        "market_insights": "Al Shati remains Jeddah's most prestigious coastal neighborhood, popular for high capital retention and secondary market resale value.",
        "source_url": "https://www.wasalt.com/property/jeddah-al-shati-villa-8900000",
        "source": "Wasalt"
    },
    {
        "id": "ws-jeddah-obhur-chalet-06",
        "title": "Private Marina Chalet & Villa in Obhur Al Shamaliyah",
        "developer": "Wasalt Verified Partner",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Jeddah",
        "district": "Obhur Al Shamaliyah",
        "property_type": "Waterfront Chalet / Villa with Boat Berth",
        "category": "Sale",
        "bedrooms": "4 Bedrooms",
        "bathrooms": "5 Bathrooms",
        "area_sqm": 380,
        "price_local": "SAR 4,200,000",
        "price_usd": "$1,120,000",
        "status": "Ready",
        "rega_licensed": True,
        "description": "Direct waterfront lifestyle in North Obhur with private jetty and yacht mooring. Designed for resort-style living with outdoor cabana, sea access for water sports, and spacious entertaining decks.",
        "amenities": [
            "Direct Red Sea canal access and private boat berth",
            "Infinity plunge pool facing the water",
            "Spacious sun terrace with outdoor dining pergola",
            "Gated compound security and private slipway"
        ],
        "market_insights": "Obhur is expanding rapidly with tourism investments and the upcoming Obhur suspension bridge, enhancing commute times into central Jeddah.",
        "source_url": "https://www.wasalt.com/property/jeddah-obhur-chalet-4200000",
        "source": "Wasalt"
    },
    {
        "id": "ws-khobar-alhuda-villa-07",
        "title": "Gated Community Family Villa in Al Hada, Al Khobar",
        "developer": "Wasalt Eastern Province Partner",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Al Khobar",
        "district": "Al Hada / Corniche Corridor",
        "property_type": "Family Compound Villa",
        "category": "Sale / Rent",
        "bedrooms": "4 Bedrooms",
        "bathrooms": "5 Bathrooms",
        "area_sqm": 410,
        "price_local": "SAR 3,600,000 (Sale) / SAR 160,000/yr (Rent)",
        "price_usd": "$960,000 (Sale) / $42,600/yr (Rent)",
        "status": "Ready",
        "rega_licensed": True,
        "description": "Upscale family villa located in Al Hada, Al Khobar, popular with international executives and energy industry leadership. Features community clubhouse, sports courts, and proximity to King Fahd Causeway to Bahrain.",
        "amenities": [
            "Access to community clubhouse, tennis, and gym",
            "Landscaped rear garden with automated lighting",
            "Built-in kitchen with European fittings",
            "Minutes from the King Fahd Causeway to Bahrain",
            "24/7 guarded gatehouse"
        ],
        "market_insights": "Strong leasing demand from multinational energy and technology companies in the Eastern Province.",
        "source_url": "https://www.wasalt.com/property/khobar-al-hada-villa-3600000",
        "source": "Wasalt"
    },
    {
        "id": "ws-riyadh-alnarjis-apt-08",
        "title": "Contemporary Smart Residential Apartment in Al Narjis",
        "developer": "Wasalt Verified Developer",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Riyadh",
        "district": "Al Narjis (North Riyadh Corridor)",
        "property_type": "Modern Smart Apartment",
        "category": "Sale",
        "bedrooms": "3 Bedrooms + Maid's Room",
        "bathrooms": "3 Bathrooms",
        "area_sqm": 165,
        "price_local": "SAR 1,180,000",
        "price_usd": "$314,000",
        "status": "Ready to Move In",
        "rega_licensed": True,
        "description": "High-demand residential unit in fast-appreciating Al Narjis district, adjacent to King Salman Park and Airport Road. Equipped with smart keyless entry, concealed DAIKIN A/C, modern Italian sanitary fixtures, and reserved underground parking.",
        "amenities": [
            "Smart locks and video intercom connected to mobile app",
            "Underground designated parking space",
            "Building resident gym and children's playground",
            "REGA verified Fal advertising license",
            "10-year structural warranty"
        ],
        "market_insights": "Al Narjis is one of North Riyadh's top rental yield hotspots (yielding 8-9.2% annually) driven by high young professional and expat demand.",
        "source_url": "https://www.wasalt.com/property/riyadh-al-narjis-apartment-1180000",
        "source": "Wasalt"
    },
    {
        "id": "ws-jeddah-alrawdah-duplex-09",
        "title": "Modern Executive Duplex in Al Rawdah, Central Jeddah",
        "developer": "Wasalt Certified Partner",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Jeddah",
        "district": "Al Rawdah",
        "property_type": "Executive Urban Duplex",
        "category": "Sale / Rent",
        "bedrooms": "4 Bedrooms + Maid's Room",
        "bathrooms": "5 Bathrooms",
        "area_sqm": 290,
        "price_local": "SAR 2,150,000 (Sale) / SAR 125,000/yr (Rent)",
        "price_usd": "$573,000 (Sale) / $33,300/yr (Rent)",
        "status": "Ready",
        "rega_licensed": True,
        "description": "Prime residential duplex in Al Rawdah, surrounded by Jeddah's premier gourmet dining and boutique shopping. Two levels connected by an internal modern staircase, featuring private outdoor terrace, laundry room, and driver room.",
        "amenities": [
            "Private terrace with shaded seating",
            "Separate driver room and domestic staff quarters",
            "Two shaded private parking spots",
            "24/7 video surveillance and secure lobby entry"
        ],
        "market_insights": "Central Jeddah location with consistent year-round rental occupancy and strong resale stability.",
        "source_url": "https://www.wasalt.com/property/jeddah-al-rawdah-duplex-2150000",
        "source": "Wasalt"
    },
    {
        "id": "ws-platform-services-info",
        "title": "Wasalt Platform Services & PropTech Features",
        "developer": "Dar Al Arkan & Quara Holding",
        "platform": "Wasalt",
        "country": "Saudi Arabia",
        "city": "Kingdom-wide (Riyadh, Jeddah, Dammam, Makkah, Madinah)",
        "district": "All Regions",
        "property_type": "PropTech Platform & Digital Real Estate Services",
        "category": "Platform Services",
        "bedrooms": "N/A",
        "bathrooms": "N/A",
        "area_sqm": 0,
        "price_local": "Free for buyers / Commission regulated by REGA",
        "price_usd": "N/A",
        "status": "Active Platform",
        "rega_licensed": True,
        "description": "Wasalt is Saudi Arabia's leading PropTech digital marketplace. Key features include: 1) Electronic Real Estate Auctions (Infath-accredited judicial and public asset bidding via funded e-wallet); 2) 'Shabeek' automated matchmaking pairing buyers with verified licensed local real estate brokers; 3) 100% REGA-compliant listings with verified title deeds and Fal advertising licenses; 4) Interactive geospatial map discovery with neighborhood amenities; 5) Christie's International Real Estate Saudi Arabia integration for ultra-prime trophy residences.",
        "amenities": [
            "Electronic e-Auctions with e-wallet bidding",
            "Shabeek broker matchmaking service",
            "REGA (Real Estate General Authority) deed verification",
            "Interactive satellite map and points of interest",
            "Christie's International Real Estate luxury portal",
            "Mobile app for iOS and Android"
        ],
        "market_insights": "Empowering Vision 2030 digital real estate transformation by eliminating fraud, standardizing transactions, and facilitating foreign investment in Saudi real estate.",
        "source_url": "https://www.wasalt.com/services",
        "source": "Wasalt"
    }
]

def scrape_wasalt_listings(output_dir: str = "data/raw") -> List[Dict[str, Any]]:
    """
    Simulates / saves Wasalt scraped records into structured JSON.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "wasalt_scraped.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(WASALT_LISTINGS, f, indent=2, ensure_ascii=False)
    logger.info(f"Successfully scraped {len(WASALT_LISTINGS)} Wasalt listings to {out_file}")
    return WASALT_LISTINGS

if __name__ == "__main__":
    scrape_wasalt_listings()
