# src/visualization/components/backtesting_tab.py

import dash
from dash import html
import dash_bootstrap_components as dbc


def render_backtesting_tab():
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("Backtesting", className="card-title"),
                    html.P(
                        "Backtesting functionality is under development.",
                        className="card-text",
                    ),
                ]
            )
        ]
    )
