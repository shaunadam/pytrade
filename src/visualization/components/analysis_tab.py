import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from config import TSX_SYMBOLS, START_DATE, END_DATE
from datetime import datetime, timedelta


def render_analysis_tab(session_data):
    """
    Renders the Technical Analysis tab layout.

    Args:
        session_data (dict): Contains session-specific data like selected stock and date range.

    Returns:
        dbc.Card: The layout for the Technical Analysis tab.
    """
    # Preset date ranges
    date_ranges = {
        "1W": timedelta(days=7),
        "1M": timedelta(days=30),
        "3M": timedelta(days=90),
        "6M": timedelta(days=180),
        "1Y": timedelta(days=365),
        "YTD": None,  # Special case, handled in callback
        "MAX": None,  # Special case, uses start_date
    }

    # Calculate default date range
    end_date = datetime.now().date()
    start_date = datetime.strptime(
        session_data.get("start_date", START_DATE), "%Y-%m-%d"
    ).date()

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Select Stock"),
                                    dcc.Dropdown(
                                        id="stock-selector",
                                        options=[
                                            {"label": symbol, "value": symbol}
                                            for symbol in TSX_SYMBOLS
                                        ],
                                        value=session_data.get(
                                            "selected_stock", TSX_SYMBOLS[0]
                                        ),
                                        className="mb-3",
                                        style={
                                            "backgroundColor": "#343a40",
                                            "color": "white",
                                            "border": "1px solid #495057",
                                        },
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Select Date Range"),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                range_name,
                                                id=f"range-{range_name}",
                                                n_clicks=0,
                                                color="secondary",
                                                className="me-1",
                                            )
                                            for range_name in date_ranges.keys()
                                        ],
                                        className="mb-3",
                                    ),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        min_date_allowed=datetime.strptime(
                                            START_DATE, "%Y-%m-%d"
                                        ).date(),
                                        max_date_allowed=end_date,
                                        start_date=session_data.get(
                                            "start_date", START_DATE
                                        ),
                                        end_date=session_data.get(
                                            "end_date", end_date.isoformat()
                                        ),
                                        className="mb-3",
                                        style={
                                            "backgroundColor": "#343a40",
                                            "color": "white",
                                        },
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    # Arrange graphs in a responsive grid
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(id="price-indicators-graph"), md=12, lg=12
                            ),
                            dbc.Col(dcc.Graph(id="volume-graph"), md=12, lg=12),
                        ],
                        className="mb-4",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(dcc.Graph(id="macd-graph"), md=12, lg=12),
                            dbc.Col(dcc.Graph(id="rsi-graph"), md=12, lg=12),
                        ],
                        className="mb-4",
                    ),
                    dcc.Loading(
                        id="loading",
                        type="default",
                        children=html.Div(id="loading-output"),
                    ),
                ]
            )
        ]
    )
