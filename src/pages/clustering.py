from dash import dcc, html, Input, Output, State, callback
import dash
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from ..data import load_data

gdf_merged, variable_dict, category_dict, _, _, _, _ = load_data()

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
layout = dmc.Container(
    fluid=True,
    p="xl",
    children=[
        dmc.Title("🔬 Clustering Territorial", order=1, mb="xs"),
        dmc.Text("Segmentation des territoires par apprentissage non supervisé", c="dimmed", size="lg", mb="xl"),

        # Explanatory card
        dmc.Paper(
            withBorder=True, shadow="sm", p="lg", radius="md", mb="xl",
            style={"borderLeft": "4px solid #3498db"},
            children=[
                dmc.Title("Qu'est-ce que le clustering ?", order=2, mb="sm"),
                dmc.Text("Le clustering regroupe automatiquement des territoires similaires selon leurs caractéristiques. Les EPCI d'un même cluster partagent un profil comparable (socio-éco, offre de soins, environnement). Cela permet d'identifier des typologies territoriales et d'adapter les politiques de prévention.", mb="sm"),
                dmc.List(spacing="xs", children=[
                    dmc.ListItem(html.Span([html.B("K-Means"), " : partitionne les données en K groupes en minimisant la variance intra-cluster."])),
                    dmc.ListItem(html.Span([html.B("Normalisation"), " : les variables sont standardisées (z-score) pour être comparables."])),
                    dmc.ListItem(html.Span([html.B("Profils"), " : le radar ci-dessous montre les caractéristiques moyennes de chaque cluster."]))
                ])
            ]
        ),

        # Interactive Tool Card
        dmc.Paper(
            withBorder=True, shadow="sm", p="lg", radius="md", mb="xl",
            style={"borderLeft": "4px solid #2ecc71"},
            children=[
                dmc.Title("🛠️ Outil de Clustering Interactif", order=2, mb="lg"),
                
                dmc.Grid(gutter="md", mb="lg", children=[
                    dmc.GridCol(span={"base": 12, "md": 4}, children=[
                        dmc.MultiSelect(
                            id='cluster-vars-social', label="Socio-Éco", data=social_options, 
                            placeholder="Variables socio-éco...", searchable=True, clearable=True
                        )
                    ]),
                    dmc.GridCol(span={"base": 12, "md": 4}, children=[
                        dmc.MultiSelect(
                            id='cluster-vars-offre', label="Offre de Soins", data=offre_options, 
                            placeholder="Variables offre...", searchable=True, clearable=True
                        )
                    ]),
                    dmc.GridCol(span={"base": 12, "md": 4}, children=[
                        dmc.MultiSelect(
                            id='cluster-vars-env', label="Environnement", data=env_options, 
                            placeholder="Variables env...", searchable=True, clearable=True
                        )
                    ])
                ]),
                
                dmc.Group(align="flex-end", gap="xl", mb="sm", children=[
                    dmc.Box(w=300, children=[
                        dmc.Text("Nombre de clusters (K)", fw=600, size="sm", mb="xs"),
                        dmc.Slider(
                            id='cluster-k', min=2, max=8, step=1, value=4,
                            marks=[{"value": i, "label": str(i)} for i in range(2, 9)]
                        )
                    ]),
                    dmc.Button(
                        "🚀 Lancer le clustering", id='cluster-run-btn', n_clicks=0,
                        color="green", size="md"
                    )
                ]),
                
                dmc.Text(id='cluster-status', c="dimmed", size="sm", mt="md")
            ]
        ),

        # Results Section
        dmc.Box(id='cluster-results', children=[
            dmc.Paper(withBorder=True, shadow="sm", p="lg", radius="md", mb="xl", children=[
                dmc.Title("🗺️ Carte des Clusters", order=3, mb="xs"),
                dmc.Text("Chaque couleur représente un cluster. Les EPCI de même couleur partagent un profil similaire.", c="dimmed", size="sm", mb="md"),
                dcc.Graph(id='cluster-map', style={'height': '500px'})
            ]),

            dmc.Paper(withBorder=True, shadow="sm", p="lg", radius="md", mb="xl", children=[
                dmc.Title("📊 Profils des Clusters", order=3, mb="xs"),
                dmc.Text("Chaque axe du radar représente la valeur moyenne normalisée (0-1) d'une variable pour chaque cluster.", c="dimmed", size="sm", mb="md"),
                dcc.Graph(id='cluster-radar', style={'height': '500px'}),
                html.Div(id='cluster-radar-guide', style={'marginTop': '20px'})
            ]),

            dmc.Paper(withBorder=True, shadow="sm", p="lg", radius="md", mb="xl", children=[
                dmc.Title("🔍 Détail par Variable (normalisé)", order=3, mb="xs"),
                dmc.Text("Valeurs moyennes normalisées (0-1) de chaque variable par cluster. Toutes les variables sont sur la même échelle.", c="dimmed", size="sm", mb="md"),
                dcc.Graph(id='cluster-bars', style={'height': '400px'}),
                html.Div(id='cluster-bars-guide', style={'marginTop': '20px'})
            ]),

            dmc.Paper(withBorder=True, shadow="sm", p="lg", radius="md", mb="xl", children=[
                dmc.Title("📋 Composition des Clusters", order=3, mb="xs"),
                dmc.Text("Liste des EPCI dans chaque cluster.", c="dimmed", size="sm", mb="md"),
                html.Div(id='cluster-epci-list')
            ])
        ])
    ]
)

