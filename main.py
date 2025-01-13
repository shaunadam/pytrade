from src.data.fetcher import DataService  # Updated import
from config import TSX_SYMBOLS, START_DATE, END_DATE, DATABASE_URL

import argparse
import logging

# Configure logging to capture debug messages from the refactored classes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_data(symbols: list = None, start_date=START_DATE, end_date=END_DATE):
    """
    Updates stock data and recalculates technical indicators for both daily and weekly time frames.

    Args:
        symbols (list, optional): List of stock symbols to update. Defaults to None.
        start_date (str, optional): Start date for fetching data. Defaults to START_DATE.
        end_date (str, optional): End date for fetching data. Defaults to END_DATE.
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

        logger.info(
            "Data update and indicator recalculation completed successfully for both daily and weekly time frames."
        )
    except Exception as e:
        logger.error(f"Error updating stocks: {str(e)}")


def recalculate_indicators(
    symbols: list = None, start_date=START_DATE, end_date=END_DATE, time_frame="daily"
):
    """
    Recalculates technical indicators for specified symbols.

    Args:
        symbols (list, optional): List of stock symbols. Defaults to None.
        start_date (str, optional): Start date for recalculating indicators. Defaults to START_DATE.
        end_date (str, optional): End date for recalculating indicators. Defaults to END_DATE.
        time_frame (str, optional): Time frame for indicators ('daily' or 'weekly'). Defaults to 'daily'.
    """
    data_service = DataService(DATABASE_URL)  # Instantiate DataService
    if symbols:
        try:
            logger.info(
                f"Recalculating indicators for symbols: {symbols} with time_frame: {time_frame}"
            )
            data_service.update_indicators(
                symbols, start_date, end_date, time_frame=time_frame
            )
            logger.info("Indicator recalculation completed successfully.")
        except Exception as e:
            logger.error(f"Error recalculating indicators: {str(e)}")
    else:
        try:
            logger.info(
                f"Recalculating indicators for all TSX symbols with time_frame: {time_frame}"
            )
            data_service.update_indicators(
                TSX_SYMBOLS, start_date, end_date, time_frame=time_frame
            )
            logger.info(
                f"Indicator recalculation for all TSX symbols with time_frame {time_frame} completed successfully."
            )
        except Exception as e:
            logger.error(f"Error recalculating indicators: {str(e)}")


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
        "--screener", type=str, help="Path to screener configuration file"
    )
    args = parser.parse_args()

    if args.update:
        update_data()
    if args.recalculate:
        recalculate_indicators(time_frame=args.time_frame)
    if args.screener:
        run_screener(args.screener)

    if not (args.update or args.recalculate or args.screener):
        print("No action specified. Use --update, --recalculate, or --screener")
