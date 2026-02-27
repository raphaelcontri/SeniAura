import dash
from dash import dcc, html, Input, Output, callback, ALL, State
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from ..data import load_data

# Load shared data
gdf_merged, variable_dict, category_dict, sens_dict, _ = load_data()

layout = dmc.Container(
    fluid=True,
    p="md",
    style={"height": "100%", "display": "flex", "flexDirection": "column"},
    children=[
        # Header
        dmc.Group(
            justify="space-between",
            pb="md",
            children=[
                dmc.Title("Carte Interactive", order=2),
                dmc.ActionIcon(
                    DashIconify(icon="akar-icons:question", width=20),
                    id="map-guide-btn",
                    size="lg",
                    variant="light",
                    color="blue",
                    radius="md"
                )
            ]
        ),

        dmc.Grid(
            gutter="md",
            style={"flex": 1, "minHeight": 0},
            children=[
                # Local sidebar
                dmc.GridCol(
                    span=3,
                    style={"display": "flex", "flexDirection": "column", "height": "85vh"},
                    children=[
                        dmc.Paper(
                            withBorder=True,
                            shadow="sm",
                            p="md",
                            radius="md",
                            style={"flex": 1, "overflowY": "auto"},
                            children=[
                                dmc.Title("Indicateur de Santé", order=4, mb="sm"),
                                dmc.Select(
                                    id='map-indic-select',
                                    data=[
                                        {'label': 'Incidence', 'value': 'INCI'},
                                        {'label': 'Mortalité', 'value': 'MORT'},
                                        {'label': 'Prévalence', 'value': 'PREV'}
                                    ],
                                    value='INCI',
                                    allowDeselect=False,
                                    mb="sm"
                                ),
                                dmc.Select(
                                    id='map-patho-select',
                                    data=[
                                        {'label': 'AVC', 'value': 'AVC'},
                                        {'label': 'Cardiopathies', 'value': 'CardIsch'},
                                        {'label': 'Insuffisance', 'value': 'InsuCard'}
                                    ],
                                    value='AVC',
                                    allowDeselect=False,
                                    mb="xl"
                                ),
                                
                                dmc.Divider(my="md"),
                                dmc.Title("Plages de filtrage", order=4, mb="sm"),
                                dmc.Text("Ajustez les curseurs pour filtrer les territoires", size="sm", c="dimmed", mb="md"),
                                html.Div(id='map-filter-stats'),
                                html.Div(id='map-dynamic-sliders')
                            ]
                        )
                    ]
                ),

                # Main Map Area
                dmc.GridCol(
                    span=9,
                    style={"height": "85vh"},
                    children=[
                        dmc.Paper(
                            withBorder=True,
                            shadow="sm",
                            radius="md",
                            style={"height": "100%", "position": "relative"},
                            children=[
                                dcc.Loading(
                                    dcc.Graph(id='map-graph', style={'height': '100%', 'width': '100%'}, config={'responsive': True}),
                                    parent_style={'height': '100%'}
                                )
                            ]
                        )
                    ]
                )
            ]
        ),

        # Guide Drawer
        dmc.Drawer(
            id="map-guide-drawer",
            title=dmc.Title("Mode d'emploi - Carte", order=3),
            opened=False,
            padding="md",
            position="right",
            size="md",
            children=[
                dmc.Stack(gap="md", children=[
                    html.Div([
                        dmc.Title("Visualiser des indicateurs", order=5, mb="xs"),
                        dmc.Text("Sélectionnez un indicateur de santé et une pathologie dans le panneau de gauche.", size="sm")
                    ]),
                    html.Div([
                        dmc.Title("Filtrer les territoires", order=5, mb="xs"),
                        dmc.Text("Les filtres (sliders) dans le menu gauche (Socio-Eco, Soins, Env) permettent de restreindre les EPCI affichés. Quand vous modifiez un filtre, les EPCI qui n'appartiennent pas à la nouvelle plage sont grisés. Sélectionnez plusieurs filtres afin de filtrer les EPCI selon plusieurs paramètres.", size="sm")
                    ]),
                    html.Div([
                        dmc.Title("Usages de cet outil", order=5, mb="xs"),
                        dmc.Text("Cet outil permet de raisonner à l'échelle régionale et d'identifier rapidement les EPCI \"à risque\" selon les variables choisies. Cette carte permet ainsi d'avoir une première idée des zones de la région dans lesquelles il serait peut-être intéressant de cibler des politiques de prévention, et dans lesquelles une analyse plus fine pourrait être menée grâce aux profils types et au graphique radar de ce dashboard.", size="sm")
                    ]),
                    html.Div([
                        dmc.Title("Données manquantes", order=5, mb="xs", c="orange"),
                        dmc.Text("Certains territoires n'ont pas de données pour certaines variables. Ils sont indiqués par des marqueurs oranges (X) sur la carte.", size="sm")
                    ]),
                    html.Div([
                        dmc.Title("Astuce !", order=5, mb="xs", c="blue"),
                        dmc.Text("Les filtres sont partagés avec le radar comparatif. Les EPCI peuvent être sélectionnés soit en cliquant sur la carte, soit en les sélectionnant ou en les cherchant dans le menu déroulant du menu gauche.", size="sm")
                    ])
                ])
            ]
        )
    ]
)

