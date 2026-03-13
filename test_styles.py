import dash
from dash import html, Output, Input, dcc
import dash_mantine_components as dmc

app = dash.Dash(__name__)

test_style = {
    "root": {
        "borderRadius": "12px",
        "marginBottom": "8px",
        "transition": "all 200ms ease",
        "color": "#495057",
        "backgroundColor": "transparent",
        "&:hover": {
            "backgroundColor": "#f8f9fa",
            "transform": "translateX(5px)"
        },
        "&[data-active]": {
            "backgroundColor": "#339af0 !important",
            "color": "white !important"
        }
    },
    "label": {"fontSize": "15px", "fontWeight": 600},
    "icon": {"marginRight": "10px"}
}

app.layout = dmc.MantineProvider([
    dmc.NavLink(label="Home", active=True, styles=test_style),
    dmc.NavLink(label="Away", active=False, styles=test_style)
])

if __name__ == '__main__':
    app.run_server(port=8051, debug=False)
