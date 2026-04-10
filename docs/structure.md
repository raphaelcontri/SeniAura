# 🗂️ Arborescence du Projet

## Structure complète

```
CardiAura-main/
│
├── app_v2.py                          # 🚀 Point d'entrée principal
├── requirements.txt                   # 📦 Dépendances Python
├── mkdocs.yml                         # 📖 Configuration de la documentation
│
├── src/                               # 📦 Package Python de l'application
│   ├── __init__.py
│   ├── data.py                        # 🗃️ Chargement, fusion et enrichissement des données
│   └── pages/
│       ├── __init__.py
│       ├── home.py                    # 🏠 Page d'accueil
│       ├── exploration.py             # 🗺️ Page d'exploration (carte + radar) ← Cœur
│       ├── methodology.py             # 📚 Page méthodologie
│       ├── radar.py                   # ⚠️ (Legacy) Radar standalone
│       ├── map.py                     # ⚠️ (Legacy) Carte standalone
│       └── clustering.py             # ⚠️ (Legacy) Clustering
│
├── assets/
│   ├── Senio.png                      # 🖼️ Logo header (75px)
│   ├── style.css                      # 🎨 Feuille de style globale (~750 lignes)
│   └── scroll.js                      # ⚡ Clientside callback (scroll smooth)
│
├── data/
│   ├── FINAL-DATASET-epci-11.xlsx     # 📊 Dataset principal (variables par EPCI)
│   ├── dictionnaire_variables.csv     # 📋 Métadonnées des variables
│   └── epci-ara.geojson               # 🗺️ Géométries EPCI de la région ARA
│
├── docs/                              # 📖 Sources MkDocs (ce site)
│
└── site/                              # 🌐 Site statique généré (gitignored)
```

---

## Description des fichiers critiques

### `app_v2.py` — Point d'entrée

Fichier principal (~590 lignes) qui instancie l'application Dash, définit le layout global via un `AppShell` Mantine, et enregistre les callbacks de navigation inter-pages.

!!! warning "Version active"
    Seul `app_v2.py` est utilisé en production. Le fichier `app.py` est l'ancienne version et peut être ignoré.

### `src/data.py` — Pipeline de données

Module chargé une seule fois au démarrage (~200 lignes). Tous les autres modules l'importent via :
```python
from ..data import load_data
gdf_merged, variable_dict, category_dict, ... = load_data()
```

### `data/dictionnaire_variables.csv` — Metadonnées

Fichier CSV pivot contrôlant **ce qui apparaît dans l'UI**. Toute nouvelle variable doit être déclarée ici. Colonnes attendues :

| Colonne | Rôle |
|:---|:---|
| `Variable` | Code exact de la colonne dans l'Excel |
| `Nom_Court` | Label court affiché dans les dropdowns |
| `Description` | Description longue affichée dans les tooltips et la méthodologie |
| `Catégorie` | `Socioéco`, `Offre de soins`, `Environnement`, `Santé` |
| `Sens` | `1` (positif) ou `-1` (négatif) — contrôle la couleur du radar |
| `Unité` | `%`, `‰`, `€`, `nb`, etc. |
| `Sources` | Institution source (INSEE, DREES, ARS, etc.) |
| `Classement` | Contrôle la visibilité dans la sidebar (voir [section dédiée](data.md#logique-de-classement)) |

---

## Fichiers legacy

Les fichiers suivants sont conservés à titre historique mais **ne sont pas utilisés** par `app_v2.py` :

| Fichier | Raison de l'archivage |
|:---|:---|
| `app.py` | Première version du point d'entrée |
| `src/pages/radar.py` | Module radar intégré dans `exploration.py` |
| `src/pages/map.py` | Module carte intégré dans `exploration.py` |
| `src/pages/clustering.py` | Exploration de clustering ML, non intégrée à l'UI |
