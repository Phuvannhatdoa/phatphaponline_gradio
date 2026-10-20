# T380 Implementation Plan — Smart Field Merge + TEMP Snapshot

**Date:** 2026-10-13  
**Task:** Selective restore 4 tables with smart field handling  
**Approach:** TEMP snapshot → DELETE → INSERT → UPDATE → Re-insert  

---

## 📋 Overview

**Problem:** Restore 4 bảng từ 11/10 10:11 nhưng GIỮ lại một số trường mới từ bản hiện tại.

**Solution:** 
1. Chụp TEMP các trường "giữ lại" trước khi DELETE
2. DELETE all từ 4 bảng
3. INSERT from backup
4. UPDATE các trường "giữ lại" từ TEMP
5. Re-insert 4 alias_* rows từ TEMP

---

## 🔧 TEMP Snapshot Logic

### **vn_person_authority TEMP**

Trước khi DELETE, lưu những trường cần GIỮ:

```sql
-- Before DELETE
CREATE TABLE temp_vpa_current AS
SELECT 
  id,
  dila_id,
  name_vi,                 -- ← GIỮ (phiên âm đúng 2 chữ)
  biographical_note_vi,    -- ← GIỮ (tiểu sử mới)
  generation_order,        -- ← GIỮ (thế hệ mới)
  status,                  -- ← GIỮ (auto_ttl)
  ttl_filename,            -- ← GIỮ (source file)
  dharma_lineage           -- ← GIỮ (phân loại mới)
FROM vn_person_authority;
```

**Kích thước:** ~1.074 rows × 8 columns

---

### **passage TEMP**

```sql
-- Before DELETE
CREATE TABLE temp_passage_current AS
SELECT 
  passage_id,
  vi_text,                 -- ← GIỮ (dịch hiện tại)
  translation_draft        -- ← GIỮ (bản dịch hiện tại)
FROM passage;
```

**Kích thước:** ~7.563 rows × 3 columns

---

### **4 alias_* TEMP**

```sql
-- Before DELETE
CREATE TABLE temp_alias_current AS
SELECT *
FROM vn_person_authority
WHERE id LIKE 'alias_%' 
  AND id NOT IN (
    SELECT id FROM backup.vn_person_authority WHERE id LIKE 'alias_%'
  );
```

**Expected:** 4 rows (alias_A009319, alias_A010534, alias_A020120, alias_A044094)

---

## ⚙️ Restore Workflow (7 bước)

### **Bước 1: Verify Schema**

```python
# Đảm bảo schema match (with entity_type allowance)
current_cols = get_pragma_table_info("lineage.db", "vn_person_authority")
backup_cols = get_pragma_table_info("backup_11_10.db", "vn_person_authority")

# entity_type sẽ được thêm sau, nên backup có nhưng current không
if not schema_compatible(current_cols, backup_cols):
    print("ERROR: Schema mismatch")
    exit(1)
```

---

### **Bước 2: Backup Current DB**

```python
import sqlite3
import hashlib
import datetime

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"data/backups/lineage_backup_T380_{ts}.db"

# Use sqlite3.backup() API (RECOMMENDED)
current = sqlite3.connect("data/lineage.db")
backup_handle = sqlite3.connect(backup_path)
with backup_handle:
    current.backup(backup_handle)

# Calculate sha256
sha256_backup = hashlib.sha256(open(backup_path, 'rb').read()).hexdigest()
sha256_source = hashlib.sha256(open("data/backups/lineage.T265-lo-D-20261011-101118.db", 'rb').read()).hexdigest()

print(f"✓ Backup created: {backup_path}")
print(f"  Backup SHA256: {sha256_backup}")
print(f"  Source SHA256: {sha256_source}")
```

---

### **Bước 3: BEGIN TRANSACTION + ALTER TABLE**

