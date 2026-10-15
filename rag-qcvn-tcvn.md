# Plan: Chatbot QCVN/TCVN (.md) — Free 100%

## 1. Mục tiêu
- Import ~10 file .md (lớn nhất QCVN 06:2022 ~570KB, đã kiểm tra mẫu TCVN 7336-2021.md 116KB/786 dòng).
- Hỏi đáp tiếng Việt, tổng hợp từ TẤT CẢ file (không so sánh, các quy chuẩn không trồng chéo).
- Dùng được trên PC + iPhone/tablet khi đi họp qua URL web.
- Chi phí 0đ: dùng free-tier + host free.

## 2. Phân tích file mẫu TCVN 7336-2021.md
- Cấu trúc tốt: `1 Phạm vi`, `2 Viện dẫn`, `3.1...3.19 Thuật ngữ`, `4,5,6,7,8,9`, `Phụ lục A/B/C`.
- Vấn đề phát hiện:
  1. Mọi heading đều là `######` -> không chunk theo `#` được. Phải chunk theo regex số hiệu.
  2. Dòng 19-34 là Mục lục (toàn số trang) -> phải loại khi index để tránh nhiễu retrieval.
  3. Nhiều bảng `|...|` và công thức Phụ lục B/C -> rule không cắt giữa bảng.
- Kết luận: plan RAG chuẩn vẫn phù hợp, chỉ cần custom `normalize + chunk` riêng cho QCVN/TCVN.

## 3. Kiến trúc chốt (Free)
```
.md gốc -> normalize.py -> chunks (800-1000 tokens, overlap 150, không cắt bảng)
  -> embedding local bge-m3 (free, chạy 1 lần trên PC)
  -> ChromaDB persistent local
  -> Retriever (top 8, filter theo ten_file khi cần)
  -> LLM Gemini 2.5 Flash free-tier (Google AI Studio), dự phòng Groq Llama 3.3 free
  -> Trả lời + trích nguồn
  -> UI Streamlit -> deploy HuggingFace Spaces / Streamlit Cloud (free, có URL mobile)
```

- Vì sao không offline 100% (Ollama): PC phải khỏe (16GB RAM+GPU), tiếng Việt kém hơn, và khó mở trên iPhone khi đi họp nếu không dựng server + Tailscale.
- Vì sao free-tier đủ: tổng ~3-4MB text -> ~3000-4000 chunks, query nhẹ, nằm trong quota free Gemini/Groq.

## 4. Chuẩn normalize .md (để implement ở Build mode — KHÔNG sửa file gốc)
File gốc giữ nguyên. Pipeline sẽ tạo bản `clean` trong bộ nhớ / thư mục `data/clean/`:
1. Bỏ khối Mục lục (dòng chứa `.... 4|` + `Lời nói đầu ...`).
2. Chuẩn hóa heading thành form:
```md
# TCVN 7336:2021 — Hệ thống chữa cháy tự động bằng nước, bọt
## 1 Phạm vi áp dụng
### 1.1 ...
## 3 Các thuật ngữ và định nghĩa
### 3.1 Chữa cháy tự động (Automatic extinguishing)
> Tự động kích hoạt các thiết bị chữa cháy mà không cần sự can thiệp của con người.
```
3. Bảng giữ nguyên khối `|...|`, công thức Phụ lục giữ nguyên dòng, thêm metadata:
`{ten_file: "TCVN 7336-2021", muc: "3.1", loai: "dinh_nghia"}`.
4. Ví dụ demo (mô tả, chưa sửa file thật do đang ở Plan mode):
   - Gốc dòng 88-92: `###### **3.1** + **Chữa cháy tự động...** + câu định nghĩa rời rạc`
   - Sau normalize: `### 3.1 Chữa cháy tự động` + quote định nghĩa + metadata trên.

## 5. Format câu trả lời
1. Trả lời trực tiếp, ngắn gọn.
2. Căn cứ: quote nguyên văn `> ...` + `[Nguồn: TCVN 7336-2021, Mục 5.x]`.
3. Nếu không tìm thấy: trả `Không có trong tài liệu đã nạp`, không bịa.
4. Gợi ý mục liên quan.

## 6. Cấu trúc project dự kiến (Build mode)
```
RAG_Project/
  data/raw/*.md
  data/clean/*.md (auto-gen)
  app.py (Streamlit)
  rag/chunk.py, rag/embed.py, rag/store.py, rag/qa.py
  requirements.txt
  .env (GEMINI_API_KEY)
```

## 7. Steps tiếp theo (khi switch sang Build)
1. Viết `normalize.py` + test trên TCVN 7336-2021.md.
2. Chạy embedding bge-m3 + build Chroma.
3. Viết `app.py` hỏi đáp + trích nguồn.
4. Test 3-5 câu hỏi thật.
5. Deploy HF Spaces để lấy URL mobile.

## 8. Rủi ro free-tier
- Giới hạn 15-50 req/phút, hết quota khi họp sẽ chậm -> mitigation: cache câu hỏi hay gặp, fallback Groq.
- Cần internet. Nếu mất mạng họp thì không dùng được (trade-off của mobile).

## 9. Backlog (chờ test thêm)
- **D. Chế độ "chỉ trích nguyên văn":** tắt phần diễn giải của AI, chỉ trả quote + nguồn.
  Dùng khi cần căn cứ pháp lý chính xác khi họp.
- **C. Lưu lịch sử vĩnh viễn:** database free (Supabase) để mở iPhone/PC đều thấy lại
  chat cũ. Rename + xóa đã có sẵn ở bản hiện tại (sidebar).
- Quy trình file: gốc (.md ban đầu) để ở `data_goc/` -> clean từng file khi yêu cầu
  -> bản clean vào `data/clean/` (thư mục dữ liệu cuối). Mai bổ sung file mới
  vào `data_goc/` rồi clean lần lượt.
