# 📄 Logique des Pages

## 5.1 — Page Accueil (`home.py`)

**Taille** : ~187 lignes

### Fonctionnement

La page d'accueil est **entièrement pilotée par un fichier texte**, ce qui permet de modifier le contenu sans toucher au code Python :

```python
# Lecture du fichier texte externe
with open("texte introductif du dashboard.txt", encoding="utf-8") as f:
    content = f.read()

# Parse les sections séparées par "\n> "
sections = content.split("\n> ")
```

Chaque section devient un `AccordionItem` avec une icône contextuelle automatiquement associée au titre.

### Callbacks

| Callback | Type | Action |
|:---|:---|:---|
| `open_prise_en_main` | Server-side | Ouvre la section "Prise en main" dans l'Accordion |
| `scrollToAccordion` | **Client-side (JS)** | Scroll smooth vers `#accordion-item-prise-en-main` |

---

## 5.2 — Page Exploration (`exploration.py`)

**Taille** : ~890 lignes — **cœur fonctionnel de l'application**

### Layout

```
Container (fluid)
├── Paper #container-map
│   ├── Titre dynamique (#map-dynamic-title)
│   ├── dcc.Graph #map-graph (550px)
│   └── Group (stats + narration)
│       ├── Paper bg=#f8f9fa : Interprétations + Narratif + Descriptions
│       └── Paper (caché) : Sélecteur d'exclusion par variable
│
└── Paper #container-radar
    ├── Titre dynamique (#radar-dynamic-title)
    ├── Placeholder (affiché si < 3 variables actives)
    ├── dcc.Graph #radar-chart (Scatterpolar)
    └── #radar-reading-guide : Interprétations + Quantiles régionaux
```

### Callback 1 : `update_sliders`

Génère dynamiquement les `RangeSlider` pour chaque variable sélectionnée dans les MultiSelects.

```
Inputs : sidebar-filter-social, sidebar-filter-offre, sidebar-filter-env
Outputs: slider-container-social, slider-container-offre, slider-container-env
```

Pour chaque variable sélectionnée, crée un composant `dcc.RangeSlider` :
- `min` / `max` calculés depuis `gdf_merged[var].min()` et `.max()`
- Marques "Min" et "Max" aux deux extrémités
- Tooltips persistants sur les poignées

### Callback 2 : `select_epci_on_click`

```
Input  : map-graph.clickData
State  : sidebar-epci-radar.value
Output : sidebar-epci-radar.value
```

Au clic sur un polygone EPCI :
1. Extrait le nom de l'EPCI depuis `clickData["points"][0]["text"]`
2. Retrouve son `CODE_EPCI` dans `gdf_merged`
3. **Bascule** son état (toggle) dans la liste MultiSelect du Radar

### Callback 3 : `update_highlight_options`

```
Inputs : sidebar-filter-social, sidebar-filter-offre, sidebar-filter-env
Output : highlight-variable-select.data
```

Met à jour la liste des variables disponibles pour la visualisation d'exclusion spécifique (le sélecteur affiché sous la carte).

### Callback 4 : `update_map` ← Plus complexe

```
Inputs: map-indic-select, map-patho-select, exploration-sliders (ALL),
        sidebar-epci-radar, highlight-variable-select
Outputs: map-graph.figure, map-stats-header-content, map-reading-guide,
         map-narrative-content, map-dynamic-title
```

#### Rendu de la carte (6 couches, ordre de superposition)

| # | Couche Plotly | Description |
|:---:|:---|:---|
| 1 | **Fond gris** (`Choropleth`) | Tous les EPCI en gris clair — base visuelle |
| 2 | **Choroplèthe coloré** (`Choropleth`) | EPCI validant tous les filtres, colorés selon l'indicateur sélectionné |
| 3 | **Frontières départements** (`Choropleth`) | Lignes noires semi-transparentes (geometries dissolves) |
| 4 | **Exclusions spécifiques** (`Choropeth`) | EPCI grisés à cause d'une seule variable (si "highlight" actif) |
| 5 | **Sélection Radar** (`Scattergeo`) | Contours rouges des EPCI sélectionnés pour le radar |
| 6 | **Villes repères** (`Scattergeo`) | 13 préfectures et villes majeures ARA (points + labels) |

