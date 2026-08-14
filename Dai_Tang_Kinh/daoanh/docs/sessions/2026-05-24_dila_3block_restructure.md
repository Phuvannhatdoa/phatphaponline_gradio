# Session: Restructure 3-block DILA display on placevn.html

**Date:** 2026-05-24

## Liên hệ ROADMAP

- **Nguồn liên quan:** DILA Authority (Person/Place), CBETA (Hán tạng số)
- **Khoá ROADMAP:** Khoá 1 — Xong core Hán → Việt (DILA + CBETA pipeline), Khoá 5 — DILA Integration Layer
- **Dòng ROADMAP tương ứng:**
  - "Hoàn thiện mapping DILA ↔ people/places, nối với CBETA (canon_citations)"
  - "Click 1 thực thể (person/place/text) → thấy toàn bộ đoạn kinh liên quan + bản tiếng Việt (nếu có)"

## Mô tả task

Restructure 3-block DILA display on `placevn.html` sidebar per admin spec:

1. **Block 1 — NGUỒN DẪN ĐẠI TẠNG KINH (DILA)**: metadata-only list (CBETA code + context hint) with "CBETA" button → opens modal. No inline full text.
2. **Block 2 — CBETA Modal**: popup triggered by "CBETA" button, shows full Han text + LLM Vietnamese summary + CBETA Online link.
3. **Block 3 — Trích Dẫn Đại Tạng**: Vietnamese LLM translations for each DILA ref, with "Dịch" button (lazy load), disclaimer.

## Thiết kế / giải pháp

### Data source
- Block 1 + 3 share same source: `knowledgeData.cbetaIds` (parsed from DILA TEI `listbibl`)
- Block 2 reuses existing `/daoanh/api/admin/cbeta/unit` API + `/daoanh/api/admin/llm/summarize` API

### Frontend architecture
- Existing `cbetaUnits` state object reused for caching loaded units (id → {unit, summary})
- New `cbetaModal` state: `{open, id, loading}`
- New handlers: `handleOpenCbetaModal`, `handleCloseCbetaModal`, `handleTranslateRef`
- Modal component: overlay + centered panel, click-outside-to-close, scrollable

### 3-block layout
```
┌─ NGUỒN DẪN ĐẠI TẠNG KINH (DILA) ───────┐
│ T50n2060_p0457c16              [CBETA]   │
│ ⤷ {少林寺}                                │
│ T51n2076_p0234a12              [CBETA]   │
│ ⤷ {長安}                                  │
└──────────────────────────────────────────┘

┌─ Trích Dẫn Đại Tạng ─────────────────────┐
│ T50n2060_p0457c16              [Dịch]     │
│ (sau khi dịch) "đoạn văn tiếng Việt..."  │
│ T51n2076_p0234a12              [Dịch]     │
│ trích dẫn: bản dịch LLM tham khảo...     │
└──────────────────────────────────────────┘
```

## Danh sách file đã sửa

| File | Thay đổi |
|------|----------|
| `admin/placevn.html` | Thêm `cbetaModal` state; thêm handlers `handleOpenCbetaModal`, `handleCloseCbetaModal`, `handleTranslateRef`; refactor Block 1 (DILA) thành metadata-only; thêm Block 2 (CBETA modal component); thay Block 3 (entity passages → Trích Dẫn Đại Tạng); thêm disclaimer |

## Cách chạy / test

```bash
# 1. Kiểm tra syntax + runtime
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run tester:agent

# 2. Hard-refresh trang /daoanh/admin/ (chọn 1 place có CBETA refs)
# 3. Block 1: kiểm tra mỗi entry có CBETA code + [CBETA] button
# 4. Click [CBETA] → modal hiện full text + LLM summary (nếu có)
# 5. Block 3: click [Dịch] → LLM Vietnamese translation xuất hiện
```

## Kết quả test

```
✅ lint PASSED
✅ test PASSED
✅ e2e PASSED
✅ e2e:runtime PASSED
```
