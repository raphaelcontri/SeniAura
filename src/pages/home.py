from dash import dcc, html
import dash_mantine_components as dmc
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

layout = dmc.Container(
    size="xl",
    mt="xl",
    children=[
        dmc.Title(
            "SeniAura : Diagnostic des maladies Cardio-Neuro-Vasculaires en Auvergne Rhône-Alpes",
            order=1,
            ta="center",
            mb="xl",
            c="blue"
        ),
        dmc.Paper(
            shadow="lg",
            p="xl",
            radius="md",
            withBorder=True,
            children=[
                dcc.Markdown(intro_text, className="intro-text")
            ]
        )
    ]
)