# Callbacks

@callback(
    Output('map-dynamic-sliders', 'children'),
    [Input('sidebar-filter-social', 'value'), Input('sidebar-filter-offre', 'value'), Input('sidebar-filter-env', 'value')]
)
def update_sliders(social, offre, env):
    selected = (social or []) + (offre or []) + (env or [])
    controls = []
    for var in selected:
        if var in gdf_merged.columns:
            mn, mx = gdf_merged[var].min(), gdf_merged[var].max()
            
            def fmt(val):
                return f"{val:.0f}" if abs(val) >= 10 else f"{val:.2f}"
            
            controls.append(dmc.Box(mb="xl", children=[
                dmc.Group(justify="space-between", mb="xs", children=[
                    dmc.Text(variable_dict.get(var, var), size="sm", fw=600),
                ]),
                dcc.RangeSlider(
                    id={'type': 'map-slider', 'index': var},
                    min=mn, max=mx, value=[mn, mx],
                    marks={mn: fmt(mn), mx: fmt(mx)},
                    tooltip={"always_visible": True, "placement": "bottom"}
                )
            ]))
    return controls

@callback(
    [Output('map-graph', 'figure'),
     Output('map-filter-stats', 'children')],
    [Input('map-indic-select', 'value'), Input('map-patho-select', 'value'),
     Input({'type': 'map-slider', 'index': ALL}, 'value'),
     Input('sidebar-epci-radar', 'value'),
     Input('sidebar-filter-social', 'value'), Input('sidebar-filter-offre', 'value'), Input('sidebar-filter-env', 'value')],
    State({'type': 'map-slider', 'index': ALL}, 'id')
)
def update_map(ind, patho, slider_vals, epci_selection, social, offre, env, slider_ids):
    target = f"{ind}_{patho}"
    if target not in gdf_merged.columns and target == 'INCI_CNR': target = 'Taux_CNR'
    
    if target not in gdf_merged.columns:
        return go.Figure(), None

    total_epci = len(gdf_merged)
    mask = pd.Series([True] * total_epci)
    exclusion_counts = {}
    nan_exclusion_counts = {}

    if slider_vals:
        for val, id_dict in zip(slider_vals, slider_ids):
            col = id_dict['index']
            if col in gdf_merged.columns:
                 nan_mask = gdf_merged[col].isna()
                 val_mask = gdf_merged[col].between(val[0], val[1])
                 mask &= val_mask
                 exclusion_counts[col] = (total_epci - val_mask.sum()) - nan_mask.sum()
                 nan_exclusion_counts[col] = nan_mask.sum()

    df_focus = gdf_merged[mask].copy()
    df_bg = gdf_merged[~mask]

    selected_vars = (social or []) + (offre or []) + (env or [])
    
    def build_hover(row):
        t_val = row[target]
        t_str = f"{t_val:.0f}" if isinstance(t_val, (int, float)) and abs(t_val) >= 10 else f"{t_val:.2f}"
        
        txt = f"<b>{row['nom_EPCI']}</b><br>"
        txt += f"{variable_dict.get(target, target)}: {t_str}<br>"
        
        if selected_vars:
            txt += "<br><i>Variables sélectionnées :</i><br>"
            for v in selected_vars:
                if v in row:
                    val = row[v]
                    if pd.notna(val):
                        v_str = f"{val:.0f}" if isinstance(val, (int, float)) and abs(val) >= 10 else f"{val:.2f}"
                        label = variable_dict.get(v, v)
                        if len(label) > 30: label = label[:27] + "..."
                        txt += f"{label}: {v_str}<br>"
        return txt

    if not df_focus.empty:
        df_focus['hover_text'] = df_focus.apply(build_hover, axis=1)

    def build_bg_hover(row):
        reasons = []
        if slider_vals:
            for val, id_dict in zip(slider_vals, slider_ids):
                col = id_dict['index']
                if col in gdf_merged.columns:
                    val_col = row[col]
                    if pd.isna(val_col):
                        reasons.append(f"{variable_dict.get(col, col)} (Donnée manquante)")
                    elif not (val[0] <= val_col <= val[1]):
                        v_str = f"{val_col:.0f}" if isinstance(val_col, (int, float)) and abs(val_col) >= 10 else f"{val_col:.2f}"
                        reasons.append(f"{variable_dict.get(col, col)} ({v_str} hors limites)")
        
        txt = f"<b>{row['nom_EPCI']}</b><br>"
        if reasons:
            txt += "<br><i>Exclu car :</i><br>"
            for reason in reasons:
                if len(reason) > 50: reason = reason[:47] + "..."
                txt += f"- {reason}<br>"
        return txt

    if not df_bg.empty:
        df_bg['hover_text'] = df_bg.apply(build_bg_hover, axis=1)

    fig = go.Figure()
    if not df_bg.empty:
        fig.add_trace(go.Choropleth(
            geojson=df_bg.geometry.__geo_interface__, locations=df_bg.index, z=df_bg[target], 
            colorscale="Blues", showscale=False, marker_opacity=0.1, 
            text=df_bg['hover_text'], hovertemplate="%{text}<extra></extra>",
            customdata=df_bg['EPCI_CODE'],
            showlegend=False
        ))
        
        if slider_vals:
            if hasattr(df_bg, 'crs') and df_bg.crs:
                df_bg_4326 = df_bg.to_crs(epsg=4326)
            else:
                df_bg_4326 = df_bg
                
            colors = ['#e74c3c', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c', '#34495e']
            added_to_legend = set()
            
            for i, (val, id_dict) in enumerate(zip(slider_vals, slider_ids)):
                col = id_dict['index']
                if col in df_bg.columns:
                    # Calculate slight horizontal offset (approx 0.05 degrees longitude)
                    offset = (i - len(slider_vals)/2) * 0.05
                    
                    # Case 1: Excluded by value filter
                    mask_val_excluded = ~df_bg[col].isna() & ~df_bg[col].between(val[0], val[1])
                    excluded_by_val = df_bg_4326[mask_val_excluded]
                    
                    if not excluded_by_val.empty:
                        centroids = excluded_by_val.geometry.centroid
                        fig.add_trace(go.Scattergeo(
                            lon=centroids.x + offset, lat=centroids.y,
                            mode='markers',
                            marker=dict(size=7, color=colors[i % len(colors)], symbol='circle', opacity=0.9, line=dict(width=1, color='white')),
                            name=f"{variable_dict.get(col, col)[:25]} (Hors limites)",
                            legendgroup=col,
                            showlegend=col not in added_to_legend,
                            hoverinfo='skip'
                        ))
                        added_to_legend.add(col)

                    # Case 2: Excluded by missing data (nan)
                    mask_nan_excluded = df_bg[col].isna()
                    excluded_by_nan = df_bg_4326[mask_nan_excluded]
                    
                    if not excluded_by_nan.empty:
                        centroids_nan = excluded_by_nan.geometry.centroid
                        fig.add_trace(go.Scattergeo(
                            lon=centroids_nan.x + offset, lat=centroids_nan.y,
                            mode='markers',
                            marker=dict(size=8, color='#ff9800', symbol='x', opacity=0.9),
                            name=f"{variable_dict.get(col, col)[:25]} (Donnée manquante)",
                            legendgroup=f"{col}_nan",
                            showlegend=True,
                            hoverinfo='skip'
                        ))
    
    if not df_focus.empty:
        fig.add_trace(go.Choropleth(
            geojson=df_focus.geometry.__geo_interface__, locations=df_focus.index, z=df_focus[target],
            colorscale="Blues", marker_opacity=1, marker_line_width=1, marker_line_color='white',
            colorbar=dict(title=variable_dict.get(target, target)),
            text=df_focus['hover_text'], hovertemplate="%{text}<extra></extra>",
            customdata=df_focus['EPCI_CODE']
        ))
        
    if epci_selection:
        if not isinstance(epci_selection, list):
            epci_selection = [epci_selection]
            
        epci_selection_str = [str(x) for x in epci_selection]
        hl = gdf_merged[gdf_merged['EPCI_CODE'].astype(str).isin(epci_selection_str)]
        
        if not hl.empty:
            fig.add_trace(go.Choropleth(
                geojson=hl.geometry.__geo_interface__, 
                locations=hl.index, 
                z=[1] * len(hl),
                colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], 
                showscale=False,
                marker_line_width=3, marker_line_color='red',
                marker_opacity=0.1,
                customdata=hl['EPCI_CODE'],
                hovertemplate="<b>%{text}</b> (Sélectionné)<extra></extra>",
                text=hl['nom_EPCI']
            ))    
            
            if hasattr(hl, 'crs') and hl.crs:
                hl_4326 = hl.to_crs(epsg=4326)
            else:
                hl_4326 = hl 
                
            centroids = hl_4326.geometry.centroid
            lats = centroids.y
            lons = centroids.x
            
            fig.add_trace(go.Scattergeo(
                lon=lons, lat=lats,
                mode='markers',
                marker=dict(size=12, color='red', symbol='circle', line=dict(width=2, color='white')),
                text=hl['nom_EPCI'],
                customdata=hl['EPCI_CODE'],
                hoverinfo='text',
                name='Sélection'
            ))

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0}, 
        dragmode=False,
        legend=dict(
            yanchor="bottom", y=0.01,
            xanchor="left", x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
            font=dict(size=11),
            title=dict(text="Exclus par :", font=dict(size=12, color="gray"))
        )
    )

    stats_children = None
    if slider_vals:
        total_excluded = total_epci - mask.sum()
        
        stat_items = []
        for id_dict in slider_ids:
            col = id_dict['index']
            if col in exclusion_counts:
                count_val = exclusion_counts[col]
                count_nan = nan_exclusion_counts.get(col, 0)
                if count_val > 0 or count_nan > 0:
                    label = variable_dict.get(col, col)
                    if len(label) > 30: label = label[:27] + "..."
                    parts = []
                    if count_val > 0: parts.append(f"{count_val} hors limites")
                    if count_nan > 0: parts.append(f"{count_nan} données manquantes")
                    stat_items.append(html.Li(f"{label} : {', '.join(parts)}"))

        if total_excluded > 0:
            stats_children = dmc.Alert(
                title=f"{total_excluded} EPCI exclus sur {total_epci}",
                color="blue",
                variant="light",
                mb="md",
                p="sm",
                children=[
                    html.Ul(stat_items, style={'margin': 0, 'paddingLeft': '20px', 'fontSize': '0.85rem'})
                ]
            )
        else:
            stats_children = dmc.Alert(
                title=f"0 EPCI exclus sur {total_epci}",
                color="green",
                variant="light",
                mb="md",
                p="sm",
            )

    return fig, stats_children

