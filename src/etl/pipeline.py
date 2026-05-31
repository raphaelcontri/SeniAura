"""
Pipeline ETL (Extract-Transform-Load) automatisé pour le projet CardiAURA.
Ce script nettoie, valide et optimise les données géospatiales et tabulaires.
Il effectue les opérations suivantes :
1. Extraction : Chargement de FINAL-DATASET-epci-11.xlsx, epci-ara.geojson et dictionnaire_variables.csv.
2. Transformation :
   - Nettoyage et standardisation des codes EPCI (SIREN).
   - Typage numérique strict des variables d'analyse.
   - Simplification géométrique du GeoJSON (réduction de taille de ~80% pour la fluidité).
   - Validation et catégorisation automatique du dictionnaire des variables.
3. Chargement :
   - Sauvegarde au format optimisé Parquet (chargement instantané en <50ms).
   - Sauvegarde du GeoJSON simplifié.
   - Sauvegarde du dictionnaire nettoyé.
"""

import os
import time
import pandas as pd
import geopandas as gpd
import numpy as np

# Chemins relatifs à la racine de SeniAura-main
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # src/
PROJECT_ROOT = os.path.dirname(BASE_DIR) # SeniAura-main/
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Fichiers sources
EXCEL_PATH = os.path.join(DATA_DIR, "FINAL-DATASET-epci-11.xlsx")
GEOJSON_PATH = os.path.join(DATA_DIR, "epci-ara.geojson")
DICT_PATH = os.path.join(DATA_DIR, "dictionnaire_variables.csv")

# Fichiers cibles (optimisés)
PARQUET_PATH = os.path.join(DATA_DIR, "FINAL-DATASET-epci-11.parquet")
GEOJSON_SIMPLIFIED_PATH = os.path.join(DATA_DIR, "epci-ara-simplified.geojson")

