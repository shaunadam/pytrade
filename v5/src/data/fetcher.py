import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.init_db import Stock, DailyData, TechnicalIndicator
from src.analysis.indicators import sma, ema, rsi, macd
from datetime import datetime
import pandas as pd
from sqlalchemy.dialects.sqlite import insert
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

        stock_data = []
        indicator_data = []
        updated_symbols = set()

        for symbol in symbols:
            if symbol not in all_data.columns.levels[0]:
                logger.warning(f"No data found for {symbol}. Skipping.")
                continue

            symbol_data = all_data[symbol]
            if symbol_data.empty:
                logger.warning(f"Empty data for {symbol}. Skipping.")
                continue

            updated_symbols.add(symbol)
            stock = session.query(Stock).filter_by(symbol=symbol).first()
            if not stock:
                stock = Stock(symbol=symbol, name=symbol)
                session.add(stock)
                session.flush()

            indicators = self.calculate_indicators(symbol_data["Close"])

            for date, row in symbol_data.iterrows():
                stock_data.append(
                    {
                        "stock_id": stock.id,
                        "date": date.date(),
                        "open": row["Open"],
                        "high": row["High"],
                        "low": row["Low"],
                        "close": row["Close"],
                        "adjclose": row[
                            "Adj Close"
                        ],  # Changed from 'adjclose' to 'Adj Close'
                        "volume": row["Volume"],
                    }
                )

                for indicator, value in indicators.loc[date].items():
                    if pd.notna(value):
                        indicator_data.append(
                            {
                                "stock_id": stock.id,
                                "date": date.date(),
                                "indicator_name": indicator,
                                "value": value,
                            }
                        )

            stock.last_updated = datetime.now()

        # Bulk insert daily data
        if stock_data:
            self.bulk_upsert(session, DailyData, stock_data, ["stock_id", "date"])

        # Bulk insert indicator data
        if indicator_data:
            self.bulk_upsert(
                session,
                TechnicalIndicator,
                indicator_data,
                ["stock_id", "date", "indicator_name"],
            )

        session.commit()
        session.close()

        logger.info(f"Updated {len(updated_symbols)} stocks successfully")
        logger.info(
            f"Skipped {len(symbols) - len(updated_symbols)} symbols due to missing data"
        )

    def bulk_upsert(self, session, model, data, conflict_columns):
        if not data:
            return

        table = model.__table__
        stmt = insert(table).values(data)

        update_dict = {
            c.name: c for c in stmt.excluded if c.name not in conflict_columns
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns, set_=update_dict
        )

        session.execute(stmt)

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

        # Convert to DataFrame
        df = pd.DataFrame([d.__dict__ for d in daily_data])
        df.set_index("date", inplace=True)
        df.index = pd.to_datetime(df.index)

        # Add indicators
        for indicator in indicators:
            df.loc[indicator.date, indicator.indicator_name] = indicator.value

        return df
