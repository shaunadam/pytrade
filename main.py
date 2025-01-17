from src.data.fetcher import DataService
from config import TSX_SYMBOLS, START_DATE, END_DATE, DATABASE_URL
from src.analysis.screeners import (
    RSIOversoldScreener,
    MACDBullishCrossScreener,
    CompositeScreener,
)

import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_data(symbols: list = None, start_date=START_DATE, end_date=END_DATE):
    """
    Updates stock data and recalculates technical indicators for both daily and weekly time frames.
    """
    data_service = DataService(DATABASE_URL)
    target_symbols = symbols if symbols else TSX_SYMBOLS

    try:
        logger.info(f"Updating data for symbols: {target_symbols}")
        data_service.update_all_stocks(target_symbols, start_date, end_date)

        # Update Daily Indicators
        logger.info("Recalculating daily technical indicators.")
        data_service.update_indicators(
            target_symbols, start_date, end_date, time_frame="daily"
        )

        # Update Weekly Indicators
        logger.info("Recalculating weekly technical indicators.")
        data_service.update_indicators(
            target_symbols, start_date, end_date, time_frame="weekly"
        )

        logger.info("Data update and indicator recalculation completed successfully.")
    except Exception as e:
        logger.error(f"Error updating stocks: {str(e)}")


def recalculate_indicators(
    symbols: list = None, start_date=START_DATE, end_date=END_DATE, time_frame="daily"
):
    """
    Recalculates technical indicators for specified symbols (or all TSX if none given).
    """
    data_service = DataService(DATABASE_URL)
    try:
        if symbols:
            logger.info(
                f"Recalculating indicators for symbols: {symbols} with time_frame: {time_frame}"
            )
            data_service.update_indicators(
                symbols, start_date, end_date, time_frame=time_frame
            )
        else:
            logger.info(
                f"Recalculating indicators for all TSX symbols with time_frame: {time_frame}"
            )
            data_service.update_indicators(
                TSX_SYMBOLS, start_date, end_date, time_frame=time_frame
            )

        logger.info("Indicator recalculation completed successfully.")
    except Exception as e:
        logger.error(f"Error recalculating indicators: {str(e)}")


def run_screener(selected_screeners: list, mode: str = "AND"):
    """
    Runs the selected screeners and prints the filtered DataFrame.
    """
    data_service = DataService(DATABASE_URL)
    data = data_service.get_stock_data_with_indicators(
        TSX_SYMBOLS, START_DATE, END_DATE
    )

    # Map screener names to classes
    screener_mapping = {
        "rsi_oversold": RSIOversoldScreener(threshold=30),
        "macd_bullish": MACDBullishCrossScreener(),
    }

    # Initialize the selected screeners
    active_screeners = [screener_mapping[name] for name in selected_screeners]

    # Apply the composite screener
    combined_screener = CompositeScreener(active_screeners, mode=mode)
    screened_data = data[combined_screener.apply(data)]
    print(screened_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TSX Stock Analysis Tool")
    parser.add_argument("--update", action="store_true", help="Update stock data")
    parser.add_argument(
        "--recalculate", action="store_true", help="Recalculate indicators"
    )
    parser.add_argument(
        "--time_frame",
        type=str,
        choices=["daily", "weekly"],
        default="daily",
        help="Time frame for indicators",
    )
    parser.add_argument(
        "--screener",
        nargs="+",
        help="List of screeners to run (e.g., rsi_oversold macd_bullish)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["AND", "OR"],
        default="AND",
        help="Combine screeners with AND/OR logic",
    )
    args = parser.parse_args()

    if args.update:
        update_data()
    if args.recalculate:
        recalculate_indicators(time_frame=args.time_frame)
    if args.screener:
        run_screener(selected_screeners=args.screener, mode=args.mode)
    if not (args.update or args.recalculate or args.screener):
        print("No action specified. Use --update, --recalculate, or --screener.")
