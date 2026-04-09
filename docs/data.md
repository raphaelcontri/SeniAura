# 🗃️ Données et Pipeline de Chargement

## Fichier : `src/data.py`

### Fonction centrale : `load_data()`

Unique point d'entrée pour toutes les données. Elle est appelée **une seule fois au démarrage** par chaque module qui en a besoin.

```python
gdf_merged, variable_dict, category_dict, sens_dict, description_dict, \
unit_dict, gdf_deps, source_dict, classement_dict = load_data()
```

#### Valeurs de retour

| Retour | Type | Description |
|:---|:---|:---|
| `gdf_merged` | `GeoDataFrame` | Données fusionnées (géométrie EPCI + toutes les variables) |
| `variable_dict` | `dict[str, str]` | `{code_variable → nom_lisible}` |
| `category_dict` | `dict[str, str]` | `{code_variable → catégorie}` |
| `sens_dict` | `dict[str, int]` | `{code_variable → 1 ou -1}` |
| `description_dict` | `dict[str, str]` | `{code_variable → description_longue}` |
| `unit_dict` | `dict[str, str]` | `{code_variable → unité}` |
| `gdf_deps` | `GeoDataFrame` | Contours dissolus des **départements** (pour l'overlay carte) |
| `source_dict` | `dict[str, str]` | `{code_variable → institution_source}` |
| `classement_dict` | `dict[str, str]` | `{code_variable → classement}` |

---

## Pipeline de chargement (5 étapes)

```
Étape 1 : GeoJSON (epci-ara.geojson)
          → gdf_epci [GeoPandas, ~130 lignes, CRS WGS84]

Étape 2 : Excel (FINAL-DATASET-epci-11.xlsx)
          → df [Pandas DataFrame, 30+ colonnes par EPCI]
          → Nettoyage des types numériques (force pd.to_numeric)
          → Fix spécifique pour IR_D9_D1_SL (confus avec une date par Excel)

Étape 3 : CSV Métadonnées (dictionnaire_variables.csv)
          → Peuple les 7 dictionnaires (variable_dict, category_dict, etc.)
          → Overrides codés en dur pour variables critiques sans entrée CSV

Étape 4 : Agrégats démographiques genrés (6 variables calculées)
          → Somme des taux bruts INSEE par sexe/tranche d'âge * 100

Étape 5 : Merge & Dissolve
          → gdf_epci ⟕ df sur EPCI_CODE = CODE_EPCI
          → Dissolve par département → gdf_deps (fond cartographique)
```

---

## Logique de classement

Le champ `Classement` du dictionnaire CSV est le **mécanisme de visibilité** de chaque variable dans l'interface.

| Valeur | Comportement dans l'UI |
|:---|:---|
| `0`, `1`, `2` | **Totalement exclues** — ni sidebar, ni méthodologie |
| `3` | **Exclues de la sidebar** mais visibles dans la page Méthodologie (catégorie Santé uniquement) |
| `67` | **Prioritaires** — remontées en premier dans les menus déroulants |
| *(vide ou autre)* | Variables standard — triées alphabétiquement |

!!! note "Cas d'usage du classement `3`"
    Les variables de santé (Incidence, Mortalité, Prévalence) sont les variables *à expliquer*. On les rend visibles en méthodologie pour la transparence, mais on les exclut des filtres pour éviter une circularité analytique.

---

## Agrégats démographiques genrés

Au lieu d'utiliser des parts d'âge globales, l'application calcule **6 variables synthétiques** à partir des taux bruts de population de l'INSEE (colonnes `SEXE1_AGEPYR*` / `SEXE2_AGEPYR*`).

### Source : INSEE RP (Recensement de la Population)

| Variable calculée | Colonnes sources | Sens | Description |
|:---|:---|:---:|:---|
| `H_0_24` | `SEXE1_AGEPYR1000` à `1018` | `-1` | Part des hommes de 0 à 24 ans |
| `F_0_24` | `SEXE2_AGEPYR1000` à `1018` | `-1` | Part des femmes de 0 à 24 ans |
| `H_25_64` | `SEXE1_AGEPYR1025`, `1040`, `1055` | `-1` | Part des hommes de 25 à 64 ans |
| `F_25_64` | `SEXE2_AGEPYR1025`, `1040`, `1055` | `-1` | Part des femmes de 25 à 64 ans |
| `H_65_plus` | `SEXE1_AGEPYR1065`, `1080` | `+1` | Part des hommes 65 ans et + |
| `F_65_plus` | `SEXE2_AGEPYR1065`, `1080` | `+1` | Part des femmes 65 ans et + |

**Formule** :
```python
df['H_65_plus'] = df[cols_H_65_plus].sum(axis=1) * 100  # → [0, 100]%
```

!!! tip "Pertinence médicale"
    La ventilation H/F est essentielle pour l'analyse CNR : les risques cardiovasculaires diffèrent substantiellement entre hommes et femmes (ex. facteurs de risque, âge d'apparition, accès aux soins).

---

## Chemins de fichiers

```python
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, "data")

GEOJSON_PATH  = DATA_DIR + "/epci-ara.geojson"
DATASET_PATH  = DATA_DIR + "/FINAL-DATASET-epci-11.xlsx"
DICT_PATH     = DATA_DIR + "/dictionnaire_variables.csv"
HOSP_PATH     = DATA_DIR + "/hospitals_ara.csv"
```

!!! warning "Prérequis de déploiement"
    Les quatre fichiers de données doivent être présents au chemin relatif indiqué. Les données ne sont **pas** versionnées dans le dépôt Git public.

---

## Données Hospitalières (Centres de soins)

Le dashboard affiche les établissements de santé (hôpitaux et centres spécialisés) de la région AURA comme repères visuels sur la carte.

### Source : Base FINESS (Extraction ARA)
- **Fichier** : `data/hospitals_ara.csv`
- **Génération** : Ce fichier est le résultat d'une intersection spatiale (`GeoPandas`) entre la base nationale des hôpitaux et le contour géographique de la région Auvergne-Rhône-Alpes.
- **Contenu** : 
    - `name` : Nom de l'établissement.
    - `lat` / `lon` : Coordonnées géographiques.

### Intégration
Contrairement aux variables EPCI qui sont chargées dans `src/data.py`, les hôpitaux sont lus directement dans le callback `update_map` de `exploration.py` pour un affichage en couche de points (`go.Scattergeo`).

