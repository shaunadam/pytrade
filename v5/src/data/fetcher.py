import logging
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Dict, Union

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker, Session
from src.analysis.indicators import sma, ema, rsi, macd, bollinger_bands
from src.database.init_db import Stock, DailyData, TechnicalIndicator

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


# ---------------------- Database Layer ----------------------


class DatabaseManager:
    """
    Manages the database connection and session lifecycle.
    """

    def __init__(self, db_path: str):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self) -> Session:
        """
        Provides a transactional scope around a series of operations.
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session rollback because of exception: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        finally:
            session.close()


class StockRepository:
    """
    Encapsulates CRUD operations for Stock, DailyData, and TechnicalIndicator models.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_stock_by_symbol(self, symbol: str) -> Union[Stock, None]:
        return self.session.query(Stock).filter_by(symbol=symbol).first()

    def add_stock(self, stock: Stock):
        self.session.add(stock)
        self.session.flush()  # To assign an ID

    def bulk_upsert_daily_data(self, daily_data_records: List[Dict]):
        """
        Performs a bulk upsert of daily stock data.
        """
        try:
            upsert_daily_stmt = text(
                """
                INSERT OR REPLACE INTO daily_data (stock_id, date, open, high, low, close, volume)
                VALUES (:stock_id, :date, :open, :high, :low, :close, :volume)
                """
            )
            self.session.execute(upsert_daily_stmt, daily_data_records)
            self.session.commit()
            logger.info(
                f"Successfully upserted {len(daily_data_records)} daily data records"
            )
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in bulk_upsert_daily_data: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def delete_indicators(self, stock_id: int, start_date: str):
        """
        Deletes existing technical indicators for a given stock and date range.
        """
        try:
            self.session.query(TechnicalIndicator).filter(
                TechnicalIndicator.stock_id == stock_id,
                TechnicalIndicator.date >= start_date,
            ).delete()
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting indicators: {str(e)}")
            logger.error(traceback.format_exc())
            raise


# ---------------------- Data Fetching Layer ----------------------


class StockDataFetcher:
    """
    Responsible for fetching stock data from external sources like yfinance.
    """

    @staticmethod
    def fetch_stock_data(
        symbols: Union[str, List[str]], start_date: str, end_date: str
    ) -> pd.DataFrame:
        try:
            data = yf.download(
                symbols,
                start=start_date,
                end=end_date,
                group_by="ticker" if isinstance(symbols, list) else None,
                threads=True,
            )
            return data
        except Exception as e:
            logger.error(f"Error fetching stock data: {str(e)}")
            logger.error(traceback.format_exc())
            return pd.DataFrame()


# ---------------------- Data Processing Layer ----------------------


class DataProcessor:
    """
    Cleans and prepares data for database insertion.
    """

    @staticmethod
    def process_symbol_data(
        symbol: str, data: pd.DataFrame, stock_id: int
    ) -> List[Dict]:
        try:
            daily_data = data.reset_index()
            daily_data["stock_id"] = stock_id
            daily_data = daily_data.rename(
                columns={
                    "Date": "date",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                }
            )
            daily_data = daily_data.drop(columns=["Adj Close"], errors="ignore")
            daily_data = daily_data.dropna()
            daily_data["date"] = pd.to_datetime(daily_data["date"]).dt.date
            return daily_data.to_dict("records")
        except Exception as e:
            logger.error(f"Error processing data for {symbol}: {str(e)}")
            logger.error(traceback.format_exc())
            raise


# ---------------------- Indicator Calculation Layer ----------------------


class IndicatorCalculator:
    """
    Calculates technical indicators.
    """

    @staticmethod
    def calculate_indicators(close_prices: pd.Series) -> pd.DataFrame:
        try:
            indicators = pd.DataFrame(index=close_prices.index)
            indicators["SMA12"] = sma(close_prices, 12)
            indicators["SMA26"] = sma(close_prices, 26)
            indicators["SMA50"] = sma(close_prices, 50)
            indicators["EMA12"] = ema(close_prices, 12)
            indicators["EMA26"] = ema(close_prices, 26)
            indicators["EMA50"] = ema(close_prices, 50)
            indicators["RSI"] = rsi(close_prices)
            macd_data = macd(close_prices)
            indicators["MACD"] = macd_data["MACD"]
            indicators["MACD_Signal"] = macd_data["Signal"]
            indicators["MACD_Histogram"] = macd_data["Histogram"]
            indicators = indicators.dropna(how="all")
            bollinger_data = bollinger_bands(close_prices)
            indicators["BB_Middle"] = bollinger_data["SMA"]
            indicators["BB_Upper"] = bollinger_data["Upper"]
            indicators["BB_Lower"] = bollinger_data["Lower"]
            return indicators
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            logger.error(traceback.format_exc())
            raise


