---
id: T44
title: Ghi nhóm exact_year (niên hiệu + số Hán) KHÔNG trùng tu vào place_timeline_events
module: Place Timeline / DILA Era Name Extraction
priority: medium
status: in_progress
depends_on: []
created: 2026-10-09
updated: 2026-10-09
done_when: >
  596 dòng exact_year/has_renovation_flag=N trong docs/evidence/2026-10-09_T44_candidates.tsv
  đã ghi vào place_timeline_events (DONE). Nhóm midpoint (672 dòng) và nhóm có cờ trùng tu
  (120 dòng) CHƯA ghi — chờ Admin duyệt riêng.
---

# T44 — Era name + số Hán → founding year (nhóm exact_year, không trùng tu)

## Phạm vi đã duyệt (Admin, 2026-10-09)

Chỉ ghi nhóm `method=exact_year` + `has_renovation_flag=N` (596/1339 dòng) trong
`docs/evidence/2026-10-09_T44_candidates.tsv`. KHÔNG ghi nhóm `midpoint` (672 dòng,
gồm 623 N + 49 Y) và KHÔNG ghi nhóm có cờ trùng tu `has_renovation_flag=Y` (71 dòng
exact_year + 49 dòng midpoint = 120 dòng).

## Việc 1 — Audit trước khi ghi (chỉ đọc)

- TSV xác nhận đúng **596 dòng** `method=exact_year AND has_renovation_flag=N`
  (phân bố đầy đủ: exact_year|N=596, exact_year|Y=71, midpoint|N=623, midpoint|Y=49,
  tổng 1339 = đúng số dòng TSV).
- Schema `place_timeline_events`: `id, dila_id, event_type, year, year_end, label_zh,
  label_vi, source, source_ref, confidence, created_at`. Không có cột `method` —
  giá trị `exact_year` được ánh xạ vào `confidence='era_name_exact'` và `source_ref`
  (`"{dila_id}·{era}·era_name_exact"`), đúng theo logic ghi hiện có trong
  `scripts/dila_era_name_extract.py` (dòng ~310-327) và script sinh TSV
  `scripts/t44_gen_candidates_tsv.py` (dùng lại `extract_year_from_era()`).
- Đối chiếu DB: mỗi `dila_id` trong 596 dòng có đúng 1 chùa trong `places_dila`
  (0 dòng `!=1`, 0 `dila_id` thiếu). 0 `dila_id` nào trong 596 đã có
  `event_type='founding'` sẵn trong `place_timeline_events` (TSV được sinh từ script
  chỉ liệt kê chùa CHƯA có founding — `t44_gen_candidates_tsv.py` dòng 38-51).
- Chạy lại `extract_year_from_era(note)` trực tiếp trên `note`/`name_zh` hiện tại
  trong DB cho cả 596 `dila_id` → **0 mismatch** so với `year/era_name/method` trong
  TSV (dữ liệu nguồn chưa đổi từ lúc sinh TSV đến lúc ghi).
- Không phát hiện bất thường nào chặn việc ghi.

## Việc 2 — Backup DB

- Backup bằng SQLite Backup API (`sqlite3.Connection.backup()`, không copy file thô):
  `data/backups/lineage.T44-exact-20261009_151431.db`.
- `PRAGMA quick_check` trên file backup → `[('ok',)]`.
- Đếm trước khi ghi: `place_timeline_events` tổng = **3688**, `event_type='founding'`
  = **2251** (khớp đúng số Admin nêu).

## Việc 3 — Ghi (1 transaction)

- Script tạm (không lưu trong repo, xoá sau khi hoàn tất): dựng 596 row insert bằng
  đúng công thức của `dila_era_name_extract.py`:
  - `event_type='founding'`
  - `source='dila_era_name'`
  - `confidence='era_name_exact'`
  - `source_ref = f"{dila_id}·{era}·era_name_exact"`
  - `label_zh = f"{name_zh} {dynasty}{era} ({era_start}年建)"` (DYNASTY lấy từ
    `ERA_TABLE[era][2]`, `era_start` từ `ERA_TABLE[era][0]`)
  - `year` lấy từ TSV (đã đối chiếu khớp `extract_year_from_era()` hiện tại).
