# ⚕️ SHAHIDI AI Platform v2.0
## Plateforme d'Analyse de Survie — Cancer Gastrique

Plateforme médicale professionnelle de prédiction de survie par intelligence artificielle,
dédiée aux départements de **Cancérologie** et **Chirurgie Générale**.

---

## 🚀 Lancement rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'application
streamlit run main.py
```

L'application sera accessible à : **http://localhost:8501**

---

## 📁 Structure du projet

```
shahidi_platform/
├── main.py                    # Point d'entrée principal
├── utils.py                   # Fonctions utilitaires partagées
├── requirements.txt           # Dépendances Python
├── .streamlit/
│   └── config.toml            # Thème et configuration Streamlit
├── data/
│   └── data.xlsx              # Base de données patients (337 cas)
├── models/
│   ├── deepsurv.keras         # Modèle DeepSurv (C-index: 0.92)
│   ├── coxph.joblib           # Modèle Cox PH (C-index: 0.85)
│   ├── rsf.joblib             # Random Survival Forest (C-index: 0.84)
│   └── gbst.joblib            # Gradient Boosting Survival (C-index: 0.88)
├── onglets/
│   ├── accueil.py             # 🏠 Tableau de bord principal
│   ├── kpi.py                 # 📈 Indicateurs clés de performance
│   ├── prediction.py          # 🧠 Prédiction de survie par IA
│   ├── registre.py            # 👥 Registre patients + enregistrement
│   ├── analyse.py             # 🔬 Analyse exploratoire des données
│   └── apropos.py             # ℹ️ À propos & équipe
└── assets/                    # Images et ressources visuelles
```

---

## 📊 Modules de la plateforme

| Module | Description |
|--------|-------------|
| 🏠 **Tableau de bord** | KPIs temps réel, courbe KM, distribution âge, facteurs de risque |
| 📈 **Indicateurs KPI** | Suivi de performance, comparaison modèles, stratification |
| 🧠 **Prédiction IA** | Formulaire clinique, prédiction temps réel, export PDF |
| 👥 **Registre patients** | Liste complète, filtres, ajout patient, import/export |
| 🔬 **Analyse des données** | Statistiques descriptives, corrélations, analyse bivariée |
| ℹ️ **À Propos** | Équipe, performances des modèles, partenaires |

---

## 🔑 Variables cliniques (12 features)

| Variable | Description |
|----------|-------------|
| AGE | Âge du patient (années) |
| Cardiopathie | Antécédent de cardiopathie |
| Ulceregastrique | Ulcère gastrique préexistant |
| Douleurepigastrique | Présence de douleur épigastrique |
| Ulcero-bourgeonnant | Lésion ulcéro-bourgeonnante |
| Denitrution | État de dénutrition |
| Tabac | Tabagisme actif |
| Mucineux | Type histologique mucineux |
| Infiltrant | Type histologique infiltrant |
| Stenosant | Type histologique sténosant |
| Metastases | Présence de métastases |
| Adenopathie | Présence d'adénopathie |

---

## 🏥 Indicateurs épidémiologiques (cohorte 337 patients)

- **Taux de mortalité** : 66.2% (223/337)
- **Survie médiane** : 21 mois
- **Âge moyen** : 52.1 ans (31-81 ans)
- **Survie à 6 mois** : 78.0%
- **Survie à 12 mois** : 64.0%
- **Survie à 24 mois** : 48.3%

---

## 🤝 Équipe & Contact

- **Pr. Aba Diop** — Maître de Conférences, UAD Bambey
- **PhD. Idrissa Sy** — Enseignant Chercheur, UAD Bambey
- **M. Ahmed Sefdine** — Étudiant Chercheur, UAD Bambey

📧 contact@shahidi-ai.sn | 🌐 Université Alioune Diop de Bambey

---

*Licence académique — Usage clinique supervisé — © 2024 SHAHIDI AI*
