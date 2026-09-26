# Session: Merge DILA citations + CBETA/LLM blocks into one unified block

**Date:** 2026-05-24

## Liên hệ ROADMAP

- **Nguồn liên quan:** DILA Authority (Place), CBETA (Hán tạng số)
- **Khoá ROADMAP:** Khoá 1 — Xong core Hán → Việt; Khoá 5 — DILA Integration Layer
- **Dòng ROADMAP tương ứng:**
  - "Click 1 thực thể (person/place/text) → thấy toàn bộ đoạn kinh liên quan + bản tiếng Việt (nếu có)"
  - "Hoàn thiện mapping DILA ↔ people/places, nối với CBETA (canon_citations)"

## Mô tả task

Gộp 2 block riêng:
1. "NGUỒN DẪN ĐẠI TẠNG KINH (DILA)" — danh sách CBETA ID + nút CBETA
2. "Trích Dẫn Đại Tạng" — LLM Vietnamese translation + nút Dịch

Thành 1 block duy nhất **"NGUỒN DẪN ĐẠI TẠNG KINH"** với:
- Mỗi citation card hiển thị: canon_id, context hint, 2 nút [CBETA] [Dịch Việt]
- Khi đã có LLM summary → hiển thị ngay dưới card (không cần block riêng)
- Keyword highlighting trong modal CBETA (dùng `name_zh`/`name_vi`)

## Thiết kế / giải pháp

**Không tạo DB table mới, không tạo API mới.** Tất cả là frontend refactor.

### highlightKeyword(text, keyword)
- Regex escape keyword, match case-insensitive
- Wrap match trong `<mark className="bg-yellow-500/30 text-yellow-200 px-0.5 rounded">`
- Dùng `dangerouslySetInnerHTML` để render

### Merge block structure
```
┌─ NGUỒN DẪN ĐẠI TẠNG KINH ────────────────────┐
│ T50n2060_p0457c16              [CBETA] [Dịch]  │
│ ⤷ {Thiếu Lâm Tự}                               │
│                                                │
│ T51n2076_p0234a12              [CBETA]         │
│ ⤷ {Trường An}                                  │
│ (đã dịch) "bản tóm tắt tiếng Việt..."           │
│                                                │
│ Trích dẫn: bản dịch LLM tham khảo...            │
└────────────────────────────────────────────────┘
```

## Danh sách file đã sửa

| File | Thay đổi |
|------|----------|
| `admin/placevn.html` | Thêm `highlightKeyword` function; gộp 2 blocks DILA (line 1311) + LLM (line 1346) → 1 block; thêm `dangerouslySetInnerHTML` + highlight trong modal CBETA |

## Cách chạy / test

```bash
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent
# Hard-refresh /daoanh/admin/, chọn place có CBETA refs
# Verify: 1 block duy nhất, mỗi card có [CBETA] + [Dịch Việt]
# Click CBETA → modal, keyword được highlight vàng
```

## Kết quả test

```
✅ lint PASSED
✅ test PASSED
✅ e2e PASSED
✅ e2e:runtime PASSED
```