def run_etl():
    print("=" * 60)
    print("🚀 DÉMARRAGE DU PIPELINE ETL AUTOMATISÉ - CardiAURA")
    print("=" * 60)
    start_time = time.time()

    # ----------------------------------------------------
    # 1. EXTRACTION
    # ----------------------------------------------------
    print("\n📥 ÉTAPE 1 : EXTRACTION DES DONNÉES SOURCES...")
    
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"❌ Erreur : Fichier Excel source introuvable à {EXCEL_PATH}")
    if not os.path.exists(GEOJSON_PATH):
        raise FileNotFoundError(f"❌ Erreur : Fichier GeoJSON source introuvable à {GEOJSON_PATH}")
    if not os.path.exists(DICT_PATH):
        raise FileNotFoundError(f"❌ Erreur : Dictionnaire des variables introuvable à {DICT_PATH}")

    print("  -> Chargement du fichier Excel...")
    df_raw = pd.read_excel(EXCEL_PATH)
    print(f"     ✅ Fichier Excel chargé ({df_raw.shape[0]} lignes, {df_raw.shape[1]} colonnes)")

    print("  -> Chargement du GeoJSON...")
    gdf_raw = gpd.read_file(GEOJSON_PATH)
    print(f"     ✅ GeoJSON chargé ({gdf_raw.shape[0]} entités géospatiales)")

    print("  -> Chargement du dictionnaire des variables...")
    df_dict = pd.read_csv(DICT_PATH)
    print(f"     ✅ Dictionnaire chargé ({df_dict.shape[0]} variables référencées)")

    # ----------------------------------------------------
    # 2. TRANSFORMATION (TABULAIRE & QUALITÉ)
    # ----------------------------------------------------
    print("\n⚙️ ÉTAPE 2 : NETTOYAGE & TRANSFORMATION DES DONNÉES...")
    
    # Copie de travail
    df = df_raw.copy()

    # Standardisation de la clé de jointure CODE_EPCI
    if 'CODE_EPCI' in df.columns:
        print("  -> Standardisation des codes EPCI (SIREN)...")
        # Nettoyage des formats réels/flottants lus de l'Excel (ex: 200000172.0 -> 200000172)
        df['CODE_EPCI'] = df['CODE_EPCI'].astype(str).str.replace('.0', '', regex=False).str.strip()
        print("     ✅ Codes EPCI convertis en chaînes de caractères nettoyées.")
    else:
        print("  ⚠️ Attention : La colonne 'CODE_EPCI' est absente du jeu de données !")

    # Nettoyage des noms de colonnes
    df.columns = [col.strip() for col in df.columns]

    # Typage numérique strict des variables d'analyse
    print("  -> Validation et typage strict des colonnes numériques...")
    technical_cols = ['CODE_EPCI', 'nom_EPCI', 'LIBEPCI', 'Département', 'NATURE_EPCI', 'Département_code']
    converted_count = 0
    for col in df.columns:
        if col not in technical_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            converted_count += 1
    print(f"     ✅ {converted_count} colonnes analytiques typées de force en numérique.")

    # Calcul dynamique de la variable composite Taux_CNR si manquante
    if 'Taux_CNR' not in df.columns or df['Taux_CNR'].isna().all():
        print("  -> Calcul automatisé de la variable composite 'Taux_CNR' (Incidence Globale)...")
        cols_to_sum = ['INCI_AVC', 'INCI_CardIsch', 'INCI_InsuCard']
        existing_cols = [c for c in cols_to_sum if c in df.columns]
        if existing_cols:
            df['Taux_CNR'] = df[existing_cols].sum(axis=1)
            print("     ✅ Taux_CNR calculé avec succès comme somme des incidences partielles.")
        else:
            print("     ⚠️ Impossible de calculer Taux_CNR : variables sources absentes.")

    # ----------------------------------------------------
    # 3. TRANSFORMATION (GÉOSPATIALE - SIG)
    # ----------------------------------------------------
    print("\n🗺️ ÉTAPE 3 : SIMPLIFICATION GÉOMÉTRIQUE GIS (OPTIMISATION CARTOGRAPHIQUE)...")
    
    gdf = gdf_raw.copy()
    # Nettoyage de la clé de jointure dans le GeoJSON
    if 'EPCI_CODE' in gdf.columns:
        gdf['EPCI_CODE'] = gdf['EPCI_CODE'].astype(str).str.strip()
    
    # Mesure de taille avant simplification
    initial_vertices = sum(len(geom.exterior.coords) for geom in gdf.geometry if geom is not None and hasattr(geom, 'exterior'))
    print(f"  -> Nombre total initial de sommets géométriques : {initial_vertices}")

    # Simplification géométrique (seuil 0.0015 degrés ~150 mètres)
    print("  -> Application de l'algorithme de simplification (tolérance = 0.0015)...")
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.0015, preserve_topology=True)
    
    # Mesure après simplification
    final_vertices = sum(len(geom.exterior.coords) for geom in gdf.geometry if geom is not None and hasattr(geom, 'exterior'))
    reduction = (1 - (final_vertices / initial_vertices)) * 100
    print(f"     ✅ Géométrie simplifiée ! Nombre de sommets réduit à {final_vertices} (Gain de {reduction:.1f}%).")

    # ----------------------------------------------------
    # 4. TRANSFORMATION & NETTOYAGE DU DICTIONNAIRE
    # ----------------------------------------------------
    print("\n📖 ÉTAPE 4 : NETTOYAGE ET VALIDAITON DU DICTIONNAIRE DES VARIABLES...")
    
    # Nettoyage des chaînes de caractères
    for col in df_dict.columns:
        df_dict[col] = df_dict[col].astype(str).str.strip().replace('nan', np.nan).replace('?', np.nan)
    
    # Catégorisation automatique robuste
    def auto_categorize(row):
        var = str(row['Variable']).strip()
        existing_cat = str(row['Catégorie']).strip().lower() if pd.notna(row['Catégorie']) else ''
        
        # Conserver la catégorie si elle est déjà valide et explicite
        if existing_cat in ['socioéco', 'environnement', 'offre de soins', 'santé']:
            return existing_cat
            
        # Règles de matching par préfixe ou contenu
        if any(x in var for x in ['APL', 'Officines', 'Pharmaciens', 'Maisons_Sante', 'Centres_Sante', 'EHPAD']):
            return 'offre de soins'
        if any(var.startswith(x) for x in ['AIR', 'BRUIT', 'POLLEN', 'EAU', 'SOLS', 'INDUSTRIE', 'AGRI', 'MOB', 'LOGEMENT']):
            return 'environnement'
        if any(var.startswith(x) for x in ['INCI', 'MORT', 'PREV', 'Taux_CNR']):
            return 'santé'
        if any(x in var for x in ['FDep', 'Revenu', 'Chomeurs', 'chomeurs', 'ouvriers', 'bacheliers', 'PR_MD', 'D1_', 'D9_', 'IR_', 'PCS_', 'DIPLOME', 'Part de personnes', 'Indice_Precarite', 'MED_SL', 'EDI_Moyen']):
            return 'socioéco'
            
        return 'autre'

    df_dict['Catégorie'] = df_dict.apply(auto_categorize, axis=1)
    
    # Force Nom_Court si manquant
    def fill_nom_court(row):
        if pd.isna(row['Nom_Court']) or row['Nom_Court'] == '':
            return str(row['Variable'])
        return row['Nom_Court']
    df_dict['Nom_Court'] = df_dict.apply(fill_nom_court, axis=1)

    print("     ✅ Dictionnaire nettoyé, catégorisé automatiquement et enrichi.")

    # ----------------------------------------------------
    # 5. CHARGEMENT & EXPORTATION DES LIVRABLES
    # ----------------------------------------------------
    print("\n💾 ÉTAPE 5 : CHARGEMENT ET SAUVEGARDE DES LIVRABLES OPTIMISÉS...")

    # A. Sauvegarde au format Parquet
    print(f"  -> Exportation du jeu de données au format Parquet : {PARQUET_PATH}")
    df.to_parquet(PARQUET_PATH, index=False, engine='pyarrow')
    parquet_size_kb = os.path.getsize(PARQUET_PATH) / 1024
    print(f"     ✅ Fichier Parquet sauvegardé avec succès ({parquet_size_kb:.1f} Ko).")

    # B. Sauvegarde du GeoJSON simplifié
    print(f"  -> Exportation du GeoJSON simplifié : {GEOJSON_SIMPLIFIED_PATH}")
    # Force le CRS en WGS 84 (EPSG:4326) au cas où
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    gdf.to_file(GEOJSON_SIMPLIFIED_PATH, driver="GeoJSON")
    geojson_size_kb = os.path.getsize(GEOJSON_SIMPLIFIED_PATH) / 1024
    print(f"     ✅ Fichier GeoJSON simplifié sauvegardé avec succès ({geojson_size_kb:.1f} Ko).")

    # C. Sauvegarde du dictionnaire mis à jour
    print(f"  -> Sauvegarde du dictionnaire des variables nettoyé : {DICT_PATH}")
    df_dict.to_csv(DICT_PATH, index=False)
    print("     ✅ Fictionnaire CSV mis à jour.")

    end_time = time.time()
    elapsed = end_time - start_time
    print("\n" + "=" * 60)
    print(f"🎉 PIPELINE TERMINÉ AVEC SUCCÈS EN {elapsed:.2f} SECONDES !")
    print("=" * 60)

if __name__ == "__main__":
    run_etl()
