from dash import dcc, html, Input, Output, State, callback, ALL
import dash
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd
import os
from ..data import load_data, PROJECT_ROOT

# Load data
gdf_merged, variable_dict, category_dict, _, description_dict, unit_dict, _, source_dict = load_data()



# Group variables by category
def get_vars_by_category(target_cat):
    """Return list of variables for a given category."""
    result = []
    for var_code, label in variable_dict.items():
        cat = str(category_dict.get(var_code, 'Autre')).lower()
        if cat == target_cat.lower():
            desc = description_dict.get(var_code, "")
            unit = unit_dict.get(var_code, "-")
            if not unit:
                unit = "-"
            source = source_dict.get(var_code, "-")
            if not source:
                source = "-"
            result.append({'code': var_code, 'label': label, 'desc': desc, 'unit': unit, 'source': source})
    return sorted(result, key=lambda x: x['label'])

def make_var_table(vars_list):
    """Create a styled table with fixed column widths for perfect alignment across tabs."""
    if not vars_list:
        return dmc.Text("Aucune variable dans cette catégorie.", c="dimmed", fs="italic")
    
    rows = []
    for item in vars_list:
        rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Text(item['label'], fw=500)),
                dmc.TableTd(dmc.Text(item['desc'], size="sm", c="dimmed")),
                dmc.TableTd(dmc.Text(item['unit'], size="sm", c="dimmed")),
                dmc.TableTd(dmc.Text(item['source'], size="xs", c="dimmed")),
                dmc.TableTd(dmc.Code(item['code'])),
            ])
        )
    
    head = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Variable", style={"width": "200px"}),
            dmc.TableTh("Description", style={"width": "400px"}),
            dmc.TableTh("Unité", style={"width": "100px"}),
            dmc.TableTh("Source", style={"width": "250px"}),
            dmc.TableTh("Code", style={"width": "120px"}),
        ])
    )
    
    body = dmc.TableTbody(rows)
    
    return dmc.Table(
        [head, body], 
        striped=True, 
        highlightOnHover=True, 
        withTableBorder=True, 
        withColumnBorders=True,
        layout="fixed",
        style={"width": "1070px"}
    )

socioeco_vars = get_vars_by_category('Socioéco')
offre_vars = get_vars_by_category('Offre de soins')
env_vars = get_vars_by_category('Environnement')
sante_vars = get_vars_by_category('Santé')

