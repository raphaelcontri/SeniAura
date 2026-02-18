
from dash import dcc, html


# Read the introductory text
import os
from pathlib import Path

# Robust path resolution
current_dir = Path(__file__).parent
try:
    # Go up two levels from src/pages to reach dashboard interactif
    text_path = current_dir.parent.parent / "texte introductif du dashboard.txt"
    with open(text_path, "r", encoding="utf-8") as f:
        intro_text = f.read()
except FileNotFoundError:
    intro_text = "Le fichier de texte introductif est introuvable."

layout = html.Div(className='home-container', children=[
    
    # Left Column: Header + Nav Buttons
    html.Div(className='home-left-column', children=[
        html.Div(className='home-header', children=[
            html.H1("SeniAura : Diagnostic des maladies Cardio-Neuro-Vasculaires en Auvergne Rhone-Alpes", className='main-title'),
            html.P("", className='subtitle'),
        ]),
        


        # Navigation cards removed as per user request (moved to sidebar)
    ]),

    # Right Column: Scrollable Introductory Text
    html.Div(className='intro-text-container', children=[
        dcc.Markdown(intro_text)
    ])
])

