# 🩺 SeniAura — Diagnostic Territorial (Auvergne-Rhône-Alpes)

<div align="center">
  <img src="assets/Senio.png" alt="SeniAura Preview" width="100%">
  <br/><br/>
  <i>Un tableau de bord interactif puissant pour explorer les déterminants sociaux, environnementaux et géographiques des <b>maladies cardio-neuro-vasculaires (CNV)</b> en Auvergne-Rhône-Alpes (Échelle EPCI).</i>
</div>

---

## 🎯 Vision du Projet

SeniAura répond au besoin des décideurs publics de disposer d'un outil de **diagnostic flash** pour comprendre la vulnérabilité de leurs territoires. Plutôt qu'une approche de prévention "descendante" et uniforme, SeniAura propose des **leviers d'actions ultra-ciblés** basés sur les spécificités locales (déserts médicaux, pollution, précarité énergétique).

## ✨ Fonctionnalités Principales

- 🗺️ **Cartographie Interactive** : Visualisation choroplèthe ultra-réactive des indicateurs de santé (Incidence, Mortalité, Prévalence).
- 〽️ **Analyse Multidimensionnelle** : Croisement des données socio-économiques, environnementales et d'offre de soins.
- 🎯 **Radar Comparatif IA-Ready** : Intégration de la directionnalité des variables (Sens + / -) pour une interprétation automatisée du territoire face à la norme régionale.
- 💡 **Recommandation de Leviers** : Suggestion dynamique des politiques (Urbanisme, Prévention, Déploiement CPTS) les plus urgentes pour corriger les faiblesses révélées.

## 🛠️ Stack Technique

SeniAura repose sur une architecture moderne de Data Visualisation :
- **Framework** : `Dash (Flask + React)`
- **Design System** : `Dash Mantine Components v7` (Mantine UI)
- **Data Engineering** : `Pandas`, `GeoPandas`, `Plotly`, `Shapely`
- **Déploiement** : Prêt pour `Gunicorn` / `Render`

## 🚀 Démarrage Rapide

### 1. Prérequis
Assurez-vous de disposer de Python 3.9 ou supérieur.

### 2. Installation
Clonez ce dépôt, puis installez les dépendances requises :
```bash
pip install -r requirements.txt
```

### 3. Exécution
Lancez le serveur backend de l'application :
```bash
python app_v2.py
```
📍 L'application sera disponible sur votre navigateur à l'adresse : **[http://127.0.0.1:8050/](http://127.0.0.1:8050/)**

---

## 📖 Architectures & Documentation
Pour les aspects plus techniques concernant le nettoyage des données, le registre spatial (EPSG:4326, EPCI) et les logiques de machine learning/fairness intégrées, veuillez consulter :

👉 **[Voir la DOCUMENTATION.md détaillée](DOCUMENTATION.md)**

---

## 👥 L'Équipe
Ce projet a été réalisé dans le cadre du Challenge **Open Data University (Latitudes x HEC Paris)** en collaboration avec la Fondation Roche et le comité de l'Inspection Générale des Affaires Sociales (IGAS).

- **Violette Marin**
- **Lia Biscafé-Park**
- **Zehlia Ndiaye**
- **Cléo Gollin**
- **Raphaël Contri**

---
<div align="center">
  <i>Conçu avec expertise par les étudiants du CPES “Sciences des données, société et santé” - Paris-Saclay & HEC Paris.</i>
</div>
