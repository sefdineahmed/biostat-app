import streamlit as st, os
from utils import TEAM, MODEL_META, GLOBAL_CSS

def a_propos():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom:1.4rem">
      <h2 style="font-size:1.5rem;font-weight:700;color:#0d1b3e;margin:0 0 .2rem 0">
        ℹ️ À Propos de SHAHIDI AI
      </h2>
      <p style="color:#6b7a9d;font-size:13px;margin:0">
        Plateforme d'analyse de survie par intelligence artificielle — Cancer gastrique
      </p>
    </div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns([1.6, 1], gap="large")

    with col_l:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#06091a,#0d1b3e);border-radius:18px;
                    padding:2rem;margin-bottom:1rem">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:1rem">
            <div style="background:linear-gradient(135deg,#1a4fc4,#00c6ff);border-radius:12px;
                        width:44px;height:44px;display:flex;align-items:center;justify-content:center;
                        font-size:22px">⚕️</div>
            <div>
              <div style="color:white;font-size:1.4rem;font-weight:700;line-height:1">SHAHIDI <span style="color:#00c6ff">AI</span></div>
              <div style="color:#8ca6d0;font-size:12px">v2.0 · Plateforme médicale · Cancer gastrique</div>
            </div>
          </div>
          <p style="color:#a0b8e8;font-size:14px;line-height:1.7;margin-bottom:1rem">
            SHAHIDI est une plateforme clinique d'aide à la décision médicale dédiée à l'analyse de survie
            des patients atteints de <strong style="color:#e0edff">cancer gastrique</strong>. Elle intègre des
            modèles de deep learning (<strong style="color:#00c6ff">DeepSurv</strong>) et de statistique de survie
            (<strong style="color:#2ed573">Cox Proportional Hazard</strong>) pour prédire la survie médiane des patients.
          </p>
          <p style="color:#8ca6d0;font-size:13px;line-height:1.6">
            Développée à l'<strong style="color:#a0c0ff">Université Alioune Diop de Bambey</strong>, cette plateforme
            est déployée pour les départements de <strong style="color:#a0c0ff">Cancérologie</strong> et
            <strong style="color:#a0c0ff">Chirurgie Générale</strong>.
          </p>
        </div>""", unsafe_allow_html=True)

        # Model perf
        st.markdown("""<div style="background:white;border-radius:14px;padding:1.4rem;border:1px solid #e2eaf8;
            box-shadow:0 2px 10px rgba(26,79,196,.05);margin-bottom:1rem">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
               letter-spacing:.06em;margin-bottom:1rem">⚡ Performance des Modèles</div>
          <table style="width:100%;border-collapse:collapse;font-size:13px">
            <tr style="background:#f8faff">
              <th style="padding:8px 12px;text-align:left;color:#6b7a9d;font-weight:600">Modèle</th>
              <th style="padding:8px 12px;color:#6b7a9d;font-weight:600">Type</th>
              <th style="padding:8px 12px;color:#6b7a9d;font-weight:600">C-Index</th>
              <th style="padding:8px 12px;color:#6b7a9d;font-weight:600">IBS</th>
            </tr>""" + "".join([
              f"""<tr style="border-top:1px solid #f0f4fb;{'background:#f0fff5' if m=='DeepSurv' else ''}">
                <td style="padding:8px 12px;font-weight:600;color:#0d1b3e">{m}</td>
                <td style="padding:8px 12px;color:#6b7a9d;font-size:12px">{MODEL_META[m]['type']}</td>
                <td style="padding:8px 12px;font-family:JetBrains Mono,monospace;font-weight:700;
                           color:{MODEL_META[m]['color']}">{MODEL_META[m]['c_index']:.2f}
                   {'<span style="background:#f0fff5;border:1px solid #b7f5ca;border-radius:4px;font-size:10px;padding:1px 5px;margin-left:4px;color:#1e7e44">BEST</span>' if m=='DeepSurv' else ''}</td>
                <td style="padding:8px 12px;font-family:JetBrains Mono,monospace;color:#6b7a9d">{MODEL_META[m]['ibs']:.3f}</td>
              </tr>"""
              for m in MODEL_META
            ]) + "</table></div>", unsafe_allow_html=True)

        # KPIs épidémio
        st.markdown("""<div style="background:white;border-radius:14px;padding:1.4rem;border:1px solid #e2eaf8;box-shadow:0 2px 10px rgba(26,79,196,.05)">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:1rem">
            📊 Indicateurs Épidémiologiques — Cohorte</div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">""" +
          "".join([
            f'<div style="background:#f8faff;border-radius:10px;padding:12px;text-align:center">'
            f'<div style="font-size:20px">{ic}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:1.3rem;font-weight:600;color:#0d1b3e">{v}</div>'
            f'<div style="font-size:11px;color:#6b7a9d">{lb}</div></div>'
            for ic,v,lb in [("👥","337","Patients cohorte"),("📅","21 mois","Survie médiane"),
                            ("🎯","0.92","C-Index max"),("🔴","66.2%","Taux mortalité"),
                            ("🎂","52.1 ans","Âge moyen"),("🔬","86.9%","Douleur épigast.")]
          ]) + "</div></div>", unsafe_allow_html=True)

    with col_r:
        # Team
        st.markdown("""<div style="background:white;border-radius:14px;padding:1.4rem;border:1px solid #e2eaf8;
            box-shadow:0 2px 10px rgba(26,79,196,.05);margin-bottom:1rem">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
               letter-spacing:.06em;margin-bottom:1rem">👥 Équipe de Recherche</div>""", unsafe_allow_html=True)

        for m in TEAM:
            avatar = "👨‍🏫" if "Pr." in m["name"] else "👨‍🔬" if "PhD" in m["name"] else "👨‍💻"
            color  = "#1a4fc4" if "Pr." in m["name"] else "#00e5bf" if "PhD" in m["name"] else "#a29bfe"
            st.markdown(f"""
            <div style="display:flex;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid #f0f4fb">
              <div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,{color}44,{color}22);
                          border:2px solid {color}44;display:flex;align-items:center;justify-content:center;
                          font-size:20px;flex-shrink:0">{avatar}</div>
              <div>
                <div style="font-size:14px;font-weight:600;color:#0d1b3e">{m['name']}</div>
                <div style="font-size:12px;color:#6b7a9d">{m['role']}</div>
                <div style="font-size:11px;color:{color};font-weight:500">{m['etablissement']}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Partners
        st.markdown("""<div style="background:white;border-radius:14px;padding:1.4rem;border:1px solid #e2eaf8;
            box-shadow:0 2px 10px rgba(26,79,196,.05);margin-bottom:1rem">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
               letter-spacing:.06em;margin-bottom:12px">🤝 Partenaires</div>""", unsafe_allow_html=True)
        for p in [("INSERM","#1a4fc4"),("OMS","#2ed573"),("CHU Dantec","#ffa502"),("UAD Bambey","#a29bfe")]:
            st.markdown(f"""<span style="background:{p[1]}18;border:1px solid {p[1]}44;color:{p[1]};
                padding:4px 12px;border-radius:6px;font-size:12px;font-weight:700;
                margin-right:6px;margin-bottom:6px;display:inline-block">{p[0]}</span>""", unsafe_allow_html=True)

        # Version info
        st.markdown("""</div>
        <div style="background:#f8faff;border-radius:14px;padding:1.2rem;border:1px solid #e2eaf8;margin-top:0">
          <div style="font-size:12px;color:#6b7a9d;margin-bottom:4px">Version</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:13px;color:#0d1b3e;font-weight:600">SHAHIDI v2.0.0 · 2024</div>
          <div style="font-size:12px;color:#6b7a9d;margin-top:6px">Licence académique · Usage clinique supervisé</div>
          <div style="font-size:12px;color:#6b7a9d;margin-top:4px">contact@shahidi-ai.sn</div>
        </div>""", unsafe_allow_html=True)
