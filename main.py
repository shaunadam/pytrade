from src.data.fetcher import DataService
from config import TSX_SYMBOLS, START_DATE, END_DATE, DATABASE_URL
from src.analysis.screeners import CompositeScreener, screener_registry
from src.analysis.report import generate_html_report
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


def preview(symbol: str = "SU.TO"):
    data_service = DataService(DATABASE_URL)
    data = data_service.get_stock_data_with_indicators(symbol, START_DATE, END_DATE)
    print(data)


def run_screener(selected_screeners: list, mode: str = "AND"):
    """
    Applies one or more screeners to the stock data and generates an HTML report.

    :param selected_screeners: List of screener names, or ["all"] to use all registered screeners.
    :param mode: "AND" or "OR" logic to combine multiple screeners if needed.
    """
    data_service = DataService(DATABASE_URL)
    # Fetch full DataFrame (with indicators) for your TSX symbols:
    data = data_service.get_stock_data_with_indicators(
        TSX_SYMBOLS, START_DATE, END_DATE
    )
    if data.empty:
        logger.warning("No data returned from the database. Exiting.")
        return

    # Determine which screeners to run:
    if len(selected_screeners) == 1 and selected_screeners[0].lower() == "all":
        # Use every screener in the registry
        active_screeners = [cls() for cls in screener_registry.values()]
    else:
        active_screeners = []
        for name in selected_screeners:
            screener_class = screener_registry.get(name.lower())
            if screener_class:
                active_screeners.append(screener_class())
            else:
                logger.warning(f"Screener '{name}' not found.")

    # If no valid screeners, bail out:
    if not active_screeners:
        logger.error("No valid screeners found. Exiting.")
        return

    # Combine them with CompositeScreener if you want an overall mask,
    # but also keep individual screener results for the report.
    combined_screener = CompositeScreener(active_screeners, mode=mode.upper())
    combined_mask = combined_screener.apply(data)
    logger.info(f"Combined screener mask shape: {combined_mask.shape}")

    # Prepare a dictionary: screener_name -> list of stock dictionaries
    screener_results = {}
    for screener in active_screeners:
        screener_name = screener.__class__.__name__  # e.g. "RSIOversoldScreener"
        mask = screener.apply(data)  # boolean series for this screener only
        df_screened = data[mask]

        stock_list = []
        if not df_screened.empty:
            # Group by symbol to gather timeseries + latest stats
            for symbol, df_symbol in df_screened.groupby("symbol"):
                if df_symbol.empty:
                    continue
                last_row = df_symbol.iloc[-1]

                stock_list.append(
                    {
                        "symbol": symbol,
                        "latest_price": last_row.get("close", None),
                        "rsi": last_row.get("RSI", None),
                        "macd": last_row.get("MACD", None),
                        "sma50": last_row.get("SMA50", None),
                        "sma200": last_row.get("SMA200", None),
                        # Entire time-series for plotting
                        "data": df_symbol[
                            ["date", "open", "high", "low", "close", "volume"]
                        ]
                        .sort_values("date")
                        .reset_index(drop=True),
                    }
                )

        screener_results[screener_name] = stock_list

    # Generate an HTML report that displays each screener's results + a plot
    generate_html_report(screener_results)


run_screener(["all"], mode="OR")


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
    parser.add_argument(
        "--preview",
        type=str,
    )
    args = parser.parse_args()

    if args.update:
        update_data()
    if args.recalculate:
        recalculate_indicators(time_frame=args.time_frame)
    if args.screener:
        run_screener(selected_screeners=args.screener, mode=args.mode)
    if args.preview:
        preview(args.preview)
    if not (args.update or args.recalculate or args.screener or args.preview):

        print(
            "No action specified. Use --update, --recalculate, preview, or --screener."
        )
