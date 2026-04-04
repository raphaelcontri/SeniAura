# 🚀 Déploiement & FAQ

## Développement local

```bash
# 1. Cloner le dépôt
git clone https://github.com/raphaelcontri/SeniAura.git
cd SeniAura-main

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer le serveur de développement
python app_v2.py

# 4. Accéder au dashboard
# → http://localhost:8050
```

!!! warning "Données manquantes"
    Le dataset Excel et le GeoJSON ne sont **pas** versionnés pour des raisons de conformité. Placez les fichiers dans `data/` avant de lancer.

---

## Production (Gunicorn)

```bash
gunicorn app_v2:server -b 0.0.0.0:8050 --workers 4
```

!!! tip "Hébergement sur Render"
    L'application est hébergée sur [Render](https://render.com). Le `Procfile` ou la commande de démarrage doit pointer vers `gunicorn app_v2:server`.

---

## Prérequis de fichiers

| Fichier | Chemin relatif | Format |
|:---|:---|:---|
| Dataset EPCI | `data/FINAL-DATASET-epci-11.xlsx` | Excel avec colonne `CODE_EPCI` |
| Dictionnaire variables | `data/dictionnaire_variables.csv` | CSV avec colonnes : Variable, Description, Catégorie, Sens, Unité, Sources, Classement, Nom_Court |
| GeoJSON EPCI | `data/epci-ara.geojson` | GeoJSON avec propriétés `EPCI_CODE` et `DEPARTEMEN` |
| Texte accueil | `texte introductif du dashboard.txt` | Texte brut, sections séparées par `\n> ` |
| Logo | `assets/Senio.png` | Image PNG |

---

## Déployer la documentation (GitHub Pages)

```bash
# À partir de la racine du projet, une seule commande suffit :
mkdocs gh-deploy
```

Cela construit le site et le pousse sur la branche `gh-pages` du dépôt.
La documentation sera disponible à :
👉 **https://raphaelcontri.github.io/SeniAura/**

---

## FAQ Technique

### Comment ajouter une nouvelle variable ?

1. Ajouter la **colonne dans l'Excel** (`FINAL-DATASET-epci-11.xlsx`) avec des valeurs numériques par EPCI
2. Ajouter une **ligne dans le dictionnaire CSV** :
   - `Variable` = nom exact de la colonne Excel
   - `Catégorie` = `Socioéco` / `Offre de soins` / `Environnement` / `Santé`
   - `Classement` = `67` (prioritaire) ou vide (standard)
   - Remplir `Description`, `Unité`, `Sources`, `Sens`, `Nom_Court`
3. **Relancer l'application** → la variable apparaît automatiquement dans les menus

!!! note "Pas besoin de toucher au code Python pour ajouter une variable standard."

---

### Comment ajouter une ville sur la carte ?

Modifier la liste `cities` dans `update_map()` dans `exploration.py` :

```python
cities = [
    {"name": "Lyon", "lat": 45.764, "lon": 4.836},
    {"name": "Nouvelle Ville", "lat": XX.XXX, "lon": Y.YYY},  # ← Ajouter ici
]
```

---

### Pourquoi le radar nécessite-t-il au moins 3 variables ?

Le graphique `Scatterpolar` de Plotly requiert **au minimum 3 axes** pour former un polygone lisible. Avec 2 variables ou moins, le graphique dégénère en une ligne (2 points) ou un point.

---

### Comment modifier le texte de la page d'accueil ?

Éditer le fichier `texte introductif du dashboard.txt`.
Les sections sont délimitées par `\n> ` suivi du titre. Le parsing est automatique dans `home.py`.

---

### Comment fonctionne le filtrage des EPCI ?

1. L'utilisateur sélectionne des variables dans la sidebar
2. Des `RangeSliders` sont générés dynamiquement pour chaque variable
3. À chaque interaction, un masque booléen est calculé :

```python
mask = pd.Series([True] * len(gdf))
for var, (lo, hi) in active_filters.items():
    mask &= (gdf[var] >= lo) & (gdf[var] <= hi)
```

Un EPCI est **inclus** (coloré) s'il satisfait **tous** les filtres simultanément.  
Un EPCI est **exclu** (grisé) dès qu'il sort de la plage d'**au moins une** variable.

---

### Comment fonctionne le SEO ?

| Mécanisme | Détail |
|:---|:---|
| `robots.txt` | Servi via route Flask dédiée dans `app_v2.py` |
| Meta `google-site-verification` | Balise HTML injectée via `dash.Dash(meta_tags=[...])` |
| Sitemap | Référencé dans `robots.txt` (URL à adapter selon le domaine) |
