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


def register_screening_callbacks(app):
    @app.callback(
        Output("screening-output", "children"),
        Output("screening-results-table", "data"),
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
        results = []

        for screener_name in selected_screeners:
            try:
                screener = Screener(
                    config_path=os.path.join(
                        os.path.dirname(__file__),
                        "../../analysis",
                        screener_name,
                    ),
                    data_fetcher=data_service,
                )

                screener_results = screener.screen(symbols, START_DATE, END_DATE)
                for _, row in screener_results.iterrows():
                    results.append({"symbol": row["symbol"], "screener": screener_name})
            except Exception as e:
                logger.error(f"Error running screener {screener_name}: {e}")
                return f"Error running screener {screener_name}: {str(e)}", []

        if not results:
            return "No symbols matched the selected screener(s).", []

        return f"Screening completed. {len(results)} results found.", results

    @app.callback(
        Output("screening-stock-graph", "figure"),
        [
            Input("screening-results-table", "active_cell"),
            Input("screening-results-table", "data"),
        ],
    )
    def update_stock_graph(active_cell, table_data):
        if not active_cell:
            return go.Figure()

        row = active_cell["row"]
        if row >= len(table_data):
            return go.Figure()

        selected_symbol = table_data[row]["symbol"]

        data_service = DataService(DB_PATH)
        df = data_service.get_stock_data_with_indicators(
            selected_symbol, START_DATE, END_DATE
        )

        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for the selected stock.",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(
                title=f"{selected_symbol} - No Data Available",
                template="plotly_dark",
            )
            return fig

        candlestick = go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price",
        )

        traces = [candlestick]

        # Add indicators if available
        indicators = ["SMA12", "SMA26", "RSI", "MACD"]
        for indicator in indicators:
            if indicator in df.columns:
                traces.append(
                    go.Scatter(
                        x=df["date"],
                        y=df[indicator],
                        mode="lines",
                        name=indicator,
                        line=dict(width=1),
                    )
                )

        fig = go.Figure(data=traces)

        fig.update_layout(
            title=f"{selected_symbol} Stock Price and Indicators",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
        )

        return fig
