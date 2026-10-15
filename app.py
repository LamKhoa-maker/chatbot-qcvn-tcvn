"""Chatbot QCVN/TCVN - Streamlit (free 100%).
Chay local:  streamlit run app.py
"""
import streamlit as st

from rag.bootstrap import bootstrap
from rag.qa import answer

st.set_page_config(page_title="Chatbot QCVN/TCVN", layout="wide")
st.title("Chatbot QCVN/TCVN - Chuyen gia PCCC")

with st.spinner("Dang chuan bi du lieu (lan dau co the mat vai phut)..."):
    info = bootstrap()
if info["status"] == "empty":
    st.error("Chua co file .md nao trong data. Hay upload file QCVN/TCVN vao repo.")
    st.stop()

with st.sidebar:
    st.header("Cai dat")
    top_k = st.slider("So doan trich (top_k)", 3, 12, 8)
    st.caption("LLM: Gemini flash-lite (free-tier). Embedding: bge-m3 local.")

if "history" not in st.session_state:
    st.session_state.history = []

q = st.chat_input("Hoi ve QCVN/TCVN, vd: Khoang cach dau phun voi tuong bao nhieu?")
if q:
    st.session_state.history.append(("user", q))
    with st.spinner("Dang tra cuu..."):
        res = answer(q, top_k=top_k)
    st.session_state.history.append(("bot", res))

for role, msg in st.session_state.history:
    with st.chat_message("user" if role == "user" else "assistant"):
        if role == "user":
            st.write(msg)
            continue
        if msg.get("warning"):
            st.warning(msg["warning"])
        if msg.get("answer"):
            st.markdown(msg["answer"])
        st.subheader("Can cu trich dan")
        for i, h in enumerate(msg["hits"], 1):
            with st.expander(f"{i}. [{h['ten_file']}] {h.get('muc_dau', h['muc'])} -> {h['muc']}"):
                st.write(h["text"][:2000])
