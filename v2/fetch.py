# Let's enhance the Data Fetching Module with error handling and logging functionalities.

import logging
import yfinance as yf
from pandas_datareader import data as pdr
import requests
import pandas as pd
import db


# Initialize logging
logging.basicConfig(filename='stock_data_fetch.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def chunks(lst, n, limit=None):
    """Yield successive n-sized chunks from lst."""
    if limit:
        for i in range(0, min(len(lst), limit), n):
            yield lst[i:i + n]
    else:
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

def scrape_ticker_list(ex):
    """Function to scrape a list of stock tickers from a JSON formatted string."""
    try:
        if ex == 'TSX':
            tsx_url = f"https://www.tsx.com/json/company-directory/search/tsx/%5E*"
            tsx_tickers = requests.get(tsx_url, timeout=5, verify=False)
            tsx_tickers.raise_for_status()  # Raise HTTPError for bad responses
            tsx_tickers = tsx_tickers.json()
            tickers = [result['symbol'] for result in tsx_tickers['results']]
            tickers2 = [t+'.TO' for t in tickers]
            tickers += tickers2
            return tickers
    except requests.RequestException as e:
        logging.error(f"Failed to scrape TSX tickers: {e}")
        return None

def fetch_historical_data(tickers, ex, start_date, end_date, limit=None):
    """Mock function to simulate fetching historical stock data for a specific ticker and date range."""
    try:
        logging.info(f"Starting data pull for {len(tickers)} tickers")
        yf.pdr_override()
        df_all = []
        from urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        for ticker in chunks(tickers, 500, limit):
            s = ' '
            ticker_chunk = s.join(ticker)
            session1 = requests.Session()
            session1.verify = False
            session1.trust_env = False
            adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
            session1.mount('http://', adapter)
            session1.mount('https://', adapter)


            df = pdr.get_data_yahoo(ticker_chunk, start_date, end=end_date, group_by='tickers', interval='1d', progress=True, threads=True, session=session1)
            df = df.stack(level=0)
            df.reset_index(level=[0, 1], inplace=True)
            df.rename(columns={'level_1':'Ticker'}, inplace=True)
            df['Exchange'] = ex
            df_all.append(df)
        df = pd.concat(df_all)
        return df
    except Exception as e:
        logging.error(f"Failed to fetch historical data: {e}")
        return None
    
    

if __name__ == '__main__':
    db_file = "pytrade/v2/historicalData.db"
    tickers = scrape_ticker_list('TSX')

    if tickers:
        data = fetch_historical_data(tickers, ex='TSX', start_date='2023-09-01', end_date='2023-09-30', limit=None)
        if data is not None:
            db.upsert_stock_data_from_df(data)
            logging.info("Successfully fetched and stored stock data.")
        else:
            logging.error("Failed to fetch stock data.")
    else:
        logging.error("Failed to fetch stock tickers.")
