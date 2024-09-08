from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from src.database.init_db import Stock, DailyData, TechnicalIndicator
from src.analysis.indicators import sma, ema, rsi, macd
from datetime import datetime
import pandas as pd
import yfinance as yf
import logging
import traceback

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self, db_path):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)
        self.update_progress = 0
        self.update_message = ""

    def fetch_stock_data(self, symbols, start_date, end_date):
        try:
            data = yf.download(
                symbols,
                start=start_date,
                end=end_date,
                group_by="ticker",
                threads=True,
            )
            return data
        except Exception as e:
            logger.error(f"Error fetching stock data: {str(e)}")
            logger.error(traceback.format_exc())
            return pd.DataFrame()

    def calculate_indicators(self, data):
        indicators = {}
        indicators["SMA12"] = sma(data, 12)
        indicators["SMA26"] = sma(data, 26)
        indicators["SMA50"] = sma(data, 50)
        indicators["EMA12"] = ema(data, 12)
        indicators["EMA26"] = ema(data, 26)
        indicators["EMA50"] = ema(data, 50)
        indicators["RSI"] = rsi(data)
        macd_data = macd(data)
        indicators["MACD"] = macd_data["MACD"]
        return pd.DataFrame(indicators)

    def set_update_progress(self, progress, message=""):
        self.update_progress = progress
        self.update_message = message

    def get_update_progress(self):
        return self.update_progress, self.update_message

    def update_all_stocks(self, symbols, start_date, end_date):
        self.set_update_progress(0, "Fetching data for all stocks...")
        all_data = self.fetch_stock_data(symbols, start_date, end_date)

        if all_data.empty:
            self.set_update_progress(100, "No data found for any symbols.")
            return

        self.set_update_progress(50, "Processing and inserting data...")

        session = self.Session()
        try:
            all_daily_data = []
            all_indicator_data = []

            for i, symbol in enumerate(symbols):
                symbol_data = all_data[symbol] if len(symbols) > 1 else all_data
                if symbol_data.empty:
                    logger.warning(f"Empty data for {symbol}. Skipping.")
                    continue

                stock = session.execute(
                    select(Stock).filter_by(symbol=symbol)
                ).scalar_one_or_none()
                if not stock:
                    stock = Stock(symbol=symbol, name=symbol)
                    session.add(stock)
                    session.flush()

                indicators = self.calculate_indicators(symbol_data["Close"])

                daily_data = symbol_data.reset_index()
                daily_data["stock_id"] = stock.id
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
                daily_data = daily_data.drop(columns=["Adj Close"])
                daily_data = daily_data.dropna()

                indicator_data = indicators.reset_index()
                indicator_data["stock_id"] = stock.id
                indicator_data = indicator_data.melt(
                    id_vars=["Date", "stock_id"],
                    var_name="indicator_name",
                    value_name="value",
                )
                indicator_data = indicator_data.rename(columns={"Date": "date"})
                indicator_data = indicator_data.dropna()

                all_daily_data.append(daily_data)
                all_indicator_data.append(indicator_data)

                stock.last_updated = datetime.now().date()
                session.commit()

                progress = int(50 + (i + 1) / len(symbols) * 50)
                self.set_update_progress(
                    progress, f"Processed {i+1}/{len(symbols)} stocks"
                )

            # Concatenate all data
            combined_daily_data = pd.concat(all_daily_data, ignore_index=True)
            combined_indicator_data = pd.concat(all_indicator_data, ignore_index=True)

            # Bulk upsert all data
            self.bulk_upsert_data(session, combined_daily_data, combined_indicator_data)

            self.set_update_progress(100, "All stocks updated successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating stocks: {str(e)}")
            logger.error(traceback.format_exc())
            self.set_update_progress(100, f"Error updating stocks: {str(e)}")
        finally:
            session.close()

    def bulk_upsert_data(self, session, daily_data_df, indicator_data_df):
        try:
            # Upsert daily data
            daily_data_df["date"] = pd.to_datetime(daily_data_df["date"]).dt.date
            daily_data_records = daily_data_df.to_dict("records")
            upsert_daily_stmt = text(
                """
                INSERT OR REPLACE INTO daily_data (stock_id, date, open, high, low, close, volume)
                VALUES (:stock_id, :date, :open, :high, :low, :close, :volume)
            """
            )
            session.execute(upsert_daily_stmt, daily_data_records)

            # Upsert indicator data
            indicator_data_df["date"] = pd.to_datetime(
                indicator_data_df["date"]
            ).dt.date
            indicator_data_records = indicator_data_df.to_dict("records")
            upsert_indicator_stmt = text(
                """
                INSERT OR REPLACE INTO technical_indicators (stock_id, date, indicator_name, value)
                VALUES (:stock_id, :date, :indicator_name, :value)
            """
            )
            session.execute(upsert_indicator_stmt, indicator_data_records)

            session.commit()
            logger.info(
                f"Successfully upserted {len(daily_data_records)} daily data records and {len(indicator_data_records)} indicator data records"
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error in bulk_upsert_data: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def get_stock_data_with_indicators(self, symbol, start_date, end_date):
        session = self.Session()
        stock = session.query(Stock).filter_by(symbol=symbol).first()

        if not stock:
            session.close()
            return None

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

        session.close()

        if not daily_data:
            return None

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
        indicator_df = indicator_df.pivot(
            index="date", columns="indicator_name", values="value"
        )

        # Merge daily data with indicator data
        df = df.join(indicator_df)

        return df
