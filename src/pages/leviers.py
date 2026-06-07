import re
import dash
from dash import dcc, html, Input, Output, State, callback, ALL
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import os
import json
import time
import random
from ..data import BASE_DIR

# Database Paths & Server-Side Functions
LEVIERS_PATH = os.path.join(BASE_DIR, "Leviers d'action.md")
COLLAB_PATH = os.path.join(BASE_DIR, "collaborative_levers.json")

def load_collaborative_levers():
    """Loads all collaborative proposed levers shared across all users from the server JSON database."""
    if not os.path.exists(COLLAB_PATH):
        try:
            with open(COLLAB_PATH, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []
        except Exception as e:
            print(f"Error creating {COLLAB_PATH}: {e}")
            return []
    try:
        with open(COLLAB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {COLLAB_PATH}: {e}")
        return []

def save_collaborative_levers(levers_list):
    """Saves all collaborative levers securely into the shared server JSON database."""
    try:
        with open(COLLAB_PATH, "w", encoding="utf-8") as f:
            json.dump(levers_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {COLLAB_PATH}: {e}")
        return False

# Load original static Action Levers
def parse_markdown_table(content):
    """Parses a simple Markdown table into a list of dictionaries with category fill-down."""
    lines = [line.strip() for line in content.strip().split('\n')]
    if len(lines) < 3:
        return []
    
    headers = [h.strip() for h in lines[0].split('|')][1:-1]
    data = []
    
    current_category = ""
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
        elif link_content and link_content.startswith("http"):
            link_node = html.A(
                dmc.Button(
                    "Consulter", 
                    variant="light", 
                    size="compact-xs", 
                    leftSection=DashIconify(icon="solar:link-bold", width=14),
                    radius="md",
                    className="premium-hover"
                ),
                href=link_content,
                target="_blank"
            )
        else:
            link_node = dmc.Text(link_content or "N/A", size="sm", c="dimmed")

        source_node = dmc.Text(item.get("Source", ""), size="sm", c="dimmed")

        rows.append(
            dmc.TableTr([
                dmc.TableTd(dmc.Text(item.get("Levier d'action", ""), fw=500)),
                dmc.TableTd(source_node),
                dmc.TableTd(link_node),
            ])
        )
    
    head = dmc.TableThead(
        dmc.TableTr([
            dmc.TableTh("Levier d'action", style={"width": "45%"}),
            dmc.TableTh("Source & Origine", style={"width": "30%"}),
            dmc.TableTh("Lien direct & ressources", style={"width": "25%"}),
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

layout = dmc.Container(
    fluid=True,
    p=0,
    children=[
        # Form Modal for Proposing Levers (Markdown Generator)
        dmc.Modal(
            title="Proposer un nouveau levier d'action",
            id="add-lever-modal",
            opened=False,
            padding="xl",
            radius="lg",
            size="lg",
            children=[
                dmc.Stack(gap="md", children=[
                    dmc.Text(
                        "Vous pouvez proposer un nouveau levier d'action en copiant la ligne de code générée ci-dessous et en l'ajoutant directement au tableau sur GitHub.",
                        size="sm", c="dimmed"
                    ),
                    
                    dmc.Select(
                        id="add-lever-category",
                        label="Catégorie thématique",
                        data=[
                            {"value": "Socio-économique", "label": "Socio-économique"},
                            {"value": "Environnement", "label": "Environnement"},
                            {"value": "Santé", "label": "Santé"}
                        ],
                        value="Santé",
                        required=True,
                        radius="md"
                    ),
                    dmc.TextInput(
                        id="add-lever-title",
                        label="Titre du levier d'action",
                        placeholder="Ex: Distribution de paniers de fruits bio locaux hebdomadaires...",
                        required=True,
                        radius="md"
                    ),
                    dmc.TextInput(
                        id="add-lever-source",
                        label="Organisme porteur du projet",
                        placeholder="Ex: Mairie de Grenoble, Association Active...",
                        required=True,
                        radius="md"
                    ),
                    dmc.TextInput(
                        id="add-lever-link",
                        label="Lien web ou contact de ressource (Optionnel)",
                        placeholder="Ex: https://www.mon-association.fr",
                        radius="md"
                    ),
                    
                    # Markdown Row Display & Copy Section
                    dmc.Paper(
                        withBorder=True, p="md", radius="md", bg="gray.0",
                        children=[
                            dmc.Text("Ligne Markdown générée", fw=700, size="sm", mb=4, c="indigo.8"),
                            dmc.Text(
                                "Cette ligne sera automatiquement mise à jour. Copiez-la et collez-la à la fin du tableau sur GitHub.", 
                                size="xs", c="dimmed", mb=10
                            ),
                            dmc.Group(gap="sm", align="center", children=[
                                dmc.Code(
                                    id="generated-markdown-line",
                                    block=True,
                                    style={
                                        "flex": 1,
                                        "padding": "12px",
                                        "overflowX": "auto",
                                        "border": "1px solid #dee2e6",
                                        "fontSize": "13px",
                                        "backgroundColor": "#fff"
                                    }
                                ),
                                dcc.Clipboard(
                                    target_id="generated-markdown-line",
                                    title="Copier la ligne",
                                    style={
                                        "padding": "10px",
                                        "border": "1px solid #dee2e6",
                                        "borderRadius": "6px",
                                        "cursor": "pointer",
                                        "backgroundColor": "#fff",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center"
                                    }
                                )
                            ])
                        ]
                    ),
                    
                    # Action buttons
                    dmc.Group(justify="flex-end", gap="sm", style={"marginTop": "15px"}, children=[
                        dmc.Button("Fermer", id="cancel-lever-btn", color="gray", variant="light", radius="md"),
                        html.A(
                            dmc.Button(
                                "Ouvrir le fichier sur GitHub", 
                                id="github-open-btn",
                                color="indigo", 
                                radius="md",
                                leftSection=DashIconify(icon="solar:link-bold", width=16)
                            ),
                            href="https://github.com/raphaelcontri/SeniAura/edit/main/Leviers%20d'action.md",
                            target="_blank",
                            style={"textDecoration": "none"}
                        )
                    ])
                ])
            ]
        ),
        
        dmc.Title("Leviers d'action et littérature", order=1, mb="xs", style={"color": "#2c3e50"}),
        dmc.Text(
            "Retrouvez ici des pistes de leviers d'actions existants selon les différentes thématiques, ou contribuez à enrichir la base commune.", 
            c="dimmed", size="lg", mb="xl"
        ),
        
        # --- Section 1: Collaborative Banner ---
        dmc.Paper(
            id='collab-banner-paper',
            withBorder=True, shadow="md", p="xl", radius="lg",
            bg="indigo.0",
            style={"borderColor": "#3b5bdb", "borderWidth": "1.5px", "marginBottom": "30px"},
            children=[
                dmc.Group(justify="space-between", align="center", gap="md", children=[
                    dmc.Group(gap="md", children=[
                        dmc.ThemeIcon(
                            DashIconify(icon="solar:users-group-rounded-bold-duotone", width=26),
                            variant="filled", color="indigo", radius="md", size="lg"
                        ),
                        dmc.Stack(gap=2, children=[
                            dmc.Text("Espace Réseau Territorial & Collaboratif", fw=800, size="lg", c="indigo.9"),
                            dmc.Text("Générez une ligne au format Markdown pour soumettre vos propres initiatives locales et enrichir la base commune.", size="sm", c="indigo.7")
                        ])
                    ]),
                    dmc.Button(
                        "Proposer un levier d'action",
                        id="open-add-modal-btn",
                        radius="md",
                        size="md",
                        color="indigo",
                        leftSection=DashIconify(icon="solar:add-circle-bold", width=18),
                        className="premium-hover"
                    )
                ])
            ]
        ),
        
        # --- Section 2: Reference knowledgebase tabs ---
        dmc.Tabs(
            id='levers-tabs',
            value='socio',
            variant="pills",
            radius="md",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("Socio-économique", value="socio", leftSection=DashIconify(icon='solar:users-group-rounded-bold-duotone', width=18)),
                    dmc.TabsTab("Environnement", value="env", leftSection=DashIconify(icon='solar:leaf-bold-duotone', width=18)),
                    dmc.TabsTab("Santé", value="sante", leftSection=DashIconify(icon='solar:medical-kit-bold-duotone', width=18)),
                ], mb="md"),
                
                dmc.TabsPanel(value='socio', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Leviers Socio-économiques", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Médiation en santé, dépistage mobile et sport-santé.", c="dimmed", mb="xl"),
                        html.Div(id='socio-table-container')
                    ])
                ]),
                
                dmc.TabsPanel(value='env', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Leviers Environnementaux", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Urbanisme favorable, mobilités actives et qualité de l'air.", c="dimmed", mb="xl"),
                        html.Div(id='env-table-container')
                    ])
                ]),
                
                dmc.TabsPanel(value='sante', children=[
                    dmc.Paper(withBorder=True, p="xl", radius="md", shadow="sm", children=[
                        dmc.Title("Leviers de Santé", order=3, mb="xs", c="#2c3e50"),
                        dmc.Text("Coordination territoriale, télémédecine et parcours post-hospitalisation.", c="dimmed", mb="xl"),
                        html.Div(id='sante-table-container')
                    ])
                ]),
            ]
        ),
        dmc.Space(h="xl")
    ]
)

