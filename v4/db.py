from sqlite3 import Error
import sqlite3 as sq
import pandas as pd


def conn_exec(db_file, c="", verbose=False):
    """create a database connection to a SQLite database and execute a command"""
    conn = None
    try:
        conn = sq.connect(db_file)
        if verbose:
            print("Execute: ", c)
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


def conn_insert_df(db_file, tblName, df, insertMode="replace"):
    """Inserts a dataframe into a SQLlite table."""
    conn = None
    try:
        conn = sq.connect(db_file)
        if insertMode == "replace":
            dd = f"Delete From " + tblName
            conn.cursor().execute(dd)
            conn.commit()

        df.to_sql(tblName, conn, if_exists="append", index=False)

    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def conn_update_const(db_file, tblName, columns, values):
    """Updates list of items that match a column in a table with the value of a constant.
    values is a list of lists. Each outer list contains an inner list of values for the record.
    """
    columns = ",".join(columns)
    conn = None
    try:
        conn = sq.connect(db_file)
        for v in values:
            v = ",".join(v)
            c = f"REPLACE INTO " + tblName + " (" + columns + ") VALUES('" + v + "'))"
            conn.cursor().execute(c)
        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def conn_read(db_file, c="", verbose=False, single=True, cols=None, ind=None):
    """Returns a single column as list (default)
    or selected cols from table,
    or entire dataframe from a table
    Can optionally set an index on the dataframe
    """
    conn = None
    try:
        conn = sq.connect(db_file)
        if verbose:
            print("Execute: ", c)
        if c != "":
            recs = conn.cursor().execute(c).fetchall()

            if single:
                records = []
                for r in recs:
                    records.append(r[0])
            else:

                records = pd.DataFrame(recs, columns=cols)
                if ind:
                    records = records.set_index(ind, True)
            return records
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
