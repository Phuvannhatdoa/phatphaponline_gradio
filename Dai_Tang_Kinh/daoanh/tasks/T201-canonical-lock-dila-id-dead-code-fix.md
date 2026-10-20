---
id: T201
title: "P0 canonical_lock.py:871 `pd.dila_id` SAI (places_dila PK=id) ⇒ nguồn #1 canonical_decision DEAD CODE; sửa + canonical row A001984"
module: Code / Canonical Identity Guard
priority: critical
status: done
owner: claudecode
depends_on: [T166, T199]
created: 2026-09-30
updated: 2026-09-30
designed_by: claudecode
handoff_to: Admin
plan_approved_at: "chờ Admin duyệt (phát hiện trong T199, defer canonical row sang đây)"
done_when: |
  Admin xác nhận nhãn `canonical_decision` canonical_name_vi cho A001984;
  canonical_lock.py:871 sửa `pd.dila_id` → `pd.id` (và rà mọi `pd.`/`pj.` reference khác);
  test hồi quy chứng minh nguồn #1 KHÔNG còn nuốt lỗi: thêm case "sqlite3.Error bị nuốt"
    vào t166_identity_audit.py (nâng check từ silent-fail sang report);
  build_canonical_lock sinh entity cho '靈祐' với source='canonical_decision.admin_approved'
    level=1.0 và is_lock_flagged=True ⇒ LOCKED;
  chèn canonical_decision 1 row A001984 (script T199 --apply --with-canonical hoặc SQL thủ công
    có backup) ⇒ verify LOCKED thật;
  test_t166_matrix.py + test_t166_canonical_lock.py + audit:t166 PASS;
  npm run pipeline PASS; tasktodo + ROLLBACK + session + dashboard.
risk: |
  - Đây là P0 vì `canonical_decision` là nguồn CAO NHẤT trong SOURCE_PRIORITY (đứng đầu) và có
    1 row `admin_approved` (PL000000000314, T68) đang chờ — nhưng vì query throw + `_safe()`
    nuốt lỗi, nguồn này im lặng không bao giờ chạy. Sửa nó sẽ BẬT lên 1 nguồn level 1.0
    ⇒ phải rà kỹ trước khi bật để không khóa sai tên (rà toàn bộ row canonical_decision).
  - `_safe()` nuốt `sqlite3.Error` là anti-pattern: mọi bug schema sau này cũng sẽ im lặng.
    Đề xuất: _safe() ghi log + audit counter thay vì trả [] im lặng.
---

# T201 — `canonical_decision` DEAD CODE + canonical row A001984

> **P0 — phát hiện khi test end-to-end T199 (2026-09-30).** Khi chèn row `canonical_decision`
> cho A001984 vào DB copy rồi chạy `canonical_lock.build_canonical_lock('靈祐 …')`, entity
> **vẫn không sinh ra** ⇒ phát hiện query nguồn #1 luôn throw.

## 1. Bug

