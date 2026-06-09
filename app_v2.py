import dash
from dash import dcc, html, Input, Output, State, no_update, ALL
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import os
import pandas as pd

# Import layouts from pages
from src.pages import home, methodology, exploration, leviers, upload
from src.data import load_data

# Load data for filter options
gdf_merged, variable_dict, category_dict, sens_dict, description_dict, unit_dict, gdf_deps, source_dict, classement_dict = load_data()

def get_options(target_cats):
    options = []
    for col, label in variable_dict.items():
        if col not in gdf_merged.columns: continue
        cat = str(category_dict.get(col, "")).lower()
        if cat in target_cats:
            rank = str(classement_dict.get(col, ""))
            # Exclude variables with Classement 0, 1, 2, 3
            if rank in ['0', '1', '2', '3']:
                continue
            is_priority = (rank == '67')
            
            # Format tooltip description
            cat_raw = category_dict.get(col, "")
            friendly_cat = "Socio-Économie" if "socio" in cat_raw.lower() else (
                "Offre de Soins" if "soins" in cat_raw.lower() or "offre" in cat_raw.lower() else (
                    "Environnement" if "env" in cat_raw.lower() else (
                        "Santé" if "sant" in cat_raw.lower() else cat_raw.capitalize()
                    )
                )
            )
            desc = description_dict.get(col, "Description non disponible.")
            sens = sens_dict.get(col, 0)
            if sens == 1:
                sens_msg = " (Plus cette variable est élevée, moins le territoire est vulnérable)"
            elif sens == -1:
                sens_msg = " (Plus cette variable est élevée, plus le territoire est vulnérable)"
            else:
                sens_msg = ""
            
            tooltip_text = f"{label} (Indicateur {friendly_cat}) : {desc}{sens_msg}"
            
            options.append({
                'label': label, 
                'value': col, 
                'priority': is_priority,
                'tooltip': tooltip_text
            })
            
    # Sort by priority (True first) then alphabetical
    sorted_options = sorted(options, key=lambda x: (not x['priority'], x['label']))
    return [{'label': x['label'], 'value': x['value'], 'tooltip': x['tooltip']} for x in sorted_options]

social_options = get_options(['socioéco'])
offre_options = get_options(['offre de soins'])
env_options = get_options(['environnement'])

epci_radar_options = [{'label': n, 'value': c} for n, c in zip(gdf_merged['nom_EPCI'], gdf_merged['EPCI_CODE']) if pd.notnull(n)]

NAV_LINK_STYLE = {
    "root": {
        "borderRadius": "12px",
        "marginBottom": "4px",
        "padding": "12px 16px",
        "transition": "all 200ms ease",
        "backgroundColor": "transparent",
        "&[data-active]": {
            "backgroundColor": "#339af0 !important",
            "boxShadow": "0 4px 12px rgba(51, 154, 240, 0.3)"
        },
        "&:hover": {
            "backgroundColor": "#f8f9fa",
            "transform": "translateX(4px)"
        }
    },
    "label": {
        "fontSize": "15px", 
        "fontWeight": 600,
        "color": "#495057",
        ".app-sidebar &[data-active] &": { "color": "white !important" }, # This is complex, let's simplify
    },
    "icon": {
        "marginRight": "12px",
        "color": "#495057"
    }
}

# Simplified approach: Use CSS selectors directly in root for all parts
NAV_LINK_STYLE = {
    "root": {
        "borderRadius": "12px",
        "marginBottom": "6px",
        "padding": "10px 16px",
        "transition": "all 200ms ease",
        "backgroundColor": "transparent",
        "color": "#495057 !important", # Base text/icon color
        "border": "1px solid #dee2e6", # Added thin border for non-active buttons
        "&[data-active]": {
            "backgroundColor": "#339af0 !important",
            "borderColor": "#339af0 !important", # Match border with background
            "color": "white !important", # Force white text/icon when active
            "boxShadow": "0 4px 12px rgba(51, 154, 240, 0.3)"
        },
        "&[data-active]:hover": {
            "backgroundColor": "#228be6 !important", # Slightly darker blue on hover
            "borderColor": "#228be6 !important",
            "color": "white !important",
            "transform": "translateX(4px)"
        },
        "&:not([data-active]):hover": {
            "backgroundColor": "#f8f9fa",
            "borderColor": "#dee2e6",
            "transform": "translateX(4px)",
            "color": "#339af0 !important"
        }
    },
    "label": {"fontSize": "15px", "fontWeight": 600, "color": "inherit"},
    "icon": {"marginRight": "12px", "color": "inherit"}
}

# --- App Setup ---
external_stylesheets = [
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
    'https://use.fontawesome.com/releases/v5.15.4/css/all.css',
    'https://unpkg.com/@mantine/core@7/styles.css',
    'https://unpkg.com/@mantine/dates@7/styles.css',
    'https://unpkg.com/@mantine/charts@7/styles.css',
]
from flask import send_from_directory, Response

