import dash
from dash import dcc, html, Input, Output, callback, ALL, State, no_update, clientside_callback, ClientsideFunction
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import random
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from src.data import load_data

try:
    df_hosp = pd.read_csv("data/hospitals_ara.csv")
except Exception:
    df_hosp = pd.DataFrame()

CONNECTORS = [
    " associé à ", " combiné à ", " couplé à ", " ainsi qu'un(e) ", 
    " avec également un(e) ", " conjointement à ", " en complément de ",
    " lié à ", " accompagné de ", " doublé d'un(e) "
]

# Load shared data
gdf_merged, variable_dict, category_dict, sens_dict, description_dict, unit_dict, gdf_deps, source_dict, classement_dict = load_data()

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
    p=0,
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
                    style={"minHeight": "650px"},
                    children=[
                        dmc.Group(justify="space-between", mb="md", children=[
                            dmc.Group(gap="xs", children=[
                                DashIconify(icon="solar:map-linear", color="#339af0"),
                                dmc.Text("Carte ", id='map-dynamic-title', fw=700),
                            ]),
                        ]),
                        dmc.Grid(
                            gutter="md",
                            style={"flex": 1, "minHeight": 0},
                            children=[
                                dmc.GridCol(
                                    span=8,
                                    style={"position": "relative"},
                                    children=[
                                        dmc.LoadingOverlay(
                                            id="map-loading-overlay",
                                            visible=False,
                                            overlayProps={"blur": 2},
                                            zIndex=1000,
                                            loaderProps={"variant": "bars", "color": "blue", "size": "xl"},
                                        ),
                                        dmc.Group(justify="flex-end", mb="xs", children=[
                                            dmc.Switch(
                                                id="show-hospitals-switch",
                                                label="Afficher les hôpitaux",
                                                checked=False, # Default to False
                                                size="xs",
                                                style={"display": "none"} # Hide the switch
                                            ),
                                        ]),
                                        dcc.Graph(
                                            id='map-graph',
                                            style={'height': "600px", "width": "100%", "borderRadius": "inherit"}, 
                                            config={
                                                'displayModeBar': True, 
                                                'scrollZoom': True,
                                                'doubleClick': 'reset+autosize',
                                                'showTips': True
                                            }
                                        ),
                                    ]
                                ),
                                # New vertical stats box
                                dmc.GridCol(
                                    span=4,
                                    children=[
                                        dmc.Paper(
                                            withBorder=True, p="md", radius="md", bg="#f8f9fa",
                                            style={'minHeight': '600px', 'maxHeight': '600px', 'overflowY': 'auto'},
                                            children=[
                                                dmc.Group(justify="space-between", mb="xs", children=[
                                                    dmc.Text("Interprétations : ", size="lg", fw=800, tt="uppercase", c="dark"),
                                                    html.Div(id='map-reading-guide', style={'fontSize': '11px', 'color': 'gray'})
                                                ]),
                                                html.Div(id='map-stats-header-content'),
                                                html.Div(id='map-narrative-content')
                                            ]
                                        ),
                                        dmc.Paper(
                                            withBorder=True, p="md", radius="md", bg="white", mt="md",
                                            style={"display": "none"},
                                            children=[
                                                dmc.Stack(gap="xs", children=[
                                                    dmc.Group(gap="xs", children=[
                                                        dmc.Text("Afficher les EPCI grisés par :", size="xs", fw=600),
                                                        dmc.Tooltip(
                                                            label="Vous pouvez visualiser quels EPCI ont été grisés par une certaine variable. En effet, quand vous sélectionnez plusieurs variables de filtres, un EPCI peut être grisé par une variable mais pas l'autre.",
                                                            w=300, multiline=True, withArrow=True,
                                                            children=dmc.ActionIcon(
                                                                DashIconify(icon="solar:question-circle-linear"),
                                                                variant="subtle", color="gray", size="sm"
                                                            )
                                                        )
                                                    ]),
                                                    dmc.Select(
                                                        id='highlight-variable-select',
                                                        size="xs",
                                                        placeholder="Choisir une variable",
                                                        data=[],
                                                        clearable=True,
                                                    )
                                                ])
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),
                        dmc.Space(h="md"),
                        # Clientside callback to toggle loading overlay
                        dash.clientside_callback(
                            """
                                function(loading_state) {
                                    if (loading_state && loading_state.is_loading) {
                                        return true;
                                    }
                                    return false;
                                }
                            """,
                            Output("map-loading-overlay", "visible"),
                            Input("map-graph", "loading_state")
                        ),
                        html.Div(
                            id="scroll-to-radar-indicator",
                            className="scroll-indicator-container",
                            style={
                                "display": "flex", 
                                "flexDirection": "column", 
                                "alignItems": "center", 
                                "cursor": "pointer",
                                "opacity": 0.8
                            },
                            n_clicks=0,
                            children=[
                                dmc.Text("Comparer les territoires (Radar)", size="xs", fw=700, c="blue.7", style={"textTransform": "uppercase", "letterSpacing": "0.8px"}),
                                DashIconify(
                                    icon="solar:alt-arrow-down-linear", 
                                    width=24, 
                                    color="#339af0",
                                    className="bounce"
                                )
                            ]
                        )
                    ]
                ),

                # Radar Section
                dmc.Paper(
                    id='container-radar',
                    withBorder=True, shadow="sm", p="md", radius="md",
                    style={"minHeight": "650px"},
                    children=[
                        dmc.Group(gap="xs", mb="md", children=[
                            DashIconify(icon="solar:chart-2-linear", color="#339af0"),
                            dmc.Text("Profil Comparatif Radar", id='radar-dynamic-title', fw=700),
                        ]),
                        html.Div(
                            id='radar-placeholder',
                            style={'display': 'flex', 'height': '600px'},
                            children=dmc.Center(
                                style={"width": "100%", "height": "100%"},
                                children=dmc.Stack(align="center", gap="xl", children=[
                                    dmc.ThemeIcon(
                                        DashIconify(icon="solar:chart-2-bold-duotone", width=100),
                                        size=140, radius=100, variant="light", color="blue"
                                    ),
                                    dmc.Paper(
                                        p="xl", radius="lg", withBorder=True, bg="blue.0",
                                        shadow="sm", maw=600,
                                        style={"border": "2px dashed #339af0"},
                                        children=[
                                            dmc.Text(
                                                "Action Requise", 
                                                fw=900, size="lg", c="blue.9", ta="center", mb=10,
                                                style={"letterSpacing": "1px", "textTransform": "uppercase"}
                                            ),
                                            dmc.Text(
                                                "Sélectionnez au moins 2 variables et un territoire pour activer le radar comparatif. La variable d'indicateur de santé sera ajoutée par défaut.",
                                                size="md", fw=700, ta="center", c="#1a1b1e",
                                                style={"lineHeight": "1.6"}
                                            )
                                        ]
                                    )
                                ])
                            )
                        ),
                        dmc.Grid(
                            id='radar-main-grid',
                            gutter="md",
                            style={"flex": 1, "minHeight": 0, "display": "none"},
                            children=[
                                dmc.GridCol(
                                    span=8,
                                    children=[
                                        dcc.Graph(id='radar-chart', style={'display': 'none', 'height': '600px'}, config={'displayModeBar': False, 'staticPlot': False, 'scrollZoom': False}),
                                    ]
                                ),
                                dmc.GridCol(
                                    span=4,
                                    children=[
                                        html.Div(
                                            style={'minHeight': '600px', 'maxHeight': '600px', 'overflowY': 'auto'},
                                            children=[
                                                html.Div(id='radar-guide-header', style={'display': 'none'}),
                                                html.Div(id='radar-reading-guide'),
                                                html.Div(id='radar-guide-paper', style={'display': 'none'}),
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                ),

                # Clustering Section
                dmc.Paper(
                    id='container-cluster',
                    withBorder=True, shadow="sm", p="md", radius="md",
                    style={"minHeight": "650px"},
                    children=[
                        dmc.Group(gap="xs", mb="md", children=[
                            DashIconify(icon="solar:widget-linear", color="#339af0"),
                            dmc.Text("Profiler de Clustering Territorial (K-Means)", id='cluster-dynamic-title', fw=700),
                        ]),
                        html.Div(
                            id='cluster-placeholder',
                            style={'display': 'flex', 'height': '600px'},
                            children=dmc.Center(
                                style={"width": "100%", "height": "100%"},
                                children=dmc.Stack(align="center", gap="xl", children=[
                                    dmc.ThemeIcon(
                                        DashIconify(icon="solar:widget-bold-duotone", width=100),
                                        size=140, radius=100, variant="light", color="indigo"
                                    ),
                                    dmc.Paper(
                                        p="xl", radius="lg", withBorder=True, bg="indigo.0",
                                        shadow="sm", maw=600,
                                        style={"border": "2px dashed #4c6ef5"},
                                        children=[
                                            dmc.Text(
                                                "Clustering Régional", 
                                                fw=900, size="lg", c="indigo.9", ta="center", mb=10,
                                                style={"letterSpacing": "1px", "textTransform": "uppercase"}
                                            ),
                                            dmc.Text(
                                                "Sélectionnez au moins un territoire et des variables dans la barre latérale pour activer le profiler de clustering K-Means.",
                                                size="md", fw=700, ta="center", c="#1a1b1e",
                                                style={"lineHeight": "1.6"}
                                            )
                                        ]
                                    )
                                ])
                            )
                        ),
                        dmc.Grid(
                            id='cluster-main-grid',
                            gutter="md",
                            style={"flex": 1, "minHeight": 0, "display": "none"},
                            children=[
                                dmc.GridCol(
                                    span=7,
                                    children=[
                                        dcc.Graph(id='cluster-chart', style={'display': 'none', 'height': '600px'}, config={'displayModeBar': False}),
                                    ]
                                ),
                                dmc.GridCol(
                                    span=5,
                                    children=[
                                        html.Div(
                                            style={'minHeight': '600px', 'maxHeight': '600px', 'overflowY': 'auto'},
                                            children=[
                                                html.Div(id='cluster-reading-guide'),
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
    ]
)

# --- Guide Content Callback ---
@callback(
    Output("aside-content", "children"),
    Input("url", "pathname")
)
def update_aside_content(pathname):
    if pathname in ['/exploration', '/carte', '/radar']:
        try:
            with open("Aide.txt", "r", encoding="utf-8") as f:
                content = f.read()
            return dmc.Stack(gap="md", children=[
                dcc.Markdown(content, style={"fontSize": "14px", "lineHeight": "1.6"})
            ])
        except Exception:
            # Fallback if file not found
            return dmc.Text("Guide d'aide non disponible.", c="dimmed", fs="italic")
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
            sliders.append(dmc.Box(mb=8, px=0, children=[
                dmc.Text(label_full, size="10px", fw=600, mb=2, c="dimmed"),
                dcc.RangeSlider(
                    id={'type': 'exploration-slider', 'index': var},
                    min=mn_rounded, max=mx_rounded, value=initial_val_rounded,
                    marks={mn_rounded: str(mn_rounded), mx_rounded: str(mx_rounded)},
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

# --- Highlight Select Options Management ---
@callback(
    Output('highlight-variable-select', 'data'),
    [Input('sidebar-filter-social', 'value'),
     Input('sidebar-filter-offre', 'value'),
     Input('sidebar-filter-env', 'value')]
)
def update_highlight_options(social, offre, env):
    all_vars = (social or []) + (offre or []) + (env or [])
    if not all_vars: return []
    return [{'label': variable_dict.get(v, v), 'value': v} for v in all_vars if v in variable_dict]

# --- Map Callback ---
@callback(
    [Output('map-graph', 'figure'),
     Output('map-stats-header-content', 'children'),
     Output('map-narrative-content', 'children'),
     Output('map-reading-guide', 'children'),
     Output('map-dynamic-title', 'children')],
    [Input('map-indic-select', 'value'), Input('map-patho-select', 'value'),
     Input({'type': 'exploration-slider', 'index': ALL}, 'value'),
     Input('sidebar-epci-radar', 'value'),
     Input('highlight-variable-select', 'value'),
     Input('show-hospitals-switch', 'checked')],
    State({'type': 'exploration-slider', 'index': ALL}, 'id')
)
def update_map(ind, patho, slider_vals, epci_selection, highlight_var, show_hospitals, slider_ids):
    try:
        # Dynamic Title logic
        indic_map = {'INCI': "l'incidence", 'MORT': "la mortalité", 'PREV': "la prévalence"}
        patho_map = {'AVC': "de l'AVC", 'CardIsch': "de la Cardiopathie Ischémique", 'InsuCard': "de l'insuffisance cardiaque"}
        i_str = indic_map.get(ind, ind)
        p_str = patho_map.get(patho, patho)
        dynamic_title = f"Carte de {i_str} {p_str} en Auvergne-Rhône-Alpes selon les variables sélectionnées"

        target = f"{ind}_{patho}"
        if target not in gdf_merged.columns and target == 'INCI_CNR': target = 'Taux_CNR'
        if target not in gdf_merged.columns: return go.Figure(), "Indicateur non trouvé", "", "", dynamic_title

        total_epci = len(gdf_merged)
        mask = pd.Series([True] * total_epci, index=gdf_merged.index)
        exclusion_reasons = pd.Series([""] * total_epci, index=gdf_merged.index)
        summaries = []
        
        if slider_vals:
            for i, (val, id_dict) in enumerate(zip(slider_vals, slider_ids)):
                col = id_dict['index']
                col_mask = gdf_merged[col].between(val[0], val[1])
                mask &= col_mask
                
                # Update exclusion reasons
                fail_mask = ~col_mask
                var_name = variable_dict.get(col, col)
                exclusion_reasons.loc[fail_mask] += f"<br>- {var_name}"
                
                # Stats
                nan_n = gdf_merged[col].isna().sum()
                bad_n = (~col_mask).sum() - nan_n
                summaries.append({
                    'id': col,
                    'label': variable_dict.get(col, col),
                    'color': MARKER_COLORS[i % len(MARKER_COLORS)],
                    'nan': int(nan_n),
                    'out': int(bad_n),
                    'val': val # [min, max]
                })

        df_focus = gdf_merged[mask].copy()
        fig = go.Figure()

        click_instruction = "<i>Cliquez sur cet EPCI pour l'ajouter au radar chart</i><br><br>"
        
        # Demographic Context for Tooltips
        demo_text_series = pd.Series([""] * total_epci, index=gdf_merged.index)
        if 'H_65_plus' in gdf_merged.columns and 'F_65_plus' in gdf_merged.columns:
             demo_h = gdf_merged['H_65_plus'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
             demo_f = gdf_merged['F_65_plus'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
             demo_text_series = "<br><span style='font-size: 11.5px;'>👨 Hommes 65+ : <b>" + demo_h + "</b>  |  👩 Femmes 65+ : <b>" + demo_f + "</b></span>"

        # Build text for background layer
        bg_text = click_instruction + "<b>" + gdf_merged['nom_EPCI'] + "</b>" + demo_text_series
        has_exclusion = exclusion_reasons != ""
        bg_text_with_reasons = bg_text.copy()
        bg_text_with_reasons.loc[has_exclusion] += "<br><span style='font-size: 11px; color: #e03131'>Grisé par :</span>" + exclusion_reasons.loc[has_exclusion]

        # 1. Background layer (All territories) - Using ID for robust mapping
        fig.add_trace(go.Choropleth(
            geojson=geojson_data,
            locations=gdf_merged.index.astype(str),
            z=[0] * total_epci,
            colorscale=[[0, '#f1f3f5'], [1, '#f1f3f5']],
            showscale=False,
            marker_line_width=0.5,
            marker_line_color='rgba(0,0,0,0.1)',
            hovertemplate="%{text}<extra></extra>",
            text=bg_text_with_reasons,
            customdata=gdf_merged['EPCI_CODE'],
            name="Région"
        ))

        # 2. Focus layer
        if not df_focus.empty:
            focus_text = df_focus['nom_EPCI'] + demo_text_series.loc[df_focus.index]
            fig.add_trace(go.Choropleth(
                geojson=geojson_data,
                locations=df_focus.index.astype(str),
                z=df_focus[target],
                colorscale="Blues",
                marker_line_width=0.5,
                marker_line_color="rgba(255,255,255,0.8)",
                colorbar=dict(thickness=15, len=0.8, y=0.5, x=0.01, xanchor="left", title=unit_dict.get(target, "")),
                hovertemplate=click_instruction + "<b>%{text}</b><br><br>" + variable_dict.get(target, target) + " : <b>%{z:.2f}</b><extra></extra>",
                text=focus_text,
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

        # 4. Highlight Exclusion (Specific Variable)
        if highlight_var:
            # Find the slider value for highlight_var
            slider_indices = [i for i, d in enumerate(slider_ids) if d['index'] == highlight_var]
            if slider_indices:
                idx = slider_indices[0]
                val = slider_vals[idx]
                
                # EPCIs specifically excluded by this variable
                # mask is already computed in the loop above, but we need the specific one here
                excluded_by_var = ~gdf_merged[highlight_var].between(val[0], val[1])
                # We only show them if they are in the background (already gray)
                df_excl_highlight = gdf_merged[excluded_by_var].copy()
                
                if not df_excl_highlight.empty:
                    fig.add_trace(go.Choropleth(
                        geojson=geojson_data,
                        locations=df_excl_highlight.index.astype(str),
                        z=[1] * len(df_excl_highlight),
                        colorscale=[[0, '#adb5bd'], [1, '#adb5bd']], # Medium gray
                        showscale=False,
                        marker_line_width=1,
                        marker_line_color='rgba(0,0,0,0.3)',
                        hovertemplate=click_instruction + "<b>%{text}</b><br>Grisé par : " + variable_dict.get(highlight_var, highlight_var) + "<extra></extra>",
                        text=df_excl_highlight['nom_EPCI'],
                        name=f"Exclu par {highlight_var}"
                    ))

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
        
        # 6. Major Cities
        cities = [
            {"name": "Lyon", "lat": 45.7640, "lon": 4.8357},
            {"name": "Saint-Étienne", "lat": 45.4397, "lon": 4.3873},
            {"name": "Grenoble", "lat": 45.1885, "lon": 5.7248},
            {"name": "Clermont-Ferrand", "lat": 45.7772, "lon": 3.0870},
            {"name": "Valence", "lat": 44.9333, "lon": 4.8917},
            {"name": "Annecy", "lat": 45.8992, "lon": 6.1293},
            {"name": "Chambéry", "lat": 45.5646, "lon": 5.9238},
            {"name": "Bourg-en-Bresse", "lat": 46.2052, "lon": 5.2258},
            {"name": "Montluçon", "lat": 46.3401, "lon": 2.6020},
            {"name": "Aurillac", "lat": 44.9264, "lon": 2.4418},
            {"name": "Le Puy-en-Velay", "lat": 45.0428, "lon": 3.8829},
            {"name": "Moulins", "lat": 46.5667, "lon": 3.3333},
            {"name": "Privas", "lat": 44.7333, "lon": 4.6000},
        ]
        
        fig.add_trace(go.Scattergeo(
            lat=[c["lat"] for c in cities],
            lon=[c["lon"] for c in cities],
            text=[c["name"] for c in cities],
            mode="markers+text",
            marker=dict(size=4, color="black", opacity=0.7),
            textposition="top center",
            textfont=dict(family="Inter, sans-serif", size=9, color="black"),
            hoverinfo="text",
            showlegend=False
        ))

        # Hospital layer (Disabled but code preserved)
        if False and not df_hosp.empty and show_hospitals:
            fig.add_trace(go.Scattergeo(
                lon=df_hosp['lon'],
                lat=df_hosp['lat'],
                text=df_hosp['name'],
                mode='markers',
                marker=dict(
                    size=4,
                    color='#d6336c',
                    symbol='circle',
                    line=dict(width=0.5, color='white'),
                    opacity=0.7
                ),
                name="Hôpitaux ARA",
                showlegend=False,
                hoverinfo="text"
            ))

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            margin={"r":0, "t":0, "l":0, "b":0},
            paper_bgcolor='white', 
            clickmode='event+select',
            dragmode='pan'
        )
        
        # Narrative Sentence Generation (with Bold info)
        narrative_children = []
        if summaries:
            narrative_children = [dmc.Text("Les territoires qui correspondent à vos filtres sont ceux dont : ", span=True)]
            for i, s in enumerate(summaries):
                unit = unit_dict.get(s['id'], "")
                if i > 0:
                    narrative_children.append(dmc.Text(" et ", fw=700, c="blue.7", span=True))
                
                narrative_children.extend([
                    dmc.Text(f" la variable {s['label']} ", fw=800, span=True),
                    dmc.Text(" est entre ", span=True),
                    dmc.Text(f"{s['val'][0]:.1f}", fw=800, c="blue.9", span=True),
                    dmc.Text(" et ", span=True),
                    dmc.Text(f"{s['val'][1]:.1f}", fw=800, c="blue.9", span=True),
                    dmc.Text(f" (unité : {unit})" if unit else "", span=True),
                ])
            narrative_children.append(dmc.Text(".", span=True))
        
        # Stats UI (Updated Format)
        inclus = len(df_focus)
        exclus = total_epci - inclus
        
        stats_header = dmc.Paper(
            p="md", withBorder=True, radius="md", bg="blue.0", mb="md",
            children=[
                dmc.Group(
                    justify="space-between",
                    align="center",
                    children=[
                        dmc.Text([
                            "Sur ", dmc.Text(str(total_epci), fw=700, span=True), " EPCI en région AURA, ",
                            dmc.Text(str(inclus), fw=700, c="blue", span=True), " sont inclus par filtres sélectionnés et ",
                            dmc.Text(str(exclus), fw=700, c="red", span=True), " sont exclus. Les territoires exclus sont ceux dont les données sont en dehors d'au moins une des plages de variables sélectionnées."
                        ], size="md", c="gray.9"),
                        dcc.Link(
                            dmc.Button(
                                "Quels leviers d'action pour ces territoires ?", 
                                variant="outline", 
                                color="blue", 
                                size="xs",
                                leftSection=DashIconify(icon="solar:lightbulb-bold-duotone", width=16),
                                className="premium-hover"
                            ),
                            href="/leviers"
                        )
                    ]
                )
            ]
        )
        
        # Narrative paper
        narrative_paper = dmc.Paper(
            p="md", withBorder=True, radius="md", bg="blue.0", mb="md",
            children=[
                dmc.Text(narrative_children, size="md", fw=400, c="gray.9", style={"lineHeight": "1.7"})
            ]
        ) if narrative_children else None

        # Descriptions des variables
        desc_children = []
        if target:
            ind_desc = description_dict.get(target, "")
            if not ind_desc:
                ind_desc = "Description non disponible."
            
            # Polarity message
            sens = sens_dict.get(target, 0)
            if sens == 1:
                sens_msg = " (Plus cette variable est élevée, moins le territoire est vulnérable)"
            elif sens == -1:
                sens_msg = " (Plus cette variable est élevée, plus le territoire est vulnérable)"
            else:
                sens_msg = ""
                
            desc_children.append(dmc.Text([
                dmc.Text(f"{variable_dict.get(target, target)} (Indicateur Santé) : ", fw=700, span=True), 
                dmc.Text(ind_desc, span=True),
                dmc.Text(sens_msg, size="xs", fw=600, c="blue.7", span=True)
            ], size="sm"))
                
        for s in summaries:
            var_desc = description_dict.get(s['id'], "")
            if not var_desc:
                var_desc = "Description non disponible."
            
            sens = sens_dict.get(s['id'], 0)
            if sens == 1:
                sens_msg = " (Plus cette variable est élevée, moins le territoire est vulnérable)"
            elif sens == -1:
                sens_msg = " (Plus cette variable est élevée, plus le territoire est vulnérable)"
            else:
                sens_msg = ""
                
            desc_children.append(dmc.Text([
                dmc.Text(f"{s['label']} : ", fw=700, span=True), 
                dmc.Text(var_desc, span=True),
                dmc.Text(sens_msg, size="xs", fw=600, c="blue.7", span=True)
            ], size="sm"))
                
        desc_paper = dmc.Paper(
            p="md", withBorder=True, radius="md", bg="blue.0", mb="md",
            children=[
                dmc.Group(
                    justify="space-between", align="center", mb="xs",
                    children=[
                        dmc.Text("Descriptions des variables", fw=700),
                        dcc.Link(
                            dmc.Button(
                                "Liste variables et méthodologie",
                                size="xs",
                                variant="outline",
                                color="blue",
                                radius="md",
                                leftSection=DashIconify(icon="solar:library-bold-duotone", width=16),
                                className="premium-hover"
                            ),
                            href="/methodologie"
                        )
                    ]
                ),
                dmc.Stack(gap="xs", children=desc_children)
            ]
        ) if desc_children else None

        if summaries:
            content = dmc.Stack(gap="xs", children=[
                stats_header,
                narrative_paper,
                desc_paper
            ])
        else:
            content = dmc.Stack(gap="xs", children=[
                dmc.Text("Aucun filtre actif", size="xs", fs="italic", c="dimmed", mb="xs"),
                desc_paper
            ])
        
        return fig, content, "", "", dynamic_title
        
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
     Output('radar-main-grid', 'style'),
     Output('radar-placeholder', 'style'),
     Output('radar-guide-paper', 'style'),
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
    selected_vars_unique = [x for x in selected_vars if not (x in seen or seen.add(x))]
    
    # Revert to original: only show if at least 3 variables are selected
    if len(selected_vars_unique) < 3:
        return go.Figure(), {'display': 'none'}, {'display': 'none'}, {'display': 'flex', 'height': '600px'}, {'display': 'none'}, "", "Radar comparatif par rapport à la moyenne régionale des variables sélectionnées"
    
    selected_vars = selected_vars_unique
    
    names_str = ""
    if epci_codes:
        # Get names from EPCI codes
        names = gdf_merged[gdf_merged['EPCI_CODE'].isin(epci_codes)]['nom_EPCI'].tolist()
        names_str = f" des territoires ({', '.join(names)})"
    
    dynamic_title = f"Radar comparatif{names_str} par rapport à la moyenne régionale des variables sélectionnées"

    if not selected_vars: 
        return go.Figure(), {'display': 'none'}, {'display': 'none'}, {'display': 'flex', 'height': '600px'}, {'display': 'none'}, "", dynamic_title
    
    fig = go.Figure()
    
    # Pre-calculate ranges and normalized stats
    norm_means = []
    norm_plus_std = []
    norm_minus_std = []
    labels = []
    for i, v in enumerate(selected_vars):
        mn, mx = gdf_merged[v].min(), gdf_merged[v].max()
        denom = mx - mn if mx != mn else 1
        
        m = gdf_merged[v].mean()
        s = gdf_merged[v].std()
        
        norm_m = (m - mn) / denom
        norm_s = s / denom # ratio of std to range
        
        norm_means.append(norm_m)
        norm_plus_std.append(min(1, norm_m + norm_s))
        norm_minus_std.append(max(0, norm_m - norm_s))
        
        unit = unit_dict.get(v, "")
        label = variable_dict.get(v, v)
        base_label = f"{label} ({unit})" if unit else label
        
        # Avoid duplicate labels by adding trailing spaces
        occurrences = selected_vars[:len(labels)].count(v)
        labels.append(base_label + (" " * occurrences))

    # Zone d'acceptation (Normalisée)
    fig.add_trace(go.Scatterpolar(
        r=norm_plus_std, 
        theta=labels, 
        fill='toself', 
        fillcolor='rgba(200,200,200,0.3)', 
        line=dict(color='rgba(0,0,0,0)'), 
        name="Moyenne ± écart type",
        hoverinfo='skip' # On ne veut pas survoler la zone d'écart type
    ))
    fig.add_trace(go.Scatterpolar(
        r=norm_minus_std, 
        theta=labels, 
        fill='toself', 
        fillcolor='white', 
        line=dict(color='rgba(0,0,0,0)'), 
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Moyenne Région (Normalisée - Closed loop)
    fig.add_trace(go.Scatterpolar(
        r=norm_means + [norm_means[0]], 
        theta=labels + [labels[0]], 
        name="Moyenne Région", 
        line=dict(dash='solid', color='#868e96'),
        customdata=[gdf_merged[v].mean() for v in selected_vars] + [gdf_merged[selected_vars[0]].mean()],
        hovertemplate="Moyenne régionale: %{customdata:.2f}<extra></extra>"
    ))

    if epci_codes:
        C = ['#339af0', '#51cf66', '#fcc419', '#ff922b', '#ae3ec9', '#15aabf']
        for i, code in enumerate(epci_codes):
            row = gdf_merged[gdf_merged['EPCI_CODE'] == code]
            if not row.empty:
                r_vals_norm = []
                r_vals_raw = []
                for v in selected_vars:
                    val = row[v].values[0]
                    mn, mx = gdf_merged[v].min(), gdf_merged[v].max()
                    denom = mx - mn if mx != mn else 1
                    r_vals_norm.append((val - mn) / denom)
                    r_vals_raw.append(val)
                
                fig.add_trace(go.Scatterpolar(
                    r=r_vals_norm + [r_vals_norm[0]], 
                    theta=labels + [labels[0]], 
                    fill=None, 
                    name=row['nom_EPCI'].values[0], 
                    line=dict(color=C[i%len(C)], width=2.5),
                    customdata=r_vals_raw + [r_vals_raw[0]],
                    hovertemplate="Valeur: %{customdata:.2f}<extra></extra>"
                ))
    
    fig.update_layout(
        dragmode=False,
        polar=dict(
            radialaxis=dict(
                visible=True, 
                range=[0, 1], 
                gridcolor="#e9ecef", 
                gridwidth=1,
                tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                ticktext=["Min", "20%", "40%", "60%", "80%", "Max"]
            ), 
            angularaxis=dict(showgrid=True, gridcolor="#e9ecef")
        ), 
        margin={"t":40,"b":40,"l":40,"r":40}, 
        autosize=True,
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center")
    )
    # --- NEW: Quantile & Relative Ranking Analysis ---
    quantile_paper = None
    if epci_codes and selected_vars:
        # Pre-calculate ranks for all selected variables across the region
        ranks_df = gdf_merged[selected_vars].rank(pct=True)
        C_radar = ['#339af0', '#51cf66', '#fcc419', '#ff922b', '#ae3ec9', '#15aabf']
        
        quantile_content = []
        for i, code in enumerate(epci_codes):
            row = gdf_merged[gdf_merged['EPCI_CODE'] == code]
            if row.empty: continue
            
            idx = row.index[0]
            epci_name = row['nom_EPCI'].values[0]
            
            epci_quantiles = []
            suggested_levers = []
            for v in selected_vars:
                pct = ranks_df.loc[idx, v] * 100
                label_name = variable_dict.get(v, v)
                
                sens = sens_dict.get(v, -1)
                is_vuln = False
                
                # sens == 1 => highest is best
                if sens == 1:
                    if pct <= 10: 
                        col = "red"
                        phrase = f"Alerte : Plus bas que 90% des territoires"
                        is_vuln = True
                    elif pct <= 25: 
                        col = "orange"
                        phrase = f"Attention : Dans les 25% les plus bas"
                        is_vuln = True
                    elif pct >= 90: 
                        col = "teal"
                        phrase = f"Point fort : Top 10% régional"
                    elif pct >= 75: 
                        col = "cyan"
                        phrase = f"Atout : Top 25% régional"
                    else: 
                        col = "gray"
                        phrase = f"Équilibré : Moyenne régionale"
                # sens == -1 (or 0 fallback) => lowest is best
                else:
                    if pct >= 90: 
                        col = "red"
                        phrase = f"Alerte : Plus élevé que 90% des territoires"
                        is_vuln = True
                    elif pct >= 75: 
                        col = "orange"
                        phrase = f"Attention : Dans les 25% les plus élevés"
                        is_vuln = True
                    elif pct <= 10: 
                        col = "teal"
                        phrase = f"Point fort : Top 10% régional"
                    elif pct <= 25: 
                        col = "cyan"
                        phrase = f"Atout : Top 25% régional"
                    else: 
                        col = "gray"
                        phrase = f"Équilibré : Moyenne régionale"
                        
                    if is_vuln:
                        cat = category_dict.get(v, "autre").lower()
                        if "socio" in cat: cat_str = "Socio-économique"; hash_val = "#socio"
                        elif "env" in cat: cat_str = "Environnement"; hash_val = "#env"
                        elif "offre" in cat or "soins" in cat or "santé" in cat or "demog" in cat or "prev" in cat: 
                            cat_str = "Santé"; hash_val = "#sante"
                        else: cat_str = "Généraux"; hash_val = ""
                        
                        if (cat_str, hash_val) not in suggested_levers:
                            suggested_levers.append((cat_str, hash_val))
                
                epci_quantiles.append(dmc.Grid(align="center", mb=8, children=[
                    dmc.GridCol(span=4, children=[dmc.Text(label_name, size="sm", fw=700)]),
                    dmc.GridCol(span=8, children=[
                        dmc.Badge(
                            phrase, 
                            variant="light", 
                            color=col, 
                            size="sm", 
                            radius="xs", 
                            fullWidth=True,
                            style={
                                "height": "auto", 
                                "padding": "6px 10px", 
                                "whiteSpace": "normal", 
                                "textAlign": "center",
                                "textTransform": "none",
                                "fontSize": "12px", 
                                "fontWeight": 600,
                                "lineHeight": "1.3"
                            }
                        )
                    ])
                ]))
            
            lever_elements = []
            if suggested_levers:
                lever_elements.append(dmc.Text("Leviers recommandés pour combler ces facteurs de vulnérabilité :", size="sm", fw=600, mt="sm", c="indigo"))
                for cl, h in suggested_levers:
                    link = f"/leviers{h}"
                    lever_elements.append(
                        dmc.Group(gap="xs", mb=5, children=[
                            DashIconify(icon="solar:arrow-right-bold-duotone", color="#339af0", width=14),
                            dmc.Text(f"Leviers {cl}", size="sm", fw=700),
                            dcc.Link(
                                dmc.Button("Consulter", color="indigo", variant="light", size="xs", radius="md", className="premium-hover"), 
                                href=link, 
                                target="_blank", 
                                style={"textDecoration": "none", "display": "inline-block"}
                            )
                        ])
                    )
            else:
                 lever_elements.append(dmc.Text("Aucune vulnérabilité majeure identifiée nécessitant une action prioritaire urgente.", size="sm", fs="italic", c="gray", mt="sm"))

            quantile_content.append(dmc.Stack(gap=2, children=[
                dmc.Text(epci_name, size="lg", fw=900, c="#2c3e50", style={"fontSize": "19px", "letterSpacing": "0.5px", "marginTop": "12px", "marginBottom": "2px"}),
                dmc.Divider(size="md", color="#adb5bd", mb="xs"),
                dmc.Stack(gap=2, children=epci_quantiles),
                dmc.Paper(p="xs", radius="sm", bg="indigo.0", mt="xs", children=dmc.Stack(gap=0, children=lever_elements))
            ]))

        quantile_paper = dmc.Paper(
            p="md", withBorder=True, radius="md", bg="gray.1", mt="md",
            style={"minHeight": "100%"},
            children=[
                dmc.Group(gap="xs", mb="sm", children=[
                    DashIconify(icon="solar:ranking-bold-duotone", color="#339af0", width=20),
                    dmc.Text("Guide de lecture : Positionnement du territoire au sein de la région", fw=800, size="sm", tt="uppercase"),
                    dmc.Tooltip(
                        label="Comparaison avec les 172 territoires de la région : Rouge/Orange pour les valeurs les plus hautes, Bleu pour les plus basses, Gris pour la moyenne.",
                        withArrow=True,
                        withinPortal=True,
                        multiline=True,
                        w=250,
                        children=dmc.ActionIcon(
                            DashIconify(icon="solar:question-circle-linear"),
                            variant="subtle", color="gray", size="xs"
                        )
                    )
                ]),
                dmc.Stack(gap="md", children=quantile_content),
                dmc.Divider(variant="dotted", my="sm"),
                dcc.Link(
                    dmc.Button(
                        "Quels leviers d'action pour ces territoires ?", 
                        variant="outline", 
                        color="blue", 
                        size="xs",
                        leftSection=DashIconify(icon="solar:lightbulb-bold-duotone", width=16),
                        className="premium-hover"
                    ),
                    href="/leviers"
                )
            ]
        )

    if quantile_paper:
        guide = dmc.Stack(gap="xs", children=[quantile_paper])
    else:
        guide = html.Div(
            dmc.Text("Sélectionnez des territoires et des variables dans le menu à gauche pour afficher l'analyse comparative détaillée.", size="sm", fs="italic", c="dimmed", ta="center", mt="xl")
        )

    return fig, {'display': 'block', 'height': '600px'}, {'display': 'flex'}, {'display': 'none'}, {'display': 'block'}, guide, dynamic_title

# --- Scroll Affordance Callback ---
clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='scrollToRadar'
    ),
    Output("scroll-to-radar-indicator", "id", allow_duplicate=True),
    Input("scroll-to-radar-indicator", "n_clicks"),
    prevent_initial_call=True
)


# --- Clustering K-Means Callback ---
@callback(
    [Output('cluster-chart', 'figure'),
     Output('cluster-chart', 'style'),
     Output('cluster-main-grid', 'style'),
     Output('cluster-placeholder', 'style'),
     Output('cluster-reading-guide', 'children'),
     Output('cluster-dynamic-title', 'children')],
    [Input('sidebar-filter-social', 'value'), 
     Input('sidebar-filter-offre', 'value'), 
     Input('sidebar-filter-env', 'value'),
     Input('sidebar-epci-radar', 'value'),
     Input('map-indic-select', 'value'), Input('map-patho-select', 'value')]
)
def update_cluster(social, offre, env, epci_codes, ind, patho):
    target = f"{ind}_{patho}"
    if target not in gdf_merged.columns and target == 'INCI_CNR' and 'Taux_CNR' in gdf_merged.columns: 
        target = 'Taux_CNR'
    
    # 1. Sélectionner les variables actives pour le clustering
    selected_vars = [target] + (social or []) + (offre or []) + (env or [])
    # Garder uniquement les valeurs uniques tout en préservant l'ordre
    seen = set()
    selected_vars = [x for x in selected_vars if not (x in seen or seen.add(x))]
    
    # Titre dynamique de l'onglet
    names_str = ""
    if epci_codes:
        names = gdf_merged[gdf_merged['EPCI_CODE'].isin(epci_codes)]['nom_EPCI'].tolist()
        names_str = f" - Position de {', '.join(names)}"
    dynamic_title = f"Profiler de Clustering Territorial (K-Means){names_str}"

    # Si pas assez de variables, on utilise un jeu par défaut intelligent pour que l'onglet ne soit pas vide
    if len(selected_vars) < 2:
        defaults = ['Taux_CNR', 'FDep_2021', 'APL-med_general_2023', 'AIR01']
        selected_vars = [v for v in defaults if v in gdf_merged.columns]

    # Extraction des données d'analyse
    df_cluster = gdf_merged[['EPCI_CODE', 'nom_EPCI'] + selected_vars].copy()
    
    # Gestion des valeurs manquantes (imputation par la médiane de colonne)
    for col in selected_vars:
        if df_cluster[col].isnull().any():
            median_val = df_cluster[col].median()
            df_cluster[col] = df_cluster[col].fillna(median_val if pd.notna(median_val) else 0.0)

    # 2. Normalisation standardisée (Z-score)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_cluster[selected_vars])

    # 3. K-Means (fixé à 4 profils territoriaux pour la clarté opérationnelle)
    n_clusters = 4
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df_cluster['Cluster'] = kmeans.fit_predict(X_scaled)

    # 4. Construction de la figure Plotly (Groupe de Barres des Centroïdes)
    fig = go.Figure()
    cluster_means = []
    labels_z = [variable_dict.get(v, v) for v in selected_vars]
    
    for c in range(n_clusters):
        c_df = df_cluster[df_cluster['Cluster'] == c]
        # Moyenne des Z-scores pour ce cluster spécifique
        c_mean_z = X_scaled[df_cluster['Cluster'] == c].mean(axis=0)
        cluster_means.append(c_mean_z)
        
        fig.add_trace(go.Bar(
            x=labels_z,
            y=c_mean_z,
            name=f"Profil {c + 1} ({len(c_df)} EPCIs)",
            marker_color=MARKER_COLORS[c % len(MARKER_COLORS)]
        ))
        
    fig.update_layout(
        barmode='group',
        xaxis=dict(title="Variables analysées", gridcolor="#e9ecef", tickangle=-15),
        yaxis=dict(title="Écart à la moyenne régionale (Z-Score)", gridcolor="#e9ecef"),
        margin={"t":40,"b":80,"l":40,"r":40},
        height=600,
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    # 5. Identifier le cluster de l'EPCI sélectionné
    selected_epci_code = epci_codes[0] if (epci_codes and len(epci_codes) > 0) else None
    epci_cluster_id = None
    epci_name = ""
    if selected_epci_code:
        row_epci = df_cluster[df_cluster['EPCI_CODE'] == selected_epci_code]
        if not row_epci.empty:
            epci_cluster_id = row_epci['Cluster'].values[0]
            epci_name = row_epci['nom_EPCI'].values[0]

    # 6. Génération narrative des profils et leviers d'action
    cluster_cards = []
    for c in range(n_clusters):
        c_df = df_cluster[df_cluster['Cluster'] == c]
        c_mean_z = cluster_means[c]
        
        # Trouver la dimension la plus forte et la plus faible de ce profil
        idx_high = np.argmax(c_mean_z)
        idx_low = np.argmin(c_mean_z)
        
        var_high = selected_vars[idx_high]
        var_low = selected_vars[idx_low]
        
        label_high = variable_dict.get(var_high, var_high)
        label_low = variable_dict.get(var_low, var_low)
        
        z_high = c_mean_z[idx_high]
        z_low = c_mean_z[idx_low]
        
        # Titre et badge
        is_target_cluster = (epci_cluster_id == c)
        badge = None
        card_style = {
            "padding": "15px", 
            "borderRadius": "8px", 
            "border": "1px solid #dee2e6", 
            "marginBottom": "10px",
            "backgroundColor": "#ffffff",
            "transition": "all 200ms ease"
        }
        
        if is_target_cluster:
            card_style.update({
                "backgroundColor": "#e7f5ff", 
                "borderColor": "#339af0", 
                "borderWidth": "2px",
                "boxShadow": "0 4px 12px rgba(51, 154, 240, 0.15)"
            })
            badge = dmc.Badge(f"Territoire cible : {epci_name}", color="blue", variant="filled", size="sm")
            
        # Recommandations automatiques basées sur la variable la plus critique
        rec = "Renforcer la prévention territoriale générale."
        # Si indicateur de santé très élevé
        if "INCI" in var_high or "MORT" in var_high or "Taux_CNR" in var_high:
            rec = f"🎯 Action Requise : Vulnérabilité cardiovasculaire élevée. Priorité absolue aux parcours de soins coordonnés et à l'éducation thérapeutique."
        # Si précarité sociale très élevée
        elif "FDep" in var_high or "Revenu" in var_low or "Precarite" in var_high:
            rec = f"🤝 Action Sociale : Précarité forte. Mettre en place des actions d'aller-vers et de prévention en santé dans les quartiers prioritaires (QPV) ou zones isolées."
        # Si offre de soins très faible
        elif "APL" in var_low or "Officines" in var_low:
            rec = f"🏥 Offre Médicale : Accès aux soins critique. Soutenir la création de Maisons de Santé Pluriprofessionnelles (MSP) ou l'accueil de internes."
        # Si environnement dégradé
        elif "AIR" in var_high or "BRUIT" in var_high:
            rec = f"🌿 OSE / Environnement : Forte exposition aux nuisances. Articuler les contrats locaux de santé (CLS) avec des plans de réduction des émissions de polluants."

        cluster_cards.append(html.Div(style=card_style, children=[
            dmc.Group([
                dmc.Text(f"Typologie {c + 1} - {len(c_df)} EPCIs", fw=700, size="sm", c=MARKER_COLORS[c % len(MARKER_COLORS)]),
                badge
            ], justify="space-between", mb=6),
            dmc.Text([
                "Description : Valeurs typiquement élevées pour ", 
                dmc.Text(label_high, fw=600, span=True), f" (Z-score moyen = {z_high:+.2f}) et particulièrement faibles pour ",
                dmc.Text(label_low, fw=600, span=True), f" (Z-score moyen = {z_low:+.2f})."
            ], size="xs", c="gray.7", mb=8),
            dmc.Text(rec, size="xs", fw=700, c="blue.8" if is_target_cluster else "gray.8")
        ]))

    # Guide global d'analyse
    guide = dmc.Stack(gap="md", children=[
        dmc.Group([
            dmc.Group([
                html.Div(style={"width":12,"height":12,"backgroundColor":"#e7f5ff","border":"2px solid #339af0","borderRadius":"3px"}), 
                dmc.Text("Territoire sélectionné", size="xs", fw=500)
            ]),
            dmc.Text("Z-Score = 0 représente la moyenne exacte de la région AURA", size="xs", c="dimmed", fs="italic"),
        ], gap="xl"),
        dmc.SimpleGrid(
            cols={"base": 1, "sm": 1},
            spacing="md",
            children=cluster_cards
        )
    ])

    return fig, {'display': 'block', 'height': '600px'}, {'display': 'flex'}, {'display': 'none'}, guide, dynamic_title



