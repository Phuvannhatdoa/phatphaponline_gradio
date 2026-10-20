---
id: T11
title: RAG Việt chat (Fojin-style, citations)
module: Translation Pipeline
priority: low
status: pending
depends_on: [T02]
created: 2026-08-13
updated: 2026-08-24
done_when: POST /daoanh/api/rag_vi/chat trả answer_vi + citations (ref/title_zh/excerpt_vi/excerpt_zh)
---

## ⏸ TREO 2026-08-24 — Undone, chờ admin mở lại

**Lý do:** phụ thuộc trực tiếp `T02` (bảng `passage_vi` với `is_official=1` — Bước 0 của task này
tự kiểm tra điều kiện đó và dừng nếu = 0). T02 đã bị user chủ động **skip** (xem
[T02-passage-vi-entity-summary.md](T02-passage-vi-entity-summary.md)) vì thiếu Gemini API key hợp lệ
(key cũ bị Google revoke) — nên tiền đề của T11 chưa tồn tại. Không code tiếp cho tới khi:
1. T02 được admin mở lại và hoàn thành (cần Gemini key mới), VÀ
2. `passage_vi` có ≥1 row `is_official=1` thật (không phải auto-generated chưa review).

Priority hạ xuống `low` vì phụ thuộc 1 blocker ngoài tầm code (cần admin cung cấp key). Admin muốn
mở lại: đổi `status` → `pending`→`in_progress`, xoá block này, làm theo "Chỉ Thị Thực Hiện" bên dưới.

# T11 — RAG Việt chat (Fojin-style, citations)

## Mục tiêu
Khoá 6 — Build RAG tiếng Việt chuyên Phật học trên `lineage.db` + `cbeta.db` (không copy Fojin, chỉ học kiến trúc: layer corpus / search / chat / citations). Trả lời tiếng Việt kèm trích dẫn Hán + mã CBETA.

## Cách tiếp cận
- Corpus: `passage_vi` (is_official=1 ưu tiên) + fallback `passage_vi_ext` (is_official=0).
- Embedding model Việt/đa ngữ (bge-multilingual / multilingual-e5).
- Vector index: FAISS/Chroma/PGVector, entry chứa embedding + passage_id + canon/text_id/loc_ref + source + is_official.
- Endpoint `POST /daoanh/api/rag_vi/chat` — embed câu hỏi → search vector (filter entity_id/canon) → LLM với prompt tránh suy diễn → trả answer_vi + citations.
- UI chat widget (floating) với consent + attribution CC BY-SA.

## Chỉ Thị Thực Hiện (2026-08-24)

**Bước 0 — Verify T02 prerequisite:**
```sql
-- Chạy trong Python REPL hoặc sqlite3
SELECT COUNT(*) FROM passage_vi WHERE is_official = 1;
-- Expected: > 0. Nếu = 0, T02 chưa xong → KHÔNG bắt đầu T11.
```

**Bước 1 — Embedding pipeline:**
```bash
pip install sentence-transformers faiss-cpu
python -c "from sentence_transformers import SentenceTransformer; m=SentenceTransformer('BAAI/bge-m3'); print('OK')"
```
- Model ưu tiên: `BAAI/bge-m3` (multilingual, MTEB #1 Việt 2024)
- Fallback: `intfloat/multilingual-e5-large`
- Corpus: `SELECT id, excerpt_vi, passage_id FROM passage_vi WHERE is_official=1`
- Save index: `data/rag_vi.faiss` + `data/rag_vi_meta.json`

**Bước 2 — API endpoint:**
```python
# Thêm vào app.py
@app.route('/daoanh/api/rag_vi/chat', methods=['POST'])
def api_rag_vi_chat():
    q = request.json.get('question', '')
    # embed(q) → search faiss → top-5 passages → LLM(prompt+passages) → return
    return jsonify({'answer_vi': ..., 'citations': [...]})
```

**Bước 3 — Verify:** `curl -X POST http://localhost:5000/daoanh/api/rag_vi/chat -d '{"question":"Thiếu Lâm Tự thành lập năm nào?"}' -H 'Content-Type: application/json'`

## Acceptance criteria (checklist)
- [ ] `passage_vi` có ≥1 row `is_official=1` (T02 prerequisite)
- [ ] Corpus passage_vi + FAISS index tạo được (`data/rag_vi.faiss`)
- [ ] Embedding model chạy local (BAAI/bge-m3 hoặc equivalent)
- [ ] Endpoint `/daoanh/api/rag_vi/chat` trả `answer_vi` + `citations[]`
- [ ] Filter theo `entity_id` / `canon` hoạt động
- [ ] UI widget chat hiển thị citations với attribution CC BY-SA
