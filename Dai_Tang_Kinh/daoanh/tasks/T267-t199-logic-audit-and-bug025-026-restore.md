---
id: T267
title: "Audit logic docs/T199 (verify read-only) + khôi phục BUG-025/BUG-026 (people A001984 + A010291 bị ETL ghi đè tên lõi)"
module: Data / Authority
priority: high
status: done
owner: claudecode
depends_on: [T199, T201, T200, T166]
created: 2026-10-09
updated: 2026-10-09
designed_by: claudecode
approved_by: Admin
plan_approved_at: "2026-10-09 (Admin phê chuẩn đề xuất: verify T199 logic read-only; quyết định B = 'verify rồi mới quyết')"
blocking_finding: |
  T199 acceptance "people.name_vi A001984 không đổi" đã bị VI PHẠM trong khoảng
  **10-02 17:26 → 10-04 (đầu session T233)**: `people[A001984].name_vi` đổi
  `'Quy Sơn Linh Hựu'` → `'Linh Hựu'`, `people[A010291].name_vi` đổi
  `'Thạch Đầu Hy Thiên'` → `'Hy Thiên'` — cùng root-cause: một DB mutation không
  ghi chép (sau 10-02), có dấu hiệu của tái-import/regenerate `people` từ nguồn
  tên lõi (pháp danh) thay vì tên hiển thị đã verify BUG-025/BUG-026.
  KHÔNG tìm thấy task/session nào trong cửa sổ tài liệu hóa việc đổi
  (T226 TTL-only, TRUNG_TEN file-only manifest, T233 codex dry-run, app.py routes
  chỉ ghi name_vi_map, person-import chỉ vn_person_authority).
  Hệ quả sai: search "Quy Sơn Linh Hựu"/"Thạch Đầu Hy Thiên" rơi vào row stale
  `name_vi_map.id=4689` (A021462, conf 1.0) / không còn khớp people;
  `scripts/verify_bug025_026.py` (regression guard của BUG-025+BUG-026) FAIL.
resolved: |
  Quyết định **B2 — khôi phục BUG-025/BUG-026** (verify xong, không tìm thấy chủ ý
  được tài liệu hóa ⇒ theo đề xuất mặc định). Backup
  `data/backups/lineage_t267_20261009-152500.db` (full snapshot 1.707.671.552 B,
  trước mọi thay đổi) + snapshot JSON
  `data/backups/lineage_t267_snapshot_20261009-152500.json`.
  UPDATE (1 transaction) `people A001984`:'Linh Hựu'→'Quy Sơn Linh Hựu' + `A010291`:'Hy Thiên'→'Thạch Đầu Hy Thiên'.
  Verify: `scripts/verify_bug025_026.py` → **VERIFY PASS** (4/4 people + không trùng tên).
done_when: |
  Audit logic docs/T199 xong (verify read-only, bằng chứng §1);
  quyết định B2 đã chốt; DB restored theo bugs.md BUG-025/BUG-026;
  backup + snapshot JSON tồn tại; verify_bug025_026.py PASS;
  tasks/T199.commit_pass2 + revert filled (91683157230d3c0849b7d57ff71f2e7918fc9977);
  tasktodo + ROLLBACK + session + Handoff + bugs.md + dashboard regen;
  `npm run pipeline` XANH; commit an toàn (CAS ref).
revert: |
  DB: khôi phục `data/backups/lineage_t267_20261009-152500.db` (khi DB đang dừng).
  Doc: `git revert --no-edit <sha_docs_T267> <sha_hashfill_T267>` (docs-only, 0 code, 0 DB).
former_ids: []
outcome: |
  Hoàn thành 2026-10-09. Đầy đủ bằng chứng audit trong
  `docs/sessions/2026-10-09_T267-t199-audit-and-restore.md` + ROLLBACK + Handoff.
---

# T267 — Audit logic T199 (verify read-only) + khôi phục BUG-025/BUG-026

## 1. Audit logic docs/T199 (verify read-only) — kết luận

`<details><summary>Bảng đối chiếu 12 claim (đầy đủ truy vết tại session log)</summary>`

