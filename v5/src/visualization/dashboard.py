import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from src.data.fetcher import DataFetcher
from config import DB_PATH, TSX_SYMBOLS, START_DATE, END_DATE

# Initialize the Dash app
app = dash.Dash(__name__)

# Initialize the DataFetcher
data_fetcher = DataFetcher(DB_PATH)

# Layout of the dashboard
app.layout = html.Div(
    [
        html.H1("TSX Stock Dashboard"),
        # Stock selector dropdown
        dcc.Dropdown(
            id="stock-selector",
            options=[{"label": symbol, "value": symbol} for symbol in TSX_SYMBOLS],
            value=TSX_SYMBOLS[0],
        ),
        # Graph to display stock data
        dcc.Graph(id="stock-graph"),
    ]
)


# Callback to update the graph based on selected stock
@app.callback(Output("stock-graph", "figure"), [Input("stock-selector", "value")])
def update_graph(selected_stock):
    # Fetch data for the selected stock
    df = data_fetcher.get_stock_data_with_indicators(
        selected_stock, START_DATE, END_DATE
    )

    if df is None:
        return go.Figure()  # Return an empty figure if no data is available

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
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
