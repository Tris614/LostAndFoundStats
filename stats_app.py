import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import streamlit as st

import db_helper

st.set_page_config(page_title="Admin Stats", layout="centered",
                   initial_sidebar_state="collapsed")

# css
st.markdown(
    """
    <style>
        /*hiding streamlit options*/
        header[data-testid="stHeader"], #MainMenu, footer {
            display: none !important;
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

        .sys-label {
            display: flex;
            gap: 2.5rem;
        }

        .sys-label a {
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
        <div class="sys-label">
            <a>System Administrator</a>
        </div>
    </div>
</div>
<div class="main-content">
""", unsafe_allow_html=True)

# pulling from DB

@st.cache_data(ttl=300)
def load_items_from_db(start_dt, end_dt):

    sql = """
    SELECT ItemId, UserId, Title, LostDescription, Category, Location, DateLost, Status, CreatedBy, CreatedDate
    FROM Items
    WHERE CreatedDate BETWEEN ? AND ?
    """

    return db_helper.query_to_df(sql, params=(start_dt, end_dt))


@st.cache_data(ttl=300)
def load_claims_from_db(start_dt, end_dt):
    # i took out status just after UserId
    sql = """
    SELECT ClaimId, ItemId, UserId, CreatedBy, CreatedDate, FoundDescription
    FROM Claims
    WHERE CreatedDate BETWEEN ? AND ?
    """
    return db_helper.query_to_df(sql, params=(start_dt, end_dt))


# UI
st.title("Admin Stats")
st.write("Statistics and KPIs for Lost & Found")

today = datetime.now().date()
default_start = today - timedelta(days=90)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date", value=default_start)
with col2:
    end_date = st.date_input("End date", value=today)

# change date to datetimes with full day
start_dt = datetime.combine(start_date, datetime.min.time())
end_dt = datetime.combine(end_date, datetime.max.time())

# load data
items_df = load_items_from_db(start_dt, end_dt)
claims_df = load_claims_from_db(start_dt, end_dt)

# validate datetimes columns
for df in [items_df, claims_df]:
    if "CreatedDate" in df.columns:
        df["CreatedDate"] = pd.to_datetime(df["CreatedDate"], errors="coerce")


# calc key points indicators
total_lost = int((items_df["Status"] == 0).sum()
                 ) if "Status" in items_df else 0
total_found = int((items_df["Status"] == 1).sum()
                  ) if "Status" in items_df else 0
total_claimed = int(
    (items_df["Status"] == 2).sum()) if "Status" in items_df else 0

# work out recovery rate
recovery_rate = (total_claimed / total_lost * 100) if total_lost > 0 else 0.0

k1, k2, k3 = st.columns(3)
k1.metric("Total Lost Items", total_lost)
k2.metric("Total Found Items", total_found)
k3.metric("Recovery Rate (%)", f"{recovery_rate:.1f}%")

# category breakdown pie
if "Category" in items_df.columns:
    cat_counts = items_df.groupby("Category").size().reset_index(name="count")
    fig_pie = px.pie(cat_counts, names="Category",
                     values="count", title="Category Breakdown")
    st.plotly_chart(fig_pie, use_container_width=True)

# lost vs found per month
if "CreatedDate" in items_df.columns and "Status" in items_df.columns:
    df_month = items_df.copy()
    df_month["month"] = df_month["CreatedDate"].dt.to_period("M").astype(str)

    # Map numeric status codes to readable labels
    status_map = {0: "Lost", 1: "Found", 2: "Claimed"}
    df_month["StatusLabel"] = df_month["Status"].map(status_map)

    # Group and aggregate
    monthly = df_month.groupby(
        ["month", "StatusLabel"]).size().reset_index(name="count")

    # Filter only Lost/Found
    monthly = monthly[monthly["StatusLabel"].isin(["Lost", "Found"])]

    if not monthly.empty:
        fig_bar = px.bar(
            monthly,
            x="month",
            y="count",
            color="StatusLabel",
            barmode="group",
            title="Lost vs Found (per month)",
            color_discrete_map={"Lost":"#eeb434",
            "Found":"#0053ff"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No Lost or Found items found for the selected period.")


