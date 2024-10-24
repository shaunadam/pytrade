# src/database/init_db.py

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
import os

Base = declarative_base()


class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    name = Column(String)
    last_updated = Column(DateTime)
    daily_data = relationship("DailyData", back_populates="stock")
    weekly_data = relationship("WeeklyData", back_populates="stock")
    technical_indicators = relationship("TechnicalIndicator", back_populates="stock")
    weekly_technical_indicators = relationship(
        "WeeklyTechnicalIndicator", back_populates="stock"
    )  # New relationship


class DailyData(Base):
    __tablename__ = "daily_data"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    stock = relationship("Stock", back_populates="daily_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uix_stock_date"),
        Index("idx_daily_data_stock_date", "stock_id", "date"),
    )


class WeeklyData(Base):
    __tablename__ = "weekly_data"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    week_start_date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    stock = relationship("Stock", back_populates="weekly_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "week_start_date", name="uix_stock_week"),
        Index("idx_weekly_data_stock_week", "stock_id", "week_start_date"),
    )


class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False)
    indicator_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    time_frame = Column(String, nullable=False, default="daily")
    stock = relationship("Stock", back_populates="technical_indicators")

    __table_args__ = (
        UniqueConstraint(
            "stock_id",
            "date",
            "indicator_name",
            "time_frame",
            name="uix_stock_date_indicator",
        ),
        Index("idx_technical_indicators_stock_date", "stock_id", "date"),
    )


class WeeklyTechnicalIndicator(Base):
    __tablename__ = "weekly_technical_indicators"
    id = Column(Integer, primary_key=True)
    stock_id = Column(
        Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False
    )
    date = Column(Date, nullable=False)
    indicator_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    stock = relationship("Stock", back_populates="weekly_technical_indicators")

    __table_args__ = (
        UniqueConstraint(
            "stock_id",
            "date",
            "indicator_name",
            name="uix_weekly_stock_date_indicator",
        ),
        Index("idx_weekly_technical_indicators_stock_date", "stock_id", "date"),
    )


def init_db(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "stocks.db")
    init_db(db_path)
    print(f"Database initialized at {db_path}")
