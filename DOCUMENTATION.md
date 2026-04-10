# Documentation Technique — CardiAURA / SeniAura Dashboard

> **Version** : 3.0 — Mars 2026  
> **Framework** : Dash + Dash Mantine Components (dmc v7) + Plotly  
> **Région** : Auvergne-Rhône-Alpes (ARA)  

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Arborescence du projet](#2-arborescence-du-projet)
3. [Données et chargement (`src/data.py`)](#3-données-et-chargement)
4. [Point d'entrée principal (`app_v2.py`)](#4-point-dentrée-principal)
5. [Pages](#5-pages)
   - 5.1 [Accueil (`home.py`)](#51-accueil)
   - 5.2 [Exploration (`exploration.py`)](#52-exploration)
   - 5.3 [Méthodologie (`methodology.py`)](#53-méthodologie)
   - 5.4 [Radar (legacy) (`radar.py`)](#54-radar-legacy)
6. [Assets front-end](#6-assets-front-end)
7. [Flux de données et callbacks](#7-flux-de-données-et-callbacks)
8. [Guide de déploiement](#8-guide-de-déploiement)
9. [FAQ technique](#9-faq-technique)

---

## 1. Vue d'ensemble

CardiAURA (alias SeniAura) est un **tableau de bord interactif** permettant d'explorer les déterminants des maladies cardio-neuro-vasculaires à l'échelle des **EPCI** (Établissements Publics de Coopération Intercommunale) de la région Auvergne-Rhône-Alpes.

### Fonctionnalités principales

| Fonctionnalité | Description |
|---|---|
| **Carte choroplèthe** | Visualisation colorée d'un indicateur de santé (Incidence, Mortalité, Prévalence) par EPCI |
| **Filtrage par variables** | Sliders dynamiques pour filtrer les EPCI selon des critères socio-éco, offre de soins, environnement |
| **Radar comparatif** | Comparaison multi-variables de territoires sélectionnés vs. la moyenne régionale |
| **Analyse textuelle auto-générée** | Interprétations narratives et positionnement en quantiles |
| **Méthodologie** | Tables détaillées des variables avec descriptions, unités et sources |

### Stack technique

```
Python 3.x
├── dash                      # Framework web réactif
├── dash-mantine-components   # Composants UI (v7, style Mantine)
├── dash-iconify              # Icônes (Solar icon set)
├── plotly                    # Graphiques (Choropleth, Scatterpolar, Scattergeo)
├── geopandas                 # Manipulation des données géographiques
├── pandas / numpy            # Manipulation des données tabulaires
├── openpyxl                  # Lecture des fichiers Excel (.xlsx)
└── gunicorn                  # Serveur WSGI pour la production
```

---

## 2. Arborescence du projet

```
SeniAura-main/
├── app_v2.py                          # Point d'entrée principal (layout + callbacks globaux)
├── requirements.txt                   # Dépendances Python
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
└── DOCUMENTATION.md                   # ← Ce fichier
```

### Fichiers legacy (non utilisés par `app_v2.py`)

- `app.py` : Ancienne version du point d'entrée.
- `src/pages/map.py`, `radar.py`, `clustering.py` : Modules originaux, remplacés par `exploration.py` qui intègre carte + radar dans une vue unifiée.

---

## 3. Données et chargement

### Fichier : `src/data.py`

#### Fonction principale : `load_data()`

Cette fonction est appelée **une seule fois** au démarrage de l'application par chaque module qui en a besoin. Elle retourne un tuple de 9 éléments :

```python
gdf_merged, variable_dict, category_dict, sens_dict, description_dict, unit_dict, gdf_deps, source_dict, classement_dict = load_data()
```

| Retour | Type | Description |
|---|---|---|
| `gdf_merged` | `GeoDataFrame` | Données fusionnées (géométrie EPCI + variables du dataset) |
| `variable_dict` | `dict` | `{code_variable: nom_lisible}` |
| `category_dict` | `dict` | `{code_variable: catégorie}` (Socioéco, Offre de soins, Environnement, Santé) |
| `sens_dict` | `dict` | `{code_variable: sens}` (1 = positif, -1 = négatif) |
| `description_dict` | `dict` | `{code_variable: description_longue}` |
| `unit_dict` | `dict` | `{code_variable: unité}` (ex: "%, ‰, €") |
| `gdf_deps` | `GeoDataFrame` | Contours des **départements** (dissolve par département) |
| `source_dict` | `dict` | `{code_variable: source_institutionnelle}` |
| `classement_dict` | `dict` | `{code_variable: classement}` (rang de priorité pour le filtrage) |

#### Pipeline de chargement

```
1. GeoJSON (epci-ara.geojson) → gdf_epci (contours EPCI)
2. Excel (FINAL-DATASET-epci-11.xlsx) → df (variables par EPCI)
3. CSV (dictionnaire_variables.csv) → Métadonnées (dicts)
4. Merge (gdf_epci ⟕ df) sur EPCI_CODE → gdf_merged
5. Dissolve par département → gdf_deps (frontières départementales)
```

#### Logique de filtrage des variables (`classement_dict`)

Le champ `Classement` dans le dictionnaire CSV contrôle la visibilité des variables :

| Classement | Comportement |
|---|---|
| `0`, `1`, `2` | **Exclues partout** (ni sidebar, ni méthodologie) |
| `3` | Exclues du sidebar mais **visibles en méthodologie** (catégorie Santé uniquement) |
| `67` | **Variables prioritaires** (affichées en premier dans les menus déroulants) |
| Autre | Variables standard, triées alphabétiquement |

---

## 4. Point d'entrée principal

### Fichier : `app_v2.py`

Ce fichier (564 lignes) contient :
1. L'initialisation de l'app Dash
2. La construction du **layout global** (AppShell)
3. Les **callbacks de navigation** et de gestion du panneau d'aide

### Architecture du layout (AppShell Mantine)

```
MantineProvider (thème : blue, Inter font)
└── AppShell
    ├── AppShellHeader (h=130px)
    │   ├── Ligne 1 : Logo Senio + Badge Région + Tabs Navigation (Accueil / Exploration / Méthodologie)
    │   └── Ligne 2 : Titre "Diagnostic Territorial..." + Bouton "Afficher l'aide"
    │
    ├── AppShellNavbar (width=350px) — Sidebar gauche
    │   ├── ScrollArea
    │   │   ├── Sélection indicateur santé (Type: INCI/MORT/PREV + Pathologie: AVC/CardIsch/InsuCard)
    │   │   ├── Filtres Socio-Économie (MultiSelect + Sliders dynamiques)
    │   │   ├── Filtres Offre de Soins (MultiSelect + Sliders dynamiques)
    │   │   ├── Filtres Environnement (MultiSelect + Sliders dynamiques)
    │   │   └── Sélection EPCI à comparer (MultiSelect)
    │   └── Footer "Équipe du projet - 2026"
    │
    ├── AppShellMain
    │   └── ScrollArea → Container → #page-content (injection dynamique des pages)
    │
    └── AppShellAside (width=450px) — Panneau d'aide (togglable)
        ├── Titre "Aide & Mode d'emploi" + Bouton fermer
        └── ScrollArea → #aside-content (contenu dynamique)
```

### Callbacks de navigation (dans `app_v2.py`)

| Callback | Trigger | Action |
|---|---|---|
| `unified_navigation` | URL change OU Tab click | Synchronise l'URL, l'onglet actif, et la visibilité de la sidebar (masquée hors Exploration) |
| `display_page` | URL change | Injecte le layout de la page correspondante dans `#page-content` |
| `toggle_guide_button` | URL change | Affiche/masque le bouton "Aide" (visible uniquement sur Exploration) |
| `toggle_aside_store` | Click "Aide" | Toggle l'état ouvert/fermé du panneau latéral |
| `sync_aside_state` | Store change | Applique l'état collapsed/visible au panneau `aside` |
| `close_aside` | Click fermer OU navigation | Ferme le panneau d'aide |

### Gestion dynamique de la sidebar

La sidebar (`AppShellNavbar`) est **automatiquement masquée** sur les pages Accueil et Méthodologie, et **visible** sur la page Exploration. Ce comportement est géré dans `unified_navigation` via :

```python
current_navbar["collapsed"] = {"desktop": not is_explor, "mobile": True}
```

---

## 5. Pages

### 5.1 Accueil

**Fichier** : `src/pages/home.py` (187 lignes)

#### Fonctionnement

1. **Lecture du fichier texte** : Parse `texte introductif du dashboard.txt`. Les sections sont séparées par `\n> `.
2. **Construction d'un Accordion** : Chaque section devient un `AccordionItem` avec une icône contextuelle (objectif → cible, EPCI → map, etc.).
3. **Boutons CTA** :
   - "Démarrer le diagnostic" → Lien vers `/exploration`
   - "Prise en main" → Smooth scroll + ouverture de la section correspondante

#### Callbacks

| Callback | Type | Action |
|---|---|---|
| `open_prise_en_main` | Server-side | Ouvre la section "Prise en main" dans l'accordion |
| `scrollToAccordion` | Client-side (JS) | Scroll smooth vers `#accordion-item-prise-en-main` |

---

### 5.2 Exploration

**Fichier** : `src/pages/exploration.py` (839 lignes) — **le cœur de l'application**

#### Layout

```
Container (fluid)
├── Paper #container-map — Carte interactive
│   ├── Titre dynamique (#map-dynamic-title)
│   ├── dcc.Graph #map-graph (Choropleth + frontières départements + exclusions + villes)
│   └── Zone d'interprétation
│       ├── Paper (bg=#f8f9fa) : Interprétations + Narratif + Descriptions variables
│       └── Paper (caché) : Sélecteur d'exclusion par variable
│
└── Paper #container-radar — Radar comparatif
    ├── Titre dynamique (#radar-dynamic-title)
    ├── Placeholder (affiché quand < 3 variables)
    ├── dcc.Graph #radar-chart (Scatterpolar)
    └── #radar-reading-guide : Interprétations + Quantiles
```

#### Callbacks principaux

##### 1. `update_sliders` — Génération dynamique des sliders

```
Inputs : sidebar-filter-social, sidebar-filter-offre, sidebar-filter-env (MultiSelect values)
States : exploration-slider values et ids (pattern-matching ALL)
Outputs : slider-container-social, slider-container-offre, slider-container-env (children)
```

- Pour chaque variable sélectionnée, crée un `dcc.RangeSlider` avec min/max calculés depuis `gdf_merged`.
- Les sliders affichent des marques Min et Max et des infobulles persistantes.

##### 2. `select_epci_on_click` — Sélection d'EPCI par clic sur la carte

```
Input  : map-graph.clickData
State  : sidebar-epci-radar.value
Output : sidebar-epci-radar.value
```

- Extrait le nom de l'EPCI cliqué, retrouve son code, l'ajoute ou le retire de la sélection (toggle).

##### 3. `update_highlight_options` — Options de mise en évidence

```
Inputs  : sidebar-filter-social, sidebar-filter-offre, sidebar-filter-env
Output  : highlight-variable-select.data
```

- Met à jour la liste déroulante des variables disponibles pour la mise en évidence des exclusions.

##### 4. `update_map` — Rendu de la carte choroplèthe

```
Inputs  : map-indic-select, map-patho-select, exploration-sliders (ALL), sidebar-epci-radar, highlight-variable-select, slider IDs (ALL)
Outputs : map-graph.figure, map-stats-header-content, map-reading-guide, map-narrative-content, map-dynamic-title
```

**Couches de la carte (ordre de rendu)** :

| # | Couche | Description |
|---|---|---|
| 1 | **Fond gris** | Tous les EPCI en gris clair (base) |
| 2 | **Choroplèthe coloré** | EPCI passant tous les filtres, colorés selon l'indicateur santé |
| 3 | **Frontières départementales** | Lignes noires translucides (dissolve du GeoJSON) |
| 4 | **Exclusions spécifiques** | EPCI grisés par une variable précise (si variable de highlight sélectionnée) |
| 5 | **Sélection rouge** | EPCI sélectionnés pour le radar (contour rouge) |
| 6 | **Villes repères** | Points noirs + étiquettes des 13 préfectures/villes majeures |

**Génération narrative** : Après le rendu de la carte, le callback construit dynamiquement :
- Un résumé statistique (nombre d'EPCI inclus/exclus)
- Des phrases narratives décrivant les filtres actifs
- Les descriptions des variables sélectionnées (avec lien vers la méthodologie)

##### 5. `update_radar` — Rendu du radar comparatif

```
Inputs  : sidebar-filter-social, sidebar-filter-offre, sidebar-filter-env, sidebar-epci-radar, map-indic-select, map-patho-select
Outputs : radar-chart.figure, radar-chart.style, radar-placeholder.style, radar-reading-guide.children, radar-dynamic-title.children
```

**Logique de normalisation** : Toutes les variables sont normalisées min-max [0, 1] sur l'ensemble de la région pour permettre une comparaison équitable sur le radar.

**Traces du radar** :

| Trace | Description |
|---|---|
| Zone Moyenne ± σ | Polygone gris clair (moyenne ± 1σ) |
| Moyenne Région | Ligne continue grise, fermée en boucle |
| Territoires (EPCI) | Polygones colorés, un par territoire sélectionné |

**Analyses automatiques** :

1. **Interprétation narrative** : Pour chaque EPCI, chaque variable est qualifiée selon son z-score :
   - `|z| < 0.5` → "proche de la moyenne régionale"
   - `0.5 ≤ z < 1.5` → "légèrement au-dessus/en dessous"
   - `z ≥ 1.5` → "nettement au-dessus/en dessous"

2. **Quantiles régionaux** : Panneau "Positionnement Relatif" avec badges colorés. *(Voir le document MkDocs `docs/pages.md` pour le détail algorithmique "1" vs "-1" affectant les couleurs).*

---

### 5.3 Méthodologie

**Fichier** : `src/pages/methodology.py` (237 lignes)

#### Structure

```
Container
├── Titre + Sous-titre
└── Tabs (pills)
    ├── Socioéco → Table des variables
    ├── Offre de soins → Table des variables
    ├── Environnement → Table des variables
    ├── Santé → Table des variables
    └── Construction et méthodologie → Accordion
        ├── Sources primaires et collecte
        ├── Nettoyage et harmonisation
        └── Standardisation géographique
```

#### Tables de variables

Chaque table affiche 4 colonnes à largeur fixe (`layout="fixed"`) :

| Colonne | Largeur | Contenu |
|---|---|---|
| Variable | 200px | Nom lisible (`Nom_Court` du dictionnaire) |
| Description | 400px | Description longue |
| Unité | 100px | %, ‰, €, nb, etc. |
| Source | 250px | Institution source (Insee, DREES, etc.) |

---

### 5.4 Radar (legacy)

**Fichier** : `src/pages/radar.py` (284 lignes)

> ⚠️ **Ce fichier n'est PAS utilisé** par `app_v2.py`. Le radar est intégré directement dans `exploration.py`. Ce fichier est conservé à titre de référence historique.

---

## 6. Assets front-end

### `assets/style.css`

Feuille de style globale (~600 lignes). Points clés :

| Sélecteur | Rôle |
|---|---|
| `.intro-text` | Typographie de la page d'accueil |
| `.header-nav-tabs .mantine-Tabs-tab` | Style des onglets de navigation |
| `.app-sidebar` | Style de la sidebar |
| `.rc-slider` | Espacement et visibilité des RangeSliders (marques Min/Max) |
| `#accordion-item-prise-en-main` | `scroll-margin-top: 100px` pour le scroll "header-aware" |
| `.mantine-ScrollArea-*` | Masquage des scrollbars redondantes |

### `assets/scroll.js`

Client-side callback pour le scroll smooth vers la section "Prise en main" :

```javascript
window.dash_clientside.clientside = {
    scrollToAccordion: function(n_clicks) {
        if (n_clicks) {
            document.getElementById('accordion-item-prise-en-main')
                .scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        return window.dash_clientside.no_update;
    }
};
```

Le `scroll-margin-top: 100px` en CSS garantit que le contenu s'arrête sous le header fixe.

### `assets/Senio.png`

Logo officiel Senio affiché dans le header (75px de hauteur).

---

## 7. Flux de données et callbacks

### Diagramme de flux global

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            SIDEBAR (app_v2.py)                         │
│                                                                         │
│  ┌─────────────────┐   ┌──────────────────┐   ┌─────────────────────┐  │
│  │ Indicateur Santé │   │ Filtres Variables │   │ Sélection EPCI      │  │
│  │ (INCI/MORT/PREV) │   │ (3 MultiSelects) │   │ (MultiSelect/Clic)  │  │
│  │ + Pathologie     │   │ + RangeSliders   │   │                     │  │
│  └────────┬────────┘   └────────┬─────────┘   └──────────┬──────────┘  │
│           │                     │                         │             │
└───────────┼─────────────────────┼─────────────────────────┼─────────────┘
            │                     │                         │
            ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        exploration.py — Callbacks                       │
│                                                                         │
│  ┌───────────────────────────────────────────────┐                      │
│  │ update_sliders()                               │                      │
│  │ Variables sélectionnées → RangeSliders          │                      │
│  └───────────────────────────────────────────────┘                      │
│                                                                         │
│  ┌───────────────────────────────────────────────┐                      │
│  │ update_map()                                   │                      │
│  │ Indicateur + Sliders + Sélection → Choropleth  │                      │
│  │ + Narrative + Descriptions + Villes            │                      │
│  └───────────────────────────────────────────────┘                      │
│                                                                         │
│  ┌───────────────────────────────────────────────┐                      │
│  │ update_radar()                                 │                      │
│  │ Variables + EPCIs → Radar + Interprétations    │                      │
│  │ + Quantiles régionaux                          │                      │
│  └───────────────────────────────────────────────┘                      │
│                                                                         │
│  ┌───────────────────────────────────────────────┐                      │
│  │ select_epci_on_click()                         │                      │
│  │ Click carte → Ajoute/retire EPCI du MultiSelect│                      │
│  └───────────────────────────────────────────────┘                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tableau récapitulatif des IDs de composants

| ID | Composant | Fichier | Rôle |
|---|---|---|---|
| `url` | `dcc.Location` | app_v2.py | Routage SPA |
| `nav-tabs` | `dmc.Tabs` | app_v2.py | Navigation header |
| `page-content` | `html.Div` | app_v2.py | Injection dynamique des pages |
| `app-shell` | `dmc.AppShell` | app_v2.py | Shell principal |
| `aside-opened-store` | `dcc.Store` | app_v2.py | État ouvert/fermé du panneau aide |
| `exploration-guide-btn` | `dmc.Button` | app_v2.py | Toggle panneau aide |
| `close-aside-btn` | `dmc.ActionIcon` | app_v2.py | Fermer panneau aide |
| `map-indic-select` | `dmc.Select` | app_v2.py | Choix type indicateur (INCI/MORT/PREV) |
| `map-patho-select` | `dmc.Select` | app_v2.py | Choix pathologie |
| `sidebar-filter-social` | `dmc.MultiSelect` | app_v2.py | Filtres socio-éco |
| `sidebar-filter-offre` | `dmc.MultiSelect` | app_v2.py | Filtres offre de soins |
| `sidebar-filter-env` | `dmc.MultiSelect` | app_v2.py | Filtres environnement |
| `sidebar-epci-radar` | `dmc.MultiSelect` | app_v2.py | Sélection EPCI pour radar |
| `map-graph` | `dcc.Graph` | exploration.py | Carte choroplèthe |
| `radar-chart` | `dcc.Graph` | exploration.py | Radar comparatif |
| `radar-placeholder` | `html.Div` | exploration.py | Message quand radar inactif |
| `highlight-variable-select` | `dmc.Select` | exploration.py | Filtrage d'exclusion par variable |
| `home-accordion` | `dmc.Accordion` | home.py | Accordion page accueil |
| `btn-prise-en-main` | `dmc.Button` | home.py | Scroll vers "Prise en main" |
| `methodo-tabs` | `dmc.Tabs` | methodology.py | Onglets méthodologie |
| `{'type': 'exploration-slider', 'index': var}` | `dcc.RangeSlider` | exploration.py | Sliders dynamiques (pattern-matching) |

---

## 8. Guide de déploiement

### Développement local

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer le serveur de développement
python3 app_v2.py

# 3. Ouvrir dans le navigateur
# http://localhost:8050
```

### Production (Gunicorn)

```bash
gunicorn app_v2:server -b 0.0.0.0:8050 --workers 4
```

### Variables d'environnement

Aucune variable d'environnement n'est requise. Tous les chemins sont résolus relativement au fichier `app_v2.py`.

### Structure des données requises

Pour que l'application fonctionne, les fichiers suivants doivent exister :

| Fichier | Chemin relatif | Format |
|---|---|---|
| Dataset EPCI | `data/FINAL-DATASET-epci-11.xlsx` | Excel (.xlsx) avec colonne `CODE_EPCI` |
| Dictionnaire variables | `data/dictionnaire_variables.csv` | CSV avec colonnes : Variable, Description, Catégorie, Sens, Unité, Sources, Classement, Nom_Court |
| GeoJSON EPCI | `data/epci-ara.geojson` | GeoJSON avec propriété `EPCI_CODE` et `DEPARTEMEN` |
| Texte introductif | `texte introductif du dashboard.txt` | Texte brut, sections séparées par `\n> ` |
| Logo | `assets/Senio.png` | Image PNG |

---

## 9. FAQ technique

### Comment ajouter une nouvelle variable ?

1. Ajouter la colonne dans `FINAL-DATASET-epci-11.xlsx` (valeurs numériques par EPCI)
2. Ajouter une ligne dans `dictionnaire_variables.csv` :
   - `Variable` = nom de la colonne Excel
   - `Catégorie` = Socioéco / Offre de soins / Environnement / Santé
   - `Classement` = 67 (prioritaire) ou vide (standard)
   - Remplir Description, Unité, Sources, Sens, Nom_Court
3. Relancer l'application → la variable apparaît automatiquement dans les menus de filtrage et la méthodologie.

### Comment ajouter une ville sur la carte ?

Modifier la liste `cities` dans la fonction `update_map()` de `exploration.py` (~ligne 435) :

```python
cities = [
    {"name": "Lyon", "lat": 45.7640, "lon": 4.8357},
    {"name": "Nouvelle Ville", "lat": XX.XXXX, "lon": Y.YYYY},  # ← Ajouter ici
    ...
]
```

### Pourquoi le radar nécessite-t-il 3+ variables ?

Le radar (`Scatterpolar`) nécessite au minimum 3 axes pour former un polygone lisible. Avec 2 axes ou moins, le graphique dégénère en ligne ou point.

### Comment modifier le texte de la page d'accueil ?

Éditer le fichier `texte introductif du dashboard.txt`. Les sections sont délimitées par `\n> ` suivi du titre de section. Le parsing est automatique dans `home.py`.

### Comment fonctionne le filtrage des EPCI ?

1. L'utilisateur sélectionne des variables dans la sidebar
2. Des `RangeSliders` sont générés dynamiquement pour chaque variable
3. Lors du rendu de la carte, un masque booléen est calculé :
   - Pour chaque variable/slider, on vérifie si la valeur de l'EPCI est dans la plage `[min_slider, max_slider]`
   - Un EPCI est **inclus** (coloré) s'il satisfait **TOUS** les filtres simultanément
   - Un EPCI est **exclu** (grisé) dès qu'il sort de la plage d'**au moins une** variable

### Comment fonctionne l'indexation SEO ?

1.  **robots.txt** : Un fichier `assets/robots.txt` est présent pour guider les moteurs de recherche. Il est servi à la racine (`/robots.txt`) via une route Flask dédiée dans `app_v2.py`.
2.  **Sitemap** : Le `robots.txt` pointe vers un sitemap (URL à adapter dans le fichier selon votre domaine Render).
3.  **Validation Google Search Console** : La validation est effectuée via une balise `<meta name="google-site-verification">` configurée dans le constructeur `dash.Dash` de `app_v2.py`.
