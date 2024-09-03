from src.data.fetcher import DataFetcher
from src.visualization.dashboard import app as dashboard_app
from config import DB_PATH, TSX_SYMBOLS, START_DATE, END_DATE
import pandas as pd


def main():
    fetcher = DataFetcher(DB_PATH)
    fetcher.update_all_stocks(TSX_SYMBOLS, START_DATE, END_DATE)


def test_indicators():
    fetcher = DataFetcher(DB_PATH)

    # Test for the first symbol in the list
    symbol = TSX_SYMBOLS[0]
    data = fetcher.get_stock_data_with_indicators(symbol, START_DATE, END_DATE)

    if data is not None:
        print(f"Data for {symbol}:")
        print(data.head())

        # Check if indicators are present
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

        # Display some statistics
        print("\nData statistics:")
        print(data.describe())
    else:
        print(f"No data found for {symbol}")


def run_dashboard():
    dashboard_app.run_server(debug=True)


if __name__ == "__main__":
    main()
    print("\nTesting indicators:")
    test_indicators()
    print("\nStarting dashboard:")
    run_dashboard()
