"""Steps 1 and 8: the chat screen (Streamlit). Run the backend first."""
import os

import pandas as pd
import requests
import streamlit as st

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Chat with Your Data", page_icon="💬")
st.title("💬 Chat with Your Data")

try:
    health = requests.get(f"{BACKEND}/health", timeout=5).json()
    st.caption(f"Backend connected · mode: {health['mode']}")
except requests.RequestException:
    st.error("Backend is not running. Start it with: uvicorn backend.main:app --reload")
    st.stop()

with st.sidebar:
    st.subheader("Database tables")
    st.code(requests.get(f"{BACKEND}/schema", timeout=5).json()["schema"])
    st.caption("Try: 'top products by revenue', 'revenue by month', 'sales by region'")

if "messages" not in st.session_state:
    st.session_state.messages = []


def show(msg: dict):
    st.write(msg["summary"])
    df = pd.DataFrame(msg["rows"], columns=msg["columns"])
    chart = msg.get("chart")
    if chart:
        data = df.set_index(chart["x"])[chart["y"]]
        (st.line_chart if chart["type"] == "line" else st.bar_chart)(data)
    st.dataframe(df, use_container_width=True)
    with st.expander("Show the generated SQL"):
        st.code(msg["sql"], language="sql")


for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"]) if m["role"] == "user" else show(m["content"])

if question := st.chat_input("Ask a question about the data..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        resp = requests.post(f"{BACKEND}/ask", json={"question": question}, timeout=60)
        if resp.ok:
            data = resp.json()
            show(data)
            st.session_state.messages.append({"role": "assistant", "content": data})
        else:
            st.error(resp.json().get("detail", "Something went wrong."))
