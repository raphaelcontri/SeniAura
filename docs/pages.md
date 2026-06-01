
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

**Taille** : ~1150 lignes — **cœur fonctionnel de l'application**

### Layout

```
Container (fluid)
├── Paper #container-map
│   ├── Titre dynamique (#map-dynamic-title)
│   ├── dcc.Graph #map-graph (600px)
│   └── Grid (Interprétations + Statistiques d'exclusions)
│
├── Paper #container-radar
│   ├── Titre dynamique (#radar-dynamic-title)
│   ├── Placeholder (si < 3 variables actives)
│   ├── dcc.Graph #radar-chart (Scatterpolar)
│   └── #radar-reading-guide : Interprétations + Quantiles régionaux
│
└── Paper #container-cluster
    ├── Titre dynamique (#cluster-dynamic-title)
    ├── Placeholder (si aucune variable active)
    ├── dcc.Graph #cluster-chart (Centroïdes / Bar chart)
    └── #cluster-reading-guide : Profils types + Recommandations d'action
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
| 7 | **Hôpitaux ARA** (`Scattergeo`) | *(Désactivé)* Points roses représentant les centres de soins |

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
| Zone Moyenne ± σ | Polygone gris clair = zone \[moyenne ± 1 écart-type\] |
| Ligne Région | Moyenne régionale en gris, fermée en boucle |
| EPCI 1...N | Polygones colorés (jusqu'à 8), un par territoire |

#### Interprétation automatique (z-score)

Pour chaque variable de chaque EPCI :

| Z-score | Libellé généré |
|:---:|:---|
| `\|z\| < 0.5` | "proche de la moyenne régionale" |
| `0.5 ≤ \|z\| < 1.5` | "légèrement au-dessus/en dessous" |
| `\|z\| ≥ 1.5` | "nettement au-dessus/en dessous" |

#### Badges de positionnement régional et Phrases d'Interprétation

L'algorithme de positionnement analyse vos territoires finement via le **sens de la variable** (`sens_dict`, défini dans `dictionnaire_variables.csv`). Ainsi, il qualifie chaque indicateur et déclenche des "Points forts" ou des alertes ciblées :

**Cas 1 : Variables où une forte valeur est un ATOUT (Sens "1", ex: Densité médicale, Revenus)**

| Badge | Couleur | Signification |
|:---|:---|:---|
| Top 10% | 🎉 **Teal** (Vert Foncé) | Point fort : Supérieur au 9ème décile |
| Top 25% | 🟢 **Cyan** (Vert Clair) | Atout : Supérieur au 3ème quartile |
| Médian | ⚪ **Gris** | Équilibré : Proche de la médiane régionale |
| Bas 25% | 🟠 **Orange** | Attention : Sous le 1er quartile (Vulnérabilité) |
| Bas 10% | 🔴 **Rouge** | Alerte : Sous le 1er décile (Alerte critique) |

**Cas 2 : Variables où une forte valeur est une VULNÉRABILITÉ (Sens "-1", ex: Polluants, Précarité, Mortalité)**

| Badge | Couleur | Signification |
|:---|:---|:---|
| Bas 10% | 🎉 **Teal** (Vert Foncé) | Point fort : Inférieur au 1er décile |
| Bas 25% | 🟢 **Cyan** (Vert Clair) | Atout : Inférieur au 1er quartile |
| Médian | ⚪ **Gris** | Équilibré : Proche de la médiane régionale |
| Haut 25% | 🟠 **Orange** | Attention : Supérieur au 3ème quartile (Vulnérabilité) |
| Haut 10% | 🔴 **Rouge** | Alerte : Supérieur au 9ème décile (Alerte critique) |

### Callback 6 : `update_cluster`

```
Inputs : cluster-theme-selector.value, sidebar-epci-radar.value,
         map-indic-select.value, map-patho-select.value
Outputs: cluster-chart.figure, cluster-main-grid.style,
         cluster-placeholder.style, cluster-reading-guide.children,
         cluster-twins-table-container.children, cluster-dynamic-title.children,
         cluster-active-badge-container.children