# --- Callbacks ---

@callback(
    Output('levers-tabs', 'value'),
    [Input('url', 'hash')],
    [State('url', 'pathname')],
    prevent_initial_call=False
)
def update_levers_tab_from_url(hash_val, pathname):
    if pathname != '/leviers':
        raise PreventUpdate
    if not hash_val:
        return 'socio'
    clean_hash = hash_val.lstrip('#')
    if clean_hash in ['socio', 'env', 'sante']:
        return clean_hash
    if clean_hash == 'acces':
        return 'sante'
    return 'socio'

# Callback to dynamically load and update all tables in real-time
@callback(
    [Output('socio-table-container', 'children'),
     Output('env-table-container', 'children'),
     Output('sante-table-container', 'children')],
    [Input('url', 'pathname')]
)
def update_all_levers_tables(pathname):
    if pathname != '/leviers':
        raise PreventUpdate
    # Filter by category from static levers_data
    socio = [l for l in levers_data if l.get('Catégorie') == 'Socio-économique']
    env = [l for l in levers_data if l.get('Catégorie') == 'Environnement']
    sante = [l for l in levers_data if l.get('Catégorie') == 'Santé']
    
    return make_levers_table(socio), make_levers_table(env), make_levers_table(sante)

# Callback to manage Modal popup and reset values
@callback(
    [Output('add-lever-modal', 'opened'),
     Output('add-lever-title', 'value'),
     Output('add-lever-source', 'value'),
     Output('add-lever-link', 'value')],
    [Input('open-add-modal-btn', 'n_clicks'),
     Input('cancel-lever-btn', 'n_clicks')],
    [State('add-lever-modal', 'opened')],
    prevent_initial_call=True
)
def toggle_modal_and_reset(n_open, n_cancel, is_opened):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_opened, dash.no_update, dash.no_update, dash.no_update
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == 'cancel-lever-btn':
        return False, "", "", ""
    if trigger_id == 'open-add-modal-btn' and n_open:
        return True, "", "", ""
    return is_opened, dash.no_update, dash.no_update, dash.no_update

# Callback to generate Markdown line dynamically
@callback(
    [Output('generated-markdown-line', 'children'),
     Output('github-open-btn', 'disabled')],
    [Input('add-lever-category', 'value'),
     Input('add-lever-title', 'value'),
     Input('add-lever-source', 'value'),
     Input('add-lever-link', 'value')]
)
def update_markdown_line(category, title, source, link):
    if not title or not title.strip() or not source or not source.strip():
        return "Veuillez saisir un titre et un organisme porteur...", True
    
    # Escape markdown pipes in fields to prevent breaking the table format
    clean_title = title.replace('|', '\\|').strip()
    clean_source = source.replace('|', '\\|').strip()
    
    if link and link.strip():
        clean_link = link.replace('|', '\\|').strip()
        link_markdown = f"[Lien]({clean_link})"
    else:
        link_markdown = ""
        
    markdown_line = f"| {category} | {clean_title} | {clean_source} | {link_markdown} |"
    return markdown_line, False

