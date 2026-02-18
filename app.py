
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import os

# Import pages
from src.pages import home, map, radar, methodology


# Setup
external_stylesheets = ['https://use.fontawesome.com/releases/v5.15.4/css/all.css']
app = dash.Dash(__name__, title="SeniAURA Dashboard", suppress_callback_exceptions=True, external_stylesheets=external_stylesheets)
server = app.server

# Sidebar Layout
sidebar = html.Div(className='sidebar', children=[
    html.H2("SeniAURA", style={'color': 'white', 'textAlign': 'center', 'marginBottom': '30px', 'cursor': 'pointer'}),
    
    html.Nav(className='nav-menu', children=[
        dcc.Link(href='/', className='nav-link', children=[
            html.I(className="fas fa-home", style={'marginRight': '10px'}), "Accueil"
        ]),
        dcc.Link(href='/carte', className='nav-link', children=[
            html.I(className="fas fa-map-marked-alt", style={'marginRight': '10px'}), "Carte Interactive"
        ]),
        dcc.Link(href='/radar', className='nav-link', children=[
            html.I(className="fas fa-chart-line", style={'marginRight': '10px'}), "Radar Comparatif"
        ]),
        dcc.Link(href='/methodologie', className='nav-link', children=[
            html.I(className="fas fa-book", style={'marginRight': '10px'}), "Méthodologie"
        ]),
    ]),

    html.Div(className='sidebar-footer', style={'marginTop': 'auto', 'textAlign': 'center', 'color': '#bdc3c7', 'fontSize': '0.8rem'}, children=[
        html.P("HEC Capstone Project"),
        html.P("v2.1 - 2026")
    ])
])

# Main Layout
app.layout = html.Div(className='app-container', children=[
    dcc.Location(id='url', refresh=False),
    
    # Sidebar
    sidebar,
    
    # Content
    html.Div(id='page-content', className='content', style={'padding': '20px', 'height': '100vh', 'overflow': 'auto'})
])

# Routing Callback
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/carte':
        return map.layout
    elif pathname == '/radar':
        return radar.layout
    elif pathname == '/methodologie':
        return methodology.layout
    else:
        return home.layout

if __name__ == '__main__':
    app.run(debug=True, port=8050)
