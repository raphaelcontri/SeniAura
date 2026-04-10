import dash
from dash import dcc, html, Input, Output, State, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import os
import pandas as pd

# Import layouts from pages
from src.pages import home, methodology, exploration, leviers
from src.data import load_data

# Load data for filter options
gdf_merged, variable_dict, category_dict, _, _, _, _, _, classement_dict = load_data()

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
            options.append({'label': label, 'value': col, 'priority': is_priority})
            
    # Sort by priority (True first) then alphabetical
    sorted_options = sorted(options, key=lambda x: (not x['priority'], x['label']))
    return [{'label': x['label'], 'value': x['value']} for x in sorted_options]

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
                                        data=[{'label': 'Incidence', 'value': 'INCI'},{'label': 'Prévalence', 'value': 'PREV'},{'label': 'Mortalité', 'value': 'MORT'}], 
                                        value='INCI', size="sm", radius="md",
                                        comboboxProps={"withinPortal": True, "shadow": "md", "offset": 5},
                                        styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff"}}
                                    ),
                                ]),
                                dmc.Box([
                                    dmc.Text("Pathologie", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed", mb=5),
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

                            # Socio-Économie group
                            dmc.Group(
                                gap="xs", align="center", mb=5, wrap="nowrap",
                                children=[
                                    dmc.Text("Socio-Économie", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed"),
                                    dmc.Tooltip(
                                        multiline=True, w=220, withArrow=True,
                                        label="Vous pouvez changer les valeurs des filtres. Les EPCI qui ne correspondent pas aux plages d'au moins une des variables seront grisés.",
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
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}}
                            ),
                            dmc.Stack(id='slider-container-social', gap="xs", mb="md", px=10),

                            # Offre de Soins group
                            dmc.Group(
                                gap="xs", align="center", mb=5, wrap="nowrap",
                                children=[
                                    dmc.Text("Offre de Soins", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed"),
                                    dmc.Tooltip(
                                        multiline=True, w=220, withArrow=True,
                                        label="Vous pouvez changer les valeurs des filtres. Les EPCI qui ne correspondent pas aux plages d'au moins une des variables seront grisés.",
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
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}}
                            ),
                            dmc.Stack(id='slider-container-offre', gap="xs", mb="md", px=10),

                            # Environnement group
                            dmc.Group(
                                gap="xs", align="center", mb=5, wrap="nowrap",
                                children=[
                                    dmc.Text("Environnement", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed"),
                                    dmc.Tooltip(
                                        multiline=True, w=220, withArrow=True,
                                        label="Vous pouvez changer les valeurs des filtres. Les EPCI qui ne correspondent pas aux plages d'au moins une des variables seront grisés.",
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
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}}
                            ),
                            dmc.Stack(id='slider-container-env', gap="xs", mb="md", px=10),

                            dmc.Group(
                                gap="xs", mb=5, align="center", wrap="nowrap",
                                children=[
                                    dmc.ThemeIcon(
                                        DashIconify(icon="solar:map-point-bold", width=20),
                                        variant="light", radius="md", size="md", color="teal"
                                    ),
                                    dmc.Text("EPCI à comparer", fw=700, size="sm", c="#2c3e50", style={"letterSpacing": "0.5px"}),
                                    dmc.Tooltip(
                                        multiline=True, w=250, withArrow=True,
                                        label="Sélectionnez des EPCI via le menu \"Choisir EPCI\" ou en cliquant directement sur la carte. Ils s'ajouteront alors au radar comparatif.",
                                        children=dmc.ActionIcon(DashIconify(icon="akar-icons:question", width=14), size="xs", variant="subtle", color="gray")
                                    )
                                ]
                            ),
                            dmc.MultiSelect(
                                id='sidebar-epci-radar',
                                data=epci_radar_options,
                                placeholder="Choisir EPCI...",
                                searchable=True,
                                clearable=True,
                                radius="md",
                                mb="sm",
                                comboboxProps={"withinPortal": True, "dropdownPosition": "bottom", "shadow": "xl", "transitionProps": {"transition": "pop-top-left", "duration": 200}, "offset": 7},
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}}
                            ),
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
                                "display": "none",
                                "fontWeight": 700,
                            }
                        )
                    ]
                ),
            ]
        )
    ]
)

app.layout = dmc.MantineProvider(
    theme={"primaryColor": "blue", "fontFamily": "'Inter', sans-serif"},
    children=[
        dcc.Location(id='url', refresh=False),
        dcc.Store(id='aside-opened-store', data=False), # Store pour l'état du panneau latéral
        dmc.AppShell(
            id="app-shell",
            header={"height": 90}, 
            navbar={"width": 350, "breakpoint": "sm", "collapsed": {"mobile": True, "desktop": False}},
            aside={"width": 450, "breakpoint": "md", "collapsed": {"desktop": True, "mobile": True}}, # Aside configuré mais masqué
            padding="md",
            children=[
                header,
                sidebar,
                dmc.AppShellMain(
                    children=[
                                        dmc.Container(
                                            size="2000px", # Wide enough for dashboard, but limits infinite stretch
                                            fluid=False,
                                            px=0,
                                            children=[
                                                html.Div(id='page-content', style={'padding': '20px'})
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
        return url_path if url_path in ['/', '/exploration', '/leviers', '/methodologie'] else '/', dash.no_update, current_navbar

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'url':
        # URL changed (back button or link)
        target_tab = '/exploration' if url_path in ['/carte', '/radar'] else url_path
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
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/':
        return home.layout
    elif pathname in ['/exploration', '/carte', '/radar']:
        return exploration.layout
    elif pathname == '/leviers':
        return leviers.layout
    elif pathname == '/methodologie':
        return methodology.layout
    else:
        return dmc.Center(dmc.Title("404 - Page non trouvée", order=1))

@app.callback(
    Output('exploration-guide-btn', 'style'),
    Input('url', 'pathname')
)
def toggle_guide_button(pathname):
    is_explor = pathname in ['/exploration', '/carte', '/radar']
    base_style = {
        "backgroundColor": "#f3f0ff", 
        "borderColor": "#845ef7", 
        "color": "#6741d9",
        "border": "1px solid #845ef7",
        "borderRadius": "12px",
        "fontWeight": 700,
        "paddingLeft": "15px",
        "paddingRight": "15px"
    }
    if is_explor:
        base_style["display"] = "block"
    else:
        base_style["display"] = "none"
    return base_style

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

if __name__ == '__main__':
    app.run(debug=True, port=8050)
