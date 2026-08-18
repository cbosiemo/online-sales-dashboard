"""
Online Sales Performance Dashboard
Built with Streamlit, Pandas and Plotly.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------------------------------------------------------
# Page configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Online Sales Performance Dashboard",
    page_icon="📊",
    layout="wide",
)

# -----------------------------------------------------------------------------
# Small amount of custom CSS for a cleaner presentation
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
        }
        [data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 12px;
            padding: 14px;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.18);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Load data
# -----------------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    """Load and prepare the sales dataset."""
    data_path = Path(__file__).parent / "Online_Sales_Data.csv"
    data = pd.read_csv(data_path)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.dropna(subset=["Date"])
    return data


df = load_data()

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.title("📊 Online Sales Performance Dashboard")
st.caption(
    "Interactive analysis of revenue, transactions, products, regions and payment methods."
)

# -----------------------------------------------------------------------------
# Sidebar filters
# -----------------------------------------------------------------------------
st.sidebar.header("Filter Data")
st.sidebar.caption("Use the filters below to explore different parts of the dataset.")

region_options = sorted(df["Region"].dropna().unique().tolist())
category_options = sorted(df["Product Category"].dropna().unique().tolist())
payment_options = sorted(df["Payment Method"].dropna().unique().tolist())

selected_regions = st.sidebar.multiselect(
    "Region",
    options=region_options,
    default=region_options,
)

selected_categories = st.sidebar.multiselect(
    "Product category",
    options=category_options,
    default=category_options,
)

selected_payments = st.sidebar.multiselect(
    "Payment method",
    options=payment_options,
    default=payment_options,
)

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
selected_dates = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

if st.sidebar.button("Reset filters", use_container_width=True):
    st.rerun()

# -----------------------------------------------------------------------------
# Apply filters
# -----------------------------------------------------------------------------
filtered_df = df[
    (df["Region"].isin(selected_regions))
    & (df["Product Category"].isin(selected_categories))
    & (df["Payment Method"].isin(selected_payments))
    & (df["Date"].dt.date >= start_date)
    & (df["Date"].dt.date <= end_date)
].copy()

if filtered_df.empty:
    st.warning("No records match the selected filters. Widen your selections and try again.")
    st.stop()

# -----------------------------------------------------------------------------
# KPI calculations
# -----------------------------------------------------------------------------
total_revenue = filtered_df["Total Revenue"].sum()
total_orders = filtered_df["Transaction ID"].nunique()
total_units = int(filtered_df["Units Sold"].sum())
avg_order_value = total_revenue / total_orders if total_orders else 0

product_revenue = (
    filtered_df.groupby("Product Name", as_index=False)["Total Revenue"]
    .sum()
    .sort_values("Total Revenue", ascending=False)
)
region_revenue = (
    filtered_df.groupby("Region", as_index=False)["Total Revenue"]
    .sum()
    .sort_values("Total Revenue", ascending=False)
)

top_product = product_revenue.iloc[0]["Product Name"] if not product_revenue.empty else "N/A"
top_region = region_revenue.iloc[0]["Region"] if not region_revenue.empty else "N/A"

# -----------------------------------------------------------------------------
# KPI row
# -----------------------------------------------------------------------------
metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("Total Revenue", f"${total_revenue:,.2f}")
metric2.metric("Transactions", f"{total_orders:,}")
metric3.metric("Units Sold", f"{total_units:,}")
metric4.metric("Average Order Value", f"${avg_order_value:,.2f}")

st.caption(f"Top product: **{top_product}**   |   Top region: **{top_region}**")
st.divider()

# -----------------------------------------------------------------------------
# Revenue trend and regional share
# -----------------------------------------------------------------------------
left, right = st.columns((1.7, 1))

with left:
    st.subheader("Revenue Trend")
    monthly_revenue = (
        filtered_df.assign(Month=filtered_df["Date"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", as_index=False)["Total Revenue"]
        .sum()
    )
    trend_fig = px.line(
        monthly_revenue,
        x="Month",
        y="Total Revenue",
        markers=True,
        labels={"Month": "Month", "Total Revenue": "Revenue ($)"},
    )
    trend_fig.update_traces(
        hovertemplate="%{x|%b %Y}<br>Revenue: $%{y:,.2f}<extra></extra>"
    )
    trend_fig.update_layout(margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(trend_fig, use_container_width=True)

with right:
    st.subheader("Revenue by Region")
    region_fig = px.pie(
        region_revenue,
        names="Region",
        values="Total Revenue",
        hole=0.5,
    )
    region_fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}<br>Revenue: $%{value:,.2f}<br>Share: %{percent}<extra></extra>",
    )
    region_fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(region_fig, use_container_width=True)

# -----------------------------------------------------------------------------
# Category and product performance
# -----------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Revenue by Product Category")
    category_revenue = (
        filtered_df.groupby("Product Category", as_index=False)["Total Revenue"]
        .sum()
        .sort_values("Total Revenue", ascending=True)
    )
    category_fig = px.bar(
        category_revenue,
        x="Total Revenue",
        y="Product Category",
        orientation="h",
        text="Total Revenue",
        labels={"Total Revenue": "Revenue ($)", "Product Category": "Category"},
    )
    category_fig.update_traces(
        texttemplate="$%{text:,.0f}",
        textposition="outside",
        hovertemplate="%{y}<br>Revenue: $%{x:,.2f}<extra></extra>",
    )
    category_fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=40, t=20, b=10),
    )
    st.plotly_chart(category_fig, use_container_width=True)

with right:
    st.subheader("Top 10 Products by Revenue")
    top_products = product_revenue.head(10).sort_values("Total Revenue", ascending=True)
    product_fig = px.bar(
        top_products,
        x="Total Revenue",
        y="Product Name",
        orientation="h",
        labels={"Total Revenue": "Revenue ($)", "Product Name": "Product"},
    )
    product_fig.update_traces(
        hovertemplate="%{y}<br>Revenue: $%{x:,.2f}<extra></extra>"
    )
    product_fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(product_fig, use_container_width=True)

# -----------------------------------------------------------------------------
# Payment methods and regional performance table
# -----------------------------------------------------------------------------
left, right = st.columns((1, 1.25))

with left:
    st.subheader("Revenue by Payment Method")
    payment_revenue = (
        filtered_df.groupby("Payment Method", as_index=False)["Total Revenue"]
        .sum()
        .sort_values("Total Revenue", ascending=False)
    )
    payment_fig = px.bar(
        payment_revenue,
        x="Payment Method",
        y="Total Revenue",
        text="Total Revenue",
        labels={"Total Revenue": "Revenue ($)", "Payment Method": "Payment method"},
    )
    payment_fig.update_traces(
        texttemplate="$%{text:,.0f}",
        textposition="outside",
        hovertemplate="%{x}<br>Revenue: $%{y:,.2f}<extra></extra>",
    )
    payment_fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(payment_fig, use_container_width=True)

with right:
    st.subheader("Regional Performance")
    regional_summary = (
        filtered_df.groupby("Region")
        .agg(
            Revenue=("Total Revenue", "sum"),
            Transactions=("Transaction ID", "nunique"),
            Units_Sold=("Units Sold", "sum"),
        )
        .reset_index()
    )
    regional_summary["Average_Order_Value"] = (
        regional_summary["Revenue"] / regional_summary["Transactions"]
    )
    regional_summary = regional_summary.sort_values("Revenue", ascending=False)

    st.dataframe(
        regional_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Region": "Region",
            "Revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
            "Transactions": st.column_config.NumberColumn("Transactions", format="%d"),
            "Units_Sold": st.column_config.NumberColumn("Units Sold", format="%d"),
            "Average_Order_Value": st.column_config.NumberColumn(
                "Avg. Order Value", format="$%.2f"
            ),
        },
    )

# -----------------------------------------------------------------------------
# Detailed data
# -----------------------------------------------------------------------------
st.divider()
st.subheader("Transaction Details")
st.caption(f"Showing {len(filtered_df):,} filtered records.")

with st.expander("View filtered transaction data"):
    display_df = filtered_df.sort_values("Date", ascending=False).copy()
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "Unit Price": st.column_config.NumberColumn("Unit Price", format="$%.2f"),
            "Total Revenue": st.column_config.NumberColumn("Total Revenue", format="$%.2f"),
        },
    )

    st.download_button(
        "Download filtered data as CSV",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_online_sales_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.caption("Built with Python, Streamlit, Pandas and Plotly.")
