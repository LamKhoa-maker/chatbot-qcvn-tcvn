from rag.qa import answer

r = answer("Chữa cháy tự động được định nghĩa như thế nào trong TCVN 7336?", top_k=5)
print("WARNING:", r["warning"])
print("ANSWER:")
print(r["answer"])
print()
for h in r["hits"][:3]:
    print(f"- [{h['ten_file']} | {h.get('muc_dau', h['muc'])[:50]} -> {h['muc'][:50]}]")
