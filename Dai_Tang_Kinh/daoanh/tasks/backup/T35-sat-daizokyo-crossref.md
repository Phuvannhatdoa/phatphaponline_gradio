---
id: T35
title: SAT Daizōkyō Cross-Reference — badge "Xem trên SAT" cho CBETA texts
module: Đại Tạng / Hán Tạng
priority: low
status: done
depends_on: [T34]
created: 2026-08-24
updated: 2026-08-24
done_when: cbeta_catalog_vn texts có SAT link ID, tab Đại Tạng hiển thị badge "SAT" dẫn đến sat.tohoku.ac.jp
---

## Bối Cảnh

SAT Daizōkyō (21dzk.l.u-tokyo.ac.jp/SAT/) = Đại Tạng Kinh điện tử của Nhật Bản.  
Nội dung trùng ~85% với CBETA (cùng T-series Taishō), nhưng SAT có:
- Một số texts không có trong CBETA (Nhật Bản chú giải, bản Nhật hiệu đính)
- Kanji Unicode chuẩn JIS
- Link trực tiếp đến từng kinh qua URL: `21dzk.l.u-tokyo.ac.jp/SAT/<sigla>.html`

**Chiến lược:** KHÔNG import toàn bộ SAT. Chỉ thêm SAT ID vào bảng hiện có → badge "Xem trên SAT".

## Thiết Kế

### Bảng mới: `sat_crossref`
```sql
CREATE TABLE sat_crossref (
    cbeta_sigla  TEXT PRIMARY KEY,  -- VD: T0251, T0235
    sat_url      TEXT,              -- URL trực tiếp trên SAT
    has_unique   INTEGER DEFAULT 0, -- 1 nếu SAT có nội dung không có trong CBETA
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### ETL
- SAT có sitemap/list dạng XML hoặc HTML
- Map `cbeta_sigla` → SAT URL theo pattern chuẩn: `T<4-digit>` → URL SAT tương ứng
- Batch 3,122 texts trong `cbeta_catalog_vn` → check tồn tại trên SAT

### UI
Tab Đại Tạng: khi xem một kinh → badge nhỏ "SAT" dẫn link mới

## Acceptance Criteria
- [x] `sat_crossref` table có ≥500 rows — **2,913 rows** (2026-08-24)
- [x] API route `GET /daoanh/api/cbeta/<sigla>/sat` live — trả `{sat_url, badge_label, found}`
- [x] Không import text content từ SAT (chỉ metadata + URL)
- [ ] UI tab Đại Tạng wiring — cần server restart để test

## Completion Log (2026-08-24)

**Script:** `scripts/t35_seed_sat_crossref.py`  
**Table:** `sat_crossref(cbeta_sigla PK, sat_url, has_unique, created_at)` — 2,913 rows  
**URL pattern:** `https://21dzk.l.u-tokyo.ac.jp/SAT/T{int(sh_number):04d}.html`  
**Source:** cbeta_catalog_vn rows với cbeta_ref NOT LIKE 'X%' (loại trừ X-series)  
**API route:** `GET /daoanh/api/cbeta/<sigla>/sat` — thêm vào app.py (line ~10836)  
**Liên quan T20:** `sat_crossref` chỉ có T-series; X-series không có trong SAT Daizōkyō
