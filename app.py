"""Chatbot QCVN/TCVN - giao dien kieu Gemini (Streamlit).
Chay local:  streamlit run app.py
"""
import time

import streamlit as st

from rag.bootstrap import bootstrap
from rag.qa import FALLBACKS, answer

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
MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-lite-latest"]

with st.spinner("Đang chuẩn bị dữ liệu (lần đầu có thể mất vài phút)..."):
    info = bootstrap()
if info["status"] == "empty":
    st.error("Chưa có file .md nào trong repo. Hãy upload file QCVN/TCVN.")
    st.stop()

if "convs" not in st.session_state:
    st.session_state.convs = {}
    st.session_state.active = None
if "model" not in st.session_state:
    st.session_state.model = MODELS[0]


def new_chat() -> str:
    cid = f"c{int(time.time() * 1000)}"
    st.session_state.convs[cid] = {"title": "Đoạn chat mới", "messages": []}
    st.session_state.active = cid
    return cid


def cur():
    cid = st.session_state.active
    if cid not in st.session_state.convs:
        cid = new_chat()
    return st.session_state.convs[cid]


def ask(q: str, top_k: int) -> None:
    conv = cur()
    conv["messages"].append(("user", q))
    if conv["title"] == "Đoạn chat mới":
        conv["title"] = (q[:42] + "...") if len(q) > 42 else q
    with st.spinner("Đang tra cứu..."):
        res = answer(q, top_k=top_k, model=st.session_state.model)
    conv["messages"].append(("bot", res))


def export_md(conv) -> str:
    lines = [f"# {conv['title']}", ""]
    for role, msg in conv["messages"]:
        if role == "user":
            lines += [f"## 🙋 {msg}", ""]
        else:
            lines += [msg.get("answer") or "_Không có câu trả lời (xem căn cứ bên dưới)._", ""]
            if msg.get("model_used"):
                u = msg.get("usage") or {}
                lines += [f"*Model: {msg['model_used']}"
                          + (f" | token in/out: {u.get('in')}/{u.get('out')}" if u.get("in") else "")
                          + "*", ""]
            for i, h in enumerate(msg["hits"], 1):
                lines += [f"- [{i}] {h['ten_file']} — {h.get('muc_dau', h['muc'])} → {h['muc']}"]
            lines += [""]
    return "\n".join(lines)


with st.sidebar:
    st.header("💬 Lịch sử")
    if st.button("➕ Đoạn chat mới", use_container_width=True):
        new_chat()
        st.rerun()
    ids = list(st.session_state.convs.keys())
    if ids:
        labels = [st.session_state.convs[c]["title"] for c in ids]
        sel = st.selectbox("Chọn đoạn chat", range(len(ids)),
                           format_func=lambda i: labels[i],
                           index=ids.index(st.session_state.active) if st.session_state.active in ids else 0)
        st.session_state.active = ids[sel]
        conv = cur()
        st.download_button("⬇️ Tải đoạn chat (.md)", export_md(conv),
                           file_name="chat-qcvn-tcvn.md", use_container_width=True)
        if st.button("🗑️ Xóa đoạn chat này", use_container_width=True):
            del st.session_state.convs[st.session_state.active]
            st.session_state.active = None
            st.rerun()
    st.divider()
    st.header("⚙️ Cài đặt")
    st.session_state.model = st.selectbox("Model", MODELS, index=MODELS.index(st.session_state.model))
    st.caption(f"Tự fallback: {', '.join(FALLBACKS)}")
    top_k = st.slider("Số đoạn trích (top_k)", 3, 12, 8)
    st.caption("LLM: Gemini free-tier. Embedding: e5-small local.")

conv = cur()

if not conv["messages"]:
    st.markdown(
        '<div class="welcome"><h1>Xin chào, tôi là chuyên gia QCVN/TCVN</h1>'
        "<p>Hỏi tôi bất cứ gì về phòng cháy chữa cháy trong các tiêu chuẩn đã nạp</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, s in enumerate(SUGGESTIONS):
        if cols[i % 2].button(s, key=f"sug_{i}", use_container_width=True):
            ask(s, top_k)
            st.rerun()

q = st.chat_input("Hỏi về QCVN/TCVN...")
if q:
    ask(q, top_k)
    st.rerun()

for role, msg in conv["messages"]:
    with st.chat_message("user" if role == "user" else "assistant"):
        if role == "user":
            st.write(msg)
            continue
        if msg.get("warning"):
            st.warning(msg["warning"])
        if msg.get("answer"):
            st.markdown(msg["answer"])
            meta = []
            if msg.get("model_used"):
                meta.append(f"Model: `{msg['model_used']}`")
            u = msg.get("usage") or {}
            if u.get("in"):
                meta.append(f"token in/out: {u['in']}/{u['out']}")
            if meta:
                st.caption(" · ".join(meta))
        with st.expander("📎 Căn cứ trích dẫn"):
            for i, h in enumerate(msg["hits"], 1):
                st.markdown(f"**{i}. [{h['ten_file']}] {h.get('muc_dau', h['muc'])} → {h['muc']}**")
                st.write(h["text"][:1500])
