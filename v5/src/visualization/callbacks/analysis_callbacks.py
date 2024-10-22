from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from src.data.fetcher import DataService
from config import DB_PATH, TSX_SYMBOLS, START_DATE
import pandas as pd
import dash
import logging
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)

# Define date_ranges locally
date_ranges = {
    "1W": timedelta(days=7),
    "1M": timedelta(days=30),
    "3M": timedelta(days=90),
    "6M": timedelta(days=180),
    "1Y": timedelta(days=365),
    "YTD": None,  # Special case, handled in callback
    "MAX": None,  # Special case, uses start_date
}


def create_price_indicators_fig(df, selected_stock):
    candlestick = go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Price",
    )
    sma = go.Scatter(
        x=df["date"],
        y=df["SMA50"],
        mode="lines",
        name="SMA50",
        line=dict(color="blue"),
    )
    ema = go.Scatter(
        x=df["date"],
        y=df["EMA50"],
        mode="lines",
        name="EMA50",
        line=dict(color="orange"),
    )
    fig = go.Figure(data=[candlestick, sma, ema])
    fig.update_layout(
        title=f"{selected_stock} Price and Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
    )
    return fig


def create_volume_fig(df, selected_stock):
    volume = go.Bar(
        x=df["date"],
        y=df["volume"],
        name="Volume",
        marker=dict(color="#1f77b4"),
    )
    fig = go.Figure(data=[volume])
    fig.update_layout(
        title=f"{selected_stock} Trading Volume",
        xaxis_title="Date",
        yaxis_title="Volume",
        template="plotly_dark",
    )
    return fig


def create_macd_fig(df, selected_stock):
    macd_trace = go.Scatter(
        x=df["date"],
        y=df["MACD"],
        mode="lines",
        name="MACD",
        line=dict(color="#ff7f0e"),
    )
    signal_trace = go.Scatter(
        x=df["date"],
        y=df["MACD_Signal"],
        mode="lines",
        name="Signal",
        line=dict(color="#2ca02c"),
    )
    histogram_trace = go.Bar(
        x=df["date"],
        y=df["MACD_Histogram"],
        name="Histogram",
        marker=dict(color="rgba(255, 127, 14, 0.5)"),
    )
    fig = go.Figure(data=[macd_trace, signal_trace, histogram_trace])
    fig.update_layout(
        title=f"{selected_stock} MACD",
        xaxis_title="Date",
        yaxis_title="MACD",
        template="plotly_dark",
    )
    return fig


def create_rsi_fig(df, selected_stock):
    rsi_trace = go.Scatter(
        x=df["date"],
        y=df["RSI"],
        mode="lines",
        name="RSI",
        line=dict(color="#d62728"),
    )
    fig = go.Figure(data=[rsi_trace])
    fig.update_layout(
        title=f"{selected_stock} RSI",
        xaxis_title="Date",
        yaxis_title="RSI",
        template="plotly_dark",
        shapes=[
            dict(
                type="line",
                x0=df["date"].min(),
                x1=df["date"].max(),
                y0=70,
                y1=70,
                line=dict(color="red", dash="dash"),
            ),
            dict(
                type="line",
                x0=df["date"].min(),
                x1=df["date"].max(),
                y0=30,
                y1=30,
                line=dict(color="green", dash="dash"),
            ),
        ],
    )
    return fig


def register_analysis_callbacks(app):
    @app.callback(
        [
            Output("price-indicators-graph", "figure"),
            Output("volume-graph", "figure"),
            Output("macd-graph", "figure"),
            Output("rsi-graph", "figure"),
        ],
        [
            Input("stock-selector", "value"),
            Input("date-range", "start_date"),
            Input("date-range", "end_date"),
            Input("range-1W", "n_clicks"),
            Input("range-1M", "n_clicks"),
            Input("range-3M", "n_clicks"),
            Input("range-6M", "n_clicks"),
            Input("range-1Y", "n_clicks"),
            Input("range-YTD", "n_clicks"),
            Input("range-MAX", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def update_stock_graphs(selected_stock, start_date, end_date, *range_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            button_id = "No clicks yet"
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Adjust date range based on button clicked
        if button_id.startswith("range-"):
            range_name = button_id.split("-")[1]
            end_date_dt = pd.to_datetime(end_date).date()
            if range_name == "MAX":
                start_date = START_DATE
            elif range_name == "YTD":
                start_of_year = datetime(end_date_dt.year, 1, 1).date()
                start_date = start_of_year.isoformat()
            else:
                delta = date_ranges.get(range_name)
                if delta:
                    start_date = (pd.to_datetime(end_date) - delta).date().isoformat()

        data_service = DataService(DB_PATH)
        df = data_service.get_stock_data_with_indicators(
            selected_stock, start_date, end_date, time_frame="daily"
        )

        if df.empty:
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text="No data available for the selected stock and date range",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            empty_fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="#2d2d2d",
                paper_bgcolor="#2d2d2d",
                font=dict(color="white"),
            )
            return empty_fig, empty_fig, empty_fig, empty_fig

        # Create individual figures
        price_fig = create_price_indicators_fig(df, selected_stock)
        volume_fig = create_volume_fig(df, selected_stock)
        macd_fig = create_macd_fig(df, selected_stock)
        rsi_fig = create_rsi_fig(df, selected_stock)

        return price_fig, volume_fig, macd_fig, rsi_fig
