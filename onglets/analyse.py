import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils import load_data, compute_km, GLOBAL_CSS

def analyse_descriptive():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    df = load_data()
    if df.empty: st.error("Aucune donnée."); return

    st.markdown("""
    <div style="margin-bottom:1.2rem">
      <h2 style="font-size:1.5rem;font-weight:700;color:#0d1b3e;margin:0 0 .2rem 0">
        🔬 Analyse Exploratoire des Données
      </h2>
      <p style="color:#6b7a9d;font-size:13px;margin:0">
        Statistiques descriptives — Cohorte {n} patients · Cancer gastrique
      </p>
    </div>""".format(n=len(df)), unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble","🔗 Corrélations","🎯 Analyse bivariée"])

    with tab1:
        n = len(df); nvars = df.shape[1]
        miss = df.isna().sum().sum(); miss_pct = df.isna().mean().mean()*100

        c1,c2,c3,c4 = st.columns(4)
        for col,val,lbl,color in [(c1,n,"Patients",("#1a4fc4")),
            (c2,nvars,"Variables","#a29bfe"),
            (c3,f"{miss} ({miss_pct:.1f}%)","Données manquantes","#ffa502"),
            (c4,f"{int(df['Tempsdesuivi'].median())}m","Survie médiane","#2ed573")]:
            col.markdown(f"""
            <div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.1rem;border:1px solid #e2eaf8;
                        box-shadow:0 2px 10px rgba(26,79,196,.05);border-top:3px solid {color};text-align:center">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:600;color:#0d1b3e">{val}</div>
              <div style="font-size:11px;color:#6b7a9d;text-transform:uppercase;letter-spacing:.07em">{lbl}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_s, col_v = st.columns([1,2])

        with col_s:
            st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem;border:1px solid #e2eaf8">
              <div style="font-size:13px;font-weight:700;color:#0d1b3e;margin-bottom:10px">📋 Statistiques — Âge</div>""",
                unsafe_allow_html=True)
            stats = df["AGE"].describe()
            for k,v in {"Moyenne":stats["mean"],"Médiane":df["AGE"].median(),"Écart-type":stats["std"],
                "Min":stats["min"],"Max":stats["max"],"Q1":stats["25%"],"Q3":stats["75%"]}.items():
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f0f4fb;font-size:13px">
                  <span style="color:#6b7a9d">{k}</span>
                  <span style="font-family:JetBrains Mono,monospace;font-weight:600;color:#0d1b3e">{v:.1f}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_v:
            st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem;border:1px solid #e2eaf8">
              <div style="font-size:13px;font-weight:700;color:#0d1b3e;margin-bottom:10px">📊 Distribution des variables cliniques</div>""",
                unsafe_allow_html=True)
            selected_var = st.selectbox("Sélectionner une variable", df.columns.tolist(), key="ana_var")
            if pd.api.types.is_numeric_dtype(df[selected_var]):
                fig = px.histogram(df, x=selected_var, nbins=30, color_discrete_sequence=["#1a4fc4"])
                fig.update_layout(height=220, margin=dict(l=0,r=0,t=10,b=0),
                    paper_bgcolor="white", plot_bgcolor="white",
                    xaxis=dict(gridcolor="#f0f4fb"), yaxis=dict(gridcolor="#f0f4fb"),
                    font=dict(family="Sora, sans-serif"), showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            else:
                cnt = df[selected_var].value_counts().reset_index()
                cnt.columns = [selected_var,"n"]
                fig = px.bar(cnt, x=selected_var, y="n",
                    color=selected_var, color_discrete_map={"OUI":"#1a4fc4","NON":"#e2eaf8"})
                fig.update_layout(height=220, margin=dict(l=0,r=0,t=10,b=0),
                    paper_bgcolor="white", plot_bgcolor="white",
                    xaxis=dict(gridcolor="#f0f4fb"), yaxis=dict(gridcolor="#f0f4fb"),
                    font=dict(family="Sora, sans-serif"), showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)

        # Data preview
        with st.expander("📄 Aperçu des données brutes", expanded=False):
            st.dataframe(df.head(30), use_container_width=True, hide_index=True, height=300)

    with tab2:
        st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem;border:1px solid #e2eaf8">
          <div style="font-size:13px;font-weight:700;color:#0d1b3e;margin-bottom:8px">🔗 Matrice de corrélation</div>
          <div style="font-size:12px;color:#6b7a9d;margin-bottom:12px">Variables binaires encodées (OUI=1, NON=0)</div>""",
            unsafe_allow_html=True)

        df_enc = df.copy()
        for c in df_enc.columns:
            if df_enc[c].dtype == object:
                df_enc[c] = (df_enc[c].str.upper() == "OUI").astype(int)
        corr = df_enc.corr()

        fig_c = go.Figure(go.Heatmap(
            z=corr.values, x=list(corr.columns), y=list(corr.index),
            colorscale=[[0,"#fff0f2"],[0.5,"white"],[1,"#1a4fc4"]],
            zmin=-1, zmax=1,
            text=np.round(corr.values,2),
            texttemplate="%{text}", textfont=dict(size=10),
            hoverongaps=False,
        ))
        fig_c.update_layout(height=480, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="white",
            xaxis=dict(tickfont=dict(size=10)),
            yaxis=dict(tickfont=dict(size=10)),
            font=dict(family="Sora, sans-serif"))
        st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar":False})
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        col_a, col_b = st.columns(2, gap="large")

        with col_a:
            st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem;border:1px solid #e2eaf8">
              <div style="font-size:13px;font-weight:700;color:#0d1b3e;margin-bottom:12px">
                📈 Survie selon un facteur binaire</div>""", unsafe_allow_html=True)
            bin_cols = [c for c in df.columns if c not in ("AGE","Tempsdesuivi","Deces")]
            selected_f = st.selectbox("Facteur à analyser", bin_cols, key="biv_f")
            d_oui = df[df[selected_f]=="OUI"]; d_non = df[df[selected_f]=="NON"]
            fig_biv = go.Figure()
            for d, name, color in [(d_oui,"OUI","#1a4fc4"),(d_non,"NON","#2ed573")]:
                if len(d) == 0: continue
                t,s = compute_km(d["Tempsdesuivi"],d["Deces"])
                fig_biv.add_trace(go.Scatter(x=t,y=s*100,mode="lines",name=f"{selected_f}={name}",
                    line=dict(color=color,width=2.5)))
            fig_biv.add_hline(y=50,line_dash="dot",line_color="#ccc",line_width=1)
            fig_biv.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor="white", plot_bgcolor="white",
                xaxis=dict(title="Mois",gridcolor="#f0f4fb"),
                yaxis=dict(title="% Survie",range=[0,105],gridcolor="#f0f4fb"),
                legend=dict(orientation="h",y=-0.2,font=dict(size=11)),
                font=dict(family="Sora, sans-serif"))
            st.plotly_chart(fig_biv, use_container_width=True, config={"displayModeBar":False})
            # Median comparison
            m_oui = int(d_oui["Tempsdesuivi"].median()) if len(d_oui)>0 else "-"
            m_non = int(d_non["Tempsdesuivi"].median()) if len(d_non)>0 else "-"
            st.markdown(f"""
            <div style="display:flex;gap:12px;margin-top:8px">
              <div style="flex:1;background:#eef4ff;border-radius:10px;padding:10px;text-align:center">
                <div style="font-size:10px;color:#6b7a9d;text-transform:uppercase">{selected_f} OUI · n={len(d_oui)}</div>
                <div style="font-family:JetBrains Mono,monospace;font-size:1.4rem;font-weight:600;color:#1a4fc4">{m_oui}m</div>
              </div>
              <div style="flex:1;background:#f0fff5;border-radius:10px;padding:10px;text-align:center">
                <div style="font-size:10px;color:#6b7a9d;text-transform:uppercase">{selected_f} NON · n={len(d_non)}</div>
                <div style="font-family:JetBrains Mono,monospace;font-size:1.4rem;font-weight:600;color:#2ed573">{m_non}m</div>
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_b:
            st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem;border:1px solid #e2eaf8">
              <div style="font-size:13px;font-weight:700;color:#0d1b3e;margin-bottom:12px">
                📦 Boxplot — Âge & Temps de suivi</div>""", unsafe_allow_html=True)
            fig_box = go.Figure()
            for val, color, name in [("OUI","#ff4757","Décédés"),("NON","#2ed573","Vivants")]:
                sub = df[df["Deces"]==val]
                fig_box.add_trace(go.Box(y=sub["Tempsdesuivi"],name=name,
                    marker_color=color, boxmean=True,
                    hovertemplate="Suivi: %{y}m<extra></extra>"))
            fig_box.update_layout(height=240, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor="white", plot_bgcolor="white",
                yaxis=dict(title="Mois de suivi",gridcolor="#f0f4fb"),
                font=dict(family="Sora, sans-serif"), showlegend=True)
            st.plotly_chart(fig_box, use_container_width=True, config={"displayModeBar":False})

            # Missing data
            miss = df.isna().sum()
            miss = miss[miss>0]
            if len(miss)>0:
                fig_miss = px.bar(x=miss.index,y=miss.values,color=miss.values,
                    color_continuous_scale="Blues")
                fig_miss.update_layout(height=160, margin=dict(l=0,r=0,t=10,b=0),
                    paper_bgcolor="white",plot_bgcolor="white",showlegend=False,
                    coloraxis_showscale=False, font=dict(family="Sora, sans-serif"))
                st.plotly_chart(fig_miss, use_container_width=True, config={"displayModeBar":False})
            else:
                st.markdown("""<div style="background:#f0fff5;border:1px solid #b7f5ca;border-radius:10px;
                    padding:12px;text-align:center;font-size:13px;color:#1e7e44;margin-top:8px">
                    ✅ Aucune valeur manquante détectée</div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
