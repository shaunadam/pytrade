import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from src.data.fetcher import DataFetcher
from config import DB_PATH, TSX_SYMBOLS, START_DATE
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import threading

# Initialize the Dash app with a dark Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)

# Custom CSS for dark theme dropdown and date range selector
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .Select-control, .Select-menu-outer {
                background-color: #333 !important;
                color: white;
            }
            .Select-value-label {
                color: white !important;
            }
            .Select-menu-outer .Select-option {
                background-color: #333;
                color: white;
            }
            .Select-menu-outer .Select-option:hover {
                background-color: #555;
            }
            .Select-arrow {
                border-color: white transparent transparent;
            }
            .is-open > .Select-control .Select-arrow {
                border-color: transparent transparent white;
            }
            .DateInput, .DateInput_input {
                background-color: #333;
                color: white;
            }
            .DateRangePickerInput {
                background-color: #333;
            }
            .DateRangePickerInput_arrow {
                color: white;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

# Initialize the DataFetcher
data_fetcher = DataFetcher(DB_PATH)

# Calculate date range
end_date = datetime.now().date()
start_date = pd.to_datetime(START_DATE).date()

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

# Layout of the dashboard
app.layout = dbc.Container(
    [
        html.H1("TSX Swing Trading Dashboard", className="my-4"),
        dcc.Store(
            id="session",
            data={
                "selected_stock": TSX_SYMBOLS[0],
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
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
    ]
)


def render_utilities_tab(session_data):
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H4("Override Date Range"),
                                    dcc.DatePickerRange(
                                        id="override-date-range",
                                        min_date_allowed=start_date,
                                        max_date_allowed=end_date,
                                        start_date=session_data["start_date"],
                                        end_date=session_data["end_date"],
                                        className="mb-3",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.H4("Update Stock Data"),
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


# Update the render_tab_content function to include the Utilities tab
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
    Input("session", "data"),
)
def render_tab_content(active_tab, session_data):
    if active_tab == "analysis":
        return render_analysis_tab(session_data)
    elif active_tab == "screening":
        return html.P("Stock Screening tab content (to be implemented)")
    elif active_tab == "backtesting":
        return html.P("Backtesting tab content (to be implemented)")
    elif active_tab == "utilities":
        return render_utilities_tab(session_data)


# Add a new callback for the download button and progress updates
@app.callback(
    Output("download-status", "children"),
    Output("download-progress-interval", "disabled"),
    Input("download-button", "n_clicks"),
    Input("download-progress-interval", "n_intervals"),
    State("override-date-range", "start_date"),
    State("override-date-range", "end_date"),
    prevent_initial_call=True,
)
def update_stock_data(n_clicks, n_intervals, start_date, end_date):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "download-button" and n_clicks:
        # Start the download process in a separate thread
        threading.Thread(
            target=data_fetcher.update_all_stocks,
            args=(TSX_SYMBOLS, start_date, end_date),
        ).start()
        return [
            dbc.Progress(value=0, id="download-progress"),
            html.Div(id="download-message", children="Initializing..."),
        ], False

    if trigger_id == "download-progress-interval":
        # Update the progress bar and message
        progress, message = data_fetcher.get_update_progress()
        if progress < 100:
            return [
                dbc.Progress(value=progress, id="download-progress"),
                html.Div(id="download-message", children=message),
            ], False
        else:
            return f"Download complete: {message}", True

    return dash.no_update, dash.no_update


def render_analysis_tab(session_data):
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        id="stock-selector",
                                        options=[
                                            {"label": symbol, "value": symbol}
                                            for symbol in TSX_SYMBOLS
                                        ],
                                        value=session_data["selected_stock"],
                                        className="mb-3",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                range_name,
                                                id=f"range-{range_name}",
                                                n_clicks=0,
                                            )
                                            for range_name in date_ranges.keys()
                                        ],
                                        className="mb-3",
                                    ),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        min_date_allowed=start_date,
                                        max_date_allowed=end_date,
                                        start_date=session_data["start_date"],
                                        end_date=session_data["end_date"],
                                        className="mb-3",
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    dcc.Graph(id="stock-graph"),
                    dcc.Loading(
                        id="loading",
                        type="default",
                        children=html.Div(id="loading-output"),
                    ),
                ]
            )
        ]
    )


@app.callback(
    Output("date-range", "start_date"),
    Output("date-range", "end_date"),
    [Input(f"range-{range_name}", "n_clicks") for range_name in date_ranges.keys()],
    State("date-range", "start_date"),
    State("date-range", "end_date"),
)
def update_date_range(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    range_name = button_id.split("-")[1]

    end_date = datetime.now().date()

    if range_name == "MAX":
        return start_date.isoformat(), end_date.isoformat()
    elif range_name == "YTD":
        return datetime(end_date.year, 1, 1).date().isoformat(), end_date.isoformat()
    else:
        delta = date_ranges[range_name]
        return (end_date - delta).isoformat(), end_date.isoformat()


@app.callback(
    Output("stock-graph", "figure"),
    Input("stock-selector", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def update_graph(selected_stock, start_date, end_date):
    if not selected_stock or not start_date or not end_date:
        # Return empty figure if inputs are not ready
        return go.Figure()

    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()

    df = data_fetcher.get_stock_data_with_indicators(
        selected_stock, start_date, end_date
    )

    if df is None or df.empty:
        # Return a figure with a text annotation if no data is available
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for the selected stock and date range",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        fig.update_layout(
            title=f"{selected_stock} - No Data Available",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_dark",
        )
        return fig

    candlestick = go.Candlestick(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Price",
    )

    traces = [candlestick]

    # Add SMA and EMA traces if available
    if "SMA50" in df.columns:
        sma_trace = go.Scatter(
            x=df.index,
            y=df["SMA50"],
            mode="lines",
            name="SMA50",
            line=dict(color="blue"),
        )
        traces.append(sma_trace)

    if "EMA50" in df.columns:
        ema_trace = go.Scatter(
            x=df.index,
            y=df["EMA50"],
            mode="lines",
            name="EMA50",
            line=dict(color="orange"),
        )
        traces.append(ema_trace)

    fig = go.Figure(data=traces)

    fig.update_layout(
        title=f"{selected_stock} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)


@app.callback(
    Output("session", "data"),
    Input("stock-selector", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    State("session", "data"),
)
def update_session(selected_stock, start_date, end_date, session_data):
    if selected_stock and start_date and end_date:
        session_data.update(
            {
                "selected_stock": selected_stock,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
    return session_data


if __name__ == "__main__":
    app.run_server(debug=True)
