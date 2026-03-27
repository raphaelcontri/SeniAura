from dash import dcc, html
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
                
        accordion_items.append(
            dmc.AccordionItem(
                [
                    dmc.AccordionControl(
                        title, 
                        icon=DashIconify(icon=left_icon, width=22, color="#339af0"),
                        style={"fontWeight": 800, "fontSize": "17px", "color": "#1a1b1e"}
                    ),
                    dmc.AccordionPanel(dcc.Markdown(content, className="intro-text"))
                ],
                value=title
            )
        )

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
                dmc.Center(
                    mt="xl",
                    children=dcc.Link(
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
                    )
                )
            ]
        ),
        
        # Accordion for the rest of the text
        dmc.Accordion(
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
    ]
)
