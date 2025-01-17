import logging
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Dict, Union

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, select, text, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker, Session

from src.analysis.indicators import (
    sma,
    ema,
    rsi,
    macd,
    bollinger_bands,
)
from src.database.init_db import (
    Stock,
    DailyData,
    WeeklyData,
    TechnicalIndicator,
    WeeklyTechnicalIndicator,
)

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


# ---------------------- Database Layer ----------------------
class DatabaseManager:
    """
    Manages the database connection and session lifecycle.
    """

    def __init__(self, db_path: str):
        self.engine = create_engine(db_path)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
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
    Encapsulates CRUD operations for Stock, DailyData, WeeklyData, and TechnicalIndicator models.
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
                INSERT INTO daily_data (stock_id, date, open, high, low, close, volume)
                VALUES (:stock_id, :date, :open, :high, :low, :close, :volume)
                ON CONFLICT (stock_id, date) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume
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

    def bulk_upsert_weekly_data(
        self, weekly_data_records: List[Dict], batch_size: int = 5000
    ):
        """
        Performs a bulk upsert of weekly stock data.
        """
        try:
            weekly_data_table = WeeklyData.__table__
            for i in range(0, len(weekly_data_records), batch_size):
                batch = weekly_data_records[i : i + batch_size]
                stmt = insert(weekly_data_table).values(batch)
                update_dict = {c.name: c for c in stmt.excluded if c.name not in ["id"]}
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=["stock_id", "week_start_date"], set_=update_dict
                )
                self.session.execute(upsert_stmt)
            logger.info(
                f"Successfully upserted {len(weekly_data_records)} weekly data records"
            )
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in bulk_upsert_weekly_data: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_all_symbols(self) -> List[str]:
        return [stock.symbol for stock in self.session.query(Stock.symbol).all()]


# ---------------------- Fetching Layer ----------------------
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
                # show_errors=False, #github says this works, it doesn't.
            )
            return data
        except Exception as e:
            logger.error(f"Error fetching stock data: {str(e)}")
            logger.error(traceback.format_exc())
            return pd.DataFrame()


# ---------------------- Indicator Calculation Layer ----------------------
class IndicatorCalculator:
    """
    Calculates technical indicators.
    """

    @staticmethod
    def calculate_indicators(
        close_prices: pd.Series, time_frame="daily"
    ) -> pd.DataFrame:
        try:
            indicators = pd.DataFrame(index=close_prices.index)
            indicators["SMA12"] = sma(close_prices, 12, time_frame=time_frame)
            indicators["SMA26"] = sma(close_prices, 26, time_frame=time_frame)
            indicators["SMA50"] = sma(close_prices, 50, time_frame=time_frame)
            indicators["SMA200"] = sma(close_prices, 200, time_frame=time_frame)
            indicators["EMA12"] = ema(close_prices, 12, time_frame=time_frame)
            indicators["EMA26"] = ema(close_prices, 26, time_frame=time_frame)
            indicators["EMA50"] = ema(close_prices, 50, time_frame=time_frame)
            indicators["EMA200"] = ema(close_prices, 200, time_frame=time_frame)
            indicators["RSI"] = rsi(close_prices, 14, time_frame=time_frame)

            macd_data = macd(close_prices, time_frame=time_frame)
            indicators["MACD"] = macd_data["MACD"]
            indicators["MACD_Signal"] = macd_data["Signal"]
            indicators["MACD_Histogram"] = macd_data["Histogram"]

            bollinger_data = bollinger_bands(close_prices, time_frame=time_frame)
            indicators["BB_Middle"] = bollinger_data["SMA"]
            indicators["BB_Upper"] = bollinger_data["Upper"]
            indicators["BB_Lower"] = bollinger_data["Lower"]

            return indicators
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            logger.error(traceback.format_exc())
            raise


