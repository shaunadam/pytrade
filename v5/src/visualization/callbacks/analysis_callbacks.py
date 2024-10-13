# src/visualization/callbacks/analysis_callbacks.py

from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from src.data.fetcher import DataService
from config import DB_PATH, TSX_SYMBOLS, START_DATE, END_DATE, date_ranges
import pandas as pd
import dash
import logging

logger = logging.getLogger(__name__)


def register_analysis_callbacks(app):
    @app.callback(
        Output("stock-graph", "figure"),
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
    def update_stock_graph(selected_stock, start_date, end_date, *range_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            button_id = "No clicks yet"
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id.startswith("range-"):
            range_name = button_id.split("-")[1]
            end_date_dt = pd.to_datetime(end_date).date()
            if range_name == "MAX":
                start_date = START_DATE
                end_date = end_date_dt.isoformat()
            elif range_name == "YTD":
                start_date = (
                    pd.to_datetime(end_date).replace(month=1, day=1).date().isoformat()
                )
                end_date = end_date_dt.isoformat()
            else:
                delta = date_ranges.get(range_name)
                if delta:
                    start_date = (pd.to_datetime(end_date) - delta).date().isoformat()

        data_service = DataService(DB_PATH)
        df = data_service.get_stock_data_with_indicators(
            selected_stock, start_date, end_date
        )

        if df.empty:
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
            x=df["date"],
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
                x=df["date"],
                y=df["SMA50"],
                mode="lines",
                name="SMA50",
                line=dict(color="blue"),
            )
            traces.append(sma_trace)

        if "EMA50" in df.columns:
            ema_trace = go.Scatter(
                x=df["date"],
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
