# Import SQLite library
import sqlite3
import os

# Import SQLite and Pandas libraries
import sqlite3
import pandas as pd

# Initialize the SQLite database and tables
def initialize_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table for stock data with revised fields based on DataFrame structure
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock_data (
                      Date TEXT,
                      Ticker TEXT,
                      "Adj Close" REAL,
                      Close REAL,
                      High REAL,
                      Low REAL,
                      Open REAL,
                      Volume REAL,
                      Exchange TEXT,
                      PRIMARY KEY (Date, Ticker, Exchange))''')
    
    # Create table for technical indicators
    cursor.execute('''CREATE TABLE IF NOT EXISTS technical_indicators (
                      Exchange TEXT,
                      Ticker TEXT,
                      Date TEXT,
                      sma REAL,
                      ema REAL,
                      rsi REAL,
                      macd REAL,
                      PRIMARY KEY (Date, Ticker, Exchange))''')
    
    conn.commit()
    conn.close()

# Insert or Update stock data into the stock_data table from a DataFrame
def upsert_stock_data_from_df(db_path, df):
    conn = sqlite3.connect(db_path)
    
    # Insert or replace data directly from DataFrame
    df.to_sql('stock_data', conn, if_exists='replace', index=False)
    
    conn.commit()
    conn.close()


# Delete stock data for a specific ticker and date
def delete_stock_data(db_path, ticker, date):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Delete stock data
    cursor.execute("DELETE FROM stock_data WHERE ticker=? AND date=?", (ticker, date))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    db_file = "pytrade/v2/historcalData.db"
    initialize_database(db_file)