
from dash import dcc, html, Input, Output, State, callback, ALL
import dash
import pandas as pd
import os
from ..data import load_data, PROJECT_ROOT

# Load data
gdf_merged, variable_dict, category_dict, _ = load_data()

# Group variables by category
def get_vars_by_category(target_cat):
    """Return list of variables for a given category."""
    result = []
    for var_code, label in variable_dict.items():
        cat = str(category_dict.get(var_code, 'Autre')).lower()
        if cat == target_cat.lower():
            result.append({'code': var_code, 'label': label})
    return sorted(result, key=lambda x: x['label'])

def make_var_table(vars_list):
    """Create a styled table for a list of variables."""
    if not vars_list:
        return html.P("Aucune variable dans cette catégorie.", style={'color': '#7f8c8d', 'fontStyle': 'italic'})
    
    rows = []
    for item in vars_list:
        rows.append(
            html.Div(className='row', style={
                'display': 'flex', 'padding': '10px 15px', 'borderBottom': '1px solid #eee',
                'alignItems': 'center', 'transition': 'background-color 0.2s'
            }, children=[
                html.Div(item['label'], style={'flex': '1', 'fontWeight': '500'}),
                html.Div(item['code'], style={'width': '200px', 'fontSize': '0.85rem', 'color': '#7f8c8d', 'fontFamily': 'monospace'}),
            ])
        )
    
    return html.Div(children=[
        html.Div(className='row', style={
            'display': 'flex', 'padding': '10px 15px', 'fontWeight': 'bold',
            'borderBottom': '2px solid #3498db', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px 5px 0 0'
        }, children=[
            html.Div("Variable", style={'flex': '1'}),
            html.Div("Code", style={'width': '200px'}),
        ]),
        *rows
    ])

socioeco_vars = get_vars_by_category('Socioéco')
offre_vars = get_vars_by_category('Offre de soins')
env_vars = get_vars_by_category('Environnement')
sante_vars = get_vars_by_category('Santé')

layout = html.Div(className='page-container', style={'padding': '20px'}, children=[
    html.H1("Méthodologie & Variables"),
    html.P("Explorez les variables disponibles organisées par thématique. Ces variables sont utilisées dans les filtres de la Carte et du Radar.", 
           style={'color': '#555', 'marginBottom': '25px'}),
    
    dcc.Tabs(id='methodo-tabs', value='socioeco', children=[
        dcc.Tab(label=f'Socio-Éco ({len(socioeco_vars)})', value='socioeco', 
                style={'fontWeight': '500'}, selected_style={'fontWeight': 'bold', 'borderTop': '3px solid #3498db'}),
        dcc.Tab(label=f'Offre de Soins ({len(offre_vars)})', value='offre',
                style={'fontWeight': '500'}, selected_style={'fontWeight': 'bold', 'borderTop': '3px solid #2ecc71'}),
        dcc.Tab(label=f'Environnement ({len(env_vars)})', value='env',
                style={'fontWeight': '500'}, selected_style={'fontWeight': 'bold', 'borderTop': '3px solid #e67e22'}),
        dcc.Tab(label=f'Santé ({len(sante_vars)})', value='sante',
                style={'fontWeight': '500'}, selected_style={'fontWeight': 'bold', 'borderTop': '3px solid #e74c3c'}),
    ]),
    
    html.Div(id='methodo-tab-content', style={'marginTop': '15px'})
])


@callback(
    Output('methodo-tab-content', 'children'),
    Input('methodo-tabs', 'value')
)
def render_tab(tab):
    if tab == 'socioeco':
        return html.Div([
            html.H3("🏠 Variables Socio-Économiques", style={'color': '#2c3e50'}),
            html.P("Indicateurs relatifs à la population, l'emploi, les revenus, le logement et l'éducation.", style={'color': '#555'}),
            make_var_table(socioeco_vars)
        ])
    elif tab == 'offre':
        return html.Div([
            html.H3("🏥 Variables Offre de Soins", style={'color': '#2c3e50'}),
            html.P("Accessibilité et densité des professionnels de santé sur le territoire.", style={'color': '#555'}),
            make_var_table(offre_vars)
        ])
    elif tab == 'env':
        return html.Div([
            html.H3("🌿 Variables Environnement", style={'color': '#2c3e50'}),
            html.P("Indicateurs liés à la qualité de l'environnement et aux risques environnementaux.", style={'color': '#555'}),
            make_var_table(env_vars)
        ])
    elif tab == 'sante':
        return html.Div([
            html.H3("❤️ Variables de Santé", style={'color': '#2c3e50'}),
            html.P("Indicateurs d'incidence, mortalité et prévalence des pathologies cardiovasculaires.", style={'color': '#555'}),
            make_var_table(sante_vars)
        ])
