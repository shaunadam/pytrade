from src.data.fetcher import DataFetcher
from src.visualization.dashboard import app as dashboard_app
from config import DB_PATH, TSX_SYMBOLS, START_DATE, END_DATE
import pandas as pd
import argparse
import yfinance as yf


def update_data(symbols: list = None):
    fetcher = DataFetcher(DB_PATH)
    if symbols:
        fetcher.update_all_stocks(symbols, START_DATE, END_DATE)
    else:
        try:
            print(f"Updating data for all TSX symbols")
            fetcher.update_all_stocks(TSX_SYMBOLS, START_DATE, END_DATE)
        except Exception as e:
            print(f"Error updating stocks: {str(e)}")


def test_indicators():
    fetcher = DataFetcher(DB_PATH)
    # Use the first valid symbol for testing
    for symbol in TSX_SYMBOLS:
        try:
            data = fetcher.get_stock_data_with_indicators(symbol, START_DATE, END_DATE)
            if data is not None and not data.empty:
                break
        except Exception:
            continue
    else:
        print("No valid symbols found for testing")
        return

    if data is not None:
        print(f"Data for {symbol}:")
        print(data.head())
        indicators = [
            "SMA",
            "EMA",
            "RSI",
            "MACD",
            "MACD_Signal",
            "MACD_Histogram",
            "BB_SMA",
            "BB_Upper",
            "BB_Lower",
        ]
        missing_indicators = [ind for ind in indicators if ind not in data.columns]
        if not missing_indicators:
            print("All indicators are present in the data.")
        else:
            print(f"Missing indicators: {', '.join(missing_indicators)}")
        print("\nData statistics:")
        print(data.describe())
    else:
        print(f"No data found for {symbol}")


def run_dashboard():
    dashboard_app.run_server(debug=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TSX Stock Analysis Tool")
    parser.add_argument("--update", action="store_true", help="Update stock data")
    parser.add_argument("--test", action="store_true", help="Test indicators")
    parser.add_argument("--dashboard", action="store_true", help="Run the dashboard")
    args = parser.parse_args()

    if args.update:
        update_data()
    if args.test:
        test_indicators()
    if args.dashboard:
        run_dashboard()

    if not (args.update or args.test or args.dashboard):
        print("No action specified. Use --update, --test, or --dashboard")
