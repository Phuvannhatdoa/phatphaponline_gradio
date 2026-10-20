---
id: T199
title: "TRIM khoảng trắng Hán vnpa/marcus (2 + 58 row) + guard alias_vi_suffix; canonical row A001984 DEFER sang T201 (canonical_decision DEAD CODE)"
module: Data / Authority
priority: high
status: pending_admin_apply
owner: claudecode
depends_on: [T166]
supersedes: T179-vnpa-verified-status-data-fix
created: 2026-09-30
updated: 2026-09-30
designed_by: claudecode
handoff_to: Admin
task: tasks/T199-vnpa-canonical-row-and-han-trim.md
deferred_task: tasks/T201-canonical-lock-dila-id-dead-code-fix.md
followup_task: tasks/T200-vnpa-dila-id-duplicate-limit1.md
plan_approved_at: "2026-09-30 (Admin: cần 1 canonical row, phê chuẩn đường canonical_decision.admin_approved; TRIM hết 58 marcus_reference.label)"
---

# T199 — TRIM khoảng trắng Hán vnpa/marcus (data-only, 0 code)

> **Thay thế** `T179-vnpa-verified-status-data-fix.md` (2026-09-26, `id: T179`, untracked).
> Lý do bác + giữ nguyên kế hoạch cũ ở §5.
>
> ⚠ **P0 phát hiện khi test end-to-end:** phần canonical row **đã defer sang T201** vì
> `canonical_decision` là **DEAD CODE** (xem §2).

## 0. P0 BLOCKER — `canonical_decision` là DEAD CODE

Đã chèn row `A001984` vào DB copy rồi chạy `canonical_lock.build_canonical_lock('靈祐 …')` —
entity **vẫn không sinh ra** (chỉ có `name_vi_map.auto` id=`4bc1b80d` level 0.7):

```
id=4bc1b80d  src_form='靈祐'  canonical='Linh Hữu'  lvl=0.7  src=name_vi_map.auto  LOCKED=False
```

Chạy tay query nguồn #1:
```
sqlite3.OperationalError: no such column: pd.dila_id
```

**Nguyên nhân** — `canonical_lock.py:871`:
```python
LEFT JOIN places_dila pd ON pd.dila_id = cd.entity_ref   # ← SAI
```
`places_dila` PK = **`id`**, không có cột `dila_id` (verify `PRAGMA table_info`; `people` cũng vậy).
`_safe()` (L854-862) nuốt `sqlite3.Error` ⇒ nguồn #1 **chưa bao giờ chạy được**.

⇒ Row `admin_approved` `PL000000000314` (T68) cũng **chưa từng** có tác dụng.
⇒ Nguồn **cao nhất** trong `SOURCE_PRIORITY` đang trống hoàn toàn.
⇒ **Fix + chèn row A001984 → task T201** (`tasks/T201-canonical-lock-dila-id-dead-code-fix.md`).

## 1. Vì sao kế hoạch T179 cũ bị bác

| # | Claim T179 | Thực tế verify read-only 2026-09-30 |
|---|---|---|
| P0-1 | `id: T179` | **trùng** — `tasks/T179-per-rule-fingerprint-phase8.md` đã tồn tại, DONE (commit `2e252d0`→`b46560a`) |
| P0-2 | `vn_person_authority` row `person_id='A001984'` | Bảng **không có cột `person_id`** (PK = `id`). Row = `id='alias_A001984'`, `dila_id='A001984'` ⇒ query như T179 viết sẽ `no such column` |
| P0-3 | `status='alias_vi_suffix'` là lỗi → nâng lên `verified` | `id`-prefix ↔ `status` ánh xạ **1:1**: `alias_*` (450 `alias_vi_suffix` + 7 `alias_zh_match`) vs khác (599 `auto_ttl` + 448 `pending` + **2 `verified`**). **438/450 alias row khác `people.name_vi` — đúng thiết kế** (alias giữ tên đầy đủ có tiền tố triều đình; `people.name_vi` giữ tên lõi) |
| P0-4 | status sai ⇒ A001984 không đạt LOCK threshold | `canonical_lock.py:901` là `SELECT … WHERE status='verified'` ⇒ chỉ trả **2 row** (A009460 `Đơn Hà Thiên Nhiên`, A010616 `Thúy Vi Vô Học`). A001984 **chưa từng** là nguồn 0.95 — vắng do cấu trúc SELECT, **không phải do trim** |
| P1-1 | trailing space trong **giá trị VI** | `name_vi` trailing = **0/1506**. Thật là `name_zh` 2 row + `marcus_reference.label` 58 row |
| P1-2 | `people.name_vi` A001984 cần sửa | `people.name_vi` = `vnpa.name_vi` = `Quy Sơn Linh Hựu` — A001984 thuộc **12/450** row khớp ⇒ không có regression tên |
| P1-3 | — | `name_vi_map` A001984 = **0 row** · `person_display_names` A001984 = **0 row** ⇒ đường ưu tiên cao đang trống, tác động lớn hơn doc cũ tưởng |

**Đối chiếu:** T195 đã ghi đúng chỗ khoảng trắng (`靈祐 ` ở `marcus_reference.label` **và** `vn_person_authority.name_zh`) — T179 là bản restatement sai lệch.

## 2. Ngữ nghĩa `vn_person_authority.status` (hiểu sai sẽ bẻ identity)

