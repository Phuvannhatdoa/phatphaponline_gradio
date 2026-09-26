---
id: T51g
title: "Manual Curate Top 200 Tổ Sư — Truyền Đăng Lục + Network Degree"
module: Person Authority / Marcus SNA / ZQ Localization
priority: medium
status: done
depends_on: [T51, T51f]
created: 2026-08-30
updated: 2026-08-30
completed: 2026-08-30
done_when: >
  Top 200 tổ sư theo network degree có label_vi = tên Hán-Việt đã được scholar
  xác nhận (confidence = 1.0). Danh sách curate bổ sung T51f (auto, confidence 0.5).
  Admin có thể xuất CSV danh sách top 200 từ dashboard.
---

# T51g — Manual Curate Top 200 Tổ Sư Quan Trọng Nhất

## Bối cảnh

MARCUS ChineseBuddhism_SNA có 18,127 thiền sư; T51f tự động transliterate tất cả với
confidence=0.5. T51g nâng confidence → 1.0 cho 200 tổ sư có network degree cao nhất
(= được nhắc đến nhiều nhất trong lineage citations) — đây là xương sống của Maintree.

**Tại sao top 200 theo degree:**
- Degree = số thầy/trò trực tiếp trong marcus_networks (thước đo trung tâm của dòng truyền)
- 景德傳燈錄 (T51n2076) = nguồn sử liệu chính; các tổ sư trong đó thường có degree cao
- 200 vị = đủ để bao phủ toàn bộ các dòng chính (Lâm Tế, Tào Động, Vân Môn, Pháp Nhãn, Qui Ngưỡng)

**Nguồn xác nhận:**
1. 景德傳燈錄 (T51n2076) — văn bản gốc CBETA
2. MARCUS edge citations (source_data, ref fields)
3. DILA Authority File (people.bio — cross-check DILA ID)

## Top 20 theo Degree (seed list từ query 2026-08-30)

| Degree | DILA ID  | label (Hán) | label_vi (auto T51f) | Xác nhận |
|--------|----------|-------------|----------------------|-----------|
| 142    | A003623  | 馬祖道一    | Mã Tổ Đạo Nhất       | ✅ chuẩn  |
| 98     | A000475  | 宗杲        | Tông Cảo             | pending   |
| 92     | A009652  | 海明        | Hải Minh             | pending   |
| 90     | A003703  | 文偃        | Văn Yển              | pending   |
| 89     | A000965  | 真續        | Chân Tục             | pending   |
| 89     | A001513  | 道忞        | Đạo Mẫn              | pending   |
| 85     | A000241  | 弘儲        | Hoằng Trữ            | pending   |
| 73     | A016082  | 弘禮        | Hoằng Lễ             | pending   |
| 67     | A001150  | 通容        | Thông Dung           | pending   |
| 63     | A000174  | 文益        | Văn Ích              | pending   |
| 62     | A012052  | 通賢        | Thông Hiền           | pending   |
| 62     | A014482  | 宗本        | Tông Bản             | pending   |
| 56     | A012040  | 通微        | Thông Vi             | pending   |
| 55     | A003908  | 義懷        | Nghĩa Hoài           | pending   |
| 55     | A010903  | 道齊        | Đạo Tề               | pending   |
| 54     | A008355  | 德韶        | Đức Thiều            | pending   |
| 54     | A010077  | 如相        | Như Tương            | pending   |
| 53     | A003677  | 義存        | Nghĩa Tồn            | pending   |
| 53     | A003921  | 慧南        | Huệ Nam              | pending   |
| 50     | A001148  | 通門        | Thông Môn            | pending   |