# ---------------------- Progress Tracking ----------------------


class ProgressTracker:
    """
    Manages progress updates and messages.
    """

    def __init__(self):
        self.update_progress = 0
        self.update_message = ""

    def set_progress(self, progress: int, message: str = ""):
        self.update_progress = progress
        self.update_message = message
        logger.debug(
            f"Progress updated to {self.update_progress}%: {self.update_message}"
        )

    def get_progress(self) -> (int, str):
        return self.update_progress, self.update_message


# ---------------------- Main Orchestrator ----------------------


class DataService:
    """
    Coordinates between different components to perform data fetching, processing, and updating.
    """

    def __init__(self, db_path: str):
        self.db_manager = DatabaseManager(db_path)
        self.progress_tracker = ProgressTracker()

    def update_all_stocks(
        self, symbols: Union[str, List[str]], start_date: str, end_date: str
    ):
        """
        Fetches and updates daily stock data for the given symbols and date range.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        self.progress_tracker.set_progress(0, "Fetching data for all stocks...")
        all_data = StockDataFetcher.fetch_stock_data(symbols, start_date, end_date)

        if all_data.empty:
            self.progress_tracker.set_progress(100, "No data found for any symbols.")
            return

        self.progress_tracker.set_progress(50, "Processing and inserting data...")

        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)
            all_daily_data = []

            try:
                for i, symbol in enumerate(symbols):
                    symbol_data = all_data[symbol] if len(symbols) > 1 else all_data
                    if symbol_data.empty:
                        logger.warning(f"Empty data for {symbol}. Skipping.")
                        continue

                    stock = repository.get_stock_by_symbol(symbol)
                    if not stock:
                        stock = Stock(symbol=symbol, name=symbol)
                        repository.add_stock(stock)

                    daily_data_records = DataProcessor.process_symbol_data(
                        symbol, symbol_data, stock.id
                    )
                    all_daily_data.extend(daily_data_records)

                    stock.last_updated = datetime.now().date()

                    # Commit after each stock to update last_updated
                    session.commit()

                    progress = int(50 + ((i + 1) / len(symbols)) * 50)
                    self.progress_tracker.set_progress(
                        progress, f"Processed {i+1}/{len(symbols)} stocks"
                    )

                # Bulk upsert all data
                repository.bulk_upsert_daily_data(all_daily_data)

                self.progress_tracker.set_progress(
                    100, "All stocks updated successfully"
                )
            except Exception as e:
                logger.error(f"Error updating stocks: {str(e)}")
                self.progress_tracker.set_progress(
                    100, f"Error updating stocks: {str(e)}"
                )
                raise

    def update_indicators(
        self,
        symbols: Union[str, List[str]],
        start_date: str,
        end_date: str,
        buffer_days: int = 365,
    ):
        """
        Recalculates and updates technical indicators for the given symbols and date range.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        start_date_with_buffer = (
            pd.to_datetime(start_date) - timedelta(days=buffer_days)
        ).strftime("%Y-%m-%d")
        self.progress_tracker.set_progress(
            0, "Recalculating indicators for all stocks..."
        )

        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)

            try:
                for i, symbol in enumerate(symbols):
                    stock = repository.get_stock_by_symbol(symbol)
                    if not stock:
                        logger.warning(
                            f"Stock {symbol} not found in database. Skipping."
                        )
                        continue

                    daily_data = (
                        session.query(DailyData)
                        .filter(
                            DailyData.stock_id == stock.id,
                            DailyData.date >= start_date_with_buffer,
                            DailyData.date <= end_date,
                        )
                        .all()
                    )

                    if not daily_data:
                        logger.warning(f"No data found for {symbol}. Skipping.")
                        continue

                    df = pd.DataFrame([d.__dict__ for d in daily_data])
                    df = df.drop(["id", "stock_id"], axis=1, errors="ignore")
                    df.set_index("date", inplace=True)
                    df.index = pd.to_datetime(df.index)

                    indicators = IndicatorCalculator.calculate_indicators(df["close"])

                    repository.delete_indicators(stock.id, start_date_with_buffer)

                    # Insert new indicators
                    indicator_records = []
                    for date, row in indicators.iterrows():
                        for indicator_name, value in row.items():
                            if pd.notna(value):
                                indicator_records.append(
                                    {
                                        "stock_id": stock.id,
                                        "date": date.date(),
                                        "indicator_name": indicator_name,
                                        "value": float(value),
                                    }
                                )

                    # Bulk insert indicators
                    if indicator_records:
                        session.bulk_insert_mappings(
                            TechnicalIndicator, indicator_records
                        )
                        session.commit()

                    stock.last_updated = datetime.now().date()
                    session.commit()

                    progress = int(((i + 1) / len(symbols)) * 100)
                    self.progress_tracker.set_progress(
                        progress,
                        f"Recalculated indicators for {i+1}/{len(symbols)} stocks",
                    )

                self.progress_tracker.set_progress(
                    100, "All indicators recalculated successfully"
                )
            except Exception as e:
                logger.error(f"Error recalculating indicators: {str(e)}")
                self.progress_tracker.set_progress(
                    100, f"Error recalculating indicators: {str(e)}"
                )
                raise

    def get_stock_data_with_indicators(
        self, symbols: Union[str, List[str]], start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Retrieves stock data along with technical indicators for the given symbols and date range.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        all_data = []

        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)

            try:
                for symbol in symbols:
                    stock = repository.get_stock_by_symbol(symbol)
                    if not stock:
                        logger.warning(
                            f"Stock {symbol} not found in database. Skipping."
                        )
                        continue

                    daily_data = (
                        session.query(DailyData)
                        .filter(
                            DailyData.stock_id == stock.id,
                            DailyData.date >= start_date,
                            DailyData.date <= end_date,
                        )
                        .all()
                    )

                    indicators = (
                        session.query(TechnicalIndicator)
                        .filter(
                            TechnicalIndicator.stock_id == stock.id,
                            TechnicalIndicator.date >= start_date,
                            TechnicalIndicator.date <= end_date,
                        )
                        .all()
                    )

                    if not daily_data:
                        logger.warning(f"No data found for {symbol}. Skipping.")
                        continue

                    # Create DataFrame from daily data
                    df = pd.DataFrame([d.__dict__ for d in daily_data])
                    df = df.drop(["id", "stock_id"], axis=1, errors="ignore")
                    df.set_index("date", inplace=True)
                    df.index = pd.to_datetime(df.index)

                    # Create DataFrame from indicators
                    indicator_data = [
                        (ind.date, ind.indicator_name, ind.value) for ind in indicators
                    ]
                    indicator_df = pd.DataFrame(
                        indicator_data, columns=["date", "indicator_name", "value"]
                    )
                    indicator_df["date"] = pd.to_datetime(indicator_df["date"])

                    # Pivot the indicator DataFrame
                    if not indicator_df.empty:
                        indicator_df = indicator_df.pivot(
                            index="date", columns="indicator_name", values="value"
                        )
                        # Merge daily data with indicator data
                        df = df.join(indicator_df)
                    else:
                        logger.warning(
                            f"No indicators found for {symbol} within the specified date range."
                        )

                    # Add a column for the stock symbol for identification in case of multiple stocks
                    df["symbol"] = symbol

                    # Append the combined data for this symbol to the list
                    all_data.append(df)

                if all_data:
                    # Concatenate all DataFrames into a single DataFrame
                    final_df = pd.concat(all_data, axis=0).reset_index()
                else:
                    # Return an empty DataFrame if no data found for any symbols
                    final_df = pd.DataFrame()

                return final_df
            except Exception as e:
                logger.error(f"Error retrieving stock data with indicators: {str(e)}")
                logger.error(traceback.format_exc())
                return pd.DataFrame()


# ---------------------- Example Usage ----------------------


def main():
    # Initialize DataService with the path to your SQLite database
    db_path = "path_to_your_db.sqlite"
    data_service = DataService(db_path)

    # Define stock symbols and date range
    symbols = ["AAPL", "GOOGL", "MSFT"]
    start_date = "2023-01-01"
    end_date = "2024-10-12"

    # Update stock data
    try:
        data_service.update_all_stocks(symbols, start_date, end_date)
        print("Stock data updated successfully.")
    except Exception as e:
        print(f"Failed to update stock data: {str(e)}")

    # Update technical indicators
    try:
        data_service.update_indicators(symbols, start_date, end_date)
        print("Technical indicators updated successfully.")
    except Exception as e:
        print(f"Failed to update technical indicators: {str(e)}")

    # Retrieve data with indicators
    try:
        df = data_service.get_stock_data_with_indicators(symbols, start_date, end_date)
        print(df)
    except Exception as e:
        print(f"Failed to retrieve stock data with indicators: {str(e)}")


if __name__ == "__main__":
    main()
