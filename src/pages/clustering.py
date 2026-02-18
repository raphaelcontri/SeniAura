
from dash import dcc, html, Input, Output, State, callback
import dash
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from ..data import load_data

gdf_merged, variable_dict, category_dict, _ = load_data()

# Prepare options by category
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

# --- LAYOUT ---
layout = html.Div(className='page-container', style={'padding': '30px', 'overflowY': 'auto', 'height': '100vh'}, children=[
    html.H1("🔬 Clustering Territorial", style={'marginBottom': '5px'}),
    html.P("Segmentation des territoires par apprentissage non supervisé", 
           style={'color': '#7f8c8d', 'fontSize': '1.1rem', 'marginBottom': '25px'}),

    # Explanatory cards
    html.Div(className='card', style={'padding': '25px', 'marginBottom': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.08)', 'borderLeft': '4px solid #3498db'}, children=[
        html.H2("Qu'est-ce que le clustering ?", style={'color': '#2c3e50', 'marginTop': 0}),
        html.P("Le clustering regroupe automatiquement des territoires similaires selon leurs caractéristiques. "
               "Les EPCI d'un même cluster partagent un profil comparable (socio-éco, offre de soins, environnement). "
               "Cela permet d'identifier des typologies territoriales et d'adapter les politiques de prévention."),
        html.Ul(style={'lineHeight': '1.8'}, children=[
            html.Li([html.B("K-Means"), " : partitionne les données en K groupes en minimisant la variance intra-cluster."]),
            html.Li([html.B("Normalisation"), " : les variables sont standardisées (z-score) pour être comparables."]),
            html.Li([html.B("Profils"), " : le radar ci-dessous montre les caractéristiques moyennes de chaque cluster."]),
        ])
    ]),

    # Interactive Tool
    html.Div(className='card', style={'padding': '25px', 'marginBottom': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.08)', 'borderLeft': '4px solid #2ecc71'}, children=[
        html.H2("🛠️ Outil de Clustering Interactif", style={'color': '#2c3e50', 'marginTop': 0}),
        
        # Variable selection
        html.Div(style={'display': 'flex', 'gap': '15px', 'marginBottom': '20px', 'flexWrap': 'wrap'}, children=[
            html.Div(style={'flex': 1, 'minWidth': '200px'}, children=[
                html.Label("Socio-Éco", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                dcc.Dropdown(id='cluster-vars-social', options=social_options, multi=True, placeholder="Variables socio-éco...")
            ]),
            html.Div(style={'flex': 1, 'minWidth': '200px'}, children=[
                html.Label("Offre de Soins", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                dcc.Dropdown(id='cluster-vars-offre', options=offre_options, multi=True, placeholder="Variables offre...")
            ]),
            html.Div(style={'flex': 1, 'minWidth': '200px'}, children=[
                html.Label("Environnement", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                dcc.Dropdown(id='cluster-vars-env', options=env_options, multi=True, placeholder="Variables env...")
            ]),
        ]),
        
        # K selection + Run button
        html.Div(style={'display': 'flex', 'gap': '20px', 'alignItems': 'flex-end', 'marginBottom': '15px'}, children=[
            html.Div(style={'width': '200px'}, children=[
                html.Label("Nombre de clusters (K)", style={'fontWeight': 'bold', 'fontSize': '0.9rem'}),
                dcc.Slider(id='cluster-k', min=2, max=8, step=1, value=4,
                          marks={i: str(i) for i in range(2, 9)},
                          tooltip={"always_visible": False})
            ]),
            html.Button("🚀 Lancer le clustering", id='cluster-run-btn', n_clicks=0,
                       style={'padding': '10px 25px', 'backgroundColor': '#2ecc71', 'color': 'white', 
                              'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer',
                              'fontWeight': 'bold', 'fontSize': '1rem', 'height': '42px'}),
        ]),
        
        html.Div(id='cluster-status', style={'color': '#7f8c8d', 'fontSize': '0.9rem', 'marginBottom': '10px'})
    ]),

    # Results Section
    html.Div(id='cluster-results', children=[
        # Cluster Map
        html.Div(className='card', style={'padding': '20px', 'marginBottom': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.08)'}, children=[
            html.H3("🗺️ Carte des Clusters", style={'color': '#2c3e50', 'marginTop': 0}),
            html.P("Chaque couleur représente un cluster. Les EPCI de même couleur partagent un profil similaire.",
                   style={'color': '#555', 'fontSize': '0.9rem'}),
            dcc.Graph(id='cluster-map', style={'height': '500px'})
        ]),

        # Cluster Profiles (Radar)
        html.Div(className='card', style={'padding': '20px', 'marginBottom': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.08)'}, children=[
            html.H3("📊 Profils des Clusters", style={'color': '#2c3e50', 'marginTop': 0}),
            html.P("Chaque axe du radar représente la valeur moyenne normalisée (0-1) d'une variable pour chaque cluster.",
                   style={'color': '#555', 'fontSize': '0.9rem'}),
            dcc.Graph(id='cluster-radar', style={'height': '500px'})
        ]),

        # Cluster Bar Chart (normalized)
        html.Div(className='card', style={'padding': '20px', 'marginBottom': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.08)'}, children=[
            html.H3("🔍 Détail par Variable (normalisé)", style={'color': '#2c3e50', 'marginTop': 0}),
            html.P("Valeurs moyennes normalisées (0-1) de chaque variable par cluster. Toutes les variables sont sur la même échelle.",
                   style={'color': '#555', 'fontSize': '0.9rem'}),
            dcc.Graph(id='cluster-bars', style={'height': '400px'})
        ]),

        # EPCI list per cluster
        html.Div(className='card', style={'padding': '20px', 'marginBottom': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.08)'}, children=[
            html.H3("📋 Composition des Clusters", style={'color': '#2c3e50', 'marginTop': 0}),
            html.P("Liste des EPCI dans chaque cluster.", style={'color': '#555', 'fontSize': '0.9rem'}),
            html.Div(id='cluster-epci-list')
        ]),
    ])
])


