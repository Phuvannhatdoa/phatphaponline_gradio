# Coordinator Report — 2026-10-22

## Tong quan
- Tong task: 184
- Done: 13 (7%)
- In progress: 42
- Blocked: 28
- Pending: 92
- Deferred: 8
- Partial: 1

## Task moi nhat (T444-T456)
- T448 [done]: "Kế hoạch fix tuần tự bug UI/GIS (BUG-037 T412 → T416 autoco
- T449 [pending]: "Guard cho audit_h3_conflicts.py: không ghi đè evidence khi 
- T450 [pending]: "Tối ưu autocomplete bền vững: FTS5 cho /daoanh/api/public/a
- T451 [in_progress]: Dry-run import phien am dia danh Claude (name_vi/name_zh the
- T452 [deferred]: Nạp lại DILA Time Authority từ SQL gốc (sửa ETL time_periods
- T453 [in_progress]: Import DILA authority_catalog tạng A (A.json) + lớp dịch Việ
- T454 [pending]: Làm sạch tên địa danh Việt có hậu tố "_ Huý"/"_ Ngoa" trong 
- T455 [pending]: Chuẩn hoá tên Việt người (people.name_vi, ZQ) dựa trên đối c
- T456 [pending]: Autocomplete cho ô Search HOME (/daoanh/) — gợi ý kinh lục D
- T457 [pending]: Import DILA biographies (高僧傳 TEI) — điểm sự kiện nexus có nă
- T458 [pending]: Cloud session dịch đoạn văn sự kiện (nexus) Cao Tăng Truyện 
- T459 [pending]: Nối kinh Hán (kinh lục DILA T453) ↔ kinh Pāli qua SuttaCentr

## High-priority pending
- T244: "M7 — Matching Engine: matchGeographicSites (điểm 
- T245: "M7 — Reference Linkage: geo_cross_ref (schema + 3
- T248: "M7 — Geo Review UI (/daoanh/admin/geo_review.html
- T249: "M7 — Maps Main (/daoanh/maps/main) + chấm liền/đứ
- T387: "Backup DB bằng SQLite backup API; sync VPS upload
- T389: "Engine số đời cũ (etl_gen_compute, +37): backup t
- T414: "Bug verify: BUG-039: Cạnh thầy–trò chưa phân biệt
- T426: "3 cây — Bước 5: API + giao diện chọn 'Cây DILA / 
- T442: "T428 Part 0: Phân tích XML/TSV places + districts
- T443: "T428 Part 1: Import Claude places + districts (co
- T444: "T428 Part 2: Gemini batch transliterate places + 
- T449: "Guard cho audit_h3_conflicts.py: không ghi đè evi
- T455: Chuẩn hoá tên Việt người (people.name_vi, ZQ) dựa 
- T456: Autocomplete cho ô Search HOME (/daoanh/) — gợi ý 
- T457: Import DILA biographies (高僧傳 TEI) — điểm sự kiện n
- T53: "CBETA Content Enhancement"

## Done tasks
T284, T406, T408, T412, T427, T428, T430, T435, T436, T437, T438, T445, T448

## Next recommended actions
1. T449 guard: Admin run audit_h3_conflicts.py --force to verify
2. T450 FTS5 research: DB copy needed before touching lineage.db
3. T455/T456: Autocomplete for HOME search (high priority)
4. T444/T443: Places districts Claude/Gemini batch (depends on T428)
5. T447: Translation gateway rules (pending approval)