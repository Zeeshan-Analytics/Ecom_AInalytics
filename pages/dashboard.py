# pages/1_📊_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📊 Executive Dashboard")

if "kpi_summary" not in st.session_state or not st.session_state.processed:
    st.warning("Please upload data on the Home page first.")
    st.stop()

kpi = st.session_state.kpi_summary

# === Core Metrics ===
st.header("🎯 Core Sales Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue (PKR)", f"₨{kpi['total_revenue']:,.0f}")
col2.metric("Total Orders", kpi['total_orders'])
col3.metric("AOV", f"₨{kpi['aov']:,.0f}")
col4.metric("Units Sold", kpi['total_units_sold'])

# === ROI Metrics ===
st.header("💰 Marketing & ROI")
col1, col2, col3 = st.columns(3)
col1.metric("Total Ad Spend", f"₨{kpi['total_ad_spend']:,.0f}")
col2.metric("ROAS", f"{kpi['roas']}x")
col3.metric("Cost Per Order", f"₨{kpi['cpo']:,.0f}")

# === Time Trends ===
st.header("📈 Time-Series Trends")
st.metric("Q2 vs Q1 Growth", f"{kpi['q2_vs_q1_growth_pct']:.1f}%")
st.metric("MoM Growth (Apr → May)", f"{kpi['mom_growth_apr_to_may_pct']:.1f}%")

# === Breakdowns ===
st.header("🔍 Performance Breakdowns")

tab1, tab2, tab3, tab4 = st.tabs(["By City", "By SKU", "By Category", "Order Status"])

with tab1:
    st.subheader("Top Cities")
    st.dataframe(pd.DataFrame(kpi['top_cities_by_revenue']))
    st.subheader("Underperforming Cities")
    st.dataframe(pd.DataFrame(kpi['bottom_cities_by_revenue']))

with tab2:
    st.subheader("Top SKUs")
    st.dataframe(pd.DataFrame(kpi['top_skus_by_revenue']))
    st.subheader("Lowest SKUs")
    st.dataframe(pd.DataFrame(kpi['bottom_skus_by_revenue']))

with tab3:
    cat_df = pd.DataFrame(list(kpi['revenue_by_category'].items()), columns=["Category", "Revenue"])
    fig = px.bar(cat_df, x="Category", y="Revenue")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    status_df = pd.DataFrame(list(kpi['order_status_distribution'].items()), columns=["Status", "Count"])
    fig2 = px.pie(status_df, names="Status", values="Count")
    st.plotly_chart(fig2, use_container_width=True)

# === Channel ROAS ===
st.header("📡 Channel Performance")
roas_df = pd.DataFrame(list(kpi['roas_by_source'].items()), columns=["Source", "ROAS"])
st.table(roas_df)