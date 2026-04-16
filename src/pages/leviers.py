import re
from dash import dcc, html, Input, Output, callback
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import os
import pandas as pd
from ..data import BASE_DIR

# Load Action Levers (Leviers d'action)
LEVIERS_PATH = os.path.join(BASE_DIR, "Leviers d'action.md")

def parse_markdown_table(content):
    """Parses a simple Markdown table into a list of dictionaries with category fill-down."""
    lines = [line.strip() for line in content.strip().split('\n')]
    if len(lines) < 3:
        return []
    
    # Extract headers (first row)
    headers = [h.strip() for h in lines[0].split('|')][1:-1]
    data = []
    
    current_category = ""
    # Skip header and separator row
    for line in lines[2:]:
        if not line: continue
        cols = [c.strip() for c in line.split('|')][1:-1]
        if len(cols) == len(headers):
            row = dict(zip(headers, cols))
            if row.get('Catégorie', '').strip():
                current_category = row['Catégorie'].replace('**', '').strip()
            row['Catégorie'] = current_category
            data.append(row)
    return data

try:
    with open(LEVIERS_PATH, "r", encoding="utf-8") as f:
        leviers_content = f.read()
    levers_data = parse_markdown_table(leviers_content)
except Exception as e:
    levers_data = []
    print(f"Error loading {LEVIERS_PATH}: {e}")

def make_levers_table(levers_list):
    """Creates a styled Mantine table from a list of action levers."""
    if not levers_list:
        return dmc.Text("Aucun levier d'action répertorié pour cette catégorie.", c="dimmed", fs="italic")
    
    rows = []
    for item in levers_list:
        # Parse link if present: [text](url)
        link_content = item.get("Lien", "")
        link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', link_content)
        if link_match:
            link_node = html.A(
                dmc.Button(
                    link_match.group(1), 
                    variant="light", 
                    size="compact-xs", 
                    leftSection=DashIconify(icon="solar:link-bold", width=14),
                    radius="md",
                    className="premium-hover"
                ),
                href=link_match.group(2),
                target="_blank"
            )
        else:
            link_node = dmc.Text(link_content, size="sm", c="dimmed")

        rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Text(item.get("Levier d'action", ""), fw=500)),
                dmc.TableTd(dmc.Text(item.get("Source", ""), size="sm", c="dimmed")),
                dmc.TableTd(link_node),
            ])
        )
    
    head = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Levier d'action", style={"width": "45%"}),
            dmc.TableTh("Source institutionnelle", style={"width": "35%"}),
            dmc.TableTh("Lien direct et ressources", style={"width": "20%"}),
        ])
    )
    
    body = dmc.TableTbody(rows)
    
    return dmc.Table(
        [head, body], 
        striped=True, 
        highlightOnHover=True, 
        withTableBorder=True, 
        withColumnBorders=True,
    )

# Filter levers by theme
socio_levers = [l for l in levers_data if l['Catégorie'] == 'Socio-économique']
env_levers = [l for l in levers_data if l['Catégorie'] == 'Environnement']
acces_levers = [l for l in levers_data if l['Catégorie'] == 'Santé']

# Icons for themes
THEME_ICONS = {
    'socio': 'solar:users-group-rounded-bold-duotone',
    'env': 'solar:leaf-bold-duotone',
    'sante': 'solar:medical-kit-bold-duotone'
}

layout = dmc.Container(
    fluid=True,
    p=0,
    children=[
        dmc.Title("Leviers d'action et littérature", order=1, mb="xs", style={"color": "#2c3e50"}),
        dmc.Text(
            "Retrouvez ici des pistes de leviers d'actions existants selon les différentes thématiques socio-économiques, environnementales ou de santé.", 
            c="dimmed", size="lg", mb="xl"
        ),
        
        dmc.Tabs(
            id='levers-tabs',
            value='socio',
            variant="pills",
            radius="md",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("Socio-économique", value="socio", leftSection=DashIconify(icon=THEME_ICONS['socio'], width=18)),
                    dmc.TabsTab("Environnement", value="env", leftSection=DashIconify(icon=THEME_ICONS['env'], width=18)),
                    dmc.TabsTab("Santé", value="sante", leftSection=DashIconify(icon=THEME_ICONS['sante'], width=18)),
                ], mb="md"),
                
                dmc.TabsPanel(value='socio', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Leviers Socio-économiques", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Médiation en santé, dépistage mobile et sport-santé.", c="dimmed", mb="xl"),
                        make_levers_table(socio_levers)
                    ])
                ]),
                
                dmc.TabsPanel(value='env', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Leviers Environnementaux", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Urbanisme favorable, mobilités actives et qualité de l'air.", c="dimmed", mb="xl"),
                        make_levers_table(env_levers)
                    ])
                ]),
                
                dmc.TabsPanel(value='sante', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Leviers de Santé", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Coordination territoriale, télémédecine et parcours post-hospitalisation.", c="dimmed", mb="xl"),
                        make_levers_table(acces_levers)
                    ])
                ]),
            ]
        ),
        dmc.Space(h="xl")
    ]
)

@callback(
    Output('levers-tabs', 'value'),
    Input('url', 'hash'),
    prevent_initial_call=False
)
def update_levers_tab_from_url(hash_val):
    if not hash_val:
        return 'socio'
    clean_hash = hash_val.lstrip('#')
    if clean_hash in ['socio', 'env', 'sante']:
        return clean_hash
    if clean_hash == 'acces':
        return 'sante'
    return 'socio'


