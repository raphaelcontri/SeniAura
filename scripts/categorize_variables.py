
import pandas as pd
import os

DATA_DIR = "/home/raphael/Documents/L3/HEC capstone/projet_github/SeniAura-main/data"
CSV_PATH = os.path.join(DATA_DIR, "dictionnaire_variables.csv")

def categorize(row):
    code = str(row['Variable'])
    desc = str(row['Description']).lower()
    
    # Existing explicit "autre" categories (like metadata) should likely stay "autre"
    # unless we want to recategorize everything. 
    # Let's prioritize functional categories.
    
    # 1. Santé
    if code.startswith(('INCI_', 'MORT_', 'PREV_', 'Taux_CNR')):
        return 'Santé'
        
    # 2. Environnement
    if code.startswith(('AIR', 'BRUIT', 'POLLEN', 'EAU', 'SOLS', 'INDUSTRIE', 'AGRI')):
        return 'Environnement'
    if code.startswith('ADT') and ('arbor' in desc or 'surface' in desc): # ADT01, ADT02
        return 'Environnement'
        
    # 3. Offre de soins
    if code.startswith(('Officines', 'Centres_Sante', 'Maisons_Sante', 'Pharmaciens', 'APL-')):
        return 'Offre de soins'
        
    # 4. Socioéco
    if code.startswith(('LOGEMENT', 'MED_', 'IR_', 'PR_', 'PCS_', 'DIPLOME_', 'Part de personnes isolées', 'Taux de chomeurs', 'FDep')):
        return 'Socioéco'
    if code.startswith('ADT'): # ADT03+ Sports
        return 'Socioéco' # Or create "Equipements"? Sticking to requested categories.
        
    # 5. Autre / Technical
    if code in ['CODE_EPCI', 'LIBEPCI', 'nom_EPCI', 'Nb_Communes', 'NATURE_EPCI', 'Département', 'Département_code', 'Population_Totale']:
        return 'autre'
    if code.startswith(('Degré', 'Libellé', 'Part population', 'Pop_', 'POP_')):
        return 'autre'

    # Fallback
    return 'Autre'

if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    # Apply categorization
    df['Catégorie'] = df.apply(categorize, axis=1)
    
    # Save back
    df.to_csv(CSV_PATH, index=False)
    print("Categories updated successfully.")
    print(df[['Variable', 'Catégorie']].head(20))
else:
    print(f"File not found: {CSV_PATH}")
