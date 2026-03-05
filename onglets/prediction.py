import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import io
from fpdf import FPDF
from utils import (FEATURE_CONFIG, encode_features, load_model, predict_survival,
                   clean_prediction, save_new_patient, MODELS, MODEL_META, GLOBAL_CSS)

# ─────────────────────────────────────────────────────────────────────────────

def _surv_curve_fig(median_s):
    months = list(range(0, min(int(median_s * 2) + 1, 73)))
    curve  = [round(100 * np.exp(-np.log(2) * t / median_s), 2) for t in months]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=curve, mode="lines", fill="tozeroy",
        line=dict(color="#1a4fc4", width=2.5),
        fillcolor="rgba(26,79,196,0.08)",
    ))
    fig.add_hline(y=50, line_dash="dot", line_color="#aaa", line_width=1,
        annotation_text="50% — médiane", annotation_position="bottom right",
        annotation_font_size=10, annotation_font_color="#888")
    fig.add_vline(x=int(median_s), line_dash="dash", line_color="#1a4fc4", line_width=1)
    fig.update_layout(height=220, margin=dict(l=0,r=0,t=10,b=0),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(title="Mois", gridcolor="#f0f4fb", tickfont=dict(size=11)),
        yaxis=dict(title="% Survie", range=[0,105], gridcolor="#f0f4fb", tickfont=dict(size=11)),
        font=dict(family="Sora, sans-serif"), showlegend=False)
    return fig

def _pdf_report(inputs, cpred, model_name, pat_id=""):
    pdf = FPDF(); pdf.add_page()
    # Header
    pdf.set_fill_color(26,79,196)
    pdf.rect(0,0,210,30,"F")
    pdf.set_font("Arial","B",20); pdf.set_text_color(255,255,255)
    pdf.cell(0,12,"",ln=True)
    pdf.cell(0,12,"   SHAHIDI AI — Rapport de Survie",ln=True)
    pdf.set_font("Arial","",10); pdf.set_text_color(200,220,255)
    pdf.cell(0,7,f"   Date : {date.today():%d/%m/%Y}   |   Modèle : {model_name}   |   {pat_id}",ln=True)
    pdf.ln(8)
    # Result
    pdf.set_font("Arial","B",16); pdf.set_text_color(26,79,196)
    pdf.cell(0,10,"Résultat de la prédiction",ln=True)
    pdf.set_fill_color(240,246,255)
    pdf.rect(10,pdf.get_y(),190,18,"F")
    pdf.set_font("Arial","B",14); pdf.set_text_color(0,0,0)
    pdf.cell(0,8,"",ln=True)
    pdf.cell(0,10,f"   Survie médiane estimée : {cpred:.1f} mois",ln=True)
    pdf.ln(6)
    # Params
    pdf.set_font("Arial","B",13); pdf.set_text_color(26,79,196)
    pdf.cell(0,10,"Paramètres cliniques utilisés",ln=True)
    pdf.set_fill_color(248,250,255); pdf.set_font("Arial","",11); pdf.set_text_color(0,0,0)
    fill=False
    for k,v in inputs.items():
        label = FEATURE_CONFIG.get(k,k)
        pdf.set_fill_color(248,250,255 if fill else 255)
        pdf.cell(95,8,f"  {label}",1,0,"L",True)
        pdf.cell(95,8,f"  {v}",1,1,"L",True)
        fill=not fill
    pdf.ln(8)
    # Disclaimer
    pdf.set_font("Arial","I",9); pdf.set_text_color(120,120,120)
    pdf.multi_cell(0,5,"Avertissement : Ce rapport est un outil d'aide à la décision clinique généré par intelligence artificielle. Il ne remplace pas l'évaluation médicale d'un clinicien qualifié. C-Index du modèle DeepSurv : 0.92.")
    buf = io.BytesIO(); pdf.output(buf); buf.seek(0)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────

