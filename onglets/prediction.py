import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import io
from fpdf import FPDF
from utils import (FEATURE_CONFIG, encode_features, load_model, predict_survival,
                   clean_prediction, save_new_patient, MODELS, MODEL_META, GLOBAL_CSS)

# ── Survival curve figure ──────────────────────────────────────────────────────
def _surv_curve_fig(median_s: float):
    months = list(range(0, min(int(median_s * 2) + 1, 73)))
    curve  = [round(100 * np.exp(-np.log(2) * t / median_s), 2) for t in months]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=curve, mode="lines", fill="tozeroy",
        line=dict(color="#1a4fc4", width=2.5),
        fillcolor="rgba(26,79,196,0.08)",
        hovertemplate="Mois %{x} → %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=50, line_dash="dot", line_color="#aaa", line_width=1,
        annotation_text="50% — médiane", annotation_position="bottom right",
        annotation_font_size=10, annotation_font_color="#888")
    fig.add_vline(x=int(median_s), line_dash="dash", line_color="#1a4fc4", line_width=1.2)
    fig.update_layout(
        height=220, margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(title="Mois", gridcolor="#f0f4fb", tickfont=dict(size=11)),
        yaxis=dict(title="% Survie", range=[0, 105], gridcolor="#f0f4fb", tickfont=dict(size=11)),
        font=dict(family="Sora, sans-serif"), showlegend=False,
    )
    return fig

