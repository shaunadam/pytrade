import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from typing import List

db_params = {
    'dbname': 'localdev',
    'user': 'shaun',
    'password': '123546',
    'host': 'localhost',
    'port': 5433
}
def get_multi_ticker_data_pg(conn, tickers: List[str], days: int = 300) -> pd.DataFrame:
    date_from = datetime.now() - timedelta(days=days)
    query = """
    SELECT * FROM stock_data
    WHERE "ticker" = ANY(%s) AND "date" >= %s
    """
    df = pd.read_sql_query(query, conn, params=(tickers, date_from))
    return df

def ticker_list():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT \"ticker\" FROM stock_data")
    tickers = [row[0] for row in cur.fetchall()]
    tick_list = []
    for x in tickers:
        tick_list.append({'value':x,'label':x})
    #multi_ticker_data = get_multi_ticker_data_pg(conn, tickers)
    conn.close()
    return tick_list

ticker = [ticker_list()[0]['value']]
stock_data = get_multi_ticker_data_pg(psycopg2.connect(**db_params),ticker,30)
print('test')
