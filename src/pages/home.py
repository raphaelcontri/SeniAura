from dash import dcc, html, Input, Output, callback, clientside_callback, State, no_update, ClientsideFunction
import dash_mantine_components as dmc
import os
from pathlib import Path
from dash_iconify import DashIconify

# Robust path resolution
current_dir = Path(__file__).parent
try:
    # Go up two levels from src/pages to reach dashboard interactif
    text_path = current_dir.parent.parent / "texte introductif du dashboard.txt"
    with open(text_path, "r", encoding="utf-8") as f:
        intro_text = f.read()
except FileNotFoundError:
    intro_text = "Le fichier de texte introductif est introuvable."

# Parse sections separated by "\n> "
parts = intro_text.split("\n> ")

intro_block = parts[0]
if intro_block.startswith("> "):
    intro_block = intro_block[2:]

ICON_MAP = {
    "objectif": "solar:target-bold",
    "EPCI": "solar:map-point-bold",
    "destinataires": "solar:users-group-rounded-bold",
    "Qui sommes-nous": "solar:user-bold",
    "Prise en main": "solar:play-bold",
    "Vidéo": "solar:videocamera-bold",
    "maladies": "solar:heart-bold",
    "cardio": "solar:heart-bold"
}

accordion_items = []
for p in parts[1:]:
    lines = p.split("\n", 1)
    if len(lines) == 2:
        title, content = lines
        
        # Find suitable icon
        left_icon = "solar:info-circle-bold"
        for key, ico in ICON_MAP.items():
            if key.lower() in title.lower():
                left_icon = ico
                break
                
        # Assign ID to "Prise en main" specifically for scrolling
        item_id = "accordion-item-prise-en-main" if title.strip() == "Prise en main" else None
        
        # Dash IDs must be strings, not None
        acc_item_props = {"children": [
                    dmc.AccordionControl(
                        title, 
                        icon=DashIconify(icon=left_icon, width=22, color="#339af0"),
                        style={"fontWeight": 800, "fontSize": "17px", "color": "#1a1b1e"}
                    ),
                    dmc.AccordionPanel(dcc.Markdown(content, className="intro-text"))
                ], "value": title}
        if item_id:
            acc_item_props["id"] = item_id
            
        accordion_items.append(dmc.AccordionItem(**acc_item_props))

layout = dmc.Container(
    size="lg", # Large instead of xl for better read flow
    mt="xl",
    mb="60px",
    children=[
        dmc.Title(
            "CardiAURA : Diagnostic des maladies Cardio-Neuro-Vasculaires en Auvergne Rhône-Alpes",
            order=1,
            ta="center",
            mb="xl",
            c="blue.8",
            style={"fontWeight": 900, "letterSpacing": "0.5px"}
        ),
        
        # Intro Box
        dmc.Paper(
            shadow="md",
            p="xl",
            radius="lg",
            withBorder=True,
            mb="xl",
            style={"backgroundColor": "#ffffff", "border": "1px solid #e9ecef"},
            children=[
                dcc.Markdown(intro_block, className="intro-text"),
                dmc.Group(
                    justify="center",
                    gap="md",
                    mt="xl",
                    children=[
                        dcc.Link(
                            href="/exploration",
                            style={"textDecoration": "none"},
                            children=dmc.Button(
                                "Démarrer le diagnostic géographique (Exploration)",
                                size="lg",
                                radius="xl",
                                variant="gradient",
                                gradient={"from": "blue", "to": "cyan", "deg": 45},
                                leftSection=DashIconify(icon="solar:map-bold-duotone", width=24),
                                style={
                                    "boxShadow": "0 8px 20px rgba(51, 154, 240, 0.3)",
                                    "fontWeight": 800,
                                    "paddingLeft": "30px",
                                    "paddingRight": "30px",
                                    "transition": "transform 200ms ease"
                                }
                            )
                        ),
                        dmc.Button(
                            "Prise en main",
                            id="btn-prise-en-main",
                            size="lg",
                            radius="xl",
                            variant="gradient",
                            gradient={"from": "indigo", "to": "cyan", "deg": 45},
                            leftSection=DashIconify(icon="solar:play-bold", width=24),
                            style={
                                "boxShadow": "0 8px 20px rgba(51, 154, 240, 0.2)",
                                "fontWeight": 800,
                                "paddingLeft": "30px",
                                "paddingRight": "30px",
                                "transition": "transform 200ms ease"
                            }
                        ),
                        html.Div(id="btn-prise-en-main-dummy", style={"display": "none"})
                    ]
                )
            ]
        ),
        
        # Accordion for the rest of the text
        html.Div(id="home-accordion-section", children=[
            dmc.Accordion(
                id="home-accordion",
                children=accordion_items,
                variant="separated",
                radius="md",
                chevronPosition="right",
                value=parts[1].split("\n", 1)[0] if len(parts) > 1 else None,
                styles={
                    "item": {
                        "border": "1.5px solid #339af0",
                        "boxShadow": "0 2px 5px rgba(0,0,0,0.05)",
                        "transition": "all 200ms ease"
                    }
                }
            )
        ])
    ]
)

# Callback to open the 'Prise en main' section on button click
@callback(
    Output("home-accordion", "value"),
    Input("btn-prise-en-main", "n_clicks"),
    State("home-accordion", "value"),
    prevent_initial_call=True
)
def open_prise_en_main(n_clicks, current_value):
    if n_clicks is None:
        return no_update
    
    # Robustly find the title containing "Prise en main"
    target_title = None
    for p in parts[1:]:
        title = p.split("\n", 1)[0].strip()
        if "Prise en main" in title:
            target_title = title
            break
            
    return target_title if target_title else no_update

# Client-side callback for smooth scroll with header offset
clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='scrollToAccordion'
    ),
    Output('btn-prise-en-main-dummy', 'children'),
    Input('btn-prise-en-main', 'n_clicks'),
    prevent_initial_call=True
)
