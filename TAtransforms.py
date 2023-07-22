import pandas as pd
import pandas_ta as ta
import sqlite3 as sq
from sqlite3 import Error
import pull_data as pu

def buildTA(tickers=None):
     df = pu.getDF('2021-01-01',period = 'D',ticker=tickers)
     df.set_index('Ticker',append=True,inplace=True,drop=True)
     df.drop('Date',axis=1,inplace=True)
     df = df.reorder_levels(['Ticker','Date'],axis=0)
     df.sort_index(level=['Ticker','Date'],inplace=True)
     for tick, df2 in df.groupby(level=0):
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
          t1=1

     t1 = 1

buildTA(['ABX.TO','SU.TO'])