import dash
from dash import dcc, html, Input, Output, State, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import os
import pandas as pd

# Import layouts from pages
from src.pages import home, methodology, exploration
from src.data import load_data

# Load data for filter options
gdf_merged, variable_dict, category_dict, _, _, _, _, _ = load_data()

def get_options(target_cats):
    options = []
    for col, label in variable_dict.items():
        if col not in gdf_merged.columns: continue
        cat = str(category_dict.get(col, "")).lower()
        if cat in target_cats:
            options.append({'label': label, 'value': col})
    return sorted(options, key=lambda x: x['label'])

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
        "&:hover": {
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
app = dash.Dash(__name__, title="SeniAURA - Accueil", suppress_callback_exceptions=True, external_stylesheets=external_stylesheets)
server = app.server

sidebar = dmc.AppShellNavbar(
    p="md",
    className="app-sidebar",
    style={"backgroundColor": "#ffffff", "borderRight": "1px solid #e9ecef"},
    children=[
        dmc.Stack(
            justify="space-between",
            h="100%",
            style={"overflowY": "auto", "flex": 1},
            children=[
                dmc.Stack(
                    gap="xs",
                    children=[
                        # Section titre des filtres
                        dmc.Divider(variant="solid", mb="md", c="gray.2"),
                        # --- Filter Section (Hidden on Home/Methodology) ---
                        html.Div(id='sidebar-filters-section', children=[
                            dmc.Group(
                                gap="xs", mb="md",
                                children=[
                                    DashIconify(icon="solar:health-diagnostics-linear", width=18, color="#339af0"),
                                    dmc.Text("Choix de l'Indicateur", fw=700, size="sm", c="#2c3e50"),
                                ]
                            ),
                            dmc.Stack(gap="xs", mb="xl", children=[
                                dmc.Select(
                                    id='map-indic-select', 
                                    data=[{'label': 'Incidence', 'value': 'INCI'},{'label': 'Mortalité', 'value': 'MORT'},{'label': 'Prévalence', 'value': 'PREV'}], 
                                    value='INCI', size="sm", radius="md",
                                    label="Type d'indicateur",
                                    comboboxProps={"withinPortal": True, "shadow": "md", "offset": 5},
                                    styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff"}}
                                ),
                                dmc.Select(
                                    id='map-patho-select', 
                                    data=[{'label': 'AVC', 'value': 'AVC'},{'label': 'Cardiopathies', 'value': 'CardIsch'},{'label': 'Insuffisance Cardiaque', 'value': 'InsuCard'}], 
                                    value='AVC', size="sm", radius="md",
                                    label="Pathologie",
                                    comboboxProps={"withinPortal": True, "shadow": "md", "offset": 5},
                                    styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff"}}
                                ),
                            ]),
                            dmc.Divider(variant="solid", mb="md", c="gray.2"),
                            dmc.Group(
                                gap="xs", mb="md",
                                children=[
                                    DashIconify(icon="solar:filter-linear", width=18, color="#339af0"),
                                    dmc.Text("Variables de Filtrage", fw=700, size="sm", c="#2c3e50"),
                                ]
                            ),

                            # Socio-Économie group
                            dmc.Text("Socio-Économie", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed", mb=5),
                            dmc.MultiSelect(
                                id='sidebar-filter-social', 
                                data=social_options, 
                                placeholder="Sélectionner...", 
                                clearable=True, 
                                searchable=True, 
                                radius="md", 
                                mb="md", 
                                comboboxProps={"withinPortal": True, "dropdownPosition": "bottom", "shadow": "xl", "transitionProps": {"transition": "pop-top-left", "duration": 200}, "offset": 7},
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}}
                            ),
                            dmc.Stack(id='slider-container-social', gap="xs", mb="md", px=10),

                            # Offre de Soins group
                            dmc.Text("Offre de Soins", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed", mb=5),
                            dmc.MultiSelect(
                                id='sidebar-filter-offre', 
                                data=offre_options, 
                                placeholder="Sélectionner...", 
                                clearable=True, 
                                searchable=True, 
                                radius="md", 
                                mb="md", 
                                comboboxProps={"withinPortal": True, "dropdownPosition": "bottom", "shadow": "xl", "transitionProps": {"transition": "pop-top-left", "duration": 200}, "offset": 7},
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}}
                            ),
                            dmc.Stack(id='slider-container-offre', gap="xs", mb="md", px=10),

                            # Environnement group
                            dmc.Text("Environnement", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed", mb=5),
                            dmc.MultiSelect(
                                id='sidebar-filter-env', 
                                data=env_options, 
                                placeholder="Sélectionner...", 
                                clearable=True, 
                                searchable=True, 
                                radius="md", 
                                mb="md", 
                                comboboxProps={"withinPortal": True, "dropdownPosition": "bottom", "shadow": "xl", "transitionProps": {"transition": "pop-top-left", "duration": 200}, "offset": 7},
                                styles={"dropdown": {"backgroundColor": "#e7f5ff", "border": "1px solid #d0ebff", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}}
                            ),
                            dmc.Stack(id='slider-container-env', gap="xs", mb="md", px=10),

                            dmc.Divider(my="lg"),
                            dmc.Text("Territoires", size="xs", fw=700, tt="uppercase", lts=1, c="dimmed", mb=5),
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
                # Footer
                dmc.Paper(
                    p="sm", radius="md", bg="#f8f9fa", withBorder=True, mx="sm", mb="sm",
                    children=[
                        dmc.Text("HEC Capstone Project", size="xs", fw=500, ta="center", c="dimmed"),
                        dmc.Text("v3.0 - 2026", size="xs", ta="center", c="dimmed", mt=2)
                    ]
                )
            ]
        )
    ]
)

header = dmc.AppShellHeader(
    h=130, # Hauteur augmentée pour accommoder le titre fixe sans surcharge
    px="xl",
    style={"backgroundColor": "white", "borderBottom": "1px solid #e9ecef", "display": "flex", "flexDirection": "column", "justifyContent": "center"},
    children=[
        # Ligne 1 : Navigation & Logo
        dmc.Group(
            justify="space-between",
            h=65,
            children=[
                dmc.Group(
                    gap="xs",
                    children=[
                        DashIconify(icon="lucide:activity", width=28, color="#339af0"),
                        dmc.Title("SeniAURA", order=2, style={"color": "#2c3e50", "letterSpacing": "-0.5px"}),
                        dmc.Badge("Région Auvergne-Rhône-Alpes", variant="light", color="blue", radius="sm", size="sm", ml=10),
                    ]
                ),
                dmc.Tabs(
                    id="nav-tabs",
                    value="/",
                    variant="pills",
                    radius="md",
                    className="header-nav-tabs",
                    styles={
                        "tab": {
                            "border": "1px solid #dee2e6",
                            "padding": "6px 16px",
                            "fontWeight": 600,
                            "transition": "all 200ms ease",
                            "backgroundColor": "#f8f9fa",
                            "color": "#495057",
                        },
                        "tab[data-active]": {
                            "backgroundColor": "#339af0 !important",
                            "borderColor": "#339af0 !important",
                            "color": "white !important"
                        }
                    },
                    children=[
                        dmc.TabsList([
                            dmc.TabsTab("Accueil", value="/", leftSection=DashIconify(icon="solar:home-2-linear", width=18)),
                            dmc.TabsTab("Exploration", value="/exploration", leftSection=DashIconify(icon="solar:map-linear", width=18)),
                            dmc.TabsTab("Liste des variables et méthodologie", value="/methodologie", leftSection=DashIconify(icon="solar:book-linear", width=18)),
                        ])
                    ]
                ),
            ]
        ),
        # Ligne 2 : Titre du Diagnostic (Fixé en haut)
        dmc.Box(
            style={"borderTop": "1px solid #f1f3f5", "paddingTop": "8px", "paddingBottom": "12px"},
            children=[
                dmc.Stack(gap=0, children=[
                    dmc.Title("Diagnostic Territorial des maladies Cardio-Neuro-Vasculaires", order=4, style={"color": "#2c3e50", "fontSize": "20px", "fontWeight": 700}),
                    dmc.Text("Analysez la répartition spatiale des maladies CNV selon différentes variables avec la carte interactive et le radar comparatif.", size="sm", c="dimmed", lineClamp=1),
                ])
            ]
        )
    ]
)

app.layout = dmc.MantineProvider(
    theme={"primaryColor": "blue", "fontFamily": "'Inter', sans-serif"},
    children=[
        dcc.Location(id='url', refresh=False),
        dmc.AppShell(
            id="app-shell",
            header={"height": 130}, # Match the new multi-line header
            navbar={"width": 300, "breakpoint": "sm", "collapsed": {"mobile": True, "desktop": False}},
            padding="md",
            children=[
                header,
                sidebar,
                dmc.AppShellMain(children=[], id='page-content', style={'minHeight': 'calc(100vh - 130px)', 'backgroundColor': '#f8f9fa'})
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
        return url_path if url_path in ['/', '/exploration', '/methodologie'] else '/', dash.no_update, current_navbar

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'url':
        # URL changed (back button or link)
        target_tab = '/exploration' if url_path in ['/carte', '/radar'] else url_path
        if target_tab not in ['/', '/exploration', '/methodologie']: target_tab = '/'
        
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
    elif pathname == '/methodologie':
        return methodology.layout
    else:
        return dmc.Center(dmc.Title("404 - Page non trouvée", order=1))

if __name__ == '__main__':
    app.run(debug=True, port=8050)
