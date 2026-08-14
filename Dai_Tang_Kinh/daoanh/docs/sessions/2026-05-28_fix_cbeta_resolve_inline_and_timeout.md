# Session: Fix CBETA Resolve Inline + Timeout khi bấm nút dịch

**Date:** 2026-05-28 (sửa tiếp 2026-05-29: focus han_sentence, dọn DB)

---

## Mô tả ngắn

1. **CBETA inline "Chưa có văn bản CBETA trong DB":** Khi bấm nút CBETA trên ref (VD T50n2060_p0457c16), không load được Hán văn dù endpoint `/cbeta/resolve` hoạt động tốt.
2. **Timeout khi dịch:** Khi bấm nút "CBETA DỊCH VIỆT" / "Giải thích" / dịch, request bị `AbortError` sau 20s → hiển thị "Máy chủ phản hồi chậm (Timeout)!".

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBETA (Hán tạng số).
- **Khoá ROADMAP:** "Khoá 1 – Xong core Hán → Việt" — CBETA pipeline (person/place → canon_citations + snippets dịch), cơ chế dịch 3 lớp.
- **Dòng ROADMAP:** "Xây xong pipeline CBETA→DILA (person trước, place sau), bắt đầu tạo `canon_citations` cho một số nhân vật mẫu"

## Thiết kế / giải pháp

### Vấn đề 1 — CBETA không hiển thị

**Root cause:** Frontend `safeFetch` trả về parsed JSON body (`{success: true, han_text: "..."}`), không phải Response object. Frontend kiểm tra `res?.ok && res?.han_block` → `res?.ok` là **undefined** vì API trả `success: true` (không có trường `ok`). Do đó rơi vào else → `res?.message || 'no_text'` → hiển thị "Chưa có văn bản CBETA trong DB".

**Fix:**
- Đổi `res?.ok && res?.han_block` → `res?.han_text` (dùng trực tiếp field có trong API response).
- Thêm `"ok": True` vào cả success và error paths của `/cbeta/resolve` endpoint cho nhất quán với các API khác.

### Vấn đề 2 — Timeout khi dịch

**Root cause:**
- `safeFetch` có hardcoded 20s timeout (`setTimeout(() => controller.abort(), 20000)`).
- `translate_gemini_cbeta` thực hiện **2 sequential Gemini calls** (stage 1: timeout 15s, stage 2: timeout 10s) → tổng ~25–30s backend time → dễ vượt 20s frontend timeout.
- Các LLM endpoint khác (explain, summarize) cũng chịu chung nguy cơ.

**Fix:**
- Sửa `safeFetch` thành configurable: `{ timeout = 20000, ...fetchOptions }` — tách timeout khỏi fetch options.
- 4 LLM call sites được set `timeout: 60000`:
  - `translateWithGemini` → `/daoanh/api/admin/translate_gemini_cbeta`
  - `explainPlace` → `/daoanh/api/admin/cbeta/explain`
  - `handleTranslateRef` → `/daoanh/api/admin/llm/summarize` (2 occurrences)
- Các call không phải LLM (DB queries) giữ nguyên 20s.

## Danh sách file đã sửa

| File | Thay đổi |
|------|----------|
| `app.py:3459` | Thêm `"ok": False` vào error responses của `/cbeta/resolve` (missing_ref, invalid_ref, not_imported, page_not_found, internal_error) |
| `app.py:3529` | Thêm `"ok": True` vào success response của `/cbeta/resolve` |
| `admin/placevn.html:293` | Sửa `safeFetch`: destructure `{ timeout = 20000, ...fetchOptions }`, dùng `fetchOptions` cho fetch, `timeout` cho AbortController |
| `admin/placevn.html:900` | Đổi `res?.ok && res?.han_block` → `res?.han_text` |
| `admin/placevn.html:940` | Thêm `timeout: 60000` cho `translate_gemini_cbeta` call |
| `admin/placevn.html:988` | Thêm `timeout: 60000` cho `cbeta/explain` call |
| `admin/placevn.html:856` | Thêm `timeout: 60000` cho `llm/summarize` call (auto-fetch) |
| `admin/placevn.html:921` | Thêm `timeout: 60000` cho `llm/summarize` call (handleTranslateRef) |

## Cách chạy test

```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run pipeline
```

Hoặc từng bước:
```bash
npm run lint    # Kiểm tra syntax JS
npm run test    # Unit tests
npm run e2e     # E2E: check HTML/JS errors
npm run e2e:runtime  # Playwright runtime test
```

## Bổ sung sau (2026-05-29)

### Task A: Focus han_sentence cho LLM

