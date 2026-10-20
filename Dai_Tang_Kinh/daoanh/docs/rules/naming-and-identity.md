# Quy tắc Naming & Identity — PTDA

## ID formats

| Entity | Canonical ID | Format | Table.column |
|--------|-------------|--------|-------------|
| Place | DILA Place ID | `PL000000000001` | `places.dila_id` |
| Person | DILA Person ID | `A000001` | `people.id` |
| Time | DILA Time ID | `T...` | `time_periods.time_id` |
| Event (T97) | UUID | `uuid` | `events.event_id` |
| Time mention | auto-increment | integer | `time_mentions.mention_id` |

**Cảnh báo:** `people.id` = DILA person ID — **không có** field `people.dila_id`.

---

## Display name priority (person)

1. `people.name_vi` — nếu có (**100% filled**: 48.673/48.673 rows, xác minh DB thật 2026-09-06 — docs cũ ghi "0% filled" là LỖI THỜI, không dùng làm argument trong audit/fix nữa)
2. `people.name_zh` — Hán danh gốc
3. `people.name_en` — tiếng Anh
4. Fallback: DILA ID

---

## Display name priority (place)

1. `entity_claims (source=ZQLOCAL, confidence≥0.8)` — name_vi đã duyệt
2. `namevi_map_places.name_vi` — phiên âm tự động
3. `places.name_zh` — Hán danh gốc (DILA)
4. `places.name_en` — tiếng Anh (DILA)

---

## Alias và homonym

- Nhiều tên Việt có thể map cùng 1 DILA ID (alias).
- Không merge 2 DILA entity dù tên giống nhau — entity identity do DILA quyết định.
- Homonym (cùng tên, khác entity): phân biệt bằng DILA ID, không bằng tên.
- Search trả về list kết quả, không auto-merge.

---

## Tên sách / triều đại

Không suy dynasty hay tên sách từ context — chỉ dùng giá trị từ `source_book` hoặc `cbeta_ref` field.

---

## CBETA ref format

- Format: `T0123n0001_p0001a01` (CBETA canonical)
- Dùng làm link mở passage: `https://cbetaonline.dila.edu.tw/...`
- Không tự tạo CBETA ref từ title hay nhan đề.
