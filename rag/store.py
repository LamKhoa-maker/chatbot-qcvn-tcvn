"""ChromaDB persistent + truy van retrieval.
Luu tai ./chroma_db (them vao gitignore khi deploy).
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DB_DIR = BASE / "chroma_db"


def collection_name() -> str:
    from rag.embed import MODEL_NAME
    slug = re.sub(r"[^a-z0-9]+", "-", MODEL_NAME.lower()).strip("-")
    return f"qcvn_tcvn_{slug}"


COLLECTION = "qcvn_tcvn"  # giu de tuong thich nguoc, ten that tinh theo model


def get_collection():
    import chromadb
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_or_create_collection(name=collection_name(), metadata={"hnsw:space": "cosine"})


def build_from_chunks(chunks_path: Path) -> int:
    from rag.embed import embed_texts
    rows = [json.loads(l) for l in chunks_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    col = get_collection()
    try:
        col.delete(where={"ten_file": rows[0]["ten_file"]})
    except Exception:
        pass
    texts = [c["text"] for c in rows]
    vecs = embed_texts(texts)
    col.add(
        ids=[f"{rows[0]['ten_file']}#{c['chunk_id']}" for c in rows],
        documents=texts,
        metadatas=[{
            "ten_file": c["ten_file"],
            "muc": c["muc"],
            "muc_dau": c.get("muc_dau", c["muc"]),
            "mucs": " | ".join(c.get("mucs", [c["muc"]]))[:800],
            "chunk_id": c["chunk_id"],
        } for c in rows],
        embeddings=vecs,
    )
    return len(rows)


def search(query: str, top_k: int = 5) -> list[dict]:
    from rag.embed import embed_texts, query_prefix
    col = get_collection()
    qv = embed_texts([query_prefix() + query])[0]
    res = col.query(query_embeddings=[qv], n_results=top_k)
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        out.append({"ten_file": meta["ten_file"], "muc": meta["muc"],
                    "muc_dau": meta.get("muc_dau", meta["muc"]),
                    "mucs": meta.get("mucs", meta["muc"]),
                    "distance": dist, "text": doc})
    return out


if __name__ == "__main__":
    import sys
    chunks = BASE / "data" / "chunks" / "TCVN 7336-2021.chunks.jsonl"
    if len(sys.argv) > 1 and not sys.argv[1].startswith("?"):
        chunks = Path(sys.argv[1])
    n = build_from_chunks(chunks)
    print(f"OK: nap {n} chunks vao {DB_DIR}")
    for q in ["Chua chay tu dong la gi?", "Khoang cach dau phun voi tuong bao nhieu?"]:
        print(f"\n### Q: {q}")
        for r in search(q, top_k=3):
            print(f"- [{r['ten_file']} | {r['muc'][:60]} | d={r['distance']:.3f}] {r['text'][:150]}...".replace("\n", " "))
