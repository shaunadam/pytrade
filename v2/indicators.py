# Importing required libraries
import psycopg2
import pandas as pd
import logging
from io import StringIO

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



# Function to fetch stock data for multiple tickers within a given date range
def get_multi_ticker_data_pg(conn, tickers):
    logging.info("Start retrieving ticker data into DataFrame")
    query = "SELECT * FROM stock_data WHERE \"Ticker\" = ANY(%s)"
    df = pd.read_sql_query(query, conn, params=(tickers,))
    logging.info("Finished retrieving ticker data into DataFrame")
    return df


def update_indicator_metadata_pg(conn, indicator_name, parameters, description):
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



# Function to transform DataFrame for database insertion
def transform_to_db_format(df: pd.DataFrame, exchange: str, indicator_id_map: dict) -> pd.DataFrame:
    logging.info(f"Start transforming dataframe for db insertion")
    transformed_data = []
    for index, row in df.iterrows():
        ticker = row["Ticker"]
        date = row["Date"]
        for indicator in indicator_id_map.keys():
            value = row[indicator]
            transformed_row = {
                "IndicatorID": indicator_id_map[indicator],
                "Exchange": exchange,
                "Ticker": ticker,
                "Date": date,
                "Value1": value,
                "Value2": None,
                "Value3": None,
            }
            transformed_data.append(transformed_row)
    transformed_df = pd.DataFrame(transformed_data)
    logging.info(f"Finished transforming dataframe for db insertion")
    return transformed_df


# Function to calculate multiple indicators
def calculate_multiple_indicators(df: pd.DataFrame) -> pd.DataFrame:
    logging.info(f"Start calculating indicators")

    # Calculate SMA indicators
    for window in [10, 50, 200]:
        col_name = f"SMA_{window}"
        df[col_name] = df.groupby("Ticker")["Close"].transform(
            lambda x: x.rolling(window=window).mean()
        )

    # Calculate EMA indicators
    for span in [10, 50, 200]:
        col_name = f"EMA_{span}"
        df[col_name] = df.groupby("Ticker")["Close"].transform(
            lambda x: x.ewm(span=span, adjust=False).mean()
        )

    # Calculate RSI_14
    df["Delta"] = df.groupby("Ticker")["Close"].transform(lambda x: x.diff())
    df["Gain"] = df.groupby("Ticker")["Delta"].transform(lambda x: x.where(x > 0, 0))
    df["Loss"] = df.groupby("Ticker")["Delta"].transform(lambda x: -x.where(x < 0, 0))
    avg_gain = df.groupby("Ticker")["Gain"].transform(
        lambda x: x.rolling(window=14).mean()
    )
    avg_loss = df.groupby("Ticker")["Loss"].transform(
        lambda x: x.rolling(window=14).mean()
    )
    rs = avg_gain / avg_loss
    df["RSI_14"] = 100 - (100 / (1 + rs))

    # Calculate MACD_12_26_9
    ema_12 = df.groupby("Ticker")["Close"].transform(
        lambda x: x.ewm(span=12, adjust=False).mean()
    )
    ema_26 = df.groupby("Ticker")["Close"].transform(
        lambda x: x.ewm(span=26, adjust=False).mean()
    )
    df["MACD_Line"] = ema_12 - ema_26
    df["Signal_Line"] = df.groupby("Ticker")["MACD_Line"].transform(
        lambda x: x.ewm(span=9, adjust=False).mean()
    )
    df["MACD_12_26_9"] = df["MACD_Line"] - df["Signal_Line"]

    # Drop temporary columns used for calculations
    df.drop(columns=["Delta", "Gain", "Loss", "MACD_Line", "Signal_Line"], inplace=True)
    logging.info(f"Finished calculating indicators")
    return df


# Function to write indicators to the database
# Function to write indicators to the database
def write_indicators_to_db_pg(multi_ticker_data, conn):
    cur = conn.cursor()
    indicator_metadata_dict = {
        "SMA_10": {
            "Parameters": "Window: 10",
            "Description": "Simple Moving Average with a window of 10",
        },
        "SMA_50": {
            "Parameters": "Window: 50",
            "Description": "Simple Moving Average with a window of 50",
        },
        "SMA_200": {
            "Parameters": "Window: 200",
            "Description": "Simple Moving Average with a window of 200",
        },
        "EMA_10": {
            "Parameters": "Span: 10",
            "Description": "Exponential Moving Average with a span of 10",
        },
        "EMA_50": {
            "Parameters": "Span: 50",
            "Description": "Exponential Moving Average with a span of 50",
        },
        "EMA_200": {
            "Parameters": "Span: 200",
            "Description": "Exponential Moving Average with a span of 200",
        },
        "RSI_14": {
            "Parameters": "Window: 14",
            "Description": "Relative Strength Index with a window of 14",
        },
        "MACD_12_26_9": {
            "Parameters": "Short Span: 12, Long Span: 26, Signal Span: 9",
            "Description": "Moving Average Convergence Divergence",
        },
    }
    indicators_df = calculate_multiple_indicators(multi_ticker_data)

    indicator_id_map = {}
    for indicator, metadata in indicator_metadata_dict.items():
        id = update_indicator_metadata_pg(
            conn, indicator, metadata["Parameters"], metadata["Description"]
        )
        indicator_id_map[indicator] = id

    transformed_df = transform_to_db_format(indicators_df, "TSX", indicator_id_map)

    # Clear old data for specific Ticker, Date, and IndicatorID combinations
    # Clear old data for specific Ticker, Date, and IndicatorID combinations
    logging.info(f"Start finding tickers to overwrite")
    to_delete = transformed_df[["Ticker", "Date", "IndicatorID"]].drop_duplicates()
    delete_tuples = list(to_delete.itertuples(index=False, name=None))
    logging.info(f"Finished finding tickers to overwrite")

    # Batch delete
    logging.info(f"Start clearing data to overwrite")
    cur.executemany(
        "DELETE FROM technical_indicators WHERE Ticker = %s AND Date = %s AND IndicatorID = %s",
        delete_tuples,
    )
    conn.commit()


    logging.info(f"Finished clearing data to overwrite")

    # Update indicator metadata
    logging.info(f"Start updating indicator metadata")
    for indicator, metadata in indicator_metadata_dict.items():
        update_indicator_metadata_pg(
            conn, indicator, metadata["Parameters"], metadata["Description"]
        )
    logging.info(f"Finished updating indicator metadata")

    logging.info(f"Start writing new indicator data to db")
    output = StringIO()
    transformed_df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    cur = conn.cursor()
    cur.copy_from(output, 'technical_indicators', null="") # Assuming technical_indicators is the table name
    conn.commit()
    logging.info(f"Finished writing new indicator data to db")


# Function to process all tickers
def process_all_tickers_pg(db_params):
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT \"Ticker\" FROM stock_data")
    tickers = [row[0] for row in cur.fetchall()]
    multi_ticker_data = get_multi_ticker_data_pg(conn, tickers)
    write_indicators_to_db_pg(multi_ticker_data, conn)
    conn.close()

    print("All tickers processed.")


if __name__ == "__main__":
    db_params = {
        'dbname': 'localdev',
        'user': 'shaun',
        'password': '123456',
        'host': 'localhost',
        'port': 5432
    }
    process_all_tickers_pg(db_params)