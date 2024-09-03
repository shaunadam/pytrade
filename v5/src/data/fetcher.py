import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.init_db import Stock, DailyData
from datetime import datetime
import pandas as pd


class DataFetcher:
    def __init__(self, db_path):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)

    def fetch_stock_data(self, symbol, start_date, end_date):
        data = yf.download(symbol, start=start_date, end=end_date)
        return data

    def update_stock_data(self, symbol, start_date, end_date):
        session = self.Session()
        stock = session.query(Stock).filter_by(symbol=symbol).first()

        if not stock:
            stock = Stock(symbol=symbol, name=yf.Ticker(symbol).info["longName"])
            session.add(stock)
            session.commit()

        new_data = self.fetch_stock_data(symbol, start_date, end_date)

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

        stock.last_updated = datetime.now()
        session.commit()
        session.close()

    def update_all_stocks(self, symbols, start_date, end_date):
        for symbol in symbols:
            print(f"Updating data for {symbol}")
            self.update_stock_data(symbol, start_date, end_date)
        print("All stocks updated successfully")
