from rag.store import search

QS = [
    "Chữa cháy tự động là gì? Định nghĩa 3.1",
    "Khoảng cách giữa đầu phun với tường không được vượt quá bao nhiêu?",
]
for q in QS:
    print("### Q:", q)
    for r in search(q, top_k=8)[:4]:
        print(f"- [{r['ten_file']} | {r['muc_dau'][:45]} -> {r['muc'][:45]} | d={r['distance']:.3f}]")
    print()