layout = dmc.Container(
    fluid=True,
    p="xl",
    children=[
        dmc.Title("Liste des variables et méthodologie", order=1, mb="xs", style={"color": "#2c3e50"}),
        dmc.Text(
            "Explorez les indicateurs pilotant les analyses de SeniAURA ainsi que la rigueur méthodologique du projet.", 
            c="dimmed", size="lg", mb="xl"
        ),
        
        dmc.Tabs(
            id='methodo-tabs',
            value='socioeco',
            variant="pills",
            radius="md",
            styles={
                "tab": {
                    "padding": "12px 20px",
                    "fontSize": "15px",
                    "fontWeight": 600,
                    "borderRadius": "12px",
                    "border": "1px solid #e9ecef",      # Same border as sidebar
                    "backgroundColor": "transparent",
                    "color": "#2c3e50",                  # Same near-black as sidebar
                    "transition": "background-color 200ms ease, border-color 200ms ease",
                    "&[data-active]": {
                        "backgroundColor": "#339af0 !important",
                        "color": "white !important",
                        "borderColor": "#1c7ed6 !important",
                        # No box-shadow
                    },
                    "&:hover": {
                        "backgroundColor": "#f1f3f5",    # Same hover bg as sidebar
                        "color": "#2c3e50",              # Text stays black on hover
                        "borderColor": "#339af0",        # Blue border on hover
                        # No transform, no box-shadow
                    }
                },
                "list": {"marginBottom": "24px", "gap": "6px"}
            },
            children=[
                # --- Tabs Navigation ---
                dmc.TabsList([
                    dmc.TabsTab("Socioéco", value="socioeco"),
                    dmc.TabsTab("Offre de soins", value="offre"),
                    dmc.TabsTab("Environnement", value="env"),
                    dmc.TabsTab("Santé", value="sante"),
                    dmc.TabsTab("Construction et méthodologie", value="construction"),
                ]),
                
                # --- Variables Panels ---
                dmc.TabsPanel(value='socioeco', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Variables socio-économiques", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Population, emploi, revenus et logement.", c="dimmed", mb="xl"),
                        dmc.ScrollArea(children=make_var_table(socioeco_vars), h=600)
                    ])
                ]),
                
                dmc.TabsPanel(value='offre', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Variables offre de soins", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Densité et accessibilité des professionnels de santé.", c="dimmed", mb="xl"),
                        dmc.ScrollArea(children=make_var_table(offre_vars), h=600)
                    ])
                ]),
                
                dmc.TabsPanel(value='env', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Variables environnement", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Qualité de l'air, bruit et risques environnementaux.", c="dimmed", mb="xl"),
                        dmc.ScrollArea(children=make_var_table(env_vars), h=600)
                    ])
                ]),
                
                dmc.TabsPanel(value='sante', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Variables de santé", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Indicateurs cardiovasculaires (incidences et prévalences).", c="dimmed", mb="xl"),
                        dmc.ScrollArea(children=make_var_table(sante_vars), h=600)
                    ])
                ]),

                # --- Methodology Panel ---
                dmc.TabsPanel(value='construction', children=[
                    dmc.Paper(
                        withBorder=True, p="xl", radius="md", shadow="sm",
                        children=[
                            dmc.Title("Prétraitements et méthodologie", order=2, mb="xl", c="#2c3e50", style={"borderBottom": "2px solid #339af0", "paddingBottom": "10px"}),
                            dmc.Accordion(
                                chevronPosition="right",
                                variant="separated",
                                value="sources",
                                radius="md",
                                children=[
                                    dmc.AccordionItem(
                                        value="sources",
                                        children=[
                                            dmc.AccordionControl(
                                                dmc.Group([
                                                    DashIconify(icon="solar:database-linear", width=22, color="#339af0"),
                                                    dmc.Text("Sources primaires et collecte des données", fw=600, fz="lg")
                                                ])
                                            ),
                                            dmc.AccordionPanel([
                                                dmc.Text("SeniAURA agrège des données hétérogènes issues de multiples sources institutionnelles :", mb="md"),
                                                dmc.List(
                                                    spacing="sm",
                                                    icon=dmc.ThemeIcon(DashIconify(icon="akar-icons:check", width=12), radius="xl", color="blue", size=20),
                                                    children=[
                                                        dmc.ListItem(html.Span([html.B("Santé"), " : Odissé / Santé Publique France."])),
                                                        dmc.ListItem(html.Span([html.B("Socio-économie"), " : Insee (Filosofi, Recensement)."])),
                                                        dmc.ListItem(html.Span([html.B("Offre de soins"), " : DREES et ORS AURA."])),
                                                        dmc.ListItem(html.Span([html.B("Environnement"), " : Balises / ORS AURA."]))
                                                    ]
                                                )
                                            ]),
                                        ],
                                    ),
                                    dmc.AccordionItem(
                                        value="cleaning",
                                        children=[
                                            dmc.AccordionControl(
                                                dmc.Group([
                                                    DashIconify(icon="solar:magic-stick-3-linear", width=22, color="#339af0"),
                                                    dmc.Text("Nettoyage et harmonisation numérique", fw=600, fz="lg")
                                                ])
                                            ),
                                            dmc.AccordionPanel(
                                                dmc.Text("Correction des formats, unification des séparateurs de milliers/décimales et gestion des types numériques pour garantir la fiabilité statistique.")
                                            ),
                                        ],
                                    ),
                                    dmc.AccordionItem(
                                        value="geo",
                                        children=[
                                            dmc.AccordionControl(
                                                dmc.Group([
                                                    DashIconify(icon="solar:globus-linear", width=22, color="#339af0"),
                                                    dmc.Text("Standardisation géographique (échelle EPCI)", fw=600, fz="lg")
                                                ])
                                            ),
                                            dmc.AccordionPanel(
                                                dmc.Text("Agrégation des données communales vers l'échelon intercommunal (EPCI) par moyenne pondérée.")
                                            ),
                                        ],
                                    ),
                                ]
                            )
                        ]
                    )
                ])
            ]
        ),
        dmc.Space(h="xl")
    ]
)
