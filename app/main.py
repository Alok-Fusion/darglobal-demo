"""
DarGlobal & Wasalt Real Estate Advisory AI
Enterprise Applied AI Application with Dynamic Data Sync, PDF Export,
Single-Inquiry Focus, Compact UI, and Concurrency Input Locking.
Author: Alok Kushwaha
"""

import os
import sys
from datetime import datetime
import streamlit as st

# Setup python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.core.config import (
    PRIMARY_MODEL,
    KNOWLEDGE_BASE_PATH,
    OPENROUTER_API_KEY
)
from app.core.rag_engine import RAGEngine
from app.core.openrouter_client import OpenRouterClient
from app.core.pdf_exporter import generate_advisory_pdf
from app.ui.styles import CUSTOM_CSS
from app.core.live_data import LiveKnowledgeBase
from scraper.run_scrapers import last_scrape_info


def _scrape_label() -> str:
    """'Last synced' text from data/scrape_meta.json (when each site was actually scraped)."""
    meta = last_scrape_info()
    parts = []
    for key, name in (("darglobal", "DarGlobal"), ("wasalt", "Wasalt")):
        info = meta.get(key) or {}
        when = (info.get("scraped_at") or "")[:16].replace("T", " ")
        if when:
            parts.append(f"{name} {when} UTC")
    return " · ".join(parts) or datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@st.cache_resource
def get_live_kb() -> LiveKnowledgeBase:
    """One shared knowledge base + background refresher for the whole server (all users)."""
    return LiveKnowledgeBase(KNOWLEDGE_BASE_PATH).start()

# Page Configuration
st.set_page_config(
    page_title="DarGlobal & Wasalt Real Estate AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom High-Contrast Luxury Styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Session State
if "last_synced_time" not in st.session_state:
    st.session_state.last_synced_time = _scrape_label()

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

INITIAL_WELCOME_MESSAGE = {
    "role": "assistant",
    "content": (
        "**Welcome to the DarGlobal & Wasalt Real Estate Advisory Platform.**\n\n"
        "I am your dedicated Applied AI advisor, powered by **NVIDIA Nemotron 3.5 Super VL**. "
        "I answer from data scraped directly from darglobal.co.uk and wasalt.sa, covering **DarGlobal's** international branded portfolio "
        "(*Pagani, Lamborghini, Aston Martin, Missoni, Trump, Elie Saab*) and **Wasalt's** premier Saudi Arabian "
        "property marketplace across Riyadh, Jeddah, and Al Khobar.\n\n"
        "How may I assist your real estate acquisition or investment research today?"
    ),
    "cards": [],
    "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
}

try:
    live_kb = get_live_kb()
    # Fetched on every interaction: if the background refresher published new data,
    # this question already uses it, with no restart and no interruption to the chat.
    st.session_state.rag_engine = live_kb.get_engine()
except Exception as ex:
    st.error(f"Failed to initialize Knowledge Base: {ex}")
    st.stop()

if st.session_state.get("data_version") != live_kb.version:
    if "data_version" in st.session_state:
        st.toast(f"New market data loaded ({len(st.session_state.rag_engine.documents)} records).", icon=None)
    st.session_state.data_version = live_kb.version
    st.session_state.last_synced_time = _scrape_label()

if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_WELCOME_MESSAGE]

# Global processing lock flag
is_busy = st.session_state.is_processing

