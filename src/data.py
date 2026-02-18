
import pandas as pd
import geopandas as gpd
import os
import numpy as np

# Paths
# Assumes this file is in src/, so we go up one level to dashboard interactif, then up/down to data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # dashboard interactif
PROJECT_ROOT = os.path.dirname(BASE_DIR) # projet_2

DATA_DIR_DASH = os.path.join(BASE_DIR, "data")
GEOJSON_PATH = os.path.join(DATA_DIR_DASH, "epci-ara.geojson")
# Using the path observed in app.py
# Using the path observed in app.py
DATASET_PATH = os.path.join(DATA_DIR_DASH, "FINAL-DATASET-epci-11.xlsx")
METADATA_PATH = os.path.join(PROJECT_ROOT, "data", "table_variables.csv")

def load_data():
    """
    Loads and merges the GeoJSON and Excel data.
    Returns:
        gdf_merged (GeoDataFrame): The merged data ready for visualization.
        variable_dict (dict): Dictionary mapping column names to human-readable labels.
        category_dict (dict): Dictionary mapping column names to their category.
    """

    # 1. Load GeoJSON
    if not os.path.exists(GEOJSON_PATH):
        raise FileNotFoundError(f"GeoJSON not found at {GEOJSON_PATH}")
    
    gdf_epci = gpd.read_file(GEOJSON_PATH)
    gdf_epci['EPCI_CODE'] = gdf_epci['EPCI_CODE'].astype(str)

    # 2. Load Excel Dataset
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
    
    df = pd.read_excel(DATASET_PATH) # engine='openpyxl' is default for xlsx
    df['CODE_EPCI'] = df['CODE_EPCI'].astype(str).str.replace('.0', '', regex=False)

    # 3. Load Metadata for Dictionary & Categories
    variable_dict = {}
    category_dict = {}
    sens_dict = {}
    
    # Path to the new CSV
    DICT_PATH = os.path.join(DATA_DIR_DASH, "dictionnaire_variables.csv")
    
    if os.path.exists(DICT_PATH):
        df_meta = pd.read_csv(DICT_PATH)
        # Expecting columns: Variable, Source, Catégorie, Description, Sens
        for _, row in df_meta.iterrows():
            var_code = str(row['Variable']).strip()
            cat = str(row['Catégorie']).strip()
            
            # Skip "autre" variables if requested? 
            # The USER said: "On peut mettre 'autre' pour que la variable n'aille nulle part et ne soit pas disponible dans les sélections"
            # So we do NOT add them to the dictionary if they are 'autre'.
            # BUT we might need them for internal logic (like Code EPCI).
            # Strategy: Add everything to internal DF, but filter variable_dict for dropdowns.
            # Here we are building variable_dict which feeds dropdowns.
            if cat.lower() == 'autre':
                continue
                
            # Prefer Nom_Court, then Description, then Code
            if 'Nom_Court' in row and pd.notna(row['Nom_Court']):
                label = str(row['Nom_Court']).strip()
            elif pd.notna(row['Description']):
                label = str(row['Description']).strip()
            else:
                label = var_code
            
            variable_dict[var_code] = label
            category_dict[var_code] = cat
            
            # Read Sens (default to -1 if missing or 0)
            try:
                s = int(row['Sens'])
                sens_dict[var_code] = s if s != 0 else -1
            except:
                sens_dict[var_code] = -1
            
    # Fallback/Overrides for critical variables if missing in CSV or strictly needed
    overrides = {
        'Taux_CNR': 'Incidence Globale CNR',
        'FDep_2021': 'Score de Précarité (FDep 2021)',
        'Indice_Precarite': 'Précarité (Score Global)',
        'Revenu médian': 'Revenu Médian (€)',
        'Taux de chomeurs': 'Taux de Chômage (%)',
        'POP_2021': 'Population Totale (2021)',
        'Degré de densité (3 postes)': 'Degré de Densité',
    }
    for k, v in overrides.items():
        if k not in variable_dict and k in df.columns:
             variable_dict[k] = v
             # Assign default category if missing
             if k not in category_dict:
                 category_dict[k] = 'autre' 
             # Default sens
             if k not in sens_dict:
                 sens_dict[k] = -1

    # 4. Processing
    # Ensure numeric for known plotting variables
    for col in df.columns:
        if col in variable_dict:
            # Specific fix for Ratio D9/D1 often misinterpreted as Date by Excel
            if col == 'IR_D9_D1_SL':
                 df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                 df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calculate Taux_CNR if missing
    if 'Taux_CNR' not in df.columns:
         cols_to_sum = ['INCI_AVC', 'INCI_CardIsch', 'INCI_InsuCard']
         existing = [c for c in cols_to_sum if c in df.columns]
         if existing:
            df['Taux_CNR'] = df[existing].sum(axis=1)
            variable_dict['Taux_CNR'] = 'Incidence Globale CNR'
            category_dict['Taux_CNR'] = 'santé'
            sens_dict['Taux_CNR'] = -1
    
    # Merge
    gdf_merged = gdf_epci.merge(df, left_on='EPCI_CODE', right_on='CODE_EPCI', how='left')
    
    return gdf_merged, variable_dict, category_dict, sens_dict
