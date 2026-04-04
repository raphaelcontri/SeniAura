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

1. GeoJSON (epci-ara.geojson) → gdf_epci (contours EPCI)
2. Excel (FINAL-DATASET-epci-11.xlsx) → df (variables par EPCI)
3. CSV (dictionnaire_variables.csv) → Métadonnées (dicts)
4. Merge (gdf_epci ⟕ df) sur EPCI_CODE → gdf_merged
5. Dissolve par département → gdf_deps (frontières départementales)

#### Logique de filtrage des variables (`classement_dict`)

Le champ `Classement` dans le dictionnaire CSV contrôle la visibilité des variables :

| Classement | Comportement |
|---|---|
| `0`, `1`, `2` | **Exclues partout** (ni sidebar, ni méthodologie) |
| `3` | Exclues du sidebar mais **visibles en méthodologie** (catégorie Santé uniquement) |
| `67` | **Variables prioritaires** (affichées en premier dans les menus déroulants) |
| Autre | Variables standard, triées alphabétiquement |