```

#### Logique de Machine Learning Transparente & Vérifiable (K-Means & Similarité)

Pour simplifier la complexité géographique (172 EPCI) et statistique de la région AURA, l'application réalise une classification automatique stable en direct :
1.  **4 Typologies Thématiques avec Sélection Explicite** : L'utilisateur sélectionne explicitement la thématique active via un magnifique composant `dmc.SegmentedControl` au sommet de la carte (Santé, Socio-économie, Offre de Soins ou Environnement). Les variables de chaque modèle sont pré-sélectionnées de manière rigoureuse et stable.
2.  **Imputation & Standardisation** : Imputation robuste des valeurs manquantes par la médiane de colonne et normalisation transparente pour l'algorithme K-Means.
3.  **Classification ($K=4$) & Tri Anti-Label Switching** : Les territoires sont groupés en 4 clusters. Pour garantir une constance visuelle absolue, les clusters sont triés par niveau de vulnérabilité globale. Le Groupe 1 est le plus vulnérable (Rouge) et le Groupe 4 le plus favorable (Vert).
4.  **Recherche géométrique de « Jumeaux Territoriaux » (Benchmark)** : L'algorithme calcule la distance euclidienne directe dans l'espace standardisé pour identifier les 3 EPCI les plus proches (semblables) du territoire sélectionné. Cette distance est ensuite convertie de manière transparente en un **Taux de ressemblance sur 100 (%)** pour en faciliter l'appropriation :
    $$\text{Taux (\%)} = \max(0, 100 - d \times 20)$$

#### Rendu Interactif & Connexion Directe aux Leviers d'Action

Le callback génère un diagnostic territorial complet sous forme de grille interactive unifiée :
*   **Carte Régionale Unifiée** : La mini-carte redondante a été supprimée au profit d'une intégration complète. L'indicateur **"Typologie de Cluster (K-Means)"** est disponible directement dans le sélecteur principal de la carte du tableau de bord. La carte principale se colore alors dynamiquement selon les 4 typologies K-Means de la thématique active. Le sélecteur de pathologies s'estompe automatiquement pour plus de clarté.
*   **Profil de Graphique en Écart Relatif (%)** : Le graphique en Z-Score, complexe pour des non-statisticiens, a été remplacé par un graphique à barres groupées représentant l'**écart relatif moyen du cluster par rapport à la moyenne régionale (0%)**. La ligne noire superpose le profil exact de l'EPCI actif avec des infobulles claires (ex. `+24.5% vs moyenne régionale`).
*   **Jumeaux Territoriaux** (`cluster-twins-table-container`) : Un tableau premium liste les 3 EPCI jumeaux avec leur taux de ressemblance exact. Les boutons **"Analyser"** mettent à jour instantanément tout le tableau de bord pour se focaliser sur le territoire jumeau sélectionné, facilitant les échanges de bonnes pratiques CPTS/CLS.
*   **Fiches Narratives d'Interprétation** (`cluster-reading-guide`) : Affiche le titre clinique/sociologique du cluster (ex: *"Surtaux Généralisé & Alerte Clinique"*, *"Désertification Médicale Critique"*) ainsi qu'un **bouton d'action direct avec ancre d'URL** (`/leviers#sante`, `/leviers#socio`, `/leviers#env`) ouvrant automatiquement le bon onglet sur la page des leviers d'action.

---

## 5.3 — Page Méthodologie (`methodology.py`)

**Taille** : ~210 lignes

#### Structure en onglets

```
Tabs (pills, variante bleue)
├── Onglet : Liste des variables  → Table des variables (Socioéco, Offre, Env, Santé)
└── Onglet : Documentation Technique → Boutons vers MkDocs et GitHub
```

---

## 5.4 — Page Leviers d'action (`leviers.py`) [NEW]

**Taille** : ~45 lignes

- Affiche le contenu du fichier `Leviers d'action.md`.
- Intégrée directement dans la navigation principale du header.

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