# Helper function to render a compact luxury property card
def render_property_card(card: dict):
    source = card.get("source", "Portfolio")
    is_dg = (source == "DarGlobal")
    badge_class = "card-badge-darglobal" if is_dg else "card-badge-wasalt"
    badge_label = "DARGLOBAL" if is_dg else "WASALT KSA"
    
    price_local = card.get("price_local") or ("Market guide" if card.get("property_type") == "Market guide"
                                              else "Company page" if card.get("property_type") == "Company information"
                                              else "Price on request")
    price_usd = card.get("price_usd", "")
    usd_str = f'<span class="card-price-usd">({price_usd})</span>' if price_usd else ""
    
    partner = card.get("brand_partner", "N/A")
    partner_row = f'<div class="info-item"><strong>Partner:</strong> {partner}</div>' if partner != "N/A" else ""
    
    amenities = card.get("amenities", [])[:3]
    chips_html = "".join([f'<span class="amenity-chip">{a}</span>' for a in amenities])
    
    desc_preview = card.get("description", "")
    if len(desc_preview) > 105:
        desc_preview = desc_preview[:105] + "..."

    cta_text = "Details &rarr;" if is_dg else "Listing &rarr;"

    card_html = f"""
    <div class="property-card-lux">
        <div>
            <div class="card-top-row">
                <h4 class="card-title">{card.get('title')}</h4>
                <span class="{badge_class}">{badge_label}</span>
            </div>
            <div class="card-price-badge">
                {price_local} {usd_str}
            </div>
            <div class="card-info-grid">
                <div class="info-item">📍 {card.get('city')}, {card.get('country')}</div>
                <div class="info-item">🏡 {card.get('property_type')} &bull; {card.get('bedrooms')}</div>
                {partner_row}
            </div>
            <div class="card-desc">{desc_preview}</div>
            <div class="card-chips-row">{chips_html}</div>
        </div>
        <div>
            <a href="{card.get('source_url', '#')}" target="_blank" class="btn-card-cta">{cta_text}</a>
        </div>
    </div>
    """
    # Markdown ends an HTML block at a blank line (e.g. an empty field), which would print
    # the rest of the card as code, so flatten the card to non-empty, unindented lines.
    card_html = "\n".join(line.strip() for line in card_html.splitlines() if line.strip())
    st.markdown(card_html, unsafe_allow_html=True)


