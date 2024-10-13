# src/visualization/components/screening_tab.py

import os
import yaml
from config import DB_PATH, TSX_SYMBOLS, START_DATE
from src.analysis.screener import Screener
from src.data.fetcher import DataService


def get_available_screeners():
    analysis_dir = os.path.join(os.path.dirname(__file__), "../../analysis")
    screener_files = [f for f in os.listdir(analysis_dir) if f.endswith(".yaml")]
    screener_names = [os.path.splitext(f)[0] for f in screener_files]
    return screener_names


def render_screening_tab():
    available_screeners = get_available_screeners()
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("Stock Screening", className="card-title"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Select Screeners"),
                                    dcc.Dropdown(
                                        id="screener-selector",
                                        options=[
                                            {"label": screener, "value": screener}
                                            for screener in available_screeners
                                        ],
                                        multi=True,
                                        placeholder="Select one or more screeners",
                                        className="mb-3",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Select Stocks"),
                                    dcc.Dropdown(
                                        id="stock-selector-screening",
                                        options=[
                                            {"label": symbol, "value": symbol}
                                            for symbol in TSX_SYMBOLS
                                        ],
                                        multi=True,
                                        placeholder="Select stocks or leave empty for all",
                                        className="mb-3",
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    dbc.Button(
                        "Run Screeners",
                        id="run-screeners-button",
                        color="primary",
                        className="mb-3",
                    ),
                    dbc.Spinner(
                        html.Div(id="screening-output"),
                        size="lg",
                        color="primary",
                        fullscreen=False,
                        className="mb-3",
                    ),
                    html.H5("Screening Results"),
                    dash_table.DataTable(
                        id="screening-results-table",
                        columns=[
                            {"name": "Symbol", "id": "symbol"},
                            {"name": "Screener", "id": "screener"},
                        ],
                        data=[],
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "textAlign": "left",
                            "padding": "5px",
                            "minWidth": "100px",
                            "width": "150px",
                            "maxWidth": "200px",
                        },
                        style_header={
                            "backgroundColor": "rgb(30, 30, 30)",
                            "color": "white",
                            "fontWeight": "bold",
                        },
                        style_data={
                            "backgroundColor": "rgb(50, 50, 50)",
                            "color": "white",
                        },
                        row_selectable="single",
                        selected_rows=[],
                    ),
                    html.H5("Stock Details"),
                    dcc.Graph(id="screening-stock-graph"),
                ]
            )
        ]
    )
