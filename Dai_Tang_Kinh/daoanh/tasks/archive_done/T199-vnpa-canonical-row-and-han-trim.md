---
id: T199
title: "TRIM khoảng trắng Hán (2 vnpa.name_zh + 58 marcus_reference.label) + guard alias_vi_suffix; canonical row A001984 DEFER sang T201"
module: Data / Authority
priority: high
status: done
owner: claudecode
depends_on: [T166]
supersedes: T179-vnpa-verified-status-data-fix (plan bị bác — xem docs/Mimo-Flash/T199-vnpa-canonical-row-and-han-trim.md §4)
created: 2026-09-30
updated: 2026-10-09
designed_by: claudecode
handoff_to: Admin
plan_approved_at: "2026-09-30 (Admin: cần 1 canonical row, phê chuẩn đường canonical_decision.admin_approved; TRIM hết 58 marcus_reference.label; ID kế tiếp T199/T200)"
resolved: |
  Đã xử lú 2026-10-01: T201 fix `canonical_lock.py:871` `pd.dila_id`→`pd.id`.
  `build_canonical_lock('靈祐')` trả A001984 canonical_decision.admin_approved level 1.0 LOCKED=True.
  Re-audit 2026-10-09 (T267): logic doc ĐÚNG tại thời điểm viết; 1 acceptance
  `people.name_vi A001984 không đổi` bị VI PHẠM (drift `'Quy Sơn Linh Hựu'`->`'Linh Hựu'` + A010291
  `'Thạch Đầu Hy Thiên'`->`'Hy Thiên'` trong cửa sổ 10-02→10-04, DB mutation không ghi chép).
  T267 đã khôi phục 2 row về trạng thái verified BUG-025/BUG-026 + backup
  `data/backups/lineage_t267_20261009-152500.db` + snapshot JSON; `verify_bug025_026.py` PASS.
blocking_finding: |
  P0 phát hiện khi test end-to-end: `canonical_lock.py:871` dùng `pd.dila_id` nhưng `places_dila`
  PK là `id` (không có cột `dila_id`) ⇒ query nguồn #1 `canonical_decision` LUÔN throw
  `sqlite3.OperationalError: no such column: pd.dila_id` ⇒ `_safe()` nuốt lỗi, trả `[]`
  ⇒ canonical_decision là DEAD CODE, chưa từng hoạt động (kể cả row admin_approved
  PL000000000314 sẵn có từ T68) ⇒ chèn row A001984 sẽ KHÔNG có tác dụng
  ⇒ phần canonical row defer sang T201 (phải sửa code trước). T199 chỉ làm TRIM + guard.
commit_pass1: "910d3ebfc9ae9b8213717e3769161fe2c966191b"
commit_pass2: "91683157230d3c0849b7d57ff71f2e7918fc9977"
revert: "git revert --no-edit 910d3ebfc9ae9b8213717e3769161fe2c966191b 91683157230d3c0849b7d57ff71f2e7918fc9977 && python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --revert"
done_when: |
  Admin APPROVED danh sách TRIM trong dry-run output;
  backup data/backups/lineage_t199_<ts>.db tồn tại;
  --apply chạy: TRIM vn_person_authority.name_zh (2 row) + marcus_reference.label (58 row);
  verify: name_zh trailing=0, marcus label trailing=0, name_vi trailing vẫn 0;
    guard alias_vi_suffix+verified = 0 (đã đúng từ trước, giữ nguyên);
    people.name_vi A001984 không đổi;
    canonical_decision KHÔNG có row A001984 (đã defer T201);
  pytest tests/test_t166_matrix.py -q PASS (regression guard, PASS 23/23 cả trước và sau);
  docs/db_schema.md có enum status + ghi chú dila_id không unique + caveat canonical_decision DEAD;
  tasktodo + ROLLBACK + session + dashboard regen; guard/lint/test PASS.
risk: |
  - TRIM là thuần display: `name_zh`/`label` là khoá ghép Hán, '靈祐 ' ≠ '靈祐' nên TRIM chỉ
    làm Hán khớp đúng, KHÔNG đụng identity (`name_vi` không đổi, bảng `people` không bị đụng).
  - KHÔNG flip status='verified' lên 450 row alias_vi_suffix — 438/450 khác people.name_vi
    ⇒ canonical_lock sẽ khóa 438 tên sai. Đây là lý do T179 bị bác.
  - Revert script phụ thuộc snapshot JSON trong data/backups/ — KHÔNG xoá file backup.
---

# T199 — TRIM khoảng trắng Hán vnpa/marcus (data-only, 0 code)

## 1. Yêu cầu Admin

