# src/visualization/callbacks/screening_callbacks.py

from dash.dependencies import Input, Output, State
from dash import dash_table
from src.visualization.components.screening_tab import get_available_screeners
from src.analysis.screener import Screener
from src.data.fetcher import DataService
from config import DB_PATH, TSX_SYMBOLS, START_DATE, END_DATE
import pandas as pd
import dash
import plotly.graph_objs as go
import logging
import os

logger = logging.getLogger(__name__)


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
        yaxis_title="Price",
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


def register_screening_callbacks(app):
    @app.callback(
        [
            Output("screening-output", "children"),
            Output("screening-results-table", "data"),
        ],
        [
            Input("run-screeners-button", "n_clicks"),
        ],
        [
            State("screener-selector", "value"),
            State("stock-selector-screening", "value"),
        ],
    )
    def run_screeners(n_clicks, selected_screeners, selected_stocks):
        if not n_clicks:
            return "", []
        if not selected_screeners:
            return "Please select at least one screener.", []

        data_service = DataService(DB_PATH)
        symbols = selected_stocks if selected_stocks else TSX_SYMBOLS

        # Fetch data once
        data = data_service.get_stock_data_with_indicators(
            symbols, START_DATE, END_DATE
        )

        if data.empty:
            return "No data available for the selected stocks.", []

        results = []

        for screener_name in selected_screeners:
            try:
                screener = Screener(
                    config_path=os.path.join(
                        os.path.dirname(__file__),
                        "../../analysis",
                        screener_name,
                    ),
                )
                # Pass the data directly to the screener
                screener_results = screener.screen_data(data)
                for _, row in screener_results.iterrows():
                    results.append({"symbol": row["symbol"], "screener": screener_name})
            except Exception as e:
                logger.error(f"Error running screener {screener_name}: {e}")
                return f"Error running screener {screener_name}: {str(e)}", []

        if not results:
            return "No symbols matched the selected screener(s).", []

        return f"Screening completed. {len(results)} results found.", results

    @app.callback(
        [
            Output("screening-price-indicators-graph", "figure"),
            Output("screening-volume-graph", "figure"),
            Output("screening-macd-graph", "figure"),
            Output("screening-rsi-graph", "figure"),
        ],
        [
            Input("screening-results-table", "active_cell"),
            Input("screening-results-table", "data"),
        ],
    )
    def update_screening_stock_graph(active_cell, table_data):
        if not active_cell:
            # Return empty figures if no cell is active
            empty_fig = go.Figure()
            empty_fig.update_layout(template="plotly_dark")
            return empty_fig, empty_fig, empty_fig, empty_fig

        row = active_cell["row"]
        if row >= len(table_data):
            # Return empty figures if row index is out of bounds
            empty_fig = go.Figure()
            empty_fig.update_layout(template="plotly_dark")
            return empty_fig, empty_fig, empty_fig, empty_fig

        selected_symbol = table_data[row]["symbol"]

        data_service = DataService(DB_PATH)
        df = data_service.get_stock_data_with_indicators(
            selected_symbol, START_DATE, END_DATE
        )

        if df.empty:
            empty_fig = go.Figure()
            empty_fig.add_annotation(
                text="No data available for the selected stock.",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            empty_fig.update_layout(
                title=f"{selected_symbol} - No Data Available",
                template="plotly_dark",
            )
            return empty_fig, empty_fig, empty_fig, empty_fig

        # Create individual figures using the defined functions
        price_fig = create_price_indicators_fig(df, selected_symbol)
        volume_fig = create_volume_fig(df, selected_symbol)
        macd_fig = create_macd_fig(df, selected_symbol)
        rsi_fig = create_rsi_fig(df, selected_symbol)

        return price_fig, volume_fig, macd_fig, rsi_fig
