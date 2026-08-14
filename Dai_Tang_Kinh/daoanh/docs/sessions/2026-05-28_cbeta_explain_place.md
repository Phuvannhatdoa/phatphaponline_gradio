# Session: CBETA "Giải thích" Feature — LLM Explanation per Place in Citation

**Date:** 2026-05-28
**Task:** Thêm nút "Giải thích" bên cạnh mỗi trích dẫn CBETA trong `placevn.html`, gọi Gemini giải thích ngắn (2–4 câu) về địa danh trong bối cảnh đoạn kinh.

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBETA (Hán tạng số)
- **Khoá ROADMAP:** Khoá 1 — Xong core Hán → Việt
- **Dòng ROADMAP:**
  - "CBETA pipeline (person/place → `canon_citations` + snippets dịch)"
  - "Cơ chế dịch 3 lớp (raw → dịch tạm → bảng chính)"
- **Vai trò:** Bổ sung cơ chế "giải thích" cho từng địa danh xuất hiện trong citation, nâng cao trải nghiệm editor hiểu nhanh ngữ cảnh mà không cần rời khỏi luồng làm việc.

## Giải pháp thiết kế

### Kiến trúc

```
Layer 1 (resolve): /daoanh/api/admin/cbeta/resolve → pure Han từ cbeta.db (đã có)
Layer 2 (translate): /daoanh/api/admin/translate_gemini_cbeta → LLM dịch (đã có)
Layer 3 (explain): /daoanh/api/admin/cbeta/explain  [MỚI] → LLM giải thích địa danh
```

### Backend

1. **Bảng mới:** `cbeta_ref_explanations` trong `lineage.db`
   - `ref TEXT`, `place_id TEXT`, `place_han TEXT`, `han_sentence TEXT`, `explanation_vi TEXT`, `created_at`, `updated_at`
   - `PRIMARY KEY (ref, place_id)`
   - Tự động tạo via `ensure_cbeta_explain_table()` gọi khi app khởi động.

2. **Helper mới:** `extract_sentence_with_place(han_block, place_han)`
   - Tách `han_block` thành câu (bằng regex `[。！？]`), trả câu đầu tiên chứa `place_han`.
   - Fallback: trả 300 ký tự đầu nếu không tìm thấy.

3. **Endpoint mới:** `POST /daoanh/api/admin/cbeta/explain`
   - **Body:** `{ ref: "T50n2060_p0457c16", place_han: "少林寺", place_id?: "shaolin" }`
   - **Flow:**
     1. Sync han_text từ cbeta.db (reuse `_sync_ref_passage`).
     2. Extract sentence chứa `place_han`.
     3. Check cache `cbeta_ref_explanations` → return ngay nếu có.
     4. Gọi Gemini 2.0 Flash với prompt Phật học + Hán-Nôm, yêu cầu giải thích 2–4 câu.
     5. Cache kết quả → return `{ explanation_vi, han_sentence, cached }`.

### Frontend (placevn.html)

1. **State mới:** `cbetaExplanation` — `{ [citationId]: { loading, expl, error } }`
2. **Function mới:** `explainPlace(citationId, rawBibl)` — trích `place_han` từ `{...}` context hint, gọi explain endpoint.
3. **UI thay đổi:**
   - Thêm nút "Giải thích" (sky-400) bên cạnh nút "CBETA DỊCH VIỆT" — chỉ hiện nếu citation có `{place_han}` context.
   - Khi loading: spinner + "Đang tra..."
   - Khi có kết quả: hiển thị "GIẢI THÍCH" label + explanation text giữa ref header và translation block.
   - Khi lỗi: "Giải thích: không có phản hồi (error)".
4. **Icon mới:** `info` thêm vào `ICON_SVGS` (Lucide `circle-i` SVG).

## Danh sách file thay đổi

| File | Thay đổi |
|------|----------|
| `docs/sessions/2026-05-28_cbeta_explain_place.md` | **MỚI** — Session log này |
| `docs/db_schema.md` | Cập nhật: thêm `cbeta_ref_explanations` table |
| `docs/progress.md` | Cập nhật: CBETA section — thêm resolve 2 tầng + explain feature |
| `app.py` | Thêm `CBETA_EXPLAIN_TABLE` DDL, `ensure_cbeta_explain_table()`, `extract_sentence_with_place()`, `POST /daoanh/api/admin/cbeta/explain` endpoint |
| `admin/placevn.html` | Thêm `cbetaExplanation` state, `explainPlace()` function, "Giải thích" button, explanation display block, `info` icon SVG |

## Cách test

1. **Test endpoint trực tiếp:**
   ```bash
   curl -X POST http://localhost:5000/daoanh/api/admin/cbeta/explain \
     -H 'Content-Type: application/json' \
     -d '{"ref":"T50n2060_p0484c02","place_han":"少林寺"}'
   ```

2. **Test UI:**
   - Mở `https://phatphaponline.org/daoanh/admin/placevn.html`
   - Tìm một place có citation CBETA với context hint `{...}` (ví dụ: địa danh có ref kèm tên Hán trong ngoặc nhọn)
   - Click "Giải thích" bên cạnh citation → đợi 2–5 giây → thấy explanation hiện ra.

3. **Pipeline:**
   ```bash
   cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
   npm run pipeline
   ```

## Kết quả test

✅ **Lint:** admin/placevn.html Syntax OK — pass
✅ **Test:** Tests passed
✅ **E2E:** placevn.html All checks passed
✅ **E2E Runtime:** 2/2 passed (load + API)

## Ghi chú

- Cache `cbeta_ref_explanations` dùng composite PK `(ref, place_id)` — cho phép cùng ref với nhiều place khác nhau.
- `place_id` có thể truyền từ front-end nếu có, nếu không thì fallback bằng `place_han`.
- Prompt Gemini được thiết kế riêng cho ngữ cảnh Phật học: yêu cầu giải thích bằng tiếng Việt, hướng tới độc giả phổ thông, liên hệ tên gọi Việt Nam hiện đại nếu có.
