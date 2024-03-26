
import db as db1
import requests
from pandas_datareader import data as pdr
import yfinance as yf
import pandas as pd
import const as c
import sqlite3 as sq
from sqlite3 import Error
import pendulum



yf.pdr_override()

def refreshTSX(p="1mo",secs = None):
    """Refreshes all tickers on TSX. Defaults to 1 month.
    “1d”, “5d”, “1mo”, “3mo”, “6mo”, “1y”, “2y”, “5y”, “10y”, “ytd”, “max”
    """
    print("Beginning Data Refresh")
    #SQLITE file
    db = c.DB

    #Setup commands on SQLITE DB
    tbl1 = "CREATE TABLE IF NOT EXISTS marketData (Exchange char(10), Ticker char(10), Date date,Open real,High real,Low real,Close real,AdjClose real,Volume int, MACD float, EMA12 float, EMA26 float, EMA50 float, SMA12 float, SMA26 float, SMA50 float, RSI float)"
    tbl1a = "CREATE UNIQUE INDEX index_name ON marketData(Date, Ticker)"
    tbl2 = "drop table if exists TMP"
    tbl2a = "CREATE TABLE TMP              (Exchange char(10), Ticker char(10), Date date,Open real,High real,Low real,Close real,AdjClose real,Volume int, MACD float, EMA12 float, EMA26 float, EMA50 float, SMA12 float, SMA26 float, SMA50 float, RSI float)"
    tbl3 = "CREATE TABLE IF NOT EXISTS Meta (Ticker char(20),Refreshed Date)"
    tbl3a = "CREATE UNIQUE INDEX idx_ticker ON Meta (Ticker)"
    setup = [tbl1,tbl1a,tbl2,tbl2a,tbl3,tbl3a]
    tickerSQL = "SELECT DISTINCT Ticker FROM marketData"
    db1.conn_exec(db,setup)

    if secs:
        tickers = secs
        metaoveride = True
    else:
        #holds a list of securities to check
        metaoveride = False
        tickers = []

        #Attempt to retrieve a list of securities from TSX website. If it times out just use a distinct list of securities already in DB
        try:
           # logging.basicConfig()
            #logging.getLogger().setLevel(logging.DEBUG)
            #requests_log = logging.getLogger("requests.packages.urllib3")
            #requests_log.setLevel(logging.DEBUG)
            #requests_log.propagate = True
            print("Refreshing Tickers")
            ti = requests.get(f"{c.TICKERURL}",timeout=5,verify=False)
            ti = ti.json()
            ti = ti['results']
            for key in ti:
                tickers.append(key['symbol'])
            tickers = [t.replace('.','-') for t in tickers]    
            tickers = [t + '.TO' for t in tickers]
            print("Done refreshing Tickers")
    

        except Exception as err:# requests.exceptions.Timeout as err: 
            print("Ticker Refresh Failed")            
            
            tickers = db1.conn_read(db,tickerSQL)
            print("Done Tickers Fall Back")

    
    mergeData = "DELETE FROM marketData where ROWID IN (SELECT F.ROWID FROM marketData F JOIN TMP T WHERE F.Ticker = T.Ticker and F.Date = T.Date)"
    insData = "INSERT INTO marketData SELECT 'TSX', Ticker, Date,Open ,High , Low , Close, AdjClose, Volume ,MACD ,EMA12,EMA26,EMA50,SMA12,SMA26,SMA50,RSI FROM TMP"
    tickers = [item for item in tickers if len(item)<15]
    lenTickers= len(tickers)
    dontRefresh = db1.conn_read(db,"SELECT Ticker FROM Meta where julianday()-julianday(Refreshed) <=1")
    if metaoveride != True:
        tickers = list(set(tickers) - set(dontRefresh))
    totTickers = len(tickers)
    print(f'{totTickers} remaining to be refreshed out of {lenTickers} found on TSX website.')
    if totTickers == 0:
        print("No tickers to refresh")

    i = 0
    for ticks in db1.chunks(tickers,100):
        s = ' '
        ss = s.join(ticks)
        session1 = requests.Session()
        session1.verify = False
        session1.trust_env = False
        from urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        df = pdr.get_data_yahoo(ss,period =p ,progress=True,threads=True,session=session1)
        df = df.rename(columns={"Adj Close": "AdjClose"})
    

        if len(ticks)==1 or totTickers == 1:
             df=df.reset_index().rename(columns={"level_0":"Ticker"})
        else:
            df=df.stack(level = 1).reset_index().rename(columns={"level_1":"Ticker"})

        db1.conn_insert_df('TMP',df,db,'replace')
        db1.conn_exec(db,mergeData)
        db1.conn_exec(db,insData)
        db1.conn_update_meta(ticks)

        i=i+len(ticks)
        print(i,"out of ",totTickers," checked")
    print("Data Refresh Complete")

