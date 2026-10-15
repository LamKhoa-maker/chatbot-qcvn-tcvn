"""QA: retrieval tu Chroma + tra loi bang Gemini 2.5 Flash (free-tier).
Neu chua co GEMINI_API_KEY: tra ve che do retrieval-only de test.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

MODEL = "gemini-3.5-flash-lite"

# Thu tu fallback khi model chinh het quota/quata tai (503/429) hoac 404.
FALLBACKS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-flash-lite-latest"]

SYSTEM = """Ban la chuyen gia ve QCVN/TCVN xay dung - PCCC.
Chi tra loi DUA TREN doan trich dan duoc cung cap.
Cau truc tra loi:
1. Tra loi truc tiep, ngan gon.
2. Can cu: trich nguyen van trong dau > va ghi ro [Nguon: ten_file, Muc X].
3. Neu thong tin khong co trong doan trich: noi ro khong tim thay, khong bia.
4. Goi y muc lien quan neu co.
Viet tieng Viet, don vi giu nguyen nhu van ban goc."""


def build_prompt(question: str, hits: list[dict]) -> str:
    ctx = []
    for i, h in enumerate(hits, 1):
        ctx.append(
            f"[Doan {i} | {h['ten_file']} | {h.get('muc_dau', h['muc'])} -> {h['muc']}]\n{h['text']}"
        )
    return f"{SYSTEM}\n\nCau hoi: {question}\n\nCac doan trich:\n" + "\n\n".join(ctx)


def answer(question: str, top_k: int = 8, model: str | None = None) -> dict:
    from rag.store import search
    hits = search(question, top_k=top_k)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return {
            "answer": None,
            "hits": hits,
            "model_used": None,
            "usage": None,
            "warning": "Chua co GEMINI_API_KEY (lay free tai Google AI Studio, bo vao file .env). Dang hien retrieval-only.",
        }
    from google import genai
    client = genai.Client(api_key=key)
    tried: list[str] = []
    for cand in dict.fromkeys([model or MODEL, *FALLBACKS]):
        tried.append(cand)
        try:
            resp = client.models.generate_content(
                model=cand, contents=build_prompt(question, hits)
            )
            usage = getattr(resp, "usage_metadata", None)
            return {
                "answer": resp.text,
                "hits": hits,
                "model_used": cand,
                "usage": {
                    "in": getattr(usage, "prompt_token_count", None),
                    "out": getattr(usage, "candidates_token_count", None),
                } if usage else None,
                "warning": (
                    f"Model {tried[0]} ban, da tu chuyen sang {cand}."
                    if len(tried) > 1 else None
                ),
            }
        except Exception as e:
            last_err = f"{cand}: {e}"
            continue
    return {
        "answer": None,
        "hits": hits,
        "model_used": None,
        "usage": None,
        "warning": f"Tat ca model deu loi (da thu: {', '.join(tried)}). Loi cuoi: {last_err}. Hay doi vai phut.",
    }
