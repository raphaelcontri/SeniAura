# Guide Databricks Community Edition - Pipeline de Calcul CardiAURA

Ce guide explique comment configurer votre espace gratuit **Databricks Community Edition** pour lire les CSV bruts importés par les utilisateurs depuis **Supabase Storage**, effectuer des traitements lourds (SQL/Spark) et du Machine Learning (K-Means), puis renvoyer les fichiers propres pour affichage automatique sur votre dashboard.

---

## ☁️ Étape 1 : Obtenir les clés d'accès de votre stockage Supabase

Pour que Databricks puisse se connecter à Supabase, nous utilisons l'API standard de Supabase Storage.
1. Connectez-vous à votre console **Supabase**.
2. Allez dans **Project Settings** (icône engrenage) > **API**.
3. Récupérez :
   * Votre **Project URL** (ex: `https://xyz.supabase.co`)
   * Votre **Service Role Key** (la clé secrète sous *Project API keys*).

---

## 🛠️ Étape 2 : Configurer l'Environnement Databricks (Calcul Serverless & Table de base)

Dans la nouvelle version **Free Edition** de Databricks, le calcul est entièrement **Serverless (sans serveur à gérer)**. Vous n'avez plus besoin de créer, configurer ou démarrer manuellement un cluster (ce qui explique pourquoi l'onglet "Compute" n'affiche que des options d'entrepôts SQL inactifs ou grisés).

Databricks gère et alloue automatiquement la puissance de calcul nécessaire en arrière-plan lorsque vous exécutez votre Notebook.

### 2.1 Importer la Table de Référence des EPCI
Pour pouvoir croiser les données utilisateur avec la population ou les noms des EPCI :
1. Dans la barre latérale gauche, cliquez sur **Catalog**.
2. Cliquez sur le bouton **Create Table** (ou **Add Data** / **Add** en haut de page, puis **Upload files**).
3. Glissez-déposez le fichier de données historique de votre projet : **`FINAL-DATASET-epci-11.xlsx`** (présent dans le dossier `data/` de votre projet local).
4. Suivez les étapes de chargement et nommez la table finale précisément : **`epci_base_referentiel`**.

---

## 📝 Étape 3 : Créer le Notebook de traitement dans Databricks

1. Cliquez sur le bouton **New** (ou le bouton **+** en haut du menu latéral) ➔ **Notebook**.
2. Nommez-le `cardiaura_pipeline`.
3. En haut à droite du Notebook, vérifiez le sélecteur de calcul (généralement étiqueté **Connect** ou avec une icône de serveur) : il doit être configuré sur **Serverless** par défaut. Si ce n'est pas le cas, cliquez dessus et sélectionnez **Serverless**.
4. Vous pouvez maintenant exécuter votre code PySpark directement sans aucun délai de démarrage de serveur !
3. Créez des cellules de code et collez les blocs de code ci-dessous.

### 3.1 Connexion et lecture du CSV brut depuis Supabase

Ce code télécharge le fichier CSV brut qui a été déposé par votre application Dash.

```python
# Notebook Databricks - Cellule 1 (Python)
# Installez le SDK Supabase officiel pour gérer proprement les nouvelles clés d'API (sb_secret_...)
# Exécutez cette ligne au début ou dans une cellule séparée en haut :
# %pip install supabase

from supabase import create_client, Client
import io
import pandas as pd

# Remplacez par vos vrais identifiants
SUPABASE_URL = "https://xyz.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "votre_service_role_key"
BUCKET_NAME = "cardiaura-datasets"

# Le chemin du fichier brut déposé
file_path_in_bucket = "raw/user123_1717320000_indicateurs.csv" 

try:
    # Connexion via le client officiel
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    # Téléchargement des octets du fichier
    file_bytes = supabase.storage.from_(BUCKET_NAME).download(file_path_in_bucket)
    
    # Charger dans un DataFrame Spark
    pdf_raw = pd.read_csv(io.BytesIO(file_bytes))
    df_spark = spark.createDataFrame(pdf_raw)
    df_spark.createOrReplaceTempView("user_csv_raw")
    print("Fichier chargé avec succès dans Spark !")
except Exception as e:
    print(f"Erreur de téléchargement : {e}")
```

---

