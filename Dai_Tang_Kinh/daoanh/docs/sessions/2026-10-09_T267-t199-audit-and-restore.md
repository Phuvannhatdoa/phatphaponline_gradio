# Session 2026-10-09 — T267: Audit logic T199 (verify read-only) + khôi phục BUG-025/BUG-026

> Task: `tasks/T267-t199-logic-audit-and-bug025-026-restore.md`
> Agent: claudecode (OpenCode big-pickle) · Admin phê chuẩn đề xuất + quyết định B = "verify rồi mới quyết"

## 1. Mục tiêu & quyết định

1. **Verify read-only** toàn bộ claim của `docs/Mimo-Flash/X-T199…` + `tasks/T199…`so với DB thật.
2. Xác định nguồn gốc + tính chủ ý của việc `people[A001984].name_vi` đổi
   `'Quy Sơn Linh Hựu'` → `'Linh Hựu'` trong ngày 10-02→10-04.
3. **Admin chọn "Verify rồi mới quyết"**: nếu không tìm thấy task/session tài liệu hóa
   chủ ý → **B2 khôi phục BUG-025/BUG-026** (kiểm chứng bằng `scripts/verify_bug025_026.py`).

## 2. Không gian môi trường (gotchas đã vấp)

- Working dir mặc định `daoanh\dashboard`; bash tool phải `workdir` = daoanh.
- `Get-ChildItem`/`node`/`npm`/`rg` là **0-byte shim** (`Cannot run a document in the middle of a pipeline`).
- `python -c` multi-line an toàn = PS here-string `@'...'@` (terminator `'@` riêng dòng) + base64.
- `lineage.db` = **1.707.663.360 B (~1,7 GB)** ⇒ `sqlite3.Connection.backup()` quá chậm
  (298MB/120s, bị kill). Giải pháp: `PRAGMA wal_checkpoint(TRUNCATE)` rồi `shutil.copy2` (convention `person_import_etl.py`).
- glob/grep tool phải truyền `path` FULL (base của glob là `daoanh\dashboard`).
- Git chạy từ toplevel `visjs-app` (AGENTS §13/§14/§17); HEAD dịch chuyển do session song song.

## 3. Verify claim docs/T199 (read-only) — số liệu đo 2026-10-09

HEAD lúc snapshot: `c5e3afb` (T263 done). Max task ID 266 ⇒ **T267** (T266 đã tồn tại).