app = dash.Dash(
    __name__, 
    title="CardiAURA - Accueil", 
    suppress_callback_exceptions=True, 
    external_stylesheets=external_stylesheets,
    meta_tags=[
        {
            "name": "viewport", 
            "content": "width=device-width, initial-scale=1.0, maximum-scale=1.2"
        },
        {
            "name": "google-site-verification", 
            "content": "KkhBSX_KhNawMneZxCpnKcVxCLAbYd38mpCqEXTEeZw"
        }
    ]
)
server = app.server

@server.route('/robots.txt')
def serve_robots():
    # Attempt to get host from request or use placeholder
    from flask import request
    host = request.host_url.rstrip('/')
    content = f"User-agent: *\nAllow: /\nSitemap: {host}/sitemap.xml"
    return Response(content, mimetype='text/plain')

@server.route('/sitemap.xml')
def serve_sitemap():
    from flask import request
    host = request.host_url.rstrip('/')
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{host}/</loc><priority>1.0</priority></url>
  <url><loc>{host}/exploration</loc><priority>0.8</priority></url>
  <url><loc>{host}/leviers</loc><priority>0.7</priority></url>
  <url><loc>{host}/methodologie</loc><priority>0.5</priority></url>
</urlset>"""
    return Response(content, mimetype='application/xml')

sidebar = dmc.AppShellNavbar(
    p="md",
    className="app-sidebar",
    style={"backgroundColor": "#ffffff", "borderRight": "1px solid #e9ecef"},
    children=[
        dmc.ScrollArea(
            h="calc(100vh - 110px)", # Ajusté pour laisser de la place au footer éventuel ou padding
            type="always",
            scrollbarSize=10,
            children=[
                dmc.Stack(
                    gap="xs",
                    px="md",
                    children=[
                        # Section titre des filtres

                        # --- Filter Section (Hidden on Home/Methodology) ---
                        html.Div(id='sidebar-filters-section', children=[
                            # Source de données (hidden to preserve callbacks)
                            dmc.Box(style={'display': 'none'}, children=[
                                dmc.Select(
                                    id='dataset-select',
                                    data=[{'label': '📊 Données régionales par défaut', 'value': 'default'}],
                                    value='default',
                                ),
                                html.Div(id='delete-dataset-btn-container')
                            ]),
                            dmc.Group(
                                gap="xs", mb=5, align="center",
                                children=[
                                    dmc.ThemeIcon(
                                        DashIconify(icon="solar:heart-pulse-bold", width=20),
                                        variant="light", radius="md", size="md"
                                    ),
                                    dmc.Text("Choix de l'indicateur de santé", fw=700, size="sm", c="#2c3e50"),
                                    dmc.Tooltip(
                                        multiline=True, w=250, withArrow=True,
                                        label="Sélectionnez l'indicateur de santé. La carte et le radar comparatif s'adapteront à votre sélection.",
                                        children=dmc.ActionIcon(DashIconify(icon="akar-icons:question", width=14), size="xs", variant="subtle", color="gray")
                                    )
                                ]
                            ),
                            dmc.Stack(gap="md", mb="xl", children=[
                                dmc.Box([
                                    dmc.Text("Type d'indicateur", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed", mb=5),
                                    dmc.Select(
                                        id='map-indic-select', 
                                        data=[
                                            {'label': 'Incidence', 'value': 'INCI'},
                                            {'label': 'Prévalence', 'value': 'PREV'},
                                            {'label': 'Mortalité', 'value': 'MORT'}
                                        ], 
                                        value='INCI', size="sm", radius="md",
                                        comboboxProps={"withinPortal": True, "shadow": "md", "offset": 5},
                                        styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff"}},
                                        renderOption={"function": "renderIndicatorOption"}
                                    ),
                                ]),
                                dmc.Box([
                                    dmc.Group(
                                        gap="xs", align="center", mb=5, wrap="nowrap",
                                        children=[
                                            dmc.Text("Pathologie", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed"),
                                            dmc.Tooltip(
                                                id="main-indicator-tooltip",
                                                label="",
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
                                    dmc.Select(
                                        id='map-patho-select', 
                                        data=[{'label': 'AVC', 'value': 'AVC'},{'label': 'Cardiopathie Ischémique', 'value': 'CardIsch'},{'label': 'Insuffisance Cardiaque', 'value': 'InsuCard'}], 
                                        value='AVC', size="sm", radius="md",
                                        comboboxProps={"withinPortal": True, "shadow": "md", "offset": 5},
                                        styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff"}}
                                    ),
                                ]),
                            ]),
                            dmc.Divider(variant="solid", mb="md", c="gray.2"),
                            dmc.Group(
                                gap="xs", mb=5, align="center", wrap="nowrap",
                                children=[
                                    dmc.ThemeIcon(
                                        DashIconify(icon="solar:filter-bold", width=20),
                                        variant="light", radius="md", size="md", color="indigo"
                                    ),
                                    dmc.Text("Choix des variables de filtrage", fw=700, size="sm", c="#2c3e50", style={"whiteSpace": "nowrap"}),
                                    dmc.Tooltip(
                                        multiline=True, w=250, withArrow=True,
                                        label="Vous pouvez sélectionner des variables de filtre dans les différentes catégories. Ces variables agissent comme des filtres pour la cartographie et des axes d'analyse pour le radar comparatif.",
                                        children=dmc.ActionIcon(DashIconify(icon="akar-icons:question", width=14), size="xs", variant="subtle", color="gray")
                                    )
                                ]
                            ),

                            # Offre de Soins group (moved up)
                            dmc.Group(
                                gap="xs", align="center", mb=5, wrap="nowrap",
                                children=[
                                    dmc.Text("Offre de Soins", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed"),
                                    dmc.Tooltip(
                                        multiline=True, w=220, withArrow=True,
                                        label="Une fois les filtres d'offre de soins sélectionnés, vous pouvez changer les valeurs des filtres avec les sliders qui s'affichent automatiquement. Les EPCI qui ne correspondent pas aux plages d'au moins une des variables seront grisés.",
                                        children=dmc.ActionIcon(DashIconify(icon="akar-icons:question", width=14), size="xs", variant="subtle", color="gray")
                                    )
                                ]
                            ),
                            dmc.MultiSelect(
                                id='sidebar-filter-offre', 
                                data=offre_options, 
                                placeholder="Sélectionner...", 
                                clearable=True, 
                                searchable=True, 
                                radius="md", 
                                mb=5, 
                                comboboxProps={"withinPortal": True, "dropdownPosition": "bottom", "shadow": "xl", "transitionProps": {"transition": "pop-top-left", "duration": 200}, "offset": 7},
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}},
                                renderOption={"function": "renderVariableOptionWithTooltip"}
                            ),
                            dmc.Stack(id='slider-container-offre', gap="xs", mb="md", px=10),

                            # Socio-Économie group (moved down)
                            dmc.Group(
                                gap="xs", align="center", mb=5, wrap="nowrap",
                                children=[
                                    dmc.Text("Socio-Économie", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed"),
                                    dmc.Tooltip(
                                        multiline=True, w=220, withArrow=True,
                                        label="Une fois les filtres socio-économiques sélectionnés, vous pouvez changer les valeurs des filtres avec les sliders qui s'affichent automatiquement. Les EPCI qui ne correspondent pas aux plages d'au moins une des variables seront grisés.",
                                        children=dmc.ActionIcon(DashIconify(icon="akar-icons:question", width=14), size="xs", variant="subtle", color="gray")
                                    )
                                ]
                            ),
                            dmc.MultiSelect(
                                id='sidebar-filter-social', 
                                data=social_options, 
                                placeholder="Sélectionner...", 
                                clearable=True, 
                                searchable=True, 
                                radius="md", 
                                mb=5, 
                                comboboxProps={"withinPortal": True, "dropdownPosition": "bottom", "shadow": "xl", "transitionProps": {"transition": "pop-top-left", "duration": 200}, "offset": 7},
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}},
                                renderOption={"function": "renderVariableOptionWithTooltip"}
                            ),
                            dmc.Stack(id='slider-container-social', gap="xs", mb="md", px=10),

                            # Environnement group
                            dmc.Group(
                                gap="xs", align="center", mb=5, wrap="nowrap",
                                children=[
                                    dmc.Text("Environnement", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed"),
                                    dmc.Tooltip(
                                        multiline=True, w=220, withArrow=True,
                                        label="Une fois les filtres environnementaux sélectionnés, vous pouvez changer les valeurs des filtres avec les sliders qui s'affichent automatiquement. Les EPCI qui ne correspondent pas aux plages d'au moins une des variables seront grisés.",
                                        children=dmc.ActionIcon(DashIconify(icon="akar-icons:question", width=14), size="xs", variant="subtle", color="gray")
                                    )
                                ]
                            ),
                            dmc.MultiSelect(
                                id='sidebar-filter-env', 
                                data=env_options, 
                                placeholder="Sélectionner...", 
                                clearable=True, 
                                searchable=True, 
                                radius="md", 
                                mb=5, 
                                comboboxProps={"withinPortal": True, "dropdownPosition": "bottom", "shadow": "xl", "transitionProps": {"transition": "pop-top-left", "duration": 200}, "offset": 7},
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}},
                                renderOption={"function": "renderVariableOptionWithTooltip"}
                            ),
                            dmc.Stack(id='slider-container-env', gap="xs", mb="md", px=10),
                        ]),
                    ]
                ),
            ]
        ),
    ]
)

header = dmc.AppShellHeader(
    h=90,
    px="lg",
    style={"backgroundColor": "white", "borderBottom": "1px solid #e9ecef", "display": "flex", "alignItems": "center", "overflow": "hidden"},
    children=[
        dmc.Group(
            justify="space-between",
            align="center",
            wrap="nowrap",
            w="100%",
            gap="md",
            children=[
                # Logo + Badge + Titre (côté gauche)
                dmc.Group(
                    gap="sm",
                    wrap="nowrap",
                    style={"flexShrink": 0},
                    children=[
                        html.Img(src="/assets/Senio.png", height=55),
                        dmc.Stack(
                            gap=2,
                            children=[
                                dmc.Badge("Région Auvergne-Rhône-Alpes", variant="light", color="blue", radius="sm", size="xs"),
                                dmc.Title("Diagnostic Territorial des maladies Cardio-Neuro-Vasculaires", order=4, className="dashboard-main-title")
                            ]
                        ),
                    ]
                ),
                # Navigation + Aide (côté droit)
                dmc.Group(
                    gap="sm",
                    align="center",
                    wrap="nowrap",
                    style={"flexShrink": 0},
                    children=[
                        dmc.Tabs(
                            id="nav-tabs",
                            value="/",
                            variant="pills",
                            radius="md",
                            className="header-nav-tabs",
                            children=[
                                dmc.TabsList([
                                    dmc.TabsTab(
                                        children=[
                                            html.Span("Accueil", className="tab-label-long"),
                                        ],
                                        value="/",
                                        leftSection=DashIconify(icon="solar:home-2-linear", width=18),
                                    ),
                                    dmc.TabsTab(
                                        children=[
                                            html.Span("Exploration", className="tab-label-long"),
                                        ],
                                        value="/exploration",
                                        leftSection=DashIconify(icon="solar:map-linear", width=18),
                                    ),
                                    dmc.TabsTab(
                                        children=[
                                            html.Span("Leviers", className="tab-label-long"),
                                        ],
                                        value="/leviers",
                                        leftSection=DashIconify(icon="solar:star-linear", width=18),
                                    ),
                                    dmc.TabsTab(
                                        children=[
                                            html.Span("Variables & Méthodo", className="tab-label-long"),
                                            html.Span("Méthodo", className="tab-label-short"),
                                        ],
                                        value="/methodologie",
                                        leftSection=DashIconify(icon="solar:book-linear", width=18),
                                    ),
                                ])
                            ]
                        ),
                        dmc.Button(
                            "Aide",
                            id="exploration-guide-btn",
                            variant="outline",
                            color="violet",
                            className="premium-hover-purple help-button-animated",
                            leftSection=DashIconify(icon="akar-icons:question", width=16),
                            radius="md",
                            size="sm",
                            style={
                                "backgroundColor": "#f3f0ff", 
                                "fontWeight": 700,
                                "border": "1px solid #845ef7",
                                "color": "#6741d9",
                                "visibility": "hidden"
                            }
                        )
                    ]
                ),
            ]
        )
    ]
)

show_migration = os.environ.get("SHOW_MIGRATION_BANNER", "False").lower() == "true"

app.layout = dmc.MantineProvider(
    theme={"primaryColor": "blue", "fontFamily": "'Inter', sans-serif"},
    children=[
        dcc.Location(id='url', refresh=False),
        dcc.Store(id='aside-opened-store', data=False), # Store pour l'état du panneau latéral
        dcc.Store(id='session-store', data={"authenticated": False}, storage_type='session'), # Store pour l'état d'authentification
        dcc.Store(id='available-datasets-store', data=[], storage_type='memory'), # Store pour stocker les métadonnées des jeux de données de l'utilisateur
        dcc.Store(id='local-datasets-store', data=[], storage_type='session'), # Store pour stocker les métadonnées des jeux de données locaux
        dcc.Store(id='delete-dataset-temp-store', data={}, storage_type='memory'),
        dcc.Store(id='dataset-refresh-trigger', data=0, storage_type='memory'),
        dmc.Modal(
            title="Supprimer le jeu de données",
            id="delete-dataset-modal",
            opened=False,
            padding="xl",
            radius="lg",
            size="md",
            children=[
                dmc.Stack(gap="md", children=[
                    dmc.Text("Êtes-vous sûr de vouloir supprimer définitivement ce jeu de données ?"),
                    dmc.Text(
                        "Cette action supprimera le fichier de données brut, le fichier nettoyé, ainsi que toutes ses métadonnées. Le jeu de données ne sera plus disponible pour personne.",
                        c="red",
                        fw=600,
                        size="sm"
                    ),
                    html.Div(id="delete-dataset-modal-alert"),
                    dmc.Group(justify="flex-end", gap="sm", children=[
                        dmc.Button("Annuler", id="cancel-delete-dataset-btn", color="gray", variant="light", radius="md"),
                        dmc.Button("Supprimer", id="confirm-delete-dataset-btn", color="red", radius="md", leftSection=DashIconify(icon="solar:trash-bin-trash-bold", width=16))
                    ])
                ])
            ]
        ),
        dmc.AppShell(
            id="app-shell",
            header={"height": 90}, 
            navbar={"width": 350, "breakpoint": "sm", "collapsed": {"mobile": True, "desktop": False}},
            aside={"width": 450, "breakpoint": "md", "collapsed": {"desktop": True, "mobile": True}}, # Aside configuré mais masqué
            padding=0,
            children=[
                header,
                sidebar,
                dmc.AppShellMain(
                    children=[
                        html.Div([
                            dmc.Alert(
                                children="Cette URL va bientôt être désactivée. Veuillez utiliser la nouvelle URL : https://cardiaura.onrender.com",
                                title="Migration en cours",
                                color="orange",
                                variant="filled",
                                withCloseButton=True,
                                style={"marginBottom": 20, "margin": 20}
                            )
                        ]) if show_migration else None,
                        dmc.Container(
                            size="2000px", 
                            fluid=False,
                            px=0,
                            children=[
                                html.Div(
                                    id='page-content', 
                                    style={
                                        'padding': '32px', 
                                        'minHeight': '100%'
                                    },
                                    children=[
                                        html.Div(id='page-home', children=home.layout, style={'display': 'block'}),
                                        html.Div(id='page-exploration', children=exploration.layout, style={'display': 'none'}),
                                        html.Div(id='page-leviers', children=leviers.layout, style={'display': 'none'}),
                                        html.Div(id='page-methodology', children=methodology.layout, style={'display': 'none'}),
                                        html.Div(id='page-upload', children=upload.layout, style={'display': 'none'}),
                                    ]
                                )
                            ]
                        )
                    ],
                    style={'backgroundColor': '#f8f9fa'}
                ),
                dmc.AppShellAside(
                    p="md",
                    children=[
                        dmc.Group(justify="space-between", mb="md", children=[
                            dmc.Title("Aide & Mode d'emploi", order=4, style={"color": "#2c3e50"}),
                            dmc.ActionIcon(
                                DashIconify(icon="lucide:x", width=20),
                                id="close-aside-btn",
                                variant="subtle",
                                color="gray"
                            )
                        ]),
                        dmc.ScrollArea(
                            h="calc(100vh - 180px)",
                            children=[
                                html.Div(id='aside-content') # Point d'injection pour le guide d'aide
                            ]
                        )
                    ],
                    style={"backgroundColor": "white", "borderLeft": "1px solid #e9ecef"}
                )
            ]
        )
    ]
)

# --- Navigation Callbacks ---

@app.callback(
    [Output('nav-tabs', 'value'),
     Output('url', 'pathname'),
     Output('app-shell', 'navbar')],
    [Input('url', 'pathname'),
     Input('nav-tabs', 'value')],
    [State('app-shell', 'navbar')]
)
def unified_navigation(url_path, tab_val, current_navbar):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Initial load
        is_explor = url_path in ['/exploration', '/carte', '/radar']
        current_navbar["collapsed"] = {"desktop": not is_explor, "mobile": True}
        if url_path in ['/espace-perso', '/upload']:
            return None, dash.no_update, current_navbar
        return url_path if url_path in ['/', '/exploration', '/leviers', '/methodologie'] else '/', dash.no_update, current_navbar

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'url':
        # URL changed (back button or link)
        target_tab = '/exploration' if url_path in ['/carte', '/radar'] else url_path
        if target_tab in ['/espace-perso', '/upload']:
            is_explor = False
            current_navbar["collapsed"] = {"desktop": True, "mobile": True}
            return None, dash.no_update, current_navbar
        if target_tab not in ['/', '/exploration', '/leviers', '/methodologie']: target_tab = '/'
        
        is_explor = target_tab == '/exploration'
        current_navbar["collapsed"] = {"desktop": not is_explor, "mobile": True}
        return target_tab, dash.no_update, current_navbar
        
    elif trigger_id == 'nav-tabs':
        # Tab clicked
        is_explor = tab_val == '/exploration'
        current_navbar["collapsed"] = {"desktop": not is_explor, "mobile": True}
        return dash.no_update, tab_val, current_navbar


    return dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('page-home', 'style'),
     Output('page-exploration', 'style'),
     Output('page-leviers', 'style'),
     Output('page-methodology', 'style'),
     Output('page-upload', 'style')],
    [Input('url', 'pathname')]
)
def display_page(pathname):
    styles = [{'display': 'none'} for _ in range(5)]
    
    if pathname == '/':
        styles[0] = {'display': 'block'}
    elif pathname in ['/exploration', '/carte', '/radar']:
        styles[1] = {'display': 'block'}
    elif pathname == '/leviers':
        styles[2] = {'display': 'block'}
    elif pathname == '/methodologie':
        styles[3] = {'display': 'block'}
    elif pathname == '/upload':
        styles[4] = {'display': 'block'}
    else:
        # Fallback to home page style
        styles[0] = {'display': 'block'}
        
    return styles


@app.callback(
    Output('exploration-guide-btn', 'style'),
    [Input('url', 'pathname'),
     Input('aside-opened-store', 'data')],
    State('exploration-guide-btn', 'style')
)
def toggle_guide_button(pathname, aside_opened, current_style):
    is_explor = pathname in ['/exploration', '/carte', '/radar']
    new_style = current_style.copy()
    if is_explor and not aside_opened:
        new_style["visibility"] = "visible"
    else:
        new_style["visibility"] = "hidden"
    return new_style

# --- Aside Toggle Callbacks ---

@app.callback(
    Output('aside-opened-store', 'data'),
    Input('exploration-guide-btn', 'n_clicks'),
    State('aside-opened-store', 'data'),
    prevent_initial_call=True
)
def toggle_aside_store(n, opened):
    return not opened

@app.callback(
    Output('app-shell', 'aside'),
    Input('aside-opened-store', 'data'),
    State('app-shell', 'aside')
)
def sync_aside_state(opened, current_aside):
    if not current_aside:
        current_aside = {"width": 450, "breakpoint": "md"}
    current_aside["collapsed"] = {"desktop": not opened, "mobile": not opened}
    return current_aside

@app.callback(
    Output('aside-opened-store', 'data', allow_duplicate=True),
    [Input('close-aside-btn', 'n_clicks'),
     Input('url', 'pathname')],
    prevent_initial_call=True
)
def close_aside(n, pathname):
    if pathname not in ['/exploration', '/carte', '/radar']:
        return False
    if dash.callback_context.triggered_id == 'close-aside-btn':
        return False
    return dash.no_update

# --- Callbacks pour la gestion dynamique des jeux de données utilisateur ---

@app.callback(
    [Output("available-datasets-store", "data"),
     Output("dataset-select", "data")],
    [Input("session-store", "data"),
     Input("url", "pathname"),
     Input("dataset-refresh-trigger", "data"),
     Input("local-datasets-store", "data")]
)
def fetch_user_datasets(session_data, pathname, refresh_trigger, local_datasets):
    default_opt = [{'label': '📊 Données régionales par défaut', 'value': 'default'}]
    if not session_data or not session_data.get("authenticated"):
        id_token = None
        uid = None
    else:
        id_token = session_data.get("idToken")
        uid = session_data.get("uid")
        
    # For local-offline flow, do not load online datasets.
    # Keep the original firebase query code intact but do not execute it for the dropdown options.
    # res = get_available_datasets(id_token=id_token, uid=uid)
    # datasets = res.get("datasets", []) if res["success"] else []
    datasets = []
    
    # Fusionner avec les datasets locaux
    if local_datasets:
        cloud_ids = {d.get("id") for d in datasets}
        for ld in local_datasets:
            if ld.get("id") not in cloud_ids:
                datasets.append(ld)
    
    seen_paths = set()
    unique_datasets = []
    options = default_opt.copy()
    
    for d in datasets:
        path = d.get('file_path')
        if not path or path in seen_paths:
            continue
        seen_paths.add(path)
        unique_datasets.append(d)
        options.append({
            'label': f"⭐ {d.get('name', d.get('dataset_name', 'Sans nom'))} ({d.get('scale', 'epci').upper()})",
            'value': path
        })
        
    return unique_datasets, options


@app.callback(
    [Output('sidebar-filter-social', 'data'),
     Output('sidebar-filter-offre', 'data'),
     Output('sidebar-filter-env', 'data'),
     Output('map-indic-select', 'data')],
    [Input('dataset-select', 'value')],
    [State('available-datasets-store', 'data'),
     State('session-store', 'data')]
)
def update_active_dataset_data(dataset_value, available_datasets, session_data):
    global gdf_merged, variable_dict, category_dict, sens_dict, description_dict, unit_dict, gdf_deps, source_dict, classement_dict
    
    import src.pages.exploration as explo
    import src.pages.methodology as methodo
    
    if not dataset_value or dataset_value == 'default':
        g, v, c, s, d, u, gd, sd, cl = load_data()
    else:
        dataset_meta = None
        for d_item in available_datasets:
            if d_item['file_path'] == dataset_value:
                dataset_meta = d_item
                break
                
        if not dataset_meta:
            g, v, c, s, d, u, gd, sd, cl = load_data()
        else:
            columns_metadata = dataset_meta.get("columns_metadata", {})
            local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", dataset_value)
            
            try:
                # Load the local CSV file
                df_user = pd.read_csv(local_path)
                
                # Merge with base data
                g_base, v_base, c_base, s_base, d_base, u_base, gd_base, sd_base, cl_base = load_data()
                
                # Simplified merging logic since the upload already aggregated it
                if "CODE_EPCI" in df_user.columns:
                    df_user['CODE_EPCI'] = df_user['CODE_EPCI'].astype(str).str.replace('.0', '', regex=False).str.strip()
                    cols_to_add = [col for col in df_user.columns if col == 'CODE_EPCI' or col not in g_base.columns]
                    df_user_filtered = df_user[cols_to_add]
                    
                    g_new = g_base.merge(df_user_filtered, left_on='EPCI_CODE', right_on='CODE_EPCI', how='left')
                    if 'CODE_EPCI_y' in g_new.columns:
                        g_new = g_new.drop(columns=['CODE_EPCI_y'])
                    if 'CODE_EPCI_x' in g_new.columns:
                        g_new = g_new.rename(columns={'CODE_EPCI_x': 'CODE_EPCI'})
                        
                    # Update dictionaries
                    new_vars = [col for col in df_user.columns if col not in ['CODE_EPCI', 'EPCI_CODE', 'CODE_COMMUNE']]
                    for var in new_vars:
                        meta = columns_metadata.get(var, {})
                        custom_label = meta.get("label", str(var).replace('_', ' ').strip().capitalize())
                        category = meta.get("category", "environnement")
                        
                        v_base[var] = f"⭐ {custom_label}"
                        c_base[var] = category
                        s_base[var] = 0
                        d_base[var] = f"Indicateur importé : {custom_label}"
                        u_base[var] = "valeur"
                        sd_base[var] = "Import local"
                        cl_base[var] = "99"
                        
                    g, v, c, s, d, u, gd, sd, cl = g_new, v_base, c_base, s_base, d_base, u_base, gd_base, sd_base, cl_base
                else:
                    print("Erreur: CODE_EPCI absent du dataset local.")
                    g, v, c, s, d, u, gd, sd, cl = g_base, v_base, c_base, s_base, d_base, u_base, gd_base, sd_base, cl_base
            except Exception as ex:
                print(f"Erreur de chargement du dataset local ({local_path}): {ex}")
                g, v, c, s, d, u, gd, sd, cl = load_data()
                
    gdf_merged = g
    variable_dict = v
    category_dict = c
    sens_dict = s
    description_dict = d
    unit_dict = u
    gdf_deps = gd
    source_dict = sd
    classement_dict = cl
    
    explo.gdf_merged = g
    explo.variable_dict = v
    explo.category_dict = c
    explo.sens_dict = s
    explo.description_dict = d
    explo.unit_dict = u
    explo.gdf_deps = gd
    explo.source_dict = sd
    explo.classement_dict = cl
    
    if g.crs is None:
        g.set_crs(epsg=4326, inplace=True)
    explo.gdf_4326 = g.to_crs(epsg=4326)
    if gd.crs is None:
        gd.set_crs(epsg=4326, inplace=True)
    explo.gdf_deps_4326 = gd.to_crs(epsg=4326)
    
    methodo.gdf_merged = g
    methodo.variable_dict = v
    methodo.category_dict = c
    methodo.sens_dict = s
    methodo.description_dict = d
    methodo.unit_dict = u
    methodo.source_dict = sd
    methodo.classement_dict = cl

    social_opts = get_options(['socioéco'])
    offre_opts = get_options(['offre de soins'])
    env_opts = get_options(['environnement'])
    
    health_opts = [
        {'label': 'Incidence', 'value': 'INCI'},
        {'label': 'Prévalence', 'value': 'PREV'},
        {'label': 'Mortalité', 'value': 'MORT'}
    ]
    user_health_vars = [var for var, cat in c.items() if cat == "santé" and var not in ['INCI_AVC', 'INCI_CardIsch', 'INCI_InsuCard', 'PREV_AVC', 'PREV_CardIsch', 'PREV_InsuCard', 'MORT_AVC', 'MORT_CardIsch', 'MORT_InsuCard', 'Taux_CNR']]
    for h_var in user_health_vars:
        label = v.get(h_var, h_var)
        health_opts.append({'label': label, 'value': h_var})

    return social_opts, offre_opts, env_opts, health_opts


# --- Callbacks pour la suppression des jeux de données utilisateur ---

@app.callback(
    Output("delete-dataset-btn-container", "children"),
    [Input("dataset-select", "value"),
     Input("session-store", "data")],
    [State("available-datasets-store", "data")]
)
def toggle_delete_dataset_button(dataset_value, session_data, available_datasets):
    if not dataset_value or dataset_value == 'default':
        return []
        
    # Trouver les métadonnées du dataset sélectionné
    target_ds = None
    for d in available_datasets:
        if d.get("file_path") == dataset_value:
            target_ds = d
            break
            
    if not target_ds:
        return []
        
    owner_uid = target_ds.get("owner_uid")
    
    # Mode offline : Si le dataset est local, n'importe quel utilisateur peut le supprimer
    if owner_uid == "local":
        return dmc.Button(
            "Supprimer ce dataset",
            id={"type": "open-delete-btn", "index": "sidebar"},
            color="red",
            variant="light",
            size="xs",
            fullWidth=True,
            radius="md",
            leftSection=DashIconify(icon="solar:trash-bin-trash-bold", width=14)
        )
        



@app.callback(
    [Output("delete-dataset-modal", "opened"),
     Output("delete-dataset-temp-store", "data"),
     Output("delete-dataset-modal-alert", "children")],
    [Input({"type": "open-delete-btn", "index": ALL}, "n_clicks"),
     Input("cancel-delete-dataset-btn", "n_clicks")],
    [State("dataset-select", "value"),
     State("available-datasets-store", "data")],
    prevent_initial_call=True
)
def manage_delete_modal(open_clicks_list, cancel_clicks, dataset_value, available_datasets):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, {}, []
        
    trigger_id_str = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id_str == "cancel-delete-dataset-btn":
        return False, {}, []
        
    try:
        trigger_id = json.loads(trigger_id_str)
        if trigger_id.get("type") == "open-delete-btn":
            if not open_clicks_list or not open_clicks_list[0]:
                return False, {}, []
                
            # Find the target dataset metadata
            target_dataset = {}
            for d in available_datasets:
                if d.get("file_path") == dataset_value:
                    target_dataset = d
                    break
            return True, target_dataset, []
    except Exception as e:
        print(f"Error in manage_delete_modal: {e}")
        
    return False, {}, []


@app.callback(
    [Output("delete-dataset-modal", "opened", allow_duplicate=True),
     Output("delete-dataset-modal-alert", "children", allow_duplicate=True),
     Output("dataset-select", "value"),
     Output("dataset-refresh-trigger", "data"),
     Output("local-datasets-store", "data", allow_duplicate=True)],
    Input("confirm-delete-dataset-btn", "n_clicks"),
    [State("delete-dataset-temp-store", "data"),
     State("session-store", "data"),
     State("dataset-refresh-trigger", "data"),
     State("local-datasets-store", "data")],
    prevent_initial_call=True
)
def execute_dataset_deletion(confirm_clicks, target_dataset, session_data, current_refresh, local_datasets):
    if not confirm_clicks or not target_dataset:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
    owner_uid = target_dataset.get("owner_uid")
    doc_id = target_dataset.get("id")
    file_path = target_dataset.get("file_path")
    
    updated_local_datasets = (local_datasets or []).copy()
    
    # Mode offline : suppression locale
    if owner_uid == "local":
        try:
            local_abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", file_path)
            if os.path.exists(local_abs_path):
                os.remove(local_abs_path)
        except Exception as e:
            print(f"Error deleting local file {file_path}: {e}")
            
        updated_local_datasets = [d for d in updated_local_datasets if d.get("id") != doc_id]
        next_refresh = (current_refresh or 0) + 1
        return False, [], "default", next_refresh, updated_local_datasets
        
        next_refresh = (current_refresh or 0) + 1
        return False, [], "default", next_refresh, updated_local_datasets


@app.callback(
    Output("main-indicator-tooltip", "label"),
    [Input("map-indic-select", "value"),
     Input("map-patho-select", "value")]
)
def update_main_indicator_tooltip(ind, patho):
    target = f"{ind}_{patho}"
    if target == 'INCI_CNR': target = 'Taux_CNR'
    
    friendly_cat = "Santé"
    label_var = variable_dict.get(target, target)
    desc = description_dict.get(target, "Description non disponible.")
    sens = sens_dict.get(target, 0)
    
    if sens == 1:
        sens_msg = " (Plus cette variable est élevée, moins le territoire est vulnérable)"
    elif sens == -1:
        sens_msg = " (Plus cette variable est élevée, plus le territoire est vulnérable)"
    else:
        sens_msg = ""
        
    return f"{label_var} (Indicateur {friendly_cat}) : {desc}{sens_msg}"


if __name__ == '__main__':

    # Trigger hot-reload after cleaning API key input logic
    app.run(debug=True, port=8050)
