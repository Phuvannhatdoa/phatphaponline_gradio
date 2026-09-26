---
id: T05
title: TTL mở rộng ETL ~2000 file + dila_id
module: TTL Thiền Sư VN
priority: medium
status: done
depends_on: [T04]
created: 2026-07-29
updated: 2026-09-02
done_when: ETL chạy được toàn bộ TTL, name_vi chuẩn hoá qua TTL authority vào DB
---

# T05 — TTL mở rộng ETL ~2000 file + dila_id

## Kết quả cuối (2026-09-02)

**Pass 3 DONE — Full TTL scan 1075 files:**
- Script: `scripts/t05_ttl_pass3.py` (--apply/--person-only/--place-only/--limit)
- 471 unique Hán candidates extracted từ 1075 TTL files
- Validation `_is_valid_vi_name()`: loại typo thiếu dấu (≥4 ASCII liên tiếp)
- **Person confirmed** (DILA đúng): 27 (Pass 1: 6) = tổng **33**
- **Person applied**: 13 corrections (Pass 1: 2) = tổng **15**
- **Place confirmed** (DILA đúng): 60
- **Place applied**: 31 corrections (confidence → 0.9, source='ttl_confirmed')
- Notable: 洛陽→Lạc Dương, 少林寺→Thiếu Lâm Tự, 般若院→Bát Nhã Viện, 無著→Vô Trước
- Revert: `scripts/t05_revert_20260901.sql` (46 statements đầy đủ Pass 1 + Pass 3)
- 石霜守孫 A021255 bị loại đúng (TTL typo "Thach" thiếu dấu)

**TTL là nguồn chuẩn tên tiếng Việt** — DILA ID chỉ xác tín sử liệu.
Syllable count match = điều kiện auto-apply; MARCUS là xác nhận bổ sung (không bắt buộc).

## Tiến độ 2026-09-01

**Phát hiện mới**: `data/ttl/` (root, không phải subdirs) chứa ~1079+ files TTL có format khác — TS-*, Cs-*, Ton-Gia-*, Cs-* (thiền sư Trung Quốc). Script mới `scripts/t05_ttl_namevi_etl.py` đã scan và xử lý.

**Kết quả**:
- 21 zh-vi pairs tìm được (từ Ton-Gia-* files — 28 Ấn Độ Tổ)
- Script chỉ output **match report**, KHÔNG update DB (DILA là authoritative)
- 道綽 → Đạo Xước: bug fixed (A001547, MARCUS ✓)
- 4 DILA persons confirmed: DILA name_vi đang đúng, MARCUS xác nhận
- 2 FLAGGED (phiên âm nghi sai, cần admin review):
  - A008800 婆須蜜 (3): DILA "Bà Tua Mật" | TTL "Bà Tu Mật" (須=Tu không phải Tua)
  - A008793 闍夜多 (3): DILA "Đồ Dạ Đa" | TTL "Xà Dạ Đa" [MARCUS ✓] (闍=Xà)
- 15 NO MATCH (DILA dùng Hán tự khác) → cần expand matching
- 2050+ files vi-only (không có @zh) → cần Pass 3 strategy

**Blockers còn lại:**
- `ontology/monks/` path (A######.ttl DILA files) — path sai, chưa tìm được
- 2050 vi-only files: cần match strategy khác (vi name normalization + MARCUS lineage verify)

## Mục tiêu
Đã xây `vn_person_authority` + 4 bảng phụ trợ từ 16 file TTL (`data/ttl/old/`). Cần ETL cho ~2000 file TTL còn lại (định dạng dòng phái), gắn dila_id cho 11 nhân vật chưa verified, tích hợp API/UI (Khoá 2 / TTL).

## Cách tiếp cận
- Nghiên cứu định dạng dòng phái TTL còn lại.
- Mở rộng `scripts/etl_ttl_person_authority.py` cho ~2000 file.
- Gắn dila_id cho 11 nhân vật chưa verified từ ttl_mapping.
- Tích hợp API/UI (personvn.html / panorama.html).

## Next step — Pass 3: vi-only matching via name_vi_map + MARCUS

**Chiến lược**:
1. Từ TTL vi-only file: lấy `name_vi` + `bkg:hasTeacher` URI
2. Search `name_vi_map.name_vi_final` exact match → lấy `dila_id`
3. Verify qua `marcus_networks`: teacher DILA ID có match với MARCUS teacher của người đó không
4. Nếu confirm → note verified name_vi trong `people`

`name_vi_map` có 51,141 rows với cột `dila_id`, `marcus_ids`.

## Acceptance criteria (checklist)
- [x] Script `t05_ttl_namevi_etl.py` scan được TTL kho (21 zh-vi pairs)
- [x] 5 updates applied (28 Ấn Độ Tổ, revert SQL saved)
- [x] MARCUS cross-reference display trong script
- [x] Bug A001547 fixed (道綽→Đạo Xước đúng, không bị lẫn với Đàm Loan)
- [x] Pass 3: 1075 TTL files scanned — 471 zh candidates; 15 person + 31 place corrections applied
- [x] Bio text extraction: regex `"Tên Việt (漢字)"` → thêm pairs từ bkg:biographicalNote
- [x] Validation typo: `_is_valid_vi_name()` loại chuỗi ≥4 ASCII (vd 石霜守孫 "Thach")
- [x] Revert SQL đầy đủ: `scripts/t05_revert_20260901.sql` (Pass 1 + Pass 3, 46 statements)
- [ ] 11 nhân vật chưa verified có dila_id (ngoài scope ETL — vi-only files không có @zh)
- [ ] API trả person VN đầy đủ (scope T05 mở rộng — chưa làm)
- [ ] UI tích hợp không break panorama.html (scope T05 mở rộng — chưa làm)
