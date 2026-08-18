"""
Interactive Sales Dashboard
Built with Streamlit + Plotly

Run with:
    streamlit run dashboard.py

Make sure Online_Sales_Data.csv is in the same folder as this file.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Sales Dashboard", page_icon="📊", layout="wide")

st.header("📈 Interactive Sales Dashboard")
st.caption("Explore, filter, and analyze online sales performance.")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Online_Sales_Data.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    return df

df = load_data()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("🔍 Filter Data")

region_filter = st.sidebar.multiselect(
    "Select Region(s)",
    options=df["Region"].unique(),
    default=df["Region"].unique(),
)

product_filter = st.sidebar.multiselect(
    "Select Product Category(s)",
    options=df["Product Category"].unique(),
    default=df["Product Category"].unique(),
)

payment_filter = st.sidebar.multiselect(
    "Select Payment Method(s)",
    options=df["Payment Method"].unique(),
    default=df["Payment Method"].unique(),
)

min_date, max_date = df["Date"].min(), df["Date"].max()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Guard against a partial date selection while the user is still picking
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
filtered_df = df[
    (df["Region"].isin(region_filter))
    & (df["Product Category"].isin(product_filter))
    & (df["Payment Method"].isin(payment_filter))
    & (df["Date"] >= pd.to_datetime(start_date))
    & (df["Date"] <= pd.to_datetime(end_date))
]

if filtered_df.empty:
    st.warning("No data matches the selected filters. Try widening your selection.")
    st.stop()

# ---------------------------------------------------------------------------
# Key metrics
# ---------------------------------------------------------------------------
st.markdown(
    f"##### Region(s): {', '.join(region_filter) if region_filter else 'None'}  \n"
    f"##### Product(s): {', '.join(product_filter) if product_filter else 'None'}"
)

col1, col2, col3, col4 = st.columns(4)

total_revenue = filtered_df["Total Revenue"].sum()
avg_revenue = filtered_df["Total Revenue"].mean()
total_units = filtered_df["Units Sold"].sum()
total_orders = filtered_df["Transaction ID"].nunique()

col1.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
col2.metric("📊 Average Revenue", f"${avg_revenue:,.2f}")
col3.metric("📦 Units Sold", f"{total_units:,}")
col4.metric("🧾 Transactions", f"{total_orders:,}")

st.divider()

# ---------------------------------------------------------------------------
# Tabs with charts
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["🛍️ Sales by Product", "🌍 Sales by Region", "📅 Sales Trend", "💳 Payment Methods"]
)

with tab1:
    st.subheader("Sales by Product Category")
    product_data = filtered_df.groupby("Product Category")["Total Revenue"].sum().reset_index()
    fig1 = px.bar(
        product_data,
        x="Product Category",
        y="Total Revenue",
        color="Product Category",
        text="Total Revenue",
    )
    fig1.update_traces(texttemplate="$%{text:,.2f}", textposition="outside")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("Sales by Region")
    region_data = filtered_df.groupby("Region")["Total Revenue"].sum().reset_index()
    fig2 = px.pie(
        region_data,
        names="Region",
        values="Total Revenue",
        title="Revenue Share by Region",
        hole=0.35,
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Revenue Trend Over Time")
    trend_data = (
        filtered_df.set_index("Date")
        .resample("D")["Total Revenue"]
        .sum()
        .reset_index()
    )
    fig3 = px.line(trend_data, x="Date", y="Total Revenue", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.subheader("Revenue by Payment Method")
    payment_data = filtered_df.groupby("Payment Method")["Total Revenue"].sum().reset_index()
    fig4 = px.bar(
        payment_data,
        x="Payment Method",
        y="Total Revenue",
        color="Payment Method",
        text="Total Revenue",
    )
    fig4.update_traces(texttemplate="$%{text:,.2f}", textposition="outside")
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Raw data view
# ---------------------------------------------------------------------------
with st.expander("🔎 View filtered raw data"):
    st.dataframe(filtered_df, use_container_width=True)
    st.download_button(
        "Download filtered data as CSV",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_sales_data.csv",
        mime="text/csv",
    )
