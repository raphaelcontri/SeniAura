from dash import dcc, html, Input, Output, State, callback, ALL
import dash
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd
import os
from ..data import load_data, PROJECT_ROOT

# Load data
gdf_merged, variable_dict, category_dict, _, description_dict, unit_dict, _ = load_data()

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
            result.append({'code': var_code, 'label': label, 'desc': desc, 'unit': unit})
    return sorted(result, key=lambda x: x['label'])

def make_var_table(vars_list):
    """Create a styled table for a list of variables using DMC."""
    if not vars_list:
        return dmc.Text("Aucune variable dans cette catégorie.", color="dimmed", fs="italic")
    
    rows = []
    for item in vars_list:
        rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Text(item['label'], fw=500)),
                dmc.TableTd(dmc.Text(item['desc'], size="sm", c="dimmed")),
                dmc.TableTd(dmc.Text(item['unit'], size="sm", c="dimmed")),
                dmc.TableTd(dmc.Code(item['code'])),
            ])
        )
    
    head = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Variable"),
            dmc.TableTh("Description"),
            dmc.TableTh("Unité"),
            dmc.TableTh("Code"),
        ])
    )
    
    body = dmc.TableTbody(rows)
    
    return dmc.Table([head, body], striped=True, highlightOnHover=True, withTableBorder=True, withColumnBorders=True)

socioeco_vars = get_vars_by_category('Socioéco')
offre_vars = get_vars_by_category('Offre de soins')
env_vars = get_vars_by_category('Environnement')
sante_vars = get_vars_by_category('Santé')

layout = dmc.Container(
    fluid=True,
    p="xl",
    children=[
        dmc.Title("Méthodologie & Variables", order=1, mb="xs"),
        dmc.Text(
            "Explorez les variables disponibles organisées par thématique. Ces variables sont utilisées dans les filtres de la Carte, du Radar et du Clustering.", 
            c="dimmed", size="lg", mb="xl"
        ),
        
        dmc.Paper(
            withBorder=True, shadow="sm", p="lg", radius="md", mb="xl", bg="gray.0",
            children=[
                dmc.Title("Construction du dataset", order=3, mb="sm"),
                dmc.Text("Le dashboard repose sur une base de données constituée à l’échelle des EPCI, agrégeant des données Open Data.", mb="md"),
                
                dmc.Title("Source des données", order=4, mb="xs"),
                dmc.List(
                    spacing="xs", mb="md",
                    icon=dmc.ThemeIcon(DashIconify(icon="akar-icons:check", width=16), radius="xl", color="blue", size=24),
                    children=[
                        dmc.ListItem(html.Span([html.B("Indicateurs de Santé"), " : Prévalence, incidence et mortalité (Odissé / Santé Publique France)."])),
                        dmc.ListItem(html.Span([html.B("Offre de soins"), " : APL Médecins/Infirmières (DREES), Inventaire des structures (Balises / ORS AURA)."])),
                        dmc.ListItem(html.Span([html.B("Déterminants Sociaux"), " : Revenus, précarité, indices F-EDI et FDep (Insee, Filosofi)."])),
                        dmc.ListItem(html.Span([html.B("Déterminants Environnementaux"), " : Polluants (PM2.5, NO2), Bruit (Balises / ORS AURA)."])),
                    ]
                ),
                
                dmc.Title("Traitements effectués", order=4, mb="xs"),
                dmc.Text("Les données ont été nettoyées, harmonisées et agrégées à l'échelle des EPCI. Les variables ont été catégorisées et normalisées pour permettre la comparaison.", mb="lg"),

                dmc.Text("Dernière mise à jour : 6 février 2026", fs="italic", c="dimmed", size="sm")
            ]
        ),
        
        dmc.Tabs(
            id='methodo-tabs',
            value='socioeco',
            children=[
                dmc.TabsList([
                    dmc.TabsTab(f'Socio-Éco ({len(socioeco_vars)})', value='socioeco', color="blue"),
                    dmc.TabsTab(f'Offre de Soins ({len(offre_vars)})', value='offre', color="green"),
                    dmc.TabsTab(f'Environnement ({len(env_vars)})', value='env', color="orange"),
                    dmc.TabsTab(f'Santé ({len(sante_vars)})', value='sante', color="red"),
                ]),
                
                dmc.TabsPanel(value='socioeco', pt="xl", children=[
                    dmc.Title("🏠 Variables Socio-Économiques", order=3, mb="xs"),
                    dmc.Text("Indicateurs relatifs à la population, l'emploi, les revenus, le logement et l'éducation.", c="dimmed", mb="md"),
                    make_var_table(socioeco_vars)
                ]),
                
                dmc.TabsPanel(value='offre', pt="xl", children=[
                    dmc.Title("🏥 Variables Offre de Soins", order=3, mb="xs"),
                    dmc.Text("Accessibilité et densité des professionnels de santé sur le territoire.", c="dimmed", mb="md"),
                    make_var_table(offre_vars)
                ]),
                
                dmc.TabsPanel(value='env', pt="xl", children=[
                    dmc.Title("🌿 Variables Environnement", order=3, mb="xs"),
                    dmc.Text("Indicateurs liés à la qualité de l'environnement et aux risques environnementaux.", c="dimmed", mb="md"),
                    make_var_table(env_vars)
                ]),
                
                dmc.TabsPanel(value='sante', pt="xl", children=[
                    dmc.Title("❤️ Variables de Santé", order=3, mb="xs"),
                    dmc.Text("Indicateurs d'incidence, mortalité et prévalence des pathologies cardiovasculaires.", c="dimmed", mb="md"),
                    make_var_table(sante_vars)
                ])
            ]
        )
    ]
)
