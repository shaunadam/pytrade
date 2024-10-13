# src/visualization/components/utilities_tab.py

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from config import START_DATE, END_DATE
from datetime import datetime
import dash


def render_utilities_tab(session_data):
    """
    Renders the Utilities tab layout.

    Args:
        session_data (dict): Contains session-specific data like selected date range.

    Returns:
        dbc.Card: The layout for the Utilities tab.
    """
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H4("Override Date Range", className="mb-3"),
                                    dcc.DatePickerRange(
                                        id="override-date-range",
                                        min_date_allowed=datetime.strptime(
                                            START_DATE, "%Y-%m-%d"
                                        ).date(),
                                        max_date_allowed=datetime.now().date(),
                                        start_date=session_data.get(
                                            "start_date", START_DATE
                                        ),
                                        end_date=session_data.get("end_date", END_DATE),
                                        className="mb-3",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.H4("Update Stock Data", className="mb-3"),
                                    dbc.Button(
                                        "Download Stock Data",
                                        id="download-button",
                                        color="primary",
                                        className="mb-3",
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(id="download-status"),
                                    dcc.Interval(
                                        id="download-progress-interval",
                                        interval=1000,  # in milliseconds
                                        n_intervals=0,
                                        disabled=True,
                                    ),
                                ]
                            )
                        ]
                    ),
                ]
            )
        ]
    )
