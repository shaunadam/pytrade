import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from src.data.fetcher import DataFetcher
from config import DB_PATH, TSX_SYMBOLS
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Initialize the DataFetcher
data_fetcher = DataFetcher(DB_PATH)

# Initialize the data cache
data_cache = {}

# Calculate default date range
end_date = datetime.now().date()
start_date = end_date - timedelta(days=180)

# Layout of the dashboard
app.layout = dbc.Container(
    [
        html.H1("TSX Stock Dashboard", className="my-4"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Stock selector dropdown
                        dcc.Dropdown(
                            id="stock-selector",
                            options=[
                                {"label": symbol, "value": symbol}
                                for symbol in TSX_SYMBOLS
                            ],
                            value=TSX_SYMBOLS[0],
                            className="mb-3",
                        ),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        # Date range selector
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=start_date,
                            max_date_allowed=end_date,
                            start_date=start_date,
                            end_date=end_date,
                            className="mb-3",
                        ),
                    ],
                    width=6,
                ),
            ]
        ),
        # Graph to display stock data
        dcc.Graph(id="stock-graph"),
        # Loading spinner
        dcc.Loading(
            id="loading", type="default", children=html.Div(id="loading-output")
        ),
    ]
)


# Callback to update the graph based on selected stock and date range
@app.callback(
    Output("stock-graph", "figure"),
    [
        Input("stock-selector", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_graph(selected_stock, start_date, end_date):
    # Convert string dates to datetime.date objects
    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()

    # Check if data is in cache, if not fetch and store it
    if selected_stock not in data_cache:
        df = data_fetcher.get_stock_data_with_indicators(
            selected_stock, start_date, end_date
        )
        data_cache[selected_stock] = df
    else:
        df = data_cache[selected_stock]

        # Check if cached data covers the selected date range
        if df.index.min().date() > start_date or df.index.max().date() < end_date:
            df = data_fetcher.get_stock_data_with_indicators(
                selected_stock, start_date, end_date
            )
            data_cache[selected_stock] = df

    if df is None or df.empty:
        return go.Figure()  # Return an empty figure if no data is available

    # Filter data based on selected date range
    df = df.loc[
        (pd.to_datetime(df.index) >= pd.to_datetime(start_date))
        & (pd.to_datetime(df.index) <= pd.to_datetime(end_date))
    ]

    # Create the candlestick trace
    candlestick = go.Candlestick(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Price",
    )

    # Create traces for SMA and EMA
    sma_trace = go.Scatter(
        x=df.index, y=df["SMA"], mode="lines", name="SMA", line=dict(color="blue")
    )
    ema_trace = go.Scatter(
        x=df.index, y=df["EMA"], mode="lines", name="EMA", line=dict(color="orange")
    )

    # Create the figure
    fig = go.Figure(data=[candlestick, sma_trace, ema_trace])

    # Update the layout
    fig.update_layout(
        title=f"{selected_stock} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
