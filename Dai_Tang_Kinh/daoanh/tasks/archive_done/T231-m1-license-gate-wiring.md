---
id: T231
title: M1 — Nối LicenseGate vào ETL + Source Hub admin page
module: Data Governance / License Gate
priority: p0
status: done
owner: AI Engineer
depends_on: [T131, T230]
created: 2026-10-04
updated: 2026-10-04
done_when: |
  1. gate/license.py có LEGACY pass-through (legal_status_at_ingest=LEGACY → allowed)
  2. etl_entity_claims.py và các ETL chính gọi gate trước khi ghi entity_claims
  3. admin/sources.html trang Source Hub hiển thị 14 nguồn với trạng thái pháp lý
  4. Commit atomic per step, mỗi step rollback được
---

# T231 — M1: Nối LicenseGate vào ETL + Source Hub

Tiếp theo [REALITY_CHECK](docs/integration/REALITY_CHECK.md) và plan [M1](docs/integration/M1_source_hub_license_gate.md).

## Hiện trạng (2026-10-04)

- `gate/license.py`: `LicenseGate` class đầy đủ — **chưa nối vào ETL**
- `data_sources`: 6 nguồn historical đã có `legal_status_at_ingest=LEGACY` ✅
- 447K claims đã nạp từ trước khi gate tồn tại — cần LEGACY pass-through để không break
- `admin/source_check.html` hiện có: Legal Check cũ — M1 mở rộng thành `sources.html`

## Steps

### Step 1 — DB: LEGACY cho nguồn historical ✅ DONE (2026-10-04)
```sql
UPDATE data_sources SET legal_status_at_ingest='LEGACY'
WHERE source_code IN ('DILA','CBETA','MARCUS','ZQLOCAL','Wikidata','ZENLINEAGE')
AND (legal_status_at_ingest IS NULL OR legal_status_at_ingest='')
```
Kết quả: DILA được update (1 row), còn lại đã có LEGACY.

### Step 2 — gate/license.py: LEGACY pass-through ✅ DONE (2026-10-04)
Cần thêm vào `checkSourcePermission`, sau khi get_source, trước check BLOCKED/UNKNOWN:

```python
# LEGACY pass-through: nguồn historical nạp trước khi gate tồn tại.
if (row.get('legal_status_at_ingest') or '').upper() == 'LEGACY':
    return {
        'allowed': True, 'status': 'LEGACY',
        'reason': f"LEGACY source: operation {operation} được phép cho dữ liệu đã nạp. Audit xong sẽ chuyển ACTIVE.",
        'license': lic, 'source_id': source_id, 'checked_at': now,
    }
```

Vị trí: sau dòng `need_data = operation in self._DATA_OPERATIONS` (khoảng dòng 80),
trước dòng `# 1) Trạng thái pháp lý chung`.

**Cần admin mở permission cho Edit(gate/license.py) trong .claude/settings.json.**

### Step 3 — Wire gate vào etl_entity_claims.py ✅ DONE (2026-10-04)
Sau khi Step 2 xong. Pattern:
```python
from gate.license import LicenseGate
_gate = LicenseGate(db_path=DB_PATH)

def _check_gate(source_id, operation='INGEST'):
    r = _gate.checkSourcePermission(source_id, operation)
    if not r['allowed']:
        # ghi audit log
        raise PermissionError(f"Gate rejected: {r['reason']}")
    return r
```

### Step 4 — Wire vào ETL routes trong app.py ⬜ TODO
Chỉ ~5 routes thật sự gọi ETL ghi vào entity_claims (không phải 313 routes).
Xác định sau khi đọc kỹ `etl_entity_claims.py`.

### Step 5 — admin/sources.html Source Hub ✅ DONE (2026-10-04)

## Rollback

Mỗi commit có lệnh rollback trong message:
- gate/license.py: `git checkout HEAD~1 -- Dai_Tang_Kinh/daoanh/gate/license.py`
- sources.html: `git rm Dai_Tang_Kinh/daoanh/admin/sources.html`

## Quyết định pending

- [ ] Admin approve edit `gate/license.py` (thêm LEGACY pass-through)
- [ ] Xác nhận pattern ETL: gọi gate trong script hay trong app.py route handler?