#### Tooltip des EPCI au survol

Inclut :
- Nom de l'EPCI en **gras**
- Instruction de clic (pour ajouter au radar)
- Démographie senior : `👨 Hommes 65+ : X%  |  👩 Femmes 65+ : Y%`

#### Contenu narratif généré

Après rendu, le callback construit dynamiquement :
1. Un résumé statistique (N EPCI inclus / N exclus)
2. Des **phrases narratives** décrivant les filtres actifs (connecteurs aléatoires)
3. Les descriptions détaillées des variables sélectionnées

### Callback 5 : `update_radar`

```
Inputs : sidebar-filter-social, sidebar-filter-offre, sidebar-filter-env,
         sidebar-epci-radar, map-indic-select, map-patho-select
Outputs: radar-chart.figure, radar-chart.style, radar-placeholder.style,
         radar-reading-guide.children, radar-dynamic-title.children
```

#### Logique de normalisation

Toutes les variables sont normalisées **min-max [0, 1]** sur l'ensemble régional pour comparaison équitable.

```python
norm_val = (val - col_min) / (col_max - col_min)
# Si sens == -1, inversion : norm_val = 1 - norm_val
```

#### Structure du graphique Radar (`Scatterpolar`)

| Trace | Description |
|:---|:---|
| Zone σ (+) | Polygone gris clair = zone \[moyenne + 1 écart-type\] |
| Zone σ (−) | Polygone masque = zone sous \[moyenne − 1 écart-type\] |
| Ligne Région | Moyenne régionale en gris, fermée en boucle |
| EPCI 1...N | Polygones colorés (jusqu'à 8), un par territoire |

#### Interprétation automatique (z-score)

Pour chaque variable de chaque EPCI :

| Z-score | Libellé généré |
|:---:|:---|
| `\|z\| < 0.5` | "proche de la moyenne régionale" |
| `0.5 ≤ \|z\| < 1.5` | "légèrement au-dessus/en dessous" |
| `\|z\| ≥ 1.5` | "nettement au-dessus/en dessous" |

#### Badges de positionnement régional

| Badge | Couleur | Signification |
|:---|:---:|:---|
| Top 10% | 🔴 Rouge | Parmi les 10% les plus élevés de la région |
| Top 25% | 🟠 Orange | Parmi le premier quartile |
| Médian | ⚫ Gris | Valeur proche de la médiane |
| Bas 25% | 🔵 Cyan | Dernier quartile |
| Bas 10% | 🟢 Teal | Parmi les 10% les plus bas |

---

## 5.3 — Page Méthodologie (`methodology.py`)

**Taille** : ~237 lignes

### Structure en onglets

```
Tabs (pills, variante bleue)
├── Onglet : Socioéco          → Table des variables
├── Onglet : Offre de soins    → Table des variables
├── Onglet : Environnement     → Table des variables
├── Onglet : Santé             → Table des variables
└── Onglet : Construction et méthodologie → Accordion
    ├── Sources primaires et collecte
    ├── Nettoyage et harmonisation
    └── Standardisation géographique
```

### Tables de variables

Chaque table affiche 4 colonnes à largeur fixe (`layout="fixed"`) pour éviter le débordement :

| Colonne | Largeur | Contenu |
|:---|:---:|:---|
| Variable | 200px | Nom court (`Nom_Court` du dictionnaire) |
| Description | 400px | Description longue |
| Unité | 100px | `%`, `‰`, `€`, `nb`, etc. |
| Source | 250px | Institution source |

---

## 5.4 — Radar Legacy (`radar.py`) ⚠️

!!! warning "Non utilisé"
    Ce fichier n'est **pas chargé** par `app_v2.py`. Le radar est intégré directement dans `exploration.py`. Ce fichier est conservé uniquement à titre de référence historique.
