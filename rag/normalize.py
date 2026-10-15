"""Normalize file .md QCVN/TCVN sang form clean-v1 de chunk + embedding.
Quy tac (theo plan rag-qcvn-tcvn.md):
1. Gi file goc nguyen, chi tao ban clean trong data/clean/.
2. Bo khoi MUC LUC (gay nhieu retrieval).
3. Chuan hoa heading theo so hieu Dieu/Muc, khong dua vao so dau #.
4. Giu nguyen bang |...| va cong thuc Phu luc, khong cat giua bang.
5. Gom cap '###### **3.1**' + '**Tieu de**' + 'dinh nghia' thanh 1 muc.
"""
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

TOC_START = "MỤC LỤC"
TOC_END = "Lời nói đầu"

RE_NUMBERED = re.compile(r"^#{1,6}\s*\*{0,2}\s*(\d+(?:\.\d+)*)\s*\*{0,2}\s*(.*)$")
RE_SPECIAL = re.compile(
    r"^#{1,6}\s*\*{0,2}\s*((?:Bảng\s+\d+.*|Phụ lục\s+[A-Z].*|Lời nói đầu"
    r"|THƯ MỤC.*|MỤC LỤC))",
    re.IGNORECASE,
)
RE_BARE_NUMBER = re.compile(r"^#{1,6}\s*\*{0,2}\s*(\d+(?:\.\d+)*)\s*\*{0,2}\s*$")
RE_BOLD_TITLE = re.compile(r"^\*{0,2}\s*(.+?)\s*\*{0,2}\s*$")


