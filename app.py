"""Chatbot QCVN/TCVN - giao dien kieu Gemini (Streamlit).
Chay local:  streamlit run app.py
"""
import streamlit as st

from rag.bootstrap import bootstrap
from rag.qa import answer

st.set_page_config(page_title="Chatbot QCVN/TCVN", page_icon="🚒", layout="centered")

GEMINI_CSS = """
<style>
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 760px; padding-top: 3rem; }
.welcome { text-align: center; margin: 2.5rem 0 1.5rem; }
.welcome h1 {
  font-size: 2rem; font-weight: 500;
  background: linear-gradient(90deg, #1a73e8, #d96570);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.welcome p { color: #5f6368; }
div[data-testid="stChatMessage"] {
  background: #f0f4f9; border-radius: 18px; padding: 0.6rem 1rem; margin: 0.4rem 0;
}
div[data-testid="stChatMessage"][data-testid-user="user"] { background: #e8f0fe; }
div[data-testid="stExpander"] { border: 1px solid #e0e3e7; border-radius: 12px; }
footer { visibility: hidden; }
</style>
"""
st.markdown(GEMINI_CSS, unsafe_allow_html=True)

SUGGESTIONS = [
    "Chữa cháy tự động được định nghĩa thế nào?",
    "Khoảng cách giữa đầu phun với tường?",
    "Cường độ phun tối thiểu nhóm nguy cơ cháy nhóm 2?",
    "Trạm bơm chữa cháy phải đặt ở đâu?",
]

with st.spinner("Đang chuẩn bị dữ liệu (lần đầu có thể mất vài phút)..."):
    info = bootstrap()
if info["status"] == "empty":
    st.error("Chưa có file .md nào trong repo. Hãy upload file QCVN/TCVN.")
    st.stop()

with st.sidebar:
    st.header("⚙️ Cài đặt")
    top_k = st.slider("Số đoạn trích (top_k)", 3, 12, 8)
    st.caption("LLM: Gemini flash-lite (free-tier). Embedding: e5-small local.")

if "history" not in st.session_state:
    st.session_state.history = []


def ask(q: str) -> None:
    st.session_state.history.append(("user", q))
    with st.spinner("Đang tra cứu..."):
        res = answer(q, top_k=top_k)
    st.session_state.history.append(("bot", res))


if not st.session_state.history:
    st.markdown(
        '<div class="welcome"><h1>Xin chào, tôi là chuyên gia QCVN/TCVN</h1>'
        "<p>Hỏi tôi bất cứ gì về phòng cháy chữa cháy trong các tiêu chuẩn đã nạp</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, s in enumerate(SUGGESTIONS):
        if cols[i % 2].button(s, key=f"sug_{i}", use_container_width=True):
            ask(s)
            st.rerun()

q = st.chat_input("Hỏi về QCVN/TCVN...")
if q:
    ask(q)
    st.rerun()

for role, msg in st.session_state.history:
    with st.chat_message("user" if role == "user" else "assistant"):
        if role == "user":
            st.write(msg)
            continue
        if msg.get("warning"):
            st.warning(msg["warning"])
        if msg.get("answer"):
            st.markdown(msg["answer"])
        with st.expander("📎 Căn cứ trích dẫn"):
            for i, h in enumerate(msg["hits"], 1):
                st.markdown(f"**{i}. [{h['ten_file']}] {h.get('muc_dau', h['muc'])} → {h['muc']}**")
                st.write(h["text"][:1500])
