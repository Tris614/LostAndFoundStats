from io import BytesIO
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import numpy as np

import db_helper

st.set_page_config(page_title="Admin Reports", layout="centered",
                   initial_sidebar_state="collapsed")

# css
st.markdown(
    """
    <style>
        /*hide streamlit options*/
        header[data-testid="stHeader"], #MainMenu, footer {
            display: none !important;
        }


        /*background*/
        [data-testid="stAppViewContainer"] {
            background-color: #F4F6FA !important;
        }

        /*header*/
        .custom-header {
            background-color: #1e3a8a;
            color: white;
            width: 100%;
            padding: 1.15rem 0;
            margin: 0;
            position: fixed; /* keeps it pinned at top */
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .header-inner {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 3rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-title {
            font-size: 1.75rem;
            font-weight: 550;
            line-height: 0.5;
        }

        .header-subtitle {
            font-size: 0.9rem;
            margin-top: 0.25rem;
            opacity: 0.9;
        }

        .nav-links {
            display: flex;
            gap: 2.5rem;
        }

        .nav-links a {
            color: white;
            text-decoration: none;
            font-size: 1.10rem;
            font-weight: 300;
        }

        /*buttons*/
        .stButton > button {
            background-color: #0B5FFF !important;
            color: white !important;
            border-radius: 6px !important;
            padding: 0.6rem 2.5rem !important;
            border: none !important;
            font-weight: 500 !important;
        }

        .stButton > button:hover {
            background-color: #004BCE !important;
        }

        .stDownloadButton > button {
            background-color: #28A745 !important;
            color: white !important;
            border-radius: 6px !important;
            padding: 0.6rem 2.5rem !important;
            border: none !important;
            font-weight: 500 !important;
        }

        .stDownloadButton > button:hover {
            background-color: #1E8E3E !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# html for header
st.markdown("""
<div class="custom-header">
    <div class="header-inner">
        <div>
            <div class="header-title">University Lost & Found</div>
            <div class="header-subtitle">Student & Lecturer Portal</div>
        </div>
        <div class="nav-links">
            <a href="#">Home</a>
            <a href="#">Report Lost Item</a>
            <a href="#">Report Found Item</a>
            <a href="#">System Administrator</a>
        </div>
    </div>
</div>
<div class="main-content">
""", unsafe_allow_html=True)

# main content
st.title("Admin Reports")
st.write("Select date range and type of report to pull")

today = datetime.now().date()
default_start = today - timedelta(days=90)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date", value=default_start)
with col2:
    end_date = st.date_input("End date", value=today)

report_type = st.selectbox("Type of report", options=[
                           "All", "Lost", "Found", "Claims"], index=0)


# convert datetimes to include EOD
start_dt = datetime.combine(start_date, datetime.min.time())
end_dt = datetime.combine(end_date, datetime.max.time())


# db queries fetching data

@st.cache_data(ttl=300)
def load_items(start_dt, end_dt):
    # removed imagepath after datelost
    sql = """
    SELECT ItemId, UserId, Title, LostDescription, Category, Location, DateLost, Status, CreatedBy, CreatedDate
    FROM Items
    WHERE DateLost BETWEEN ? AND ?
    ORDER BY DateLost DESC
    """

    return db_helper.query_to_df(sql, params=(start_dt, end_dt))


@st.cache_data(ttl=300)
def load_claims(start_dt, end_dt):
    # removed status after userId
    sql = """
    SELECT ClaimId, ItemId, UserId, CreatedBy, CreatedDate, FoundDescription
    FROM Claims
    WHERE CreatedDate BETWEEN ? AND ?
    ORDER BY CreatedDate DESC
    """
    return db_helper.query_to_df(sql, params=(start_dt, end_dt))


# date ranges
items_df = load_items(start_dt, end_dt)
claims_df = load_claims(start_dt, end_dt)


# convert dict of dfs to excel bytes
def to_excel_bytes(dfs: dict) -> bytes:
    buffer = BytesIO()
    # openpyxl
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            df_to_save = df.copy()

            # convert datetimes to string
            for col in df_to_save.select_dtypes(include=["datetime64[ns]"]).columns:
                df_to_save[col] = df_to_save[col].dt.strftime(
                    "%Y-%m-%d %H:%M:%S")
            df_to_save.to_excel(
                writer, sheet_name=sheet_name[:31], index=False)
    buffer.seek(0)
    return buffer.getvalue()


def prep_export(report_type: str, items_filtered):
    if report_type == "All":
        sheets = {
            "Lost Items": items_filtered[items_filtered["Status"] == 0].sort_values("DateLost"),
            "Found Items": items_filtered[items_filtered["Status"] == 1].sort_values("DateLost"),
            "Claims": items_filtered[items_filtered["Status"] == 2].sort_values("DateLost")
        }
    elif report_type == "Lost":
        sheets = {
            "Lost Items": items_filtered[items_filtered["Status"] == 0].sort_values("DateLost")}
    elif report_type == "Found":
        sheets = {
            "Found Items": items_filtered[items_filtered["Status"] == 1].sort_values("DateLost")}
    elif report_type == "Claims":
        sheets = {
            "Claims": items_filtered[items_filtered["Status"] == 2].sort_values("DateLost")}
    else:
        sheets = {}
    return sheets


# already filtered
items_filtered = items_df
claims_filtered = claims_df

today_str = datetime.now().strftime("%Y-%m-%d")
fin_file = f"LostAndFound_{report_type}_Report_{today_str}.xlsx"

if st.button("Generate Report"):
    sheets = prep_export(report_type, items_filtered)
    if not sheets or not any(len(df) > 0 for df in sheets.values()):
        st.warning("No data for type of report and date range.")
    else:
        excel_bytes = to_excel_bytes(sheets)
        st.success(f"Prepared {fin_file} download below.")
        st.download_button(
            label="Download Excel",
            data=excel_bytes,
            file_name=fin_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


