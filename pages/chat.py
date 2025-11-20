# pages/2_🤖_AI_Chat.py
import streamlit as st
from utils.chat_engine import answer_question
from utils.email_sender import send_email_report
import json

st.title("🤖 Chat with Your Data")

# Guard: ensure data is loaded
if "kpi_summary" not in st.session_state or not st.session_state.processed:
    st.warning("Please upload data on the Home page first.")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
if prompt := st.chat_input("Ask strategic questions (e.g., 'How to grow revenue in Zaida?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = answer_question(prompt, st.session_state.kpi_summary, session_id="default")
        st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# === EMAIL BUTTON ===
st.divider()
if st.button("📧 Email Chat Summary", type="secondary"):
    if not st.session_state.messages:
        st.warning("No conversation to email.")
    else:
        with st.spinner("Sending email..."):
            # Build full report
            chat_text = "\n".join([
                f"**{m['role'].title()}**: {m['content']}"
                for m in st.session_state.messages
            ])
            kpi_summary_str = json.dumps(st.session_state.kpi_summary, indent=2)
            full_report = f"""
**EcomAI Analyst Report**

**KPI Summary**:
{kpi_summary_str}

**Conversation**:
{chat_text}
            """
            try:
                send_email_report(full_report)
                st.success("✅ Report sent to your email!")
            except Exception as e:
                st.error(f"❌ Failed to send email: {e}")

st.info("💡 Try: _'Suggest ways to boost sales in Zaida and Batkhela'_ or _'Which products should I bundle?'_")