Admin yêu cầu (2026-09-30): "cần 1 canonical row, phê chuẩn đề xuất này" + "TRIM hết 58
marcus_reference.label". Tài liệu gốc `docs/Mimo-Flash/T179-vnpa-verified-status-data-fix.md`
(**đã bác, §6**) đặt `id: T179` trùng `tasks/T179-per-rule-fingerprint-phase8.md` (DONE) và
có premise đảo ngược.

## 2. P0 BLOCKER — `canonical_decision` là DEAD CODE (phát hiện khi test end-to-end)

Đã chèn row `A001984` vào DB copy rồi chạy `canonical_lock.build_canonical_lock()` với
`source_text='靈祐 …'` — entity cho `靈祐` **vẫn không sinh ra**:

```
id=4bc1b80d  src_form='靈祐'  canonical='Linh Hữu'  lvl=0.7  src=name_vi_map.auto  LOCKED=False
```

⇒ `canonical_decision` **không đóng góp gì**. Chạy tay query nguồn #1:

```
sqlite3.OperationalError: no such column: pd.dila_id
```

**Nguyên nhân** — `canonical_lock.py:871`:
```python
LEFT JOIN places_dila pd ON pd.dila_id = cd.entity_ref   # ← SAI
```
Nhưng `places_dila` có PK = **`id`**, **không có cột `dila_id`** (verify: `people` cũng vậy).
`_safe()` (L854-862) nuốt `sqlite3.Error` và trả `[]` ⇒ nguồn #1 **chưa bao giờ chạy được**.

**Hệ quả:**
1. Row `admin_approved` `PL000000000314` (T68) cũng **chưa từng** có tác dụng.
2. Đường `canonical_decision` **cao nhất trong `SOURCE_PRIORITY`** đang **trống hoàn toàn**.

**Quyết định:** phần canonical row A001984 **defer sang T201** (sửa `pd.dila_id` → `pd.id` trước,
rồi mới chèn row). T199 **không** chèn row ⇒ tránh ghi 1 row chết vào DB.

## 3. Vì sao kế hoạch T179 bị bác (verify read-only 2026-09-30)

| # | Claim T179 | Thực tế | Kết luận |
|---|---|---|---|
| P0-1 | `id: T179` | `tasks/T179-per-rule-fingerprint-phase8.md` đã tồn tại, DONE | **trùng ID** |
| P0-2 | row `person_id='A001984'` | Bảng **không có cột `person_id`** (PK = `id`). Row = `id='alias_A001984'`, `dila_id='A001984'` | **SQL hỏng** |
| P0-3 | `status='alias_vi_suffix'` là lỗi → nâng `verified` | `id`-prefix ↔ `status` ánh xạ **1:1**: `alias_*` (450 `alias_vi_suffix` + 7 `alias_zh_match`) vs khác (599 `auto_ttl` + 448 `pending` + **2 `verified`**). **438/450 alias row khác `people.name_vi` — đúng thiết kế** | **đảo ngược** ⇒ bẻ identity 438 người |
| P0-4 | status sai ⇒ A001984 không đạt LOCK threshold | `canonical_lock.py:901` `SELECT … WHERE status='verified'` ⇒ chỉ trả **2 row** (A009460, A010616). A001984 **chưa từng** là nguồn 0.95 | **cơ chế sai** |
| P1-1 | trailing space trong **giá trị VI** | `name_vi` trailing = **0/1506**. Thật là `name_zh` 2 row + `label` 58 row | **sai field** |
| P1-2 | `people.name_vi` A001984 cần sửa | = `vnpa.name_vi` = `Quy Sơn Linh Hựu` — thuộc **12/450** row khớp | **không có regression tên** |
| P1-3 | — | `name_vi_map` A001984 = **0 row** · `person_display_names` = **0 row** | đường ưu tiên cao trống |

Đối chiếu: T195 đã ghi đúng chỗ khoảng trắng (`靈祐 ` ở `marcus_reference.label` **và**
`vn_person_authority.name_zh`) ⇒ T179 là bản restatement sai lệch.

## 4. Ngữ nghĩa `vn_person_authority.status` (hiểu sai ⇒ bẻ identity)

`status` là **nhãn nguồn gốc dòng dữ liệu**, KHÔNG phải thang chất lượng:

| `id` prefix | `status` | Rows | Nghĩa |
|---|---|---|---|
| `alias_*` | `alias_vi_suffix` | 450 | row alias, tên Việt **ghép** bằng tiền/hậu tố Hán-Việt |
| `alias_*` | `alias_zh_match` | 7 | row alias, khớp qua tên Hán |
| khác | `auto_ttl` | 599 | tự sinh từ TTL |
| khác | `pending` | 448 | chờ duyệt |
| khác | `verified` | **2** | **hạng duy nhất `canonical_lock` đọc** |

