import pandas as pd
import sqlite3 as sq
from sqlite3 import Error
import pull_data as pu

def buildTA(tickers=None):
     df = pu.getDF('2021-01-01',period = 'D',ticker=tickers)
     t1 = 1

buildTA(['ABX.TO','SU.TO'])