`status` là **nhãn nguồn gốc dòng dữ liệu**, KHÔNG phải thang chất lượng:

| `id` prefix | `status` | Rows | Nghĩa |
|---|---|---|---|
| `alias_*` | `alias_vi_suffix` | 450 | row alias, tên Việt **ghép** bằng tiền/hậu tố Hán-Việt |
| `alias_*` | `alias_zh_match` | 7 | row alias, khớp qua tên Hán |
| khác | `auto_ttl` | 599 | tự sinh từ TTL |
| khác | `pending` | 448 | chờ duyệt |
| khác | `verified` | **2** | **hạng duy nhất `canonical_lock` đọc** (level 0.95) |

`canonical_lock.SOURCE_LEVELS` chỉ có `'vn_person_authority.verified': 0.95`; `_LOCK_FLAGS` chỉ có
`'vn_person_authority.verified'`. `git grep` toàn bộ `*.py`: **không consumer nào** đọc
`alias_vi_suffix` / `alias_zh_match` / `auto_ttl` ⇒ 4 giá trị này là **nhãn mô tả cách dòng sinh ra**,
không phải "chưa xác minh".

## 3. Scope (Admin đã phê chuẩn, đã loại canonical row → T201)

### 3.1 TRIM khoảng trắng Hán

| Bảng | Cột | Rows | Ghi chú |
|---|---|---|---|
| `vn_person_authority` | `name_zh` | **2** | `alias_A001984`=`'靈祐 '` (3→2) · `alias_A004697`=`'師範   '` (5→2) |
| `marcus_reference` | `label` | **58** | display-only · gồm `A001984`=`'靈祐 '` (3→2) |

`name_vi` **không đụng** (đã sạch 1506/1506). An toàn: `name_zh`/`label` là khoá ghép Hán;
`'靈祐 '` ≠ `'靈祐'` nên TRIM chỉ làm Hán khớp đúng, **không** đụng identity.

### 3.2 Guard chống tái phát P0-3
`SELECT count(*) FROM vn_person_authority WHERE id LIKE 'alias_%' AND status='verified'` = **0**
(đã đúng từ trước; script **từ chối** `--apply` nếu ≠ 0).

### 3.3 Documentation (0 code) → `docs/db_schema.md`
1. Enum `vn_person_authority.status` (§2) + nhấn mạnh `alias_*` = nhãn nguồn gốc
2. `dila_id` **KHÔNG unique** — 33 nhóm 2–3 dòng; `app.py:5964` / `app.py:12841` dùng
   `LIMIT 1` **không `ORDER BY`** ⇒ chọn dòng không xác định → **T200**
3. **Caveat `canonical_decision` DEAD** — `canonical_lock.py:871` `pd.dila_id` sai (PK=`id`) → **T201**

## 4. Thực thi

```bash
python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --stats
python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --dry-run   # Admin duyệt danh sách
python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --apply     # backup + ghi
python -X utf8 scripts/t199_vnpa_trim_and_canonical.py --revert    # rollback theo snapshot
```

Đã test end-to-end trên **DB copy** (`--db-path`): apply 60 row + verify 6 assert PASS; revert OK.

## 5. Kế hoạch cũ bị bác (giữ lịch sử)

T179 (2026-09-26) đề xuất `UPDATE status='verified'` cho **toàn bộ 450 row** `alias_vi_suffix`
sau khi Admin duyệt danh sách. **Bác** vì:
1. `status` là nhãn nguồn gốc, không phải hạng chất lượng
2. **438/450 lệch `people.name_vi`** ⇒ `canonical_lock` (0.95 = LOCKED) khóa 438 tên sai
3. `LIMIT 1` không `ORDER BY` ở 33 nhóm trùng ⇒ kết quả **không xác định**
4. Blast radius khổng lồ so với **1 người** Admin thực sự cần

Thay bằng: TRIM 60 row Hán (T199) + canonical row A001984 (T201, sau khi sửa DEAD code).

## 6. Acceptance

- [ ] Admin `APPROVED` danh sách TRIM trong `--dry-run` — **bắt buộc trước `--apply`**
- [ ] backup `data/backups/lineage_t199_<ts>.db` tồn tại
- [ ] `name_zh` trailing = 0 · `marcus_reference.label` trailing = 0 · `name_vi` trailing vẫn 0
- [ ] **guard**: alias+verified = **0**
- [ ] `people.name_vi` A001984 = `Quy Sơn Linh Hựu` **không đổi**
- [ ] `canonical_decision` **KHÔNG** có row A001984 (đã defer T201)
- [ ] CASE 2/3/4 bất biến
- [ ] `pytest tests/test_t166_matrix.py -q` PASS **23/23 trước và sau** — đã verify PASS sẵn ở HEAD ⇒ **regression guard, KHÔNG phải fix-verifier**
- [ ] `docs/db_schema.md` có enum + 3 ghi chú (§3.3)
- [ ] script + lệnh revert có trong ROLLBACK row

## 7. Ngoài phạm vi

❌ Flip status 450 row (bị bác, §5) · ❌ TRIM `name_vi` (đã sạch)
❌ INSERT canonical_decision (DEAD CODE, §0 → **T201**) · ❌ Sửa `canonical_lock.py:871` → **T201**
❌ Sửa `LIMIT 1` không `ORDER BY` → **T200** · ❌ BUG-026 (A010291) · ❌ BUG-025 stale rows