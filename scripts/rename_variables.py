import pandas as pd
import re

# Load the dictionary
csv_path = '/home/raphael/Documents/L3/HEC capstone/projet_github/SeniAura-main/data/dictionnaire_variables.csv'
df = pd.read_csv(csv_path)

def generate_short_name(row):
    code = str(row['Variable'])
    desc = str(row['Description'])
    
    # Custom Mappings based on Logic
    
    # Santé (INCI, MORT, PREV)
    if code.startswith('INCI_'):
        suffix = code.replace('INCI_', '')
        mapping = {'AVC': 'AVC', 'CardIsch': 'Cardio Isch.', 'InsuCard': 'Insu. Card.'}
        return f"Incidence {mapping.get(suffix, suffix)}"
    if code.startswith('MORT_'):
        suffix = code.replace('MORT_', '')
        mapping = {'AVC': 'AVC', 'CardIsch': 'Cardio Isch.', 'InsuCard': 'Insu. Card.'}
        return f"Mortalité {mapping.get(suffix, suffix)}"
    if code.startswith('PREV_'):
        suffix = code.replace('PREV_', '')
        mapping = {'AVC': 'AVC', 'CardIsch': 'Cardio Isch.', 'InsuCard': 'Insu. Card.'}
        return f"Prévalence {mapping.get(suffix, suffix)}"
        
    # PCS
    if code.startswith('PCS_'):
        if '1 :' in desc: return "Agriculteurs"
        if '2 :' in desc: return "Artisans/Comm."
        if '3 :' in desc: return "Cadres"
        if '4 :' in desc: return "Prof. Interm."
        if '5 :' in desc: return "Employés"
        if '6 :' in desc: return "Ouvriers"
        if 'Total' in desc: return "TOTAL Actifs"
        
    # Diplômes
    if code.startswith('DIPLOME_'):
        if 'Aucun' in desc: return "Sans Diplôme"
        if 'BEPC' in desc: return "Brevet/Collège"
        if 'CAP' in desc: return "CAP/BEP"
        if 'Baccalauréat' in desc and '350T351' in code: return "Baccalauréat"
        if 'supérieur de cycle court' in desc: return "Supérieur Court (Bac+2)"
        if 'Licence' in desc: return "Licence (Bac+3/4)"
        if '200_RP' in desc: return "Brevet" # Correction for some rows
        if code == 'DIPLOME__T': return "Master et + (Bac+5)" # Fix
        if '700_RP' in desc: return "Master et +" # Fix check
        
    # Environnement (AIR, BRUIT, etc.)
    if code.startswith('AIR'):
        if 'PM2,5' in desc and 'Moyenne' in desc: return "Exp. PM2.5 (Moy)"
        if 'PM2,5' in desc and 'supérieurs' in desc: return "Pop. Exposée PM2.5"
        if 'NO2' in desc and 'Moyenne' in desc: return "Exp. NO2 (Moy)"
        if 'NO2' in desc and 'supérieurs' in desc: return "Pop. Exposée NO2"
        if 'décès' in desc: return "Mortalité Pollution"
        
    # Offre de soins (APL, Effectifs)
    if 'APL' in code or 'APL' in desc:
        year = re.search(r'20\d\d', code)
        y_str = f" ({year.group(0)})" if year else ""
        if 'general' in code: return f"APL Généralistes{y_str}"
        if 'kine' in code: return f"APL Kinés{y_str}"
        if 'infirm' in code: return f"APL Infirmiers{y_str}"
        if 'dent' in code: return f"APL Dentistes{y_str}"
        if 'sages_femmes' in code: return f"APL Sages-Femmes{y_str}"
        
    if 'Pharmaciens' in code:
        year = re.search(r'20\d\d', code)
        return f"Pharmaciens ({year.group(0)})" if year else "Pharmaciens"
        
    if 'FDep' in code: return "Indice Défaveur (FDep)"
    if 'Precarite' in code and 'Indice' in code: return "Précarité (Score)"
    if 'MED_SL' in code: return "Niveau de Vie Médian"
    if 'IR_D9' in code: return "Inégalités (D9/D1)"
    if 'PR_MD_60' in code: return "Tx Pauvreté (60%)"
    if 'chomeurs' in desc or 'chomeurs' in code: return "Tx Chômage"
    
    # Fallback to description truncated if too long, or code
    if len(desc) < 30: return desc
    return code

# Apply
df['Nom_Court'] = df.apply(generate_short_name, axis=1)

# Save
df.to_csv(csv_path, index=False)
print("Updated dictionnaire_variables.csv with Nom_Court")
