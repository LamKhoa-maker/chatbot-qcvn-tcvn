from rag.qa import answer

QS = [
    "Khoảng cách giữa đầu phun với tường quy định thế nào?",
    "Cường độ phun tối thiểu cho nhóm nguy cơ cháy nhóm 2 là bao nhiêu?",
    "Trạm bơm chữa cháy phải đặt ở đâu?",
    "Tiêu chuẩn này không áp dụng cho trường hợp nào?",
]
for q in QS:
    r = answer(q, top_k=5)
    print("=" * 80)
    print("Q:", q)
    print(r["answer"])
    print()
