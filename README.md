# 🩺 CardiAURA — Diagnostic Territorial (ARA)

> Un tableau de bord interactif pour explorer les déterminants des maladies cardio-neuro-vasculaires en Auvergne-Rhône-Alpes (Échelle EPCI).

![CardiAURA Preview](assets/Senio.png)

---

## 🚀 Démarrage Rapide

### 1. Installation
Assurez-vous d'avoir Python 3.9+ installé. Clonez le dépôt et installez les dépendances :

```bash
pip install -r requirements.txt
```

### 2. Lancement
Lancez l'application via le point d'entrée principal :

```bash
python app_v2.py
```
Ensuite, ouvrez votre navigateur à l'adresse : `http://127.0.0.1:8050/`

---

## 📖 Documentation Complète

Pour tout savoir sur l'architecture du code, les données utilisées et la gestion des callbacks, consultez notre guide technique détaillé :

👉 **[Consultez la DOCUMENTATION.md](DOCUMENTATION.md)**

---

## ✨ Fonctionnalités Clés

- **Cartographie Interactive** : Visualisation choroplèthe des indicateurs de santé (Incidence, Mortalité, Prévalence).
- **Filtrage Dynamique** : Filtres socio-économiques, environnementaux et d'offre de soins via sliders.
- **Radar Comparatif** : Comparez plusieurs territoires (EPCI) par rapport à la moyenne régionale.
- **Analyse Automatisée** : Interprétations narratives et positionnement en quantiles régionaux.
- **SEO Ready** : Support `robots.txt` et méta-données optimisés pour l'indexation.

---

## 🛠️ Stack Technique

- **Backend/Frontend** : Dash (Flask + React)
- **UI Components** : Dash Mantine Components (v7)
- **Data** : Pandas, GeoPandas, Plotly
- **Hébergement** : Optimisé pour Render (Gunicorn)

---

## 👥 Équipe
Projet **HEC Capstone / SeniAura** — 2026.
