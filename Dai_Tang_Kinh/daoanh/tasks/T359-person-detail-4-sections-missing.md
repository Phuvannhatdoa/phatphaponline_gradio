---
id: T359
title: "admin/person.html?id=A000035 — 4 khối thông tin bị thiếu (Thầy/Học trò, Sự kiện, Nơi xuất xứ, CBETA citation)"
status: in_progress
created: 2026-10-12
updated: 2026-10-12
parent: null
former_ids: []
depends_on: []
done_when:
  - "A000035 hiển thị đầy đủ teacher/student (số liệu lấy sau khi debugger verify thật DB/XML, không giả định trước)"
  - "A000035 hiển thị timeline event 'Hoạt động khoảng 1138' (floruit)"
  - "A000035 hiển thị 'Nơi xuất xứ' lấy từ person_origin_link (place_id=PL000000014900) qua API"
  - "A000035 hiển thị CBETA citations nếu data thật đã có sẵn (code trỏ đúng nguồn, KHÔNG backfill nếu rỗng)"
  - "A000035 hiển thị Places (activeAt) và Works (worksBy) nếu data thật đã có sẵn trong DB/XML"
  - "KHÔNG backfill/tạo data mới cho bất kỳ section nào nếu chưa có xác nhận admin — chỉ sửa code đọc đúng nguồn có sẵn"
---

## Cập nhật scope (2026-10-12, từ coordinator)

Coordinator báo XML gốc A000035 có đầy đủ: 1 teacher + 5 students (listRelation), 8 CBETA citations (listBibl),
4 places (activeAt), 6 works (worksBy) — nhưng code hiện chỉ load partial. Lưu ý: số liệu này **mâu thuẫn**
với audit gốc bên dưới (18 edges + 6 primary_teacher từ DB `lineage_edge_assertions`/`lineage_primary_teacher`).
daoanh-debugger phải tự verify lại DB + XML trước khi code, không tin số liệu nào chưa kiểm chứng.
Mở rộng phạm vi: thêm CBETA (fix 4a — chỉ sửa code trỏ đúng bảng, không backfill), Places, Works.
Vẫn giữ nguyên tắc: không backfill/tạo data mới, không đổi schema, không git commit.

## Triệu chứng

Route: `admin/person.html?id=A000035` (local, http://127.0.0.1:8080/...). 4 khối thông tin không hiển thị dù data đã có sẵn trong DB.

## Root cause (đã audit, xác nhận trước khi sửa)

1. **Thầy/Học trò (Teacher/Student)** — `_t148_load_dila_extra` query bảng `ttl_v2_source_records` không tồn tại → exception bị nuốt im, không fallback.
   - Data thật: 18 edges trong `lineage_edge_assertions` + 6 trong `lineage_primary_teacher` cho A000035.
   - Fix: UI trỏ sang endpoint đã hoạt động `/daoanh/api/person/<id>/dila-axis` thay vì `dila_full` đang gãy.

2. **Sự kiện/Timeline (Events)** — API `/daoanh/api/persons/A000035` đã trả `timeline: [...]` nhưng UI không đọc field này.
   - Data thật: 1 event (floruit, 1138).
   - Fix: thêm renderer đọc `timeline` field từ response, hiển thị dạng list.

3. **Địa điểm xuất xứ (Origin Place)** — API chưa expose field `origin_place`; UI không có block hiển thị.
   - Data thật: `person_origin_link` có 1 dòng (place_id=PL000000014900).
   - Fix: thêm query `person_origin_link` vào API + thêm UI block hiển thị tên địa danh.

4. **CBETA citations (ưu tiên thấp nhất)** — code gọi bảng `listbibl` thay vì `cbeta_person_mentions`.
   - Data thật: A000035 hiện có 0 dòng trong `cbeta_person_mentions` (chưa import/assign).
   - Fix (a): sửa API trỏ đúng bảng `cbeta_person_mentions`.
   - Fix (b): backfill mention — **CẦN XÁC NHẬN ADMIN TRƯỚC**, không tự làm trong task này.

## Phạm vi dự kiến

- File liên quan nghi vấn (debugger audit lại trước khi sửa, không giả định path cứng):
  - `daoanh/app.py` — route `_t148_load_dila_extra`, endpoint `/daoanh/api/persons/<id>`, endpoint dila-axis, endpoint CBETA mentions.
  - `daoanh/static/admin/person.html` (hoặc tương đương) — renderer timeline, origin place, teacher/student, CBETA block.
- Chỉ sửa code (resolver/API/UI renderer). Không sửa raw data, không backfill CBETA mention (fix 4b) nếu chưa có xác nhận.
- Không revert T172/TTL code. Không đổi cấu trúc hiện tại ngoài phạm vi 4 fix trên.

## Kế hoạch

1. Backup các file sẽ sửa vào `docs/sessions/2026-10-12/`.
2. Giao `daoanh-debugger` sửa fix 1-3 (code only).
3. Giao `daoanh-qa` kiểm chứng.
4. Báo cáo admin, hỏi xác nhận DONE và hỏi quyết định về fix 4b (backfill CBETA).

---

## Session Log (2026-10-12 Session Update)

### Fix 1-3: ✅ COMPLETED & BROWSER VERIFIED

**Commit:** `36ed846` (Oct 12, after person.html reorder)

- ✅ Teacher/Student section: displaying 1 teacher (Nguyên Huệ A020314) + 5 students via `/dila-axis` API
- ✅ Timeline section: displaying 1 event (floruit 1138) from `vn_person_events`
- ✅ Origin Place section: displaying 1 place (Tân Điếm PL000000014900) from `person_origin_link`

**Browser verification (http://127.0.0.1:8080/daoanh/admin/person.html?id=A000035):**
- All 3 sections load with correct data
- No API errors, no JS console errors
- Data matches expected XML source

### UI Layout Adjustment

**Commit:** `36ed846` (reorder sections)

- Moved "KIỂM TRA PHIÊN ÂM HÁN–VIỆT (CHARWISE)" section to first position (was 5th, now 2nd after header)
- New layout: Header → T172 → Place → Timeline → Lineage → DILA XML → Biography
- User requested: align with session flow priorities

### Pending Decisions

**Fix 4 (CBETA):** 0 rows for A000035 in `cbeta_person_mentions`
- XML shows 8 CBETA citations, but 158 rows exist with name "了然" mapped to **wrong ID** (A009729 instead of A000035)
- Action: awaiting admin decision on data remapping vs. skip

**Fix 5-6 (Works/Places):** data not yet explored
- May depend on XML schema verification and DB schema check
