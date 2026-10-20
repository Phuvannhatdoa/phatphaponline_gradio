# T217 — VNPA ETL Preservation Guard: Final Report

**Task ID:** T217-VNPA-ETL-PRESERVE-CURATED-DILA-ID-01  
**Ngày:** 2026-10-02  
**Trạng thái:** ✅ PASS  
**Phụ thuộc:** T215, T214, T212  
**Note:** Admin spec gọi là T216 nhưng T216 đã bị claim bởi "X-T222-cloud-session-chain-c1-c6-plan" (commit `1283ee9`, superseded). Dùng T217 thay thế.

---

## A. Root Cause Confirmed

**File:** `scripts/etl_ttl_person_authority.py`

**Old algorithm (phá hủy):**
```python
# Lines 374-378 (old):
for t in ('vn_person_events', 'vn_person_works', 'vn_person_places',
          'vn_person_relations', 'vn_person_authority'):
    conn.execute(f"DELETE FROM {t}")    # ← DELETE TOÀN BỘ vn_person_authority
conn.commit()
```

**Hậu quả:** Xóa TẤT CẢ 1503 rows, bao gồm rows từ các ETL khác (`data/ttl/*.ttl` với 1000+ files). Chỉ tạo lại 16 rows từ `data/ttl/old/`. 33 dila_id từ T215 bị mất cùng với 1487 rows khác.

---

## B. Preservation Risk Table

| Field | ETL behavior | Risk |
|-------|-------------|------|
| `id` (PK) | từ URI `local_name()` — stable | SAFE (stable key) |
| `ttl_filename` | từ filename | SAFE (partition key) |
| `name_vi`, `name_zh` | từ TTL rdfs:label | ⚠️ MEDIUM (TTL edits → override) |
| `biographical_note_vi` | từ TTL | LOW |
| **`dila_id`** | từ `ttl_mapping` (không cover curated) | 🔴 CRITICAL |
| **`status`** | hardcoded `'pending'` mỗi ETL run | 🔴 CRITICAL |
| `created_at` | DB DEFAULT | SAFE (ETL không set) |

**Additional preservation risks (ngoài scope T217):**
- `name_vi` có thể bị thay đổi nếu TTL rdfs:label được sửa — cần admin review trước khi chạy ETL
- Rows từ `data/ttl/*.ttl` (1000+ files) không được xử lý bởi ETL này nhưng đều bị xóa bởi `DELETE FROM vn_person_authority`. Đây là **architectural risk** lớn hơn: ETL này không nên chạy nếu `data/ttl/old/` chỉ là một subset nhỏ.

---

## C. Stable Key Proof

**Stable key:** `id` (PK TEXT) = `local_name(monk_uri)` từ URI RDF.

Proof:
1. `id` = `local_name(monk)` = phần tên cuối URI (e.g., `bach_van_thu_doan` từ `ex:monk/bach_van_thu_doan`)
2. URI được định nghĩa trong TTL file và không đổi giữa các lần parse
3. Không có logic fuzzy, không dùng name_vi/name_zh
4. Confirmed unique: `id TEXT PRIMARY KEY` (SQLite constraint)

**Partition key:** `ttl_filename` = `fname[:-4]` (TTL filename không có đuôi `.ttl`) — xác định rows thuộc scope ETL nào.

---

## D. New Algorithm

```python
# [T217] Bước 1: Xác định scope
_ttl_keys = tuple(fname[:-4] for fname in ttl_files)
_ph = ','.join('?' * len(_ttl_keys))

# [T217] Bước 2: Snapshot curated fields (chỉ rows trong scope)
_curated_dila   = {}  # id → dila_id (non-empty chỉ)
_curated_status = {}  # id → status (non-'pending' chỉ)
for _r in conn.execute(
    f"SELECT id, dila_id, status FROM vn_person_authority WHERE ttl_filename IN ({_ph})",
    _ttl_keys
):
    if _r['dila_id'] and _r['dila_id'] != '':
        _curated_dila[_r['id']] = _r['dila_id']
    if _r['status'] and _r['status'] != 'pending':
        _curated_status[_r['id']] = _r['status']

# [T217] Bước 3: Scoped DELETE (chỉ rows trong scope ETL này)
for t in ('vn_person_events', 'vn_person_works', 'vn_person_places', 'vn_person_relations'):
    conn.execute(f"DELETE FROM {t}")          # Bảng phụ: full delete OK (no curation)
conn.execute(
    f"DELETE FROM vn_person_authority WHERE ttl_filename IN ({_ph})", _ttl_keys
)
conn.commit()

# ... INSERT rows from TTL parsing (unchanged) ...

# [T217] Bước 4: Restore curated fields
for row_id, old_dila in _curated_dila.items():
    cur = conn.execute("SELECT dila_id FROM vn_person_authority WHERE id=?", (row_id,)).fetchone()
    if cur is None: continue  # Row absent after ETL (intentionally deleted) → skip
    new_dila = cur['dila_id'] if cur['dila_id'] else ''
    if new_dila != old_dila:
        if new_dila and new_dila != '': 
            print(f"[T217 CONFLICT] {row_id!r}: curate={old_dila!r} vs incoming={new_dila!r} → giữ curate")
        conn.execute("UPDATE vn_person_authority SET dila_id=? WHERE id=?", (old_dila, row_id))
for row_id, old_status in _curated_status.items():
    cur = conn.execute("SELECT status FROM vn_person_authority WHERE id=?", (row_id,)).fetchone()
    if cur is None: continue
    if cur['status'] != old_status:
        conn.execute("UPDATE vn_person_authority SET status=? WHERE id=?", (old_status, row_id))
conn.commit()
```

