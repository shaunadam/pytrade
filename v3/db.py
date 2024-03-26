from sqlite3 import Error
import sqlite3 as sq
import requests
import pandas as pd
import const as c

def conn_exec(db_file,c="",verbose=False):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sq.connect(db_file)
        if verbose:
            print('Execute: ',c)
        if isinstance(c, list):
            for com in c:
                conn.cursor().execute(com)
            conn.commit()
        else:
            conn.cursor().execute(c)
            conn.commit()

    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def conn_insert_df(tblName,df,db_file,insertMode = 'replace'):
    """Inserts a dataframe into a SQLlite table.
    If insertMode = 'repalce' the table will be deleted first.
    """
    conn = None
    try:
        conn = sq.connect(db_file)
        if insertMode == 'replace':
            dd = f"Delete From "+ tblName 
            conn.cursor().execute(dd)
            conn.commit()

        df.to_sql(tblName, conn,if_exists='append', index=False)

    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def conn_update_meta(val):
    """Updates the metadata table with the date ticker was last pulled
    """
    db = c.DB
    conn = None
    try:
        conn = sq.connect(db)
        for v in val:
            c = f"REPLACE INTO Meta (Ticker,Refreshed) VALUES('"+v+"',datetime(CURRENT_TIMESTAMP, 'localtime'))"
            conn.cursor().execute(c)
        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def conn_read(db_file,c="", verbose=False, single=True, cols = None, ind = None):
    """Returns a single column as list (default) 
    or selected cols from table, 
    or entire dataframe from a table
    Can optionally set an index on the dataframe
    """
    conn = None
    try:
        conn = sq.connect(db_file)
        if verbose:
            print('Execute: ',c)
        if c != "":
            recs = conn.cursor().execute(c).fetchall()
            
            if single:
                records = []
                for r in recs:
                    records.append(r[0])
            else:
                
                records = pd.DataFrame(recs,columns=cols)
                if ind:
                    records = records.set_index(ind,True)
            return records
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]