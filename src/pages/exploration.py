import dash
from dash import dcc, html, Input, Output, callback, ALL, State, no_update, clientside_callback, ClientsideFunction
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import random
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

# Save department boundaries to assets once at startup to optimize transfer
import json
import os
assets_dep_path = "assets/departments-ara.geojson"
if not os.path.exists(assets_dep_path):
    try:
        with open(assets_dep_path, "w", encoding="utf-8") as f:
            json.dump(geojson_deps, f)
    except Exception as e:
        print(f"Error saving departments geojson: {e}")

MARKER_COLORS = ['#e03131', '#1971c2', '#2b8a3e', '#e67700', '#9c36b5', '#0b7285', '#5c940d', '#d9480f']

THEME_METADATA = {
    'sante': {
        'label': "Profil Épidémiologique & Santé",
        'badge_color': "red",
        'vars': ['INCI_AVC', 'INCI_CardIsch', 'INCI_InsuCard', 'MORT_AVC', 'MORT_CardIsch', 'MORT_InsuCard', 'PREV_AVC', 'PREV_CardIsch', 'PREV_InsuCard']
    },
    'socio': {
        'label': "Déterminants Socio-Économiques",
        'badge_color': "teal",
        'vars': ['FDep_2021', 'MED_SL', 'PR_MD60', 'Part de personnes isolées 60 ans et plus', 'Taux de chomeurs_2022']
    },
    'offre': {
        'label': "Offre de Soins & Accessibilité",
        'badge_color': "blue",
        'vars': ['APL-med_general_2023', 'APL_Cardio_EPCI', 'Officines_2025', 'Centres_Sante_2025', 'Maisons_Sante_2025']
    },
    'env': {
        'label': "Exposition Environnementale",
        'badge_color': "green",
        'vars': ['AIR01', 'AIR02', 'BRUIT01', 'BRUIT02']
    }
}

CLUSTER_COLORS = ['#e03131', '#ff922b', '#fcc419', '#51cf66'] # Rouge, Orange, Jaune, Vert

