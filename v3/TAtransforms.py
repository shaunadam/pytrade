import pandas as pd
import pandas_ta as ta
import sqlite3 as sq
from sqlite3 import Error
import pull_data as pu
import db as db1
import pendulum
import const as c

def buildTA(start,tickers=None):
     df = pu.getDF(start,period = 'D',ticker=tickers)
     df.set_index('Ticker',append=True,inplace=True,drop=True)
     df.drop('Date',axis=1,inplace=True)
     df = df.reorder_levels(['Ticker','Date'],axis=0)
     df.sort_index(level=['Ticker','Date'],inplace=True)
     for tick, df2 in df.groupby(level=0):
          if len(df2)>50:
               df2.drop(['MACD','EMA12','EMA26','EMA50','SMA12','SMA26','SMA50'],axis=1,inplace=True)
               df2.ta.macd(close='Adj_Close',append=True)
               df2.ta.ema(close='Adj_Close',length=12,append=True)
               df2.ta.ema(close='Adj_Close',length=26,append=True)
               df2.ta.ema(close='Adj_Close',length=50,append=True)

               df2.ta.sma(close='Adj_Close',length=12,append=True)
               df2.ta.sma(close='Adj_Close',length=26,append=True)
               df2.ta.sma(close='Adj_Close',length=50,append=True)
               df2.rename(columns={'MACDh_12_26_9':'MACD','EMA_12':'EMA12','EMA_26':'EMA26','EMA_50':'EMA50','SMA_12':'SMA12','SMA_26':'SMA26','SMA_50':'SMA50'},inplace=True)
               df.update(df2)
     df.reset_index(inplace=True)
     df.rename(columns={'Adj_Close':'AdjClose'},inplace=True)
     return df

def updateTA(start):
     tickerSQL = "SELECT DISTINCT Ticker FROM marketData"
     tickers = db1.conn_read(db,tickerSQL)
     #tickers = ['ABX.TO','SU.TO']

     db = c.DB
     


     prog = 0
     for ticks in db1.chunks(tickers,20):
          prog += len(ticks)
          df = buildTA(start,ticks)
          print(f'Currently processing {prog} of {len(tickers)} tickers')
          print(ticks)
          DeleteData = "DELETE FROM marketData where ROWID IN (SELECT F.ROWID FROM marketData F JOIN taTMP T WHERE F.Ticker = T.Ticker and F.Date = T.Date)"
          insData = "INSERT INTO marketData SELECT 'TSX', Ticker, Date,Open ,High , Low , Close, AdjClose, Volume ,MACD ,EMA12,EMA26,EMA50,SMA12,SMA26,SMA50,RSI FROM taTMP"
          conn = None
          try:
               conn = sq.connect(db)
               df.to_sql("taTMP", conn,if_exists='replace', index=False)
               db1.conn_exec(db,DeleteData)
               db1.conn_exec(db,insData)

          except Error as e:
               print(e)
          finally:
               if conn:
                    conn.close()


