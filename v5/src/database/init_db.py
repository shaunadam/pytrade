from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import os

Base = declarative_base()


class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    name = Column(String)
    last_updated = Column(DateTime)
    daily_data = relationship("DailyData", back_populates="stock")


class DailyData(Base):
    __tablename__ = "daily_data"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    stock = relationship("Stock", back_populates="daily_data")


def init_db(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "stocks.db")
    init_db(db_path)
    print(f"Database initialized at {db_path}")