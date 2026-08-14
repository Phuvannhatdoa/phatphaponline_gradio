# Session: Fix Vietnamese place names + CBETA translate per-ref

**Date:** 2026-05-27
**Task:** Handle remaining Han characters in Vietnamese place names + ensure per‑ref CBETA translation resolves correctly.

## Liên hệ ROADMAP
- **Nguồn liên quan:** DILA (place name mapping), CBETA (Hán tạng translation).
- **Khoá ROADMAP:** "Khoá 1 – Xong core Hán → Việt" (mapping tên Việt + pipeline phiên âm).
- **Dòng ROADMAP tương ứng:** "Hoàn thiện mapping DILA ↔ people/places, nối với CBETA (canon_citations)".

---

## Part A – Fix place names with remaining Han characters

### Vấn đề

Hiện tượng: `PL000000000066  Bạt 姞 Bà Già Lam` (姞 còn sót chữ Hán), `PL000000000183  邸 Sơn Tự` (邸 còn sót). Nguyên nhân: `_ensure_vietnamese()` chỉ lookup char qua `hanviet_fallback`, nếu không có thì giữ nguyên chữ Hán.

### Giải pháp

1. **`CUSTOM_HANVIET` dict** – Override map cho các chữ hiếm (姞→Cát, 邸→Để, 磧→Tích, 杲→Cảo, 祐→Hựu… ~300 entries).
2. **Thay đổi logic** trong `_ensure_vietnamese()`:
   - Priority 1: `CUSTOM_HANVIET.get(c)`
   - Priority 2: `hanviet_fallback` (DB cache)
   - Priority 3: Skip (không append raw CJK) + log vào `missing_hanzi`.
3. **Bảng `missing_hanzi`** – Tự động tạo, admin xem để expand CUSTOM_HANVIET dần.
4. **Script batch** `scripts/fix_vietnamese_names.py` – Quét toàn bộ `namevi_map_places`, `places_pending`, `places`, update name_vi bằng pipeline mới.

### File modified

| File | Change |
|------|--------|
| `app.py` (lines 120–200) | Added CUSTOM_HANVIET dict + `_ensure_missing_hanzi_table` + `_log_missing_hanzi` + improved `_ensure_vietnamese` |
| `docs/db_schema.md` | Added `missing_hanzi` table documentation |
| `scripts/fix_vietnamese_names.py` | NEW - batch cleanup script |

---

## Part B – CBETA translate per-ref

### Kết quả kiểm tra

Code hiện tại (`app.py` lines 971–1168) **đã hoàn chỉnh**:
- `translate_gemini_cbeta` endpoint nhận `{ ref, context }` → resolve per‑ref.
- `_sync_ref_passage()` query `cbeta_content_index` với exact page+col match, fallback prefix match, context‑aware fallback.
- `build_name_map()` + `make_cbeta_prompt()` xây prompt per‑ref.
- Gemini translate + Gemini summarization per‑ref.
- Kết quả cache riêng trong `cbeta_ref_passages[ref_code]`.

**Không cần thay đổi code** cho Part B.

---

## Cách test

```bash
# Check pipeline
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
npm run pipeline

# Test _ensure_vietnamese with custom chars
python3 -c "
from app import _ensure_vietnamese
print(_ensure_vietnamese('Bạt 姞 Bà Già Lam'))  # Expect: Bạt Cát Bà Già Lam
print(_ensure_vietnamese('邸 Sơn Tự'))          # Expect: Để Sơn Tự
print(_ensure_vietnamese('Trưởng 磧 Tự'))        # Expect: Trưởng Tích Tự
"

# Check missing_hanzi table
sqlite3 data/lineage.db "SELECT * FROM missing_hanzi ORDER BY count DESC LIMIT 10;"
```
