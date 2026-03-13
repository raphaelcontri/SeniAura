import dash
from dash import dcc, html, Input, Output, callback, ALL, State, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from ..data import load_data

# Load shared data
gdf_merged, variable_dict, category_dict, sens_dict, _, unit_dict, gdf_deps, _ = load_data()

# Ensure consistent projection and index for robust mapping
if gdf_merged.crs is None:
    gdf_merged.set_crs(epsg=4326, inplace=True)

gdf_4326 = gdf_merged.to_crs(epsg=4326)
# IMPORTANT: Create a clean ID for Plotly Choropleth mapping
gdf_4326['id'] = gdf_4326.index.astype(str)
geojson_data = gdf_4326.__geo_interface__

# Prepare departments
gdf_deps_4326 = gdf_deps.to_crs(epsg=4326).reset_index()
gdf_deps_4326['id'] = gdf_deps_4326.index.astype(str)
geojson_deps = gdf_deps_4326.__geo_interface__

MARKER_COLORS = ['#e03131', '#1971c2', '#2b8a3e', '#e67700', '#9c36b5', '#0b7285', '#5c940d', '#d9480f']

layout = dmc.Container(
    fluid=True,
    p="md",
    style={"display": "flex", "flexDirection": "column", "gap": "15px"},
    children=[
        # Page Header
        dmc.Group(
            justify="space-between",
            children=[
                dmc.Stack(gap=0, children=[
                    dmc.Title("Exploration du Territoire", order=2, c="#2c3e50"),
                    dmc.Text("Analysez la répartition spatiale et comparez les profils territoriaux.", size="sm", c="dimmed"),
                ]),
                dmc.Group(children=[
                    dmc.Select(
                        id='exploration-view-select',
                        data=[
                            {'label': 'Vue Combinée', 'value': 'both'},
                            {'label': 'Carte Uniquement', 'value': 'map'},
                            {'label': 'Radar Uniquement', 'value': 'radar'}
                        ],
                        value='both',
                        radius="md",
                        w=220,
                        leftSection=DashIconify(icon="solar:layers-linear", width=18),
                        comboboxProps={"withinPortal": True, "shadow": "xl", "transitionProps": {"transition": "pop-top-left", "duration": 200}, "offset": 7},
                        styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}}
                    ),
                    dmc.ActionIcon(
                        DashIconify(icon="akar-icons:question", width=20),
                        id="exploration-guide-btn",
                        size="lg",
                        variant="light",
                        color="blue",
                        radius="md"
                    )
                ])
            ]
        ),

        # Main Interface
        html.Div(
            id='exploration-main-container',
            style={"display": "flex", "flexDirection": "column", "gap": "20px"},
            children=[
                # Map Section
                dmc.Paper(
                    id='container-map',
                    withBorder=True, shadow="sm", p="md", radius="md",
                    style={"display": "flex", "flexDirection": "column", "minHeight": "65vh"},
                    children=[
                        dmc.Group(justify="space-between", mb="md", children=[
                            dmc.Group(gap="xs", children=[
                                DashIconify(icon="solar:map-linear", color="#339af0"),
                                dmc.Text("Analyse Spatiale", fw=700),
                            ]),
                            dmc.Group(gap="xs", children=[
                                dmc.Select(id='map-indic-select', data=[{'label': 'Incidence', 'value': 'INCI'},{'label': 'Mortalité', 'value': 'MORT'},{'label': 'Prévalence', 'value': 'PREV'}], value='INCI', size="xs", w=100, radius="md", comboboxProps={"withinPortal": True, "shadow": "md", "offset": 5}, styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff"}}),
                                dmc.Select(id='map-patho-select', data=[{'label': 'AVC', 'value': 'AVC'},{'label': 'Cardiopathies', 'value': 'CardIsch'},{'label': 'Insuffisance', 'value': 'InsuCard'}], value='AVC', size="xs", w=120, radius="md", comboboxProps={"withinPortal": True, "shadow": "md", "offset": 5}, styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff"}}),
                                dmc.Switch(id='map-show-markers-switch', label="Points/Exclusions", checked=True, size="xs"),
                            ])
                        ]),
                        dmc.Grid(
                            gutter="md",
                            children=[
                                dmc.GridCol(
                                    span=9,
                                    children=[
                                        dcc.Graph(id='map-graph', style={'height': "550px", "width": "100%"}, config={'displayModeBar': False}),
                                    ]
                                ),
                                dmc.GridCol(
                                    span=3,
                                    children=[
                                        dmc.Stack(
                                            gap="md",
                                            children=[
                                                dmc.Paper(
                                                    withBorder=True, p="sm", radius="md", bg="#f8f9fa",
                                                    children=[
                                                        dmc.Text("Statistiques & Légende", size="xs", fw=700, tt="uppercase", c="dimmed", mb="sm"),
                                                        html.Div(id='map-legend-stats-content'),
                                                        html.Div(id='map-reading-guide', style={'fontSize': '11px', 'color': 'gray', 'marginTop': '10px'})
                                                    ]
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                ),

                # Radar Section
                dmc.Paper(
                    id='container-radar',
                    withBorder=True, shadow="sm", p="md", radius="md",
                    style={"display": "flex", "flexDirection": "column", "minHeight": "60vh"},
                    children=[
                        dmc.Group(gap="xs", mb="md", children=[
                            DashIconify(icon="solar:chart-2-linear", color="#339af0"),
                            dmc.Text("Profil Comparatif", fw=700),
                        ]),
                        html.Div(
                            id='radar-placeholder',
                            style={'flex': 1, 'display': 'flex', 'minHeight': '300px'},
                            children=dmc.Center(
                                style={"width": "100%"},
                                children=dmc.Stack(align="center", gap="xs", children=[
                                    DashIconify(icon="solar:chart-2-bold-duotone", width=60, color="#ced4da"),
                                    dmc.Text("Sélectionnez >2 variables et un territoire pour activer le radar", size="sm", c="dimmed"),
                                ])
                            )
                        ),
                        dcc.Graph(id='radar-chart', style={'display': 'none', 'flex': 1, 'minHeight': "450px"}, config={'displayModeBar': False}),
                        html.Div(id='radar-reading-guide', style={'fontSize': '12px', 'marginTop': '10px'})
                    ]
                )
            ]
        ),

        # Guide Drawer
        dmc.Drawer(
            id="exploration-guide-drawer",
            title=dmc.Title("Mode d'emploi - Exploration", order=3),
            opened=False, p="md", position="right", size="md",
            children=[
                dmc.Stack(gap="md", children=[
                    dmc.Text("La vue exploration combine la carte régionale et le radar comparatif.", size="sm"),
                    dmc.Divider(),
                    dmc.Title("Carte", order=5),
                    dmc.Text("- Utilisez les curseurs à gauche pour filtrer. Les territoires hors limites restent grisés avec un point de couleur.", size="sm"),
                    dmc.Text("- Cliquez sur n'importe quel zone pour l'ajouter/retirer du comparateur.", size="sm"),
                    dmc.Title("Défilement", order=5),
                    dmc.Text("- Faites défiler la page pour accéder au radar chart situé sous la carte.", size="sm"),
                ])
            ]
        )
    ]
)

# --- Guide Drawer Callback ---
@callback(
    Output("exploration-guide-drawer", "opened"),
    Input("exploration-guide-btn", "n_clicks"),
    State("exploration-guide-drawer", "opened"),
    prevent_initial_call=True,
)
def toggle_drawer(n, opened):
    return not opened

# --- Sliders Management ---
@callback(
    [Output('slider-container-social', 'children'),
     Output('slider-container-offre', 'children'),
     Output('slider-container-env', 'children')],
    [Input('sidebar-filter-social', 'value'),
     Input('sidebar-filter-offre', 'value'),
     Input('sidebar-filter-env', 'value')],
    [State({'type': 'exploration-slider', 'index': ALL}, 'value'),
     State({'type': 'exploration-slider', 'index': ALL}, 'id')]
)
def update_sliders(social, offre, env, current_vals, current_ids):
    val_map = {id_dict['index']: val for val, id_dict in zip(current_vals, current_ids)}
    
    def make_slider(var):
        if var not in gdf_merged.columns: return None
        mn, mx = gdf_merged[var].min(), gdf_merged[var].max()
        initial_val = val_map.get(var, [mn, mx])
        fmt = lambda val: f"{val:.0f}" if abs(val) >= 10 else f"{val:.2f}"
        label = variable_dict.get(var, var)
        unit = unit_dict.get(var, "")
        if unit: label += f" ({unit})"
        
        return dmc.Box(mb="md", children=[
            dmc.Text(label, size="xs", fw=600, mb=5),
            dcc.RangeSlider(
                id={'type': 'exploration-slider', 'index': var},
                min=mn, max=mx, value=initial_val,
                marks={mn: fmt(mn), mx: fmt(mx)},
                tooltip={"always_visible": True, "placement": "bottom"}
            )
        ])

    return [make_slider(v) for v in (social or [])], \
           [make_slider(v) for v in (offre or [])], \
           [make_slider(v) for v in (env or [])]

# --- View Switching ---
@callback(
    [Output('container-map', 'style'),
     Output('container-radar', 'style')],
    Input('exploration-view-select', 'value')
)
def update_view_visibility(view):
    base_map = {"display": "flex", "flexDirection": "column"}
    base_radar = {"display": "flex", "flexDirection": "column"}
    if view == 'map': return {**base_map, "minHeight": "80vh"}, {"display": "none"}
    if view == 'radar': return {"display": "none"}, {**base_radar, "minHeight": "80vh"}
    return {**base_map, "minHeight": "65vh"}, {**base_radar, "minHeight": "60vh"}

# --- Map Click Selection ---
@callback(
    Output('sidebar-epci-radar', 'value'),
    Input('map-graph', 'clickData'),
    State('sidebar-epci-radar', 'value'),
    prevent_initial_call=True
)
def select_epci_on_click(clickData, current_selection):
    if not clickData: return no_update
    epci_code = None
    if 'customdata' in clickData['points'][0]:
        cd = clickData['points'][0]['customdata']
        epci_code = cd[0] if isinstance(cd, list) else cd
        
    if not epci_code: return no_update
    
    selection = current_selection or []
    if epci_code in selection: selection.remove(epci_code)
    else: selection.append(epci_code)
    return selection

# --- Map Callback ---
@callback(
    [Output('map-graph', 'figure'),
     Output('map-legend-stats-content', 'children'),
     Output('map-reading-guide', 'children')],
    [Input('map-indic-select', 'value'), Input('map-patho-select', 'value'),
     Input({'type': 'exploration-slider', 'index': ALL}, 'value'),
     Input('sidebar-epci-radar', 'value'),
     Input('map-show-markers-switch', 'checked')],
    State({'type': 'exploration-slider', 'index': ALL}, 'id')
)
def update_map(ind, patho, slider_vals, epci_selection, show_markers, slider_ids):
    try:
        target = f"{ind}_{patho}"
        if target not in gdf_merged.columns and target == 'INCI_CNR': target = 'Taux_CNR'
        if target not in gdf_merged.columns: return go.Figure(), "Indicateur non trouvé", ""

        total_epci = len(gdf_merged)
        mask = pd.Series([True] * total_epci)
        summaries = []
        
        if slider_vals:
            for i, (val, id_dict) in enumerate(zip(slider_vals, slider_ids)):
                col = id_dict['index']
                col_mask = gdf_merged[col].between(val[0], val[1])
                mask &= col_mask
                
                # Stats
                nan_n = gdf_merged[col].isna().sum()
                bad_n = (~col_mask).sum() - nan_n
                summaries.append({
                    'label': variable_dict.get(col, col),
                    'color': MARKER_COLORS[i % len(MARKER_COLORS)],
                    'nan': int(nan_n),
                    'out': int(bad_n)
                })

        df_focus = gdf_merged[mask].copy()
        fig = go.Figure()

        # 1. Background layer (All territories) - Using ID for robust mapping
        fig.add_trace(go.Choropleth(
            geojson=geojson_data,
            locations=gdf_merged.index.astype(str),
            z=[0] * total_epci,
            colorscale=[[0, '#f1f3f5'], [1, '#f1f3f5']],
            showscale=False,
            marker_line_width=0.5,
            marker_line_color='rgba(0,0,0,0.1)',
            hoverinfo='text',
            text=gdf_merged['nom_EPCI'],
            customdata=gdf_merged['EPCI_CODE'],
            name="Région"
        ))

        # 2. Focus layer
        if not df_focus.empty:
            fig.add_trace(go.Choropleth(
                geojson=geojson_data,
                locations=df_focus.index.astype(str),
                z=df_focus[target],
                colorscale="Blues",
                marker_line_width=0.5,
                marker_line_color="rgba(255,255,255,0.8)",
                colorbar=dict(thickness=15, len=0.8, y=0.5, x=0.01, xanchor="left", title=unit_dict.get(target, "")),
                hovertemplate="<b>%{text}</b><br>" + variable_dict.get(target, target) + ": %{z:.2f}<extra></extra>",
                text=df_focus['nom_EPCI'],
                customdata=df_focus['EPCI_CODE']
            ))

        # 3. Department outlines
        fig.add_trace(go.Choropleth(
            geojson=geojson_deps,
            locations=gdf_deps_4326.index.astype(str),
            z=[0] * len(gdf_deps_4326),
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
            showscale=False,
            marker_line_width=1.5,
            marker_line_color='rgba(0,0,0,0.6)',
            hoverinfo='skip'
        ))

        # 4. Exclusion Markers
        if show_markers and slider_vals:
            for i, (val, id_dict) in enumerate(zip(slider_vals, slider_ids)):
                col = id_dict['index']
                bad_m = ~gdf_merged[col].between(val[0], val[1])
                excluded = gdf_4326[bad_m].copy()
                if not excluded.empty:
                    centroids = excluded.geometry.centroid
                    offset = (i - len(slider_vals)/2) * 0.045
                    fig.add_trace(go.Scattergeo(
                        lon=centroids.x + offset, lat=centroids.y,
                        mode='markers',
                        marker=dict(size=8, color=MARKER_COLORS[i % len(MARKER_COLORS)], opacity=0.85, line=dict(width=1, color='white')),
                        hoverinfo='text',
                        text=excluded['nom_EPCI'].apply(lambda x: f"Exclu par: {variable_dict.get(col, col)}<br>EPCI: {x}"),
                        customdata=excluded['EPCI_CODE'],
                        showlegend=False
                    ))

        # 5. Highlight selection
        if epci_selection:
            sel = epci_selection if isinstance(epci_selection, list) else [epci_selection]
            hl = gdf_4326[gdf_4326['EPCI_CODE'].isin(sel)]
            if not hl.empty:
                centroids = hl.geometry.centroid
                fig.add_trace(go.Scattergeo(
                    lon=centroids.x, lat=centroids.y,
                    mode='markers',
                    marker=dict(size=18, color='#e03131', symbol='circle', line=dict(width=2, color='white')),
                    text=hl['nom_EPCI'], customdata=hl['EPCI_CODE'],
                    showlegend=False, hoverinfo='text'
                ))

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor='white', clickmode='event+select')
        
        # Stats UI
        stats_header = dmc.Group(justify="space-between", mb=10, children=[
            dmc.Badge(f"{len(df_focus)} EPCI", color="blue", variant="filled"),
            dmc.Badge(f"{total_epci - len(df_focus)} exclus", color="red", variant="light")
        ])
        
        rows = [dmc.Group(gap=8, align="flex-start", mb=10, children=[
            html.Div(style={"width": "12px", "height": "12px", "borderRadius": "50%", "backgroundColor": s['color'], "marginTop": "3px"}),
            dmc.Stack(gap=0, style={"flex": 1}, children=[
                dmc.Text(s['label'], size="xs", fw=700, style={"lineHeight": 1.1}),
                dmc.Text(f"Élimine : {s['out']} (lim) | {s['nan']} (man)", size="10px", c="dimmed")
            ])
        ]) for s in summaries]
        
        content = dmc.Stack(gap="xs", children=[stats_header] + (rows or [dmc.Text("Aucun filtre actif", size="xs", italic=True, c="dimmed")]))
        return fig, content, dmc.Text("Intensité : Valeur indicateur. Points : Raison exclusion.", size="xs", c="dimmed")
        
    except Exception as e:
        import traceback
        err = f"Crash Traceback:\n{traceback.format_exc()}"
        print(err)
        # Return a visible error in the stats area for debugging if needed
        return go.Figure(), dmc.Alert(f"Erreur de rendu : {str(e)}", color="red"), "Erreur technique"

# --- Radar Callback ---
@callback(
    [Output('radar-chart', 'figure'),
     Output('radar-chart', 'style'),
     Output('radar-placeholder', 'style'),
     Output('radar-reading-guide', 'children')],
    [Input('sidebar-filter-social', 'value'), Input('sidebar-filter-offre', 'value'), Input('sidebar-filter-env', 'value'),
     Input('sidebar-epci-radar', 'value')]
)
def update_radar(social, offre, env, epci_codes):
    selected_vars = (social or []) + (offre or []) + (env or [])
    if len(selected_vars) < 3: return go.Figure(), {'display': 'none'}, {'display': 'flex', 'flex': 1}, ""
    
    fig = go.Figure()
    means = [gdf_merged[v].mean() for v in selected_vars]
    stds = [gdf_merged[v].std() for v in selected_vars]
    labels = [variable_dict.get(v, v) for v in selected_vars]
    
    # Zone d'acceptation
    fig.add_trace(go.Scatterpolar(r=[m+s for m,s in zip(means,stds)], theta=labels, fill='toself', fillcolor='rgba(200,200,200,0.3)', line=dict(color='rgba(0,0,0,0)'), name="Normalité (±1σ)"))
    fig.add_trace(go.Scatterpolar(r=[max(0,m-s) for m,s in zip(means,stds)], theta=labels, fill='toself', fillcolor='white', line=dict(color='rgba(0,0,0,0)'), showlegend=False))
    fig.add_trace(go.Scatterpolar(r=means, theta=labels, name="Moyenne Région", line=dict(dash='dash', color='#868e96')))

    if epci_codes:
        C = ['#339af0', '#51cf66', '#fcc419', '#ff922b', '#ae3ec9', '#15aabf']
        for i, code in enumerate(epci_codes):
            row = gdf_merged[gdf_merged['EPCI_CODE'] == code]
            if not row.empty:
                r_vals = [row[v].values[0] for v in selected_vars]
                fig.add_trace(go.Scatterpolar(r=r_vals, theta=labels, fill='toself', name=row['nom_EPCI'].values[0], line=dict(color=C[i%len(C)])))
    
    fig.update_layout(polar=dict(radialaxis=dict(visible=True), angularaxis=dict(gridcolor="#e9ecef")), margin={"t":60,"b":40,"l":100,"r":100}, legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"))
    return fig, {'display': 'block', 'flex': 1}, {'display': 'none'}, dmc.Alert("Zone ombrée : moyenne ± écart-type.", color="gray", variant="light")
