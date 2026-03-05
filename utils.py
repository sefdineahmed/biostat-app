"""
utils.py — Fonctions partagées SHAHIDI AI Platform
TensorFlow importé en lazy (uniquement si modèle keras demandé)
"""
import os
import joblib
import numpy as np
import pandas as pd
import streamlit as st

# ── Patch sklearn ────────────────────────────────────────────────────────────
try:
    from sklearn.base import BaseEstimator
    if not hasattr(BaseEstimator, "sklearn_tags"):
        @property
        def sklearn_tags(self): return {}
        BaseEstimator.sklearn_tags = sklearn_tags
except Exception:
    pass

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_PATH = "data/data.xlsx"
LOGO_PATH = "assets/shahidi.png"

# ── Models registry ──────────────────────────────────────────────────────────
MODELS = {
    "DeepSurv": "models/deepsurv.keras",
    "CoxPH":    "models/coxph.joblib",
    "RSF":      "models/rsf.joblib",
    "GBST":     "models/gbst.joblib",
}

MODEL_META = {
    "DeepSurv": {"c_index": 0.92, "ibs": 0.044, "type": "Deep Learning",      "color": "#00c6ff"},
    "CoxPH":    {"c_index": 0.85, "ibs": 0.080, "type": "Statistique",         "color": "#2ed573"},
    "RSF":      {"c_index": 0.84, "ibs": 0.077, "type": "Machine Learning",    "color": "#ffa502"},
    "GBST":     {"c_index": 0.88, "ibs": 0.061, "type": "Gradient Boosting",   "color": "#a29bfe"},
}

FEATURE_CONFIG = {
    "AGE":                 "Âge (années)",
    "Cardiopathie":        "Cardiopathie",
    "Ulceregastrique":     "Ulcère gastrique",
    "Douleurepigastrique": "Douleur épigastrique",
    "Ulcero-bourgeonnant": "Lésion ulcéro-bourgeonnante",
    "Denitrution":         "Dénutrition",
    "Tabac":               "Tabagisme actif",
    "Mucineux":            "Type mucineux",
    "Infiltrant":          "Type infiltrant",
    "Stenosant":           "Type sténosant",
    "Metastases":          "Métastases",
    "Adenopathie":         "Adénopathie",
}

TEAM = [
    {"name": "Pr. Aba Diop",     "role": "Maître de Conférences", "etablissement": "UAD Bambey",
     "photo": "assets/aba.jpeg",         "email": "aba.diop@uadb.edu.sn"},
    {"name": "PhD. Idrissa Sy",  "role": "Enseignant Chercheur",  "etablissement": "UAD Bambey",
     "photo": "assets/team/sy.jpeg",     "email": "idrissa.sy@uadb.edu.sn"},
    {"name": "M. Ahmed Sefdine", "role": "Étudiant Chercheur",    "etablissement": "UAD Bambey",
     "photo": "assets/team/sefdine.jpeg","email": "sefdine668@gmail.com"},
]

# ── Cox loss (défini ici mais TF importé seulement si besoin) ─────────────────
def _get_cox_loss():
    """Retourne la fonction cox_loss en important TF à la demande."""
    import tensorflow as tf
    def cox_loss(y_true, y_pred):
        event    = tf.cast(y_true[:, 0], dtype=tf.float32)
        risk     = y_pred[:, 0]
        log_risk = tf.math.log(tf.cumsum(tf.exp(risk), reverse=True))
        return -tf.reduce_mean((risk - log_risk) * event)
    return cox_loss

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=60)
def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_PATH):
        return pd.read_excel(DATA_PATH)
    st.error(f"❌ Fichier introuvable : {DATA_PATH}")
    return pd.DataFrame()

# ── Model loading (lazy TF) ───────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_model(model_path: str):
    ext = os.path.splitext(model_path)[1].lower()
    if not os.path.exists(model_path):
        st.error(f"❌ Modèle introuvable : {model_path}")
        return None
    try:
        if ext == ".joblib":
            return joblib.load(model_path)
        # .keras / .h5 → TensorFlow importé ici seulement
        from tensorflow.keras.models import load_model as tf_load_model
        return tf_load_model(model_path, custom_objects={"cox_loss": _get_cox_loss()})
    except ImportError:
        st.error("❌ TensorFlow non installé. Utilisez un modèle joblib (CoxPH, RSF, GBST).")
        return None
    except Exception as e:
        st.error(f"❌ Erreur chargement modèle : {e}")
        return None

# ── Feature encoding ──────────────────────────────────────────────────────────
def encode_features(inputs: dict) -> pd.DataFrame:
    encoded = {}
    for k, v in inputs.items():
        if k == "AGE":
            encoded[k] = float(v)
        else:
            encoded[k] = 1.0 if str(v).strip().upper() == "OUI" else 0.0
    return pd.DataFrame([encoded], dtype=float)

