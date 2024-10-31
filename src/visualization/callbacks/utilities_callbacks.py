from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from src.data.fetcher import DataService
from config import DB_PATH, TSX_SYMBOLS
import dash
import logging
import threading

logger = logging.getLogger(__name__)


def register_utilities_callbacks(app):
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
        if not ctx.triggered:
            return dash.no_update, dash.no_update

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "download-button" and n_clicks:
            # Start the download process in a separate thread
            threading.Thread(
                target=lambda: (
                    DataService(DATABASE_URL).update_all_stocks(
                        TSX_SYMBOLS, start_date, end_date
                    ),
                    DataService(DATABASE_URL).update_indicators(
                        TSX_SYMBOLS, start_date, end_date, time_frame="daily"
                    ),
                ),
                daemon=True,  # Ensure thread exits when main program does
            ).start()
            logger.info("Started updating stock data in a separate thread.")
            return dbc.Progress(value=0, id="download-progress"), False

        if trigger_id == "download-progress-interval":
            # need to implement
            return "Download complete.", True

        return dash.no_update, dash.no_update
