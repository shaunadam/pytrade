import logging
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Dict, Union

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, select, text
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

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str):
        self.engine = create_engine(db_path)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
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
    def __init__(self, session: Session):
        self.session = session

    def get_stock_by_symbol(self, symbol: str) -> Union[Stock, None]:
        return self.session.query(Stock).filter_by(symbol=symbol).first()

    def add_stock(self, stock: Stock):
        self.session.add(stock)
        self.session.flush()

    #
    # 1) Updated daily data upsert: chunked approach using PostgreSQL's
    #    ON CONFLICT DO UPDATE. Make sure you have a unique constraint on (stock_id, date).
    #
    def bulk_upsert_daily_data(
        self, daily_data_records: List[Dict], batch_size: int = 5000
    ):
        if not daily_data_records:
            return
        try:
            daily_data_table = DailyData.__table__
            for i in range(0, len(daily_data_records), batch_size):
                batch = daily_data_records[i : i + batch_size]
                stmt = insert(daily_data_table).values(batch)
                # Exclude ID from the update dict
                update_dict = {c.name: c for c in stmt.excluded if c.name not in ["id"]}
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=[
                        "stock_id",
                        "date",
                    ],  # must match your unique constraint
                    set_=update_dict,
                )
                self.session.execute(upsert_stmt)

            logger.info(
                f"Successfully upserted {len(daily_data_records)} daily data records."
            )
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in bulk_upsert_daily_data: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    #
    # 2) Weekly data upsert is already using chunked approach. We keep this.
    #
    def bulk_upsert_weekly_data(
        self, weekly_data_records: List[Dict], batch_size: int = 5000
    ):
        if not weekly_data_records:
            return
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
                f"Successfully upserted {len(weekly_data_records)} weekly data records."
            )
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in bulk_upsert_weekly_data: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_all_symbols(self) -> List[str]:
        return [stock.symbol for stock in self.session.query(Stock.symbol).all()]


class StockDataFetcher:
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


class IndicatorCalculator:
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


