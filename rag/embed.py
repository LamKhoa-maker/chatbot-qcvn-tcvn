"""Embedding local free bang sentence-transformers.
Model mac dinh BAAI/bge-m3 (chat luong cao, can ~2GB RAM).
Tren Streamlit Cloud (RAM nho): dat EMBED_MODEL=intfloat/multilingual-e5-small.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

MODEL_NAME = os.getenv("EMBED_MODEL", "BAAI/bge-m3").strip() or "BAAI/bge-m3"

_model = None


def query_prefix() -> str:
    if "e5" in MODEL_NAME.lower():
        return "query: "
    return "Represent this sentence for searching relevant passages: "


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    vecs = model.encode(texts, batch_size=8, show_progress_bar=False, normalize_embeddings=True)
    return [v.tolist() for v in vecs]
