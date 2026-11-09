---
id: T219
former_ids: [T206]
title: "Data curation: sửa 2 canonical_name_vi corrupt (PL000000000314 + PL000000000001) → Thế Sát Hải / Khoát Tạt Đa Quốc"
module: Data / Canonical Identity
priority: high
status: done
owner: claudecode
depends_on: [T203, T201, T200]
created: 2026-10-02
updated: 2026-10-02
designed_by: claudecode
handoff_to: Admin
plan_approved_at: "2026-10-02 (Admin paste T206 spec — authorized 2 PL corrections only)"
commit: "9641215"
done_when: |
  Backup lineage_t206_20261002_005334.db tồn tại và SHA256 verified.
  canonical_decision.canonical_name_vi cho PL000000000314 = 'Thế Sát Hải' (UTF-8 sạch).
  canonical_decision.canonical_name_vi cho PL000000000001 = 'Khoát Tạt Đa Quốc' (UTF-8 sạch).
  is_valid_vi() trả True cho cả 2.
  build_canonical_lock() cho PL000000000314 (世剎海): LOCKED, authority_level=1.0, canonical_decision.admin_approved.
  build_canonical_lock() cho PL000000000001 (闊悉多國): CANDIDATE, authority_level=0.7, canonical_decision.auto_transliterate.
  DB integrity: 3 rows unchanged, 2 field mutations only (canonical_name_vi), schema unchanged, DILA IDs unchanged.
  T166 41/41 PASS. audit:t166 PASS (0 FAIL). npm run pipeline exit 0.
  tasktodo + ROLLBACK + session log.
risk: |
  - PL000000000314 rank=admin_approved → authority_level=1.0 → LOCKED sau correction.
    Canonical lock seẽ bắt đầu apply row này cho '世剎海' → canonical_value='Thế Sát Hải'.
    T203 đã phân tích: đây là hành vi đúng — tên authoritative từ place_desc_vi_draft.
  - PL000000000001 rank=auto_transliterate → authority_level=0.7 → CANDIDATE (chưa LOCKED).
    vstatus='needs_review' chưa đổi (không nằm trong scope T206).
    Admin cần quyết định có nâng vstatus → verified/admin_approved không (task riêng).
  - namevi_map_places và places_pending còn corrupt (ngoài scope T206 — deferred).
---

# T219 —Sửa 2 canonical_name_vi corrupt (PL rows)

> **Data-only task.** 0 code change. 0 schema change. Chỉ UPDATE 2 trường `canonical_name_vi`.
> Nguồn ủy quyền: T203-ADMIN-DATA-CURATION-PACK-01 (Class A — authoritative name available in place_desc_vi_draft).

## 1. Vấn đề (từ T203)

Hai row trong `canonical_decision` có `canonical_name_vi` chứa byte 0x3F (`?`) thay vì ký tự có dấu:

| entity_ref | corrupt value | hex |
|---|---|---|
| `PL000000000314` | `'Th? S?t H?i'` | `54683F20533F7420483F69` |
| `PL000000000001` | `'Kho?t T?t ?a Qu?c'` | `4B686F3F7420543F74203F612051753F63` |

Hệ quả:
- `is_valid_vi()` trả `False` (ASCII-only) → cả 2 row bị lọc khỏi canonical lock
- `PL000000000314` có `rank=admin_approved` (level=1.0) nhưng không bao giờ LOCK được

## 2. Nguồn authoritative (T203 Class A)

`place_desc_vi_draft` chứa tên UTF-8 sạch:

| place_id | name_vi | desc_source | created_at |
|---|---|---|---|
| `PL000000000314` | `'Thế Sát Hải'` | `dila_note_zh` | `2026-08-28T08:11:40` |
| `PL000000000001` | `'Khoát Tạt Đa Quốc'` | `dila_note_zh` | `2026-08-28T08:11:40` |

## 3. Thực thi (2026-10-02)

**Script**: `t206_backup_and_apply_v2.py` (scratchpad)

### Backup

```
file:    data/backups/lineage_t206_20261002_005334.db
size:    1,500,381,184 bytes
sha256:  50fd01fc25d939a2088dddb26e5da6fc2e99e8a912f073733acf572f2174958e
```

### Mutations applied

```
UPDATE canonical_decision
SET canonical_name_vi = '<new>', updated_at = '2026-10-02T00:54:46...'
WHERE entity_ref = '<id>'
```

