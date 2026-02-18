
import dash
from dash import dcc, html, Input, Output, callback, ALL, State
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from ..data import load_data

# Load shared data
gdf_merged, variable_dict, category_dict, sens_dict = load_data()

layout = html.Div(style={'height': '100vh', 'display': 'flex', 'flexDirection': 'column'}, children=[
    # Header
    html.Div(className='page-header', style={'padding': '15px 20px', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'backgroundColor': '#fff', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}, children=[
        html.H1("Carte Interactive", style={'fontSize': '1.5rem', 'margin': 0}),
    ]),

    html.Div(className='row', style={'flex': '1', 'display': 'flex', 'overflow': 'hidden'}, children=[
        # Local sidebar: map-specific controls
        html.Div(className='local-sidebar', style={'width': '280px', 'overflowY': 'auto', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRight': '1px solid #ddd'}, children=[
            html.Div(className='card', style={'padding': '15px', 'marginBottom': '15px', 'backgroundColor': '#fff', 'borderRadius': '5px', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
                html.H4("Indicateur de Santé", style={'marginTop': 0}),
                dcc.Dropdown(
                    id='map-indic-select',
                    options=[{'label': 'Incidence', 'value': 'INCI'}, {'label': 'Mortalité', 'value': 'MORT'}, {'label': 'Prévalence', 'value': 'PREV'}],
                    value='INCI', clearable=False,
                    style={'marginBottom': '10px'}
                ),
                dcc.Dropdown(
                    id='map-patho-select',
                    options=[{'label': 'AVC', 'value': 'AVC'}, {'label': 'Cardiopathies', 'value': 'CardIsch'}, {'label': 'Insuffisance', 'value': 'InsuCard'}], 
                    value='AVC', clearable=False
                )
            ]),
            html.H4("Plages de filtrage"),
            html.Div(id='map-dynamic-sliders', style={'marginTop': '10px'})
        ]),

        # Main content: Map + Gap Chart side by side
        html.Div(style={'flexGrow': 1, 'display': 'flex', 'flexDirection': 'column', 'overflow': 'hidden'}, children=[
            # Map
            html.Div(style={'flex': '1', 'position': 'relative', 'minHeight': '0'}, children=[
                dcc.Loading(dcc.Graph(id='map-graph', style={'height': '100%', 'width': '100%'}, config={'responsive': True}))
            ]),

        ])
    ]),

    # Guide Button & Drawer
    html.Button(id='map-guide-btn', className='guide-button', children=[html.I(className="fas fa-question")]),
    
    html.Div(id='map-guide-drawer', className='guide-drawer', children=[
        html.Div(className='guide-header', children=[
            html.H3("Mode d'emploi - Carte"),
            html.Button("×", id='map-guide-close', className='guide-close')
        ]),
        html.Div(className='guide-content', children=[
            html.H4("1. Visualiser des indicateurs"),
            html.P("Sélectionnez un indicateur de santé et une pathologie dans le panneau de gauche."),
            
            html.H4("2. Filtrer les territoires"),
            html.P("Les filtres dans la sidebar globale (Socio-Eco, Soins, Env) permettent de restreindre les EPCI affichés."),
            
            html.H4("3. Écart diagnostique"),
            html.P("Le graphique en bas montre les 15 EPCI où l'état de santé est plus mauvais que ce que les variables sélectionnées prédiraient. Un écart élevé = territoire prioritaire pour la prévention."),
            
            html.H4("4. Synchronisation"),
            html.P("Les filtres sont partagés avec le Radar Comparatif.")
        ])
    ])
])


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
            p05 = gdf_merged[var].quantile(0.05)
            p95 = gdf_merged[var].quantile(0.95)
            
            # Helper to format numbers nicely
            def fmt(val):
                return f"{val:.0f}" if abs(val) >= 10 else f"{val:.2f}"
            
            # Create marks with float keys to ensure they appear correctly
            marks = {
                mn: {'label': fmt(mn), 'style': {'color': '#bdc3c7', 'fontSize': '0.7rem'}},
                mx: {'label': fmt(mx), 'style': {'color': '#bdc3c7', 'fontSize': '0.7rem'}},
                p05: {'label': '5%', 'style': {'color': '#e67e22', 'fontWeight': 'bold', 'fontSize': '0.8rem'}},
                p95: {'label': '95%', 'style': {'color': '#e67e22', 'fontWeight': 'bold', 'fontSize': '0.8rem'}}
            }
            
            controls.append(html.Div([
                html.Div([
                    html.Label(variable_dict.get(var, var), style={'fontSize': '0.85rem', 'fontWeight': '600'}),
                    html.Span(f" (Q5: {fmt(p05)} - Q95: {fmt(p95)})", style={'fontSize': '0.75rem', 'color': '#7f8c8d'})
                ], style={'display':'flex', 'justifyContent':'space-between', 'alignItems':'baseline'}),
                
                dcc.RangeSlider(
                    id={'type': 'map-slider', 'index': var},
                    min=mn, max=mx, value=[mn, mx],
                    marks=marks,
                    tooltip={"always_visible": True, "placement": "bottom"}
                )
            ], style={'marginBottom': '20px'}))
    return controls

