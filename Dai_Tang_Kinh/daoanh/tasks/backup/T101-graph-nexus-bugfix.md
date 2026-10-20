---
id: T101
title: Graph / Nexus — 5 Bugs Audit Fix (label, curated links, dynasty)
module: Graph / Nexus
priority: high
status: in_progress
depends_on: [T92]
created: 2026-09-07
updated: 2026-09-07
done_when: BUG-001/004/005 đã fix trong code; BUG-002/003 có script migration riêng; py_compile + node --check PASS; admin xác nhận
---

# T101 — Graph / Nexus Bug Fix (audit 2026-09-07)

## Nguồn gốc

Audit bởi `daoanh-debugger` agent — query DB thật + đọc source code.  
Root entity: Thiếu Lâm Tự `PL000000023255`.

## Bugs xác minh

### BUG-001 — Label Hán sai ở center node [CRITICAL]
- **Triệu chứng**: Root hiển thị `少室寺` thay vì `少林寺`.
- **Nguyên nhân**: `_resolve_dila_id()` và `api_nexus` place branch dùng `places_dila.name_zh='少室寺'` (tên alternative), trong khi `places_dila.name='少林寺'` là tên chính thức DILA.
- **File/line**: `app.py:4052-4054` (`_resolve_dila_id`), `app.py:5138` (`api_nexus` place label_zh)
- **Fix**: SELECT cả `name` và `name_zh` từ `places_dila`; ưu tiên `name` làm label chính.

### BUG-002 — Person identity sai trong place_person_bibl (4 rows) [DATA — migration riêng]
- **Triệu chứng**: 4/24 tăng nhân bị link nhầm person_id (vd: `恒月` → `釋普寂`).
- **Nguyên nhân**: `place_person_bibl.person_id` gán nhầm dila_id người khác (confidence=0.8 nhưng name mismatch).
- **Evidence**: A002000, A009319, A009365, A008784 tại `place_id=PL000000023255`.
- **Fix**: Script migration (cần tạo riêng, dry-run + --revert bắt buộc). **Chưa implement trong T101.**

### BUG-003 — event_text_link confidence sai cho NULL-person rows [DATA — migration riêng]
- **Triệu chứng**: Edge NULL-person render solid (confidence=1.0) dù chưa xác minh.
- **Nguyên nhân**: ETL place_person_bibl→event_text_link gán mặc định confidence=1.0.
- **Evidence**: `place_person_bibl id=7328 confidence=0.0` → `event_text_link id=7052 confidence=1.0`.
- **Fix**: Re-run ETL với copy nguyên confidence. **Chưa implement trong T101.**

### BUG-004 — Curated links (Bồ Đề Đạt Ma, Huệ Khả) không xuất hiện trong Đồ Thị [HIGH]
- **Triệu chứng**: 2 curated person links chất lượng cao nhất không hiện trong tab Đồ Thị.
- **Nguyên nhân**: `api_places_graph` không SELECT từ `place_person_link`.
- **Evidence**: DB có 2 rows (`A001361`, `A003881`) với source `景德傳燈錄 T51n2076`; grep `place_person_link` trong `api_places_graph` → 0 kết quả.
- **Fix**: Thêm query `place_person_link` vào `api_places_graph`, dedupe theo `seen_pids`.

### BUG-005 — Dynasty string chưa chuẩn hoá [MEDIUM]
- **Triệu chứng**: Subgroup `'北宋\n    五代十國'` (gộp 2 triều đại), `'印度'` lẫn vào phân loại triều đại.
- **Nguyên nhân**: `people.dynasty` chưa chuẩn hoá; `_fmtDynasty` không tách/lọc.
- **Fix**: Expand `_DYNASTY_VI` map; `_fmtDynasty` trim + split trên `[\n/,;]+`; fallback rõ ràng cho non-dynasty.

## Acceptance criteria

- [x] BUG-001: `_resolve_dila_id` và `api_nexus` trả `name` (少林寺) thay vì `name_zh` (少室寺)
- [x] BUG-004: `api_places_graph` query `place_person_link`, tạo node + edge solid có evidence
- [x] BUG-005: `_fmtDynasty` tách multi-value, expand `_DYNASTY_VI`, fallback '印度'→'Khác'
- [x] BUG-002: Script migration identity fix — `scripts/t101b_bug002_person_identity_fix.py` (2026-09-08; place_person_bibl 4 rows + nexus_events 4 rows → person_id=NULL; revert qua snapshot)
- [ ] BUG-003: Script migration confidence fix (task riêng hoặc sub-task)
- [x] `py_compile app.py` PASS
- [x] `node --check places.html` PASS (inline script check)
- [ ] Admin xác nhận live

## Blockers

BUG-002/003 là lỗi tầng DB (migration), cần script riêng với dry-run + --revert. Chưa có trong T101.
