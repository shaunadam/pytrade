from src.data.fetcher import DataFetcher
from src.visualization.dashboard import app as dashboard_app
from src.analysis.screener import Screener
from config import DB_PATH, TSX_SYMBOLS, START_DATE, END_DATE
import pandas as pd
import argparse
import yfinance as yf
import yaml
import os


def update_data(symbols: list = None, start_date=START_DATE, end_date=END_DATE):
    fetcher = DataFetcher(DB_PATH)
    if symbols:
        fetcher.update_all_stocks(symbols, start_date, end_date)
        fetcher.update_indicators(symbols, start_date, end_date)
    else:
        try:
            print(f"Updating data for all TSX symbols")
            fetcher.update_all_stocks(TSX_SYMBOLS, start_date, end_date)
            fetcher.update_indicators(TSX_SYMBOLS, start_date, end_date)
        except Exception as e:
            print(f"Error updating stocks: {str(e)}")


def recalculate_indicators(
    symbols: list = None, start_date=START_DATE, end_date=END_DATE
):
    fetcher = DataFetcher(DB_PATH)
    if symbols:
        fetcher.recalculate_indicators(symbols, start_date, end_date)
    else:
        try:
            print(f"Recalculating indicators for all TSX symbols")
            fetcher.recalculate_indicators(TSX_SYMBOLS, start_date, end_date)
        except Exception as e:
            print(f"Error recalculating indicators: {str(e)}")


def run_dashboard():
    dashboard_app.run_server(debug=True)


def run_screener(config_name):
    fetcher = DataFetcher(DB_PATH)
    screener = Screener(config_name, fetcher)

    print(f"Running screener: {screener.config['name']}")
    print(f"Description: {screener.config['description']}")

    results = screener.screen(TSX_SYMBOLS, START_DATE, END_DATE)

    print("\nScreening Results:")
    print(results.to_string(index=False))


# run_screener("gold_cross")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TSX Stock Analysis Tool")
    parser.add_argument("--update", action="store_true", help="Update stock data")
    parser.add_argument(
        "--recalculate", action="store_true", help="Recalculate indicators"
    )
    parser.add_argument("--test", action="store_true", help="Test indicators")
    parser.add_argument("--dashboard", action="store_true", help="Run the dashboard")
    parser.add_argument(
        "--screener", type=str, help="Path to screener configuration file"
    )
    args = parser.parse_args()

    if args.update:
        update_data()
    if args.recalculate:
        recalculate_indicators()
    if args.dashboard:
        run_dashboard()
    if args.screener:
        run_screener(args.screener)

    if not (
        args.update or args.recalculate or args.test or args.dashboard or args.screener
    ):
        print(
            "No action specified. Use --update, --recalculate, --test, --dashboard, or --screener"
        )
