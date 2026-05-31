"""
Script de benchmark pour mesurer les gains de performance de chargement des données.
Compare le chargement via Parquet vs Excel d'origine.
"""

import os
import time
import pandas as pd
import geopandas as gpd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # SeniAura-main
DATA_DIR = os.path.join(BASE_DIR, "data")

EXCEL_PATH = os.path.join(DATA_DIR, "FINAL-DATASET-epci-11.xlsx")
PARQUET_PATH = os.path.join(DATA_DIR, "FINAL-DATASET-epci-11.parquet")
GEO_ORIGINAL = os.path.join(DATA_DIR, "epci-ara.geojson")
GEO_SIMPLIFIED = os.path.join(DATA_DIR, "epci-ara-simplified.geojson")

def test_load(df_path, geo_path, desc):
    start = time.time()
    
    # 1. Load GeoJSON
    gdf = gpd.read_file(geo_path)
    gdf['EPCI_CODE'] = gdf['EPCI_CODE'].astype(str).str.strip()
    # 2. Load Data
    if df_path.endswith('.parquet'):
        df = pd.read_parquet(df_path)
    else:
        df = pd.read_excel(df_path)
    df['CODE_EPCI'] = df['CODE_EPCI'].astype(str).str.replace('.0', '', regex=False).str.strip()
    # 3. Merge
    gdf_merged = gdf.merge(df, left_on='EPCI_CODE', right_on='CODE_EPCI', how='left')
    
    elapsed = (time.time() - start) * 1000 # ms
    print(f"⏱️ Chargement [{desc}] : {elapsed:.2f} ms")
    return elapsed

def main():
    print("=" * 60)
    print("📊 BENCHMARK DE PERFORMANCE DE CHARGEMENT")
    print("=" * 60)
    
    # Test 1 : Ancien format (Excel + GeoJSON original)
    if os.path.exists(EXCEL_PATH) and os.path.exists(GEO_ORIGINAL):
        t_old = test_load(EXCEL_PATH, GEO_ORIGINAL, "Excel + GeoJSON original (Avant)")
    else:
        t_old = None
        print("⚠️ Anciens fichiers non trouvés pour test.")
        
    # Test 2 : Nouveau format (Parquet + GeoJSON simplifié)
    if os.path.exists(PARQUET_PATH) and os.path.exists(GEO_SIMPLIFIED):
        t_new = test_load(PARQUET_PATH, GEO_SIMPLIFIED, "Parquet + GeoJSON simplifié (Après)")
    else:
        t_new = None
        print("⚠️ Nouveaux fichiers non trouvés pour test.")
        
    if t_old and t_new:
        gain = (t_old - t_new) / t_old * 100
        factor = t_old / t_new
        print("-" * 60)
        print(f"🚀 Gain de performance : +{gain:.1f}%")
        print(f"⚡ Le chargement est {factor:.1f}x plus rapide !")
    print("=" * 60)

if __name__ == "__main__":
    main()