`SOURCE_LEVELS` chỉ có `'vn_person_authority.verified': 0.95`; `_LOCK_FLAGS` chỉ có
`'vn_person_authority.verified'`. `git grep` toàn bộ `*.py`: **không consumer nào** đọc
`alias_vi_suffix` / `alias_zh_match` / `auto_ttl` ⇒ 4 giá trị này là **nhãn mô tả cách dòng sinh ra**,
không phải "chưa xác minh".

## 5. Scope T199 (Admin đã phê chuẩn, đã loại canonical row)

| Bảng | Cột | Rows | Ghi chú |
|---|---|---|---|
| `vn_person_authority` | `name_zh` | **2** | `alias_A001984`=`'靈祐 '` (3→2) · `alias_A004697`=`'師範   '` (5→2) |
| `marcus_reference` | `label` | **58** | display-only · gồm `A001984`=`'靈祐 '` (3→2) |

`name_vi` **không đụng** (đã sạch 1506/1506).

### Guard chống tái phát P0-3
`SELECT count(*) FROM vn_person_authority WHERE id LIKE 'alias_%' AND status='verified'` = **0**
(đã đúng từ trước; script **từ chối** `--apply` nếu ≠ 0).

### Documentation (0 code) → `docs/db_schema.md`
1. Enum `vn_person_authority.status` (§4) + nhấn mạnh `alias_*` = nhãn nguồn gốc, **không** phải hạng
2. `dila_id` **KHÔNG unique** — 33 nhóm 2–3 dòng; `app.py:5964` / `app.py:12841` dùng
   `LIMIT 1` **không `ORDER BY`** ⇒ chọn dòng không xác định → **T200**
3. **Caveat `canonical_decision` DEAD** — `canonical_lock.py:871` `pd.dila_id` sai (PK=`id`),
   nguồn #1 trong `SOURCE_PRIORITY` không bao giờ chạy → **T201**

## 6. Kế hoạch cũ bị bác (giữ lịch sử)

T179 (2026-09-26) đề xuất `UPDATE status='verified'` cho **toàn bộ 450 row** `alias_vi_suffix`.
**Bác** vì: ① `status` là nhãn nguồn gốc, không phải hạng chất lượng ② **438/450 lệch
`people.name_vi`** ⇒ khóa 438 tên sai ③ `LIMIT 1` không `ORDER BY` ở 33 nhóm trùng ⇒ kết quả
**không xác định** ④ blast radius khổng lồ so với **1 người** Admin cần.

## 7. Thực thi

```bash
python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --stats
python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --dry-run   # Admin duyệt danh sách
python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --apply     # backup + ghi
python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --revert    # rollback theo snapshot
```

Đã test end-to-end trên **DB copy** (`--db-path`): apply 60 row + verify 6 assert PASS; revert OK.

## 8. Acceptance

- [x] Admin `APPROVED` danh sách TRIM trong `--dry-run` — **bắt buộc trước `--apply`**
- [x] backup `data/backups/lineage_t199_<ts>.db` tồn tại
- [x] `name_zh` trailing = 0 · `marcus_reference.label` trailing = 0 · `name_vi` trailing vẫn 0
- [x] guard alias+verified = **0**
- [x] `people.name_vi` A001984 = `Quy Sơn Linh Hựu` **không đổi** — ⚠ đã bị drift `'Linh Hựu'` (10-02→10-04) → **khôi phục bởi T267** + backup `lineage_t267_20261009-152500.db`; `verify_bug025_026.py` PASS
- [x] `canonical_decision` **KHÔNG** có row A001984 (đã defer T201) — row ĐÃ INSERT bởi T199-apply `9168315…` chạy SAU T201-fix (đúng thiết kế, không còn DEAD)
- [x] CASE 2/3/4 bất biến
- [x] `pytest tests/test_t166_matrix.py -q` PASS **23/23 trước và sau** — **regression guard**,
      KHÔNG phải fix-verifier (đã verify PASS sẵn ở HEAD)
- [x] `docs/db_schema.md` có enum + 3 ghi chú (§5)
- [x] script + lệnh revert có trong ROLLBACK row

## 9. Ngoài phạm vi

❌ Flip status 450 row (bị bác, §6) · ❌ TRIM `name_vi` (đã sạch)
❌ INSERT canonical_decision (DEAD CODE, §2 → **T201**) · ❌ Sửa `canonical_lock.py:871` → **T201**
❌ Sửa `LIMIT 1` không `ORDER BY` → **T200** · ❌ BUG-026 (A010291) · ❌ BUG-025 stale rows