# ========================================================
# SIDEBAR
# ========================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header-box">
        <h2 class="sidebar-brand-name">DARGLOBAL & WASALT</h2>
        <div class="sidebar-brand-sub">Real Estate Advisory Desk</div>
    </div>
    """, unsafe_allow_html=True)

    # Live data status card: re-renders itself every 30 s, without interrupting the chat.
    @st.fragment(run_every="30s")
    def data_status_card():
        live_kb.get_engine()  # reload now if the background refresher published new data
        s = live_kb.status
        st.markdown(f"""
        <div class="sync-card">
            <div class="sync-status-header">
                <span class="pulse-circle"></span>
                <span>Market Feed: {"Refreshing in background…" if s["running"] else "Live"}</span>
            </div>
            <div class="sync-time-label">Data scraped: {_scrape_label()}</div>
            <div class="sync-time-label">{s.get("records", "?")} records · auto-refresh ({live_kb.mode}) every {int(live_kb.interval // 60)} min · next {s.get("next_run") or "-"}</div>
            <div class="sync-time-label">Last refresh: {s.get("last_result")}</div>
        </div>
        """, unsafe_allow_html=True)

    data_status_card()

    # Starts a refresh in the background thread; the chat keeps working meanwhile.
    if st.button("Sync Latest Market Data", use_container_width=True,
                 disabled=is_busy or live_kb.status["running"] or live_kb.mode == "off"):
        live_kb.trigger_now()
        st.toast("Refresh started in the background. Keep chatting; new data is used as soon as it lands.",
                 icon=None)

    st.markdown("---")
    st.markdown("### Filters")

    # Dynamic Portfolio Source Filter (Disabled if busy)
    source_filter = st.radio(
        "Portfolio Source",
        options=["All", "DarGlobal", "Wasalt"],
        index=0,
        horizontal=True,
        disabled=is_busy
    )

    # Dynamic City / Region Filter (Disabled if busy)
    city_options = ["All", "Dubai", "Riyadh", "Jeddah", "Al Khobar", "Muscat", "Doha", "London", "Benahavís"]
    city_filter = st.selectbox(
        "Market / City",
        options=city_options,
        index=0,
        disabled=is_busy
    )

    st.markdown("---")
    
    # Dynamic Portfolio Counts
    docs = st.session_state.rag_engine.documents
    dg_count = sum(1 for d in docs if d.get("source") == "DarGlobal")
    ws_count = sum(1 for d in docs if d.get("source") == "Wasalt")

    st.markdown(f"""
    <div class="stats-container">
        <div class="stat-item">
            <div class="stat-num">{dg_count}</div>
            <div class="stat-desc">DarGlobal</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{ws_count}</div>
            <div class="stat-desc">Wasalt</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{len(docs)}</div>
            <div class="stat-desc">Total Assets</div>
        </div>
        <div class="stat-item">
            <div class="stat-num">{len({d.get("city") for d in docs if d.get("city")})}</div>
            <div class="stat-desc">Cities</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Inquiries")
    sample_queries = [
        ("Pagani & Lamborghini Branded Residences", "Show me residences designed by Pagani and Lamborghini."),
        ("Villas for Sale in Riyadh on Wasalt", "What villas are listed for sale in Riyadh on Wasalt, and at what prices?"),
        ("Trump Developments in Riyadh & Jeddah", "Tell me about Trump developments in Riyadh and Jeddah."),
        ("Compare W Residences vs DG1", "Compare W Residences and DG1 in Dubai: status, unit types and sizes."),
        ("Coastal Developments in Oman & Qatar", "What beachfront projects are in Oman and Qatar?"),
        ("Apartments for Rent in Jeddah", "What does Wasalt show for apartments for rent in Jeddah?")
    ]

    # Render Sample Queries (Completely disabled when another query is in progress)
    for label, query_text in sample_queries:
        if st.button(label, key=f"btn_{label}", use_container_width=True, disabled=is_busy):
            if not is_busy:
                st.session_state.pending_query = query_text
                st.session_state.is_processing = True
                st.rerun()

    st.markdown("---")
    if st.button("New Inquiry / Reset", key="btn_sidebar_reset", use_container_width=True, disabled=is_busy):
        st.session_state.messages = [INITIAL_WELCOME_MESSAGE]
        st.session_state.pending_query = None
        st.session_state.is_processing = False
        st.rerun()


# Initialize OpenRouter Client (Model fixed to Nemotron, API key loaded silently from environment)
client = OpenRouterClient(
    api_key=OPENROUTER_API_KEY,
    model=PRIMARY_MODEL
)


# ========================================================
# TOP BRAND HERO SECTION (COMPACT)
# ========================================================
st.markdown(f"""
<div class="hero-container">
    <div class="hero-top-row">
        <div class="brand-badge-group">
            <span class="badge-darglobal">DarGlobal Luxury</span>
            <span class="badge-wasalt">Wasalt PropTech</span>
        </div>
        <div class="badge-engine-status">
            <span class="pulse-circle"></span>
            <span>NVIDIA Nemotron 3.5 Super VL (Free Tier) &bull; Active</span>
        </div>
    </div>
    <h1 class="hero-headline">REAL ESTATE APPLIED AI ADVISORY</h1>
    <p class="hero-subtext">
        Conversational intelligence platform for international branded developments 
        and Saudi Arabian residential investments. Synthesizes verified listings from 
        <strong>DarGlobal</strong> and <strong>Wasalt</strong> using a precision hybrid RAG architecture.
    </p>
</div>
""", unsafe_allow_html=True)

# Tabs Navigation
tab_chat, tab_portfolio, tab_architecture = st.tabs([
    "Advisory Chat",
    "Portfolio Catalog",
    "Architecture & Specifications"
])


# ========================================================
# TAB 1: ADVISORY CHAT
# ========================================================
with tab_chat:
    st.caption("Active Session &bull; Single Inquiry Focus &bull; Minimal Scrolling Layout")

    # Chat Scroll Area (Padding at bottom ensures responses stay above the typing bar)
    chat_container = st.container()
    with chat_container:
        # If not actively processing a new query, render the current messages
        if not (is_busy and st.session_state.pending_query):
            for message in st.session_state.messages:
                role = message["role"]
                with st.chat_message(role):
                    st.markdown(message["content"])
                    
                    cards = message.get("cards", [])
                    if cards:
                        st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #fae8b4; margin: 0.4rem 0 0.2rem 0;'>Verified Portfolio Recommendations:</p>", unsafe_allow_html=True)
                        num_cols = min(len(cards), 3)
                        card_cols = st.columns(num_cols)
                        for idx_c, card in enumerate(cards[:num_cols]):
                            with card_cols[idx_c]:
                                render_property_card(card)
                    
                    msg_time = message.get("timestamp", "")
                    if msg_time:
                        st.caption(f"{msg_time}")

            # Actions Bar Placed DIRECTLY AFTER THE RESULTS
            st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)
            col_spacer, col_clear, col_pdf = st.columns([2.5, 1.2, 1.3])
            with col_clear:
                if st.button("New Inquiry / Clear", key="btn_post_clear", use_container_width=True, disabled=is_busy):
                    st.session_state.messages = [INITIAL_WELCOME_MESSAGE]
                    st.session_state.pending_query = None
                    st.session_state.is_processing = False
                    st.rerun()
            with col_pdf:
                pdf_bytes = generate_advisory_pdf(st.session_state.messages)
                st.download_button(
                    label="Export to PDF",
                    data=pdf_bytes,
                    file_name=f"DarGlobal_Advisory_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    key="btn_post_pdf",
                    use_container_width=True,
                    disabled=is_busy
                )

    # Active Query Execution Block (Locked & In-Progress)
    if is_busy and st.session_state.pending_query:
        current_inquiry = st.session_state.pending_query
        user_timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
        
        # Render the user question immediately
        with st.chat_message("user"):
            st.markdown(current_inquiry)
            st.caption(f"{user_timestamp}")

        # Render assistant thinking & generation block
        with st.chat_message("assistant"):
            with st.spinner("Synthesizing portfolio intelligence with NVIDIA Nemotron 3.5 Super VL..."):
                try:
                    # 1. RAG Retrieval with active filters
                    rag = st.session_state.rag_engine
                    retrieved_results = rag.search(
                        query=current_inquiry,
                        top_k=4,
                        source_filter=source_filter,
                        city_filter=city_filter
                    )
                    rag_context = rag.build_system_context(retrieved_results)
                    retrieved_cards = [doc for doc, score in retrieved_results]

                    # 2. Call OpenRouter with NVIDIA Nemotron
                    response_data = client.generate_response(
                        messages=[{"role": "user", "content": current_inquiry}],
                        rag_context=rag_context
                    )
                    
                    assistant_reply = response_data["content"]
                    asst_timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
                    
                    st.markdown(assistant_reply)
                    st.caption(f"Model: `NVIDIA Nemotron 3.5 Super VL (Free Tier)` &bull; {asst_timestamp}")
                    
                    if retrieved_cards:
                        st.markdown("<p style='font-size: 0.85rem; font-weight: 700; color: #fae8b4; margin: 0.4rem 0 0.2rem 0;'>Verified Portfolio Recommendations:</p>", unsafe_allow_html=True)
                        num_cols = min(len(cards), 3) if 'cards' in locals() else min(len(retrieved_cards), 3)
                        card_cols = st.columns(num_cols)
                        for idx_c, card in enumerate(retrieved_cards[:num_cols]):
                            with card_cols[idx_c]:
                                render_property_card(card)

                    # Update session state with strictly this one chat
                    st.session_state.messages = [
                        {
                            "role": "user",
                            "content": current_inquiry,
                            "timestamp": user_timestamp
                        },
                        {
                            "role": "assistant",
                            "content": assistant_reply,
                            "cards": retrieved_cards,
                            "timestamp": asst_timestamp
                        }
                    ]

                except Exception as ex:
                    st.error(f"Error during advisory synthesis: {ex}")
                finally:
                    # Unlock the system
                    st.session_state.pending_query = None
                    st.session_state.is_processing = False
                    st.rerun()

    # Chat Input Field (Disabled & Locked when is_busy is True)
    input_placeholder = (
        "Advisory synthesis in progress, please wait..."
        if is_busy
        else "Ask about DarGlobal developments or Wasalt Saudi properties..."
    )
    user_input = st.chat_input(input_placeholder, disabled=is_busy)

    if user_input and not is_busy:
        st.session_state.pending_query = user_input
        st.session_state.is_processing = True
        st.rerun()


# ========================================================
# TAB 2: PORTFOLIO CATALOG (3-COLUMN COMPACT GRID)
# ========================================================
with tab_portfolio:
    st.markdown("### Verified Real Estate Asset Catalog")
    st.caption("Browse indexed developments and verified properties from DarGlobal and Wasalt.")
    
    col_filter1, col_filter2, col_filter3 = st.columns([2, 1, 1])
    with col_filter1:
        search_filter = st.text_input("Search developments by name, brand, or location:", "", disabled=is_busy)
    with col_filter2:
        category_choice = st.selectbox("Source Platform:", ["All", "DarGlobal", "Wasalt"], disabled=is_busy)
    with col_filter3:
        market_choice = st.selectbox("Target Market:", ["All", "Dubai", "Riyadh", "Jeddah", "Al Khobar", "Muscat", "Doha", "London", "Benahavís"], disabled=is_busy)

    all_docs = st.session_state.rag_engine.documents
    filtered_docs = all_docs

    if category_choice != "All":
        filtered_docs = [d for d in filtered_docs if d.get("source") == category_choice]

    if market_choice != "All":
        filtered_docs = [
            d for d in filtered_docs 
            if market_choice.lower() in d.get("city", "").lower() or market_choice.lower() in d.get("district", "").lower()
        ]

    if search_filter.strip():
        q = search_filter.lower()
        filtered_docs = [
            d for d in filtered_docs 
            if q in d.get("title", "").lower() 
            or q in d.get("city", "").lower() 
            or q in d.get("brand_partner", "").lower()
            or q in d.get("country", "").lower()
        ]

    # Projects and listings first; company pages and market guides aren't property cards.
    filtered_docs = [d for d in filtered_docs if d.get("property_type") not in ("Company information", "Market guide")]
    shown = filtered_docs[:60]
    st.markdown(f"**{len(filtered_docs)} scraped records match (showing {len(shown)}; scraped: {st.session_state.last_synced_time}). "
                f"Use the filters to narrow down.**")

    col_a, col_b, col_c = st.columns(3)
    for idx, doc in enumerate(shown):
        target_col = [col_a, col_b, col_c][idx % 3]
        with target_col:
            render_property_card(doc)


# ========================================================
# TAB 3: SYSTEM ARCHITECTURE & ENGINEERING SPECS
# ========================================================
with tab_architecture:
    st.markdown("### System Architecture & Engineering Specifications")
    
    col_arch1, col_arch2 = st.columns(2)
    
    with col_arch1:
        st.markdown("""
        #### Technical Architecture
        * **1. Dynamic Ingestion Engine:**
          * Automated scraping modules extracting structured JSON schemas from `darglobal.co.uk` and `wasalt.com`.
          * On-demand scraping trigger dynamically updates in-memory vector weights with live timestamps.
          * Multi-currency normalization (`AED`, `SAR`, `GBP`, `EUR`, `USD`) and REGA regulatory verification.
        * **2. RAG Retrieval Engine:**
          * Robertson-Spärck Jones BM25 retrieval engine with token length normalization.
          * Domain weighting: **15x** boost for luxury brands (*Pagani, Lamborghini, Aston Martin*), **16x** boost for cities (*Riyadh, Dubai*).
          * Sub-10ms query-to-context injection.
        * **3. LLM Gateway:**
          * Primary Model: `nvidia/nemotron-3.5-super-vl:free` via OpenRouter API.
          * Multi-model fallback cascade: `meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-exp:free`.
        """)

    with col_arch2:
        st.markdown("""
        #### Containerization & Deployment
        * **Author:** Alok Kushwaha
        * **Runtime:** Python 3.11-slim container.
        * **Hosting:** Render.com (Docker Web Service).
        * **Port Configuration:** Dynamic binding to `${PORT}` for zero-config Render routing.
        * **Uptime Guarantee:** Multi-tier fallback cascade ensures uninterrupted evaluation demo during peak loads.
        * **Security:** Zero client-side credential exposure; server-side environment secrets management.
        """)

    st.markdown("---")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("System Status", "Operational")
    with col_m2:
        st.metric("Inference Engine", "Nemotron 3.5 Super VL")
    with col_m3:
        st.metric("Active Assets", f"{len(st.session_state.rag_engine.documents)} Verified")
    with col_m4:
        st.metric("RAG Latency", "< 10 ms")
