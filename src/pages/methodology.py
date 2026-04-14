from dash import dcc, html, Input, Output, State, callback, ALL
import dash
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd
import os
from ..data import load_data, PROJECT_ROOT

# Load data
from ..data import load_data, PROJECT_ROOT, DATA_DIR_DASH, BASE_DIR
gdf_merged, variable_dict, category_dict, sens_dict, description_dict, unit_dict, _, source_dict, classement_dict = load_data()

# Load Action Levers (Leviers d'action)
LEVIERS_PATH = os.path.join(BASE_DIR, "Leviers d'action.md")
try:
    with open(LEVIERS_PATH, "r", encoding="utf-8") as f:
        leviers_content = f.read()
except Exception as e:
    print(f"Error loading {LEVIERS_PATH}: {e}")
    leviers_content = "### Leviers d'action non disponibles."



# Group variables by category
def get_vars_by_category(target_cat):
    """Return list of variables for a given category."""
    result = []
    for var_code, label in variable_dict.items():
        cat = str(category_dict.get(var_code, 'Autre')).lower()
        if cat == target_cat.lower():
            # Filter variables to match dashboard availability
            # Dashboard sidebar excludes 0, 1, 2, 3. 
            # We exclude 0, 1, 2 for analysis categories but keep 3 for Santé (indicators).
            rank = str(classement_dict.get(var_code, ""))
            if rank in ['0', '1', '2'] or (rank == '3' and cat != 'santé'):
                continue
                
            desc = description_dict.get(var_code, "")
            unit = unit_dict.get(var_code, "-")
            if not unit:
                unit = "-"
            source = source_dict.get(var_code, "-")
            if not source:
                source = "-"
            
            sens = sens_dict.get(var_code, 0)
            result.append({'code': var_code, 'label': label, 'desc': desc, 'unit': unit, 'source': source, 'sens': sens})
    return sorted(result, key=lambda x: x['label'])

def make_var_table(vars_list):
    """Create a styled table with fixed column widths for perfect alignment across tabs."""
    if not vars_list:
        return dmc.Text("Aucune variable dans cette catégorie.", c="dimmed", fs="italic")
    
    rows = []
    for item in vars_list:
        sens = item.get('sens', 0)
        if sens == 1:
            sens_badge = dmc.Group([
                DashIconify(icon="solar:add-circle-bold", width=16, color="#0ca678"),
                dmc.Text("Plus cette variable est élevée, moins le territoire est vulnérable", size="sm", fw=600, c="#0ca678")
            ], gap=8, style={"padding": "4px 12px", "backgroundColor": "#ebfbee", "borderRadius": "4px", "whiteSpace": "nowrap", "border": "1px solid #b2f2bb"})
        elif sens == -1:
            sens_badge = dmc.Group([
                DashIconify(icon="solar:danger-bold", width=16, color="#f03e3e"),
                dmc.Text("Plus cette variable est élevée, plus le territoire est vulnérable", size="sm", fw=600, c="#f03e3e")
            ], gap=8, style={"padding": "4px 12px", "backgroundColor": "#fff5f5", "borderRadius": "4px", "whiteSpace": "nowrap", "border": "1px solid #ffa8a8"})
        else:
            sens_badge = dmc.Badge("Neutre", color="gray", variant="light")
            

        rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Text(item['label'], fw=500)),
                dmc.TableTd(dmc.Text(item['desc'], size="sm", c="dimmed")),
                dmc.TableTd(dmc.Text(item['unit'], size="sm", ta="center", c="dimmed")),
                dmc.TableTd(dmc.Text(item['source'], size="xs", c="dimmed")),
                dmc.TableTd(sens_badge),
            ])
        )
    
    head = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Variable", style={"width": "180px"}),
            dmc.TableTh("Description", style={"width": "350px"}),
            dmc.TableTh("Unité", style={"width": "80px"}),
            dmc.TableTh("Source", style={"width": "150px"}),
            dmc.TableTh("Impact sur la vulnérabilité"),
        ])
    )
    
    body = dmc.TableTbody(rows)
    
    return dmc.Table(
        [head, body], 
        striped=True, 
        highlightOnHover=True, 
        withTableBorder=True, 
        withColumnBorders=True,
        style={"minWidth": "1400px"}
    )

socioeco_vars = get_vars_by_category('Socioéco')
offre_vars = get_vars_by_category('Offre de soins')
env_vars = get_vars_by_category('Environnement')
sante_vars = get_vars_by_category('Santé')

