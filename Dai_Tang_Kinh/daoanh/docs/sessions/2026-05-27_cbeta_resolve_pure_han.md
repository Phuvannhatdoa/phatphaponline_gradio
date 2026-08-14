# Session: Fix CBETA Resolver — Trả Hán văn thuần, hai tầng resolve/translate

**Ngày:** 2026-05-27
**Cập nhật:** 2026-05-27 (Round 2 — xoá cache skip hoàn toàn)

## Mô tả

UI Đạo Ảnh hiển thị "Tóc ngọc xõa xuống, bánh xe vàng ngự trị bầu trời..." cho ref `T50n2060_p0457c16` (Tiểu sử Huyền Trang, Thiếu Lâm Tự) thay vì Hán văn đúng. Lỗi do `translate_gemini_cbeta` trả cache `vi_summary_clean` cũ (Gemini dịch sai) mà không kiểm tra `han_text` còn tươi từ `cbeta.db`.

Yêu cầu: hai tầng tách biệt:
- **Layer 1** — `resolve_ref`: chỉ đọc `cbeta.db` → trả Hán văn thuần
- **Layer 2** — `translate_ref`: gọi Layer 1 trước, rồi mới dịch

## Phân tích schema thật

```
cbeta.db → cbeta_texts(id, sigla, canon, vol, title_zh, ...)
        → cbeta_content_index(id, text_id(FK), juan, page, line_num, content_zh)

- page = '0457a' (đã gồm column letter)
- line_num = NULL cho hầu hết (lưu full page, không per-line)
- content_zh = Hán văn thuần (VD: 竊聞。六爻探賾局於生滅之場。...)
```

Ref `T50n2060_p0457c16` → Page '0457c' không tồn tại trong DB (chỉ có '0457a'). Prefix fallback `0457%` tìm được '0457a' có Hán đúng, nhưng cache `vi_summary_clean` giữ bản Gemini cũ.

## Giải pháp

1. **Endpoint mới** `GET /daoanh/api/admin/cbeta/resolve?ref=T50n2060_p0457c16`
   - Chỉ query `cbeta.db` (`cbeta_texts` + `cbeta_content_index`)
   - Không join bảng Việt/translation nào
   - Trả `ensure_ascii=False` (UTF-8 raw qua `Response(json.dumps(...))`)

2. **Sửa `translate_gemini_cbeta`**
   - Snapshot `old_han_text` từ `cbeta_ref_passages` TRƯỚC khi sync
   - Luôn gọi `_sync_ref_passage(ref, context)` để resolve tươi từ `cbeta.db`
   - So sánh `old_han_text` vs `han_text` mới → nếu khác, xoá `vi_summary_clean`/`vi_summary_raw` (stale cache)

## File thay đổi

| File | Thay đổi |
|------|----------|
| `app.py:3358-3460` | Thêm endpoint `/daoanh/api/admin/cbeta/resolve` (Layer 1) |
| `app.py:1450-1518` | Sửa `translate_gemini_cbeta`: snapshot + re-resolve + clear stale cache |

## Cách chạy/test

```bash
# Khởi động server
cd /opt/daoanh && python app.py

# Test resolve (Layer 1)
curl "http://127.0.0.1:5000/daoanh/api/admin/cbeta/resolve?ref=T50n2060_p0457c16"
# → han_text phải là Hán (竊聞。六爻探賾局於生滅之場...)

curl "http://127.0.0.1:5000/daoanh/api/admin/cbeta/resolve?ref=T50n2060_p0484c02"
# → phải có "少林寺" trong han_text

curl "http://127.0.0.1:5000/daoanh/api/admin/cbeta/resolve?ref=T50n2060_p0611b02"
# → phải có "少林寺" trong han_text

curl "http://127.0.0.1:5000/daoanh/api/admin/cbeta/resolve?ref=INVALID"
# → error: invalid_ref

# Pipeline
npm run pipeline
```

## Kết quả test

```
=== T50n2060_p0457c16 ===
success: True, page: 0457a
han_text: 竊聞。六爻探賾局於生滅之場。百物正名。... (Hán thuần ✓)

=== T50n2060_p0484c02 ===
success: True, page: 0484c
han_text: ...後於少林寺攝心夏坐... (có "少林寺" ✓)

=== T50n2060_p0611b02 ===
success: True
han_text: ...初住嵩高少林寺... (có "少林寺" ✓)

=== INVALID ===
error: invalid_ref ✓

Pipeline: lint ✅ test ✅ e2e ✅ e2e:runtime ✅
```

## Round 2 fix (2026-05-27) — Xoá cache skip

### Vấn đề phát hiện thêm
Cache pre-check so sánh `old_han_text == new_han_text` nhưng `han_text` **luôn đúng** (đã được sync từ `cbeta.db`). `vi_summary_clean` chứa "Tóc ngọc xõa xuống..." không bao giờ bị clear vì han_text không thay đổi.

### Fix
Xoá hoàn toàn cache pre-check trong `translate_gemini_cbeta`:
- Không snapshot `old_han_text`
- Luôn `_sync_ref_passage(ref, context)` → Hán tươi từ `cbeta.db`
- Luôn translate lại với Gemini (không cache skip)
- Lưu kết quả vào `cbeta_ref_passages` sau translate

### File thay đổi
| File | Thay đổi |
|------|----------|
| `app.py:1449-1518` | Xoá block cache skip (58 dòng → 4 dòng) |

### Kết quả test
3 refs trả Hán đúng (T50n2060_p0457c16 chứa 玄奘 + 少林寺, p0484c02 chứa 少林寺, p0611b02 chứa 嵩高少林寺).
Pipeline: lint ✅ test ✅ e2e ✅ e2e:runtime ✅

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBETA (Hán tạng số)
- **Khoá ROADMAP:** Khoá 1 – Xong core Hán → Việt
  - "CBETA pipeline (person/place → canon_citations + snippets dịch)"
  - "Cơ chế dịch 3 lớp (raw → dịch tạm → bảng chính)"
- **Dòng ROADMAP:** "API translate_gemini_cbeta (Gemini + GoogleTranslate fallback)" → bổ sung resolve layer riêng
