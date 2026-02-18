
import dash
from dash import dcc, html, Input, Output
import os

# Import layouts from pages
from src.pages import home, map, radar, methodology, clustering
from src.data import load_data

# Load data for filter options
gdf_merged, variable_dict, category_dict, _ = load_data()

def get_options(target_cats):
    options = []
    for col, label in variable_dict.items():
        if col not in gdf_merged.columns: continue
        cat = str(category_dict.get(col, "")).lower()
        if cat in target_cats:
            options.append({'label': label, 'value': col})
    return sorted(options, key=lambda x: x['label'])

social_options = get_options(['socioéco'])
offre_options = get_options(['offre de soins'])
env_options = get_options(['environnement'])

import pandas as pd

epci_radar_options = [{'label': n, 'value': c} for n, c in zip(gdf_merged['nom_EPCI'], gdf_merged['EPCI_CODE']) if pd.notnull(n)]

# --- App Setup ---
external_stylesheets = ['https://use.fontawesome.com/releases/v5.15.4/css/all.css']
app = dash.Dash(__name__, title="SeniAURA - Accueil", suppress_callback_exceptions=True, external_stylesheets=external_stylesheets)
server = app.server

# --- Shared Filters (always in DOM) ---
shared_filters = html.Div(id='sidebar-filters', style={'display': 'none'}, children=[
    html.Hr(style={'borderColor': 'rgba(255,255,255,0.2)', 'margin': '15px 10px'}),
    html.H4("Filtres partagés", style={'color': 'white', 'padding': '0 15px', 'fontSize': '0.9rem', 'textTransform': 'uppercase', 'letterSpacing': '1px'}),

    # EPCI Select (by code, for Radar)
    html.Div(style={'padding': '5px 15px'}, children=[
        html.Label("🎯 EPCI (Multi)", style={'color': '#bdc3c7', 'fontSize': '0.8rem'}),
        dcc.Dropdown(
            id='sidebar-epci-radar',
            options=epci_radar_options,
            placeholder="Choisir des EPCI...",
            clearable=True,
            multi=True,
            style={'marginBottom': '10px'}
        ),
    ]),

    # Variable Filters
    html.Div(style={'padding': '5px 15px'}, children=[
        html.Label("Socio-Eco", style={'color': '#bdc3c7', 'fontSize': '0.8rem'}),
        dcc.Dropdown(id='sidebar-filter-social', options=social_options, multi=True, placeholder="Sélectionner..."),
    ]),
    html.Div(style={'padding': '5px 15px', 'marginTop': '5px'}, children=[
        html.Label("Offre de Soins", style={'color': '#bdc3c7', 'fontSize': '0.8rem'}),
        dcc.Dropdown(id='sidebar-filter-offre', options=offre_options, multi=True, placeholder="Sélectionner..."),
    ]),
    html.Div(style={'padding': '5px 15px', 'marginTop': '5px'}, children=[
        html.Label("Environnement", style={'color': '#bdc3c7', 'fontSize': '0.8rem'}),
        dcc.Dropdown(id='sidebar-filter-env', options=env_options, multi=True, placeholder="Sélectionner..."),
    ]),
])

# --- Main Shell ---
sidebar = html.Div(className='sidebar', children=[
    html.H2("SeniAURA", style={'color': 'white', 'textAlign': 'center', 'marginBottom': '30px', 'cursor': 'pointer'}),
    
    html.Nav(className='nav-menu', children=[
        dcc.Link(href='/', className='nav-link', children=[
            html.I(className="fas fa-home", style={'marginRight': '10px'}), "Accueil"
        ]),
        dcc.Link(href='/carte', className='nav-link', children=[
            html.I(className="fas fa-map-marked-alt", style={'marginRight': '10px'}), "Carte Interactive"
        ]),
        dcc.Link(href='/radar', className='nav-link', children=[
            html.I(className="fas fa-chart-line", style={'marginRight': '10px'}), "Radar Comparatif"
        ]),
        dcc.Link(href='/methodologie', className='nav-link', children=[
            html.I(className="fas fa-book", style={'marginRight': '10px'}), "Méthodologie"
        ]),
        dcc.Link(href='/clustering', className='nav-link', children=[
            html.I(className="fas fa-project-diagram", style={'marginRight': '10px'}), "Clustering"
        ]),
    ]),

    shared_filters,

    html.Div(className='sidebar-footer', style={'marginTop': 'auto', 'textAlign': 'center', 'color': '#bdc3c7', 'fontSize': '0.8rem'}, children=[
        html.P("HEC Capstone Project"),
        html.P("v2.1 - 2026")
    ])
])


app.layout = html.Div(className='app-container', children=[
    dcc.Location(id='url', refresh=False),
    sidebar,
    html.Div(id='page-content', className='content', style={'padding': '20px', 'height': '100vh', 'overflow': 'auto'})
])

# --- Routing Callback ---
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/carte':
        return map.layout
    elif pathname == '/radar':
        return radar.layout
    elif pathname == '/methodologie':
        return methodology.layout
    elif pathname == '/clustering':
        return clustering.layout
    else:
        return home.layout

# --- Show/Hide Filters based on page ---
@app.callback(Output('sidebar-filters', 'style'), Input('url', 'pathname'))
def toggle_filters(pathname):
    if pathname in ['/carte', '/radar']:
        return {'display': 'block'}
    return {'display': 'none'}

if __name__ == '__main__':
    app.run(debug=True, port=8050)
