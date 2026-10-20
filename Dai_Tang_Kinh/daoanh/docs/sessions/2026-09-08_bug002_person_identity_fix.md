# Session 2026-09-08 — BUG-002 Person Identity Fix

**Task:** T101b — Graph/Nexus Person Identity Migration  
**Thực hiện:** Claude Code (daoanh-debugger)  
**Thời gian:** 2026-09-08 18:38–18:43

---

## Vấn đề (đã verify bằng DB + API)

4 rows trong `place_person_bibl` cho Thiếu Lâm Tự (PL000000023255) bị ETL gán nhầm `person_id`:

| ppb.id | person_name_raw | person_id sai | Tên sai hiển thị | Lý do |
|--------|----------------|---------------|-----------------|-------|
| 7326 | 釋辯相 | A002000 | Tịnh Ảnh Huệ Viễn | 淨影慧遠 (523-592) ≠ 釋辯相 |
| 7340 | 恒月 | A009319 | Thích Phổ Tịch | 釋普寂 (651-739) ≠ 恒月 |
| 7343 | 智常 | A009365 | Lí Vạn Quyển | 李萬卷 (quan văn) ≠ 智常 |
| 7346 | 思睿 | A008784 | Đại Trí Thiền Sư | 大智禪師 ≠ 思睿 |

ETL cũng đã populate sai vào `nexus_events` (nguồn của graph API):
- nexus_events.id = 5254, 5263, 5265, 5267

**Tác động UI:** Tab Đồ Thị hiển thị 4 người sai lịch sử cho Thiếu Lâm Tự.

---

## Fix áp dụng

**Script:** `scripts/t101b_bug002_person_identity_fix.py`

### Thay đổi DB:

```sql
-- place_person_bibl (4 rows)
UPDATE place_person_bibl SET person_id=NULL, confidence=0.0
WHERE id IN (7326, 7340, 7343, 7346);

-- nexus_events (4 rows)  
UPDATE nexus_events SET person_dila_id=NULL
WHERE id IN (5254, 5263, 5265, 5267);
```

**Giữ nguyên:** `person_name_raw` (釋辯相, 恒月, 智常, 思睿) — bằng chứng gốc từ sách.

### Snapshot rollback:
`data/bug002_person_identity_snapshot.json` — chứa 4 ppb + 4 nexus_events gốc.  
Rollback: `python scripts/t101b_bug002_person_identity_fix.py --revert`

---

## Kết quả verify

| Check | Before | After |
|-------|--------|-------|
| place_person_bibl rows | person_id=A002000/A009319/A009365/A008784, conf=0.8 | person_id=NULL, conf=0.0 |
| nexus_events rows | person_dila_id có 4 sai | person_dila_id=NULL |
| API /graph person count | 26 (4 sai) | **22 (chỉ đúng)** |
| 4 wrong nodes in API | PRESENT | **REMOVED ✓** |

**API endpoint verified:** `GET /daoanh/api/places/PL000000023255/graph`

---

## Trạng thái sau fix

- Thiếu Lâm Tự graph: 22 tăng nhân đúng lịch sử (bỏ 4 người nhầm)
- 4 tên gốc (釋辯相 etc.) vẫn trong DB, chờ DILA scholar resolve đúng person_id
- BUG-003 (event_text_link confidence sai) — chưa fix, cần session riêng
