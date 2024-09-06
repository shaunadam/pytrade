import yfinance as yf
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from src.database.init_db import Stock, DailyData, TechnicalIndicator
from src.analysis.indicators import sma, ema, rsi, macd
from datetime import datetime
import pandas as pd
import numpy as np
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self, db_path):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.create_requests_session()

    def create_requests_session(self):
        session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(
            pool_connections=100, pool_maxsize=100, max_retries=retries
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_stock_data(self, symbols, start_date, end_date):
        try:
            data = yf.download(
                symbols,
                start=start_date,
                end=end_date,
                group_by="ticker",
                threads=True,
                session=self.session,
            )
            return data
        except Exception as e:
            logger.error(f"Error fetching stock data: {str(e)}")
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

    def update_all_stocks(self, symbols, start_date, end_date):
        session = self.Session()
        logger.info(f"Fetching data for {len(symbols)} symbols")
        all_data = self.fetch_stock_data(symbols, start_date, end_date)

        if all_data.empty:
            logger.error("Failed to fetch any stock data")
            return

        daily_data_list = []
        indicator_data_list = []
        stocks_to_update = []

        for symbol in symbols:
            if symbol not in all_data.columns.levels[0]:
                logger.warning(f"No data found for {symbol}. Skipping.")
                continue

            symbol_data = all_data[symbol]
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
            daily_data = daily_data.dropna()
            daily_data_list.append(
                daily_data[
                    ["stock_id", "date", "open", "high", "low", "close", "volume"]
                ]
            )

            indicator_data = indicators.reset_index()
            indicator_data["stock_id"] = stock.id
            indicator_data = indicator_data.melt(
                id_vars=["Date", "stock_id"],
                var_name="indicator_name",
                value_name="value",
            )
            indicator_data = indicator_data.rename(columns={"Date": "date"})
            indicator_data = indicator_data.dropna()
            indicator_data_list.append(indicator_data)

            stocks_to_update.append(
                {"id": stock.id, "last_updated": datetime.now().date()}
            )

        all_daily_data = pd.concat(daily_data_list, ignore_index=True)
        all_indicator_data = pd.concat(indicator_data_list, ignore_index=True)

        self.bulk_upsert_daily_data(session, all_daily_data)
        self.bulk_upsert_indicator_data(session, all_indicator_data)

        session.bulk_update_mappings(Stock, stocks_to_update)

        session.commit()
        session.close()

        logger.info(f"Updated {len(symbols)} stocks successfully")

    def bulk_upsert_daily_data(self, session, df):
        df["date"] = df["date"].dt.date  # Convert to Python date objects
        existing = pd.read_sql(
            select(DailyData.id, DailyData.stock_id, DailyData.date),
            session.connection(),
        )
        existing["date"] = pd.to_datetime(existing["date"]).dt.date

        merged = df.merge(existing, on=["stock_id", "date"], how="left", indicator=True)
        new_records = merged[merged["_merge"] == "left_only"].drop(
            ["_merge", "id"], axis=1
        )
        update_records = merged[merged["_merge"] == "both"].drop("_merge", axis=1)

        if not new_records.empty:
            session.bulk_insert_mappings(DailyData, new_records.to_dict("records"))

        if not update_records.empty:
            session.bulk_update_mappings(DailyData, update_records.to_dict("records"))

    def bulk_upsert_indicator_data(self, session, df):
        df["date"] = df["date"].dt.date  # Convert to Python date objects
        existing = pd.read_sql(
            select(
                TechnicalIndicator.id,
                TechnicalIndicator.stock_id,
                TechnicalIndicator.date,
                TechnicalIndicator.indicator_name,
            ),
            session.connection(),
        )
        existing["date"] = pd.to_datetime(existing["date"]).dt.date

        merged = df.merge(
            existing,
            on=["stock_id", "date", "indicator_name"],
            how="left",
            indicator=True,
        )
        new_records = merged[merged["_merge"] == "left_only"].drop(
            ["_merge", "id"], axis=1
        )
        update_records = merged[merged["_merge"] == "both"].drop("_merge", axis=1)

        if not new_records.empty:
            session.bulk_insert_mappings(
                TechnicalIndicator, new_records.to_dict("records")
            )

        if not update_records.empty:
            session.bulk_update_mappings(
                TechnicalIndicator, update_records.to_dict("records")
            )

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

        df = pd.DataFrame([d.__dict__ for d in daily_data])
        df.set_index("date", inplace=True)
        df.index = pd.to_datetime(df.index)

        for indicator in indicators:
            df.loc[indicator.date, indicator.indicator_name] = indicator.value

        return df
