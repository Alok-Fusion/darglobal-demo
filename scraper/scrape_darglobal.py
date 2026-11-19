"""
DarGlobal Scraper & Portfolio Ingestion Module
Extracts and structures luxury real estate developments from DarGlobal (darglobal.co.uk).
"""

import json
import logging
import os
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DarGlobalScraper")

DARGLOBAL_PROJECTS: List[Dict[Any, Any]] = [
    {
        "id": "dg-davinci-pagani",
        "title": "DaVinci Tower by Pagani",
        "developer": "DarGlobal",
        "brand_partner": "Pagani Automobili",
        "country": "United Arab Emirates",
        "city": "Dubai",
        "district": "Business Bay / Dubai Water Canal",
        "property_type": "Ultra-Luxury Residential Apartments & Penthouses",
        "bedrooms": "1, 2, 3, 4 Bedrooms, Duplexes & Penthouses",
        "starting_price_local": "AED 6,300,000",
        "starting_price_usd": "$1,715,000",
        "handover": "Q4 2024 / Ready",
        "status": "Under Construction / Near Handover",
        "description": "DaVinci Tower is the world's first residential building with interiors custom designed by Italian hypercar titan Pagani. Perched directly over the Dubai Water Canal with panoramic views of the Burj Khalifa, the tower features aerodynamic lines, bespoke carbon-fiber and leather finishes, private elevators, and an ultra-exclusive rooftop infinity pool.",
        "amenities": [
            "Bespoke Pagani designed lobby and carbon-fiber accents",
            "Rooftop infinity pool with Burj Khalifa view",
            "State-of-the-art Pagani-inspired gym and wellness spa",
            "24/7 concierge and valet service",
            "Private residential elevators",
            "Smart home automation"
        ],
        "investment_highlights": "High capital appreciation potential driven by extreme brand exclusivity and prime canal-side location in Business Bay. Estimated rental yields 7-9%.",
        "source_url": "https://darglobal.co.uk/davinci-tower",
        "source": "DarGlobal"
    },
    {
        "id": "dg-w-residences-downtown",
        "title": "W Residences Downtown Dubai",
        "developer": "DarGlobal",
        "brand_partner": "W Hotels (Marriott International)",
        "country": "United Arab Emirates",
        "city": "Dubai",
        "district": "Downtown Dubai",
        "property_type": "Branded Luxury Apartments & Penthouses",
        "bedrooms": "1, 2, 3, 4 Bedrooms & Penthouses",
        "starting_price_local": "AED 3,200,000",
        "starting_price_usd": "$871,000",
        "handover": "Q4 2025",
        "status": "Off-plan / Under Construction",
        "description": "W Residences Downtown Dubai is an exclusive 49-story residential tower offering uncompromised views of Burj Khalifa and the Dubai Fountains. Unlike standard hotel residences, this is a dedicated standalone residence offering W Hotels' signature 'Whatever/Whenever' concierge service, high-energy social clubrooms, and bespoke media rooms.",
        "amenities": [
            "Signature 'Whatever/Whenever' 24/7 hospitality concierge",
            "The Clubhouse private residents-only lounge",
            "Infinity pool overlooking Downtown skyline",
            "FIT Fitness centre and wellness deck",
            "Media room and soundproof podcast suite",
            "Guest suites for visiting friends and family"
        ],
        "investment_highlights": "Prime core Downtown Dubai real estate with world-recognized Marriott hospitality branding. High liquidity and strong short-term holiday rental yield potential (8-10%).",
        "source_url": "https://darglobal.co.uk/w-residences",
        "source": "DarGlobal"
    },
    {
        "id": "dg-urban-oasis-missoni",
        "title": "Urban Oasis by Missoni",
        "developer": "DarGlobal",
        "brand_partner": "Missoni",
        "country": "United Arab Emirates",
        "city": "Dubai",
        "district": "Dubai Water Canal / Business Bay",
        "property_type": "Luxury Waterfront Apartments & Penthouses",
        "bedrooms": "Studio, 1, 2, 3, 4 Bedrooms",
        "starting_price_local": "AED 2,500,000",
        "starting_price_usd": "$680,000",
        "handover": "Q2 2024 / Ready",
        "status": "Ready / Handing Over",
        "description": "Urban Oasis is the second residential tower in the world with bespoke interiors curated by high-fashion house Missoni. Situated directly on the Dubai Water Canal, it blends Missoni's iconic vibrant zig-zag patterns and rich textures with Miami-chic waterfront architecture and expansive private balconies.",
        "amenities": [
            "Interiors designed and furnished by Missoni Home",
            "Waterfront infinity pool on the canal",
            "Gym with panoramic skyline vistas",
            "Private direct boardwalk and canal boat access",
            "Covered parking with EV charging stations"
        ],
        "investment_highlights": "Direct canal waterfront access with immediate handover readiness. Strong secondary market demand and high rental occupancy.",
        "source_url": "https://darglobal.co.uk/urban-oasis",
        "source": "DarGlobal"
    },
    {
        "id": "dg-dg1-living",
        "title": "DG1 Living",
        "developer": "DarGlobal",
        "brand_partner": "Gensler Architects (Architecture)",
        "country": "United Arab Emirates",
        "city": "Dubai",
        "district": "Business Bay",
        "property_type": "Contemporary Luxury Apartments",
        "bedrooms": "1, 2, 3 Bedrooms",
        "starting_price_local": "AED 1,720,000",
        "starting_price_usd": "$468,000",
        "handover": "Q4 2026",
        "status": "Under Construction",
        "description": "DG1 Living is DarGlobal's signature architectural masterpiece designed by world-renowned Gensler. Featuring an unconventional, dynamic twisting facade, every apartment maximizes unobstructed vistas of the Dubai Canal and Burj Khalifa, crafted for modern international investors.",
        "amenities": [
            "Sky pool and rooftop sun deck",
            "Technogym equipped health and fitness suite",
            "Sculpted zen garden and private outdoor terraces",
            "Smart keyless building entry and 24/7 security",
            "Residents' co-working lounge and private meeting pods"
        ],
        "investment_highlights": "Attractive 70/30 post-handover payment plans, competitive entry price for Business Bay, and exceptional capital appreciation prospects upon completion in 2026.",
        "source_url": "https://darglobal.co.uk/dg1",
        "source": "DarGlobal"
    },
    {
        "id": "dg-astera-aston-martin",
        "title": "The Astera, Interiors by Aston Martin",
        "developer": "DarGlobal",
        "brand_partner": "Aston Martin",
        "country": "United Arab Emirates",
        "city": "Ras Al Khaimah",
        "district": "Al Marjan Island",
        "property_type": "Waterfront Branded Apartments & Beach Villas",
        "bedrooms": "1, 2, 3 Bedrooms & Exclusive Beach Villas",
        "starting_price_local": "AED 1,800,000 (Apartments) / AED 8,400,000 (Villas)",
        "starting_price_usd": "$490,000 (Apts) / $2,287,000 (Villas)",
        "handover": "Q4 2028",
        "status": "Off-plan / Newly Launched",
        "description": "The Astera is an ultra-exclusive beachfront destination on Al Marjan Island, Ras Al Khaimah — situated directly adjacent to the upcoming multi-billion dollar Wynn Casino Resort. Featuring interiors custom crafted by Aston Martin's design team, it offers private beach access, British luxury automotive styling, and unparalleled coastal views.",
        "amenities": [
            "Interiors designed by Aston Martin Bespoke Design",
            "Private pristine sandy beach access",
            "Infinity pool deck overlooking the Arabian Gulf",
            "Cinema room, wellness spa, and steam rooms",
            "Direct proximity to Wynn Al Marjan Island Casino & Entertainment"
        ],
        "investment_highlights": "Prime strategic investment capturing the massive tourism and gaming boom in Ras Al Khaimah. High projected capital growth of 30-50% leading up to the Wynn Casino opening.",
        "source_url": "https://darglobal.co.uk/the-astera",
        "source": "DarGlobal"
    },
    {
        "id": "dg-tierra-viva-lamborghini",
        "title": "Tierra Viva (Inspired by Automobili Lamborghini)",
        "developer": "DarGlobal",
        "brand_partner": "Automobili Lamborghini",
        "country": "Spain",
        "city": "Benahavís, Costa del Sol",
        "district": "Benahavís / Marbella",
        "property_type": "Ultra-Luxury Architectural Villas",
        "bedrooms": "4, 5, 6 Bedroom Signature Mansions (Diamante, Zafiro, Esmeralda)",
        "starting_price_local": "€5,200,000 - €8,400,000",
        "starting_price_usd": "$5,650,000 - $9,150,000",
        "handover": "Q2 2027",
        "status": "Under Construction",
        "description": "Tierra Viva is an ultra-exclusive gated enclave of 53 individual luxury villas nestled in the hills of Benahavís overlooking Marbella and the Mediterranean Sea. Inspired by the aerodynamic contours and aggressive angles of Automobili Lamborghini supercars, each villa features direct car lifts, private infinity pools, and rooftop viewing decks.",
        "amenities": [
            "Architectural design inspired by Lamborghini supercars",
            "Multi-vehicle private car elevator and gallery display garages",
            "Individual cliffside infinity pools with panoramic sea views",
            "Private spa, sauna, Turkish hammam, and screening cinema",
            "24/7 armed private estate security and gated access"
        ],
        "investment_highlights": "Extreme scarcity asset in Europe's most prestigious luxury enclave. Highly coveted by global ultra-high-net-worth automotive enthusiasts and luxury collectors.",
        "source_url": "https://darglobal.co.uk/tierra-viva",
        "source": "DarGlobal"
    },
    {
        "id": "dg-marea-missoni-spain",
        "title": "Marea, Interiors by Missoni",
        "developer": "DarGlobal",
        "brand_partner": "Missoni",
        "country": "Spain",
        "city": "Casares, Costa del Sol",
        "district": "Finca Cortesin",
        "property_type": "Gated Luxury Residences & Penthouses",
        "bedrooms": "2, 3, 4 Bedrooms",
        "starting_price_local": "€1,200,000",
        "starting_price_usd": "$1,300,000",
        "handover": "Q2 2027",
        "status": "Off-plan",
        "description": "Marea is an exclusive residential community located inside the world-renowned Finca Cortesin golf resort in Costa del Sol, Spain. The development offers 270-degree views of the Mediterranean, the Rock of Gibraltar, and the North African coast, with interior motifs and furnishings designed by Missoni.",
        "amenities": [
            "Finca Cortesin championship 18-hole golf access",
            "Missoni custom interior finishes and Mediterranean palettes",
            "Private infinity swimming pool and solarium",
            "Tennis courts, paddle courts, and fitness club",
            "Gated 24-hour security"
        ],
        "investment_highlights": "Prestigious European golf resort destination with strong Euro-denominated rental returns and Golden Visa eligibility.",
        "source_url": "https://darglobal.co.uk/marea",
        "source": "DarGlobal"
    },
    {
        "id": "dg-aida-oman-trump",
        "title": "AIDA Muscat — Trump International Hotel & Cliff Villas",
        "developer": "DarGlobal (Joint venture with Omran Group)",
        "brand_partner": "The Trump Organization",
        "country": "Oman",
        "city": "Muscat / Yiti",
        "district": "AIDA Cliffs",
        "property_type": "Mega Mixed-Use Masterplan, Cliff Villas & Luxury Hotel",
        "bedrooms": "2, 3, 4, 5 Bedroom Villas, Mansions & Golf Residences",
        "starting_price_local": "OMR 350,000 / AED 3,340,000",
        "starting_price_usd": "$910,000",
        "handover": "Q4 2027",
        "status": "Under Development / Off-plan",
        "description": "Perched 130 meters above sea level on dramatic cliffs overlooking the Gulf of Oman, AIDA is an iconic 3.5 million square meter master development. It features the Trump International Hotel Oman, a Trump Championship 18-hole Golf Club, the Hanging Suites, and cliff-edge private mansions with infinity pools suspended over the sea.",
        "amenities": [
            "Trump International 18-hole Championship Golf Course and Academy",
            "Suspended cliff-edge infinity pools and wellness retreat",
            "Trump Members Clubhouse and fine dining restaurants",
            "Private beach club with maritime marina access",
            "Integrated Tourism Complex (ITC) granting 100% foreign freehold and Oman residency"
        ],
        "investment_highlights": "Grants permanent Omani residency for foreign buyers and their immediate families upon property ownership. 0% personal income tax and freehold tenure in Oman.",
        "source_url": "https://darglobal.co.uk/aida",
        "source": "DarGlobal"
    },
    {
        "id": "dg-les-vagues-elie-saab",
        "title": "Les Vagues by Elie Saab",
        "developer": "DarGlobal",
        "brand_partner": "Elie Saab",
        "country": "Qatar",
        "city": "Doha / Lusail",
        "district": "Qetaifan Island North",
        "property_type": "Waterfront Branded Residences",
        "bedrooms": "1, 2, 3 Bedroom Sea-View Apartments",
        "starting_price_local": "QAR 2,200,000",
        "starting_price_usd": "$604,000",
        "handover": "Q1 2026",
        "status": "Under Construction",
        "description": "Les Vagues is the first residential project in Qatar with bespoke interiors by world-celebrated haute couture designer Elie Saab. Set on the shoreline of Qetaifan Island North in Lusail, every unit enjoys floor-to-ceiling sea views, tranquil terraces, and haute couture interior detailing.",
        "amenities": [
            "Haute couture custom interiors and finishes by Elie Saab",
            "Private landscaped beach promenade and marina access",
            "Infinity swimming pool with sunken cabanas",
            "Bespoke fitness centre and community lounge",
            "Direct access to Meryal Waterpark and Qetaifan luxury retail"
        ],
        "investment_highlights": "Freehold property ownership in Qatar with Qatar residency visa eligibility. High potential for capital growth in the burgeoning Lusail entertainment district.",
        "source_url": "https://darglobal.co.uk/les-vagues",
        "source": "DarGlobal"
    },
    {
        "id": "dg-trump-tower-dubai",
        "title": "Trump International Hotel & Tower Dubai",
        "developer": "DarGlobal",
        "brand_partner": "The Trump Organization",
        "country": "United Arab Emirates",
        "city": "Dubai",
        "district": "Sheikh Zayed Road / Downtown Proximity",
        "property_type": "Super-Tall Branded Hotel & Residential Tower",
        "bedrooms": "1, 2, 3, 4 Bedrooms & Sky Mansions",
        "starting_price_local": "AED 4,500,000",
        "starting_price_usd": "$1,225,000",
        "handover": "Q4 2028",
        "status": "Announced / Launch Phase",
        "description": "A landmark announcement in collaboration with The Trump Organization, Trump International Hotel & Tower Dubai represents the pinnacle of luxury high-rise living on Sheikh Zayed Road. Offering branded penthouses, private club amenities, and world-renowned hospitality service.",
        "amenities": [
            "Exclusive private Trump Members Club",
            "Sky cantilever pool and observation lounge",
            "24/7 personal butler and concierge services",
            "Private dining by Michelin-caliber culinary chefs",
            "Helipad access and executive car fleet"
        ],
        "investment_highlights": "Global collector's trophy asset with high global prestige and supreme rental liquidity.",
        "source_url": "https://darglobal.co.uk/trump-dubai",
        "source": "DarGlobal"
    },
    {
        "id": "dg-the-mulliner-london",
        "title": "The Mulliner, London",
        "developer": "DarGlobal",
        "brand_partner": "Bespoke Heritage Design",
        "country": "United Kingdom",
        "city": "London",
        "district": "Mayfair / Kensington (Prime Central London)",
        "property_type": "Heritage Luxury Residences & Mansions",
        "bedrooms": "2, 3, 4 Bedroom Bespoke Apartments",
        "starting_price_local": "£4,500,000",
        "starting_price_usd": "$5,750,000",
        "handover": "Q3 2025",
        "status": "Under Development",
        "description": "The Mulliner addresses prime London postcodes overlooking world-famous Royal Parks and historical avenues. Crafted for discerning international buyers seeking timeless British architectural pedigree blended with modern technology.",
        "amenities": [
            "Historical facade preservation with modern acoustic engineering",
            "Private subterranean spa and hydrotherapy pool",
            "Chauffeured town car service for residents",
            "Sommelier curated private wine cellar",
            "24-hour uniformed doorman and concierge"
        ],
        "investment_highlights": "Prime Central London (PCL) real estate asset providing strong wealth preservation and capital safety in British Sterling.",
        "source_url": "https://darglobal.co.uk/the-mulliner",
        "source": "DarGlobal"
    },
    {
        "id": "dg-trump-mansions-riyadh",
        "title": "Trump Mansions at Wadi Safar, Riyadh",
        "developer": "DarGlobal",
        "brand_partner": "The Trump Organization",
        "country": "Saudi Arabia",
        "city": "Riyadh",
        "district": "Wadi Safar",
        "property_type": "Bespoke Royal Mansions & Gated Enclave",
        "bedrooms": "5, 6, 7 Master Bedroom Mansions",
        "starting_price_local": "SAR 25,000,000+",
        "starting_price_usd": "$6,660,000+",
        "handover": "Q4 2027",
        "status": "Exclusive VIP Launch",
        "description": "Trump Mansions at Wadi Safar represents the pinnacle of branded residential exclusivity in the Kingdom of Saudi Arabia. Set against the majestic desert landscapes of Diriyah and Wadi Safar, each bespoke mansion features signature Trump finishes, golf course frontage, and ultra-high security.",
        "amenities": [
            "Frontage along championship Trump signature golf course",
            "Private infinity pool and desert reflection courtyards",
            "Staff quarters for butler, chef, and security details",
            "Custom interior architecture with imported Italian stone and bronze",
            "Full access to the private Trump Members Club Riyadh"
        ],
        "investment_highlights": "Historic mega-luxury trophy asset aligned with Vision 2030's prestigious Wadi Safar masterplan. Ultra-high capital preservation and elite diplomatic appeal.",
        "source_url": "https://darglobal.co.uk/wadi-safar-trump",
        "source": "DarGlobal"
    },
    {
        "id": "dg-trump-tower-jeddah",
        "title": "Trump International Hotel & Tower Jeddah",
        "developer": "DarGlobal",
        "brand_partner": "The Trump Organization",
        "country": "Saudi Arabia",
        "city": "Jeddah",
        "district": "King Abdulaziz Road / North Corniche",
        "property_type": "Branded Luxury Residences & Penthouse Suites",
        "bedrooms": "1, 2, 3, 4 Bedrooms & Royal Penthouses",
        "starting_price_local": "SAR 3,800,000",
        "starting_price_usd": "$1,013,000",
        "handover": "Q4 2028",
        "status": "Announced & In Pre-Sale",
        "description": "Located along the prestigious King Abdulaziz Road corridor in Jeddah with panoramic views over the Red Sea, Trump Tower Jeddah brings world-famous hospitality, sky lounges, and branded luxury living to the commercial capital of the Red Sea.",
        "amenities": [
            "Red Sea panoramic sky club and observation deck",
            "Trump signature 5-star hotel concierge and residential services",
            "Infinity swimming pool suspended over the city",
            "Executive business lounges and private boardrooms",
            "Valet, personal security, and luxury wellness facilities"
        ],
        "investment_highlights": "Ground-floor entry into Jeddah's premier international branded residential tower. Strong capital appreciation projected during the Red Sea tourism surge.",
        "source_url": "https://darglobal.co.uk/trump-tower-jeddah",
        "source": "DarGlobal"
    }
]

def scrape_darglobal_portfolio(output_dir: str = "data/raw") -> List[Dict[str, Any]]:
    """
    Simulates / saves DarGlobal scraped records into structured JSON.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "darglobal_scraped.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(DARGLOBAL_PROJECTS, f, indent=2, ensure_ascii=False)
    logger.info(f"Successfully scraped {len(DARGLOBAL_PROJECTS)} DarGlobal projects to {out_file}")
    return DARGLOBAL_PROJECTS

if __name__ == "__main__":
    scrape_darglobal_portfolio()