### 3.1 VNPA status hiện tại (bảng đầy đủ)
```sql
SELECT status, COUNT(*) FROM vn_person_authority GROUP BY status;
-- auto_ttl 589 · alias_vi_suffix 446 · pending 443 · verified 22 · alias_zh_match 7 · Tổng 1507
```
Doc §2 ghi 599/450/448/2/7/**1506** = snapshot **2026-09-30** (stale; verified 22 vs 2 vì sau đó có thêm verified row).

### 3.2 Trailing + guard
```sql
-- name_zh trailing = 0 · name_vi trailing = 0 · marcus label trailing = 0
-- guard: SELECT count(*) FROM vn_person_authority WHERE id LIKE 'alias_%' AND status='verified' → 0
```

### 3.3 canonical_decision (3 row)
| entity_ref | canonical_name_vi | authority_rank | verification_status | decided_at |
|---|---|---|---|---|
| PL000000000314 | (T68) | 1.0 | verified | — |
| PL000000000001 | | auto_transliterate | needs_review | — |
| **A001984** | **Quy Sơn Linh Hựu** | **1.0** | **verified** | **2026-10-01T14:28:56** (editor=admin) |

→ Doc §6 "KHÔNG có row A001984 (defer T201)" giờ vượt qua: T199-apply `9168315…` chạy SAU T201-fix `b9a3216…` nên INSERT thành công (không còn DEAD).

### 3.4 P0 DEAD CODE → đã fix (kiểm code hiện tại)
`canonical_lock.py`:
- dòng **911**: `LEFT JOIN places_dila pd ON pd.id = cd.entity_ref` ✅ (T201 fix, `pd.dila_id`→`pd.id`)
- dòng **873**: `_safe()` bây giờ **log warning** (không còn nuốt im lặng)
- dòng **772**: `SOURCE_LEVELS` (`canonical_decision.admin_approved`: 1.0)
- dòng **797**: `_LOCK_FLAGS`

Commit liên quan: `910d3eb` (T199 plan docs) → `b9a3216` (T201 fix) → `9168315` (T199 APPLY TRIM 60 + canonical A001984) → `9641215` (T206 fix canonical corrupt PL).

### 3.5 Alias khớp people
- alias matched people: **453 row**; lệch `people.name_vi`: **442** (~97,6%) (doc: 438/450 — tỷ lệ giữ).
- A001984: vnpa `alias_A001984` = 'Quy Sơn Linh Hựu' / `alias_vi_suffix`; **people.name_vi = 'Linh Hựu'** ← drift (doc §5 nói 12/450 row khớp, trong đó có A001984).

### 3.6 dila_id trùng + name_vi_map
- dila_id dup: **31** nhóm (doc: 33).
- `name_vi_map` A001984 = **1 row** (doc: 0).
- `person_display_names` A001984 = **0 row** (khớp doc).
- marcus_reference: **18.127** row.
- ⚠ row stale `name_vi_map.id=4689`: `dila_id='A021462', name_vi='Quy Sơn Linh Hựu', confidence=1.0` **VẪN TỒN TẠI** (đã biết T195/T200; search fallback nguy hiểm nhưng theo T267 scope KHÔNG sửa).

### 3.7 Consumer mới của status (bác claim "không consumer nào đọc")
grep `vn_person_authority` + `auto_ttl|alias_vi_suffix|alias_zh_match` (chạy từ daoanh):
- `vnpa_lookup.py` (T200): `VNPA_STATUS_RANK`/rank WHEN 2/3/4 tie-break
- `app.py`: dòng 71, 6154 (comment thứ tự ưu tiên verified>pending>auto_ttl>alias_*, tie-break id), 6162, 15440-15442, 15606-15608
- `tests/test_t227_db_ttl_export.py`, `tests/test_t217_vnpa_etl_preservation.py` (đọc nhãn trong test)

⇒ §2 "không consumer nào đọc auto_ttl/alias_*" **không còn đúng** (các file này đọc làm rank tie-break, vẫn KHÔNG phải thang chất lượng). Ghi chú vào doc.

## 4. Truy vết drift `people[A001984].name_vi` (backup chrono)

| Thời điểm | File | A001984 | A010291 |
|---|---|---|---|
| 2026-09-28 | `lineage_t169_20260928_130129.db` | Quy Sơn Linh Hựu | — |
| 2026-10-01 | `lineage_t199_20261001_141928.db` / `142839.db` | Quy Sơn Linh Hựu | — |
| 2026-10-02 17:26 | `lineage_t215_20261002_172632.db` | Quy Sơn Linh Hựu | — |
| ~10-04 (đầu T233) | `T233-codex-namevi-20261004/lineage-before.db` | **Linh Hựu** ← | — |
| 2026-10-05 07:48 | `lineage_t22ld1_20261005_074831.db` | Linh Hựu | — |
| 2026-10-06 | `lineage_t242_20261006_132928.db`, `lineage_T251_20261006_141338.db`, `t252w3/w4` | Linh Hựu | — |
| hiện tại | `lineage.db` | **Linh Hựu** | **Hy Thiên** |

**Cửa sổ đổi = (10-02 17:26 → 10-04 đầu session T233).**

### 4.1 Loại trừ nguyên nhân (đọc task/session/backup trong cửa sổ)
- **T226** (10-03, TTL profile): đọc DB → không ghi people.
- **T227** (10-04, DB→TTL export): read-only xuất.
- **TRUNG_TEN_HIEN_THI_001-20261003/manifest.json**: chỉ backup file `admin/search_all.html` (sha) — **file-only, không phải DB change**.
- **T233-codex-namevi-20261004** (10-04): task = cột "Codex name_vi tham khảo" cho person import (48.673 ID); manifest `rollback-manifest.json` liệt kê backup **file code** (`api_ttl_profile_v2.py`, `admin/ttl-profile-v2.js`, `admin/monk_ttl_add.html`, `src_python/ttl_db_export.py`, `package.json`) — **additive codex tables, read-only cho people; `lineage-before.db` ĐÃ có 'Linh Hựu'** → đổi xảy ra trước khi session T233 backup, KHÔNG phải T233 làm.
- **person-import-PI-TEST-1/lineage.db**: không có bảng `people` (test fixture) — không dùng được.
- **app.py route 15020-15052** (`name_vi_map` update, approved_by='admin'): chỉ ghi `name_vi_map`, KHÔNG đụng `people`.

**Kết luận:** DB mutation không ghi chép, không session/task nào tài liệu hóa chủ ý. Dấu hiệu mạnh nhất: dạng "tái-import/regenerate `people` từ nguồn tên lõi (pháp danh)" — `'Linh Hựu'` trùng `marcus_reference.label_vi` A001984 (`curated_T51g`), `'Hy Thiên'` trùng pháp danh của A010291. Trạng thái này khớp mô hình B/C (T195) nhưng **vi phạm** trạng thái verified BUG-025/BUG-026 + `verify_bug025_026.py` println.

## 5. Quyết định

**B2 — khôi phục BUG-025/BUG-026** (Admin: "verify rồi mới quyết"; không tìm thấy chủ ý được ghi chép ⇒ mặc định khôi phục).

## 6. Thực thi (đã làm, 2026-10-09)

```sql
PRAGMA wal_checkpoint(TRUNCATE);            -- flame WAL 86KB vào main (an toàn copy)
-- backup full → data/backups/lineage_t267_20261009-152500.db  (1.707.671.552 B)
UPDATE people SET name_vi='Quy Sơn Linh Hựu'  WHERE id='A001984' AND name_vi='Linh Hựu';   -- 1 row
UPDATE people SET name_vi='Thạch Đầu Hy Thiên' WHERE id='A010291' AND name_vi='Hy Thiên';  -- 1 row
```
Backup & snapshot: `lineage_t267_20261009-152500.db` + `lineage_t267_snapshot_20261009-152500.json`
(before/after: people A001984/A010291, count 'Quy Sơn Linh Hựu', 'Thạch Đầu Hy Thiên', vnpa, canonical, name_vi_map 4689).

⚠ Lệnh backup lần đầu dùng `con.backup()` bị timeout 120s (298MB/120s) + để lại `-journal` dở → **đã xóa**; retry bằng checkpoint+copy2 thành công 152500.

## 7. Verify

```
python -X utf8 scripts/verify_bug025_026.py
✅ BUG-025 A021462=Kính Đường Giác Viên · ✅ BUG-025 A001984=Quy Sơn Linh Hựu
✅ BUG-026 A010291=Thạch Đầu Hy Thiên · ✅ BUG-026 A001744=Tuệ Biện
✅ Chỉ 1 row Thạch Đầu Hy Thiên · ✅ Chỉ 1 row Quy Sơn Linh Hựu
🎉 VERIFY PASS
```

## 8. Docs & commit

- Tạo `tasks/T267-t199-logic-audit-and-bug025-026-restore.md` (id T267, status done).
- Fill `tasks/T199.commit_pass2 = 91683157230d3c0849b7d57ff71f2e7918fc9977` + revert sha; §8 [x].
- Banner audit `docs/Mimo-Flash/X-T199-*.md`.
- `docs/tasktodo.md` anchor T267.
- `docs/ROLLBACK.md` row T267.
- `docs/bugs.md` BUG-025/BUG-026: chú thích tái phát → repair T267.
- `docs/Handoff-2026-10-09.md`.
- Regen `data/progress_data.json` + `npm run pipeline` XANH (16:00, guard/dup:ids/audit/lint/test/e2e/e2e:runtime).
- Commit docs lượt 1 (nội dung): `a341caf01ebee48b2f98e790309a94fcf0525c8` (9 file: T267/T199 task, X-T199 banner, tasktodo, ROLLBACK, bugs.md, session, Handoff, progress_data.json); lượt 2 hash-fill: `79679eaeec0079a90a8b1158432fe8bc9957d202` (4 file).

## 9. Ngoài phạm vi / việc chưa xong

- `name_vi_map.id=4689` (A021462 → 'Quy Sơn Linh Hựu', conf 1.0) **KHÔNG được sửa** (T195/T200 đã khoanh; chỉ tài liệu hóa). Cần Admin quyết sớm vì search "Quy Sơn Linh Hựu" vẫn có thể rơi vào row này ở search-path #2 (khi people path #1 không thắng).
- Xác định **kẻ đổi chính xác** trong cửa sổ (person-ttl-draft-20261003, T232-generation-engine-20261004 chưa loại hẳn vì backup lineage DB của chúng chưa probe) — nếu ETL rebuild `people` từ nguồn tên lõi vẫn còn, drift có thể tái phát; cần task riêng thêm guard.
- `docs/db_schema.md` §canonical (A001984) không cần sửa (row vẫn đúng).