# --- CALLBACKS ---

CLUSTER_COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']

@callback(
    [Output('cluster-map', 'figure'),
     Output('cluster-radar', 'figure'),
     Output('cluster-bars', 'figure'),
     Output('cluster-epci-list', 'children'),
     Output('cluster-status', 'children')],
    Input('cluster-run-btn', 'n_clicks'),
    [State('cluster-vars-social', 'value'),
     State('cluster-vars-offre', 'value'),
     State('cluster-vars-env', 'value'),
     State('cluster-k', 'value')],
    prevent_initial_call=True
)
def run_clustering(n_clicks, social, offre, env, k):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, ""
    
    selected = (social or []) + (offre or []) + (env or [])
    valid_vars = [v for v in selected if v in gdf_merged.columns]
    
    if len(valid_vars) < 2:
        empty = go.Figure()
        return empty, empty, empty, html.P("⚠️ Sélectionnez au moins 2 variables.", style={'color': '#e74c3c'}), "⚠️ Pas assez de variables"
    
    # Prepare data — keep index aligned with gdf_merged for the map
    df = gdf_merged[['nom_EPCI'] + valid_vars].dropna().copy()
    
    if len(df) < k:
        empty = go.Figure()
        return empty, empty, empty, html.P("⚠️ Pas assez de données."), "⚠️ Pas assez de données"
    
    # Standardize for KMeans
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[valid_vars])
    
    # Cluster
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)
    
    # Labels
    var_labels = [variable_dict.get(v, v) for v in valid_vars]
    
    # Min-max normalization for display (shared across radar + bars)
    mins = df[valid_vars].min()
    maxs = df[valid_vars].max()
    ranges = maxs - mins
    ranges[ranges == 0] = 1
    
    # === MAP: Choropleth colored by cluster ===
    map_fig = go.Figure()
    gdf_with_clusters = gdf_merged.copy()
    gdf_with_clusters['cluster'] = np.nan
    gdf_with_clusters.loc[df.index, 'cluster'] = df['cluster']
    
    for c in range(k):
        subset = gdf_with_clusters[gdf_with_clusters['cluster'] == c]
        if not subset.empty:
            map_fig.add_trace(go.Choropleth(
                geojson=subset.geometry.__geo_interface__, locations=subset.index,
                z=[c]*len(subset),
                colorscale=[[0, CLUSTER_COLORS[c % len(CLUSTER_COLORS)]], [1, CLUSTER_COLORS[c % len(CLUSTER_COLORS)]]],
                showscale=False,
                marker_line_width=1, marker_line_color='white',
                text=subset['nom_EPCI'],
                name=f'Cluster {c+1}',
                hovertemplate="<b>%{text}</b><br>Cluster " + str(c+1) + "<extra></extra>"
            ))
    
    # Grey out EPCIs not in clustering (missing data)
    excluded = gdf_with_clusters[gdf_with_clusters['cluster'].isna()]
    if not excluded.empty:
        map_fig.add_trace(go.Choropleth(
            geojson=excluded.geometry.__geo_interface__, locations=excluded.index,
            z=[0]*len(excluded),
            colorscale=[[0, '#e0e0e0'], [1, '#e0e0e0']],
            showscale=False, marker_line_width=0.5, marker_line_color='#ccc',
            text=excluded['nom_EPCI'], name='Non classé',
            hovertemplate="<b>%{text}</b><br>Données manquantes<extra></extra>"
        ))
    
    map_fig.update_geos(fitbounds="locations", visible=False)
    map_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, dragmode=False,
                         legend=dict(orientation="h", yanchor="bottom", y=-0.05))
    
    # === RADAR: Normalized cluster profiles ===
    radar_fig = go.Figure()
    for c in range(k):
        cluster_data = df[df['cluster'] == c][valid_vars]
        norm_means = ((cluster_data.mean() - mins) / ranges).tolist()
        
        radar_fig.add_trace(go.Scatterpolar(
            r=norm_means,
            theta=var_labels,
            fill='toself',
            name=f'Cluster {c+1} ({len(cluster_data)} EPCI)',
            line_color=CLUSTER_COLORS[c % len(CLUSTER_COLORS)],
            opacity=0.7
        ))
    
    radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        title="Profils Normalisés des Clusters (0 = min régional, 1 = max régional)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=60, b=80)
    )
    
    # === BARS: Normalized means per cluster per variable ===
    bar_data = []
    for c in range(k):
        cluster_data = df[df['cluster'] == c][valid_vars]
        for vi, var in enumerate(valid_vars):
            norm_val = (cluster_data[var].mean() - mins[var]) / ranges[var]
            bar_data.append({
                'Cluster': f'Cluster {c+1}',
                'Variable': var_labels[vi],
                'Moyenne normalisée': round(norm_val, 3)
            })
    
    bar_df = pd.DataFrame(bar_data)
    bar_fig = px.bar(bar_df, x='Variable', y='Moyenne normalisée', color='Cluster', barmode='group',
                     color_discrete_sequence=CLUSTER_COLORS[:k])
    bar_fig.update_layout(
        title="Moyennes Normalisées par Cluster (0 = min, 1 = max)",
        xaxis_tickangle=-30,
        yaxis_range=[0, 1],
        margin=dict(t=60, b=100),
        legend=dict(orientation="h", yanchor="bottom", y=-0.35)
    )
    
    # === EPCI LIST per cluster ===
    cluster_cards = []
    for c in range(k):
        epci_names = sorted(df[df['cluster'] == c]['nom_EPCI'].tolist())
        cluster_cards.append(
            html.Div(style={
                'padding': '15px', 'marginBottom': '10px', 'borderRadius': '5px',
                'border': f'2px solid {CLUSTER_COLORS[c % len(CLUSTER_COLORS)]}',
                'backgroundColor': '#fafafa'
            }, children=[
                html.H4(f"Cluster {c+1} — {len(epci_names)} EPCI", 
                        style={'margin': '0 0 10px 0', 'color': CLUSTER_COLORS[c % len(CLUSTER_COLORS)]}),
                html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '5px'}, children=[
                    html.Span(name, style={
                        'padding': '3px 8px', 'backgroundColor': '#fff', 'borderRadius': '3px',
                        'fontSize': '0.8rem', 'border': '1px solid #ddd'
                    }) for name in epci_names
                ])
            ])
        )
    
    status = f"✅ Clustering terminé : {k} clusters sur {len(df)} EPCI avec {len(valid_vars)} variables"
    
    return map_fig, radar_fig, bar_fig, cluster_cards, status