@callback(
    Output('map-guide-drawer', 'opened'),
    Input('map-guide-btn', 'n_clicks'),
    State('map-guide-drawer', 'opened'),
    prevent_initial_call=True
)
def toggle_map_guide(n_clicks, opened):
    return not opened

@callback(
    Output('sidebar-epci-radar', 'value'),
    Input('map-graph', 'clickData'),
    State('sidebar-epci-radar', 'value'),
    prevent_initial_call=True
)
def sync_map_click(clickData, current_selection):
    if not clickData:
        return dash.no_update
        
    try:
        point = clickData['points'][0]
        clicked_epci_code = None
        
        # Priority 1: Check customdata (works for Scattergeo and updated Choropleth)
        if 'customdata' in point:
            clicked_epci_code = point['customdata']
        # Priority 2: Check location index
        elif 'location' in point:
            point_index = point['location']
            clicked_epci_code = gdf_merged.loc[point_index, 'EPCI_CODE']
            
        if clicked_epci_code is None:
            return dash.no_update
            
    except Exception:
        return dash.no_update
    
    # Normalize to string to avoid int/str comparison issues
    clicked_epci_code_str = str(clicked_epci_code)
    
    # Ensure current_selection is a list of strings
    if not current_selection:
        current_selection = []
    if not isinstance(current_selection, list):
        current_selection = [str(current_selection)]
    else:
        current_selection = [str(x) for x in current_selection]
        
    # Toggle selection using set logic for efficiency and safety
    if clicked_epci_code_str in current_selection:
        return [x for x in current_selection if x != clicked_epci_code_str]
    else:
        return current_selection + [clicked_epci_code_str]
