import requests
import db as db
import const as c
from helpers import chunks
import pandas_datareader as pdr
import yfinance as yf
import pendulum as pn


def db_setup(DB):
    # Setup commands on SQLITE DB
    tbl1 = "CREATE TABLE IF NOT EXISTS MarketData (Exchange char(10), Ticker char(10), Date date,Open real,High real,Low real,Close real,AdjClose real,Volume int, MACD float, EMA12 float, EMA26 float, EMA50 float, SMA12 float, SMA26 float, SMA50 float, RSI float)"
    tbl1a = "CREATE UNIQUE INDEX index_name ON MarketData(Date, Ticker)"
    tbl2 = "drop table if exists TMP"
    tbl2a = "CREATE TABLE TMP              (Exchange char(10), Ticker char(10), Date date,Open real,High real,Low real,Close real,AdjClose real,Volume int, MACD float, EMA12 float, EMA26 float, EMA50 float, SMA12 float, SMA26 float, SMA50 float, RSI float)"
    tbl3 = "CREATE TABLE IF NOT EXISTS Meta (Ticker char(20),RefreshedDate)"
    tbl3a = "CREATE UNIQUE INDEX idx_ticker ON Meta (Ticker)"
    setup = [tbl1, tbl1a, tbl2, tbl2a, tbl3, tbl3a]

    db.conn_exec(DB, setup)


def tickersTSX(
    DB,
    table,
    column=None,
    securities=[],
):
    """Refreshes list of all tickers."""
    tickers = []
    if len(securities) == 0:
        try:
            print("Refreshing Tickers")
            tickersList = requests.get(f"{c.TICKERURL}", timeout=5, verify=False)
            tickersList = tickersList.json()
            tickersList = tickersList["results"]
            for key in tickersList:
                tickers.append(key["symbol"])
            tickers = [t.replace(".", "-") for t in tickers]
            tickers = [t + ".TO" for t in tickers]
            print("Done refreshing Tickers")

        except Exception as err:  # requests.exceptions.Timeout as err:
            print("Ticker Refresh Failed")
            if column != None:
                tickerSQL = "SELECT DISTINCT " + column + " FROM " + table
                tickers = db.conn_read(DB, tickerSQL)
                print("Done Tickers Fall Back")
            else:
                print("No backup column set")
                tickers = []
    else:
        tickers = securities

    return tickers


def refreshDailyTSX(months=3, tickercol="Ticker", metaTable="Meta", metaOveride=False):
    """FVUI9H11KBU2JWVU"""
    today = pn.now()
    start = today.add(-1 * months)
    tickers = tickersTSX(c.DB, "marketData")
    if metaOveride == False:
        donotrefresh = db.conn_read(
            c.DB,
            "SELECT "
            + tickercol
            + " FROM "
            + metaTable
            + " where julianday()-julianday(RefreshedDate) <=1",
        )
        if donotrefresh:
            tickers = list(set(tickers) - set(donotrefresh))

    totalTickers = len(tickers)
    if totalTickers == 0:
        print("No tickers to refresh")

    i = 0
    for ticks in chunks(tickers, 20):
        s = " "
        ss = s.join(ticks)
        session1 = requests.Session()
        session1.verify = False
        session1.trust_env = False
        from urllib3.exceptions import InsecureRequestWarning

        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        df = pdr.get_data_yahoo(  # yahoo function has changed. need to work out a start, end. Also, this thing can do weekly pulls now!
            ss, start=start, end=today, interval="d", chunksize=20, session=session1
        )
        df = df.rename(columns={"Adj Close": "AdjClose"})

        if len(ticks) == 1 or totalTickers == 1:
            df = df.reset_index().rename(columns={"level_0": "Ticker"})
        else:
            df = df.stack(level=1).reset_index().rename(columns={"level_1": "Ticker"})


refreshDailyTSX()