### 3.2 Analyse et jointures lourdes en Spark SQL

Une fois le fichier brut chargé dans Spark, vous pouvez le croiser avec votre jeu de données de référence. 

Vous pouvez importer votre dataset de base (le fichier Parquet existant des EPCI) une fois dans Databricks pour pouvoir faire des jointures SQL.

```sql
%sql
-- Notebook Databricks - Cellule 2 (SQL)
-- Jointure et calcul d'un indicateur normalisé par rapport à la population de l'EPCI

CREATE OR REPLACE TEMP VIEW epci_processed_data AS
SELECT 
    c.CODE_EPCI,
    c.indicateur_brut,
    b.nom_EPCI,
    b.POP_2021,
    -- Normalisation automatique : taux pour 100 000 habitants
    (c.indicateur_brut / b.POP_2021) * 100000 AS indicateur_taux_100k
FROM user_csv_raw c
INNER JOIN epci_base_referentiel b ON c.CODE_EPCI = b.CODE_EPCI
```

---

### 3.3 Exécution du Machine Learning (Clustering K-Means sous PySpark)

Vous pouvez exécuter des pipelines ML complexes sur les nouvelles variables importées.

```python
# Notebook Databricks - Cellule 3 (Python / SparkML)
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler, StandardScaler

# Charger les données calculées à l'étape précédente
df_features = spark.sql("SELECT CODE_EPCI, indicateur_taux_100k FROM epci_processed_data")

# Pipeline SparkML de clustering K-Means
assembler = VectorAssembler(inputCols=["indicateur_taux_100k"], outputCol="features")
df_assembled = assembler.transform(df_features)

scaler = StandardScaler(inputCol="features", outputCol="scaledFeatures")
scaler_model = scaler.fit(df_assembled)
df_scaled = scaler_model.transform(df_assembled)

# Entrainement de K-Means (K=4)
kmeans = KMeans(k=4, seed=42, featuresCol="scaledFeatures", predictionCol="cluster_user")
model = kmeans.fit(df_scaled)
df_predictions = model.transform(df_scaled)

# Enregistrer les résultats de prédictions
df_predictions.createOrReplaceTempView("user_clusters")
```

---

### 3.4 Réécriture du fichier de résultats propre vers Supabase

Enfin, ce code prend le dataset final agrégé et labellisé (avec les clusters K-Means utilisateur), le convertit en CSV, et le téléverse dans le sous-dossier `clean/` de votre Bucket Supabase. Le dashboard Dash le lira alors instantanément de manière transparente.

```python
# Notebook Databricks - Cellule 4 (Python)
# Envoyer le fichier nettoyé vers Supabase Storage en utilisant le SDK officiel
try:
    # Initialisation du client (si pas déjà fait dans la cellule 1)
    from supabase import create_client, Client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    # Récupérer le dataframe final combiné
    df_final = spark.sql("""
        SELECT p.*, c.cluster_user 
        FROM epci_processed_data p
        JOIN user_clusters c ON p.CODE_EPCI = c.CODE_EPCI
    """).toPandas()
    
    # Convertir le DataFrame en CSV
    csv_data = df_final.to_csv(index=False)
    csv_bytes = csv_data.encode('utf-8')
    
    # Définir le chemin de sortie propre dans Supabase
    clean_file_path = file_path_in_bucket.replace("raw/", "clean/")
    
    # Téléverser le fichier propre (écrase si existant grâce à x-upsert: true)
    response = supabase.storage.from_(BUCKET_NAME).upload(
        path=clean_file_path,
        file=csv_bytes,
        file_options={"content-type": "text/csv", "x-upsert": "true"}
    )
    print(f"Jeu de données traité envoyé avec succès ! Chemin : {clean_file_path}")
except Exception as e:
    print(f"Échec de l'envoi : {e}")
```

---

## 🎯 Résultat & Automatisme

Grâce à cette boucle d'architecture :
1. L'utilisateur dépose son CSV sur votre site.
2. Databricks s'occupe de faire les jointures, les nettoyages et le clustering K-Means.
3. Les données nettoyées sont replacées dans Supabase dans le dossier `clean/`.
4. Le dashboard Dash est mis à jour et affiche la nouvelle carte et le nouveau radar interactif de l'utilisateur !