THEME_INTERPRETATIONS = {
    'sante': {
        0: {
            'title': "Surtaux Généralisé & Alerte Clinique",
            'desc': "Territoires caractérisés par des taux d'incidence, de mortalité et de prévalence cardiovasculaire nettement supérieurs à la moyenne régionale. Ce profil regroupe des populations âgées ou à fort passé industriel.",
            'rec': "🎯 Action Clinique : Dépistage massif hors-les-murs, éducation thérapeutique renforcée (ETP) et coordination resserrée des parcours de soins cardiologiques.",
            'hash': 'sante'
        },
        1: {
            'title': "Incidence Forte avec Performance Clinique",
            'desc': "Forte survenue de pathologies cardiaques aiguës (AVC, cardiopathie) mais taux de mortalité bas. Cela démontre une excellente performance de la filière locale des urgences et de la réanimation.",
            'rec': "🏥 Recommandation : Pérenniser le soutien aux services d'urgence et consolider le maillage en lits de soins intensifs de cardiologie.",
            'hash': 'sante'
        },
        2: {
            'title': "Vulnérabilité Chronique Émergente",
            'desc': "Prévalence élevée combinée à une mortalité modérée. Ce profil abrite une part de patients vivant avec des pathologies cardiovasculaires chroniques stabilisées.",
            'rec': "🤝 Recommandation : Renforcer l'accompagnement à domicile, le rôle des infirmières en pratique avancée (IPA) et la télésurveillance cardiaque.",
            'hash': 'sante'
        },
        3: {
            'title': "Préservation & Protection Cardiovasculaire",
            'desc': "Territoires présentant des taux de pathologies très inférieurs à la moyenne régionale. Ce profil regroupe généralement des populations actives ou périurbaines bénéficiant d'un excellent capital santé.",
            'rec': "🌿 Recommandation : Maintenir la promotion de modes de vie actifs, d'une alimentation saine et pérenniser les campagnes de prévention primaire.",
            'hash': 'sante'
        }
    },
    'socio': {
        0: {
            'title': "Précarité Cumulative & Isolement",
            'desc': "Territoires associant un niveau de vie très bas, un indice de précarité FDep élevé et une forte proportion de seniors isolés. Risque majeur de renoncement aux soins par manque de ressources.",
            'rec': "🤝 Action Sociale : Déployer des actions d'aller-vers, renforcer la médiation en santé et soutenir les centres communaux d'action sociale (CCAS).",
            'hash': 'socio'
        },
        1: {
            'title': "Disparités Urbaines Denses",
            'desc': "Territoires à forte densité de population caractérisés par des poches de chômage important, coexistant avec des zones plus aisées (métropoles).",
            'rec': "🎯 Recommandation : Cibler les actions de prévention en santé dans les Quartiers de la Politique de la Ville (QPV) et les foyers de travailleurs.",
            'hash': 'socio'
        },
        2: {
            'title': "Ruralité Isolée en Transition",
            'desc': "Chômage faible et revenus intermédiaires, mais marqué par un fort vieillissement de la population. L'isolement est ici principalement physique et géographique.",
            'rec': "🏥 Recommandation : Développer les navettes de santé solidaires et les services de télémédecine en mairies rurales pour lutter contre l'isolement.",
            'hash': 'socio'
        },
        3: {
            'title': "Périurbanisation Aisée & Dynamique",
            'desc': "Hauts revenus, chômage quasi-nul et population active. Ces territoires bénéficient d'un excellent capital socio-économique protecteur.",
            'rec': "🌿 Recommandation : Développer l'offre d'activités physiques de loisir et promouvoir le bien-être au travail en lien avec les entreprises locales.",
            'hash': 'socio'
        }
    },
    'offre': {
        0: {
            'title': "Désertification Médicale Critique",
            'desc': "Accessibilité aux généralistes (APL) très défavorable et temps d'accès aux services d'urgence supérieur à la moyenne régionale. Risque fort de retards de diagnostic.",
            'rec': "🏥 Offre de Soins : Soutenir l'installation de Maisons de Santé Pluriprofessionnelles (MSP) et encourager le déploiement de cabines de téléconsultation.",
            'hash': 'sante'
        },
        1: {
            'title': "Ruralité Fragile sous Vigilance",
            'desc': "Accès de premier recours (médecins traitants) modéré mais absence marquée de spécialistes de second recours et d'officines de pharmacie de proximité.",
            'rec': "💊 Recommandation : Favoriser les regroupements de professionnels en CPTS et soutenir les officines rurales comme relais de premier secours.",
            'hash': 'sante'
        },
        2: {
            'title': "Périurbain Médicalement Dépendant",
            'desc': "Excellente densité de médecins généralistes locaux mais temps d'accès aux urgences hospitalières élevé. Dépendance forte envers les métropoles voisines.",
            'rec': "🚑 Recommandation : Consolider la formation des secouristes locaux (pompiers) et renforcer les protocoles de premier accueil urgences en MSP.",
            'hash': 'sante'
        },
        3: {
            'title': "Hyper-concentration & Métropolisation",
            'desc': "Accessibilité exceptionnelle à l'ensemble des professionnels de santé (généralistes, spécialistes), présence immédiate de cliniques et d'un CHU.",
            'rec': "🔬 Recommandation : Développer les projets de recherche clinique territoriale et optimiser la régulation pour désengorger les urgences hospitalières.",
            'hash': 'sante'
        }
    },
    'env': {
        0: {
            'title': "Expositions Multiples & Couloirs Routiers",
            'desc': "Concentrations élevées de PM2.5/NO2 associées à de fortes nuisances sonores. Profil typique des grandes vallées alpines circulatoires ou du couloir rhodanien.",
            'rec': "🌿 Environnement : Articuler les contrats locaux de santé (CLS) avec des plans de réduction des émissions de polluants et des zones à faibles émissions (ZFE).",
            'hash': 'env'
        },
        1: {
            'title': "Pollution Urbaine Diffuse",
            'desc': "Exposition importante de fond aux particules fines PM2.5 en zone dense liée aux systèmes de chauffage et au trafic urbain, nuisances sonores directes modérées.",
            'rec': "🔥 Recommandation : Accélérer la transition énergétique des modes de chauffage individuels (rénovation énergétique) et promouvoir les transports en commun.",
            'hash': 'env'
        },
        2: {
            'title': "Vallées Encaissées & Chauffage Biomasse",
            'desc': "Qualité de l'air de fond excellente, sauf en hiver où des inversions thermiques retiennent les polluants issus du chauffage au bois individuel.",
            'rec': "🪵 Recommandation : Subventionner le renouvellement des anciens poêles à bois et sensibiliser les populations aux bonnes pratiques de combustion.",
            'hash': 'env'
        },
        3: {
            'title': "Préservation Environnementale Haute",
            'desc': "Qualité de l'air exceptionnelle et silence acoustique total. Communes de moyenne et haute montagne offrant un environnement protecteur majeur.",
            'rec': "⛰️ Recommandation : Valoriser le label 'Air Pur' et développer des sentiers sport-santé tirant parti de cette qualité environnementale.",
            'hash': 'env'
        }
    }
}