@callback(
    Output('map-graph', 'figure'),
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
        return go.Figure()

    mask = pd.Series([True] * len(gdf_merged))
    if slider_vals:
        for val, id_dict in zip(slider_vals, slider_ids):
            col = id_dict['index']
            if col in gdf_merged.columns:
                 mask &= gdf_merged[col].between(val[0], val[1])

    df_focus = gdf_merged[mask]
    df_bg = gdf_merged[~mask]

    fig = go.Figure()
    if not df_bg.empty:
        fig.add_trace(go.Choropleth(geojson=df_bg.geometry.__geo_interface__, locations=df_bg.index, z=df_bg[target], colorscale="Blues", showscale=False, marker_opacity=0.1, hoverinfo='skip'))
    
    if not df_focus.empty:
        fig.add_trace(go.Choropleth(
            geojson=df_focus.geometry.__geo_interface__, locations=df_focus.index, z=df_focus[target],
            colorscale="Blues", marker_opacity=1, marker_line_width=1, marker_line_color='white',
            colorbar=dict(title=variable_dict.get(target, target)),
            text=df_focus['nom_EPCI'], hovertemplate="<b>%{text}</b><br>Val: %{z:.2f}<extra></extra>"
        ))
        
    # Highlight Selected EPCIs from Radar (Red Point)
    if epci_selection:
        if not isinstance(epci_selection, list):
            epci_selection = [epci_selection]
            
        # Ensure codes are strings for comparison to avoid int/str mismatch
        epci_selection_str = [str(x) for x in epci_selection]
        
        # Filter (casting df column to str safely)
        hl = gdf_merged[gdf_merged['EPCI_CODE'].astype(str).isin(epci_selection_str)]
        
        if not hl.empty:
            # 1. Overlay with Red Outline
            # Use a dummy Z and transparent scale to only show outline
            fig.add_trace(go.Choropleth(
                geojson=hl.geometry.__geo_interface__, 
                locations=hl.index, 
                z=[1] * len(hl),
                colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], 
                showscale=False,
                marker_line_width=3, marker_line_color='red',
                marker_opacity=0.1, # Slight fill to ensure clickable?
                hoverinfo='skip'
            ))    
            
            # 2. Add Red Dot at Centroid
            # CRITICAL: Ensure we use Lat/Lon (EPSG:4326)
            # If gdf is projected (e.g. 2154), centroids will be invalid for Scattergeo.
            # We reproject the geometry to 4326 before taking centroid.
            
            # Check if crs is defined, otherwise assume we need to convert if context implies it.
            # Safe bet: to_crs(4326) if has crs.
            if hasattr(hl, 'crs') and hl.crs:
                hl_4326 = hl.to_crs(epsg=4326)
            else:
                hl_4326 = hl # Hope it's already 4326 or no CRS
                
            centroids = hl_4326.geometry.centroid
            lats = centroids.y
            lons = centroids.x
            
            fig.add_trace(go.Scattergeo(
                lon=lons, lat=lats,
                mode='markers',
                marker=dict(size=12, color='red', symbol='circle', line=dict(width=2, color='white')),
                text=hl['nom_EPCI'],
                hoverinfo='text',
                name='Sélection'
            ))



    # Highlight top-10 gap EPCIs in orange on the map
    selected_vars = (social or []) + (offre or []) + (env or [])
    if selected_vars and target in gdf_merged.columns:
        valid_vars = [v for v in selected_vars if v in gdf_merged.columns]
        if valid_vars:
            df_gap = gdf_merged[['nom_EPCI', target] + valid_vars].dropna().copy()
            if len(df_gap) >= 5:
                # Health Rank: Always High = Bad
                health_rank = df_gap[target].rank(ascending=True, pct=True)
                
                # Context Rank: Depend on Sens
                # Sens 1 (High=Good) -> Rank Ascending False (High=0=Good, Low=1=Bad)
                # Sens -1 (High=Bad) -> Rank Ascending True (High=1=Bad, Low=0=Good)
                context_ranks = []
                for v in valid_vars:
                    sens = sens_dict.get(v, -1)
                    asc = True if sens == -1 else False
                    context_ranks.append(df_gap[v].rank(ascending=asc, pct=True))
                
                composite_rank = pd.concat(context_ranks, axis=1).mean(axis=1)
                
                df_gap['gap'] = health_rank - composite_rank
                top_gap = df_gap.nlargest(10, 'gap')
                top_idx = top_gap.index
                hl_gap = gdf_merged.loc[top_idx]
                if not hl_gap.empty:
                    fig.add_trace(go.Choropleth(
                        geojson=hl_gap.geometry.__geo_interface__, locations=hl_gap.index,
                        z=[1]*len(hl_gap),
                        colorscale=[[0, 'rgba(230,126,34,0.15)'], [1, 'rgba(230,126,34,0.15)']],
                        showscale=False,
                        marker_line_width=4, marker_line_color='#e67e22',
                        text=hl_gap['nom_EPCI'],
                        hovertemplate="<b>%{text}</b><br>⚠️ Écart diagnostique élevé<extra></extra>"
                    ))

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, dragmode=False)
    return fig