def getDF(date,period = 'D',ticker = None):
    """Retrieve a dataframe for a:
    single ticker (string)
    list of tickers
    from date specified forward.
    Can also specify period = 'W' for weekly resample.
    """
    cols = ['Ticker', 'Date','Open' ,'High' , 'Low' , 'Close', 'AdjClose', 'Volume','MACD' ,'EMA12','EMA26','EMA50','SMA12','SMA26','SMA50','RSI']
    db = c.DB
    if ticker:
        if type(ticker) == list and len(ticker) >1:
            ticker = "','".join(ticker)
            ticker = "'"+ticker+"'"
            q =  "Select Ticker, Date,Open ,High , Low , Close, AdjClose, Volume, MACD ,EMA12,EMA26,EMA50,SMA12,SMA26,SMA50,RSI from marketData where Ticker in ("+ticker+") and Date >='"+date+"'"
            
        elif type(ticker) == list and len(ticker) ==1:
            q =  "Select Ticker, Date,Open ,High , Low , Close, AdjClose, Volume, MACD ,EMA12,EMA26,EMA50,SMA12,SMA26,SMA50,RSI from marketData where Ticker ='"+ticker[0]+"' and Date >='"+date+"'"
        elif type(ticker) == str:
            q =  "Select Ticker, Date,Open ,High , Low , Close, AdjClose, Volume, MACD ,EMA12,EMA26,EMA50,SMA12,SMA26,SMA50,RSI from marketData where Ticker ='"+ticker+"' and Date >='"+date+"'"
    else:
        q =  "Select Ticker, Date,Open ,High , Low , Close, AdjClose, Volume, MACD ,EMA12,EMA26,EMA50,SMA12,SMA26,SMA50,RSI from marketData where Date >='"+date+"'"
    df = db1.conn_read(db,q,False,False,cols)
    df =df.set_index([pd.DatetimeIndex(df['Date'])])
    return df


#merge TA and this weekly functions into a module name processing
#improve structure of this function - just barely pieced together
#refactor to use be called from Main with parameters
#refactor TA functions to be able to work on daily and weekly tables
#finish screeners
def dfWeekly(start,verbose = False):
    db = c.DB
    tickerSQL = "SELECT DISTINCT Ticker FROM marketData"
    tbl1 = "CREATE TABLE IF NOT EXISTS weeklyData (Exchange char(10), Ticker char(10), Date date,Open real,High real,Low real,Close real,AdjClose real,Volume int, MACD float, EMA12 float, EMA26 float, EMA50 float, SMA12 float, SMA26 float, SMA50 float, RSI float)"
    tbl1a = "CREATE UNIQUE INDEX weekly ON weeklyData(Date, Ticker)"
    setup = [tbl1,tbl1a]
    db1.conn_exec(db,setup)

    tickers = db1.conn_read(db,tickerSQL)

    prog = 0
    for ticks in db1.chunks(tickers,200):
        prog += len(ticks)
        print(f'Currently processing {prog} of {len(tickers)} tickers')
        if verbose == True:
            print(ticks)
        df = getDF(start, ticker=ticks)
        df= df.groupby('Ticker').resample('W-MON',label='left',closed='left').agg({'Open':'first','High':'max','Low':'min','Close':'last','AdjClose':'last','Volume':'sum'})
        df = df.sort_index()

        DeleteData = "DELETE FROM weeklyData where ROWID IN (SELECT F.ROWID FROM marketData F JOIN weeklyTMP T WHERE F.Ticker = T.Ticker and F.Date = T.Date)"
        insData = "INSERT INTO weeklyData SELECT 'TSX' 'Exchange', Ticker, Date,Open ,High , Low , Close, AdjClose, Volume ,null,null,null,null,null,null,null,null FROM weeklyTMP"
        conn = None
        try:
            conn = sq.connect(db)
            df.reset_index(inplace=True)
            df.to_sql("weeklyTMP", conn,if_exists='replace', index=False)
            db1.conn_exec(db,DeleteData)
            db1.conn_exec(db,insData)

        except Error as e:
            print(e)
        finally:
            if conn:
                conn.close()
if __name__ == '__main__':
    now = pendulum.now()
    start = now.subtract(years=c.TAYEARS).strftime('%Y-%m-%d')
    dfWeekly(start)