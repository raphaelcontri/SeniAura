
# Dashboard Interactif EPCI

Ce tableau de bord permet de visualiser des indicateurs de précarité et de santé à l'échelle des EPCI (Établissements Publics de Coopération Intercommunale).

## Prérequis

Assurez-vous d'avoir installé les dépendances nécessaires :

```bash
pip install -r ../requirements.txt
```

(Le fichier `requirements.txt` se trouve à la racine du projet)

## Structure des Données

Le dashboard utilise :
- **GeoJSON** : `data/epci-ara.geojson` (Généré à partir de `communes-ara.geojson` via le script `scripts/prepare_geo_data.py`)
- **CSV Data** : `../../data/sources/dataset_pour_python_60_ans_et_plus_avec_score_precarite - df1_with_precarity_score(1).csv.csv`

## Lancement

Pour lancer l'application :

```bash
python app.py
```

Ensuite, ouvrez votre navigateur à l'adresse : `http://127.0.0.1:8050/`

## Fonctionnalités

- **Carte Choroplèthe** : Visualisation des différents indicateurs.
- **Sélecteur de Métrique** : Choisissez "Score de Précarité", "Population 60+", etc.
- **Survol** : Affichez le nom de l'EPCI et la valeur au survol de la souris.
- **Zoom/Pan** : Navigation interactive sur la carte.
