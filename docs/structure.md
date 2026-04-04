## 2. Arborescence du projet

```
SeniAura-main/
├── app_v2.py                          # Point d'entrée principal (layout + callbacks globaux)
├── requirements.txt                   # Dépendances Python
├── mkdocs.yml                         # Configuration de la documentation
├── docs/                              # Dossier source de la documentation MkDocs
│
├── src/
│   ├── __init__.py                    # Package Python
│   ├── data.py                        # Chargement et fusion des données
│   └── pages/
│       ├── __init__.py
│       ├── home.py                    # Page d'accueil (texte introductif)
│       ├── exploration.py             # Page d'exploration (carte + radar + analyses)
│       ├── methodology.py             # Page méthodologie (tables de variables)
│       ├── radar.py                   # (Legacy) Module radar standalone
│       ├── map.py                     # (Legacy) Module carte standalone
│       └── clustering.py              # (Legacy) Clustering exploratoire
│
├── assets/
│   ├── Senio.png                      # Logo Senio (header)
│   ├── style.css                      # Feuille de style globale
│   └── scroll.js                      # Clientside callback JS (scroll smooth)
│
├── data/
│   ├── FINAL-DATASET-epci-11.xlsx     # Dataset principal (variables par EPCI)
│   ├── dictionnaire_variables.csv     # Métadonnées des variables (nom, catégorie, unité, source...)
│   └── epci-ara.geojson               # Contours géographiques des EPCI ARA
│
├── texte introductif du dashboard.txt # Contenu textuel de la page d'accueil
├── Aide.txt                           # Contenu du panneau d'aide latéral
└── DOCUMENTATION.md                   # Documentation monolithique (source)
```

### Fichiers legacy (non utilisés par `app_v2.py`)

- `app.py` : Ancienne version du point d'entrée.
- `src/pages/map.py`, `radar.py`, `clustering.py` : Modules originaux, remplacés par `exploration.py` qui intègre carte + radar dans une vue unifiée.
