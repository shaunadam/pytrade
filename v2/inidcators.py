# Refactoring the given code to improve its structure, maintainability, and readability.

# Importing required libraries
import psycopg2
import pandas as pd
import logging
from io import StringIO
from datetime import datetime, timedelta
from typing import List, Dict, Any

def setup_logging():
    """
    Setup logging configuration
    """
    # Create or get the root logger
    logger = logging.getLogger()

    # Clear previous handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Set the logging level
    logger.setLevel(logging.INFO)

    # Create and add the file handler
    file_handler = logging.FileHandler('indicators.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))
    logger.addHandler(file_handler)

    # Create and add the stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))
    logger.addHandler(stream_handler)


def get_multi_ticker_data_pg(conn, tickers: List[str], days: int = 300) -> pd.DataFrame:
    """
    Fetch stock data for multiple tickers within a given date range
    """
    logging.info("Start retrieving ticker data into DataFrame")
    date_from = datetime.now() - timedelta(days=days)
    query = """
    SELECT * FROM stock_data
    WHERE "Ticker" = ANY(%s) AND "Date" >= %s
    """
    df = pd.read_sql_query(query, conn, params=(tickers, date_from))
    logging.info("Finished retrieving ticker data into DataFrame")
    return df


def update_indicator_metadata_pg(conn, indicator_name: str, parameters: str, description: str) -> int:
    """
    Update indicator metadata in the PostgreSQL database
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM indicator_metadata WHERE IndicatorName = %s", (indicator_name,))
    data = cur.fetchone()
    if data is None:
        cur.execute(
            "INSERT INTO indicator_metadata (IndicatorName, Parameters, Description) VALUES (%s, %s, %s)",
            (indicator_name, parameters, description),
        )
        conn.commit()
        cur.execute("SELECT lastval();")
        id_of_new_row = cur.fetchone()[0]
        logging.info(f"Added new indicator metadata for {indicator_name}")
        return id_of_new_row
    return data[0]  # Assuming IndicatorID is the first column

def transform_to_db_format(df: pd.DataFrame, exchange: str, indicator_id_map: Dict[str, int]) -> pd.DataFrame:
    """
    Transform the DataFrame into the format suitable for database insertion
    """
    logging.info("Start transforming DF for insertion")
    dfs = []
    for indicator, indicator_id in indicator_id_map.items():
        temp_df = df[['Ticker', 'Date', indicator]].copy()
        temp_df['IndicatorID'] = indicator_id
        temp_df['Exchange'] = exchange
        temp_df['Value1'] = temp_df[indicator]
        temp_df = temp_df.drop(indicator, axis=1)
        dfs.append(temp_df)
    transformed_df = pd.concat(dfs, ignore_index=True)
    transformed_df = transformed_df[['IndicatorID', 'Exchange', 'Ticker', 'Date', 'Value1']]
    logging.info("Finished transforming DF for insertion")
    return transformed_df

def calculate_multiple_indicators(df: pd.DataFrame) -> pd.DataFrame:
    logging.info(f"Start calculating indicators")
    indicator_meta = {}
    df_copy = df.copy()  # Create a copy to avoid SettingWithCopyWarning
    
    # Calculate SMA indicators
    for window in [10, 50, 200]:
        col_name = f"SMA_{window}"
        df_copy[col_name] = df_copy.groupby("Ticker")["Close"].transform(
            lambda x: x.rolling(window=window).mean()
        )
        meta = {
            "Parameters": f"Window: {window}",
            "Description": f"Simple Moving Average with a window of {window}",
        }
        indicator_meta[col_name] = meta

    # Calculate EMA indicators
    for span in [10, 50, 200]:
        col_name = f"EMA_{span}"
        df_copy[col_name] = df_copy.groupby("Ticker")["Close"].transform(
            lambda x: x.ewm(span=span, adjust=False).mean()
        )
        meta = {
            "Parameters": f"Span: {span}",
            "Description": f"Exponential Moving Average with a span of {span}",
        }
        indicator_meta[col_name] = meta

    # Calculate RSI_14
    df_copy["Delta"] = df_copy.groupby("Ticker")["Close"].transform(lambda x: x.diff())
    df_copy["Gain"] = df_copy.groupby("Ticker")["Delta"].transform(lambda x: x.where(x > 0, 0))
    df_copy["Loss"] = df_copy.groupby("Ticker")["Delta"].transform(lambda x: -x.where(x < 0, 0))
    avg_gain = df_copy.groupby("Ticker")["Gain"].transform(lambda x: x.rolling(window=14).mean())
    avg_loss = df_copy.groupby("Ticker")["Loss"].transform(lambda x: x.rolling(window=14).mean())
    rs = avg_gain / avg_loss
    df_copy["RSI_14"] = 100 - (100 / (1 + rs))
    meta = {
        "Parameters": f"Window: 14",
        "Description": "Relative Strength Index with a window of 14",
    }
    indicator_meta["RSI_14"] = meta

    # Calculate MACD_12_26_9
    ema_12 = df_copy.groupby("Ticker")["Close"].transform(lambda x: x.ewm(span=12, adjust=False).mean())
    ema_26 = df_copy.groupby("Ticker")["Close"].transform(lambda x: x.ewm(span=26, adjust=False).mean())
    df_copy["MACD_12_26_9_Line"] = ema_12 - ema_26
    df_copy["MACD_12_26_9_Signal"] = df_copy.groupby("Ticker")["MACD_12_26_9_Line"].transform(
        lambda x: x.ewm(span=9, adjust=False).mean()
    )
    df_copy["MACD_12_26_9"] = df_copy["MACD_12_26_9_Line"] - df_copy["MACD_12_26_9_Signal"]
    meta = {
        "Parameters": "Short Span: 12, Long Span: 26, Signal Span: 9",
        "Description": "Moving Average Convergence Divergence",
    }
    indicator_meta["MACD_12_26_9"] = meta
    indicator_meta["MACD_12_26_9_Line"] = meta
    indicator_meta["MACD_12_26_9_Signal"] = meta

    # Drop temporary columns used for calculations
    df_copy.drop(columns=["Delta", "Gain", "Loss"], inplace=True)
    logging.info(f"Finished calculating indicators")
    
    return df_copy, indicator_meta


# Function to delete the last N days of indicators
def delete_last_n_days_indicators_pg(conn, tickers, days=30):
    logging.info("Start deleting last N days of indicators")
    date_from = datetime.now() - timedelta(days=days)
    query = """
    DELETE FROM technical_indicators
    WHERE \"ticker\" = ANY(%s) AND \"date\" >= %s
    """
    cur = conn.cursor()
    cur.execute(query, (tickers, date_from))
    conn.commit()
    logging.info("Finished deleting last N days of indicators")

# Refactored Function to write indicators to the database
def write_indicators_to_db_pg(multi_ticker_data, conn, tickers):
    cur = conn.cursor()

    # Extract the last 30 days of indicators
    last_30_days_df = multi_ticker_data[multi_ticker_data['Date'] >= (datetime.now() - timedelta(days=30))]
    indicators, indicator_meta = calculate_multiple_indicators(last_30_days_df)
    indicator_id_map = {}
    for indicator, metadata in indicator_meta.items():
        id = update_indicator_metadata_pg(
            conn, indicator, metadata["Parameters"], metadata["Description"]
        )
        indicator_id_map[indicator] = id
    # Your existing logic for transforming data into DB format
    transformed_last_30_days_df = transform_to_db_format(indicators, "TSX", indicator_id_map)

    # Delete the last 30 days of indicators from the database
    delete_last_n_days_indicators_pg(conn, tickers, days=30)

    # Insert the new last 30 days into the database
    logging.info(f"Start writing new last 30 days indicator data to db")
    output = StringIO()
    transformed_last_30_days_df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    cur = conn.cursor()
    cur.copy_from(output, 'technical_indicators', null="")  # Assuming technical_indicators is the table name
    conn.commit()
    logging.info(f"Finished writing new last 30 days indicator data to db")

# Refactored Function to process all tickers
def process_all_tickers_pg(db_params: Dict[str, Any]):
    """
    Process all tickers: fetch data, calculate indicators, and update the database
    """
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT \"Ticker\" FROM stock_data")
    tickers = [row[0] for row in cur.fetchall()]
    multi_ticker_data = get_multi_ticker_data_pg(conn, tickers)
    write_indicators_to_db_pg(multi_ticker_data, conn, tickers)
    conn.close()
    print("All tickers processed.")

# Main Execution
if __name__ == "__main__":
    setup_logging()
    db_params = {
        'dbname': 'localdev',
        'user': 'shaun',
        'password': '123456',
        'host': 'localhost',
        'port': 5432
    }
    process_all_tickers_pg(db_params)