# ── PDF report ─────────────────────────────────────────────────────────────────
def _pdf_report(inputs: dict, cpred: float, model_name: str, pat_id: str = "") -> bytes:
    pdf = FPDF()
    pdf.add_page()
    # Header band
    pdf.set_fill_color(26, 79, 196)
    pdf.rect(0, 0, 210, 32, "F")
    pdf.set_font("Arial", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "", ln=True)
    pdf.cell(0, 14, "   SHAHIDI AI  -  Rapport de Survie", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(180, 210, 255)
    pdf.cell(0, 7, f"   {date.today():%d/%m/%Y}   |   Modele : {model_name}   |   {pat_id}", ln=True)
    pdf.ln(8)
    # Result box
    pdf.set_font("Arial", "B", 15)
    pdf.set_text_color(26, 79, 196)
    pdf.cell(0, 10, "Resultat de la prediction", ln=True)
    pdf.set_fill_color(240, 246, 255)
    pdf.rect(10, pdf.get_y(), 190, 18, "F")
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "", ln=True)
    pdf.cell(0, 10, f"   Survie mediane estimee : {cpred:.1f} mois", ln=True)
    pdf.ln(6)
    # Parameters table
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(26, 79, 196)
    pdf.cell(0, 10, "Parametres cliniques", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(0, 0, 0)
    fill = False
    for k, v in inputs.items():
        label = FEATURE_CONFIG.get(k, k)
        pdf.set_fill_color(248, 250, 255 if fill else 255, )
        pdf.cell(95, 8, f"  {label}", 1, 0, "L", True)
        pdf.cell(95, 8, f"  {v}", 1, 1, "L", True)
        fill = not fill
    pdf.ln(8)
    # Disclaimer
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(130, 130, 130)
    pdf.multi_cell(0, 5,
        "Avertissement : Ce rapport est un outil d'aide a la decision clinique genere par "
        "intelligence artificielle. Il ne remplace pas l'evaluation medicale d'un clinicien qualifie. "
        f"C-Index du modele {model_name} : {MODEL_META.get(model_name, {}).get('c_index', 'N/A')}.")
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.getvalue()

# ── Main function ──────────────────────────────────────────────────────────────
def modelisation():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:1.2rem">
      <h2 style="font-size:1.5rem;font-weight:700;color:#0d1b3e;margin:0 0 .2rem 0">
        🧠 Prédiction de Survie par Intelligence Artificielle
      </h2>
      <p style="color:#6b7a9d;font-size:13px;margin:0">
        Saisir les paramètres cliniques du patient — Résultat instantané
      </p>
    </div>""", unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""
    <div style="background:#fff8e1;border-left:4px solid #ffa502;border-radius:0 10px 10px 0;
                padding:10px 14px;font-size:13px;color:#7d5a00;margin-bottom:1.2rem">
      ⚠️ <strong>Aide à la décision uniquement</strong> — Résultats à interpréter par un médecin qualifié.
      Ne pas utiliser comme unique base diagnostique ou thérapeutique.
    </div>""", unsafe_allow_html=True)

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("**🔬 Configuration du modèle**")

        # Only show models that are actually available
        available = {k: v for k, v in MODELS.items() if "__" not in k}
        selected = st.selectbox(
            "Modèle de prédiction",
            list(available.keys()),
            format_func=lambda x: f"{x}  (C={MODEL_META[x]['c_index']})  — {MODEL_META[x]['type']}"
        )
        meta = MODEL_META[selected]

        if selected == "DeepSurv":
            st.markdown("""
            <div style="background:rgba(255,165,2,.12);border:1px solid rgba(255,165,2,.3);
                        border-radius:8px;padding:8px 10px;font-size:12px;color:#c07000;margin-top:6px">
              ⚠️ DeepSurv nécessite TensorFlow.<br>
              Si non installé, utilisez CoxPH, RSF ou GBST.
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:rgba(255,255,255,.07);border-radius:10px;padding:10px;margin-top:8px">
          <div style="font-size:11px;color:#8ca6d0;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px">
            Performances</div>
          <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px">
            <span>C-Index</span>
            <span style="font-family:JetBrains Mono,monospace;color:{meta['color']};
                         font-weight:700">{meta['c_index']:.2f}</span>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:12px">
            <span>IBS</span>
            <span style="font-family:JetBrains Mono,monospace;color:#a0b8e8">{meta['ibs']:.3f}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        pat_id = st.text_input("ID Patient (optionnel)", placeholder="PAT-2024-001")
        dept   = st.selectbox("Département", ["Cancérologie", "Chirurgie Générale"])
        enreg  = st.checkbox("💾 Enregistrer après prédiction", value=True)

    # ── Layout ─────────────────────────────────────────────────────────────────
    col_form, col_res = st.columns([1.6, 1], gap="large")

    with col_form:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:16px;padding:1.6rem 1.8rem;
                    border:1px solid #e2eaf8;box-shadow:0 2px 16px rgba(26,79,196,.06)">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
               letter-spacing:.06em;margin-bottom:1rem;padding-bottom:.6rem;
               border-bottom:2px solid #f0f4fb">👤 Profil Clinique du Patient</div>""",
            unsafe_allow_html=True)

        inputs = {}

        # Démographie
        st.markdown("""<div style="font-size:10px;font-weight:700;color:#1a4fc4;
            text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px">
            ── DÉMOGRAPHIE</div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            inputs["AGE"] = st.number_input("Âge (années)", 18, 100, 55,
                help="Âge du patient au moment du diagnostic")
        with c2:
            st.selectbox("Sexe biologique", ["Masculin", "Féminin"])

        # Antécédents
        st.markdown("""<div style="font-size:10px;font-weight:700;color:#1a4fc4;
            text-transform:uppercase;letter-spacing:.12em;margin:10px 0 6px 0">
            ── ANTÉCÉDENTS & COMORBIDITÉS</div>""", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: inputs["Cardiopathie"]        = st.selectbox("Cardiopathie",        ["NON","OUI"], key="p_card")
        with c2: inputs["Ulceregastrique"]     = st.selectbox("Ulcère gastrique",    ["NON","OUI"], key="p_ulc")
        with c3: inputs["Douleurepigastrique"] = st.selectbox("Douleur épigastrique",["OUI","NON"], key="p_doul")
        c4, c5 = st.columns(2)
        with c4: inputs["Tabac"]       = st.selectbox("Tabagisme actif",             ["NON","OUI"], key="p_tab")
        with c5: inputs["Denitrution"] = st.selectbox("Dénutrition",                 ["NON","OUI"], key="p_den")

        # Tumeur
        st.markdown("""<div style="font-size:10px;font-weight:700;color:#1a4fc4;
            text-transform:uppercase;letter-spacing:.12em;margin:10px 0 6px 0">
            ── CARACTÉRISTIQUES TUMORALES</div>""", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: inputs["Mucineux"]            = st.selectbox("Type mucineux",           ["OUI","NON"], key="p_muc")
        with c2: inputs["Infiltrant"]          = st.selectbox("Type infiltrant",         ["NON","OUI"], key="p_inf")
        with c3: inputs["Stenosant"]           = st.selectbox("Type sténosant",          ["NON","OUI"], key="p_sten")
        c4, c5, c6 = st.columns(3)
        with c4: inputs["Ulcero-bourgeonnant"] = st.selectbox("Lés. ulcéro-bourg.",      ["NON","OUI"], key="p_ulcb")
        with c5: inputs["Metastases"]          = st.selectbox("Métastases",              ["NON","OUI"], key="p_meta")
        with c6: inputs["Adenopathie"]         = st.selectbox("Adénopathie",             ["NON","OUI"], key="p_aden")

        st.markdown("<br>", unsafe_allow_html=True)
        run = st.button("🧠 Calculer la prédiction de survie", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Result panel ───────────────────────────────────────────────────────────
    with col_res:
        if not run:
            st.markdown("""
            <div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:16px;padding:2rem;border:1px solid #e2eaf8;
                        box-shadow:0 2px 16px rgba(26,79,196,.06);text-align:center;
                        min-height:380px;display:flex;flex-direction:column;
                        align-items:center;justify-content:center;gap:10px">
              <div style="font-size:48px">🔬</div>
              <div style="font-size:15px;font-weight:600;color:#0d1b3e">Résultats</div>
              <div style="font-size:13px;color:#6b7a9d;max-width:200px;line-height:1.5">
                Remplissez le profil clinique et cliquez sur Calculer
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            with st.spinner("Analyse en cours..."):
                try:
                    model  = load_model(MODELS[selected])
                    df_in  = encode_features(inputs)
                    pred   = predict_survival(model, df_in)
                    cpred  = clean_prediction(pred)

                    # Probabilities at key timepoints
                    p6  = round(100 * np.exp(-np.log(2) * 6  / cpred), 1)
                    p12 = round(100 * np.exp(-np.log(2) * 12 / cpred), 1)
                    p24 = round(100 * np.exp(-np.log(2) * 24 / cpred), 1)
                    p36 = round(100 * np.exp(-np.log(2) * 36 / cpred), 1)

                    # Risk category
                    if cpred >= 36:
                        risk_label, risk_color, risk_icon = "Faible risque",    "#2ed573", "🟢"
                    elif cpred >= 18:
                        risk_label, risk_color, risk_icon = "Risque modéré",    "#ffa502", "🟡"
                    elif cpred >= 8:
                        risk_label, risk_color, risk_icon = "Risque élevé",     "#ff6b35", "🟠"
                    else:
                        risk_label, risk_color, risk_icon = "Risque très élevé","#ff4757", "🔴"

                    # Needle position on risk gauge (0% = low risk, 100% = high risk)
                    needle_pct = max(5, min(93, int((1 - cpred / 60) * 93)))

                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:16px;padding:1.6rem;
                                border:1px solid #e2eaf8;
                                box-shadow:0 2px 16px rgba(26,79,196,.06);
                                border-top:4px solid {risk_color}">

                      <!-- Main result -->
                      <div style="text-align:center;margin-bottom:1.2rem;padding-bottom:1rem;
                                  border-bottom:1px solid #f0f4fb">
                        <div style="font-size:10px;color:#6b7a9d;text-transform:uppercase;
                                    letter-spacing:.1em;margin-bottom:4px">
                          SURVIE MÉDIANE · {selected}
                        </div>
                        <div style="font-family:'JetBrains Mono',monospace;font-size:3.5rem;
                                    font-weight:700;color:#0d1b3e;line-height:1">{cpred:.0f}</div>
                        <div style="font-size:14px;color:#6b7a9d;margin-top:2px">mois</div>
                        <div style="display:inline-flex;align-items:center;gap:6px;
                                    background:{risk_color}18;border:1px solid {risk_color}44;
                                    padding:4px 14px;border-radius:20px;font-size:12px;
                                    font-weight:700;color:{risk_color};margin-top:10px">
                          {risk_icon} {risk_label}
                        </div>
                      </div>

                      <!-- Risk gauge -->
                      <div style="margin-bottom:1.1rem">
                        <div style="display:flex;justify-content:space-between;
                                    font-size:10px;color:#6b7a9d;margin-bottom:4px">
                          <span>Risque faible</span><span>Risque élevé</span>
                        </div>
                        <div style="background:linear-gradient(90deg,#2ed573,#ffa502,#ff4757);
                                    border-radius:5px;height:9px;position:relative">
                          <div style="position:absolute;left:{needle_pct}%;top:-5px;
                                      transform:translateX(-50%);width:4px;height:19px;
                                      background:#0d1b3e;border-radius:2px;
                                      box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>
                        </div>
                      </div>

                      <!-- 4 probabilities grid -->
                      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:1rem">
                        {"".join([
                          f'<div style="background:#f8faff;border-radius:8px;padding:10px 12px">'
                          f'<div style="font-size:10px;color:#6b7a9d;margin-bottom:2px;text-transform:uppercase">à {m} mois</div>'
                          f'<div style="font-family:JetBrains Mono,monospace;font-size:1.25rem;font-weight:700;'
                          f'color:{"#2ed573" if p>=50 else "#ffa502" if p>=30 else "#ff4757"}">{p}%</div></div>'
                          for p, m in [(p6, 6), (p12, 12), (p24, 24), (p36, 36)]
                        ])}
                      </div>

                      <!-- Model info -->
                      <div style="background:#f8faff;border-radius:8px;padding:10px 12px">
                        <div style="display:flex;justify-content:space-between;
                                    font-size:12px;margin-bottom:4px">
                          <span style="color:#6b7a9d">Modèle</span>
                          <span style="font-weight:600;color:#0d1b3e">{selected}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:12px">
                          <span style="color:#6b7a9d">C-Index</span>
                          <span style="font-family:JetBrains Mono,monospace;font-weight:700;
                                       color:{meta['color']}">{meta['c_index']:.2f}</span>
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)

                    # Survival curve
                    st.markdown("""
                    <div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1rem 1.2rem;
                                border:1px solid #e2eaf8;box-shadow:0 2px 8px rgba(26,79,196,.05);
                                margin-top:.8rem">
                      <div style="font-size:12px;font-weight:700;color:#0d1b3e;margin-bottom:.4rem">
                        Courbe de survie individuelle</div>""",
                        unsafe_allow_html=True)
                    st.plotly_chart(_surv_curve_fig(cpred), use_container_width=True,
                        config={"displayModeBar": False})
                    st.markdown("</div>", unsafe_allow_html=True)

                    # Save patient record
                    if enreg:
                        rec = df_in.to_dict(orient="records")[0]
                        rec["Tempsdesuivi"] = round(cpred, 1)
                        rec["Deces"] = "OUI"
                        if save_new_patient(rec):
                            st.success("✅ Patient enregistré dans la base de données")

                    # PDF export
                    rec_display = {
                        FEATURE_CONFIG.get(k, k): (
                            int(v) if k == "AGE" else ("OUI" if v == 1.0 else "NON")
                        )
                        for k, v in inputs.items()
                    }
                    pdf_bytes = _pdf_report(rec_display, cpred, selected, pat_id)
                    st.download_button(
                        "📄 Télécharger le rapport PDF",
                        pdf_bytes,
                        file_name=f"rapport_{pat_id or 'patient'}_{date.today():%Y%m%d}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

                except Exception as e:
                    st.error(f"❌ Erreur de prédiction : {e}")
                    if "tensorflow" in str(e).lower() or "keras" in str(e).lower():
                        st.warning(
                            "💡 **TensorFlow non installé.** "
                            "Sélectionnez **CoxPH**, **RSF** ou **GBST** dans la barre latérale "
                            "— ces modèles fonctionnent sans TensorFlow."
                        )
                    else:
                        st.info("💡 Vérifiez que les fichiers modèles sont présents dans `models/`")