class DataService:
    def __init__(self, db_path: str):
        self.db_manager = DatabaseManager(db_path)
        self.indicator_calc = IndicatorCalculator()

    #
    # Helper: Convert the downloaded raw DataFrame into a list-of-dicts
    # for daily data, with columns we care about.
    #
    def _process_symbol_data(
        self, symbol: str, data: pd.DataFrame, stock_id: int
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
            # We don't need "Adj Close" if present
            daily_data = daily_data.drop(columns=["Adj Close"], errors="ignore")

            # Drop any rows that are entirely NaN
            daily_data = daily_data.dropna()

            daily_data["date"] = pd.to_datetime(daily_data["date"]).dt.date

            return daily_data.to_dict("records")
        except Exception as e:
            logger.error(f"Error processing data for {symbol}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    #
    # B) A single in-memory aggregator that handles ALL symbols together.
    # We'll skip the old loop-based aggregator (see the "deprecated" method below).
    #
    def _aggregate_weekly_data_in_memory(
        self, all_daily_data: pd.DataFrame
    ) -> pd.DataFrame:
        try:
            # all_daily_data is a DF containing columns:
            #   [stock_id, date, open, high, low, close, volume, ...]
            # We'll convert date to datetime index, groupby stock_id, resample weekly
            df = all_daily_data.copy()
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            # Group by stock_id, then resample to weekly. "W-MON" means weekly on Monday.
            weekly_df = (
                df.groupby("stock_id")
                .resample("W-MON")
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
            # This resample creates a MultiIndex: (stock_id, date)
            weekly_df.reset_index(inplace=True)
            weekly_df.rename(columns={"date": "week_start_date"}, inplace=True)
            return weekly_df
        except Exception as e:
            logger.error(f"Error aggregating weekly data in memory: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    #
    # MAIN ENTRY: Update daily data for all symbols, then do the weekly aggregator in memory.
    #
    def update_all_stocks(
        self, symbols: Union[str, List[str]], start_date: str, end_date: str
    ):
        if isinstance(symbols, str):
            symbols = [symbols]

        # 1) Fetch data from Yahoo for all symbols at once:
        all_data = StockDataFetcher.fetch_stock_data(symbols, start_date, end_date)
        if all_data.empty:
            logger.warning("No data retrieved from yfinance.")
            return

        # 2) Upsert daily data in a single pass, then mark last_updated
        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)
            all_daily_records = []

            for symbol in symbols:
                # If multiple symbols, the downloaded DataFrame has a nested structure: data[symbol]
                if len(symbols) > 1:
                    symbol_data = all_data[symbol]
                else:
                    symbol_data = all_data

                if symbol_data.empty:
                    logger.warning(f"Empty data for {symbol}. Skipping.")
                    continue

                # Ensure we have a Stock record
                stock = repository.get_stock_by_symbol(symbol)
                if not stock:
                    stock = Stock(symbol=symbol, name=symbol)
                    repository.add_stock(stock)

                # Convert that DataFrame portion to a list of dicts for DB upsert
                daily_data_records = self._process_symbol_data(
                    symbol, symbol_data, stock.id
                )
                all_daily_records.extend(daily_data_records)

            # Bulk upsert daily data
            repository.bulk_upsert_daily_data(all_daily_records)
            # Mark last_updated on these stocks
            updated_ids = {rec["stock_id"] for rec in all_daily_records}
            session.query(Stock).filter(Stock.id.in_(updated_ids)).update(
                {Stock.last_updated: datetime.now().date()},
                synchronize_session=False,
            )

        # 3) Now do a single in-memory aggregation of weekly data for all symbols.
        #    We'll reuse the same 'all_daily_records' to build a DF for weekly aggregator.
        if not all_daily_records:
            logger.warning("No daily data was upserted, skipping weekly aggregation.")
            return

        daily_df = pd.DataFrame(all_daily_records)

        # Only include the date range asked for (plus maybe a small buffer),
        # in case the downloaded data had extra.
        daily_df = daily_df[
            (pd.to_datetime(daily_df["date"]) >= pd.to_datetime(start_date))
            & (pd.to_datetime(daily_df["date"]) <= pd.to_datetime(end_date))
        ]

        weekly_df = self._aggregate_weekly_data_in_memory(daily_df)
        if weekly_df.empty:
            logger.warning("No weekly data generated, skipping upsert.")
            return

        # Convert to list-of-dicts for the weekly_data table
        weekly_records = []
        for _, row in weekly_df.iterrows():
            weekly_records.append(
                {
                    "stock_id": int(row["stock_id"]),
                    "week_start_date": row["week_start_date"].date(),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(row["volume"]),
                }
            )

        # 4) Bulk upsert weekly data
        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)
            repository.bulk_upsert_weekly_data(weekly_records)

    #
    # The OLD aggregator method is kept here but not called. Use at your own risk.
    # This does a DB query for each symbol's daily data. We replaced it with
    # the single in-memory aggregator above.
    #
    def aggregate_and_update_weekly_data(
        self, symbols: Union[str, List[str]], start_date: str, end_date: str
    ):
        logger.warning(
            "DEPRECATED: aggregate_and_update_weekly_data() is replaced by in-memory weekly aggregation."
        )
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

                # Aggregation
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

    #
    # Indicator updates remain the same. You could optimize further by combining queries,
    # but this is unchanged for now.
    #
    def update_indicators(
        self,
        symbols: Union[str, List[str]],
        start_date: str,
        end_date: str,
        time_frame: str = "daily",
    ):
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

                indicators = self.indicator_calc.calculate_indicators(
                    df["close"], time_frame=time_frame
                )

                # Remove old indicators in the same date range
                repository.session.query(indicator_model).filter(
                    indicator_model.stock_id == stock.id,
                    indicator_model.date >= start_date_with_buffer,
                    indicator_model.date <= end_date,
                ).delete(synchronize_session=False)
                repository.session.commit()

                # Insert new rows
                indicator_records = []
                for date_idx, row in indicators.iterrows():
                    for name, value in row.items():
                        if pd.notna(value):
                            indicator_records.append(
                                {
                                    "stock_id": stock.id,
                                    "date": date_idx.date(),
                                    "indicator_name": name,
                                    "value": float(value),
                                }
                            )
                if indicator_records:
                    repository.session.bulk_insert_mappings(
                        indicator_model, indicator_records
                    )
                    repository.session.commit()

                stock.last_updated = datetime.now().date()
                repository.session.commit()

    #
    # Reading data with indicators is unchanged.
    #
    def get_stock_data_with_indicators(
        self,
        symbols: Union[str, List[str]],
        start_date: str,
        end_date: str,
        time_frame: str = "daily",
    ) -> pd.DataFrame:
        if isinstance(symbols, str):
            symbols = [symbols]

        with self.db_manager.session_scope() as session:
            repository = StockRepository(session)
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

            data_df["symbol"] = data_df["stock_id"].map(stock_id_to_symbol)
            data_df.drop(columns=["id", "stock_id"], inplace=True)
            data_df[date_field] = pd.to_datetime(data_df[date_field])

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
                data_pivot = data_df.pivot_table(
                    index=[date_field, "symbol"],
                    values=["open", "high", "low", "close", "volume"],
                )
                final_df = data_pivot.reset_index()
                return final_df

            indicators_df["symbol"] = indicators_df["stock_id"].map(stock_id_to_symbol)
            indicators_df.drop(columns=["id", "stock_id"], inplace=True)
            indicators_df[date_field] = pd.to_datetime(indicators_df[date_field])

            indicators_pivot = indicators_df.pivot_table(
                index=[date_field, "symbol"],
                columns="indicator_name",
                values="value",
            ).reset_index()

            merged_df = pd.merge(
                data_df,
                indicators_pivot,
                on=[date_field, "symbol"],
                how="left",
            )
            merged_df.sort_values(by=["symbol", date_field], inplace=True)
            merged_df.reset_index(drop=True, inplace=True)

            return merged_df
