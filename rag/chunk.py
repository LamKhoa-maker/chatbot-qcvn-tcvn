"""Chunk file clean-v1 thanh doan 800-1000 tokens de embedding.
Quy tac:
- Khong cat giua bang markdown (khoi lien tuc cac dong bat dau bang '|').
- Moi chunk giu metadata {ten_file, muc} de trich nguon khi tra loi.
- Uoc luong: 1 token ~ 4 ky tu -> max_chars=3200 (~800 tokens), overlap=600.
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MAX_CHARS = 3200
OVERLAP_CHARS = 600

RE_HEADING = re.compile(r"^(#{1,4})\s+(.+)$")
RE_FRONTMATTER = re.compile(r'^ten_file:\s*"(.+)"\s*$')


def parse_blocks(lines: list[str]) -> tuple[str, list[dict]]:
    ten_file = "unknown"
    blocks: list[dict] = []
    cur_muc = "dau_file"
    buf_table: list[str] = []

    def flush_table():
        if buf_table:
            blocks.append({"type": "table", "muc": cur_muc, "text": "\n".join(buf_table)})
            buf_table.clear()

    in_frontmatter = False
    seen_frontmatter = False
    for ln in lines:
        s = ln.rstrip("\n")
        if s.strip() == "---" and not seen_frontmatter:
            # mo/dong frontmatter YAML o dau file
            if not in_frontmatter:
                in_frontmatter = True
            else:
                in_frontmatter = False
                seen_frontmatter = True
            continue
        if in_frontmatter:
            m_fm = RE_FRONTMATTER.match(s.strip())
            if m_fm:
                ten_file = m_fm.group(1)
            continue
        # bo dong ghi chu demo, tranh lam nhieu retrieval
        if "File clean demo" in s:
            continue
        if s.strip().startswith("|"):
            buf_table.append(s)
            continue
        flush_table()
        m_h = RE_HEADING.match(s.strip())
        if m_h:
            cur_muc = m_h.group(2).strip()
            blocks.append({"type": "heading", "muc": cur_muc, "text": s.strip()})
            continue
        if not s.strip():
            continue
        blocks.append({"type": "para", "muc": cur_muc, "text": s.strip()})
    flush_table()
    return ten_file, blocks


def build_chunks(ten_file: str, blocks: list[dict]) -> list[dict]:
    chunks: list[dict] = []
    cur_text: list[str] = []
    cur_len = 0
    cur_muc = blocks[0]["muc"] if blocks else "dau_file"
    cur_mucs: list[str] = []
    seen_mucs: set[str] = set()

    def push():
        nonlocal cur_text, cur_len, cur_muc, cur_mucs, seen_mucs
        if not cur_text:
            return
        text = "\n".join(cur_text).strip()
        if text:
            mucs = [m for m in cur_mucs if m]
            chunks.append({
                "ten_file": ten_file,
                "muc": mucs[-1] if mucs else cur_muc,
                "muc_dau": mucs[0] if mucs else cur_muc,
                "mucs": mucs,
                "chunk_id": len(chunks),
                "chars": len(text),
                "tokens_uoc_luong": len(text) // 4,
                "text": text,
            })
        # overlap: giu duoi chunk truoc lam mo dau chunk sau
        tail = text[-OVERLAP_CHARS:] if len(text) > OVERLAP_CHARS else ""
        cur_text = [tail] if tail else []
        cur_len = len(tail)
        cur_mucs = [cur_muc] if cur_muc else []
        seen_mucs = set(cur_mucs)

    for b in blocks:
        piece = b["text"]
        # bang qua dai (hiem): tach nguyen bang thanh 1 chunk rieng
        if b["type"] == "table" and len(piece) > MAX_CHARS:
            push()
            mucs = [m for m in cur_mucs if m] + ([b["muc"]] if b["muc"] not in cur_mucs else [])
            chunks.append({
                "ten_file": ten_file,
                "muc": b["muc"],
                "muc_dau": mucs[0] if mucs else b["muc"],
                "mucs": mucs,
                "chunk_id": len(chunks),
                "chars": len(piece),
                "tokens_uoc_luong": len(piece) // 4,
                "text": piece,
                "ghi_chu": "bang_dai_nguyen_khoi",
            })
            cur_text, cur_len = [], 0
            continue
        if cur_len + len(piece) + 1 > MAX_CHARS and cur_text:
            push()
        if b["type"] == "heading":
            cur_muc = b["muc"]
            if b["muc"] not in seen_mucs:
                seen_mucs.add(b["muc"])
                cur_mucs.append(b["muc"])
        cur_text.append(piece)
        cur_len += len(piece) + 1
    push()
    return chunks


def chunk_file(clean_path: Path) -> Path:
    lines = clean_path.read_text(encoding="utf-8").splitlines()
    ten_file, blocks = parse_blocks(lines)
    chunks = build_chunks(ten_file, blocks)
    out_dir = BASE / "data" / "chunks"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (clean_path.stem.replace(".clean", "") + ".chunks.jsonl")
    with out_path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return out_path


if __name__ == "__main__":
    target = BASE / "data" / "clean" / "TCVN 7336-2021.clean.md"
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    out = chunk_file(target)
    rows = out.read_text(encoding="utf-8").splitlines()
    print(f"OK: {out} | so_chunks={len(rows)}")
    for r in rows[:3]:
        c = json.loads(r)
        print(f"--- chunk {c['chunk_id']} | muc={c['muc'][:60]} | chars={c['chars']}")
        print(c["text"][:300].replace("\n", " "))
