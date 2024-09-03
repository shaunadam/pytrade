import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.init_db import Stock, DailyData, TechnicalIndicator
from src.analysis.indicators import sma, ema, rsi, macd, bollinger_bands
from datetime import datetime
import pandas as pd


class DataFetcher:
    def __init__(self, db_path):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)

    def fetch_stock_data(self, symbol, start_date, end_date):
        data = yf.download(symbol, start=start_date, end=end_date)
        return data

    def calculate_indicators(self, data):
        indicators = {}
        indicators["SMA"] = sma(data["Close"])
        indicators["EMA"] = ema(data["Close"])
        indicators["RSI"] = rsi(data["Close"])

        macd_data = macd(data["Close"])
        indicators["MACD"] = macd_data["MACD"]
        indicators["MACD_Signal"] = macd_data["Signal"]
        indicators["MACD_Histogram"] = macd_data["Histogram"]

        bb_data = bollinger_bands(data["Close"])
        indicators["BB_SMA"] = bb_data["SMA"]
        indicators["BB_Upper"] = bb_data["Upper"]
        indicators["BB_Lower"] = bb_data["Lower"]

        return pd.DataFrame(indicators)

    def update_stock_data(self, symbol, start_date, end_date):
        session = self.Session()
        stock = session.query(Stock).filter_by(symbol=symbol).first()

        if not stock:
            stock = Stock(symbol=symbol, name=yf.Ticker(symbol).info["longName"])
            session.add(stock)
            session.commit()

        new_data = self.fetch_stock_data(symbol, start_date, end_date)
        indicators = self.calculate_indicators(new_data)

        for date, row in new_data.iterrows():
            daily_data = DailyData(
                stock_id=stock.id,
                date=date.date(),
                open=row["Open"],
                high=row["High"],
                low=row["Low"],
                close=row["Close"],
                volume=row["Volume"],
            )
            session.add(daily_data)

            # Add technical indicators
            for indicator, value in indicators.loc[date].items():
                if pd.notna(value):
                    tech_indicator = TechnicalIndicator(
                        stock_id=stock.id,
                        date=date.date(),
                        indicator_name=indicator,
                        value=value,
                    )
                    session.add(tech_indicator)

        stock.last_updated = datetime.now()
        session.commit()
        session.close()

    def update_all_stocks(self, symbols, start_date, end_date):
        for symbol in symbols:
            print(f"Updating data for {symbol}")
            self.update_stock_data(symbol, start_date, end_date)
        print("All stocks updated successfully")

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

        # Add indicators
        for indicator in indicators:
            df.loc[indicator.date, indicator.indicator_name] = indicator.value

        return df