# --- CALLBACKS ---

CLUSTER_COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']

@callback(
    [Output('cluster-map', 'figure'),
     Output('cluster-radar', 'figure'),
     Output('cluster-bars', 'figure'),
     Output('cluster-epci-list', 'children'),
     Output('cluster-status', 'children'),
     Output('cluster-radar-guide', 'children'),
     Output('cluster-bars-guide', 'children')],
    Input('cluster-run-btn', 'n_clicks'),
    [State('cluster-vars-social', 'value'),
     State('cluster-vars-offre', 'value'),
     State('cluster-vars-env', 'value'),
     State('cluster-k', 'value')],
    prevent_initial_call=True
)
def run_clustering(n_clicks, social, offre, env, k):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, "", None, None
    
    selected = (social or []) + (offre or []) + (env or [])
    valid_vars = [v for v in selected if v in gdf_merged.columns]
    
    if len(valid_vars) < 2:
        empty = go.Figure()
        err_msg = dmc.Alert("⚠️ Sélectionnez au moins 2 variables.", color="red", title="Attention")
        return empty, empty, empty, err_msg, "⚠️ Pas assez de variables", None, None
    
    df = gdf_merged[['nom_EPCI'] + valid_vars].dropna().copy()
    
    if len(df) < k:
        empty = go.Figure()
        err_msg = dmc.Alert("⚠️ Pas assez de données.", color="red")
        return empty, empty, empty, err_msg, "⚠️ Pas assez de données", None, None
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[valid_vars])
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)
    
    var_labels = [variable_dict.get(v, v) for v in valid_vars]
    
    mins = df[valid_vars].min()
    maxs = df[valid_vars].max()
    ranges = maxs - mins
    ranges[ranges == 0] = 1
    
    # === MAP ===
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
    
    # === RADAR ===
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
    
    # === BARS ===
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
            dmc.Paper(
                withBorder=True, shadow="xs", p="md", mb="md", radius="md",
                style={'borderTop': f'4px solid {CLUSTER_COLORS[c % len(CLUSTER_COLORS)]}'},
                children=[
                    dmc.Title(f"Cluster {c+1} — {len(epci_names)} EPCI", order=4, c=CLUSTER_COLORS[c % len(CLUSTER_COLORS)], mb="sm"),
                    dmc.Group(gap="xs", children=[
                        dmc.Badge(name, variant="outline", color="gray", radius="sm") for name in epci_names
                    ])
                ]
            )
        )
    
    status = f"✅ Clustering terminé : {k} clusters sur {len(df)} EPCI avec {len(valid_vars)} variables"
    
    # === GUIDES DE LECTURE ===
    # Radar guide
    radar_guide = dmc.Alert(
        title="💡 Lecture du Radar", color="indigo", radius="sm", variant="light",
        children=dmc.Text([
            "Ce graphique radar superpose les profils moyens des différents clusters. Observez la forme de chaque ligne : ",
            "les sommets étirés vers l'extérieur indiquent une valeur moyenne élevée pour ce cluster sur la variable correspondante."
        ], size="sm")
    )
    
    # Bars guide
    bars_guide = dmc.Alert(
        title="💡 Lecture des Barres", color="indigo", radius="sm", variant="light",
        children=dmc.Text([
            "Ce graphique permet de comparer l'ensemble des clusters, variable par variable. ",
            "Il est particulièrement utile pour identifier la / les variable(s) qui différencient le plus fortement un cluster des autres."
        ], size="sm")
    )
    
    return map_fig, radar_fig, bar_fig, cluster_cards, status, radar_guide, bars_guide
