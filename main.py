import streamlit as st
from onglets import accueil, analyse_descriptive, modelisation, registre, kpi, a_propos

st.set_page_config(
    page_title="SHAHIDI AI — Plateforme Oncologie",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 0 20px 0">
      <div style="background:linear-gradient(135deg,#1a4fc4,#00c6ff);border-radius:10px;
                  width:36px;height:36px;display:flex;align-items:center;justify-content:center;
                  font-size:18px;flex-shrink:0">⚕️</div>
      <div>
        <div style="color:white;font-size:1rem;font-weight:700;line-height:1">SHAHIDI <span style="color:#00c6ff">AI</span></div>
        <div style="color:#6b82aa;font-size:11px">Oncologie · Cancer gastrique</div>
      </div>
    </div>""", unsafe_allow_html=True)

    PAGES = {
        "🏠  Tableau de bord":    "accueil",
        "📈  Indicateurs KPI":    "kpi",
        "🧠  Prédiction IA":      "prediction",
        "👥  Registre patients":  "registre",
        "🔬  Analyse des données":"analyse",
        "ℹ️  À Propos":           "apropos",
    }

    st.markdown("""<div style="font-size:10px;font-weight:700;color:#4a6090;
        text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">Navigation</div>""",
        unsafe_allow_html=True)

    selected = st.radio("", list(PAGES.keys()), label_visibility="collapsed")

    st.markdown("""---
    <div style="font-size:10px;color:#4a6090;text-transform:uppercase;letter-spacing:.1em;
                margin-bottom:6px;margin-top:4px">Département actif</div>""", unsafe_allow_html=True)

    dept = st.selectbox("", ["Tous les départements","Cancérologie","Chirurgie Générale"],
        label_visibility="collapsed")

    st.markdown("""---""")
    st.markdown("""
    <div style="background:rgba(46,213,115,.12);border:1px solid rgba(46,213,115,.25);
                border-radius:10px;padding:10px 12px;margin-top:4px">
      <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:#2ed573;font-weight:600">
        <span style="width:7px;height:7px;background:#2ed573;border-radius:50%;display:inline-block"></span>
        Système opérationnel
      </div>
      <div style="font-size:11px;color:#4a8060;margin-top:3px">DeepSurv C-index : 0.92</div>
    </div>""", unsafe_allow_html=True)

# ── Page routing ──────────────────────────────────────────────────────────────
page_id = PAGES[selected]

if page_id == "accueil":
    accueil()
elif page_id == "kpi":
    kpi()
elif page_id == "prediction":
    modelisation()
elif page_id == "registre":
    registre()
elif page_id == "analyse":
    analyse_descriptive()
elif page_id == "apropos":
    a_propos()
