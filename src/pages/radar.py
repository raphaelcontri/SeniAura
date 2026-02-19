import dash
from dash import dcc, html, Input, Output, callback, State
import plotly.graph_objects as go
import pandas as pd
from ..data import load_data

gdf_merged, variable_dict, category_dict, sens_dict, _ = load_data()

# Layout — no local filters, everything comes from sidebar
layout = html.Div(style={'height': '100vh', 'display': 'flex', 'flexDirection': 'column'}, children=[
    html.Div(className='page-header', style={'padding': '15px', 'backgroundColor': '#fff', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}, children=[
        html.H1("Radar Comparatif", style={'margin': 0})
    ]),
    
    # Graph Area
    html.Div(style={'flex': '1', 'padding': '10px', 'overflow': 'hidden', 'minHeight': '0'}, children=[
        dcc.Graph(id='radar-chart', style={'height': '100%'})
    ]),

    # Guide Button & Drawer
    html.Button(id='radar-guide-btn', className='guide-button', children=[html.I(className="fas fa-question")]),
    
    html.Div(id='radar-guide-drawer', className='guide-drawer', children=[
        html.Div(className='guide-header', children=[
            html.H3("Mode d'emploi - Radar"),
            html.Button("×", id='radar-guide-close', className='guide-close')
        ]),
        html.Div(className='guide-content', children=[
            html.H4("Sélectionnez les variables"),
            html.P("Dans le menu gauche, sélectionnez les variables que vous souhaitez ajouter au graphique radar (au moins trois). Les variables ainsi que les EPCI qui avaient déjà été sélectionnés sur la carte restent sélectionnés !"),
            
            html.H4("Lecture"),
            html.Ul([
                html.Li("Ligne discontinue = Moyenne régionale."),
                html.Li("Zone grise = écart type (moyenne des écarts à la moyenne)."),
                html.Li("Ligne pleine = Vos territoires."),
                html.Li("Si votre ligne sort de la zone grise, l'écart est significatif."),
            ]),
            
            html.H4("Usages de cet outil"),
            html.P("Après avoir identifié les zones à risque grâce à la carte interactive, il peut être intéressant de passer à une analyse plus fine sur ces zones à risque pour mieux les comprendre. Cet outil permet donc :"),
            html.Ul([
                html.Li("D'identifier les forces et faiblesses d'un EPCI en particulier, en comparant les variables sélectionnés pour cet EPCI et la moyenne régionnale de ces varaibles. La zone d'écart type permet de mesurer à quel point la valeur d'une variable pour un EPCI en particulier est éloignée de la valeur moyenne régionale."),
                html.Li("De comparer plusieurs EPCI. En sélectionnant plusieurs EPCI, vous pouvez tirer des conclusions sur les forces et faiblesses d'un EPCI en particulier par rapport aux EPCI voisins par exemple, ou aux autres EPCI vulnérables"),
            ]),
            html.P("Cet outil permet donc une analyse plus fine sur les territoires à risques pour mesurer un potentiel \"cumul des vulnérabilités\" sanitaires, sociales, économiques et environnementales. Cet outil peut donc indiquer sur quelles variables en particulier des politiques de prévnetion pourraient agir afin d'améliorer la vulnérabilité sociale, économique et environnementale d'un EPCI. L'outil de profils types peut être aussi utilisé pour analyser plus facilement la situation par groupes d'EPCI et donc faciliter la prise de décisions de mesures de prévention, pour éviter de faire du 'cas par cas'.")
        ])
    ])
])
# Callbacks — use global sidebar IDs