def modelisation():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:1.2rem">
      <h2 style="font-size:1.5rem;font-weight:700;color:#0d1b3e;margin:0 0 .2rem 0">
        🧠 Prédiction de Survie par Intelligence Artificielle
      </h2>
      <p style="color:#6b7a9d;font-size:13px;margin:0">
        Modèles DeepSurv & CoxPH — Saisir les paramètres cliniques du patient
      </p>
    </div>""", unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""<div style="background:#fff8e1;border-left:4px solid #ffa502;border-radius:0 10px 10px 0;
        padding:10px 14px;font-size:13px;color:#7d5a00;margin-bottom:1.2rem">
        ⚠️ <strong>Aide à la décision uniquement</strong> — Les résultats doivent être interprétés par un médecin
        qualifié. Ne pas utiliser comme unique base diagnostique ou thérapeutique.
    </div>""", unsafe_allow_html=True)

    # ── Sidebar config ────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("**🔬 Paramètres du modèle**")
        selected = st.selectbox("Modèle de prédiction",
            list(MODELS.keys()),
            format_func=lambda x: f"{x} — {MODEL_META[x]['type']} (C={MODEL_META[x]['c_index']})")
        meta = MODEL_META[selected]
        st.markdown(f"""
        <div style="background:rgba(255,255,255,.08);border-radius:10px;padding:12px;margin-top:8px">
          <div style="font-size:12px;color:#a0b8e8;text-transform:uppercase;letter-spacing:.07em;margin-bottom:8px">Performances</div>
          <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
            <span>C-Index</span>
            <span style="font-family:JetBrains Mono,monospace;color:{meta['color']};font-weight:700">{meta['c_index']:.2f}</span>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:12px">
            <span>IBS</span>
            <span style="font-family:JetBrains Mono,monospace;color:#a0b8e8">{meta['ibs']:.3f}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        pat_id = st.text_input("ID Patient (optionnel)", placeholder="ex: PAT-2024-001")
        dept   = st.selectbox("Département", ["Cancérologie","Chirurgie Générale"])
        enreg  = st.checkbox("💾 Enregistrer après prédiction", value=True)

    # ── Layout: form + results ─────────────────────────────────────────────────
    col_form, col_res = st.columns([1.6, 1], gap="large")

    with col_form:
        st.markdown("""<div style="background:white;border-radius:16px;padding:1.6rem;
            border:1px solid #e2eaf8;box-shadow:0 2px 16px rgba(26,79,196,.06)">
          <div style="font-size:14px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
               letter-spacing:.06em;margin-bottom:1rem;padding-bottom:.6rem;border-bottom:2px solid #f0f4fb">
            👤 Profil Clinique du Patient
          </div>""", unsafe_allow_html=True)

        inputs = {}

        # Données démographiques
        st.markdown("""<div style="font-size:11px;font-weight:700;color:#1a4fc4;text-transform:uppercase;
            letter-spacing:.1em;margin-bottom:8px">DÉMOGRAPHIE</div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            inputs["AGE"] = st.number_input("Âge (années)", min_value=18, max_value=100,
                value=55, help="Âge du patient au moment du diagnostic")
        with c2:
            sexe = st.selectbox("Sexe biologique", ["Masculin","Féminin"])

        # Antécédents
        st.markdown("""<div style="font-size:11px;font-weight:700;color:#1a4fc4;text-transform:uppercase;
            letter-spacing:.1em;margin:12px 0 8px 0">ANTÉCÉDENTS & COMORBIDITÉS</div>""", unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1: inputs["Cardiopathie"]        = st.selectbox("Cardiopathie",["NON","OUI"],key="card")
        with c2: inputs["Ulceregastrique"]     = st.selectbox("Ulcère gastrique",["NON","OUI"],key="ulc")
        with c3: inputs["Douleurepigastrique"] = st.selectbox("Douleur épigastrique",["OUI","NON"],key="doul")
        c4,c5 = st.columns(2)
        with c4: inputs["Tabac"]      = st.selectbox("Tabagisme actif",["NON","OUI"],key="tab")
        with c5: inputs["Denitrution"]= st.selectbox("Dénutrition",["NON","OUI"],key="den")

        # Caractéristiques tumorales
        st.markdown("""<div style="font-size:11px;font-weight:700;color:#1a4fc4;text-transform:uppercase;
            letter-spacing:.1em;margin:12px 0 8px 0">CARACTÉRISTIQUES TUMORALES</div>""", unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1: inputs["Mucineux"]            = st.selectbox("Type mucineux",["OUI","NON"],key="muc")
        with c2: inputs["Infiltrant"]          = st.selectbox("Type infiltrant",["NON","OUI"],key="inf")
        with c3: inputs["Stenosant"]           = st.selectbox("Type sténosant",["NON","OUI"],key="sten")
        c4,c5,c6 = st.columns(3)
        with c4: inputs["Ulcero-bourgeonnant"] = st.selectbox("Lés. ulcéro-bourg.",["NON","OUI"],key="ulcb")
        with c5: inputs["Metastases"]          = st.selectbox("Métastases",["NON","OUI"],key="meta")
        with c6: inputs["Adenopathie"]         = st.selectbox("Adénopathie",["NON","OUI"],key="aden")

        st.markdown("<br>", unsafe_allow_html=True)
        run = st.button("🧠 Calculer la prédiction de survie", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Results panel ─────────────────────────────────────────────────────────
    with col_res:
        result_ph = st.empty()

        if not run:
            result_ph.markdown("""
            <div style="background:white;border-radius:16px;padding:1.8rem;border:1px solid #e2eaf8;
                        box-shadow:0 2px 16px rgba(26,79,196,.06);text-align:center;min-height:400px;
                        display:flex;flex-direction:column;align-items:center;justify-content:center">
              <div style="font-size:48px;margin-bottom:12px">🔬</div>
              <div style="font-size:16px;font-weight:600;color:#0d1b3e;margin-bottom:6px">
                Résultats de prédiction
              </div>
              <div style="font-size:13px;color:#6b7a9d;max-width:220px">
                Remplissez le formulaire clinique et cliquez sur "Calculer"
              </div>
            </div>""", unsafe_allow_html=True)

    if run:
        with col_res:
            with st.spinner("Analyse en cours..."):
                try:
                    model  = load_model(MODELS[selected])
                    df_in  = encode_features(inputs)
                    pred   = predict_survival(model, df_in)
                    cpred  = clean_prediction(pred)

                    # Survival probabilities
                    p6  = round(100 * np.exp(-np.log(2)*6/cpred),  1)
                    p12 = round(100 * np.exp(-np.log(2)*12/cpred), 1)
                    p24 = round(100 * np.exp(-np.log(2)*24/cpred), 1)
                    p36 = round(100 * np.exp(-np.log(2)*36/cpred), 1)

                    # Risk category
                    if cpred >= 36:
                        risk_label, risk_color, risk_icon = "Faible risque",   "#2ed573", "🟢"
                    elif cpred >= 18:
                        risk_label, risk_color, risk_icon = "Risque modéré",   "#ffa502", "🟡"
                    elif cpred >= 8:
                        risk_label, risk_color, risk_icon = "Risque élevé",    "#ff6b35", "🟠"
                    else:
                        risk_label, risk_color, risk_icon = "Risque très élevé","#ff4757","🔴"

                    # Risk needle position
                    max_s = 60
                    needle_pct = max(5, min(95, int((1 - cpred/max_s)*95)))

                    # Result card
                    st.markdown(f"""
                    <div style="background:white;border-radius:16px;padding:1.6rem;border:1px solid #e2eaf8;
                                box-shadow:0 2px 16px rgba(26,79,196,.06);border-top:4px solid {risk_color}">
                      <div style="text-align:center;margin-bottom:1.2rem;padding-bottom:1rem;border-bottom:1px solid #f0f4fb">
                        <div style="font-size:11px;color:#6b7a9d;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">
                          SURVIE MÉDIANE ESTIMÉE · {selected}
                        </div>
                        <div style="font-family:'JetBrains Mono',monospace;font-size:3.5rem;font-weight:600;
                                    color:#0d1b3e;line-height:1">{cpred:.0f}</div>
                        <div style="font-size:15px;color:#6b7a9d;margin-top:2px">mois</div>
                        <div style="display:inline-flex;align-items:center;gap:6px;background:{risk_color}18;
                                    border:1px solid {risk_color}44;padding:4px 14px;border-radius:20px;
                                    font-size:12px;font-weight:700;color:{risk_color};margin-top:10px">
                          {risk_icon} {risk_label}
                        </div>
                      </div>

                      <div style="margin-bottom:1rem">
                        <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7a9d;margin-bottom:4px">
                          <span>Risque faible</span><span>Risque élevé</span>
                        </div>
                        <div style="background:linear-gradient(90deg,#2ed573,#ffa502,#ff4757);
                                    border-radius:5px;height:8px;position:relative">
                          <div style="position:absolute;left:{needle_pct}%;top:-5px;transform:translateX(-50%);
                                      width:4px;height:18px;background:#0d1b3e;border-radius:2px;
                                      box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>
                        </div>
                      </div>

                      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:1rem">
                        {"".join([
                          f'<div style="background:#f8faff;border-radius:8px;padding:10px 12px">'
                          f'<div style="font-size:10px;color:#6b7a9d;margin-bottom:2px">SURVIE À {m} MOIS</div>'
                          f'<div style="font-family:JetBrains Mono,monospace;font-size:1.2rem;font-weight:600;'
                          f'color:{"#2ed573" if p>=50 else "#ffa502" if p>=30 else "#ff4757"}">{p}%</div></div>'
                          for p,m in [(p6,6),(p12,12),(p24,24),(p36,36)]
                        ])}
                      </div>

                      <div style="background:#f8faff;border-radius:8px;padding:10px 12px;margin-bottom:1rem">
                        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                          <span style="color:#6b7a9d">Modèle utilisé</span>
                          <span style="font-weight:600;color:#0d1b3e">{selected}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:12px">
                          <span style="color:#6b7a9d">C-Index</span>
                          <span style="font-family:JetBrains Mono,monospace;font-weight:700;
                                       color:{MODEL_META[selected]['color']}">{MODEL_META[selected]['c_index']:.2f}</span>
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)

                    # Survival curve
                    st.markdown("""<div style="background:white;border-radius:14px;padding:1rem 1.2rem;
                        border:1px solid #e2eaf8;box-shadow:0 2px 8px rgba(26,79,196,.05);margin-top:.8rem">
                        <div style="font-size:12px;font-weight:700;color:#0d1b3e;margin-bottom:.5rem">
                        Courbe de survie individuelle</div>""", unsafe_allow_html=True)
                    st.plotly_chart(_surv_curve_fig(cpred), use_container_width=True,
                        config={"displayModeBar":False})
                    st.markdown("</div>", unsafe_allow_html=True)

                    # Save patient
                    if enreg:
                        rec = df_in.to_dict(orient="records")[0]
                        rec["Tempsdesuivi"] = round(cpred, 1)
                        rec["Deces"] = "OUI"
                        if save_new_patient(rec):
                            st.success("✅ Patient enregistré dans la base de données")

                    # PDF export
                    rec_display = {FEATURE_CONFIG.get(k,k): ("OUI" if v==1.0 else "NON") if k!="AGE" else int(v)
                                   for k,v in inputs.items()}
                    pdf_bytes = _pdf_report(rec_display, cpred, selected, pat_id)
                    st.download_button("📄 Télécharger le rapport PDF", pdf_bytes,
                        file_name=f"rapport_{pat_id or 'patient'}_{date.today():%Y%m%d}.pdf",
                        mime="application/pdf", use_container_width=True)

                except Exception as e:
                    st.error(f"❌ Erreur de prédiction : {e}")
                    st.info("💡 Vérifiez que les modèles sont bien présents dans le dossier `models/`")
