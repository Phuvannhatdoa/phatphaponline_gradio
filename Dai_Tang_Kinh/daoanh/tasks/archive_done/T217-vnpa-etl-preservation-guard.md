---
id: T217
title: "VNPA ETL Preservation Guard — scoped DELETE + curated dila_id/status preservation"
module: Data / Canonical Identity
priority: high
status: done
created: 2026-10-02
updated: 2026-10-07
owner: claudecode
depends_on: [T215, T214, T212]
done_when: |
  ETL scripts/etl_ttl_person_authority.py dùng scoped DELETE theo ttl_filename thay vì DELETE toàn bộ,
  snapshot dila_id/status trước DELETE, restore curated values sau INSERT; test 19/19 PASS;
  dry-run giữ 33/33 dila_id T215, 0 conflict, production DB SHA unchanged.
---

# T217 — VNPA ETL Preservation Guard

**ID:** T217-VNPA-ETL-PRESERVE-CURATED-DILA-ID-01  
**Admin spec:** T216 (renumbered T217 — T216 đã bị claim bởi cloud-session-chain commit `1283ee9`)  
**Ngày:** 2026-10-02  
**Trạng thái:** ✅ DONE  
**Phụ thuộc:** T215, T214, T212

---

## Mô tả

ETL `scripts/etl_ttl_person_authority.py` thực hiện `DELETE FROM vn_person_authority` toàn bộ (1503 rows) nhưng chỉ tạo lại 16 rows từ `data/ttl/old/`. Hậu quả: 33 dila_id vừa được restore bởi T215 bị mất hoàn toàn mỗi khi ETL chạy.

**Root cause:** Full table DELETE thay vì Scoped DELETE theo ttl_filename.

---

## Fix đã thực hiện

**File:** `scripts/etl_ttl_person_authority.py`

1. **`--db=<path>` override** — cho phép test trên DB copy, không động production
2. **Scoped DELETE** — `DELETE FROM vn_person_authority WHERE ttl_filename IN (ttl_keys)` thay vì `DELETE FROM vn_person_authority`
3. **Snapshot trước DELETE** — ghi lại `dila_id` (non-empty) và `status` (non-'pending') của rows trong scope
4. **Restore sau INSERT** — phục hồi curated values; CASE E (conflict) → giữ curated, log warning

---

## Test

**File:** `tests/test_t217_vnpa_etl_preservation.py`

- 15 unit tests (Cases A-M + status preservation): ✅ PASS
- 4 integration tests (G: 33 rows survive, H: T212 aliases, I: idempotency, production SHA): ✅ PASS
- **Tổng: 19/19 PASS**

---

## Dry-run kết quả

| Metric | Kết quả |
|--------|---------|
| T215 33-row preservation | 33/33 ✓ |
| T212 aliases resurrected | 0/4 ✓ |
| dila_id conflicts | 0 |
| Production DB SHA | Unchanged ✓ |
| Total rows | 1503 → 1496 (-7 stale scope rows) |

---

## Regression

| Test | Kết quả |
|------|---------|
| T217 19/19 | ✅ PASS |
| T200 25/25 | ✅ PASS |
| T166 audit | ✅ PASS |
| Translation | ⚠️ 25/27 (2 FAIL pre-existing) |

---

## NOT DONE (ngoài scope — Admin trigger needed)

- D3: A021395 canonical choice (bao_an_phap_dien vs tu_to_phap_dien)
- D4: dam_chau_bao_cai_uoc wrong-person fix (A010511)
- T213: Classification của 211 dila_id='' rows
- T165-P8: FROZEN
