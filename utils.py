import os, joblib, numpy as np, pandas as pd, streamlit as st, tensorflow as tf
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import load_model as tf_load_model

try:
    from sklearn.base import BaseEstimator
    if not hasattr(BaseEstimator, "sklearn_tags"):
        @property
        def sklearn_tags(self): return {}
        BaseEstimator.sklearn_tags = sklearn_tags
except Exception: pass

try:
    from lifelines import CoxPHFitter
except ImportError:
    CoxPHFitter = None

adam = Adam()
DATA_PATH   = "data/data.xlsx"
LOGO_PATH   = "assets/shahidi.png"

MODELS = {
    "DeepSurv": "models/deepsurv.keras",
    "CoxPH":    "models/coxph.joblib",
    "RSF":      "models/rsf.joblib",
    "GBST":     "models/gbst.joblib",
}

MODEL_META = {
    "DeepSurv": {"c_index": 0.92, "ibs": 0.044, "type": "Deep Learning",     "color": "#00c6ff"},
    "CoxPH":    {"c_index": 0.85, "ibs": 0.080, "type": "Statistique",        "color": "#2ed573"},
    "RSF":      {"c_index": 0.84, "ibs": 0.077, "type": "Machine Learning",   "color": "#ffa502"},
    "GBST":     {"c_index": 0.88, "ibs": 0.061, "type": "Gradient Boosting",  "color": "#a29bfe"},
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
    {"name": "Pr. Aba Diop",      "role": "Maître de Conférences", "etablissement": "UAD Bambey", "photo": "assets/aba.jpeg",        "email": "aba.diop@uadb.edu.sn"},
    {"name": "PhD. Idrissa Sy",   "role": "Enseignant Chercheur",  "etablissement": "UAD Bambey", "photo": "assets/team/sy.jpeg",    "email": "idrissa.sy@uadb.edu.sn"},
    {"name": "M. Ahmed Sefdine",  "role": "Étudiant Chercheur",    "etablissement": "UAD Bambey", "photo": "assets/team/sefdine.jpeg","email": "sefdine668@gmail.com"},
]

def cox_loss(y_true, y_pred):
    event    = tf.cast(y_true[:, 0], dtype=tf.float32)
    risk     = y_pred[:, 0]
    log_risk = tf.math.log(tf.cumsum(tf.exp(risk), reverse=True))
    return -tf.reduce_mean((risk - log_risk) * event)

@st.cache_data(show_spinner=False, ttl=60)
def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_PATH):
        return pd.read_excel(DATA_PATH)
    st.error(f"❌ Fichier introuvable : {DATA_PATH}")
    return pd.DataFrame()

@st.cache_resource(show_spinner=False)
def load_model(model_path: str):
    ext = os.path.splitext(model_path)[1].lower()
    if not os.path.exists(model_path):
        return None
    try:
        if ext == ".joblib":
            return joblib.load(model_path)
        return tf_load_model(model_path, custom_objects={"cox_loss": cox_loss})
    except Exception as e:
        st.error(f"❌ Erreur chargement modèle : {e}")
        return None

def encode_features(inputs: dict) -> pd.DataFrame:
    encoded = {}
    for k, v in inputs.items():
        if k == "AGE":
            encoded[k] = float(v)
        else:
            encoded[k] = 1.0 if str(v).strip().upper() == "OUI" else 0.0
    return pd.DataFrame([encoded], dtype=float)

def predict_survival(model, data: pd.DataFrame) -> float:
    if model is None:
        raise ValueError("Modèle non chargé.")
    baseline = 60.0
    if isinstance(model, tf.keras.Model):
        raw = float(model.predict(data, verbose=0).flatten()[0])
    elif CoxPHFitter is not None and isinstance(model, CoxPHFitter):
        raw = float(model.predict_partial_hazard(data).values.flatten()[0])
    elif hasattr(model, "predict"):
        raw = float(np.ravel(model.predict(data))[0])
    else:
        raise ValueError("Modèle incompatible.")
    return baseline * np.exp(-raw)

def clean_prediction(pred) -> float:
    try:
        return max(float(pred), 1.0)
    except Exception:
        return 1.0

def save_new_patient(new_data: dict) -> bool:
    df = load_data()
    new_df = pd.DataFrame([new_data])
    for c in new_df.columns:
        if c not in ("AGE", "Tempsdesuivi", "Deces"):
            new_df[c] = new_df[c].apply(lambda x: "OUI" if str(x).upper() == "OUI" else "NON")
    df = pd.concat([df, new_df], ignore_index=True)
    try:
        df.to_excel(DATA_PATH, index=False)
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur enregistrement : {e}")
        return False

def compute_km(durations: pd.Series, events: pd.Series):
    ev = (events.str.upper() == "OUI").astype(int)
    df = pd.DataFrame({"t": durations.values, "e": ev.values}).sort_values("t")
    n, surv = len(df), 1.0
    times, survs = [0], [1.0]
    for t, grp in df.groupby("t"):
        d = grp["e"].sum()
        c = len(grp)
        if n > 0:
            surv *= (1 - d / n)
        times.append(int(t)); survs.append(round(surv, 6))
        n -= c
    return np.array(times), np.array(survs)

def survival_proba_at(times, survs, month: int) -> float:
    idx = np.searchsorted(times, month, side="right") - 1
    idx = max(0, min(idx, len(survs) - 1))
    return round(survs[idx] * 100, 1)

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem !important; padding-bottom: 2rem !important; max-width: 1280px !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #06091a 0%, #0d1b3e 100%) !important; border-right: 1px solid rgba(255,255,255,0.07); }
[data-testid="stSidebar"] * { color: #c8d4f0 !important; }
[data-testid="stMetric"] { background: white; border-radius: 14px; padding: 1.2rem 1.4rem; border: 1px solid #e2eaf8; box-shadow: 0 2px 12px rgba(26,79,196,0.06); }
[data-testid="stMetricLabel"] { font-size: 11px !important; color: #6b7a9d !important; text-transform: uppercase; letter-spacing: 0.07em; }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 1.9rem !important; color: #0d1b3e !important; font-weight: 600 !important; }
.stTabs [data-baseweb="tab-list"] { background: #f0f4fb; border-radius: 10px; padding: 4px; gap: 2px; }
.stTabs [data-baseweb="tab"] { background: transparent !important; border-radius: 8px !important; font-size: 13px !important; font-weight: 500 !important; color: #6b7a9d !important; padding: 8px 18px !important; }
.stTabs [aria-selected="true"] { background: white !important; color: #1a4fc4 !important; box-shadow: 0 2px 8px rgba(26,79,196,0.12) !important; }
.stButton > button { background: linear-gradient(135deg, #1a4fc4, #00a8e8) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; font-size: 14px !important; padding: 0.55rem 1.4rem !important; transition: all 0.2s !important; box-shadow: 0 4px 14px rgba(26,79,196,0.22) !important; }
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 20px rgba(26,79,196,0.32) !important; }
[data-baseweb="input"] input, [data-baseweb="select"] { border-radius: 8px !important; }
.streamlit-expanderHeader { background: #f8faff !important; border-radius: 10px !important; font-weight: 600 !important; color: #0d1b3e !important; }
</style>
"""