| # | Claim docs/T199 | Verify 2026-10-09 | Kết luận |
|---|---|---|---|
| P0-1 | `canonical_decision` DEAD CODE (`canonical_lock.py:871` `pd.dila_id`, places_dila PK=`id`) | TRUE **tại thời điểm viết**; **T201 đã fix** `b9a32166f6d0fc3b2729fe41559cd4a23af70688` — code hiện dòng 911 `LEFT JOIN places_dila pd ON pd.id = cd.entity_ref`, `_safe()` (873) giờ log warning | ✅ ĐÚNG (apply đã chạy sau fix) |
| P0-2 | canonical A001984 không tồn tại lúc viết | Row `canonical_decision` A001984 = 'Quy Sơn Linh Hựu' admin_approved/verified 1.0 editor admin `2026-10-01T14:28:56` (đã INSERT bởi T199-apply `9168315…` chạy sau T201-fix) | ✅ nay đã tồn tại (đúng thiết kế) |
| P0-3 | `status` = nhãn nguồn gốc; 4 class | vnpa hiện tại: auto_ttl **589** / alias_vi_suffix **446** / pending **443** / verified **22** / alias_zh_match **7** = **1507** (snapshot doc 599/450/448/**2**/7/1506 = 2026-09-30) | ✅ cấu trúc đúng; số liệu cũ |
| P0-4 | 438/450 alias khác people.name_vi | alias khớp people **453** row, lệch name_vi **442** (~97,6%) | ✅ giữ (~97,6%) |
| §4 | no consumer đọc auto_ttl/alias_* | **SAI nay**: `vnpa_lookup.py` (T200) rank WHEN 2/3/4 + `app.py` 71/6154/6162/15440-15442/15606-15608 + tests đọc 4 nhãn (rank tie-break, không phải chất lượng) | ⚠ ghi chú cập nhật |
| §3.3 | dila_id trùng 33 nhóm | hiện **31** nhóm | ⚠ khác nhẹ (loại 2) |
| P1-3 | name_vi_map A001984 = 0 row | hiện **1 row** | ⚠ khác nhẹ |
| §8 item | `people.name_vi` A001984 không đổi | **VI PHẠM**: A001984='Linh Hựu' (drift ~10-02→10-04), A010291='Hy Thiên' → **T267 restore B2** | ❌ → đã sửa |
| BUG-025/026 | people = Kính Đường Giác Viên / Quy Sơn Linh Hựu / Thạch Đầu Hy Thiên / Tuệ Biện | A021462 ✅, A001744 ✅; A001984 + A010291 đã bị drift → restore | ❌ → đã sửa |

`</details>`

## 2. Truy vết cửa sổ đổi `people.name_vi` (backup chrono)

| Thời điểm | Backup | A001984 |
|---|---|---|
| 2026-09-28 | `lineage_t169_20260928_130129.db` | `Quy Sơn Linh Hựu` |
| 2026-10-01 | `lineage_t199_20261001_141928.db` / `142839.db` | `Quy Sơn Linh Hựu` |
| 2026-10-02 17:26 | `lineage_t215_20261002_172632.db` | `Quy Sơn Linh Hựu` |
| **10-02 17:26 → 10-04 (T233 session)** | `T233-codex-namevi-20261004/lineage-before.db` | **`Linh Hựu`** ← BẮT ĐẦU ĐỔI |
| 2026-10-05 07:48 | `lineage_t22ld1_20261005_074831.db` | `Linh Hựu` |
| 2026-10-06 | `lineage_t242_20261006_132928.db`, `T251…141338.db`, `t252w3/w4` | `Linh Hựu` |
| 2026-10-08 | `T265-pre-support-20261008…db` | `Linh Hựu` |

Loại trừ nguyên nhân: T226 (10-03, TTL read-only) · TRUNG_TEN_HIEN_THI_001-20261003
(manifest chỉ backup file `admin/search_all.html`) · T233-codex (dry-run, manifest
file-only, additive codex tables) · app.py routes (15020-15052 chỉ `name_vi_map`) ·
person-import ETL (chỉ `vn_person_authority`). **DB mutation không ghi chép.

## 3. Thực thi B2 (đã làm)

```bash
# backup full + snapshot
cp  data/lineage.db → data/backups/lineage_t267_20261009-152500.db   (1.707.671.552 B, checkpoint TRUNCATE trước)
snapshot → data/backups/lineage_t267_snapshot_20261009-152500.json

UPDATE people SET name_vi='Quy Sơn Linh Hựu'  WHERE id='A001984' AND name_vi='Linh Hựu';    -- 1 row
UPDATE people SET name_vi='Thạch Đầu Hy Thiên' WHERE id='A010291' AND name_vi='Hy Thiên';   -- 1 row
```

## 4. Verify

```bash
python -X utf8 scripts/verify_bug025_026.py
# 🎉 VERIFY PASS — BUG-025 + BUG-026 DONE (4/4 people đúng, không trùng tên)
```

## 5. Ngoài phạm vi

❌ sửa row stale `name_vi_map.id=4689` (A021462→'Quy Sơn Linh Hựu', conf 1.0) —
đã biết từ T195/T200, chỉ tài liệu hóa, KHÔNG ghi DB (giữ nguyên quyết định cũ). Nếu
sau này search vẫn rơi vào row này, tách task riêng (không sửa trong session song song).