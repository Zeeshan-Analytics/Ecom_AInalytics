# Home.py
import streamlit as st
import pandas as pd
import os
from utils.data_processor import process_data
# Add this temporarily to Home.py
import os
from dotenv import load_dotenv
load_dotenv()
print("HF Token loaded:", bool(os.getenv("HUGGINGFACE_API_TOKEN")))

st.set_page_config(page_title="EcomAI Analyst", layout="centered")
st.title("🛍️ EcomAI Analyst")
st.subheader("Upload your ecommerce data to unlock insights")

# Initialize session state
if "kpi_summary" not in st.session_state:
    st.session_state.kpi_summary = None
if "processed" not in st.session_state:
    st.session_state.processed = False

# File upload
col1, col2 = st.columns(2)
with col1:
    orders_file = st.file_uploader("Upload Orders CSV", type="csv")
with col2:
    adspend_file = st.file_uploader("Upload Ad Spend CSV", type="csv")

if st.button("🚀 Generate Dashboard & AI Insights", type="primary"):
    if not orders_file or not adspend_file:
        st.error("Please upload both files.")
    else:
        with st.spinner("Processing your data..."):
            try:
                orders_df = pd.read_csv(orders_file)
                adspend_df = pd.read_csv(adspend_file)
                kpi_summary, shipped_df, daily_df = process_data(orders_df, adspend_df)
                
                # Save to session state for other pages
                st.session_state.kpi_summary = kpi_summary
                st.session_state.shipped_df = shipped_df
                st.session_state.daily_df = daily_df
                st.session_state.processed = True
                
                st.success("✅ Ready! Go to **Dashboard** or **AI Chat** tabs above.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.info("After processing, use the sidebar to navigate to **Dashboard** or **AI Chat**.")