from dash import dcc, html
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import os
from ..data import BASE_DIR

# Load Action Levers (Leviers d'action)
LEVIERS_PATH = os.path.join(BASE_DIR, "Leviers d'action.md")
try:
    with open(LEVIERS_PATH, "r", encoding="utf-8") as f:
        leviers_content = f.read()
except Exception as e:
    leviers_content = f"### Leviers d'action non disponibles.\n\nErreur lors du chargement : {e}"

layout = dmc.Container(
    fluid=True,
    p=0,
    children=[
        dmc.Title("Leviers d'action et littérature", order=1, mb="xs", style={"color": "#2c3e50"}),
        dmc.Text(
            "Retrouvez ici les leviers d'intervention et les références scientifiques structurant l'approche de CardiAURA.", 
            c="dimmed", size="lg", mb="xl"
        ),
        
        dmc.Paper(
            withBorder=True, p="xl", radius="md", shadow="sm",
            children=[
                dmc.Box(
                    className="markdown-container",
                    children=[
                        dcc.Markdown(
                            leviers_content,
                            link_target="_blank",
                            className="methodo-markdown"
                        )
                    ]
                )
            ]
        ),
        dmc.Space(h="xl")
    ]
)