layout = dmc.Container(
    fluid=True,
    p=0,
    style={"display": "flex", "flexDirection": "column", "gap": "15px"},
    children=[
        # Main Interface
        html.Div(
            id='exploration-main-container',
            style={"display": "flex", "flexDirection": "column", "gap": "20px"},
            children=[
                # Map Section
                dmc.Paper(
                    id='container-map',
                    withBorder=True, shadow="sm", p="md", radius="md",
                    style={"minHeight": "600px"},
                    children=[
                        dmc.Group(justify="space-between", mb="md", children=[
                            dmc.Group(gap="xs", children=[
                                DashIconify(icon="solar:map-linear", color="#339af0"),
                                dmc.Text("Carte ", id='map-dynamic-title', fw=700),
                            ]),
                            dmc.Tooltip(
                                label="Nous avons réalisé les analyses nécessaires démontrant qu'il est possible d'étendre cette étude à d'autres régions françaises. Vous pouvez retrouver l'ensemble des variables requises pour cette extension nationale en consultant la FAQ sur la page d'accueil !",
                                multiline=True,
                                w=300,
                                withArrow=True,
                                children=dmc.Badge(
                                    "Extension nationale possible",
                                    color="teal",
                                    variant="light",
                                    size="sm",
                                    radius="md",
                                    style={"cursor": "pointer"}
                                )
                            ),
                        ]),
                        dmc.Box(
                            mb="md",
                            children=[
                                dmc.Group(
                                    gap="xs", mb=5, align="center", wrap="nowrap",
                                    children=[
                                        DashIconify(icon="solar:map-point-bold", width=18, color="#339af0"),
                                        dmc.Text("Territoires EPCI à analyser ou comparer", fw=700, size="sm", c="#2c3e50"),
                                        dmc.Tooltip(
                                            multiline=True, w=250, withArrow=True,
                                            label="Sélectionnez des EPCI via ce menu ou en cliquant directement sur la carte pour les analyser sur le radar comparatif.",
                                            children=dmc.ActionIcon(DashIconify(icon="akar-icons:question", width=14), size="xs", variant="subtle", color="gray")
                                        )
                                    ]
                                ),
                                dmc.MultiSelect(
                                    id='sidebar-epci-radar',
                                    data=[{'label': n, 'value': c} for n, c in zip(gdf_merged['nom_EPCI'], gdf_merged['EPCI_CODE']) if pd.notnull(n)],
                                    placeholder="Choisir EPCI...",
                                    searchable=True,
                                    clearable=True,
                                    radius="md",
                                    comboboxProps={"withinPortal": True, "dropdownPosition": "bottom", "shadow": "xl", "transitionProps": {"transition": "pop-top-left", "duration": 200}, "offset": 7},
                                    styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}}
                                ),
                            ]
                        ),
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
                                            style={'height': "550px", "width": "100%", "borderRadius": "inherit"}, 
                                            config={
                                                'displayModeBar': False, 
                                                'scrollZoom': False,
                                                'doubleClick': False,
                                                'showTips': False
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
                                            style={'minHeight': '550px', 'maxHeight': '550px', 'overflowY': 'auto'},
                                            children=[
                                                dmc.Group(justify="space-between", mb="xs", children=[
                                                    dmc.Text("INTERPRETATIONS", size="lg", fw=800, c="dark"),
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
                                                        renderOption={"function": "renderVariableOptionWithTooltip"}
                                                    )
                                                ])
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),
                        dmc.Space(h="xs"),
                        html.Div(
                            id="scroll-to-radar-indicator",
                            className="scroll-indicator-container",
                            style={
                                "display": "flex", 
                                "flexDirection": "column", 
                                "alignItems": "flex-start", 
                                "cursor": "pointer",
                                "opacity": 0.9,
                                "marginTop": "5px",
                                "width": "fit-content",
                                "transformOrigin": "left center"
                            },
                            n_clicks=0,
                            children=[
                                dmc.Button(
                                    "Poursuivre l'Analyse",
                                    color="red",
                                    radius="md",
                                    className="bounce",
                                    rightSection=DashIconify(icon="solar:alt-arrow-down-linear", width=16)
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
                        dmc.Group(justify="space-between", mb="md", children=[
                            dmc.Group(gap="xs", children=[
                                DashIconify(icon="solar:chart-2-linear", color="#339af0"),
                                dmc.Text("Profil Comparatif Radar", id='radar-dynamic-title', fw=700),
                            ]),
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
            
            # Retrieve category, description, polarity to format tooltip
            cat = category_dict.get(var, "")
            friendly_cat = "Socio-Économie" if "socio" in cat.lower() else (
                "Offre de Soins" if "soins" in cat.lower() or "offre" in cat.lower() else (
                    "Environnement" if "env" in cat.lower() else (
                        "Santé" if "sant" in cat.lower() else cat.capitalize()
                    )
                )
            )
            desc = description_dict.get(var, "Description non disponible.")
            sens = sens_dict.get(var, 0)
            if sens == 1:
                sens_msg = " (Plus cette variable est élevée, moins le territoire est vulnérable)"
            elif sens == -1:
                sens_msg = " (Plus cette variable est élevée, plus le territoire est vulnérable)"
            else:
                sens_msg = ""
            
            tooltip_text = f"{label_var} (Indicateur {friendly_cat}) : {desc}{sens_msg}"
            
            sliders.append(dmc.Box(mb=8, px=0, children=[
                dmc.Group(
                    gap="xs", align="center", mb=2, wrap="nowrap",
                    children=[
                        dmc.Text(label_full, size="10px", fw=600, c="dimmed"),
                        dmc.Tooltip(
                            label=tooltip_text,
                            multiline=True,
                            w=260,
                            withArrow=True,
                            children=dmc.ActionIcon(
                                DashIconify(icon="solar:info-circle-linear", width=14),
                                size="xs",
                                variant="subtle",
                                color="gray"
                            )
                        )
                    ]
                ),
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
     Input('sidebar-filter-env', 'value')],
    [State('url', 'pathname')]
)
def update_highlight_options(social, offre, env, pathname):
    if pathname not in ['/exploration', '/carte', '/radar']:
        raise dash.exceptions.PreventUpdate
    all_vars = (social or []) + (offre or []) + (env or [])
    if not all_vars: return []
    
    options = []
    for v in all_vars:
        if v not in variable_dict: continue
        label = variable_dict[v]
        cat_raw = category_dict.get(v, "")
        friendly_cat = "Socio-Économie" if "socio" in cat_raw.lower() else (
            "Offre de Soins" if "soins" in cat_raw.lower() or "offre" in cat_raw.lower() else (
                "Environnement" if "env" in cat_raw.lower() else (
                    "Santé" if "sant" in cat_raw.lower() else cat_raw.capitalize()
                )
            )
        )
        desc = description_dict.get(v, "Description non disponible.")
        sens = sens_dict.get(v, 0)
        if sens == 1:
            sens_msg = " (Plus cette variable est élevée, moins le territoire est vulnérable)"
        elif sens == -1:
            sens_msg = " (Plus cette variable est élevée, plus le territoire est vulnérable)"
        else:
            sens_msg = ""
        tooltip_text = f"{label} (Indicateur {friendly_cat}) : {desc}{sens_msg}"
        options.append({'label': label, 'value': v, 'tooltip': tooltip_text})
    return options

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
     Input('show-hospitals-switch', 'checked'),
     Input('url', 'pathname')],
    [State({'type': 'exploration-slider', 'index': ALL}, 'id')]
)
def update_map(ind, patho, slider_vals, epci_selection, highlight_var, show_hospitals, pathname, slider_ids):
    if pathname not in ['/exploration', '/carte', '/radar']:
        raise dash.exceptions.PreventUpdate
    try:
        click_instruction = "<i>Cliquez sur cet EPCI pour l'ajouter au radar chart et au profiler</i><br><br>"
        total_epci = len(gdf_merged)
        
        # Demographic Context for Tooltips
        demo_text_series = pd.Series([""] * total_epci, index=gdf_merged.index)
        if 'H_65_plus' in gdf_merged.columns and 'F_65_plus' in gdf_merged.columns:
             demo_h = gdf_merged['H_65_plus'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
             demo_f = gdf_merged['F_65_plus'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
             demo_text_series = "<br><span style='font-size: 11.5px;'>👨 Hommes 65+ : <b>" + demo_h + "</b>  |  👩 Femmes 65+ : <b>" + demo_f + "</b></span>"

        # ----------------------------------------------------
        # STANDARD DISEASE CHLOROPLETH MAP MODE
        # ----------------------------------------------------
        indic_map = {'INCI': "l'incidence", 'MORT': "la mortalité", 'PREV': "la prévalence"}
        patho_map = {'AVC': "de l'AVC", 'CardIsch': "de la Cardiopathie Ischémique", 'InsuCard': "de l'insuffisance cardiaque"}
        
        # Vérification si l'indicateur sélectionné est un indicateur utilisateur direct
        if ind in gdf_merged.columns:
            target = ind
            dynamic_title = f"Carte de l'indicateur : {variable_dict.get(ind, ind)}"
        else:
            i_str = indic_map.get(ind, ind)
            p_str = patho_map.get(patho, patho)
            dynamic_title = f"Carte de {i_str} {p_str} en Auvergne-Rhône-Alpes"
            target = f"{ind}_{patho}"
            if target not in gdf_merged.columns and target == 'INCI_CNR': target = 'Taux_CNR'

        if target not in gdf_merged.columns: return go.Figure(), "Indicateur non trouvé", "", "", dynamic_title

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

        # Build text for background layer
        bg_text = click_instruction + "<b>" + gdf_merged['nom_EPCI'] + "</b>" + demo_text_series
        has_exclusion = exclusion_reasons != ""
        bg_text_with_reasons = bg_text.copy()
        bg_text_with_reasons.loc[has_exclusion] += "<br><span style='font-size: 11px; color: #e03131'>Grisé par :</span>" + exclusion_reasons.loc[has_exclusion]

        # 1. Background layer (All territories) - Using ID for robust mapping
        fig.add_trace(go.Choropleth(
            geojson="/assets/epci-ara-simplified.geojson",
            featureidkey="properties.EPCI_CODE",
            locations=gdf_merged['EPCI_CODE'].astype(str),
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
                geojson="/assets/epci-ara-simplified.geojson",
                featureidkey="properties.EPCI_CODE",
                locations=df_focus['EPCI_CODE'].astype(str),
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
        dep_locations = (
            gdf_deps_4326['DEPARTEMEN'].astype(str) 
            if 'DEPARTEMEN' in gdf_deps_4326.columns 
            else gdf_deps_4326.index.astype(str)
        )
        fig.add_trace(go.Choropleth(
            geojson="/assets/departments-ara.geojson",
            featureidkey="properties.DEPARTEMEN",
            locations=dep_locations,
            z=[0] * len(gdf_deps_4326),
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
            showscale=False,
            marker_line_width=1.5,
            marker_line_color='rgba(0,0,0,0.6)',
            hoverinfo='skip'
        ))

        # 4. Highlight Exclusion (Specific Variable)
        if highlight_var:
            slider_indices = [i for i, d in enumerate(slider_ids) if d['index'] == highlight_var]
            if slider_indices:
                idx = slider_indices[0]
                val = slider_vals[idx]
                excluded_by_var = ~gdf_merged[highlight_var].between(val[0], val[1])
                df_excl_highlight = gdf_merged[excluded_by_var].copy()
                
                if not df_excl_highlight.empty:
                    fig.add_trace(go.Choropleth(
                        geojson="/assets/epci-ara-simplified.geojson",
                        featureidkey="properties.EPCI_CODE",
                        locations=df_excl_highlight['EPCI_CODE'].astype(str),
                        z=[1] * len(df_excl_highlight),
                        colorscale=[[0, '#adb5bd'], [1, '#adb5bd']],
                        showscale=False,
                        marker_line_width=1,
                        marker_line_color='rgba(0,0,0,0.3)',
                        hovertemplate=click_instruction + "<b>%{text}</b><br>Grisé par : " + variable_dict.get(highlight_var, highlight_var) + "<extra></extra>",
                        text=df_excl_highlight['nom_EPCI'],
                        name=f"Exclu par {highlight_var}"
                    ))

        # 5. Highlight selection
        if epci_selection:
            sel = epci_selection if isinstance(epci_selection, list) else [epci_selection]
            hl = gdf_merged[gdf_merged['EPCI_CODE'].isin(sel)]
            if not hl.empty:
                fig.add_trace(go.Choropleth(
                    geojson="/assets/epci-ara-simplified.geojson",
                    featureidkey="properties.EPCI_CODE",
                    locations=hl['EPCI_CODE'].astype(str),
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

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            margin={"r":0, "t":0, "l":0, "b":0},
            paper_bgcolor='white', 
            clickmode='event+select',
            dragmode=False
        )
        
        # Stats UI
        inclus = len(df_focus)
        exclus = total_epci - inclus
        
        # Build a list of how many EPCIs each variable suppresses
        if summaries:
            list_items = []
            for s in summaries:
                total_excluded = s['out'] + s['nan']
                list_items.append(
                    dmc.Text([
                        dmc.Text(f"• {s['label']}", fw=600, span=True),
                        dmc.Text(" : ", span=True),
                        dmc.Text(f"supprime {total_excluded} EPCI", fw=700, c="red.7" if total_excluded > 0 else "gray.6", span=True),
                        dmc.Text(f" (dont {s['nan']} données manquantes)" if s['nan'] > 0 else "", size="xs", c="dimmed", span=True)
                    ], size="sm")
                )
            
            stats_list_paper = dmc.Paper(
                p="sm", withBorder=True, radius="md", bg="white", mt="sm",
                children=[
                    dmc.Text("Impact individuel des filtres sélectionnés :", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed", mb="xs"),
                    dmc.Stack(gap=2, children=list_items)
                ]
            )
        else:
            stats_list_paper = None

        stats_header = dmc.Paper(
            p="md", withBorder=True, radius="md", bg="blue.0", mb="md",
            children=[
                dmc.Stack(
                    gap="md",
                    children=[
                        dmc.Stack(
                            gap=2,
                            children=[
                                dmc.Text([
                                    "Sur ", dmc.Text(str(total_epci), fw=700, span=True), " EPCI en région AURA, ",
                                    dmc.Text(str(inclus), fw=700, c="blue", span=True), " sont inclus par filtres sélectionnés et ",
                                    dmc.Text(str(exclus), fw=700, c="red", span=True), " sont exclus."
                                ], size="md", c="gray.9"),
                                dmc.Text(
                                    "Les territoires exclus sont ceux dont les données sont en dehors d'au moins une des plages de variables sélectionnées.",
                                    size="xs", fs="italic", c="dimmed"
                                )
                            ]
                        ),
                        dcc.Link(
                            dmc.Button(
                                "Quels leviers d'action pour ces territoires ?", 
                                variant="outline", 
                                color="blue", 
                                size="xs",
                                fullWidth=True,
                                leftSection=DashIconify(icon="solar:lightbulb-bold-duotone", width=16),
                                className="premium-hover"
                            ),
                            href="/leviers",
                            style={"textDecoration": "none"}
                        )
                    ]
                )
            ]
        )
        
        # Simplified description helper link card
        desc_paper = dmc.Paper(
            p="sm", withBorder=True, radius="md", bg="gray.0",
            children=[
                dmc.Group(
                    gap="xs", align="center", wrap="nowrap",
                    children=[
                        DashIconify(icon="solar:info-circle-bold", color="blue", width=18),
                        dmc.Text([
                            "Retrouvez le descriptif détaillé et la méthodologie de l'ensemble des variables sur la ",
                            dcc.Link(
                                "page dédiée", 
                                href="/methodologie", 
                                style={"color": "#1c7ed6", "fontWeight": 600, "textDecoration": "underline"}
                            ),
                            "."
                        ], size="sm", c="gray.7")
                    ]
                )
            ]
        )

        if summaries:
            content = dmc.Stack(gap="xs", children=[
                stats_header,
                stats_list_paper,
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
        return go.Figure(), dmc.Alert(f"Erreur de rendu : {str(e)}", color="red"), "Erreur technique", "Erreur", "Carte"

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
     Input('map-indic-select', 'value'), Input('map-patho-select', 'value')],
    [State('url', 'pathname')]
)
def update_radar(social, offre, env, epci_codes, ind, patho, pathname):
    if pathname not in ['/exploration', '/carte', '/radar']:
        raise dash.exceptions.PreventUpdate
    target = f"{ind}_{patho}"
    # Consistency with map logic for CNR
    if target not in gdf_merged.columns and target == 'INCI_CNR' and 'Taux_CNR' in gdf_merged.columns: target = 'Taux_CNR'
    
    # Always include health indicator as first axis
    selected_vars = [target] + (social or []) + (offre or []) + (env or [])
    # Unique values only while preserving order if possible
    seen = set()
    selected_vars_unique = [x for x in selected_vars if not (x in seen or seen.add(x))]
    
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


# --- Clustering K-Means Dynamic Profiler ---

THEME_INTERPRETATIONS = {
    'sante': {
        0: {
            'title': "Surtaux Généralisé & Alerte Clinique",
            'desc': "Territoires caractérisés par des taux d'incidence, de mortalité et de prévalence cardiovasculaire nettement supérieurs à la moyenne régionale. Ce profil regroupe des populations âgées ou à fort passé industriel.",
            'rec': "🎯 Action Clinique : Dépistage massif hors-les-murs, éducation thérapeutique renforcée (ETP) et coordination resserrée des parcours de soins cardiologiques.",
            'hash': 'sante'
        },
        1: {
            'title': "Incidence Forte avec Performance Clinique",
            'desc': "Forte survenue de pathologies cardiaques aiguës (AVC, cardiopathie) mais taux de mortalité bas. Cela démontre une excellente performance de la filière locale des urgences et de la réanimation.",
            'rec': "🏥 Recommandation : Pérenniser le soutien aux services d'urgence et consolider le maillage en lits de soins intensifs de cardiologie.",
            'hash': 'sante'
        },
        2: {
            'title': "Vulnérabilité Chronique Émergente",
            'desc': "Prévalence élevée combinée à une mortalité modérée. Ce profil abrite une part de patients vivant avec des pathologies cardiovasculaires chroniques stabilisées.",
            'rec': "🤝 Recommandation : Renforcer l'accompagnement à domicile, le rôle des infirmières en pratique avancée (IPA) et la télésurveillance cardiaque.",
            'hash': 'sante'
        },
        3: {
            'title': "Préservation & Protection Cardiovasculaire",
            'desc': "Territoires présentant des taux de pathologies très inférieurs à la moyenne régionale. Ce profil regroupe généralement des populations actives ou périurbaines bénéficiant d'un excellent capital santé.",
            'rec': "🌿 Recommandation : Maintenir la promotion de modes de vie actifs, d'une alimentation saine et pérenniser les campagnes de prévention primaire.",
            'hash': 'sante'
        }
    },
    'socio': {
        0: {
            'title': "Précarité Cumulative & Isolement",
            'desc': "Territoires associant un niveau de vie très bas, un indice de précarité FDep élevé et une forte proportion de seniors isolés. Risque majeur de renoncement aux soins par manque de ressources.",
            'rec': "🤝 Action Sociale : Déployer des actions d'aller-vers, renforcer la médiation en santé et soutenir les centres communaux d'action sociale (CCAS).",
            'hash': 'socio'
        },
        1: {
            'title': "Disparités Urbaines Denses",
            'desc': "Territoires à forte densité de population caractérisés par des poches de chômage important, coexistant avec des zones plus aisées (métropoles).",
            'rec': "🎯 Recommandation : Cibler les actions de prévention en santé dans les Quartiers de la Politique de la Ville (QPV) et les foyers de travailleurs.",
            'hash': 'socio'
        },
        2: {
            'title': "Ruralité Isolée en Transition",
            'desc': "Chômage faible et revenus intermédiaires, mais marqué par un fort vieillissement de la population. L'isolement est ici principalement physique et géographique.",
            'rec': "🏥 Recommandation : Développer les navettes de santé solidaires et les services de télémédecine en mairies rurales pour lutter contre l'isolement.",
            'hash': 'socio'
        },
        3: {
            'title': "Périurbanisation Aisée & Dynamique",
            'desc': "Hauts revenus, chômage quasi-nul et population active. Ces territoires bénéficient d'un excellent capital socio-économique protecteur.",
            'rec': "🌿 Recommandation : Développer l'offre d'activités physiques de loisir et promouvoir le bien-être au travail en lien avec les entreprises locales.",
            'hash': 'socio'
        }
    },
    'offre': {
        0: {
            'title': "Désertification Médicale Critique",
            'desc': "Accessibilité aux généralistes (APL) très défavorable et temps d'accès aux services d'urgence supérieur à la moyenne régionale. Risque fort de retards de diagnostic.",
            'rec': "🏥 Offre de Soins : Soutenir l'installation de Maisons de Santé Pluriprofessionnelles (MSP) et encourager le déploiement de cabines de téléconsultation.",
            'hash': 'sante'
        },
        1: {
            'title': "Ruralité Fragile sous Vigilance",
            'desc': "Accès de premier recours (médecins traitants) modéré mais absence marquée de spécialistes de second recours et d'officines de pharmacie de proximité.",
            'rec': "💊 Recommandation : Favoriser les regroupements de professionnels en CPTS et soutenir les officines rurales comme relais de premier secours.",
            'hash': 'sante'
        },
        2: {
            'title': "Périurbain Médicalement Dépendant",
            'desc': "Excellente densité de médecins généralistes locaux mais temps d'accès aux urgences hospitalières élevé. Dépendance forte envers les métropoles voisines.",
            'rec': "🚑 Recommandation : Consolider la formation des secouristes locaux (pompiers) et renforcer les protocoles de premier accueil urgences en MSP.",
            'hash': 'sante'
        },
        3: {
            'title': "Hyper-concentration & Métropolisation",
            'desc': "Accessibilité exceptionnelle à l'ensemble des professionnels de santé (généralistes, spécialistes), présence immédiate de cliniques et d'un CHU.",
            'rec': "🔬 Recommandation : Développer les projets de recherche clinique territoriale et optimiser la régulation pour désengorger les urgences hospitalières.",
            'hash': 'sante'
        }
    },
    'env': {
        0: {
            'title': "Expositions Multiples & Couloirs Routiers",
            'desc': "Concentrations élevées de PM2.5/NO2 associées à de fortes nuisances sonores. Profil typique des grandes vallées alpines circulatoires ou du couloir rhodanien.",
            'rec': "🌿 Environnement : Articuler les contrats locaux de santé (CLS) avec des plans de réduction des émissions de polluants et des zones à faibles émissions (ZFE).",
            'hash': 'env'
        },
        1: {
            'title': "Pollution Urbaine Diffuse",
            'desc': "Exposition importante de fond aux particules fines PM2.5 en zone dense liée aux systèmes de chauffage et au trafic urbain, nuisances sonores directes modérées.",
            'rec': "🔥 Recommandation : Accélérer la transition énergétique des modes de chauffage individuels (rénovation énergétique) et promouvoir les transports en commun.",
            'hash': 'env'
        },
        2: {
            'title': "Vallées Encaissées & Chauffage Biomasse",
            'desc': "Qualité de l'air de fond excellente, sauf en hiver où des inversions thermiques retiennent les polluants issus du chauffage au bois individuel.",
            'rec': "🪵 Recommandation : Subventionner le renouvellement des anciens poêles à bois et sensibiliser les populations aux bonnes pratiques de combustion.",
            'hash': 'env'
        },
        3: {
            'title': "Préservation Environnementale Haute",
            'desc': "Qualité de l'air exceptionnelle et silence acoustique total. Communes de moyenne et haute montagne offrant un environnement protecteur majeur.",
            'rec': "⛰️ Recommandation : Valoriser le label 'Air Pur' et développer des sentiers sport-santé tirant parti de cette qualité environnementale.",
            'hash': 'env'
        }
    }
}

CLUSTER_COLORS = ['#e03131', '#ff922b', '#fcc419', '#51cf66'] # Rouge, Orange, Jaune, Vert


