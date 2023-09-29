import json
import yfinance as yf
from pandas_datareader import data as pdr
import requests
import db
import pandas as pd

def chunks(lst, n,limit=None):
    """Yield successive n-sized chunks from lst."""
    if limit:
        for i in range(0, min(len(lst),limit), n):
            yield lst[i:i + n]
    else:
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

def scrape_ticker_list(ex):
    """
    Function to scrape a list of stock tickers from a JSON formatted string.
    """
    if ex == 'TSX':
        
        tsx_url = f"https://www.tsx.com/json/company-directory/search/tsx/%5E*"
        tsx_tickers = requests.get(tsx_url,timeout=5,verify=False)
        tsx_tickers = tsx_tickers.json()
        #tsx_tickers = json.loads(tsx_tickers)
        tickers = [result['symbol'] for result in tsx_tickers['results']]
        tickers2 = [t+'.TO' for t in tickers]
        tickers += tickers2
        return tickers

# Mock function to simulate fetching historical stock data for a specific ticker and date range.
def fetch_historical_data(tickers, ex, start_date, end_date,limit=None):
    yf.pdr_override()
    df_all = []

    for ticker in chunks(tickers,500,limit):
        s = ' '
        ticker_chunk = s.join(ticker)
        session1 = requests.Session()
        session1.verify = False
        session1.trust_env = False
        from urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        df = pdr.get_data_yahoo(ticker_chunk, start_date, end =end_date, group_by='tickers',interval='1d' ,progress=True,threads=True,session=session1)
        df=df.stack(level = 0)
        df.reset_index(level=[0, 1], inplace=True)
        df.rename(columns={'level_1':'Ticker'},inplace=True)
        df['Exchange'] = ex
        df_all.append(df)
    df = pd.concat(df_all)

    return df



if __name__ == '__main__':
    db_file = "pytrade/v2/historcalData.db"
    tickers = scrape_ticker_list('TSX')
    data = fetch_historical_data(tickers, ex= 'TSX',start_date='2020-01-01', end_date='2023-09-29', limit=None)
    db.upsert_stock_data_from_df(db_file,data)
    # upsert_stock_data(db_path, records)  # Assuming upsert_stock_data is imported from the Database Module
