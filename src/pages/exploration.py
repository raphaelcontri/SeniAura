import dash
from dash import dcc, html, Input, Output, callback, ALL, State, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import random
from ..data import load_data

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
                                        dmc.Group(
                                            align="stretch", gap="md", mt="sm",
                                            children=[
                                                dmc.Paper(
                                                    withBorder=True, p="md", radius="md", bg="#f8f9fa",
                                                    style={'flex': 1},
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
                                                    withBorder=True, p="md", radius="md", bg="white",
                                                    style={"width": "300px", "display": "none"},
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
                                    dmc.Text("Sélectionnez au moins 2 variables et un territoire pour activer le radar comparatif. La variable d'indicateur de santé sera ajoutée par défaut", size="sm", c="dimmed"),
                                ])
                            )
                        ),
                        dcc.Graph(id='radar-chart', style={'display': 'none', 'flex': 1, 'minHeight': "750px"}, config={'displayModeBar': False, 'staticPlot': False, 'scrollZoom': False}),
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
        try:
            # Try to read Aide.txt (usually in the project root)
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
     Input('highlight-variable-select', 'value')],
    State({'type': 'exploration-slider', 'index': ALL}, 'id')
)
def update_map(ind, patho, slider_vals, epci_selection, highlight_var, slider_ids):
    try:
        # Dynamic Title logic
        indic_map = {'INCI': "l'incidence", 'MORT': "la mortalité", 'PREV': "la prévalence"}
        patho_map = {'AVC': "de l'AVC", 'CardIsch': "de la Cardiopathie Ischémique", 'InsuCard': "de l'insuffisance cardiaque"}
        i_str = indic_map.get(ind, ind)
        p_str = patho_map.get(patho, patho)
        dynamic_title = f"Carte choroplèthe de {i_str} {p_str} en Auvergne-Rhône-Alpes selon les variables sélectionnées"

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
        
        # Build text for background layer
        bg_text = click_instruction + "<b>" + gdf_merged['nom_EPCI'] + "</b>"
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
            fig.add_trace(go.Choropleth(
                geojson=geojson_data,
                locations=df_focus.index.astype(str),
                z=df_focus[target],
                colorscale="Blues",
                marker_line_width=0.5,
                marker_line_color="rgba(255,255,255,0.8)",
                colorbar=dict(thickness=15, len=0.8, y=0.5, x=0.01, xanchor="left", title=unit_dict.get(target, "")),
                hovertemplate=click_instruction + "<b>%{text}</b><br>" + variable_dict.get(target, target) + ": %{z:.2f}<extra></extra>",
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

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            margin={"r":0, "t":0, "l":0, "b":0},
            paper_bgcolor='white', 
            clickmode='event+select',
            dragmode=False # Désactive le panoramique et le zoom par glissement
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
                dmc.Text([
                    "Sur ", dmc.Text(str(total_epci), fw=700, span=True), " EPCI en région AURA, ",
                    dmc.Text(str(inclus), fw=700, c="blue", span=True), " sont inclus par filtres sélectionnés et ",
                    dmc.Text(str(exclus), fw=700, c="red", span=True), " sont exclus."
                ], size="md", c="gray.9")
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
            desc_children.append(dmc.Text([dmc.Text(f"{variable_dict.get(target, target)} (Indicateur Santé) : ", fw=700, span=True), ind_desc], size="sm"))
                
        for s in summaries:
            var_desc = description_dict.get(s['id'], "")
            if not var_desc:
                var_desc = "Description non disponible."
            desc_children.append(dmc.Text([dmc.Text(f"{s['label']} : ", fw=700, span=True), var_desc], size="sm"))
                
        desc_paper = dmc.Paper(
            p="md", withBorder=True, radius="md", bg="blue.0", mb="md",
            children=[
                dmc.Text("Descriptions des variables", fw=700, mb="xs"),
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
    selected_vars_unique = [x for x in selected_vars if not (x in seen or seen.add(x))]
    
    # Revert to original: only show if at least 3 variables are selected
    if len(selected_vars_unique) < 3:
        return go.Figure(), {'display': 'none'}, {'display': 'flex', 'flex': 1}, "", "Radar comparatif par rapport à la moyenne régionale des variables sélectionnées"
    
    selected_vars = selected_vars_unique
    
    names_str = ""
    if epci_codes:
        # Get names from EPCI codes
        names = gdf_merged[gdf_merged['EPCI_CODE'].isin(epci_codes)]['nom_EPCI'].tolist()
        names_str = f" des territoires ({', '.join(names)})"
    
    dynamic_title = f"Radar comparatif{names_str} par rapport à la moyenne régionale des variables sélectionnées"

    if not selected_vars: 
        return go.Figure(), {'display': 'none'}, {'display': 'flex', 'flex': 1}, "", dynamic_title
    
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
        name="Zone d'acceptabilité (écart type)",
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
    
    # Moyenne Région (Normalisée)
    fig.add_trace(go.Scatterpolar(
        r=norm_means, 
        theta=labels, 
        name="Moyenne Région", 
        line=dict(dash='solid', color='#868e96'),
        customdata=[gdf_merged[v].mean() for v in selected_vars],
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
                    r=r_vals_norm, 
                    theta=labels, 
                    fill='toself', 
                    name=row['nom_EPCI'].values[0], 
                    line=dict(color=C[i%len(C)]),
                    customdata=r_vals_raw,
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
        height=700, 
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center")
    )
    # Dynamic Narrative Guide (Advanced Analysis)
    narrative_sections = []
    
    if epci_codes and selected_vars:
        for code in epci_codes:
            row = gdf_merged[gdf_merged['EPCI_CODE'] == code]
            if row.empty: continue
            
            epci_name = row['nom_EPCI'].values[0]
            epci_highlights = []
            
            for v in selected_vars_unique:
                val = row[v].values[0]
                m = gdf_merged[v].mean()
                s = gdf_merged[v].std()
                z = (val - m) / s if s > 0 else 0
                
                # Natural language qualifiers
                if abs(z) < 0.5: 
                    qual = "proche de la moyenne régionale"
                elif z >= 1.5: 
                    qual = "nettement au-dessus de la moyenne régionale"
                elif z >= 0.5:
                    qual = "légèrement au-dessus de la moyenne régionale"
                elif z <= -1.5:
                    qual = "nettement en dessous de la moyenne régionale"
                else: # z <= -0.5
                    qual = "légèrement en dessous de la moyenne régionale"
                
                unit = unit_dict.get(v, "")
                label_name = variable_dict.get(v, v)
                indice_str = f" (indice : {unit})" if unit else ""
                
                epci_highlights.append(dmc.Text([
                    "la variable ", dmc.Text(label_name, fw=800, span=True), 
                    dmc.Text(indice_str, span=True),
                    " est ", dmc.Text(qual, fw=700, c="blue.7", span=True)
                ], span=True))
            
            # Combine highlights for this EPCI
            epci_narrative = [dmc.Text("Pour l'EPCI ", span=True), dmc.Text(epci_name, fw=800, c="blue.9", span=True), " : "]
            for i, h in enumerate(epci_highlights):
                if i > 0:
                    epci_narrative.append(dmc.Text(" et ", span=True))
                epci_narrative.append(h)
            epci_narrative.append(dmc.Text(". ", span=True))
            narrative_sections.append(dmc.Box(epci_narrative, mb=4))
    else:
        narrative_sections = [dmc.Text("Sélectionnez des territoires et des variables pour voir l'analyse.", fs="italic", c="dimmed")]

    guide = dmc.Stack(gap="xs", children=[
        
        dmc.Group(justify="space-between", mb="xs", mt="sm", children=[
            dmc.Group(gap="xs", children=[
                dmc.Text("Interprétations : ", size="lg", fw=800, tt="uppercase", c="dark"),
                dmc.Tooltip(
                    label="L'interprétation des variables ci-dessous est évaluée selon l'écart-type : 'proche de la moyenne régionale' < 0.5 écart type, 'légèrement au dessus / en dessous de la moyenne régionale' de 0.5 écart type à 1.5 écart type, et 'nettement au dessus / en dessous de la moyenne régionale' > 1.5 écart type.",
                    w=300, multiline=True, withArrow=True,
                    children=dmc.ActionIcon(
                        DashIconify(icon="solar:question-circle-linear"),
                        variant="subtle", color="gray", size="sm"
                    )
                )
            ])
        ]),
        dmc.Paper(
            p="md", withBorder=True, radius="md", bg="blue.0",
            children=[
                dmc.Stack(gap=4, children=narrative_sections)
            ]
        )
    ])

    return fig, {'display': 'block', 'flex': 1}, {'display': 'none'}, guide, dynamic_title
