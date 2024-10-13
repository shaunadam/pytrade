# src/visualization/dashboard.py

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from src.visualization.components import (
    render_analysis_tab,
    render_backtesting_tab,
    render_screening_tab,
    render_utilities_tab,
)
from src.visualization.callbacks import (
    register_analysis_callbacks,
    register_backtesting_callbacks,
    register_screening_callbacks,
    register_utilities_callbacks,
)
from config import DB_PATH, TSX_SYMBOLS, START_DATE
from datetime import datetime, timedelta
import os

# Initialize the Dash app with a dark Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)

# Layout of the dashboard
app.layout = dbc.Container(
    [
        html.H1("TSX Swing Trading Dashboard", className="my-4"),
        dcc.Store(
            id="session",
            data={
                "selected_stock": TSX_SYMBOLS[0],
                "start_date": START_DATE,
                "end_date": datetime.now().date().isoformat(),
            },
        ),
        dbc.Tabs(
            [
                dbc.Tab(label="Technical Analysis", tab_id="analysis"),
                dbc.Tab(label="Stock Screening", tab_id="screening"),
                dbc.Tab(label="Backtesting", tab_id="backtesting"),
                dbc.Tab(label="Utilities", tab_id="utilities"),
            ],
            id="tabs",
            active_tab="analysis",
        ),
        html.Div(id="tab-content", className="mt-4"),
    ],
    fluid=True,
)


# Callback to render the content of each tab
@app.callback(
    dash.Output("tab-content", "children"),
    [dash.Input("tabs", "active_tab")],
    [dash.State("session", "data")],
    prevent_initial_call=True,
)
def render_tab_content(active_tab, session_data):
    if active_tab == "analysis":
        return render_analysis_tab(session_data)
    elif active_tab == "screening":
        return render_screening_tab()
    elif active_tab == "backtesting":
        return render_backtesting_tab()
    elif active_tab == "utilities":
        return render_utilities_tab(session_data)
    else:
        return html.P("Tab not found")


# Register Callbacks
register_analysis_callbacks(app)
register_screening_callbacks(app)
register_utilities_callbacks(app)
register_backtesting_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)
