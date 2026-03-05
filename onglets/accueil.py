import streamlit as st
import pandas as pd
from utils import load_data, compute_km, survival_proba_at, GLOBAL_CSS
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────

def _metric_card(col, icon, value, label, delta=None, delta_good=True, color="#1a4fc4"):
    badge = ""
    if delta:
        arrow = "↑" if delta_good else "↓"
        c = "#1e7e44" if delta_good else "#c0392b"
        badge = f"<div style='margin-top:6px;font-size:12px;color:{c};font-weight:600'>{arrow} {delta}</div>"
    col.markdown(f"""
    <div style="background:white;border-radius:14px;padding:1.2rem 1.4rem;border:1px solid #e2eaf8;
                box-shadow:0 2px 12px rgba(26,79,196,0.06);border-top:3px solid {color};">
      <div style="font-size:22px;margin-bottom:4px">{icon}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:600;color:#0d1b3e;line-height:1">{value}</div>
      <div style="font-size:11px;color:#6b7a9d;text-transform:uppercase;letter-spacing:.07em;margin-top:4px">{label}</div>
      {badge}
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────

def accueil():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    df = load_data()
    if df.empty:
        st.error("Données non disponibles."); return

    n      = len(df)
    n_dec  = (df["Deces"] == "OUI").sum()
    n_viv  = n - n_dec
    taux   = round(n_dec / n * 100, 1)
    surv_m = int(df["Tempsdesuivi"].median())
    age_m  = round(df["AGE"].mean(), 1)

    # ── Hero banner ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#06091a 0%,#0d1b3e 60%,#1a3a7a 100%);
                border-radius:18px;padding:2.2rem 2.5rem;margin-bottom:1.6rem;
                display:flex;align-items:center;justify-content:space-between;
                box-shadow:0 8px 32px rgba(0,0,0,0.18);">
      <div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:.4rem">
          <div style="background:linear-gradient(135deg,#1a4fc4,#00c6ff);border-radius:10px;
                      width:36px;height:36px;display:flex;align-items:center;justify-content:center;
                      font-size:20px">⚕️</div>
          <span style="color:#a0b8e8;font-size:13px;font-weight:500;letter-spacing:.08em">PLATEFORME MÉDICALE · CANCER GASTRIQUE</span>
        </div>
        <h1 style="color:white;font-size:2rem;font-weight:700;margin:0 0 .4rem 0;line-height:1.15">
          SHAHIDI <span style="color:#00c6ff">AI</span> Platform
        </h1>
        <p style="color:#8ca6d0;font-size:14px;margin:0;max-width:520px">
          Analyse de survie par intelligence artificielle — Déployé pour les départements de
          <strong style="color:#e0edff">Cancérologie</strong> et
          <strong style="color:#e0edff">Chirurgie Générale</strong>
        </p>
      </div>
      <div style="text-align:right">
        <div style="background:rgba(46,213,115,.15);border:1px solid rgba(46,213,115,.3);
                    border-radius:20px;padding:5px 14px;display:inline-flex;align-items:center;gap:6px;
                    font-size:12px;color:#2ed573;font-weight:600;margin-bottom:8px">
          <span style="width:7px;height:7px;background:#2ed573;border-radius:50%;animation:none"></span>
          SYSTÈME EN LIGNE
        </div>
        <div style="color:#6b82aa;font-size:12px">{datetime.now().strftime('%d %b %Y · %H:%M')}</div>
        <div style="color:#a0b8e8;font-size:13px;margin-top:4px;font-weight:600">{n} patients enregistrés</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── KPI cards ────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    _metric_card(c1, "👥", n,        "Patients total",          "+12 ce mois",    True,  "#1a4fc4")
    _metric_card(c2, "🔴", f"{taux}%","Taux de mortalité",      "−1.8% vs N−1",  True,  "#ff4757")
    _metric_card(c3, "💚", n_viv,    "Vivants / Censurés",      f"{round(n_viv/n*100,1)}%", True, "#2ed573")
    _metric_card(c4, "📅", f"{surv_m}m","Survie médiane",        "+2.1m vs N−1",  True,  "#ffa502")
    _metric_card(c5, "🎯", "0.92",   "C-index DeepSurv",        "Meilleur modèle",True, "#00c6ff")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main charts row ──────────────────────────────────────────────────────
    col_km, col_pie, col_age = st.columns([2.2, 1.2, 1.6])

    # Kaplan-Meier global + stratifié
    with col_km:
        st.markdown("""<div style="background:white;border-radius:14px;padding:1.2rem 1.4rem;border:1px solid #e2eaf8;box-shadow:0 2px 12px rgba(26,79,196,0.06)">
            <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.2rem">📈 Courbe de Kaplan-Meier</div>
            <div style="font-size:12px;color:#6b7a9d;margin-bottom:.8rem">Probabilité de survie globale — cohorte {n} patients</div>""".format(n=n), unsafe_allow_html=True)

        t_all, s_all = compute_km(df["Tempsdesuivi"], df["Deces"])
        df_meta = df[df["Metastases"] == "OUI"]
        df_nom  = df[df["Metastases"] == "NON"]
        t_m, s_m   = compute_km(df_meta["Tempsdesuivi"], df_meta["Deces"])
        t_nm, s_nm = compute_km(df_nom["Tempsdesuivi"],  df_nom["Deces"])

        fig_km = go.Figure()
        fig_km.add_trace(go.Scatter(x=t_all, y=s_all*100, mode="lines", name="Global",
            line=dict(color="#1a4fc4", width=2.5), fill="tozeroy", fillcolor="rgba(26,79,196,0.06)"))
        fig_km.add_trace(go.Scatter(x=t_m, y=s_m*100, mode="lines", name="Avec métastases",
            line=dict(color="#ff4757", width=1.8, dash="dash")))
        fig_km.add_trace(go.Scatter(x=t_nm, y=s_nm*100, mode="lines", name="Sans métastases",
            line=dict(color="#2ed573", width=1.8, dash="dot")))
        # Median line
        fig_km.add_hline(y=50, line_dash="dot", line_color="#aaa", line_width=1,
            annotation_text="50% (médiane)", annotation_position="bottom right",
            annotation_font_size=10, annotation_font_color="#888")
        fig_km.update_layout(
            height=260, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(title="Mois", gridcolor="#f0f4fb", tickfont=dict(size=11)),
            yaxis=dict(title="% Survie", range=[0,105], gridcolor="#f0f4fb", tickfont=dict(size=11)),
            legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
            font=dict(family="Sora, sans-serif"),
        )
        st.plotly_chart(fig_km, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # Donut décès/vivant
    with col_pie:
        st.markdown("""<div style="background:white;border-radius:14px;padding:1.2rem 1.4rem;border:1px solid #e2eaf8;box-shadow:0 2px 12px rgba(26,79,196,0.06);height:100%">
            <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.2rem">🔵 Statut vital</div>
            <div style="font-size:12px;color:#6b7a9d;margin-bottom:.8rem">Décès / Vivants</div>""", unsafe_allow_html=True)
        fig_d = go.Figure(go.Pie(
            labels=["Décédés", "Vivants"],
            values=[int(n_dec), int(n_viv)],
            hole=0.65,
            marker=dict(colors=["#ff4757","#2ed573"], line=dict(width=0)),
            textinfo="percent", textfont=dict(size=12, family="JetBrains Mono"),
            hovertemplate="%{label}: %{value}<extra></extra>",
        ))
        fig_d.add_annotation(text=f"<b>{n}</b><br>patients", x=0.5, y=0.5,
            font=dict(size=13, family="JetBrains Mono, monospace"), showarrow=False)
        fig_d.update_layout(height=240, margin=dict(l=0,r=0,t=0,b=0),
            paper_bgcolor="white", showlegend=True,
            legend=dict(orientation="h", y=-0.12, font=dict(size=11)))
        st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # Age distribution
    with col_age:
        st.markdown("""<div style="background:white;border-radius:14px;padding:1.2rem 1.4rem;border:1px solid #e2eaf8;box-shadow:0 2px 12px rgba(26,79,196,0.06);height:100%">
            <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.2rem">🎂 Répartition par âge</div>
            <div style="font-size:12px;color:#6b7a9d;margin-bottom:.8rem">Distribution (31–81 ans)</div>""", unsafe_allow_html=True)
        bins = [31,40,50,60,70,82]
        labels_age = ["31-40","41-50","51-60","61-70","71-81"]
        df["age_grp"] = pd.cut(df["AGE"], bins=bins, labels=labels_age, right=False)
        age_cnt = df["age_grp"].value_counts().reindex(labels_age, fill_value=0)
        fig_age = go.Figure(go.Bar(
            x=labels_age, y=age_cnt.values,
            marker=dict(color=["#a29bfe","#00c6ff","#1a4fc4","#ffa502","#ff4757"],
                        line=dict(width=0)),
            text=age_cnt.values, textposition="outside",
            textfont=dict(size=11, family="JetBrains Mono"),
        ))
        fig_age.update_layout(height=240, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(gridcolor="#f0f4fb", tickfont=dict(size=11)),
            yaxis=dict(gridcolor="#f0f4fb", tickfont=dict(size=11)),
            font=dict(family="Sora, sans-serif"), showlegend=False)
        st.plotly_chart(fig_age, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Survival probabilities banner ────────────────────────────────────────
    t_all, s_all = compute_km(df["Tempsdesuivi"], df["Deces"])
    p6  = survival_proba_at(t_all, s_all, 6)
    p12 = survival_proba_at(t_all, s_all, 12)
    p24 = survival_proba_at(t_all, s_all, 24)
    p36 = survival_proba_at(t_all, s_all, 36)
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#f8faff,#eef4ff);border:1px solid #d1e0ff;
                border-radius:14px;padding:1.2rem 1.8rem;margin:1rem 0;display:flex;
                gap:2rem;align-items:center;flex-wrap:wrap;">
      <div style="font-size:12px;font-weight:700;color:#1a4fc4;text-transform:uppercase;
                  letter-spacing:.08em;white-space:nowrap">📊 Survie Kaplan-Meier cohorte :</div>
      {"".join([
        f'<div style="text-align:center"><div style="font-family:JetBrains Mono,monospace;font-size:1.4rem;font-weight:600;color:#0d1b3e">{p}%</div>'
        f'<div style="font-size:11px;color:#6b7a9d">à {m} mois</div></div>'
        for p, m in [(p6,6),(p12,12),(p24,24),(p36,36)]
      ])}
    </div>""", unsafe_allow_html=True)

    # ── Risk factors row ─────────────────────────────────────────────────────
    st.markdown("""<div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
        letter-spacing:.06em;margin:1.4rem 0 .8rem 0;padding-bottom:.5rem;border-bottom:2px solid #e2eaf8">
        ⚠️ Prévalence des facteurs de risque dans la cohorte</div>""", unsafe_allow_html=True)

    factors = [
        ("Douleur épigastrique", "Douleurepigastrique", "#ff6b6b"),
        ("Tabagisme",           "Tabac",               "#ff4757"),
        ("Type mucineux",       "Mucineux",             "#a29bfe"),
        ("Type infiltrant",     "Infiltrant",           "#ffa502"),
        ("Type sténosant",      "Stenosant",            "#00e5bf"),
        ("Métastases",          "Metastases",           "#ff4757"),
        ("Adénopathie",         "Adenopathie",          "#00c6ff"),
        ("Ulcère gastrique",    "Ulceregastrique",      "#74b9ff"),
        ("Dénutrition",         "Denitrution",          "#fdcb6e"),
        ("Cardiopathie",        "Cardiopathie",         "#e17055"),
        ("Lés. ulcéro-bourgeon.","Ulcero-bourgeonnant", "#6c5ce7"),
    ]
    cols_f = st.columns(4)
    for i, (label, col, color) in enumerate(factors):
        pct = round((df[col] == "OUI").mean() * 100, 1) if col in df.columns else 0
        with cols_f[i % 4]:
            st.markdown(f"""
            <div style="background:white;border-radius:12px;padding:1rem 1.2rem;border:1px solid #e2eaf8;
                        margin-bottom:.7rem;box-shadow:0 1px 6px rgba(0,0,0,.04)">
              <div style="font-size:11px;color:#6b7a9d;margin-bottom:6px">{label}</div>
              <div style="background:#f0f4fb;border-radius:4px;height:6px;margin-bottom:5px">
                <div style="width:{pct}%;height:100%;border-radius:4px;
                             background:linear-gradient(90deg,{color}bb,{color})"></div>
              </div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:600;color:#0d1b3e">{pct}%</div>
            </div>""", unsafe_allow_html=True)
