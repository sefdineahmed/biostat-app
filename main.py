import streamlit as st
from onglets import accueil, analyse_descriptive, modelisation, registre, kpi, a_propos

st.set_page_config(
    page_title="SHAHIDI AI — Plateforme Oncologie",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global sidebar + background ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── APP BACKGROUND ─────────────────────────────────────────────────────── */
/* Dégradé doux bleu-ardoise médical, non agressif pour les yeux */
[data-testid="stAppViewContainer"] {
    background:
        linear-gradient(160deg,
            #eef3fb 0%,
            #e8f0fc 25%,
            #f0f5fd 50%,
            #e6eef9 75%,
            #edf3fb 100%) !important;
}

/* Overlay texture subtile (points) */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image:
        radial-gradient(circle, rgba(26,79,196,0.04) 1px, transparent 1px);
    background-size: 28px 28px;
}

/* Bandes médicales décoratives en arrière-plan */
[data-testid="stAppViewContainer"]::after {
    content: '';
    position: fixed;
    top: -80px; right: -120px;
    width: 520px; height: 520px;
    border-radius: 50%;
    background: radial-gradient(circle,
        rgba(26,79,196,0.07) 0%,
        rgba(0,198,255,0.04) 50%,
        transparent 70%);
    pointer-events: none; z-index: 0;
}

/* Second orbe décoratif */
[data-testid="stMain"]::before {
    content: '';
    position: fixed;
    bottom: -100px; left: 200px;
    width: 400px; height: 400px;
    border-radius: 50%;
    background: radial-gradient(circle,
        rgba(0,198,255,0.06) 0%,
        rgba(26,79,196,0.03) 50%,
        transparent 70%);
    pointer-events: none; z-index: 0;
}

/* Contenu au-dessus des orbes */
[data-testid="block-container"],
[data-testid="stSidebar"] { position: relative; z-index: 1; }

/* ── SIDEBAR ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #07102a 0%, #0c1d42 55%, #0f2352 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* Textes sidebar */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div { color: #c4d4f0 !important; }

/* Radio buttons */
[data-testid="stSidebar"] [data-baseweb="radio"] label {
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 7px 10px !important;
    border-radius: 8px !important;
    transition: background .15s;
}
[data-testid="stSidebar"] [data-baseweb="radio"] label:hover {
    background: rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] [aria-checked="true"] > div:first-child {
    background-color: #1a4fc4 !important;
    border-color: #1a4fc4 !important;
}

/* Selectbox sidebar */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
}

/* Divider */
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 10px 0 !important;
}

/* ── MAIN CONTENT ─────────────────────────────────────────────────────────── */
#MainMenu, footer { visibility: hidden; }
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1280px !important;
}
html, body, [class*="css"] { font-family: 'Sora', sans-serif !important; }

/* Metrics */
[data-testid="stMetric"] {
    background: white;
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    border: 1px solid #e2eaf8;
    box-shadow: 0 2px 12px rgba(26,79,196,0.07);
}
[data-testid="stMetricLabel"] {
    font-size: 11px !important; color: #6b7a9d !important;
    text-transform: uppercase; letter-spacing: 0.07em;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.9rem !important; color: #0d1b3e !important; font-weight: 600 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(240,244,251,0.85); border-radius: 10px; padding: 4px; gap: 2px;
    backdrop-filter: blur(8px);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border-radius: 8px !important;
    font-size: 13px !important; font-weight: 500 !important;
    color: #6b7a9d !important; padding: 8px 18px !important;
}
.stTabs [aria-selected="true"] {
    background: white !important; color: #1a4fc4 !important;
    box-shadow: 0 2px 8px rgba(26,79,196,0.12) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1a4fc4, #00a8e8) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 14px !important;
    padding: 0.55rem 1.4rem !important; transition: all 0.2s !important;
    box-shadow: 0 4px 14px rgba(26,79,196,0.22) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(26,79,196,0.32) !important;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(10px);
    border-radius: 16px; padding: 1.4rem;
    border: 1px solid rgba(226,234,248,0.9);
    box-shadow: 0 2px 16px rgba(26,79,196,0.07);
}

/* Inputs */
[data-baseweb="input"] input, [data-baseweb="select"] { border-radius: 8px !important; }
.streamlit-expanderHeader {
    background: rgba(248,250,255,0.9) !important;
    border-radius: 10px !important; font-weight: 600 !important; color: #0d1b3e !important;
}
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # ── Logo + titre ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding: 20px 16px 4px 16px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
        <div style="background:linear-gradient(135deg,#1a4fc4,#00c6ff);border-radius:10px;
                    width:38px;height:38px;display:flex;align-items:center;justify-content:center;
                    font-size:19px;flex-shrink:0;box-shadow:0 4px 12px rgba(26,79,196,0.4)">⚕️</div>
        <div>
          <div style="color:white;font-size:1.05rem;font-weight:700;line-height:1.1">
            SHAHIDI <span style="color:#00c6ff">AI</span>
          </div>
          <div style="color:#6b82aa;font-size:11px;margin-top:1px">v2.0 · Cancer gastrique</div>
        </div>
      </div>

      <!-- Bandeau département -->
      <div style="background:rgba(0,198,255,0.08);border:1px solid rgba(0,198,255,0.18);
                  border-radius:8px;padding:6px 10px;margin-top:10px;margin-bottom:2px">
        <div style="font-size:10px;font-weight:700;color:#5090c0;text-transform:uppercase;
                    letter-spacing:.1em;margin-bottom:3px">Département actif</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Selectbox département — directement après le label HTML
    dept = st.selectbox(
        "Département",
        ["Tous les départements", "Cancérologie", "Chirurgie Générale"],
        label_visibility="collapsed",
        key="dept_select"
    )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.divider()

    # ── Navigation ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:0 16px;margin-bottom:4px">
      <div style="font-size:10px;font-weight:700;color:#3a5080;text-transform:uppercase;
                  letter-spacing:.1em">Navigation</div>
    </div>
    """, unsafe_allow_html=True)

    PAGES = {
        "🏠  Tableau de bord":     "accueil",
        "📈  Indicateurs KPI":     "kpi",
        "🧠  Prédiction IA":       "prediction",
        "👥  Registre patients":   "registre",
        "🔬  Analyse des données": "analyse",
        "ℹ️  À Propos":            "apropos",
    }

    selected = st.radio(
        "nav",
        list(PAGES.keys()),
        label_visibility="collapsed",
        key="nav_radio"
    )

    st.divider()

    # ── Status badge ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin: 0 4px 16px 4px;background:rgba(46,213,115,0.10);
                border:1px solid rgba(46,213,115,0.22);border-radius:10px;padding:10px 12px">
      <div style="display:flex;align-items:center;gap:7px;font-size:12px;
                  color:#2ed573;font-weight:600;margin-bottom:3px">
        <span style="width:7px;height:7px;background:#2ed573;border-radius:50%;
                     display:inline-block;box-shadow:0 0 6px #2ed573"></span>
        Système opérationnel
      </div>
      <div style="font-size:11px;color:#3a6050">DeepSurv  ·  C-index : 0.92</div>
    </div>
    """, unsafe_allow_html=True)

# ── PAGE ROUTING ──────────────────────────────────────────────────────────────
page_id = PAGES[selected]

if   page_id == "accueil":    accueil()
elif page_id == "kpi":        kpi()
elif page_id == "prediction": modelisation()
elif page_id == "registre":   registre()
elif page_id == "analyse":    analyse_descriptive()
elif page_id == "apropos":    a_propos()