- `translate_gemini_cbeta`: thêm `extract_sentence_with_place(han_text, context)` → `llm_input`, dùng `llm_input` làm input cho LLM (prompt + fallback translate). Giữ `han_text` cho `build_name_map` (name scanning cần full text).
- `llm_summarize`: thêm `extract_sentence_with_place(han_text, place_name)` → `llm_input`, dùng cho tất cả prompt + fallback.

### Task B: Dọn đoạn Việt sai "Tóc ngọc xõa…"

- **DB table:** `cbeta_ref_passages`, ref_code `T50n2060_p0457c16`.
- **Xóa:** `vi_summary_clean` và `vi_summary_raw` (set rỗng).
- **Verify:** không còn record nào chứa "Tóc ngọc" trong DB.

### Files changed (bổ sung)

| File | Thay đổi |
|------|----------|
| `app.py:1499-1501` | Translate endpoint: extract han_sentence → llm_input cho LLM |
| `app.py:3561-3564` | Summarize endpoint: extract han_sentence → llm_input cho LLM |
| `data/lineage.db` | Xóa `vi_summary_clean`, `vi_summary_raw` cho T50n2060_p0457c16 |

### Task D: Dịch đoạn (per-segment translation) (2026-05-29)

- **Mới:** `POST /daoanh/api/admin/cbeta/translate_segment`
- Body: `{"han_text": "少林寺即魏孝文所立。", "segment_id": "T50n2060_seg9098"}`
- Split `han_text` by `[。！？；]` → translate mỗi câu bằng GoogleTranslator
- Trả về `{units: [{han, vi}], sentence_count, source}`
- Fallback: nếu không split được, translate cả block

**Frontend:**
- Mỗi context result block (match) có button **Dịch đoạn**
- Click → gọi translate_segment → hiển thị song ngữ grid 2 cột (HÁN | VI) bên dưới

**Files changed:**
| File | Thay đổi |
|------|----------|
| `app.py:3550-3600` | Endpoint mới `cbeta_translate_segment()` |
| `admin/placevn.html:187` | State `cbetaSegmentTranslations` |
| `admin/placevn.html:912-931` | Handler `translateSegment()` |
| `admin/placevn.html:1425-1470` | Render context block + per-segment translate button + bilingual grid |

### Task C: Endpoint `/api/cbeta/context` (2026-05-29)

- **Mới:** `GET /daoanh/api/admin/cbeta/context?work=T50n2060&query=少林寺&window=2`
- Tìm tất cả xuất hiện của `query` trong toàn bộ work, split theo dấu câu Hán `。！？；\n`
- Trả về `context_before[]`, `match`, `context_after[]` — mỗi segment lọc chỉ giữ Han runs
- Fallback: nếu không có `query` (contextHint null), vẫn dùng `cbeta/resolve` cũ
- Frontend: `toggleCbetaHan(id, contextHint)` — ưu tiên context endpoint nếu có place name
- Hiển thị: mỗi match là 1 block với match in bold amber, context trước/sau xám

**Files changed:**
| File | Thay đổi |
|------|----------|
| `app.py:3550-3615` | Endpoint mới `cbeta_context()` |
| `admin/placevn.html:887-913` | `toggleCbetaHan` nhận tham số `query`, 2 luồng context/resolve |
| `admin/placevn.html:1387-1389` | Button gọi `toggleCbetaHan(id, contextHint)` |
| `admin/placevn.html:1409-1430` | Render context_results dạng match blocks |

### Sự cố 502 + 404 (2026-05-29)

**Triệu chứng:**
- `POST /daoanh/api/login/check` → **502 Bad Gateway** (qua nginx)
- `POST /daoanh/api/admin/cbeta/translate_segment` → **404 Not Found**

**Root cause:**
1. **502:** `server.py` (auth gateway, port 5001) không chạy — process chết sau start vì `nohup`/`&` không đủ để tách khỏi shell session. Khi bash tool kết thúc, child process bị cleanup.
2. **404:** `app.py` (port 5000) đang chạy code cũ, chưa có endpoint `translate_segment`.

**Fix:**
1. Dùng `setsid` thay vì `nohup` để detach process:
   ```bash
   setsid python3 server.py > /tmp/server.log 2>&1 &
   ```
2. Kill `app.py` cũ, restart để load code mới.

**Trạng thái:**
- `:5001` (server.py) → `POST /daoanh/api/login/check` → `{"valid":false}` HTTP 200 ✅
- `:5000` (app.py) → `POST /daoanh/api/admin/cbeta/translate_segment` → HTTP 200 ✅

## Kết quả test

```
✅ Lint: All syntax checks PASSED (12 files, placevn.html OK)
✅ Test: Tests passed
✅ E2E: All pages passed E2E checks
✅ E2E Runtime: 2 passed
```