# Diagnostic Gap Chart



# Toggle Guide Drawer
@callback(
    Output('map-guide-drawer', 'className'),
    [Input('map-guide-btn', 'n_clicks'), Input('map-guide-close', 'n_clicks')],
    State('map-guide-drawer', 'className'),
    prevent_initial_call=True
)
def toggle_map_guide(n1, n2, current_class):
    if 'guide-drawer-open' in current_class:
        return current_class.replace(' guide-drawer-open', '')
    else:
        return current_class + ' guide-drawer-open'

# Sync Map Click -> Radar Selection (Multi)
@callback(
    Output('sidebar-epci-radar', 'value'),
    Input('map-graph', 'clickData'),
    State('sidebar-epci-radar', 'value'),
    prevent_initial_call=True
)
def sync_map_click(clickData, current_selection):
    if not clickData:
        return dash.no_update
        
    # Get clicked EPCI code (location id)
    # Ensure geojson id is mapped to dataframe index which is EPCI code or Name?
    # In update_map: locations=df.index. df is indexed by default?
    # Let's check update_map again. 
    # df_bg = gdf_merged[~mask]. 
    # locations=df_bg.index. 
    # gdf_merged index is RangeIndex usually unless set.
    # WAIT. choropleth `locations` matches `feature.id`. 
    # In load_data, gdf_merged is a merge of gdf_epci and df.
    # We didn't set index to EPCI_CODE.
    # We need to verify what `locations` receives. 
    # If standard RangeIndex, clickData provides that index.
    # We need to retrieve the EPCI Code from that index.
    
    # Better approach: In update_map, we should check what is passed to locations.
    # `locations=df_focus.index`.
    # If index is just numbers 0..N, then we look up gdf_merged.iloc[clicked_point_index]['EPCI_CODE'].
    
    point_index = clickData['points'][0]['location']
    
    # Retrieve the row from the GLOBAL gdf_merged using this index
    # (Assuming gdf_merged index hasn't been shuffled/reset in a way that breaks this)
    # gdf_merged is static from load_data.
    
    clicked_epci_code = gdf_merged.loc[point_index, 'EPCI_CODE']
    
    # Update selection
    if not current_selection:
        return [clicked_epci_code]
    
    if isinstance(current_selection, list):
        if clicked_epci_code not in current_selection:
            return current_selection + [clicked_epci_code]
        else:
            # Optional: toggle behavior (remove if clicking again?)
            # User said "Select multiple", didn't specify toggle. Let's append only.
            return dash.no_update
    else:
        # Should be a list since we set multi=True, but initial state might be None or str if legacy
        if clicked_epci_code != current_selection:
            return [current_selection, clicked_epci_code]
            
    return dash.no_update
