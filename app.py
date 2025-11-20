# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
from utils.data_processor import process_data
from utils.chat_engine import answer_question

load_dotenv()

# Page config
st.set_page_config(page_title="EcomAI Analyst", layout="wide")
st.title("EcomAI Analyst: Talk to Your Store Data")

# Initialize session state
if "kpi_summary" not in st.session_state:
    st.session_state.kpi_summary = None
if "processed" not in st.session_state:
    st.session_state.processed = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# === FILE UPLOAD ===
st.header("📤 Upload Your Data")
col1, col2 = st.columns(2)

with col1:
    orders_file = st.file_uploader("Upload Orders CSV", type="csv")
with col2:
    adspend_file = st.file_uploader("Upload Ad Spend CSV", type="csv")

if orders_file and adspend_file and not st.session_state.processed:
    with st.spinner("Processing your data..."):
        try:
            orders_df = pd.read_csv(orders_file)
            adspend_df = pd.read_csv(adspend_file)

            # Process data → returns kpi_summary + raw processed data
            kpi_summary, shipped_df, daily_df = process_data(orders_df, adspend_df)

            st.session_state.kpi_summary = kpi_summary
            st.session_state.shipped_df = shipped_df
            st.session_state.daily_df = daily_df
            st.session_state.processed = True
            st.success("✅ Data processed successfully!")
        except Exception as e:
            st.error(f"❌ Error processing files: {e}")
            st.stop()

# === DASHBOARD ===
if st.session_state.processed:
    kpi = st.session_state.kpi_summary

    st.header("📊 Executive Dashboard")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue (PKR)", f"₨{kpi['total_revenue']:,.0f}")
    col2.metric("Total Orders", kpi['total_orders'])
    col3.metric("AOV", f"₨{kpi['aov']:,.0f}")
    col4.metric("ROAS", f"{kpi['roas']}x")

    # Revenue by Category
    st.subheader("Revenue by Category")
    cat_df = pd.DataFrame(list(kpi['revenue_by_category'].items()), columns=["Category", "Revenue"])
    fig1 = px.bar(cat_df, x="Category", y="Revenue", color="Category")
    st.plotly_chart(fig1, use_container_width=True)

    # Revenue over time
    st.subheader("Daily Revenue Trend")
    daily_df = st.session_state.daily_df
    fig2 = px.line(daily_df, x="date", y="revenue", title="Daily Revenue")
    st.plotly_chart(fig2, use_container_width=True)

    # Ad Spend vs Revenue
    st.subheader("Ad Spend vs Revenue (Daily)")
    fig3 = px.scatter(daily_df, x="ad_spend", y="revenue", trendline="ols")
    st.plotly_chart(fig3, use_container_width=True)

    # === CHAT INTERFACE ===
    st.divider()
    st.header("💬 Ask Your Data")

    # Display chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # User input
    # Inside app.py, in the chat input section:
if prompt := st.chat_input("e.g., Which city brings most revenue?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Pass session_id = "default" (or user ID if multi-user later)
            response = answer_question(
                prompt,
                st.session_state.kpi_summary,
                session_id="default"
            )
        st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        
# === RESET BUTTON (for testing) ===
if st.session_state.processed:
    if st.button("🔄 Reset & Upload New Data"):
        st.session_state.processed = False
        st.session_state.kpi_summary = None
        st.session_state.messages = []
        st.rerun()