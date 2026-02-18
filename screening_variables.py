
import pandas as pd
from scipy import stats
from src.data import load_data
import sys

def calculate_regression(df, x_col, y_col):
    """Calculates linear regression stats."""
    # Drop NaNs for the pair AND nom_EPCI (to match dashboard logic)
    # The dashboard uses: df_c = gdf_merged[[x, y, 'nom_EPCI']].dropna()
    cols_to_check = [x_col, y_col, 'nom_EPCI']
    # Check if nom_EPCI logic applies
    if 'nom_EPCI' in df.columns:
         sub_df = df[cols_to_check].dropna()
    else:
         sub_df = df[[x_col, y_col]].dropna()

    if len(sub_df) < 3:
        return None
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(sub_df[x_col], sub_df[y_col])
    return {
        'x': x_col,
        'y': y_col,
        'slope': slope,
        'r2': r_value**2,
        'p_value': p_value,
        'n': len(sub_df)
    }

def main():
    print("Chargement des données...")
    try:
        gdf, var_dict = load_data()
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        return

    # Définition des groupes de variables
    # Indicateurs de Santé (Y)
    health_indicators = [
        'INCI_AVC', 'INCI_CardIsch', 'INCI_InsuCard',
        'MORT_AVC', 'MORT_CardIsch', 'MORT_InsuCard',
        # 'PREV_AVC', 'PREV_CardIsch', # Ajoutés si présents
        'Taux_CNR'
    ]
    # Filtrer pour ne garder que ceux présents dans le DF
    health_indicators = [col for col in health_indicators if col in gdf.columns]

    # Déterminants (X)
    determinants = [
        'FDep_2021',
        'Revenu médian',
        'Taux de chomeurs',
        'Taux d\'ouvriers',
        'Taux de bacheliers',
        'APL-med_general_2023',
        'APL-infirmieres_2023',
        'POP_2021'
    ]
    determinants = [col for col in determinants if col in gdf.columns]

    print(f"Indicateurs de Santé trouvés ({len(health_indicators)}) : {health_indicators}")
    print(f"Déterminants trouvés ({len(determinants)}) : {determinants}")
    print("-" * 50)

    results = []

    print("Calcul des régressions...")
    for y_col in health_indicators:
        for x_col in determinants:
            stats_res = calculate_regression(gdf, x_col, y_col)
            if stats_res:
                results.append(stats_res)
    
    # Tri par R² décroissant (ou p-value croissante)
    # Ici on privilégie R² pour la "force" du lien, mais on peut vérifier la p-value
    results_sorted = sorted(results, key=lambda k: k['r2'], reverse=True)

    print(f"\nTop 20 des corrélations les plus significatives (classées par R²) :\n")
    print(f"{'Déterminant (X)':<30} | {'Indicateur Santé (Y)':<30} | {'R²':<10} | {'P-value':<10} | {'Pente':<10}")
    print("-" * 100)

    for res in results_sorted[:20]:
        x_name = var_dict.get(res['x'], res['x'])[:28]
        y_name = var_dict.get(res['y'], res['y'])[:28]
        r2_str = f"{res['r2']:.4f}"
        p_str = f"{res['p_value']:.4e}"
        slope_str = f"{res['slope']:.4f}"
        
        print(f"{x_name:<30} | {y_name:<30} | {r2_str:<10} | {p_str:<10} | {slope_str:<10}")

    # Sauvegarde CSV optionnelle
    df_res = pd.DataFrame(results_sorted)
    output_file = "resultats_screening.csv"
    # Mapping noms lisibles
    df_res['x_label'] = df_res['x'].map(lambda x: var_dict.get(x, x))
    df_res['y_label'] = df_res['y'].map(lambda y: var_dict.get(y, y))
    
    df_res.to_csv(output_file, index=False)
    print(f"\nRésultats complets sauvegardés dans '{output_file}'")

if __name__ == "__main__":
    main()
