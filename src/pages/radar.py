import dash
from dash import dcc, html, Input, Output, callback, State
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import pandas as pd
from ..data import load_data

gdf_merged, variable_dict, category_dict, sens_dict, _ = load_data()

# Layout — no local filters, everything comes from sidebar
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
                dmc.Title("Radar Comparatif", order=2),
                dmc.ActionIcon(
                    DashIconify(icon="akar-icons:question", width=20),
                    id="radar-guide-btn",
                    size="lg",
                    variant="light",
                    color="blue",
                    radius="md"
                )
            ]
        ),

        # Graph Area
        dmc.Paper(
            withBorder=True,
            shadow="sm",
            radius="md",
            style={"flex": 1, "minHeight": 0},
            children=[
                dcc.Graph(id='radar-chart', style={'height': '100%'})
            ]
        ),

        # Guide Drawer
        dmc.Drawer(
            id="radar-guide-drawer",
            title=dmc.Title("Mode d'emploi - Radar", order=3),
            opened=False,
            padding="md",
            position="right",
            size="md",
            children=[
                dmc.Stack(gap="md", children=[
                    html.Div([
                        dmc.Title("Sélectionnez les variables", order=5, mb="xs"),
                        dmc.Text("Dans le menu gauche, sélectionnez les variables que vous souhaitez ajouter au graphique radar (au moins trois). Les variables ainsi que les EPCI qui avaient déjà été sélectionnés sur la carte restent sélectionnés !", size="sm")
                    ]),
                    html.Div([
                        dmc.Title("Lecture", order=5, mb="xs"),
                        dmc.List(
                            spacing="xs",
                            size="sm",
                            center=True,
                            icon=dmc.ThemeIcon(DashIconify(icon="akar-icons:circle-fill", width=8), radius="xl", color="blue", size=24),
                            children=[
                                dmc.ListItem("Ligne discontinue = Moyenne régionale."),
                                dmc.ListItem("Zone grise = écart type (moyenne des écarts à la moyenne)."),
                                dmc.ListItem("Ligne pleine = Vos territoires."),
                                dmc.ListItem("Si votre ligne sort de la zone grise, l'écart est significatif.")
                            ]
                        )
                    ]),
                    html.Div([
                        dmc.Title("Usages de cet outil", order=5, mb="xs"),
                        dmc.Text("Après avoir identifié les zones à risque grâce à la carte interactive, il peut être intéressant de passer à une analyse plus fine sur ces zones à risque pour mieux les comprendre. Cet outil permet donc :", size="sm", mb="xs"),
                        dmc.List(
                            spacing="sm",
                            size="sm",
                            center=False,
                            icon=dmc.ThemeIcon(DashIconify(icon="akar-icons:check", width=16), radius="xl", color="teal", size=24),
                            children=[
                                dmc.ListItem("D'identifier les forces et faiblesses d'un EPCI en particulier, en comparant les variables sélectionnées pour cet EPCI et la moyenne régionale de ces variables. La zone d'écart type permet de mesurer à quel point la valeur d'une variable pour un EPCI en particulier est éloignée de la valeur moyenne régionale."),
                                dmc.ListItem("De comparer plusieurs EPCI. En sélectionnant plusieurs EPCI, vous pouvez tirer des conclusions sur les forces et faiblesses d'un EPCI en particulier par rapport aux EPCI voisins par exemple, ou aux autres EPCI vulnérables.")
                            ]
                        ),
                        dmc.Text("Cet outil permet donc une analyse plus fine sur les territoires à risques pour mesurer un potentiel \"cumul des vulnérabilités\" sanitaires, sociales, économiques et environnementales. Cet outil peut donc indiquer sur quelles variables en particulier des politiques de prévention pourraient agir.", size="sm", mt="md")
                    ])
                ])
            ]
        )
    ]
)

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
        raw_mean = df[var].mean()
        raw_std = df[var].std()
        
        mn, mx = df[var].min(), df[var].max()
        denom = mx - mn if mx != mn else 1
        
        norm_mean = (raw_mean - mn) / denom
        means.append(norm_mean)
        
        p_std = (raw_mean + raw_std - mn) / denom
        m_std = (raw_mean - raw_std - mn) / denom
        
        plus_std.append(max(0, min(1, p_std)))
        minus_std.append(max(0, min(1, m_std)))
            
    fig = go.Figure()
    theta = [variable_dict.get(v,v) for v in vars_list]
    
    fig.add_trace(go.Scatterpolar(
        r=plus_std, theta=theta,
        mode='lines', line=dict(color='rgba(189, 195, 199, 0.0)'),
        showlegend=False, hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=minus_std, theta=theta,
        mode='lines', line=dict(color='rgba(189, 195, 199, 0.0)'),
        fill='tonext', fillcolor='rgba(189, 195, 199, 0.3)',
        name='Zone Standard (+/- 1σ)', hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=means, theta=theta,
        mode='lines', line=dict(dash='dash', color='rgba(127, 140, 141, 0.8)'),
        name='Moyenne Régionale', hovertemplate="Moyenne: %{r:.2f}<extra></extra>"
    ))
    
    if epci_codes:
        if not isinstance(epci_codes, list):
            epci_codes = [epci_codes]
        
        epci_codes_str = [str(x) for x in epci_codes]
            
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f1c40f']
        df['EPCI_CODE_STR'] = df['EPCI_CODE'].astype(str)
        
        for i, code in enumerate(epci_codes_str):
            row = df[df['EPCI_CODE_STR'] == code]
            if not row.empty:
                name = row['nom_EPCI'].values[0]
                
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
    Output('radar-guide-drawer', 'opened'),
    Input('radar-guide-btn', 'n_clicks'),
    State('radar-guide-drawer', 'opened'),
    prevent_initial_call=True
)
def toggle_radar_guide(n_clicks, opened):
    return not opened