| entity_ref | OLD | NEW |
|---|---|---|
| `PL000000000314` | `'Th? S?t H?i'` | `'Thế Sát Hải'` |
| `PL000000000001` | `'Kho?t T?t ?a Qu?c'` | `'Khoát Tạt Đa Quốc'` |

Total affected: **2 rows** (expected 2 ✓)

## 4. Canonical lock validation (post-correction)

| entity_ref | source_text | canonical_value | authority_source | authority_level | status |
|---|---|---|---|---|---|
| `PL000000000314` | `世剎海` | `'Thế Sát Hải'` | `canonical_decision.admin_approved` | **1.0** | **LOCKED** |
| `PL000000000001` | `闊悉多國` | `'Khoát Tạt Đa Quốc'` | `canonical_decision.auto_transliterate` | 0.7 | CANDIDATE |

`is_valid_vi()`:
- `'Thế Sát Hải'` → `True` ✓
- `'Khoát Tạt Đa Quốc'` → `True` ✓
- `'Th? S?t H?i'` (old) → `False` (reference)
- `'Kho?t T?t ?a Qu?c'` (old) → `False` (reference)

`safe_errors()` = `[]` ✓

## 5. DB integrity

| Check | Result |
|---|---|
| `canonical_decision` row count | `3` → `3` (unchanged) ✓ |
| Total field mutations | `2` (canonical_name_vi only) ✓ |
| Unapproved field changes | `0` ✓ |
| Schema changed | No ✓ |
| DILA IDs changed | No ✓ |
| Unexpected INSERT | No ✓ |
| Unexpected DELETE | No ✓ |

## 6. Regression

| Test | Result |
|---|---|
| `test_t166_matrix.py + test_t166_canonical_lock.py` | **41/41 PASS** |
| `audit:t166` | **PASS (0 FAIL)** + 1 WARN (Gemini key — pre-existing) |
| `npm run pipeline` | **exit 0** |

## 7. Deferred (ngoài scope T206)

### T200 — 33 duplicate DILA-ID groups

Giữ nguyên theo T203. Không có mutation nào. Admin curation required:
- 7 CLEAR_ALIAS — cần Admin approve xóa duplicate row
- 10 POSSIBLE_DUPLICATE — cần xác nhận 1 người
- 11 POSSIBLE_ID_COLLISION — cần tra DILA
- 3 TRUE_CANONICAL_CONFLICT — cần tra DILA + tách dila_id
- 2 NEEDS_MORE_EVIDENCE — cần tra DILA

**A047679**: `ADMIN APPROVAL REQUIRED` — không tách, không merge. Cần evidence từ DILA source XML.

**A021395**: `ADMIN APPROVAL REQUIRED` — 1 người (Pháp Diễn 法演), 3 tiền tố chùa. Admin chọn canonical row.

**A010511**: `ADMIN APPROVAL REQUIRED` — TRUE_CANONICAL_CONFLICT. `nam_nhac_huyen_thai` là canonical winner. 2 rows kia sai dila_id. Admin approve tách + sửa `name_zh` câu thơ thiền.

### 211 dila_id='' rows

Không mutation. Deferred. Admin cần phân loại sub-categories trước.

### namevi_map_places + places_pending

`PL000000000314` và `PL000000000001` trong `namevi_map_places` và `places_pending` vẫn corrupt (ngoài scope T206). Cần task riêng sau khi Admin approve.

### PL000000000001 vstatus

`vstatus='needs_review'` — chưa nâng lên `verified` (scope T206 không cover). Admin quyết định.

## 8. Rollback

```powershell
copy /Y "data\backups\lineage_t206_20261002_005334.db" "data\lineage.db"
```

Hoặc dùng SQLite:
```bash
sqlite3 data/lineage.db ".restore 'data/backups/lineage_t206_20261002_005334.db'"
```

**Backup SHA256**: `50fd01fc25d939a2088dddb26e5da6fc2e99e8a912f073733acf572f2174958e`

## 9. Ngoài phạm vi

❌ namevi_map_places corrupt rows — task riêng
❌ places_pending.name_vi corrupt — task riêng
❌ A010511/A047679/A021395 tách dila_id — chưa approved
❌ 211 dila_id='' rows — chưa classified
❌ canonical_lock.py / app.py — 0 code change
❌ T181/T100/T73/T198/T196 — không liên quan
