"""
Professional Luxury Theme Styling for DarGlobal & Wasalt Real Estate AI.
Engineered for high-contrast readability, polished dark aesthetic, and executive presentation.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Cinzel:wght@600;700&display=swap');

/* Base Styles & Typography */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #e2e8f0 !important;
}

.stApp {
    background-color: #070b14 !important;
}

/* Hide Default Streamlit Menus & Footers */
#MainMenu, footer, header {
    visibility: hidden;
}

/* ========================================================
   TOP BRAND BANNER (HERO)
   ======================================================== */
.hero-container {
    background: linear-gradient(135deg, #0e1526 0%, #090e1a 100%);
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 16px;
    padding: 1.8rem 2rem 1.6rem 2rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    position: relative;
    overflow: hidden;
}

.hero-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #c5a059, #f7e7b4, #c5a059);
}

.hero-top-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 0.8rem;
}

.brand-badge-group {
    display: flex;
    gap: 0.6rem;
    align-items: center;
}

.badge-darglobal {
    background: rgba(212, 175, 55, 0.15);
    color: #fae8b4;
    border: 1px solid rgba(212, 175, 55, 0.4);
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 1px;
}

.badge-wasalt {
    background: rgba(56, 189, 248, 0.15);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.4);
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 1px;
}

.badge-engine-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #6ee7b7;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}

.pulse-circle {
    width: 8px;
    height: 8px;
    background-color: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 8px #10b981;
}

.hero-headline {
    font-family: 'Cinzel', serif !important;
    font-size: 2.1rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 1px;
    margin: 0.3rem 0 0.5rem 0;
    background: linear-gradient(135deg, #ffffff 0%, #fae8b4 50%, #d4af37 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtext {
    font-size: 0.95rem;
    color: #94a3b8;
    line-height: 1.6;
    margin: 0;
    max-width: 900px;
}

/* ========================================================
   SIDEBAR STYLING
   ======================================================== */
section[data-testid="stSidebar"] {
    background-color: #0a0f1d !important;
    border-right: 1px solid rgba(212, 175, 55, 0.2) !important;
}

.sidebar-header-box {
    background: #0f172a;
    border: 1px solid rgba(212, 175, 55, 0.25);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    margin-bottom: 1.4rem;
}

.sidebar-brand-name {
    font-family: 'Cinzel', serif !important;
    font-size: 1.15rem;
    color: #fae8b4;
    letter-spacing: 1.5px;
    margin: 0;
}

.sidebar-brand-sub {
    font-size: 0.72rem;
    color: #38bdf8;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 0.2rem;
}

/* Dynamic Live Sync Box in Sidebar */
.sync-card {
    background: #0b1120;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 10px;
    padding: 0.8rem;
    margin-bottom: 1.2rem;
}

.sync-status-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.78rem;
    font-weight: 700;
    color: #6ee7b7;
    margin-bottom: 0.3rem;
}

.sync-time-label {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-bottom: 0.5rem;
}

/* Sidebar Stats Grid */
.stats-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
    margin-bottom: 1.4rem;
}

.stat-item {
    background: #0e1526;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 0.75rem 0.5rem;
    text-align: center;
}

.stat-num {
    font-size: 1.3rem;
    font-weight: 800;
    color: #f7e7b4;
}

.stat-desc {
    font-size: 0.68rem;
    color: #94a3b8;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-top: 0.2rem;
}

/* Sidebar Inputs & Controls */
div[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}

/* Quick Inquiry Buttons */
.stButton button {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 0.85rem !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
}

.stButton button:hover {
    background: #1e293b !important;
    border-color: #d4af37 !important;
    color: #fae8b4 !important;
    transform: translateY(-1px) !important;
}

/* ========================================================
   CHAT CONTAINER & MESSAGES (HIGH CONTRAST)
   ======================================================== */
.stChatMessage {
    background-color: #0c1220 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    padding: 1.2rem 1.4rem !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

/* User Bubble */
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
    background-color: #111a30 !important;
    border-left: 4px solid #6366f1 !important;
}

/* Assistant Bubble */
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
    background-color: #0b111e !important;
    border-left: 4px solid #d4af37 !important;
}

.stChatMessage p, .stChatMessage li, .stChatMessage span {
    color: #e2e8f0 !important;
    line-height: 1.65 !important;
    font-size: 0.95rem !important;
}

.stChatMessage h1, .stChatMessage h2, .stChatMessage h3, .stChatMessage h4 {
    color: #fae8b4 !important;
    font-weight: 700 !important;
    margin: 0.8rem 0 0.4rem 0 !important;
}

.stChatMessage strong {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* ========================================================
   LUXURY PROPERTY CARDS (HIGH CONTRAST & READABLE)
   ======================================================== */
.property-card-lux {
    background: #0f1628;
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 14px;
    padding: 1.3rem;
    margin: 1rem 0;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    position: relative;
    transition: all 0.25s ease;
}

.property-card-lux:hover {
    border-color: #f7e7b4;
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(212, 175, 55, 0.15);
}

.card-top-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.6rem;
    flex-wrap: wrap;
}

.card-title {
    font-size: 1.18rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    line-height: 1.3;
}

.card-badge-darglobal {
    background: rgba(212, 175, 55, 0.18);
    color: #fae8b4;
    border: 1px solid rgba(212, 175, 55, 0.45);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.25rem 0.65rem;
    border-radius: 6px;
    letter-spacing: 0.6px;
}

.card-badge-wasalt {
    background: rgba(56, 189, 248, 0.18);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.45);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.25rem 0.65rem;
    border-radius: 6px;
    letter-spacing: 0.6px;
}

.card-price-badge {
    display: inline-flex;
    align-items: baseline;
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
    font-size: 1.15rem;
    font-weight: 800;
    padding: 0.3rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 0.8rem;
}

.card-price-usd {
    font-size: 0.85rem;
    font-weight: 500;
    color: #94a3b8;
    margin-left: 0.4rem;
}

.card-info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.5rem;
    background: #080d1a;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 0.75rem 0.9rem;
    margin-bottom: 0.8rem;
}

.info-item {
    font-size: 0.83rem;
    color: #cbd5e1;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

.info-item strong {
    color: #94a3b8;
    font-weight: 500;
}

.card-desc {
    font-size: 0.86rem;
    color: #cbd5e1;
    line-height: 1.5;
    margin-bottom: 0.8rem;
}

.card-chips-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-bottom: 0.9rem;
}

.amenity-chip {
    background: #141d33;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #94a3b8;
    font-size: 0.74rem;
    padding: 0.2rem 0.55rem;
    border-radius: 12px;
}

.btn-card-cta {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(135deg, #d4af37 0%, #aa8214 100%);
    color: #070b14 !important;
    font-size: 0.82rem;
    font-weight: 700;
    padding: 0.45rem 1rem;
    border-radius: 6px;
    text-decoration: none !important;
    transition: all 0.2s ease;
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.btn-card-cta:hover {
    background: #fae8b4;
    transform: translateY(-1px);
}

/* ========================================================
   CHAT INPUT BAR & TABS
   ======================================================== */
div[data-testid="stChatInput"] {
    background: #0d1424 !important;
    border: 1px solid rgba(212, 175, 55, 0.3) !important;
    border-radius: 12px !important;
}

div[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: #0a0f1d !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    padding: 0.35rem !important;
    gap: 0.5rem !important;
}

.stTabs [data-baseweb="tab"] {
    color: #94a3b8 !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.1rem !important;
    border-radius: 8px !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(212, 175, 55, 0.2) !important;
    color: #fae8b4 !important;
    border: 1px solid rgba(212, 175, 55, 0.4) !important;
}
</style>
"""
