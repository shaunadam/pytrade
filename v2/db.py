# Import PostgreSQL and Pandas libraries
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine

# Initialize the PostgreSQL database and tables
def initialize_database():
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="localdev",
        user="shaun",
        password="123456"
    )
    cursor = conn.cursor()

    # Create table for indicator metadata first
    cursor.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS indicator_metadata (
                      IndicatorID SERIAL PRIMARY KEY,
                      IndicatorName VARCHAR(50),
                      Parameters VARCHAR(50),
                      Description TEXT)'''))

    # Create table for stock data
    cursor.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS stock_data (
                      Date DATE,
                      Ticker VARCHAR(10),
                      "Adj Close" FLOAT,
                      Close FLOAT,
                      High FLOAT,
                      Low FLOAT,
                      Open FLOAT,
                      Volume FLOAT,
                      Exchange VARCHAR(10),
                      PRIMARY KEY (Date, Ticker, Exchange))'''))

    # Now create table for technical indicators
    cursor.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS technical_indicators (
                      IndicatorID INT,
                      Exchange VARCHAR(10),
                      Ticker VARCHAR(10),
                      Date DATE,
                      Value1 FLOAT,
                      Value2 FLOAT,
                      Value3 FLOAT,
                      PRIMARY KEY (Date, Ticker, IndicatorID),
                      FOREIGN KEY (IndicatorID) REFERENCES indicator_metadata(IndicatorID))'''))

    # Create an index for faster queries (if not exists)
    cursor.execute(sql.SQL("CREATE INDEX IF NOT EXISTS idx_ticker_date_ind ON technical_indicators (Ticker, Date, IndicatorID)"))

    conn.commit()
    conn.close()

# Insert or Update stock data into the stock_data table from a DataFrame
engine = create_engine('postgresql://shaun:123456@localhost:5432/localdev')

def upsert_stock_data_from_df(df):
    df.to_sql('stock_data', engine, if_exists='append', index=False)


# Delete stock data for a specific ticker and date
def delete_stock_data(ticker, start_date, end_date):
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="localdev",
        user="shaun",
        password="123456"
    )
    cursor = conn.cursor()

    # Delete stock data within the date range
    cursor.execute(sql.SQL("DELETE FROM stock_data WHERE ticker=%s AND date BETWEEN %s AND %s"), (ticker, start_date, end_date))

    conn.commit()
    conn.close()

# Function to insert technical indicators into the technical_indicators table
def insert_technical_indicators(indicator_data):
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="localdev",
        user="shaun",
        password="123456"
    )
    cursor = conn.cursor()

    # Prepare the SQL query
    sql_query = sql.SQL('''INSERT INTO technical_indicators (IndicatorID, Exchange, Ticker, Date, Value1, Value2, Value3)
                   VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (Date, Ticker, IndicatorID) DO UPDATE SET Value1 = excluded.Value1, Value2 = excluded.Value2, Value3 = excluded.Value3''')

    # Execute the SQL query with the indicator data
    cursor.executemany(sql_query, indicator_data)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