# ---------------------- Main Orchestrator ----------------------
class DataService:
    """
    Coordinates database operations, data fetching, and indicator calculations.
    """

    def __init__(self, db_path: str):
        self.db_manager = DatabaseManager(db_path)
        self.indicator_calc = IndicatorCalculator()

    # ----------------------------------------------------------------------
    # The following private methods replace the old DataProcessor class.
    # ----------------------------------------------------------------------

    def _process_symbol_data(
        self, symbol: str, data: pd.DataFrame, stock_id: int
    ) -> List[Dict]:
        """
        Cleans and normalizes raw symbol data from yfinance into a list of records
        suitable for insertion into the daily_data table.
        """
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

    def _aggregate_weekly_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates daily data into weekly intervals.
        """
        try:
            weekly_df = (
                df.resample("W-MON")
                .agg(
                    {
                        "open": "first",
                        "high": "max",
                        "low": "min",
                        "close": "last",
                        "volume": "sum",
                    }
                )
                .dropna()
            )
            weekly_df = weekly_df.reset_index().rename(
                columns={"date": "week_start_date"}
            )
            return weekly_df
        except Exception as e:
            logger.error(f"Error aggregating weekly data: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    # ----------------------------------------------------------------------
    # Methods that orchestrate the entire fetch/insert/update flow
    # ----------------------------------------------------------------------

    def update_all_stocks(
        self, symbols: Union[str, List[str]], start_date: str, end_date: str
    ):
        """
        Fetches data from yfinance, processes daily data, upserts into DB,
        and then handles weekly aggregation.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        # Fetch data in one go
        all_data = StockDataFetcher.fetch_stock_data(symbols, start_date, end_date)
        if all_data.empty:
            logger.warning("No data retrieved from yfinance.")
            return

        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)
            all_daily_data = []
            stock_ids = []

            for i, symbol in enumerate(symbols):
                # For multiple symbols, yfinance returns a multi-index DataFrame
                if len(symbols) > 1:
                    symbol_data = all_data[symbol]
                else:
                    symbol_data = all_data

                if symbol_data.empty:
                    logger.warning(f"Empty data for {symbol}. Skipping.")
                    continue

                # Create stock if not exists
                stock = repository.get_stock_by_symbol(symbol)
                if not stock:
                    stock = Stock(symbol=symbol, name=symbol)
                    repository.add_stock(stock)

                # Prepare daily records
                daily_data_records = self._process_symbol_data(
                    symbol, symbol_data, stock.id
                )
                all_daily_data.extend(daily_data_records)
                stock_ids.append(stock.id)

            # Bulk upsert all daily data
            repository.bulk_upsert_daily_data(all_daily_data)

            # Update last_updated for all relevant stocks
            session.query(Stock).filter(Stock.id.in_(stock_ids)).update(
                {Stock.last_updated: datetime.now().date()},
                synchronize_session=False,
            )

            # Aggregate daily -> weekly
            self.aggregate_and_update_weekly_data(symbols, start_date, end_date)

    def aggregate_and_update_weekly_data(
        self, symbols: Union[str, List[str]], start_date: str, end_date: str
    ):
        """
        Aggregates daily data into weekly data and updates the weekly_data table.
        Processes only the specified symbols and date range (adjusted 2 weeks earlier).
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        adjusted_start_date = (
            pd.to_datetime(start_date) - timedelta(days=14)
        ).strftime("%Y-%m-%d")

        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)
            for symbol in symbols:
                stock = repository.get_stock_by_symbol(symbol)
                if not stock:
                    logger.warning(f"Stock {symbol} not found in database. Skipping.")
                    continue

                # Fetch daily data from DB
                daily_data = (
                    session.query(DailyData)
                    .filter(
                        DailyData.stock_id == stock.id,
                        DailyData.date >= adjusted_start_date,
                        DailyData.date <= end_date,
                    )
                    .order_by(DailyData.date)
                    .all()
                )

                if not daily_data:
                    logger.warning(
                        f"No daily data for {symbol} in the date range. Skipping."
                    )
                    continue

                df = pd.DataFrame([d.__dict__ for d in daily_data])
                df = df.drop(
                    columns=["id", "stock_id", "_sa_instance_state"], errors="ignore"
                )
                df["date"] = pd.to_datetime(df["date"])
                df.set_index("date", inplace=True)

                # Aggregate to weekly
                weekly_df = self._aggregate_weekly_data(df)

                # Prepare records for bulk upsert
                weekly_records = []
                for _, row in weekly_df.iterrows():
                    weekly_records.append(
                        {
                            "stock_id": stock.id,
                            "week_start_date": row["week_start_date"].date(),
                            "open": row["open"],
                            "high": row["high"],
                            "low": row["low"],
                            "close": row["close"],
                            "volume": row["volume"],
                        }
                    )

                repository.bulk_upsert_weekly_data(weekly_records)
                logger.info(f"Weekly data updated for {symbol}.")

    def update_indicators(
        self,
        symbols: Union[str, List[str]],
        start_date: str,
        end_date: str,
        time_frame: str = "daily",
    ):
        """
        Recalculates and updates technical indicators for the given symbols and date range.
        Supports both daily and weekly time frames.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        start_date_with_buffer = (
            pd.to_datetime(start_date) - timedelta(days=365)
        ).strftime("%Y-%m-%d")

        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)
            for symbol in symbols:
                stock = repository.get_stock_by_symbol(symbol)
                if not stock:
                    logger.warning(f"Stock {symbol} not found in database. Skipping.")
                    continue

                if time_frame == "weekly":
                    data_query = (
                        session.query(WeeklyData)
                        .filter(
                            WeeklyData.stock_id == stock.id,
                            WeeklyData.week_start_date >= start_date_with_buffer,
                            WeeklyData.week_start_date <= end_date,
                        )
                        .all()
                    )
                    date_field = "week_start_date"
                    indicator_model = WeeklyTechnicalIndicator
                else:
                    data_query = (
                        session.query(DailyData)
                        .filter(
                            DailyData.stock_id == stock.id,
                            DailyData.date >= start_date_with_buffer,
                            DailyData.date <= end_date,
                        )
                        .all()
                    )
                    date_field = "date"
                    indicator_model = TechnicalIndicator

                if not data_query:
                    logger.warning(f"No data found for {symbol}. Skipping.")
                    continue

                df = pd.DataFrame([d.__dict__ for d in data_query])
                df = df.drop(
                    columns=["id", "stock_id", "_sa_instance_state"],
                    errors="ignore",
                )
                df[date_field] = pd.to_datetime(df[date_field])
                df.set_index(date_field, inplace=True)

                # Calculate indicators
                indicators = self.indicator_calc.calculate_indicators(
                    df["close"], time_frame=time_frame
                )

                # Delete existing indicators for this time frame
                repository.session.query(indicator_model).filter(
                    indicator_model.stock_id == stock.id,
                    indicator_model.date >= start_date_with_buffer,
                ).delete(synchronize_session=False)
                repository.session.commit()

                # Insert new indicator records
                indicator_records = [
                    {
                        "stock_id": stock.id,
                        "date": date_idx.date(),
                        "indicator_name": name,
                        "value": float(value),
                    }
                    for date_idx, row in indicators.iterrows()
                    for name, value in row.items()
                    if pd.notna(value)
                ]

                if indicator_records:
                    repository.session.bulk_insert_mappings(
                        indicator_model, indicator_records
                    )
                    repository.session.commit()

                stock.last_updated = datetime.now().date()
                repository.session.commit()

    def get_stock_data_with_indicators(
        self,
        symbols: Union[str, List[str]],
        start_date: str,
        end_date: str,
        time_frame: str = "daily",
    ) -> pd.DataFrame:
        """
        Fetches daily or weekly price data plus technical indicators
        for the specified symbols and date range, returning a merged DataFrame.
        """
        if isinstance(symbols, str):
            symbols = [symbols]

        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)

            # Fetch all stocks matching the symbols
            stocks = session.query(Stock).filter(Stock.symbol.in_(symbols)).all()
            if not stocks:
                logger.warning("No stocks found for the given symbols.")
                return pd.DataFrame()

            stock_id_to_symbol = {stock.id: stock.symbol for stock in stocks}
            stock_ids = list(stock_id_to_symbol.keys())

            if time_frame == "weekly":
                data_query = (
                    session.query(WeeklyData)
                    .filter(
                        WeeklyData.stock_id.in_(stock_ids),
                        WeeklyData.week_start_date >= start_date,
                        WeeklyData.week_start_date <= end_date,
                    )
                    .order_by(WeeklyData.week_start_date)
                )
                date_field = "week_start_date"
                indicator_model = WeeklyTechnicalIndicator
            else:
                data_query = (
                    session.query(DailyData)
                    .filter(
                        DailyData.stock_id.in_(stock_ids),
                        DailyData.date >= start_date,
                        DailyData.date <= end_date,
                    )
                    .order_by(DailyData.date)
                )
                date_field = "date"
                indicator_model = TechnicalIndicator

            data_df = pd.read_sql(data_query.statement, session.bind)
            if data_df.empty:
                logger.warning("No data found for the given date range.")
                return pd.DataFrame()

            # Map stock IDs to symbols
            data_df["symbol"] = data_df["stock_id"].map(stock_id_to_symbol)
            data_df.drop(columns=["id", "stock_id"], inplace=True)
            data_df[date_field] = pd.to_datetime(data_df[date_field])

            # Fetch technical indicators in bulk
            indicators_query = (
                session.query(indicator_model)
                .filter(
                    indicator_model.stock_id.in_(stock_ids),
                    indicator_model.date >= start_date,
                    indicator_model.date <= end_date,
                )
                .order_by(indicator_model.date)
            )
            indicators_df = pd.read_sql(indicators_query.statement, session.bind)
            if indicators_df.empty:
                logger.warning("No technical indicators found for the given range.")
                # Return data without indicators
                data_pivot = data_df.pivot_table(
                    index=[date_field, "symbol"],
                    values=["open", "high", "low", "close", "volume"],
                )
                final_df = data_pivot.reset_index()
                return final_df

            # Map stock IDs to symbols in the indicators
            indicators_df["symbol"] = indicators_df["stock_id"].map(stock_id_to_symbol)
            indicators_df.drop(columns=["id", "stock_id"], inplace=True)
            indicators_df[date_field] = pd.to_datetime(indicators_df[date_field])

            # Pivot the indicators DataFrame
            indicators_pivot = indicators_df.pivot_table(
                index=[date_field, "symbol"],
                columns="indicator_name",
                values="value",
            ).reset_index()

            # Merge price data with indicators
            merged_df = pd.merge(
                data_df,
                indicators_pivot,
                on=[date_field, "symbol"],
                how="left",
            )

            # Sort for readability
            merged_df.sort_values(by=["symbol", date_field], inplace=True)
            merged_df.reset_index(drop=True, inplace=True)

            return merged_df
