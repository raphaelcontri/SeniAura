import dash
from dash import dcc, html, Input, Output, callback, ALL, State, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from ..data import load_data

# Load shared data
gdf_merged, variable_dict, category_dict, sens_dict, description_dict, unit_dict, gdf_deps, source_dict = load_data()

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
        # (Le titre et le bouton Aide sont désormais fixés dans le Header global)

        # Main Interface
        html.Div(
            id='exploration-main-container',
            style={"display": "flex", "flexDirection": "column", "gap": "20px"},
            children=[
                # Map Section
                dmc.Paper(
                    id='container-map',
                    withBorder=True, shadow="sm", p="md", radius="md",
                    style={"display": "flex", "flexDirection": "column", "minHeight": "650px"},
                    children=[
                        dmc.Group(justify="space-between", mb="md", children=[
                            dmc.Group(gap="xs", children=[
                                DashIconify(icon="solar:map-linear", color="#339af0"),
                                dmc.Text("Carte choroplèthe", id='map-dynamic-title', fw=700),
                            ]),
                        ]),
                        dmc.Grid(
                            gutter="md",
                            children=[
                                dmc.GridCol(
                                    span=12,
                                    children=[
                                        dcc.Graph(
                                            id='map-graph',
                                            style={'height': "550px", "width": "100%"}, 
                                            config={
                                                'displayModeBar': False, 
                                                'scrollZoom': False,
                                                'doubleClick': 'reset+autosize',
                                                'showTips': False
                                            }
                                        ),
                                        # New horizontal stats box
                                        dmc.Paper(
                                            withBorder=True, p="md", radius="md", bg="#f8f9fa", mt="sm",
                                            children=[
                                                dmc.Group(justify="space-between", mb="xs", children=[
                                                    dmc.Text("Détails des exclusions par variable", size="xs", fw=700, tt="uppercase", c="dimmed"),
                                                    html.Div(id='map-reading-guide', style={'fontSize': '11px', 'color': 'gray'})
                                                ]),
                                                html.Div(id='map-legend-stats-content'),
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
                    style={"display": "flex", "flexDirection": "column", "minHeight": "600px"},
                    children=[
                        dmc.Group(gap="xs", mb="md", children=[
                            DashIconify(icon="solar:chart-2-linear", color="#339af0"),
                            dmc.Text("Profil Comparatif", id='radar-dynamic-title', fw=700),
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
                        dcc.Graph(id='radar-chart', style={'display': 'none', 'flex': 1, 'minHeight': "750px"}, config={'displayModeBar': False}),
                        html.Div(id='radar-reading-guide', style={'fontSize': '12px', 'marginTop': '10px'})
                    ]
                )
            ]
        ),
    ]
)

# --- Guide Content Callback ---
@callback(
    Output("aside-content", "children"),
    Input("url", "pathname")
)
def update_aside_content(pathname):
    if pathname in ['/exploration', '/carte', '/radar']:
        return dmc.Stack(gap="md", children=[
            dmc.Title("Mode d'emploi - Exploration", order=3, c="#2c3e50"),
            dmc.Text("La vue exploration combine la carte régionale et le radar comparatif.", size="sm"),
            dmc.Divider(),
            dmc.Title("Carte", order=5),
            dmc.Text("- Utilisez les curseurs à gauche pour filtrer. Les territoires hors limites restent grisés.", size="sm"),
            dmc.Text("- Cliquez sur n'importe quel zone pour l'ajouter/retirer du comparateur.", size="sm"),
            dmc.Title("Radar Chart", order=5),
            dmc.Text("- Le radar affiche les indicateurs pour l'EPCI sélectionné par rapport à la moyenne régionale (zone bleue).", size="sm"),
            dmc.Text("- Faites défiler pour voir le radar sous la carte.", size="sm"),
            dmc.Divider(),
            dmc.Alert(
                "Le panneau de filtrage à gauche s'adapte à vos choix d'indicateur de santé.",
                title="Astuce",
                color="blue",
                variant="light",
                radius="md"
            )
        ])
    return dmc.Text("Aucune aide spécifique pour cette page.", c="dimmed", fs="italic")

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
    
    def make_category_item(vars, label_cat):
        if not vars: return []
        
        sliders = []
        for var in vars:
            if var not in gdf_merged.columns: continue
            mn, mx = gdf_merged[var].min(), gdf_merged[var].max()
            initial_val = val_map.get(var, [mn, mx])
            fmt = lambda val: f"{val:.0f}" if abs(val) >= 10 else f"{val:.2f}"
            label_var = variable_dict.get(var, var)
            unit = unit_dict.get(var, "")
            label_full = f"{label_var} ({unit})" if unit else label_var
            mn_rounded = round(mn, 3 if (mx-mn) < 10 else 1)
            mx_rounded = round(mx, 3 if (mx-mn) < 10 else 1)
            initial_val_rounded = [round(v, 3 if (mx-mn) < 10 else 1) for v in initial_val]
            q05 = round(gdf_merged[var].quantile(0.05), 3 if (mx-mn) < 10 else 1)
            q95 = round(gdf_merged[var].quantile(0.95), 3 if (mx-mn) < 10 else 1)
            
            sliders.append(dmc.Box(mb=8, px=0, children=[
                dmc.Text(label_full, size="10px", fw=600, mb=2, c="dimmed"),
                dcc.RangeSlider(
                    id={'type': 'exploration-slider', 'index': var},
                    min=mn_rounded, max=mx_rounded, value=initial_val_rounded,
                    marks={q05: {"label": "5%", "style": {"fontSize": "8px", "marginTop": "-15px"}}, 
                           q95: {"label": "95%", "style": {"fontSize": "8px", "marginTop": "-15px"}}},
                    step=round((mx-mn)/100, 3 if (mx-mn) < 10 else 1),
                    tooltip={"always_visible": True, "placement": "bottom"}
                )
            ]))
        
        return sliders if sliders else []

    return make_category_item(social, "Socio-Économie"), \
           make_category_item(offre, "Offre de Soins"), \
           make_category_item(env, "Environnement")

# --- View Switching ---
# Visibility control removed as requested (Combined view is now the permanent default).

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
     Output('map-reading-guide', 'children'),
     Output('map-dynamic-title', 'children')],
    [Input('map-indic-select', 'value'), Input('map-patho-select', 'value'),
     Input({'type': 'exploration-slider', 'index': ALL}, 'value'),
     Input('sidebar-epci-radar', 'value')],
    State({'type': 'exploration-slider', 'index': ALL}, 'id')
)
def update_map(ind, patho, slider_vals, epci_selection, slider_ids):
    try:
        # Dynamic Title logic
        indic_map = {'INCI': "l'incidence", 'MORT': "la mortalité", 'PREV': "la prévalence"}
        patho_map = {'AVC': "de l'AVC", 'CardIsch': "de la Cardiopathie Ischémique", 'InsuCard': "de l'insuffisance cardiaque"}
        i_str = indic_map.get(ind, ind)
        p_str = patho_map.get(patho, patho)
        dynamic_title = f"Carte choroplèthe de {i_str} {p_str} en Auvergne-Rhône-Alpes selon les variables sélectionnées"

        target = f"{ind}_{patho}"
        if target not in gdf_merged.columns and target == 'INCI_CNR': target = 'Taux_CNR'
        if target not in gdf_merged.columns: return go.Figure(), "Indicateur non trouvé", "", dynamic_title

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
                    'id': col,
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

        # 4. Exclusion Markers - DELETED as requested.
        # Markers for excluded territories are no longer displayed on the map.

        # 5. Highlight selection
        selection_alert = None
        if epci_selection:
            sel = epci_selection if isinstance(epci_selection, list) else [epci_selection]
            hl = gdf_merged[gdf_merged['EPCI_CODE'].isin(sel)]
            if not hl.empty:
                fig.add_trace(go.Choropleth(
                    geojson=geojson_data,
                    locations=hl.index.astype(str),
                    z=[1] * len(hl),
                    colorscale=[[0, 'rgba(224, 49, 49, 0.05)'], [1, 'rgba(224, 49, 49, 0.05)']],
                    showscale=False,
                    marker_line_width=2.5,
                    marker_line_color='#e03131',
                    hoverinfo='skip',
                    name="Sélection"
                ))

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            margin={"r":0, "t":0, "l":0, "b":0},
            paper_bgcolor='white', 
            clickmode='event+select',
            dragmode=False # Désactive le panoramique et le zoom par glissement
        )
        
        # Stats UI (Horizontal Layout beneath the map)
        total_excl = total_epci - len(df_focus)
        stats_header = dmc.Box(mb=10, children=[
            dmc.Text([
                "Sur ", dmc.Text(str(total_epci), fw=700, span=True), " EPCI en région AURA, ",
                dmc.Text(str(total_excl), fw=700, c="red", span=True), 
                " sont exclus par les filtres sélectionnés."
            ], size="md", c="gray.8")
        ])
        
        # Interpretation Guide Intro
        interpretation_guide = dmc.Text(
            "Cette section vous aide à comprendre pourquoi certains territoires sont grisés sur la carte. "
            "Les filtres réglés dans la barre latérale écartent les zones ne répondant pas à vos critères.",
            size="sm", c="gray.6", mb="md", fs="italic"
        )

        # Display each contributing variable with clear sentences (2 columns for better readability of phrases)
        stats_grid = dmc.SimpleGrid(
            cols=2, spacing="md", verticalSpacing="sm",
            children=[
                dmc.Paper(
                    p="sm", withBorder=True, radius="sm", bg="white",
                    children=[
                        dmc.Text(s['label'], size="sm", fw=700, mb=6, c="blue.9"),
                        dmc.Stack(gap=4, children=[
                            dmc.Text(f"• {s['out']} territoires sont grisés car en dehors de la plage sélectionnée pour cette variable.", size="xs", c="gray.8"),
                            dmc.Text(f"• {s['nan']} territoires sont grisés par manque de données.", size="xs", c="gray.8") if s['nan'] > 0 else None
                        ])
                    ]
                ) for s in summaries
            ]
        )
        
        content = dmc.Stack(gap=0, children=[interpretation_guide, stats_header, stats_grid]) if summaries else dmc.Text("Aucun filtre actif", size="xs", fs="italic", c="dimmed")
        
        # Standard reading guide
        guide = dmc.Group([
            dmc.Group([html.Div(style={"width":8,"height":8,"backgroundColor":"#1971c2"}), dmc.Text("Risque Fort", size="10px")]),
            dmc.Group([html.Div(style={"width":8,"height":8,"backgroundColor":"#e7f5ff"}), dmc.Text("Risque Faible", size="10px")]),
            dmc.Divider(orientation="vertical"),
            dmc.Text("Gris : Territoires ne répondant pas aux critères", size="xs", c="dimmed"),
        ], gap="sm")
        
        return fig, content, guide, dynamic_title
        
    except Exception as e:
        import traceback
        err = f"Crash Traceback:\n{traceback.format_exc()}"
        print(err)
        # Return a visible error in the stats area for debugging if needed
        return go.Figure(), dmc.Alert(f"Erreur de rendu : {str(e)}", color="red"), "Erreur technique", "Erreur"

# --- Radar Callback ---
@callback(
    [Output('radar-chart', 'figure'),
     Output('radar-chart', 'style'),
     Output('radar-placeholder', 'style'),
     Output('radar-reading-guide', 'children'),
     Output('radar-dynamic-title', 'children')],
    [Input('sidebar-filter-social', 'value'), 
     Input('sidebar-filter-offre', 'value'), 
     Input('sidebar-filter-env', 'value'),
     Input('sidebar-epci-radar', 'value'),
     Input('map-indic-select', 'value'), Input('map-patho-select', 'value')]
)
def update_radar(social, offre, env, epci_codes, ind, patho):
    target = f"{ind}_{patho}"
    # Consistency with map logic for CNR
    if target not in gdf_merged.columns and target == 'INCI_CNR' and 'Taux_CNR' in gdf_merged.columns: target = 'Taux_CNR'
    
    # Always include health indicator as first axis
    selected_vars = [target] + (social or []) + (offre or []) + (env or [])
    # Unique values only while preserving order if possible
    seen = set()
    selected_vars = [x for x in selected_vars if not (x in seen or seen.add(x))]
    
    names_str = ""
    if epci_codes:
        # Get names from EPCI codes
        names = gdf_merged[gdf_merged['EPCI_CODE'].isin(epci_codes)]['nom_EPCI'].tolist()
        names_str = f" des territoires ({', '.join(names)})"
    
    dynamic_title = f"Radar comparatif{names_str} par rapport à la moyenne régionale des variables sélectionnées"

    if not selected_vars: 
        return go.Figure(), {'display': 'none'}, {'display': 'flex', 'flex': 1}, "", dynamic_title
    
    fig = go.Figure()
    means = [gdf_merged[v].mean() for v in selected_vars]
    stds = [gdf_merged[v].std() for v in selected_vars]
    labels = [variable_dict.get(v, v) for v in selected_vars]
    
    # Zone d'acceptation
    fig.add_trace(go.Scatterpolar(r=[m+s for m,s in zip(means,stds)], theta=labels, fill='toself', fillcolor='rgba(200,200,200,0.3)', line=dict(color='rgba(0,0,0,0)'), name="Zone d'acceptabilité (écart type)"))
    fig.add_trace(go.Scatterpolar(r=[max(0,m-s) for m,s in zip(means,stds)], theta=labels, fill='toself', fillcolor='white', line=dict(color='rgba(0,0,0,0)'), showlegend=False))
    fig.add_trace(go.Scatterpolar(r=means, theta=labels, name="Moyenne Région", line=dict(dash='dash', color='#868e96')))

    if epci_codes:
        C = ['#339af0', '#51cf66', '#fcc419', '#ff922b', '#ae3ec9', '#15aabf']
        for i, code in enumerate(epci_codes):
            row = gdf_merged[gdf_merged['EPCI_CODE'] == code]
            if not row.empty:
                r_vals = [row[v].values[0] for v in selected_vars]
                fig.add_trace(go.Scatterpolar(r=r_vals, theta=labels, fill='toself', name=row['nom_EPCI'].values[0], line=dict(color=C[i%len(C)])))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, gridcolor="#e9ecef", gridwidth=1), angularaxis=dict(gridcolor="#e9ecef")), 
        margin={"t":40,"b":40,"l":40,"r":40}, 
        height=700, 
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center")
    )
    return fig, {'display': 'block', 'flex': 1}, {'display': 'none'}, dmc.Alert("Zone ombrée : moyenne ± écart-type.", color="gray", variant="light"), dynamic_title
