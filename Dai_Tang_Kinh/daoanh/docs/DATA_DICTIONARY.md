# DATA DICTIONARY — Timeline & Person Events

> Handover "vô não" cho Admin. Bảng tra cứu: các bảng timeline, event_type, định dạng năm,
> confidence theo nguồn, và **rollback SQL 1-lệnh** cho từng task (T79/T80/T81/T82).
> Cập nhật: **2026-09-01** (T79, T80, T81 done; T82 Step1-2 build)

---

## 1. Bảng `vn_person_events` — Sự kiện của Nhân Vật

Lưu các mốc thời gian của một nhân vật (sinh/tịch/hoạt động) + sự kiện ngữ nghĩa (đóng góp, lập trường).

| Cột | Ý nghĩa |
|-----|---------|
| `id` | PK auto |
| `person_id` | Mã nhân vật. **2 namespace**: `A000xxx` (DILA) hoặc slug `bach_van_thu_doan` (TTL curated) |
| `event_type` | Loại sự kiện — xem bảng dưới |
| `event_id` | Mã sự kiện (duy nhất theo person+type; 1/person với active/floruit) |
| `event_label_vi` | Nhãn tiếng Việt mô tả |
| `event_year` | Năm CE (nếu có); NULL với sự kiện không có năm (Contribution...) |
| `ttl_filename` | File TTL nguồn (chỉ legacy_ttl) |
| `source` | Nguồn ETL — xem bảng confidence |
| `confidence` | Độ tin cậy 0–1 |
| `source_ref` | Pattern/range đã dùng để extract |

**UNIQUE constraint:** `(person_id, event_type, event_id)` — đảm bảo không duplicate.

### `event_type` taxonomy

| event_type | Nghĩa | Nguồn sinh | Confidence |
|------------|-------|-----------|-----------|
| `birth` | Năm sinh | T79 (`dila_person_regex`), T82 legacy (`legacy_ttl`) | 0.85 / 1.0 |
| `death` | Năm tịch | T79 (`dila_person_regex`), T82 legacy (`legacy_ttl`) | 0.92 / 1.0 |
| `active` | Cửa sổ hoạt động (≥2 `（YYYY）` trong bio) | T81 (`dila_active_regex`) | 0.70 |
| `floruit` | Điểm hoạt động (1 `（YYYY）`) | T81 (`dila_active_regex`) | 0.55 |
| `KeyLifeEvent` | Sự kiện trọng yếu (ngộ đạo, trụ trì...) | T82 legacy (`legacy_ttl`) | 1.0 |
| `Contribution` | Đóng góp (sáng lập phái...) | T82 legacy (`legacy_ttl`) | 1.0 |
| `PhilosophicalStance` | Lập trường tư tưởng | T82 legacy (`legacy_ttl`) | 1.0 |

> Lưu ý: T82 Step1 **chuẩn hoá casing** — legacy cũ dùng `Birth`/`Death` (hoa) nay đổi thành `birth`/`death`
> (thường) để khớp T79/T81. Các type ngữ nghĩa (KeyLifeEvent/Contribution/PhilosophicalStance) **giữ nguyên**
> vì mang thông tin riêng, không flatten vào birth/death/active/floruit.

### Các source trong `vn_person_events`

| source | Số dòng (2026-09-01) | Nghĩa | Rollback |
|--------|----------------------|-------|----------|
| `legacy_ttl` | 45 | Curated TTL (T82 Step1 hợp nhất từ source=NULL) | `DELETE FROM vn_person_events WHERE source='legacy_ttl'` (hoặc restore backup t82) |
| `dila_person_regex` | 203 | Death từ `（YYYY）示寂` (T79) | `DELETE FROM vn_person_events WHERE source='dila_person_regex'` |
| `dila_active_regex` | 5,103 | Active/floruit (T81) | `DELETE FROM vn_person_events WHERE source='dila_active_regex'` |

**Tổng:** 5,351 dòng.

---

## 2. Bảng `place_timeline_events` — Sự kiện của Địa Danh

| Cột | Ý nghĩa |
|-----|---------|
| `dila_id` | Mã place (`PL000000000xxx`) |
| `event_type` | Loại (`founding`, `dynasty`, `era`...) |
| `year` / `year_end` | Năm CE |
| `label_zh` / `label_vi` | Nhãn Hán / Việt |
| `source` | Nguồn |
| `confidence` | 0–1 |

### Các source & confidence

| source | Số dòng | Nghĩa | Rollback |
|--------|---------|-------|----------|
| `dila_era_name` | 1,471 | Kỷ hiệu (T32) | `DELETE FROM place_timeline_events WHERE source='dila_era_name'` |
| `dila_note` | 719 | Note pattern T22 | `DELETE FROM place_timeline_events WHERE source='dila_note'` |
| `dila_note_regex` | 276 | Regex DILA note (T22d) | `DELETE FROM place_timeline_events WHERE source='dila_note_regex'` |
| `dila_founding_phase2` | 55 | `（YYYY）` gần từ khoá founding (T80) | `DELETE FROM place_timeline_events WHERE source='dila_founding_phase2'` |
| `dila_dynasty` | 851 | Triều đại | theo source tương ứng |
| `dila_fosizhi` | 15 | Gazetteer TEI (T45) | `... WHERE source='dila_fosizhi'` |
| `wikidata` / `wikidata_p571` | 301 | Wikidata P571 | theo source |

**Tổng distinct place covered:** 3,534. **Temple coverage (12,919 temple places): 27.4%** (T80 reframe).

---

## 3. Định dạng năm (quan trọng — rút kinh nghiệm từ T79–T81)

- **Dùng `（YYYY）`** (paren + CE year): `皇祐五年（1053）`, `元文保元年（1317）示寂` → CE year nhiều khả năng của chủ thể.
- **KHÔNG dùng `XX年`** (đa nghĩa) hoặc **`（YYYY-YYYY）`** (2 năm = **năm sống của sư phụ/vị khác**, KHÔNG phải chủ thể —
  vd `晦機元熙（1238-1319）` là thầy của 大訢, không phải 大訢).
- Single-year parens → sự kiện của chủ thể (năm dịch kinh/trụ trì/khai sơn/tịch).

---

## 4. Data-Lock Checksum (T82 Step2)

- Script: `scripts/t82_checksum.py` — streaming sha256 từng dòng (zero-RAM), KHÔNG nạp toàn bảng vào RAM.
- File: `data/checksums.json` — baseline sau mỗi phiên build.
- Dùng: `python scripts/t82_checksum.py` (ghi baseline) / `python scripts/t82_checksum.py --verify` (so sánh → phát hiện regression).
- Bảng khoá (7): `people`, `places`, `places_dila`, `place_timeline_events`, `vn_person_events`, `place_person_bibl`, `entity_claims`.

---

## 5. Scripts T82

| Script | Công việc | Vòng đời |
|--------|-----------|----------|
| `t82_merge_events.py` | Hợp nhất + chuẩn hoá 45 legacy rows | `--dry-run` / `--apply` / `--revert` / `--stats` |
| `t82_checksum.py` | Data-Lock checksum | `--list` / (default ghi) / `--verify` |

**Rollback T82 Step1:** `python scripts/t82_merge_events.py --revert` → khôi phục 45 rows về source=NULL như gốc
(backup `data/t82_legacy_backup.json`).
