# shared db helper

import pyodbc
import pandas as pd
import traceback
import streamlit as st

# DB CONFIG
DB_CONFIG = {
    "server": "richfield.database.windows.net,1433",  # confirm later
    "database": "Richfield",                     # confirm later
    "username": "richfieldDev",                       # confirm later
    "password": "Rich@123",                           # confirm later
    "driver": "ODBC Driver 18 for SQL Server"
}


def get_connection():
    # create pyodbc connection

    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        "Encrypt=yes;TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=10)


def query_to_df(sql: str, params: list = None, fallback_df=None):
    # run  query and return pandas DataFrame.
    # if DB connection fails, return fallback_df
    # parameter placeholders '?' for pyodbc.

    try:
        conn = get_connection()
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        # debugging message
        st.error(
            "Database connection/query failed. Using fallback/mocked data if provided.")
        st.write("DB error:", str(e))
        st.write(traceback.format_exc())
        if fallback_df is not None:
            return fallback_df
        else:
            # if no fallback provided, return empty dataframe
            return pd.DataFrame()


def test_connection():
    # function to test connection
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception as e:
        st.error("Unable to connect to DB. Check DB_CONFIG in db_helper.py.")
        st.write(str(e))
        return False
