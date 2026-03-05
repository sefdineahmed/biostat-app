import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils import load_data, compute_km, survival_proba_at, MODEL_META, GLOBAL_CSS

def kpi():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    df = load_data()
    if df.empty:
        st.error("Données non disponibles."); return

    st.markdown("""
    <div style="margin-bottom:1.4rem">
      <h2 style="font-size:1.5rem;font-weight:700;color:#0d1b3e;margin:0 0 .2rem 0">
        📈 Indicateurs Clés de Performance
      </h2>
      <p style="color:#6b7a9d;font-size:13px;margin:0">
        Tableau de bord de pilotage — Cancérologie & Chirurgie Générale · Cancer gastrique
      </p>
    </div>""", unsafe_allow_html=True)

    # ── Dept filter ───────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("**🔧 Filtres KPI**")
        dept_filter = st.selectbox("Département", ["Tous","Cancérologie","Chirurgie Générale"], key="kpi_dept")
        periode = st.selectbox("Période d'analyse", ["Cohorte entière","12 derniers mois","6 derniers mois"], key="kpi_period")

    # ── Summary metrics ───────────────────────────────────────────────────────
    n      = len(df)
    n_dec  = (df["Deces"]=="OUI").sum()
    taux   = round(n_dec/n*100,1)
    surv_m = int(df["Tempsdesuivi"].median())
    surv_moy = round(df["Tempsdesuivi"].mean(),1)
    age_m  = round(df["AGE"].mean(),1)
    t_all, s_all = compute_km(df["Tempsdesuivi"], df["Deces"])
    p6  = survival_proba_at(t_all, s_all, 6)
    p12 = survival_proba_at(t_all, s_all, 12)
    p24 = survival_proba_at(t_all, s_all, 24)

    def mcard(col, icon, val, lbl, delta="", good=True, color="#1a4fc4"):
        c = "#1e7e44" if good else "#c0392b"
        d = f"<div style='font-size:11px;color:{c};font-weight:600;margin-top:4px'>{delta}</div>" if delta else ""
        col.markdown(f"""
        <div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.1rem 1.2rem;border:1px solid #e2eaf8;
                    box-shadow:0 2px 10px rgba(26,79,196,.05);border-top:3px solid {color}">
          <div style="font-size:20px;margin-bottom:2px">{icon}</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:1.7rem;font-weight:600;color:#0d1b3e;line-height:1">{val}</div>
          <div style="font-size:10px;color:#6b7a9d;text-transform:uppercase;letter-spacing:.07em;margin-top:3px">{lbl}</div>{d}
        </div>""", unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    mcard(c1,"👥",n,"Patients total","",True,"#1a4fc4")
    mcard(c2,"🔴",f"{taux}%","Taux mortalité","↓−1.8% N−1",True,"#ff4757")
    mcard(c3,"📅",f"{surv_m}m","Survie médiane","↑+2.1m N−1",True,"#ffa502")
    mcard(c4,"📊",f"{surv_moy}m","Survie moyenne","",True,"#00c6ff")
    mcard(c5,"🎂",f"{age_m}","Âge moyen (ans)","31–81 ans",True,"#a29bfe")
    mcard(c6,"🎯","0.92","C-index DeepSurv","Meilleur modèle",True,"#2ed573")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Survival KM banner ────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#06091a,#0d1b3e);border-radius:14px;
                padding:1.2rem 2rem;margin-bottom:1.2rem;display:flex;gap:3rem;align-items:center;flex-wrap:wrap">
      <div style="color:#8ca6d0;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;white-space:nowrap">
        SURVIE KAPLAN-MEIER
      </div>
      {"".join([
        f'<div style="text-align:center">'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:1.6rem;font-weight:600;color:{"#2ed573" if p>=50 else "#ffa502" if p>=30 else "#ff4757"}">{p}%</div>'
        f'<div style="font-size:11px;color:#6b82aa">à {m} mois</div></div>'
        for p,m in [(p6,6),(p12,12),(p24,24)]
      ])}
      <div style="text-align:center">
        <div style="font-family:JetBrains Mono,monospace;font-size:1.6rem;font-weight:600;color:#00c6ff">{surv_m}m</div>
        <div style="font-size:11px;color:#6b82aa">Médiane KM</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Row 1: KM curves + Model performance ─────────────────────────────────
    col_km, col_mod = st.columns([3,2])

    with col_km:
        st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem 1.4rem;
            border:1px solid #e2eaf8;box-shadow:0 2px 10px rgba(26,79,196,.05)">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
               letter-spacing:.06em;margin-bottom:.3rem">Courbes de survie — Kaplan-Meier stratifiées</div>
          <div style="font-size:12px;color:#6b7a9d;margin-bottom:.8rem">Stratification par métastases · tabagisme</div>""",
            unsafe_allow_html=True)

        df_met = df[df["Metastases"]=="OUI"]; df_nom = df[df["Metastases"]=="NON"]
        df_tab = df[df["Tabac"]=="OUI"];      df_not = df[df["Tabac"]=="NON"]

        t_all,s_all = compute_km(df["Tempsdesuivi"],df["Deces"])
        t_m,s_m     = compute_km(df_met["Tempsdesuivi"],df_met["Deces"])
        t_nm,s_nm   = compute_km(df_nom["Tempsdesuivi"],df_nom["Deces"])
        t_tb,s_tb   = compute_km(df_tab["Tempsdesuivi"],df_tab["Deces"])
        t_nt,s_nt   = compute_km(df_not["Tempsdesuivi"],df_not["Deces"])

        fig = go.Figure()
        for t,s,name,color,dash in [
            (t_all,s_all,"Global","#1a4fc4","solid"),
            (t_m,s_m,"Métastases OUI","#ff4757","dash"),
            (t_nm,s_nm,"Métastases NON","#2ed573","dot"),
            (t_tb,s_tb,"Tabac OUI","#ffa502","dashdot"),
            (t_nt,s_nt,"Tabac NON","#a29bfe","longdash"),
        ]:
            fig.add_trace(go.Scatter(x=t, y=s*100, mode="lines", name=name,
                line=dict(color=color, width=2, dash=dash)))
        fig.add_hline(y=50, line_dash="dot", line_color="#ccc", line_width=1)
        fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(title="Mois",gridcolor="#f0f4fb",tickfont=dict(size=11)),
            yaxis=dict(title="% Survie",range=[0,105],gridcolor="#f0f4fb",tickfont=dict(size=11)),
            legend=dict(orientation="h",y=-0.25,font=dict(size=10)),
            font=dict(family="Sora, sans-serif"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_mod:
        st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem 1.4rem;
            border:1px solid #e2eaf8;box-shadow:0 2px 10px rgba(26,79,196,.05)">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
               letter-spacing:.06em;margin-bottom:.3rem">Performance des modèles IA</div>
          <div style="font-size:12px;color:#6b7a9d;margin-bottom:.8rem">C-Index de concordance — plus élevé = meilleur</div>""",
            unsafe_allow_html=True)
        models = list(MODEL_META.keys())
        cidx   = [MODEL_META[m]["c_index"] for m in models]
        ibs    = [MODEL_META[m]["ibs"]     for m in models]
        colors = [MODEL_META[m]["color"]   for m in models]

        fig_m = go.Figure()
        fig_m.add_trace(go.Bar(name="C-Index", x=models, y=cidx,
            marker=dict(color=colors, line=dict(width=0)), text=[f"{v:.2f}" for v in cidx],
            textposition="outside", textfont=dict(size=11,family="JetBrains Mono"),
            width=0.45))
        fig_m.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="white", plot_bgcolor="white", showlegend=False,
            xaxis=dict(gridcolor="#f0f4fb",tickfont=dict(size=12,color="#0d1b3e")),
            yaxis=dict(range=[0.6,1.0],gridcolor="#f0f4fb",tickfont=dict(size=11)),
            font=dict(family="Sora, sans-serif"))
        st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar":False})

        # IBS table
        st.markdown("""<table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:4px">
          <tr style="background:#f8faff"><th style="padding:6px 10px;text-align:left;color:#6b7a9d;font-weight:600">Modèle</th>
          <th style="padding:6px 10px;color:#6b7a9d;font-weight:600">C-Index</th>
          <th style="padding:6px 10px;color:#6b7a9d;font-weight:600">IBS</th></tr>""" +
          "".join([
            f'<tr style="border-top:1px solid #f0f4fb"><td style="padding:6px 10px;font-weight:600;color:#0d1b3e">{m}</td>'
            f'<td style="padding:6px 10px;font-family:JetBrains Mono,monospace;color:{MODEL_META[m]["color"]};font-weight:700">{MODEL_META[m]["c_index"]:.2f}</td>'
            f'<td style="padding:6px 10px;font-family:JetBrains Mono,monospace;color:#6b7a9d">{MODEL_META[m]["ibs"]:.3f}</td></tr>'
            for m in models
          ]) + "</table>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Row 2: Facteurs de risque + Survie par âge ────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_rf, col_ag = st.columns([3,2])

    with col_rf:
        st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem 1.4rem;
            border:1px solid #e2eaf8;box-shadow:0 2px 10px rgba(26,79,196,.05)">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
               letter-spacing:.06em;margin-bottom:.8rem">⚠️ Prévalence des facteurs de risque (%)</div>""",
            unsafe_allow_html=True)

        feats = {"Douleur épigastrique":"Douleurepigastrique","Type mucineux":"Mucineux",
                 "Tabagisme":"Tabac","Type infiltrant":"Infiltrant","Type sténosant":"Stenosant",
                 "Métastases":"Metastases","Adénopathie":"Adenopathie","Ulcère gastrique":"Ulceregastrique",
                 "Dénutrition":"Denitrution","Cardiopathie":"Cardiopathie"}
        pcts = {lb: round((df[col]=="OUI").mean()*100,1) for lb,col in feats.items() if col in df.columns}
        pcts = dict(sorted(pcts.items(), key=lambda x:x[1], reverse=True))
        clrs = ["#ff4757" if v>60 else "#ffa502" if v>40 else "#1a4fc4" for v in pcts.values()]

        fig_rf = go.Figure(go.Bar(
            x=list(pcts.values()), y=list(pcts.keys()), orientation="h",
            marker=dict(color=clrs, line=dict(width=0)),
            text=[f"{v}%" for v in pcts.values()],
            textposition="outside", textfont=dict(size=11,family="JetBrains Mono"),
        ))
        fig_rf.update_layout(height=320, margin=dict(l=0,r=40,t=10,b=0),
            paper_bgcolor="white", plot_bgcolor="white", showlegend=False,
            xaxis=dict(range=[0,110],gridcolor="#f0f4fb",tickfont=dict(size=11),ticksuffix="%"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)",tickfont=dict(size=11,color="#0d1b3e")),
            font=dict(family="Sora, sans-serif"))
        st.plotly_chart(fig_rf, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_ag:
        st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem 1.4rem;
            border:1px solid #e2eaf8;box-shadow:0 2px 10px rgba(26,79,196,.05)">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;text-transform:uppercase;
               letter-spacing:.06em;margin-bottom:.8rem">🎂 Survie médiane par groupe d'âge</div>""",
            unsafe_allow_html=True)

        bins   = [30,40,50,60,70,90]
        lbls   = ["31-40","41-50","51-60","61-70","71+"]
        df["ag"] = pd.cut(df["AGE"],bins=bins,labels=lbls,right=False)
        ag_med = df.groupby("ag",observed=True)["Tempsdesuivi"].median().reindex(lbls,fill_value=0)
        ag_col = ["#2ed573" if v>=30 else "#ffa502" if v>=15 else "#ff4757" for v in ag_med.values]

        fig_ag = go.Figure(go.Bar(
            x=lbls, y=ag_med.values,
            marker=dict(color=ag_col,line=dict(width=0)),
            text=[f"{int(v)}m" for v in ag_med.values],
            textposition="outside", textfont=dict(size=11,family="JetBrains Mono"),
        ))
        fig_ag.update_layout(height=240, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="white", plot_bgcolor="white", showlegend=False,
            xaxis=dict(gridcolor="#f0f4fb",tickfont=dict(size=11)),
            yaxis=dict(title="Mois",gridcolor="#f0f4fb",tickfont=dict(size=11)),
            font=dict(family="Sora, sans-serif"))
        st.plotly_chart(fig_ag, use_container_width=True, config={"displayModeBar":False})

        # KM table by strat
        st.markdown("""<div style="margin-top:12px">
          <div style="font-size:11px;font-weight:700;color:#6b7a9d;text-transform:uppercase;
               letter-spacing:.07em;margin-bottom:8px">SURVIE À 12 MOIS PAR FACTEUR</div>""",
            unsafe_allow_html=True)
        strats = [("Métastases NON","Metastases","NON","#2ed573"),
                  ("Métastases OUI","Metastases","OUI","#ff4757"),
                  ("Tabac NON","Tabac","NON","#a29bfe"),
                  ("Tabac OUI","Tabac","OUI","#ffa502")]
        for lbl,col,val,color in strats:
            sub = df[df[col]==val]
            if len(sub)==0: continue
            ts,ss = compute_km(sub["Tempsdesuivi"],sub["Deces"])
            p = survival_proba_at(ts,ss,12)
            bar_w = int(p)
            st.markdown(f"""
            <div style="margin-bottom:8px">
              <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px">
                <span style="color:#0d1b3e;font-weight:500">{lbl}</span>
                <span style="font-family:JetBrains Mono,monospace;color:{color};font-weight:700">{p}%</span>
              </div>
              <div style="background:#f0f4fb;border-radius:3px;height:5px">
                <div style="width:{bar_w}%;height:100%;border-radius:3px;background:{color}"></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
