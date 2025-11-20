# utils/chat_engine.py
import os
import traceback
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from typing import Dict

# Initialize OpenAI model
llm = ChatOpenAI(
    model="gpt-4o-mini",  # or "gpt-4o" for higher quality
    temperature=0.3,
    max_tokens=512,
    api_key=os.getenv("OPENAI_API_KEY")
)

# In-memory chat history
store: Dict[str, ChatMessageHistory] = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Strategic, data-driven prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior ecommerce growth consultant for a Pakistani online store.
Use ONLY the KPI data below to answer questions. When asked about underperforming areas:
1. Identify the issue using specific data (e.g., "Zaida generated only ₨899")
2. Suggest 2–3 actionable, cost-effective recommendations (e.g., localized offers, bundling, ad reallocation)
3. Reference top performers (e.g., Karachi) if relevant

Be concise, practical, and data-driven. Avoid fluff.
"""),
    ("system", "KPI Summary:\n{data_context}"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

chain = prompt | llm
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

def answer_question(user_query: str, kpi_summary: dict, session_id: str = "default") -> str:
    try:
        # Truncate KPI context to stay within token limits
        shortened_kpi = str(kpi_summary)[:3500]
        response = chain_with_history.invoke(
            {
                "question": user_query,
                "data_context": shortened_kpi
            },
            config={"configurable": {"session_id": session_id}}
        )
        return response.content
    except Exception as e:
        error_msg = f"❌ OpenAI Error: {str(e)}"
        print("🔥 FULL ERROR:")
        traceback.print_exc()
        return error_msg