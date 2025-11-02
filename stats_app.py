import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

import db_helper

st.set_page_config(page_title="Admin Stats", layout="centered",
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


# DB connect test button

if st.sidebar.button("Test DB connection"):
    ok = db_helper.test_connection()
    if ok:
        st.sidebar.success("DB connection OK")
    else:
        st.sidebar.error("DB connection failed - using mock data fallback")

# fallback data


def gen_ran_val(num_items: int = 300, year: int = datetime.now().year) -> pd.DataFrame:
    rng = np.random.default_rng(seed=123)
    categories = ["Electronics", "Clothing",
                  "Personal", "Miscellaneous", "Stationery"]
    statuses = ["Lost", "Found", "Claimed"]
    rows = []
    for i in range(1, num_items + 1):
        month = rng.integers(1, min(12, datetime.now().month) + 1)
        day = rng.integers(1, 28)
        dt = datetime(year, month, int(day), rng.integers(8, 18), 0, 0)
        status = rng.choice(statuses, p=[0.45, 0.45, 0.1])
        category = rng.choice(categories)
        rows.append({
            "ItemID": i,
            "UserID": int(rng.integers(1, 50)),
            "Title": f"Item {i}",
            "Description": f"Mock description {i}",
            "Category": category,
            "Location": f"Location {int(rng.integers(1,10))}",
            "DateTime": dt,
            "Status": status,
            "CreatedBy": "system"
        })
    return pd.DataFrame(rows)


def gen_ran_claims(items_df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(seed=999)
    claims = []
    claimable_items = items_df.sample(frac=0.2, random_state=42)
    claim_id = 1
    for _, row in claimable_items.iterrows():
        n_claims = rng.integers(0, 3)
        for _ in range(n_claims):
            status = rng.choice(
                ["Pending", "Approved", "Rejected"], p=[0.5, 0.3, 0.2])
            claims.append({
                "ClaimID": claim_id,
                "ItemID": int(row["ItemID"]),
                "UserID": int(rng.integers(1, 50)),
                "Status": status,
                "CreatedBy": f"user{int(rng.integers(1,50))}",
                "CreatedDate": row["DateTime"] + pd.Timedelta(days=int(rng.integers(0, 10))),
                "Reason": "Mock claim"
            })
            claim_id += 1
    return pd.DataFrame(claims)


# pulling from DB
@st.cache_data(ttl=300)
def load_items_from_db(start_dt, end_dt):

    sql = """
    SELECT ItemId, UserId, Title, LostDescription, Category, Location, DateLost, Status, CreatedBy, CreatedDate
    FROM Items
    WHERE DateLost BETWEEN ? AND ?
    """
    # fallback data for when DB fails
    fallback = gen_ran_val(300)
    return db_helper.query_to_df(sql, params=[start_dt, end_dt], fallback_df=fallback)


@st.cache_data(ttl=300)
def load_claims_from_db(start_dt, end_dt):
    # i took out status just after UserId
    sql = """
    SELECT ClaimId, ItemId, UserId, CreatedBy, CreatedDate, FoundDescription
    FROM Claims
    WHERE CreatedDate BETWEEN ? AND ?
    """
    fallback_items = gen_ran_val(300)
    fallback_claims = gen_ran_claims(fallback_items)
    return db_helper.query_to_df(sql, params=[start_dt, end_dt], fallback_df=fallback_claims)


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
for col in ["DateLost", "CreatedDate"]:
    if col in items_df.columns:
        items_df["DateLost"] = pd.to_datetime(
            items_df["DateLost"], errors="coerce")
    if col in claims_df.columns:
        claims_df["CreatedDate"] = pd.to_datetime(
            claims_df["CreatedDate"], errors="coerce")

# key points
total_lost = int((items_df["Status"] == "Lost").sum()
                 ) if "Status" in items_df else 0
total_found = int((items_df["Status"] == "Found").sum()
                  ) if "Status" in items_df else 0
total_claimed = int(
    (items_df["Status"] == "Claimed").sum()) if "Status" in items_df else 0

# recovery rate
recovery_rate = (total_claimed / total_lost * 100) if total_lost > 0 else 0.0

k1, k2, k3 = st.columns(3)
k1.metric("Total Lost Items", total_lost)
k2.metric("Total Found Items", total_found)
k3.metric("Recovery Rate (%)", f"{recovery_rate:.1f}%")

# category breakdown
if "Category" in items_df.columns:
    cat_counts = items_df.groupby("Category").size().reset_index(name="count")
    fig_pie = px.pie(cat_counts, names="Category",
                     values="count", title="Category Breakdown")
    st.plotly_chart(fig_pie, use_container_width=True)

# lost vs found per month
if "DateLost" in items_df.columns:
    df_month = items_df.copy()
    df_month["month"] = df_month["DateLost"].dt.to_period("M").astype(str)
    monthly = df_month.groupby(
        ["month", "Status"]).size().reset_index(name="count")
    # only need lost and found statuses
    monthly = monthly[monthly["Status"].isin(["Lost", "Found"])]
    if not monthly.empty:
        fig_bar = px.bar(monthly, x="month", y="count", color="Status", barmode="group",
                         title="Lost vs Found (per month)")
        st.plotly_chart(fig_bar, use_container_width=True)


# can remove all below
# Show simple data table preview
st.markdown("### Recent items (preview)")
st.dataframe(items_df.sort_values(by="DateLost", ascending=False).head(20))

st.markdown("### Recent claims (preview)")
st.dataframe(claims_df.sort_values(by="CreatedDate", ascending=False).head(20))