- `BEGIN` → 596 `INSERT` → `COMMIT`. Không lỗi, không ROLLBACK. `inserted = 596`.

## Việc 4 — Kiểm tra sau ghi

| Chỉ số | Trước | Sau | Kỳ vọng | Khớp? |
|---|---|---|---|---|
| Tổng `place_timeline_events` | 3688 | 4284 | 3688+596=4284 | ✅ |
| `event_type='founding'` | 2251 | 2847 | 2251+596=2847 | ✅ |
| `source='dila_dynasty'` | 851 | 851 | không đổi | ✅ |
| `source='dila_fosizhi'` | 15 | 15 | không đổi | ✅ |
| `source='dila_founding_phase2'` | 55 | 55 | không đổi | ✅ |
| `source='dila_note'` | 719 | 719 | không đổi | ✅ |
| `source='dila_note_regex'` | 276 | 276 | không đổi | ✅ |
| `source='wikidata'` | 155 | 155 | không đổi | ✅ |
| `source='wikidata_p571'` | 146 | 146 | không đổi | ✅ |
| `source='dila_era_name'` | 1471 | 2067 | +596 | ✅ |

- Không `dila_id` nào trong 596 dòng mới bị trùng (mỗi id ghi đúng 1 dòng, đã kiểm
  trước khi ghi `distinct ids = 596`).
- Kiểm tra `dila_id+year` có `event_type='founding'` trùng > 1: phát hiện **15 cặp
  tiền tồn tại từ trước** (ví dụ `PL000000023255` year=495 count=4) — **đối chiếu
  với bản backup pre-insert: DANH SÁCH 15 CẶP NÀY GIỐNG Y HỆT TRƯỚC KHI GHI**, và
  **0 overlap** giữa 15 `dila_id` đó với 596 `dila_id` trong batch T44. Đây là tình
  trạng trùng year từ nhiều nguồn khác nhau tồn tại sẵn trong DB trước T44, không
  phải do lần ghi này tạo ra — KHÔNG đụng, không sửa trong phạm vi T44.

## Bất thường

**1 điều cần Admin biết (không phải lỗi, không chặn ghi):** 15 `dila_id` đã có
nhiều dòng `founding` trùng năm từ nhiều `source` khác nhau — pre-existing, 0 liên
quan đến batch 596 dòng vừa ghi. Danh sách: PL000000000136(420×2), PL000000000357
(1592×2), PL000000005450(601×2), PL000000023255(495×4), PL000000023547(762×2),
PL000000028299(826×2), PL000000056019(1650×3), PL000000056755(348×2),
PL000000058474(1694×2), PL000000058539(1882×2), PL000000058750(1649×2),
PL000000059231(1709×2), PL000000060062(1740×2), PL000000060128(1906×3),
PL000000060132(558×2). Có thể cần task riêng để rà soát/hợp nhất sau này.

## Hoàn tác

```bash
# Cách A — xoá đúng 596 dòng vừa thêm (điều kiện chính xác)
sqlite3 data/lineage.db "DELETE FROM place_timeline_events WHERE source='dila_era_name' AND confidence='era_name_exact' AND created_at >= '2026-10-09'"

# Cách B — khôi phục từ backup (an toàn hơn, ghi đè toàn bộ DB)
# Dừng mọi process đang mở data/lineage.db trước khi copy đè.
cp data/backups/lineage.T44-exact-20261009_151431.db data/lineage.db
```

## Chưa làm (chờ Admin duyệt riêng)

- Nhóm `midpoint` (672 dòng, 623 N + 49 Y) — year xấp xỉ, chưa ghi.
- Nhóm có cờ trùng tu `has_renovation_flag=Y` (120 dòng, 71 exact_year + 49 midpoint)
  — nghi ngờ note có nhắc trùng tu, chưa ghi.
- **KHÔNG đổi `status` của task này sang `done`** — còn 2 nhóm trên pending Admin.
