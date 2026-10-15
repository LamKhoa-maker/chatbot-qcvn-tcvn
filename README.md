# Chatbot QCVN/TCVN

Chuyen gia tra loi ve QCVN/TCVN xay dung - PCCC, kem trich dan den tung Muc/Dieu.
Free 100%: embedding local + Gemini API free-tier + host Streamlit Community Cloud.

## Chay local

```bash
pip install -r requirements.txt
cp .env.example .env   # dan GEMINI_API_KEY vao
streamlit run app.py
```

Lan chay dau tien tu dong: normalize `.md` -> chunk -> embedding -> ChromaDB.

## Deploy Streamlit Community Cloud

1. Push repo nay len GitHub (khong commit file `.env`, `chroma_db/`).
2. Vao https://share.streamlit.io -> New app -> chon repo/branch/`app.py` -> Deploy.
3. Vao **App settings -> Secrets**, them:

```toml
GEMINI_API_KEY = "paste-key-cua-ban"
EMBED_MODEL = "intfloat/multilingual-e5-small"
```

4. Mo URL app tren PC/iPhone de su dung.

## Them tai lieu moi

Copy file `.md` vao thu muc goc (canh `TCVN 7336-2021.md`), commit + push.
Lan khoi dong ke tiep app se tu nap file moi (can reboot app tren Cloud).