```sql
BEGIN TRANSACTION;

-- Add entity_type column if not exists
ALTER TABLE vn_person_authority 
ADD COLUMN entity_type TEXT DEFAULT 'monk';

-- Create TEMP tables (snapshot)
CREATE TABLE temp_vpa_current AS
SELECT 
  id, dila_id, name_vi, biographical_note_vi, generation_order,
  status, ttl_filename, dharma_lineage
FROM vn_person_authority;

CREATE TABLE temp_passage_current AS
SELECT passage_id, vi_text, translation_draft
FROM passage;

CREATE TABLE temp_alias_current AS
SELECT *
FROM vn_person_authority
WHERE id LIKE 'alias_%';

-- Log: "✓ TEMP snapshots created"
```

**Why TEMP first:** Dữ liệu sẽ bị DELETE ngay sau, nên phải snapshot trước!

---

### **Bước 4: DELETE 4 Tables**

```sql
DELETE FROM ai_person_name;
DELETE FROM passage;
DELETE FROM vn_person_authority;
DELETE FROM vn_person_relations;

-- Log: "✓ 4 tables cleared (ai_person_name, passage, vn_person_authority, vn_person_relations)"
```

---

### **Bước 5: INSERT from Backup (Dynamic Columns)**

```python
# Read PRAGMA again (after ALTER, entity_type cột mới)
backup_cols = get_pragma_table_info("backup_11_10.db", "vn_person_authority")
current_cols = get_pragma_table_info("lineage.db", "vn_person_authority")

# Build INSERT with only COMMON columns
common_cols = get_common_columns(current_cols, backup_cols)

# ai_person_name
execute("INSERT INTO ai_person_name ({cols}) SELECT {cols} FROM backup.ai_person_name".format(
  cols=','.join(common_cols['ai_person_name'])
))

# passage (tất cả columns)
execute("INSERT INTO passage SELECT * FROM backup.passage")

# vn_person_authority (smart merge — chỉ columns sẽ UPDATE lại sau)
execute("""
  INSERT INTO vn_person_authority (
    id, dila_id, name_zh, status, entity_type, ...
    {cols từ backup, không gồm: name_vi, biographical_note_vi, generation_order, ttl_filename, dharma_lineage}
  )
  SELECT 
    id, dila_id, name_zh, status, entity_type, ...
    {cols từ backup}
  FROM backup.vn_person_authority
""")

# vn_person_relations
execute("INSERT INTO vn_person_relations SELECT * FROM backup.vn_person_relations")

# Log row counts
```

---

### **Bước 6: UPDATE "Keep Current" Fields from TEMP**

```sql
-- vn_person_authority: restore từ TEMP những trường GIỮ
UPDATE vn_person_authority
SET 
  name_vi = (SELECT name_vi FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id),
  biographical_note_vi = (SELECT biographical_note_vi FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id),
  generation_order = (SELECT generation_order FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id),
  status = (SELECT status FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id),
  ttl_filename = (SELECT ttl_filename FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id),
  dharma_lineage = (SELECT dharma_lineage FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id),
  dila_id = (SELECT dila_id FROM temp_vpa_current WHERE temp_vpa_current.id = vn_person_authority.id)
WHERE id IN (SELECT id FROM temp_vpa_current);

-- passage: restore dịch từ TEMP
UPDATE passage
SET 
  vi_text = (SELECT vi_text FROM temp_passage_current WHERE temp_passage_current.passage_id = passage.passage_id),
  translation_draft = (SELECT translation_draft FROM temp_passage_current WHERE temp_passage_current.passage_id = passage.passage_id)
WHERE passage_id IN (SELECT passage_id FROM temp_passage_current);

-- Log: "✓ Updated {N} rows with CURRENT values"
```

---

### **Bước 7: Re-insert 4 alias_* Rows**

