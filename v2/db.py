# Import SQLite library
import sqlite3
import os

# Initialize the SQLite database and tables
def initialize_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table for stock data with 'exchange' field
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock_data (
                      ticker TEXT,
                      exchange TEXT,
                      date TEXT,
                      open REAL,
                      high REAL,
                      low REAL,
                      close REAL,
                      volume INTEGER,
                      PRIMARY KEY (ticker, exchange, date))''')
    
    # Create table for technical indicators
    cursor.execute('''CREATE TABLE IF NOT EXISTS technical_indicators (
                      ticker TEXT,
                      date TEXT,
                      sma REAL,
                      ema REAL,
                      rsi REAL,
                      macd REAL,
                      PRIMARY KEY (ticker, date))''')
    
    conn.commit()
    conn.close()

# Insert stock data into the stock_data table
def insert_stock_data(db_path, stock_data):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert stock data
    cursor.executemany("INSERT INTO stock_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)", stock_data)
    
    conn.commit()
    conn.close()

# Fetch stock data for a specific ticker and date range
def fetch_stock_data(db_path, ticker, start_date, end_date):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch stock data
    cursor.execute("SELECT * FROM stock_data WHERE ticker=? AND date BETWEEN ? AND ?", (ticker, start_date, end_date))
    data = cursor.fetchall()
    
    conn.close()
    return data

# Update stock data for a specific ticker and date
def update_stock_data(db_path, stock_data, ticker, date):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update stock data
    cursor.execute("UPDATE stock_data SET open=?, high=?, low=?, close=?, volume=? WHERE ticker=? AND date=?", stock_data + (ticker, date))
    
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