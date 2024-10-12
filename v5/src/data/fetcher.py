from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from src.database.init_db import Stock, DailyData, TechnicalIndicator
from src.analysis.indicators import sma, ema, rsi, macd
from datetime import datetime
import pandas as pd
import yfinance as yf
import logging
import traceback
from typing import List, Dict

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

    def update_all_stocks(self, symbols, start_date, end_date):
        """
        Fetches and updates daily stock data only.
        """
        self.set_update_progress(0, "Fetching data for all stocks...")
        all_data = self.fetch_stock_data(symbols, start_date, end_date)

        if all_data.empty:
            self.set_update_progress(100, "No data found for any symbols.")
            return

        self.set_update_progress(50, "Processing and inserting data...")

        session = self.Session()
        try:
            all_daily_data = []

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

                all_daily_data.append(daily_data)

                stock.last_updated = datetime.now().date()
                session.commit()

                progress = int(50 + (i + 1) / len(symbols) * 50)
                self.set_update_progress(
                    progress, f"Processed {i+1}/{len(symbols)} stocks"
                )

            # Concatenate all data
            combined_daily_data = pd.concat(all_daily_data, ignore_index=True)

            # Bulk upsert all data
            self.bulk_upsert_daily_data(session, combined_daily_data)

            self.set_update_progress(100, "All stocks updated successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating stocks: {str(e)}")
            logger.error(traceback.format_exc())
            self.set_update_progress(100, f"Error updating stocks: {str(e)}")
        finally:
            session.close()

    def update_indicators(self, symbols, start_date, end_date):
        """
        Recalculates and updates indicator data separately.
        """
        self.set_update_progress(0, "Recalculating indicators for all stocks...")
        session = self.Session()
        try:
            for i, symbol in enumerate(symbols):
                stock = session.query(Stock).filter_by(symbol=symbol).first()
                if not stock:
                    logger.warning(f"Stock {symbol} not found in database. Skipping.")
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

                if not daily_data:
                    logger.warning(f"No data found for {symbol}. Skipping.")
                    continue

                df = pd.DataFrame([d.__dict__ for d in daily_data])
                df = df.drop(["id", "stock_id"], axis=1, errors="ignore")
                df.set_index("date", inplace=True)
                df.index = pd.to_datetime(df.index)

                indicators = self.calculate_indicators(df["close"])

                # Delete existing indicators for this stock and date range
                session.query(TechnicalIndicator).filter(
                    TechnicalIndicator.stock_id == stock.id,
                    TechnicalIndicator.date >= start_date,
                    TechnicalIndicator.date <= end_date,
                ).delete()

                # Insert new indicators
                for date, row in indicators.iterrows():
                    for indicator_name, value in row.items():
                        if pd.notna(value):  # Only insert non-NaN values
                            indicator = TechnicalIndicator(
                                stock_id=stock.id,
                                date=date.date(),
                                indicator_name=indicator_name,
                                value=float(value),  # Ensure the value is a float
                            )
                            session.add(indicator)

                stock.last_updated = datetime.now().date()
                session.commit()

                progress = int((i + 1) / len(symbols) * 100)
                self.set_update_progress(
                    progress, f"Recalculated indicators for {i+1}/{len(symbols)} stocks"
                )

            self.set_update_progress(100, "All indicators recalculated successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Error recalculating indicators: {str(e)}")
            logger.error(traceback.format_exc())
            self.set_update_progress(100, f"Error recalculating indicators: {str(e)}")
        finally:
            session.close()

    def bulk_upsert_daily_data(self, session, daily_data_df):
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
            session.commit()
            logger.info(
                f"Successfully upserted {len(daily_data_records)} daily data records"
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error in bulk_upsert_daily_data: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def calculate_indicators(self, data):
        """
        Calculate technical indicators.
        """
        indicators = pd.DataFrame(index=data.index)
        indicators["SMA12"] = sma(data, 12)
        indicators["SMA26"] = sma(data, 26)
        indicators["SMA50"] = sma(data, 50)
        indicators["EMA12"] = ema(data, 12)
        indicators["EMA26"] = ema(data, 26)
        indicators["EMA50"] = ema(data, 50)
        indicators["RSI"] = rsi(data)
        macd_data = macd(data)
        indicators["MACD"] = macd_data["MACD"]
        indicators["MACD_Signal"] = macd_data["Signal"]
        indicators["MACD_Histogram"] = macd_data["Histogram"]

        # Drop rows where all indicator values are NaN
        indicators = indicators.dropna(how="all")

        return indicators

    def set_update_progress(self, progress, message=""):
        self.update_progress = progress
        self.update_message = message

    def get_update_progress(self):
        return self.update_progress, self.update_message
