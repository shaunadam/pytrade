# Import PostgreSQL and Pandas libraries
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, text

# Initialize the PostgreSQL database and tables
def initialize_database():
    conn = psycopg2.connect(
        host="my_postgres_container",
        port="5432",
        dbname="localdev",
        user="shaun",
        password="123546"
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
                      "adj close" FLOAT,
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
                      PRIMARY KEY (Date, Ticker, IndicatorID),
                      FOREIGN KEY (IndicatorID) REFERENCES indicator_metadata(IndicatorID))'''))

    # Create an index for faster queries (if not exists)
    cursor.execute(sql.SQL("CREATE INDEX IF NOT EXISTS idx_ticker_date_ind ON technical_indicators (Ticker, Date, IndicatorID)"))

    conn.commit()
    conn.close()

# Insert or Update stock data into the stock_data table from a DataFrame
engine = create_engine('postgresql://shaun:123546@my_postgres_container:5432/localdev')

def upsert_stock_data_from_df(df):
    # Step 1: Identify overlapping date ranges for each Ticker
    overlap = df.groupby('ticker')['date'].agg(['min', 'max']).reset_index()
    
    conn = psycopg2.connect(
        host="my_postgres_container",
        port="5432",
        dbname="localdev",
        user="shaun",
        password="123546"
    )
    cursor = conn.cursor()
    
    # Step 2: Issue DELETE queries for each Ticker and corresponding date range
    for row in overlap.iterrows():
        ticker, start_date, end_date = row[1]['ticker'], row[1]['min'], row[1]['max']
        cursor.execute(sql.SQL("DELETE FROM stock_data WHERE \"ticker\"=%s AND \"date\" BETWEEN %s AND %s"), (ticker, start_date, end_date))
    
    # Commit all DELETE queries in a single transaction
    conn.commit()
    conn.close()
    
    # Step 3: Insert the new data
    df.to_sql('stock_data', engine, if_exists='append', index=False) #need to make df column and db column cases match!!!

# Function to insert technical indicators into the technical_indicators table
def insert_technical_indicators(indicator_data):
    conn = psycopg2.connect(
        host="my_postgres_container",
        port="5432",
        dbname="localdev",
        user="shaun",
        password="123546"
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