def clean_inline(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^#{1,6}\s*", "", s)
    s = s.replace("<u>", "").replace("</u>", "")
    s = s.replace("**", "").replace("__", "").strip()
    s = re.sub(r"\s{2,}", " ", s)
    s = s.replace("TCVN 7336 : 2021", "TCVN 7336:2021")
    return s.strip(" -–—:").strip()


def level_for_numbered(num: str) -> str:
    dots = num.count(".")
    if dots == 0:
        return "##"
    if dots == 1:
        return "###"
    return "####"


def normalize(src: Path, dst: Path, ten_file: str) -> dict:
    text = src.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    out: list[str] = []
    out.append("---")
    out.append(f'ten_file: "{ten_file}"')
    out.append('nguon: "TCVN 7336:2021"')
    out.append('dinh_dang: "clean-v1"')
    out.append("---")
    out.append("")
    out.append("# TCVN 7336:2021 - He thong chua chay tu dong bang nuoc, bot")
    out.append("")
    out.append("> File clean demo tu dong tao boi rag/normalize.py. File goc giu nguyen.")
    out.append("")

    in_toc = False
    skipped_toc = 0
    merged_terms = 0
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        s = raw.strip()

        # Bat dau / ket thuc khoi muc luc
        if TOC_START in s and s.startswith("#"):
            in_toc = True
            i += 1
            continue
        if in_toc:
            skipped_toc += 1
            # Chi ket thuc TOC khi gap heading Loi noi dau that su (bat dau bang #)
            if s.startswith("#") and TOC_END in s:
                in_toc = False
                # giu lai heading Loi noi dau dang chuan
                out.append("## Lời nói đầu")
                out.append("")
            i += 1
            continue
        # Bo dong muc luc roi rac con sot (toan dau .... + so trang)
        if re.search(r"\.{4,}\s*\d+\|?$", s):
            skipped_toc += 1
            i += 1
            continue

        if not s:
            if out and out[-1] != "":
                out.append("")
            i += 1
            continue

        # Giu nguyen bang markdown
        if s.startswith("|"):
            out.append(s)
            i += 1
            continue

        # Heading dac biet: Bang / Phu luc / Loi noi dau / Thu muc
        m_sp = RE_SPECIAL.match(s)
        if m_sp:
            title = clean_inline(m_sp.group(1))
            if "mục lục" in title.lower():
                i += 1
                continue
            out.append(f"## {title}")
            out.append("")
            i += 1
            continue

        # Truong hop tach: '###### **3.1**' o 1 dong, tieu de o dong sau
        m_bare = RE_BARE_NUMBER.match(s)
        if m_bare:
            num = m_bare.group(1)
            # nhin truoc 2 dong tiep theo tim tieu de + dinh nghia
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            title = ""
            if j < n:
                cand = clean_inline(lines[j].strip())
                # neu dong ke tiep khong phai heading so khac thi coi la tieu de
                if cand and not RE_NUMBERED.match(lines[j].strip()) and not RE_BARE_NUMBER.match(lines[j].strip()) and not cand.startswith("|"):
                    # loai tru CHU THICH / cau van dai: neu qua dai (>160 ky tu) thi khong phai title
                    if len(cand) <= 160:
                        title = cand
            lv = level_for_numbered(num)
            head = f"{lv} {num} {title}".strip()
            out.append(head)
            out.append("")
            merged_terms += 1
            i = j + 1 if title else i + 1
            continue

        # Heading danh so day du: '**5.1.4** ...' hoac '###### **1 Pham vi...**'
        # hoac '**6 He thong...**' khong co dau # (van la heading dieu lon)
        m_bold_num = re.match(r"^\*{0,2}\s*(\d+(?:\.\d+)*)\s+(.{3,160})\*{0,2}\s*$", s)
        if m_bold_num and not s.startswith("|") and not s.startswith(">"):
            num, rest = m_bold_num.group(1), clean_inline(m_bold_num.group(2))
            # chi nhan neu phan con lai ngan gon nhu tieu de dieu/muc
            if len(rest) <= 160 and not rest.endswith("."):
                lv = level_for_numbered(num)
                out.append(f"{lv} {num} {rest}".strip())
                out.append("")
                i += 1
                continue
            # neu la cau dai co dau cham cuoi cau -> van co the la Dieu 6/7/8/9
            if re.match(r"^[6-9]$", num):
                lv = level_for_numbered(num)
                out.append(f"{lv} {num} {rest}".strip())
                out.append("")
                i += 1
                continue

        m_num = RE_NUMBERED.match(s)
        if m_num:
            num, rest = m_num.group(1), clean_inline(m_num.group(2))
            lv = level_for_numbered(num)
            head = f"{lv} {num} {rest}".strip()
            out.append(head)
            out.append("")
            i += 1
            continue

        # CHU THICH -> blockquote de giu ngu canh
        if s.startswith("CHÚ THÍCH"):
            out.append(f"> {s}")
            i += 1
            continue

        # Dong tieu de thua: '# **<u>TCVN</u>**', '## **TCVN 7336 : 2021**' -> bo
        low = clean_inline(s).lower()
        if low in {"tcvn", "tcvn 7336:2021", "t i ê u c h u ẩ n q u ố c g i a"}:
            i += 1
            continue
        if low.startswith("t i ê u c h u") and "tcvn 7336" in low:
            i += 1
            continue
        if s.startswith("#") and "TCVN 7336" in s and len(clean_inline(s)) < 40:
            i += 1
            continue

        # Heading chung co dau # nhung con dinh ** -> chuan hoa sach
        if s.startswith("#"):
            hashes = re.match(r"^(#{1,6})", s).group(1)
            title = clean_inline(s)
            if title:
                out.append(f"{hashes} {title}")
                i += 1
                continue

        out.append(raw.rstrip())
        i += 1

    # Gon dong trang thua
    final: list[str] = []
    blank = False
    for ln in out:
        if not ln.strip():
            if not blank:
                final.append("")
            blank = True
        else:
            final.append(ln)
            blank = False

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(final) + "\n", encoding="utf-8")
    return {"skipped_toc": skipped_toc, "merged_terms": merged_terms, "lines_out": len(final)}


if __name__ == "__main__":
    raw = BASE / "TCVN 7336-2021.md"
    if len(sys.argv) > 1:
        raw = Path(sys.argv[1])
    ten = raw.stem
    clean = BASE / "data" / "clean" / (raw.stem + ".clean.md")
    stats = normalize(raw, clean, ten)
    print(f"OK: {clean} | {stats}")
