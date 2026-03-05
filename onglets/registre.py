import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import load_data, save_new_patient, FEATURE_CONFIG, GLOBAL_CSS
from datetime import date
import io

# ─────────────────────────────────────────────────────────────────────────────

def registre():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    df = load_data()

    st.markdown("""
    <div style="margin-bottom:1.2rem">
      <h2 style="font-size:1.5rem;font-weight:700;color:#0d1b3e;margin:0 0 .2rem 0">
        👥 Registre des Patients — Cancer Gastrique
      </h2>
      <p style="color:#6b7a9d;font-size:13px;margin:0">
        Base de données clinique complète — Cancérologie & Chirurgie Générale
      </p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Liste des patients", "➕ Nouveau patient", "📥 Import / Export"])

    # ── TAB 1: Patient list ───────────────────────────────────────────────────
    with tab1:
        if df.empty:
            st.error("Aucune donnée disponible."); return

        # Filters
        col_f1, col_f2, col_f3, col_f4 = st.columns([2,2,2,1])
        with col_f1:
            deces_f = st.selectbox("Statut", ["Tous","Décédés (OUI)","Vivants (NON)"], key="reg_d")
        with col_f2:
            meta_f  = st.selectbox("Métastases", ["Tous","Avec métastases","Sans métastases"], key="reg_m")
        with col_f3:
            age_r   = st.slider("Tranche d'âge", int(df["AGE"].min()), int(df["AGE"].max()),
                                (int(df["AGE"].min()), int(df["AGE"].max())), key="reg_age")
        with col_f4:
            search  = st.text_input("🔍", placeholder="Rechercher...", key="reg_s")

        dff = df.copy()
        if deces_f == "Décédés (OUI)":     dff = dff[dff["Deces"]=="OUI"]
        elif deces_f == "Vivants (NON)":   dff = dff[dff["Deces"]=="NON"]
        if meta_f == "Avec métastases":    dff = dff[dff["Metastases"]=="OUI"]
        elif meta_f == "Sans métastases":  dff = dff[dff["Metastases"]=="NON"]
        dff = dff[(dff["AGE"]>=age_r[0]) & (dff["AGE"]<=age_r[1])]

        # Summary strip
        n=len(dff); n_dec=(dff["Deces"]=="OUI").sum(); n_viv=n-n_dec
        surv_m = int(dff["Tempsdesuivi"].median()) if n>0 else 0
        st.markdown(f"""
        <div style="display:flex;gap:1.5rem;background:#f8faff;border-radius:12px;padding:.8rem 1.2rem;
                    margin:.8rem 0;border:1px solid #e2eaf8;flex-wrap:wrap">
          <div><span style="font-family:JetBrains Mono,monospace;font-size:1.2rem;font-weight:600;color:#1a4fc4">{n}</span>
          <span style="font-size:12px;color:#6b7a9d;margin-left:4px">patients affichés</span></div>
          <div><span style="font-family:JetBrains Mono,monospace;font-size:1.2rem;font-weight:600;color:#ff4757">{n_dec}</span>
          <span style="font-size:12px;color:#6b7a9d;margin-left:4px">décédés</span></div>
          <div><span style="font-family:JetBrains Mono,monospace;font-size:1.2rem;font-weight:600;color:#2ed573">{n_viv}</span>
          <span style="font-size:12px;color:#6b7a9d;margin-left:4px">vivants</span></div>
          <div><span style="font-family:JetBrains Mono,monospace;font-size:1.2rem;font-weight:600;color:#ffa502">{surv_m}m</span>
          <span style="font-size:12px;color:#6b7a9d;margin-left:4px">survie médiane</span></div>
        </div>""", unsafe_allow_html=True)

        # Rename columns for display
        col_map = {
            "AGE":"Âge","Cardiopathie":"Cardiopathie","Ulceregastrique":"Ulcère gastrique",
            "Douleurepigastrique":"Douleur épigast.","Ulcero-bourgeonnant":"Ulcéro-bourgeon.",
            "Denitrution":"Dénutrition","Tabac":"Tabac","Mucineux":"Mucineux",
            "Infiltrant":"Infiltrant","Stenosant":"Sténosant","Metastases":"Métastases",
            "Adenopathie":"Adénopathie","Deces":"Décès","Tempsdesuivi":"Suivi (mois)"
        }
        dff_disp = dff.rename(columns=col_map)

        st.dataframe(
            dff_disp,
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config={
                "Décès": st.column_config.TextColumn("Décès", width="small"),
                "Âge": st.column_config.NumberColumn("Âge", format="%d ans"),
                "Suivi (mois)": st.column_config.ProgressColumn("Suivi (mois)", min_value=0, max_value=60, format="%d m"),
                "Métastases": st.column_config.TextColumn("Métastases", width="small"),
                "Tabac": st.column_config.TextColumn("Tabac", width="small"),
            }
        )

        # Export
        st.markdown("<br>", unsafe_allow_html=True)
        col_dl1, col_dl2, _ = st.columns([1,1,3])
        with col_dl1:
            csv = dff.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Export CSV", csv, "patients_registre.csv", "text/csv", use_container_width=True)
        with col_dl2:
            buf = io.BytesIO()
            dff.to_excel(buf, index=False)
            st.download_button("⬇️ Export Excel", buf.getvalue(),
                "patients_registre.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)

    # ── TAB 2: New patient ────────────────────────────────────────────────────
    with tab2:
        st.markdown("""<div style="background:#fff8e1;border-left:4px solid #ffa502;border-radius:0 10px 10px 0;
            padding:10px 14px;font-size:13px;color:#7d5a00;margin-bottom:1.2rem">
            🔒 <strong>Confidentialité</strong> — Toutes les données sont soumises au secret médical.
            Vérifiez l'identité du patient avant la saisie.</div>""", unsafe_allow_html=True)

        col_form, col_info = st.columns([2,1], gap="large")

        with col_form:
            with st.form("new_patient_form", clear_on_submit=True):
                st.markdown("""<div style="font-size:13px;font-weight:700;color:#0d1b3e;
                    text-transform:uppercase;letter-spacing:.06em;margin-bottom:1rem">
                    IDENTIFICATION DU PATIENT</div>""", unsafe_allow_html=True)

                c1,c2 = st.columns(2)
                with c1: pat_id  = st.text_input("N° Dossier *", placeholder="CANC-2024-0001")
                with c2: dept_p  = st.selectbox("Département *",["Cancérologie","Chirurgie Générale"])
                c3,c4 = st.columns(2)
                with c3: age_p   = st.number_input("Âge *", 18, 100, 55)
                with c4: sexe_p  = st.selectbox("Sexe", ["Masculin","Féminin"])
                c5,c6 = st.columns(2)
                with c5: date_p  = st.date_input("Date d'admission", value=date.today())
                with c6: medecin = st.text_input("Médecin référent", placeholder="Dr. ...")

                st.markdown("""<div style="font-size:11px;font-weight:700;color:#1a4fc4;
                    text-transform:uppercase;letter-spacing:.1em;margin:12px 0 8px 0">
                    ANTÉCÉDENTS & COMORBIDITÉS</div>""", unsafe_allow_html=True)
                c1,c2,c3 = st.columns(3)
                with c1: card_p  = st.selectbox("Cardiopathie",["NON","OUI"],key="np_c")
                with c2: ulc_p   = st.selectbox("Ulcère gastrique",["NON","OUI"],key="np_u")
                with c3: doul_p  = st.selectbox("Douleur épigastrique",["OUI","NON"],key="np_d")
                c4,c5 = st.columns(2)
                with c4: tab_p   = st.selectbox("Tabagisme",["NON","OUI"],key="np_t")
                with c5: den_p   = st.selectbox("Dénutrition",["NON","OUI"],key="np_dn")

                st.markdown("""<div style="font-size:11px;font-weight:700;color:#1a4fc4;
                    text-transform:uppercase;letter-spacing:.1em;margin:12px 0 8px 0">
                    CARACTÉRISTIQUES TUMORALES</div>""", unsafe_allow_html=True)
                c1,c2,c3 = st.columns(3)
                with c1: muc_p   = st.selectbox("Type mucineux",["OUI","NON"],key="np_m")
                with c2: inf_p   = st.selectbox("Type infiltrant",["NON","OUI"],key="np_i")
                with c3: sten_p  = st.selectbox("Type sténosant",["NON","OUI"],key="np_s")
                c4,c5,c6 = st.columns(3)
                with c4: ulcb_p  = st.selectbox("Lés. ulcéro-bourg.",["NON","OUI"],key="np_ub")
                with c5: meta_p  = st.selectbox("Métastases",["NON","OUI"],key="np_mt")
                with c6: aden_p  = st.selectbox("Adénopathie",["NON","OUI"],key="np_a")

                st.markdown("""<div style="font-size:11px;font-weight:700;color:#1a4fc4;
                    text-transform:uppercase;letter-spacing:.1em;margin:12px 0 8px 0">
                    SUIVI</div>""", unsafe_allow_html=True)
                c1,c2 = st.columns(2)
                with c1: suivi_p = st.number_input("Temps de suivi (mois)", 0, 120, 0)
                with c2: deces_p = st.selectbox("Statut décès",["NON — En vie","OUI — Décédé"])

                notes_p = st.text_area("Notes cliniques", placeholder="Observations, traitement en cours, RCP...", height=80)

                submitted = st.form_submit_button("💾 Enregistrer le patient", use_container_width=True)

            if submitted:
                if not pat_id:
                    st.error("⚠️ Le N° de dossier est obligatoire.")
                else:
                    new_rec = {
                        "AGE": int(age_p),
                        "Cardiopathie": card_p, "Ulceregastrique": ulc_p,
                        "Douleurepigastrique": doul_p, "Ulcero-bourgeonnant": ulcb_p,
                        "Denitrution": den_p, "Tabac": tab_p, "Mucineux": muc_p,
                        "Infiltrant": inf_p, "Stenosant": sten_p,
                        "Metastases": meta_p, "Adenopathie": aden_p,
                        "Deces": "OUI" if "OUI" in deces_p else "NON",
                        "Tempsdesuivi": int(suivi_p),
                    }
                    if save_new_patient(new_rec):
                        st.success(f"✅ Patient **{pat_id}** enregistré avec succès dans la base de données !")
                        st.balloons()

        with col_info:
            st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.2rem;
                border:1px solid #e2eaf8;box-shadow:0 2px 10px rgba(26,79,196,.05)">
              <div style="font-size:13px;font-weight:700;color:#0d1b3e;margin-bottom:12px">
                📋 Checklist dossier</div>""", unsafe_allow_html=True)
            checks = [
                ("✅", "Identité patient complète"),
                ("✅", "Antécédents médicaux"),
                ("✅", "Caractéristiques tumorales"),
                ("⬜", "Résultats anapath. joints"),
                ("⬜", "Bilan d'extension (TDM)"),
                ("⬜", "Consentement éclairé signé"),
                ("⬜", "Prédiction IA calculée"),
                ("⬜", "Avis RCP obtenu"),
            ]
            for icon, txt in checks:
                c = "#1e7e44" if icon=="✅" else "#6b7a9d"
                st.markdown(f"<div style='font-size:12px;color:{c};padding:4px 0;border-bottom:1px solid #f0f4fb'>{icon} {txt}</div>",
                    unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Stats recap
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#f8faff,#eef4ff);border-radius:14px;
                padding:1.2rem;border:1px solid #d1e0ff;margin-top:12px">
              <div style="font-size:12px;font-weight:700;color:#1a4fc4;text-transform:uppercase;
                   letter-spacing:.07em;margin-bottom:8px">BASE DE DONNÉES</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.8rem;font-weight:600;color:#0d1b3e">{len(df)}</div>
              <div style="font-size:12px;color:#6b7a9d">patients enregistrés</div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 3: Import / Export ────────────────────────────────────────────────
    with tab3:
        col_imp, col_exp = st.columns(2, gap="large")

        with col_imp:
            st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.4rem;border:1px solid #e2eaf8">
              <div style="font-size:14px;font-weight:700;color:#0d1b3e;margin-bottom:12px">
                📥 Import de données</div>""", unsafe_allow_html=True)
            uploaded = st.file_uploader("Fichier Excel/CSV patients",
                type=["xlsx","csv"], label_visibility="collapsed")
            if uploaded:
                try:
                    if uploaded.name.endswith(".csv"):
                        df_new = pd.read_csv(uploaded)
                    else:
                        df_new = pd.read_excel(uploaded)
                    st.success(f"✅ {len(df_new)} lignes détectées")
                    st.dataframe(df_new.head(5), use_container_width=True, hide_index=True)
                    if st.button("✅ Confirmer l'import"):
                        df_merged = pd.concat([df, df_new], ignore_index=True)
                        df_merged.to_excel("data/data.xlsx", index=False)
                        st.success(f"Données importées. Total : {len(df_merged)} patients.")
                except Exception as e:
                    st.error(f"Erreur : {e}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_exp:
            st.markdown("""<div style="background:rgba(255,255,255,0.88);backdrop-filter:blur(8px);border-radius:14px;padding:1.4rem;border:1px solid #e2eaf8">
              <div style="font-size:14px;font-weight:700;color:#0d1b3e;margin-bottom:12px">
                📤 Export de données</div>""", unsafe_allow_html=True)
            st.markdown(f"**{len(df)} patients** dans la base de données courante.")
            c1,c2 = st.columns(2)
            with c1:
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ CSV complet", csv, "export_complet.csv","text/csv",use_container_width=True)
            with c2:
                buf = io.BytesIO(); df.to_excel(buf,index=False)
                st.download_button("⬇️ Excel complet", buf.getvalue(),
                    "export_complet.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)

            st.markdown("<br>**Statistiques de la base :**", unsafe_allow_html=True)
            st.dataframe(df.describe().round(2), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