@callback(
    Output('radar-chart', 'figure'),
    [Input('sidebar-epci-radar', 'value'),
     Input('sidebar-filter-social', 'value'),
     Input('sidebar-filter-offre', 'value'),
     Input('sidebar-filter-env', 'value')]
)
def update_radar(epci_codes, social, offre, env):
    vars_list = (social or []) + (offre or []) + (env or [])
    
    if not vars_list or len(vars_list) < 3:
        return go.Figure().update_layout(title="Sélectionnez au moins 3 variables dans la sidebar")
    
    # Calculate stats
    df = gdf_merged.copy()
    
    # Arrays for plotting
    means = []
    plus_std = []
    minus_std = []
    
    for var in vars_list:
        # 1. Global Stats (Raw)
        raw_mean = df[var].mean()
        raw_std = df[var].std()
        
        # 2. Min-Max Normalization Params
        mn, mx = df[var].min(), df[var].max()
        denom = mx - mn if mx != mn else 1
        
        # 3. Normalize Stats
        # Mean
        norm_mean = (raw_mean - mn) / denom
        means.append(norm_mean)
        
        # Std Bounds (clamped 0-1 for display)
        p_std = (raw_mean + raw_std - mn) / denom
        m_std = (raw_mean - raw_std - mn) / denom
        
        plus_std.append(max(0, min(1, p_std)))
        minus_std.append(max(0, min(1, m_std)))
            
    # Plot Logic
    fig = go.Figure()
    
    # Theme settings
    theta = [variable_dict.get(v,v) for v in vars_list]
    
    # 1. Standard Deviation "Tunnel" (Grey Area)
    # Trace for Mean + 1 Std
    fig.add_trace(go.Scatterpolar(
        r=plus_std, theta=theta,
        mode='lines', line=dict(color='rgba(189, 195, 199, 0.0)'), # Invisible line
        showlegend=False, hoverinfo='skip'
    ))
    
    # Trace for Mean - 1 Std (Filled to previous)
    fig.add_trace(go.Scatterpolar(
        r=minus_std, theta=theta,
        mode='lines', line=dict(color='rgba(189, 195, 199, 0.0)'), # Invisible line
        fill='tonext', fillcolor='rgba(189, 195, 199, 0.3)', # Grey fill
        name='Zone Standard (+/- 1σ)', hoverinfo='skip'
    ))
    
    # 2. Regional Mean (Dashed Line)
    fig.add_trace(go.Scatterpolar(
        r=means, theta=theta,
        mode='lines', line=dict(dash='dash', color='rgba(127, 140, 141, 0.8)'),
        name='Moyenne Régionale', hovertemplate="Moyenne: %{r:.2f}<extra></extra>"
    ))
    
    # 3. Selected EPCIs (Loop)
    if epci_codes:
        if not isinstance(epci_codes, list):
            epci_codes = [epci_codes]
        
        # Ensure string comparison
        epci_codes_str = [str(x) for x in epci_codes]
            
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f1c40f']
        
        # Ensure DF uses strings for comparison
        df['EPCI_CODE_STR'] = df['EPCI_CODE'].astype(str)
        
        for i, code in enumerate(epci_codes_str):
            row = df[df['EPCI_CODE_STR'] == code]
            if not row.empty:
                name = row['nom_EPCI'].values[0]
                
                # Calculate normalized values for this EPCI
                vals = []
                for var in vars_list:
                    raw_val = row[var].values[0]
                    mn, mx = df[var].min(), df[var].max()
                    denom = mx - mn if mx != mn else 1
                    vals.append((raw_val - mn) / denom)
                
                color = colors[i % len(colors)]
                fig.add_trace(go.Scatterpolar(
                    r=vals, theta=theta,
                    fill='toself', name=name,
                    line=dict(width=3, color=color)
                ))
        
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])), 
        title="Profil Comparatif (Normalisé)",
        margin=dict(t=40, b=20),
        legend=dict(orientation="h", y=-0.1)
    )

    return fig

# Toggle Guide Drawer
@callback(
    Output('radar-guide-drawer', 'className'),
    [Input('radar-guide-btn', 'n_clicks'), Input('radar-guide-close', 'n_clicks')],
    State('radar-guide-drawer', 'className'),
    prevent_initial_call=True
)
def toggle_radar_guide(n1, n2, current_class):
    if 'guide-drawer-open' in current_class:
        return current_class.replace(' guide-drawer-open', '')
    else:
        return current_class + ' guide-drawer-open'