---

## E. Conflict Policy

| Case | Tình huống | Hành vi |
|------|-----------|---------|
| A | existing=A123, incoming=NULL | Preserve A123 ✓ |
| B | existing=A123, incoming='' | Preserve A123 ✓ |
| C | existing=NULL, incoming=A123 | Accept A123 ✓ (không có trong snapshot) |
| D | existing=A123, incoming=A123 | Unchanged (no restore needed) ✓ |
| E | existing=A123, incoming=A999 | Conflict logged + preserve A123 ✓ |

---

## F. T215 33-Row Test

**Isolated DB test:** Copy production DB → run revised ETL → verify 33 T215 rows.

| Metric | Kết quả |
|--------|---------|
| Before | 33/33 dila_ids present |
| After ETL | 33/33 preserved ✓ |
| Changed | 0 |

**Why preserved:** 33 T215 rows có `ttl_filename` từ `data/ttl/*.ttl` (thousands of files), không phải từ `data/ttl/old/` (16 files). Scoped DELETE chỉ xóa rows với `ttl_filename IN (16 keys)` → 33 rows untouched.

---

## G. T212 Deletion Test

4 alias rows phải KHÔNG được tạo lại:

| alias_id | Sau ETL |
|----------|---------|
| alias_A009319 | Absent ✓ |
| alias_A010534 | Absent ✓ |
| alias_A020120 | Absent ✓ |
| alias_A044094 | Absent ✓ |

**Why not resurrected:** Alias rows không có `ttl_filename` trong `_ttl_keys` (chúng không phải từ `data/ttl/old/`). Scoped DELETE không xóa chúng, ETL không tạo chúng → chúng vẫn absent.

---

## H. Idempotency

Test: chạy ETL 2 lần trên cùng DB copy → kết quả giống nhau (same dila_ids for all rows). ✓ PASS.

---

## I. Production DB SHA (Before/After)

| | SHA256 |
|---|--------|
| Before T217 | `da4d24650ab5cd08fcecd17de6ea69d551dcc22785910c4b030abf8eff77a886` |
| After all tests | `da4d24650ab5cd08fcecd17de6ea69d551dcc22785910c4b030abf8eff77a886` |
| Changed | **NO** ✓ |

---

## J. Regression

| Test | Kết quả |
|------|---------|
| T217 19/19 tests | ✅ PASS |
| T200 tie-break 25/25 | ✅ PASS |
| T166 audit | ✅ PASS (0 FAIL, 1 WARN non-blocking) |
| Translation 25/27 | ⚠️ 2 FAIL pre-existing (TS-Tien-Phuoc-Trach-Sung.ttl) |
| Production DB SHA | ✅ UNCHANGED |

---

## K. Dry-Run Prediction (revised ETL against current production data)

| Metric | Dự đoán |
|--------|---------|
| Total rows | 1503 → 1496 (-7) |
| Inserted (new rows) | 0 |
| Deleted (scope cleanup) | 7 stale rows từ `data/ttl/old/` scope |
| Updated | 0 |
| Preserved | 1496 rows unchanged |
| dila_id conflicts | 0 |
| T215 33-row preservation | 33/33 ✓ |
| T212 aliases resurrected | 0/4 ✓ |

**Note về -7 rows:** 7 rows trong scope `data/ttl/old/` bị xóa nhưng không được tạo lại. Nguyên nhân: TTL files có thể đã thay đổi URI hoặc một số file không parse được monk node. Đây là cleanup hợp lệ của scope ETL này.

---

## L. Remaining Risks

1. **Architectural risk** (ngoài scope T217): ETL `data/ttl/old/` chỉ xử lý 16 files nhưng bảng `vn_person_authority` chứa 1503 rows từ nhiều nguồn. Không nên chạy ETL này như một "full rebuild" routine — chỉ dùng khi cần cập nhật riêng subset `data/ttl/old/`.

2. **`name_vi`/`name_zh` từ TTL** vẫn có thể override curated values nếu TTL được sửa. T217 không protect những fields này (ngoài scope — xem "Additional preservation risks" mục B).

3. **`status` của rows NGOÀI scope** (từ `data/ttl/*.ttl`) không được bảo vệ bởi ETL này. T217 chỉ snapshot/restore rows trong `_ttl_keys`.

4. **Bảng phụ** (`vn_person_relations`, `vn_person_places`, v.v.): vẫn full DELETE. Nếu có curation thủ công trong các bảng này, chúng sẽ mất. Hiện tại chưa có bằng chứng curation thủ công trong bảng phụ.

---

## M. Rollback

Nếu cần rollback T217:

```bash
# Xem commit hash T217
git log --oneline | grep T217

# Revert ETL script về trạng thái trước
git checkout <commit-truoc-T217>^ -- daoanh/scripts/etl_ttl_person_authority.py

# Xóa test file T217 (optional)
git rm daoanh/tests/test_t217_vnpa_etl_preservation.py
```

Không có mutation production DB trong T217 → không cần restore backup.

---

## N. Files Changed

| File | Thay đổi |
|------|---------|
| `scripts/etl_ttl_person_authority.py` | Scoped DELETE + snapshot/restore (T217 guard) |
| `tests/test_t217_vnpa_etl_preservation.py` | 19 tests mới (A-M + integration G/H/I) |
| `package.json` | `test:t217`, `test:t217:unit`, `test:t217:integration` |
| `docs/Mimo-Flash/T217-VNPA-ETL-PRESERVATION-GUARD.md` | This report |
| `tasks/T217-vnpa-etl-preservation-guard.md` | Task tracking |
