# Session: Fix CBETA translate input & hidden error display

**Date:** 2026-05-24

## Liên hệ ROADMAP

- **Nguồn liên quan:** CBETA (Hán tạng số), DILA (canon_citations)
- **Khoá ROADMAP:** "Khoá 1 — Xong core Hán → Việt"
- **Dòng ROADMAP tương ứng:**
  - "Hoàn thiện mapping DILA ↔ people/places, nối với CBETA (canon_citations)"
  - "Chưa import hệ thống; mới ở mức ý tưởng pipeline XML → text_entities_raw → canon_texts/canon_citations"

## Mô tả task

Sửa 2 lỗi trong block **NGUỒN DẪN ĐẠI TẠNG KINH**:

1. **Sai input cho Gemini** — API gửi chữ Hán ngắn ("少林寺") thay vì đoạn trích CBETA đầy đủ
2. **Error hidden** — `error: "no_text"` bị filter `tr?.error !== 'no_text'`, user không thấy thông báo lỗi

## Thiết kế / giải pháp

### Backend (`app.py`)

- `_fetch_cbeta_han_text(ref)`: query `cbeta_texts` + `cbeta_content_index` theo sigla + page
- `translate_gemini_cbeta`: nhận `{ ref, han_text? }` — nếu DB không có han_text, dùng `han_text` từ frontend làm fallback
- Toàn bộ endpoint bọc trong `try/except` global → luôn trả JSON, không bao giờ trả HTML

### Frontend (`placevn.html`)

- `translateWithGemini(id)`: gửi `{ ref: id, han_text: cbetaUnits[id]?.unit?.han_text }` — dùng han_text đã load từ `/cbeta/unit` nếu có
- Error display: bỏ filter `!== 'no_text'`, hiển thị mọi lỗi. Nếu `error === 'no_text'` → "Chưa có văn bản CBETA để dịch. Hãy mở CBETA trước để tải nội dung."

## Danh sách file đã sửa

| File | Thay đổi |
|------|----------|
| `app.py` | `_call_gemini()` shared helper; `_fetch_cbeta_han_text()` helper; `translate_gemini_cbeta` endpoint mới với global try/except + fallback han_text từ body |
| `admin/placevn.html` | `translateWithGemini` gửi `{ ref, han_text }`; error hiển thị mọi trường hợp (bỏ filter `no_text`) |

## Cách chạy / test

```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent
# Sau đó restart Flask
```

## Kết quả test

```
✅ lint PASSED
✅ test PASSED
✅ e2e PASSED
✅ e2e:runtime PASSED
```