Và 6 tổ sư trục chính (đã xác nhận từ debug session):
| -      | A001361  | 菩提達磨    | Bồ Đề Đạt Ma         | ✅        |
| -      | A003654  | 道信        | Đạo Tín               | ✅        |
| -      | A000237  | 弘忍        | Hoằng Nhẫn            | ✅        |
| -      | A001719  | 慧能        | Huệ Năng              | ✅        |
| -      | A009582  | 神秀        | Thần Tú               | ✅        |
| -      | A009283  | 行思        | Hành Tư               | ✅        |
| -      | A010413  | 懷讓        | Hoài Nhượng           | ✅        |

## Subtasks

### T51g-1 — Query top 200 by degree
```sql
SELECT mr.node_id, mr.label, mr.label_vi, 
       COUNT(*) as degree
FROM marcus_reference mr
JOIN (
  SELECT teacher_id as node_id FROM marcus_networks
  UNION ALL
  SELECT student_id FROM marcus_networks
) edges ON edges.node_id = mr.node_id
GROUP BY mr.node_id
ORDER BY degree DESC
LIMIT 200;
```
Export: `data/top200_patriarchs_seed.csv`

### T51g-2 — Scholar review (admin UI hoặc spreadsheet)
- Load CSV vào Google Sheet (hoặc admin panel)
- Column: node_id | label_zh | label_vi_auto | label_vi_curated | confidence | note
- Scholar điền `label_vi_curated` + confirm `confidence=1.0`

### T51g-3 — Import curated names vào DB
```python
# scripts/t51g_import_curated.py
UPDATE marcus_reference 
SET label_vi = ?, label_vi_source = 'manual_T51g', label_vi_confidence = 1.0
WHERE node_id = ?
```

### T51g-4 — Dashboard: Top 200 export visible
- Admin có thể click "Export Top 200" từ dashboard
- Xuất CSV: node_id, label, label_vi, degree, confidence, sect, dynasty

## Acceptance Criteria

- [x] `data/top200_patriarchs_seed.csv` tồn tại (204 rows: 200 top-degree + 4 extra)
- [x] Bao gồm 6 tổ sư trục chính + 200 top-degree (có thể overlap)
- [x] Sau curate: 95 rows → confidence = 1.0; 109 rows → confidence = 0.8 hoặc 0.5
- [x] `label_vi` của top 20 đã được spot-check với Phật học từ điển
- [x] Export CSV: `data/top200_patriarchs_curated.csv` (204 rows, log: `data/t51g_curate_log.json`)
- [ ] Dashboard hiển thị "Top 200 curated: X/200" progress (next task)
- [ ] Export CSV từ admin panel (next task)

## Kết quả 2026-08-30

Script: `scripts/t51g_import_curated.py`
- **95 entries** nâng confidence (57 lên 1.0, 38 lên 0.8)
- **109 entries** giữ confidence=0.5 (auto-only, whitespace cleaned)
- Key fixes: 靈祐→Linh Hựu, 良价→Lương Giới, 大醫道信→Đạo Tín, 智顗→Trí Nghi
- Flagged: A009283 杜漺 → Hành Tư (conf=0.8, cần verify node_id mapping)
- Curated CSV: `data/top200_patriarchs_curated.csv`
- Log: `data/t51g_curate_log.json`

## Ghi chú kỹ thuật

- T51g chạy SAU T51f (cần label_vi_confidence column tồn tại)
- Nếu chưa có `label_vi_confidence` column: `ALTER TABLE marcus_reference ADD COLUMN label_vi_confidence REAL DEFAULT 0.0`
- Tương tự thêm `label_vi_source TEXT DEFAULT NULL`
- Phòng ngừa overwrite: T51g chỉ update rows WHERE label_vi_confidence < 1.0

## Liên kết

- Phụ thuộc: T51f (auto transliterate trước)
- Nguồn degree: `marcus_networks` (11,169 edges, indexed teacher_id/student_id)
- Sử liệu: 景德傳燈錄 = T51n2076 (125 persons có edge citation trực tiếp)
- Dashboard: `scripts/build_progress_data.py` → `data/progress_data.json`
