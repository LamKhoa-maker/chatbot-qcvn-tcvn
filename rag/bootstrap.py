"""Bootstrap: raw .md -> clean -> chunks -> chroma.
Chay 1 lan khi app khoi dong neu collection dang rong
(de chay duoc ngay tren HuggingFace Spaces).
Bo qua neu collection da co du lieu, tru khi force=True.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def raw_files() -> list[Path]:
    files = list(BASE.glob("TCVN *.md")) + list(BASE.glob("QCVN *.md"))
    files += list((BASE / "data_goc").glob("*.md"))
    files += list((BASE / "data" / "raw").glob("*.md"))
    seen, out = set(), []
    for f in files:
        if f.name not in seen and f.is_file():
            seen.add(f.name)
            out.append(f)
    return sorted(out)


def collection_count() -> int:
    try:
        from rag.store import get_collection
        return get_collection().count()
    except Exception:
        return 0


def bootstrap(force: bool = False) -> dict:
    from rag.chunk import chunk_file
    from rag.normalize import normalize
    from rag.store import build_from_chunks

    if not force and collection_count() > 0:
        return {"status": "skip", "count": collection_count()}

    raws = raw_files()
    if not raws:
        return {"status": "empty", "count": 0}

    clean_dir = BASE / "data" / "clean"
    total = 0
    for raw in raws:
        clean = clean_dir / (raw.stem + ".clean.md")
        normalize(raw, clean, raw.stem)
        chunks_path = chunk_file(clean)
        total += build_from_chunks(chunks_path)
    return {"status": "built", "files": len(raws), "chunks": total}