layout = dmc.Container(
    fluid=True,
    p=0,
    children=[
        dmc.Title("Liste des variables et méthodologie", order=1, mb="xs", style={"color": "#2c3e50"}),
        dmc.Text(
            "Explorez les indicateurs pilotant les analyses de CardiAURA ainsi que la rigueur méthodologique du projet.", 
            c="dimmed", size="lg", mb="xl"
        ),
        
        dmc.Tabs(
            id='methodo-tabs-main',
            value='variables',
            variant="pills",
            radius="md",
            children=[
                # --- Main Tabs Navigation ---
                # --- Main Tabs Navigation ---
                dmc.TabsList([
                    dmc.TabsTab("Liste des variables", value="variables"),
                    dmc.TabsTab("Sources des datasets", value="sources", leftSection=DashIconify(icon="solar:link-bold-duotone", width=18)),
                    dmc.TabsTab("Documentation Technique", value="documentation", leftSection=DashIconify(icon="solar:document-bold-duotone", width=18)),
                ]),
                
                # --- Variables Main Panel (with Nested Tabs) ---
                dmc.TabsPanel(value='variables', children=[
                    dmc.Paper(withBorder=True, p="md", radius="md", mt="md", mb="md", bg="gray.0", children=[
                        dmc.Group(gap="lg", children=[
                            dmc.Stack(gap=2, children=[
                                dmc.Text("Guide de lecture des colonnes :", fw=700, size="sm"),
                                dmc.Text("• Variable : Nom court utilisé dans l'application.", size="xs"),
                                dmc.Text("• Description : Détails de la mesure de l'indicateur.", size="xs"),
                            ]),
                            dmc.Stack(gap=2, children=[
                                dmc.Text(" ", size="sm"),
                                dmc.Text("• Unité : Unité de mesure (%, taux, nombre...).", size="xs"),
                                dmc.Text("• Source : Organisme producteur de la donnée.", size="xs"),
                            ]),
                            dmc.Stack(gap=2, children=[
                                dmc.Text(" ", size="sm"),
                                dmc.Text("• Polarité : Impact d'une hausse de la valeur sur la vulnérabilité.", size="xs"),
                                dmc.Text(" ", size="xs"),
                            ]),
                        ])
                    ]),
                    dmc.Tabs(
                        id='variables-sub-tabs',
                        value='socioeco',
                        variant="pills",
                        radius="md",
                        children=[
                            dmc.TabsList([
                                dmc.TabsTab("Socioéco", value="socioeco"),
                                dmc.TabsTab("Offre de soins", value="offre"),
                                dmc.TabsTab("Environnement", value="env"),
                                dmc.TabsTab("Santé", value="sante"),
                            ]),
                            
                            dmc.TabsPanel(value='socioeco', children=[
                                dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                                    dmc.Title("Variables socio-économiques", order=3, mb="xs", c="#2c3e50"),
                                    dmc.Text("Population, emploi, revenus et logement.", c="dimmed", mb="xl"),
                                    dmc.ScrollArea(children=make_var_table(socioeco_vars))
                                ])
                            ]),
                            
                            dmc.TabsPanel(value='offre', children=[
                                dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                                    dmc.Title("Variables offre de soins", order=3, mb="xs", c="#2c3e50"),
                                    dmc.Text("Densité et accessibilité des professionnels de santé.", c="dimmed", mb="xl"),
                                    dmc.ScrollArea(children=make_var_table(offre_vars))
                                ])
                            ]),
                            
                            dmc.TabsPanel(value='env', children=[
                                dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                                    dmc.Title("Variables environnement", order=3, mb="xs", c="#2c3e50"),
                                    dmc.Text("Qualité de l'air, bruit et risques environnementaux.", c="dimmed", mb="xl"),
                                    dmc.ScrollArea(children=make_var_table(env_vars))
                                ])
                            ]),
                            
                            dmc.TabsPanel(value='sante', children=[
                                dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                                    dmc.Title("Variables de santé", order=3, mb="xs", c="#2c3e50"),
                                    dmc.Text("Indicateurs cardiovasculaires (incidences et prévalences).", c="dimmed", mb="xl"),
                                    dmc.ScrollArea(children=make_var_table(sante_vars))
                                ])
                            ]),
                        ]
                    )
                ]),

                # --- Dataset Sources Panel ---
                dmc.TabsPanel(value='sources', children=[
                    dmc.Paper(
                        withBorder=True, p="xl", radius="md", shadow="sm", mt="md",
                        children=[
                            dmc.Title("Sources des Datasets", order=2, mb="xs", c="#2c3e50"),
                            dmc.Text("Accédez aux sources originales des données utilisées dans ce tableau de bord.", c="dimmed", mb="xl"),
                            
                            dmc.Stack(gap="xl", children=[
                                # --- Subsection: Indicateurs de Santé ---
                                dmc.Stack(gap="xs", children=[
                                    dmc.Group([
                                        DashIconify(icon="solar:heart-pulse-bold-duotone", width=24, color="red"),
                                        dmc.Text("Indicateurs de Santé", fw=700, size="lg")
                                    ]),
                                    dmc.Card(withBorder=True, radius="md", p="sm", bg="gray.0", children=[
                                        dmc.Group([
                                            dmc.Text("Odissée CNV : Maladies cardio-neuro-vasculaires (taux standardisés)", fw=500),
                                            html.A(
                                                dmc.Button("Consulter", variant="light", size="sm", leftSection=DashIconify(icon="solar:link-linear")),
                                                href="https://odisse.santepubliquefrance.fr/explore/dataset/maladies-cardio-neuro-vasculaires-taux-standardises-epci/information/?flg=fr-fr&disjunctive.type_patho&disjunctive.libreg&disjunctive.libdep",
                                                target="_blank"
                                            )
                                        ], justify="space-between")
                                    ])
                                ]),

                                # --- Subsection: Offre de Soins ---
                                dmc.Stack(gap="xs", children=[
                                    dmc.Group([
                                        DashIconify(icon="solar:medical-kit-bold-duotone", width=24, color="blue"),
                                        dmc.Text("Offre de Soins", fw=700, size="lg")
                                    ]),
                                    dmc.Stack(gap="md", children=[
                                        dmc.Card(withBorder=True, radius="md", p="sm", bg="gray.0", children=[
                                            dmc.Group([
                                                dmc.Text("Balises : Structures de santé (AURA)", fw=500, size="sm"),
                                                html.A(
                                                    dmc.Button("Consulter", variant="light", size="sm", leftSection=DashIconify(icon="solar:link-linear")),
                                                    href="https://www.balises-auvergne-rhone-alpes.org/data/les_bases.php?acces-aux-donnees",
                                                    target="_blank"
                                                )
                                            ], justify="space-between")
                                        ]),
                                        dmc.Card(withBorder=True, radius="md", p="sm", bg="gray.0", children=[
                                            dmc.Group([
                                                dmc.Text("DREES : Accessibilité (APL)", fw=500, size="sm"),
                                                html.A(
                                                    dmc.Button("Consulter", variant="light", size="sm", leftSection=DashIconify(icon="solar:link-linear")),
                                                    href="https://www.data.gouv.fr/datasets/laccessibilite-potentielle-localisee-apl",
                                                    target="_blank"
                                                )
                                            ], justify="space-between")
                                        ])
                                    ])
                                ]),

                                # --- Subsection: Déterminants Sociaux ---
                                dmc.Stack(gap="xs", children=[
                                    dmc.Group([
                                        DashIconify(icon="solar:users-group-rounded-bold-duotone", width=24, color="orange"),
                                        dmc.Text("Déterminants Sociaux & Démographie", fw=700, size="lg")
                                    ]),
                                    dmc.Stack(gap="sm", children=[
                                        dmc.Card(withBorder=True, radius="md", p="sm", bg="gray.0", children=[
                                            dmc.Group([
                                                dmc.Text("Balises : Indice Fdep", size="sm", fw=500),
                                                html.A(
                                                    dmc.Button("Consulter", variant="light", size="sm", leftSection=DashIconify(icon="solar:link-linear")),
                                                    href="https://www.balises-auvergne-rhone-alpes.org//OSE.php", 
                                                    target="_blank"
                                                )
                                            ], justify="space-between")
                                        ]),
                                        dmc.Card(withBorder=True, radius="md", p="sm", bg="gray.0", children=[
                                            dmc.Group([
                                                dmc.Text("INSEE : Revenus & Pauvreté (Filosofi)", size="sm", fw=500),
                                                html.A(
                                                    dmc.Button("Consulter", variant="light", size="sm", leftSection=DashIconify(icon="solar:link-linear")),
                                                    href="https://catalogue-donnees.insee.fr/fr/catalogue/recherche/DS_FILOSOFI_CC", 
                                                    target="_blank"
                                                )
                                            ], justify="space-between")
                                        ]),
                                        dmc.Card(withBorder=True, radius="md", p="sm", bg="gray.0", children=[
                                            dmc.Group([
                                                dmc.Text("INSEE : PCS & Emploi", size="sm", fw=500),
                                                html.A(
                                                    dmc.Button("Consulter", variant="light", size="sm", leftSection=DashIconify(icon="solar:link-linear")),
                                                    href="https://catalogue-donnees.insee.fr/fr/catalogue/recherche/DS_RP_EMPLOI_LR_COMP", 
                                                    target="_blank"
                                                )
                                            ], justify="space-between")
                                        ]),
                                        dmc.Card(withBorder=True, radius="md", p="sm", bg="gray.0", children=[
                                            dmc.Group([
                                                dmc.Text("INSEE : Niveaux d'études", size="sm", fw=500),
                                                html.A(
                                                    dmc.Button("Consulter", variant="light", size="sm", leftSection=DashIconify(icon="solar:link-linear")),
                                                    href="https://catalogue-donnees.insee.fr/fr/catalogue/recherche/DS_RP_EMPLOI_LR_PRINC", 
                                                    target="_blank"
                                                )
                                            ], justify="space-between")
                                        ]),
                                    ])
                                ]),

                                # --- Subsection: Environnement ---
                                dmc.Stack(gap="xs", children=[
                                    dmc.Group([
                                        DashIconify(icon="solar:leaf-bold-duotone", width=24, color="green"),
                                        dmc.Text("Déterminants Environnementaux", fw=700, size="lg")
                                    ]),
                                    dmc.Card(withBorder=True, radius="md", p="sm", bg="gray.0", children=[
                                        dmc.Group([
                                            dmc.Text("Balises : Observatoire Santé Environnement (OSE)", fw=500),
                                            html.A(
                                                dmc.Button("Consulter", variant="light", size="sm", leftSection=DashIconify(icon="solar:link-linear")),
                                                href="https://www.balises-auvergne-rhone-alpes.org//OSE.php",
                                                target="_blank"
                                            )
                                        ], justify="space-between")
                                    ])
                                ]),
                            ])
                        ]
                    )
                ]),

                # --- Technical Documentation Panel ---
                dmc.TabsPanel(value='documentation', children=[
                    dmc.Paper(
                        withBorder=True, p="xl", radius="md", shadow="sm",
                        children=[
                            dmc.Title("Documentation Technique & Méthodologie", order=2, mb="xs", c="#2c3e50"),
                            dmc.Text("Accédez à la documentation complète du projet : architecture, pipeline de données et détails méthodologiques.", c="dimmed", mb="xl"),
                            
                            dmc.Group([
                                html.A(
                                    dmc.Button(
                                        "Ouvrir la Documentation Technique",
                                        leftSection=DashIconify(icon="solar:document-bold-duotone", width=20),
                                        size="lg",
                                        variant="gradient",
                                        gradient={"from": "blue", "to": "indigo", "deg": 45},
                                        radius="md",
                                        className="premium-hover-purple"
                                    ),
                                    href="https://raphaelcontri.github.io/SeniAura/",
                                    target="_blank",
                                    style={"textDecoration": "none"}
                                ),
                                html.A(
                                    dmc.Button(
                                        "Voir sur GitHub",
                                        leftSection=DashIconify(icon="akar-icons:github-fill", width=20),
                                        size="lg",
                                        variant="outline",
                                        color="gray",
                                        radius="md"
                                    ),
                                    href="https://github.com/raphaelcontri/SeniAura",
                                    target="_blank",
                                    style={"textDecoration": "none"}
                                )
                            ], gap="md")
                        ]
                    )
                ]),

            ]
        ),
        dmc.Space(h="xl")
    ]
)

# --- URL Deep linking callback ---
@callback(
    Output('methodo-tabs-main', 'value'),
    Input('url', 'hash'),
    prevent_initial_call=False
)
def update_methodo_tab_from_url(hash_val):
    if hash_val == '#leviers':
        return 'leviers'
    if hash_val == '#variables':
        return 'variables'
    if hash_val == '#construction':
        return 'construction'
    return dash.no_update