```sql
-- Lấy 4 alias_* từ TEMP, insert lại với entity_type='monk'
INSERT INTO vn_person_authority 
SELECT 
  id, dila_id, name_vi, name_zh, status, 'monk' AS entity_type,
  {other columns from TEMP}
FROM temp_alias_current
WHERE id NOT IN (
  SELECT id FROM vn_person_authority WHERE id LIKE 'alias_%'
);

-- Log: "✓ Re-inserted 4 alias_* rows with entity_type='monk'"
```

---

### **Bước 8: Verify + Commit/Rollback**

```sql
-- Verify row counts
PRAGMA quick_check;

SELECT COUNT(*) FROM ai_person_name;          -- Expected: 39.269
SELECT COUNT(*) FROM passage;                 -- Expected: 44.820
SELECT COUNT(*) FROM vn_person_authority;    -- Expected: 1.511 (1.507 + 4 alias)
SELECT COUNT(*) FROM vn_person_relations;    -- Expected: 2.013

-- If all counts match:
COMMIT;  -- ✓ Success

-- If any count wrong:
ROLLBACK;  -- ❌ Rollback everything (atomic!)
```

---

## 🧪 Dry-run Mode

```python
# Same workflow as above, BUT:
# At the end: ROLLBACK (no changes to DB)
# Purpose: Verify script logic without touching real data

python T380_RESTORE_SCRIPT.py --mode dry-run
# Should complete with:
# - TEMP snapshots created ✓
# - 4 tables cleared ✓
# - Data inserted ✓
# - Updates applied ✓
# - Row counts verified ✓
# - ROLLBACK executed ✓ (safe, no changes)
```

---

## 📊 Expected Results

### Row Counts

| Table | Current | After Restore | Δ |
|---|---|---|---|
| ai_person_name | 0 | 39.269 | +39.269 |
| passage | 7.563 | 44.820 | +37.257 |
| vn_person_authority | 1.074 | 1.511 | +437 |
| vn_person_relations | 84 | 2.013 | +1.929 |

### Field Verification

| Field | Before | After | Source |
|---|---|---|---|
| name_vi (1.007 rows) | Tên ngắn | Tên ngắn (SAME) | CURRENT (via TEMP UPDATE) |
| biographical_note_vi (15 rows) | Tiểu sử | Tiểu sử (SAME) | CURRENT (via TEMP UPDATE) |
| name_zh (10 rows) | NULL | Hán chữ | Backup (RESTORE) |
| generation_order (23 rows) | Thế hệ | Thế hệ (SAME) | CURRENT (via TEMP UPDATE) |
| vi_text (137 rows) | Dịch | Dịch (SAME) | CURRENT (via TEMP UPDATE) |
| translation_draft (137 rows) | Dịch | Dịch (SAME) | CURRENT (via TEMP UPDATE) |
| entity_type (all 1.511) | N/A | monk/lay/... | Backup (via ALTER + entity_type col) |

---

## 🔄 Rollback Procedure

If restore FAILS or Admin wants to undo:

```bash
# 1. Stop servers (PID từ T380 task)
# 2. Restore backup
cp data/backups/lineage_backup_T380_<ts>.db data/lineage.db

# 3. Remove WAL files
rm data/lineage.db-wal data/lineage.db-shm

# 4. Verify
sqlite3 data/lineage.db "PRAGMA quick_check;"

# 5. Count rows (should match pre-restore)
sqlite3 data/lineage.db "SELECT COUNT(*) FROM ai_person_name;"  # Should be 0

# 6. Restart servers
```

**Backup location:** `data/backups/lineage_backup_T380_<ts>.db`  
**Documented in:** `docs/ROLLBACK.md`

---

## ⚠️ Critical Notes

1. **TEMP must snapshot BEFORE DELETE** — nếu không, dữ liệu sẽ mất
2. **Dynamic columns** — script đọc từ PRAGMA, không hardcode tên cột
3. **Atomic transaction** — nếu error → ROLLBACK tất cả
4. **Dry-run SAFE** — không touch real DB, ROLLBACK always
5. **sha256 checksumming** — verify data integrity before/after

---

## Attribution

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