# ── Prediction (lazy TF check) ────────────────────────────────────────────────
def predict_survival(model, data: pd.DataFrame) -> float:
    if model is None:
        raise ValueError("Modèle non chargé.")
    baseline = 60.0

    # Try to detect keras model without importing TF at module level
    model_type = type(model).__module__ or ""
    is_keras = "keras" in model_type or "tensorflow" in model_type

    if is_keras:
        raw = float(model.predict(data, verbose=0).flatten()[0])
    else:
        # lifelines CoxPH
        try:
            from lifelines import CoxPHFitter
            if isinstance(model, CoxPHFitter):
                raw = float(model.predict_partial_hazard(data).values.flatten()[0])
                return baseline * np.exp(-raw)
        except ImportError:
            pass
        # scikit-survival / sklearn-like
        if hasattr(model, "predict"):
            arr = model.predict(data)
            raw = float(np.ravel(arr)[0])
        else:
            raise ValueError("Modèle incompatible.")

    return baseline * np.exp(-raw)

def clean_prediction(pred) -> float:
    try:
        return max(float(pred), 1.0)
    except Exception:
        return 1.0

# ── Save patient ──────────────────────────────────────────────────────────────
def save_new_patient(new_data: dict) -> bool:
    df = load_data()
    new_df = pd.DataFrame([new_data])
    for c in new_df.columns:
        if c not in ("AGE", "Tempsdesuivi", "Deces"):
            new_df[c] = new_df[c].apply(
                lambda x: "OUI" if str(x).upper() == "OUI" else "NON"
            )
    df = pd.concat([df, new_df], ignore_index=True)
    try:
        df.to_excel(DATA_PATH, index=False)
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur enregistrement : {e}")
        return False

# ── Kaplan-Meier (pur numpy, sans lifelines) ──────────────────────────────────
def compute_km(durations: pd.Series, events: pd.Series):
    """Retourne (times_array, survival_array) pour la courbe KM."""
    ev = (events.str.upper() == "OUI").astype(int)
    df = pd.DataFrame({"t": durations.values, "e": ev.values}).sort_values("t")
    n, surv = len(df), 1.0
    times, survs = [0], [1.0]
    for t, grp in df.groupby("t"):
        d = grp["e"].sum()
        c = len(grp)
        if n > 0:
            surv *= (1 - d / n)
        times.append(int(t))
        survs.append(round(surv, 6))
        n -= c
    return np.array(times), np.array(survs)

def survival_proba_at(times, survs, month: int) -> float:
    idx = np.searchsorted(times, month, side="right") - 1
    idx = max(0, min(idx, len(survs) - 1))
    return round(survs[idx] * 100, 1)

# ── CSS global ────────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem !important; padding-bottom: 2rem !important; max-width: 1280px !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #06091a 0%, #0d1b3e 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.07);
}
[data-testid="stSidebar"] * { color: #c8d4f0 !important; }
[data-testid="stSidebar"] .stSelectbox > div > div { background: rgba(255,255,255,0.07) !important; border-color: rgba(255,255,255,0.12) !important; }

/* Metrics */
[data-testid="stMetric"] { background: white; border-radius: 14px; padding: 1.1rem 1.3rem; border: 1px solid #e2eaf8; box-shadow: 0 2px 12px rgba(26,79,196,0.06); }
[data-testid="stMetricLabel"] { font-size: 11px !important; color: #6b7a9d !important; text-transform: uppercase; letter-spacing: 0.07em; }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 1.9rem !important; color: #0d1b3e !important; font-weight: 600 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #f0f4fb; border-radius: 10px; padding: 4px; gap: 2px; }
.stTabs [data-baseweb="tab"] { background: transparent !important; border-radius: 8px !important; font-size: 13px !important; font-weight: 500 !important; color: #6b7a9d !important; padding: 8px 18px !important; }
.stTabs [aria-selected="true"] { background: white !important; color: #1a4fc4 !important; box-shadow: 0 2px 8px rgba(26,79,196,0.12) !important; }

/* Buttons */
.stButton > button { background: linear-gradient(135deg, #1a4fc4, #00a8e8) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; font-size: 14px !important; padding: 0.55rem 1.4rem !important; transition: all 0.2s !important; box-shadow: 0 4px 14px rgba(26,79,196,0.22) !important; }
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 20px rgba(26,79,196,0.32) !important; }

/* Inputs */
[data-baseweb="input"] input, [data-baseweb="select"] { border-radius: 8px !important; }
.streamlit-expanderHeader { background: #f8faff !important; border-radius: 10px !important; font-weight: 600 !important; color: #0d1b3e !important; }

/* DataFrame */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden; }
</style>
"""
