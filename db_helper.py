import pandas as pd
from sqlalchemy import create_engine
import urllib
import streamlit as st


def get_engine():
    secrets = st.secrets["azure_sql"]

    # streamlit works with secrets for connection details
    server_full = secrets["server"]
    host, port = server_full.split(",")
    database = secrets["database"]
    username = secrets["username"]
    password = secrets["password"]

    # build ODBC connection string
    odbc_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        f"Server={host},{port};"
        f"Database={database};"
        f"Uid={username};"
        f"Pwd={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    # URL encode and build SQLAlchemy engine
    conn_str = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc_str)}"
    return create_engine(conn_str)


def query_to_df(query, params=None):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return pd.DataFrame()


def test_connection():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


