import dash
from dash import dcc, html, Input, Output
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import os
import pandas as pd

# Import layouts from pages
from src.pages import home, map, radar, methodology, clustering
from src.data import load_data

# Load data for filter options
gdf_merged, variable_dict, category_dict, _, _ = load_data()

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

# --- App Setup ---
external_stylesheets = [
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
    style={"backgroundColor": "#2c3e50"}, # keeping the dark theme for the sidebar
    children=[
        dmc.Stack(
            justify="space-between",
            h="100%",
            children=[
                dmc.Stack(
                    gap="sm",
                    children=[
                        dmc.Title("SeniAURA", order=2, ta="center", mb="lg", style={"color": "white", "cursor": "pointer"}),
                        
                        dcc.Link(href='/', style={'textDecoration': 'none'}, children=[
                            dmc.NavLink(
                                label="Accueil",
                                leftSection=DashIconify(icon="akar-icons:home", width=20, color="white"),
                                variant="subtle",
                                color="blue",
                                styles={
                                    "label": {"color": "white", "fontWeight": 500},
                                    "root": {
                                        "&:hover": {
                                            "backgroundColor": "#1a252f", # Darker hover background
                                            "color": "white"
                                        }
                                    },
                                    "icon": {"color": "white"}
                                }
                            )
                        ]),
                        dcc.Link(href='/carte', style={'textDecoration': 'none'}, children=[
                            dmc.NavLink(
                                label="Carte Interactive",
                                leftSection=DashIconify(icon="lucide:map", width=20, color="white"),
                                variant="subtle",
                                color="blue",
                                styles={
                                    "label": {"color": "white", "fontWeight": 500},
                                    "root": {
                                        "&:hover": {
                                            "backgroundColor": "#1a252f",
                                            "color": "white"
                                        }
                                    },
                                    "icon": {"color": "white"}
                                }
                            )
                        ]),
                        dcc.Link(href='/radar', style={'textDecoration': 'none'}, children=[
                            dmc.NavLink(
                                label="Radar Comparatif",
                                leftSection=DashIconify(icon="lucide:radar", width=20, color="white"),
                                variant="subtle",
                                color="blue",
                                styles={
                                    "label": {"color": "white", "fontWeight": 500},
                                    "root": {
                                        "&:hover": {
                                            "backgroundColor": "#1a252f",
                                            "color": "white"
                                        }
                                    },
                                    "icon": {"color": "white"}
                                }
                            )
                        ]),
                        dcc.Link(href='/methodologie', style={'textDecoration': 'none'}, children=[
                            dmc.NavLink(
                                label="Méthodologie",
                                leftSection=DashIconify(icon="lucide:book-open", width=20, color="white"),
                                variant="subtle",
                                color="blue",
                                styles={
                                    "label": {"color": "white", "fontWeight": 500},
                                    "root": {
                                        "&:hover": {
                                            "backgroundColor": "#1a252f",
                                            "color": "white"
                                        }
                                    },
                                    "icon": {"color": "white"}
                                }
                            )
                        ]),
                        
                        # --- Shared Filters (always in DOM) ---
                        html.Div(id='sidebar-filters', style={'display': 'none'}, children=[
                            dmc.Divider(variant="solid", my="md", color="gray.6"),
                            dmc.Text("Filtres partagés", size="sm", fw=700, tt="uppercase", lts=1, c="gray.3", mb="sm"),

                            # EPCI Select (by code, for Radar)
                            html.Div(style={'padding': '5px 0px'}, children=[
                                dmc.MultiSelect(
                                    id='sidebar-epci-radar',
                                    label="🎯 EPCI (Multi)",
                                    data=epci_radar_options,
                                    placeholder="Choisir des EPCI...",
                                    searchable=True,
                                    clearable=True,
                                    mb="sm",
                                    styles={
                                    "option": {"borderBottom": "2px solid #dee2e6", "padding": "12px", "color": "#2c3e50"}, # Darker text and thicker border
                                    "dropdown": {"borderRadius": "8px", "boxShadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"}
                                }
                            )]),

                            # Variable Filters
                            html.Div(style={'padding': '5px 0px'}, children=[
                                dmc.MultiSelect(id='sidebar-filter-social', label="Socio-Eco", data=social_options, placeholder="Sélectionner...", clearable=True, searchable=True, styles={"label": {"color": "white"}, "option": {"borderBottom": "2px solid #dee2e6", "padding": "12px", "color": "#2c3e50"}}),
                            ]),
                            html.Div(style={'padding': '5px 0px', 'marginTop': '5px'}, children=[
                                dmc.MultiSelect(id='sidebar-filter-offre', label="Offre de Soins", data=offre_options, placeholder="Sélectionner...", clearable=True, searchable=True, styles={"label": {"color": "white"}, "option": {"borderBottom": "2px solid #dee2e6", "padding": "12px", "color": "#2c3e50"}}),
                            ]),
                            html.Div(style={'padding': '5px 0px', 'marginTop': '5px'}, children=[
                                dmc.MultiSelect(id='sidebar-filter-env', label="Environnement", data=env_options, placeholder="Sélectionner...", clearable=True, searchable=True, styles={"label": {"color": "white"}, "option": {"borderBottom": "2px solid #dee2e6", "padding": "12px", "color": "#2c3e50"}}),
                            ]),
                        ]),
                    ]
                ),
                dmc.Center(
                    dmc.Stack(
                        gap=5,
                        align="center",
                        children=[
                            dmc.Text("HEC Capstone Project", size="xs", c="gray.4"),
                            dmc.Text("v2.1 - 2026", size="xs", c="gray.4")
                        ]
                    )
                )
            ]
        )
    ]
)

app.layout = dmc.MantineProvider(
    theme={"primaryColor": "blue"},
    children=[
        dcc.Location(id='url', refresh=False),
        dmc.AppShell(
            navbar={"width": 300, "breakpoint": "sm"},
            padding="md",
            children=[
                sidebar,
                dmc.AppShellMain(children=[], id='page-content', style={'height': '100vh', 'overflow': 'auto', 'backgroundColor': '#f4f6f8'})
            ]
        )
    ]
)

# --- Routing Callback ---
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/carte':
        return map.layout
    elif pathname == '/radar':
        return radar.layout
    elif pathname == '/methodologie':
        return methodology.layout
    elif pathname == '/clustering':
        return clustering.layout
    else:
        return home.layout

# --- Show/Hide Filters based on page ---
@app.callback(Output('sidebar-filters', 'style'), Input('url', 'pathname'))
def toggle_filters(pathname):
    if pathname in ['/carte', '/radar']:
        return {'display': 'block'}
    return {'display': 'none'}

if __name__ == '__main__':
    app.run(debug=True, port=8050)