`canonical_lock.py:869-874` (nguồn #1 `canonical_decision`):
```sql
SELECT COALESCE(pd.name_zh, pj.name_zh, cd.entity_ref) AS sf, cd.canonical_name_vi, ...
FROM canonical_decision cd
LEFT JOIN places_dila pd ON pd.dila_id = cd.entity_ref   -- ← SAI: pd.dila_id không tồn tại
LEFT JOIN people     pj ON pj.id      = cd.entity_ref   -- đúng
WHERE COALESCE(pd.name_zh, pj.name_zh) IN (?,…) OR cd.entity_ref IN (?,…)
```

Chạy tay:
```
sqlite3.OperationalError: no such column: pd.dila_id
```

**Root cause:** `places_dila` PK = `id` (TEXT), **không có cột `dila_id`**. Verify:
`PRAGMA table_info(places_dila)` ⇒ PK=['id'], `dila_id` không tồn tại. `people` cũng vậy (PK=id).

`_safe()` (L854-862) bắt `sqlite3.Error` và trả `[]` ⇒ nguồn #1 **luôn rỗng, im lặng**.

**Hệ quả:**
1. Row `admin_approved` `PL000000000314` (T68, `decision_note='Conflict resolved …'`) chưa từng có tác dụng.
2. `canonical_decision` (đầu `SOURCE_PRIORITY`, cao nhất) **trống hoàn toàn** ⇒ mọi tính năng
   admin-decision trong T166/T68 đã triển khai đều im lặng vô hiệu.

## 2. Fix

1. **Sửa SQL**: `pd.dila_id` → `pd.id`. Rà toàn bộ `pd.`/`pj.` reference khác trong `canonical_lock.py`.
2. **Test hồi quy**: `_safe()` nuốt lỗi là anti-pattern — thêm counter/log khi source #1 throw
   (audit:t166 hiện đang pass vì `_safe` trả `[]` ⇒ 0 dòng ⇒ không ai thấy). Đề xuất: thêm
   `LOG.warning` khi `_safe` nuốt lỗi, để bug schema lộ ra.
3. **Rà tên trước khi bật** (quan trọng): bật nguồn #1 ⇒ level 1.0 ⇒ LOCKED. Trước khi sửa,
   rà toàn bộ row `canonical_decision` hiện có để chắc không khóa sai tên (2 row: PL…314 admin_approved, PL…001 auto_transliterate).
4. **Canonical row A001984** (chỉ sau khi #2 fix + test pass):
   ```sql
   INSERT INTO canonical_decision (entity_ref, canonical_name_vi, authority_rank, confidence,
     verification_status, decision_note, evidence_citations, editor, decided_at, updated_at)
   VALUES ('A001984','Quy Sơn Linh Hựu','admin_approved',1.0,'verified',
     'T201 — canonical row A001984 (people.name_zh=靈祐, vnpa.name_vi=Quy Sơn Linh Hựu)',
     '["people A001984"]','admin',datetime('now'),datetime('now'));
   ```

## 2b. Kết quả thực thiên (2026-10-01)

**Fix đã commit:** `canonical_lock.py` `pd.dila_id` → `pd.id` (+ `import logging`, `logger`,
`_SAFE_ERRORS`, `safe_errors()`); `scripts/t166_identity_audit.py` thêm `_check_safe_errors()`.

**Verify trên DB thẪt — `build_canonical_lock('靈祐')` (trước fix: chỉ 1 entity `name_vi_map.auto` 0.7):**
| canonical_id | canonical_value | level | source | LOCKED |
|---|---|---|---|---|
| `A001984` | `Quy Sơn Linh Hựu` | **1.0** | `canonical_decision.admin_approved` | **True** |
| `4bc1b80d` | `Linh Hựu` | 0.7 | `name_vi_map.auto` | False |

`safe_errors()` = `[]` ⇒ không cò lỗi schema.

**Rà 2 row `canonical_decision` cũ TRưỜ bật:**
| entity_ref | canonical_name_vi | rank | hex |
|---|---|---|---|
| `PL000000000314` | `Th? S?t H?i` | `admin_approved` (1.0) | `54683F20533F7420483F69` |
| `PL000000000001` | `Kho?t T?t ?a Qu?c` | `auto_transliterate` | `4B686F3F7420543F74203F612051753F63` |

⚠ **Data corrupt** — chứa byte `?` thật (0x3F), không phải lỗi console.
`is_valid_vi()` trả **False** cho cả hai (chuỗi toàn ASCII) ⇒ **bị lọc đúng**,
không khóa sai tên. **Nhưng phải sửa dử liệu** — task riêng.

**Red-team audit:** rename `places_dila` trong DB copy → `_check_safe_errors()` báo
`[FAIL] canonical_lock nguốn chết do lỗi schema ... no such table: places_dila` ✓

**Regression:** `guard` PASS · `lint` PASS · `test` PASS · `test:t166` 18/18 · `test_t166_matrix` 23/23 ·
`audit:t166` PASS (0 FAIL) · `test:uat` 3/3 PASS · `test:compliance` PASS · `test:gov` 17 passed · `e2e` PASS.

## 3. Verify

- [ ] `build_canonical_lock('靈祐 …')` sinh entity với `source='canonical_decision.admin_approved'`
      level=1.0, `is_lock_flagged(...)=True` ⇒ LOCKED
- [ ] `canonical_decision` A001984 = 1 row `admin_approved`/`verified`/1.0
- [ ] `test_t166_matrix.py` PASS + `test_t166_canonical_lock.py` PASS + `audit:t166` PASS
- [ ] Rà 2 row `canonical_decision` sẵn có: sau khi sửa, chúng có hoạt động không ⇒ nếu
      `PL…314`/`PL…001` bắt đầu khóa sai tên thì dừng, báo Admin
- [ ] `npm run pipeline` PASS

## 4. Ngoài phạm vi

❌ Sửa `_ENTITY_TYPE_BY_SOURCE['canonical_decision']` ('PLACE' cứng) — T200
❌ Xử lý 33 nhóm `dila_id` trùng / `LIMIT 1` không `ORDER BY` — T200
❌ BUG-025 / BUG-026 / T199 TRIM