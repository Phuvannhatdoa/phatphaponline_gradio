# DEV-REPORT — T387 SQLite backup API + safe VPS sync

- **Task:** T387 (`tasks/T387-sqlite-backup-api-and-safe-sync.md`), parent T382
- **Developer:** OpenCode (deepseek-v4.1-flash-free)
- **Timestamp:** 2026-10-25
- **Status:** DEV_DONE (code complete, tests pass) — awaiting `daoanh-qa` + Admin DONE
- **Commit:** NOT committed (Admin requested done-confirmation first)

## 1. Objectives / acceptance criteria

| # | done_when | Result |
|---|---|---|
| 1 | Shared helper `scripts/db_safe_backup.py` using `sqlite3.Connection.backup()` + `quick_check` + sha256/size in `.manifest.json` | ✅ `backup_to()`, `verify_backup()`, manifest written on compress |
| 2 | `scripts/backup_db_daily.py` uses helper instead of `shutil.copy2` | ✅ (+ path bug fixed, see §3) |
| 3 | The 6 raw copy/restore scripts use helper; overwrite-restore only with `--i-know-server-is-stopped` | ✅ all 6 wired; gate enforced by `restore_from()` |
| 4 | `sync_to_vps.ps1`: backup-API snapshot → upload `lineage.db.incoming-<ts>` → verify sha256 + quick_check → atomic `mv` → restart only on success → health check | ✅ rewritten (PS parse OK) |
| 5 | Test helper on temp WAL DB with in-flight write ⇒ snapshot intact. No real sync, no SSH | ✅ `tests/test_t387_db_safe_backup.py` 10 passed |
| 6 | Separate commit + Admin DONE | ⏳ pending |

## 2. Files changed

| File | Change |
|---|---|
| `scripts/db_safe_backup.py` | Added `verify_backup()` (magic header + `PRAGMA quick_check`), `restore_from()` (refuses without `i_know_server_is_stopped`, removes `-wal`/`-shm`), fixed `prune_old_backups()` date regex (old code never matched), CLI now exits 0/1 |
| `scripts/backup_db_daily.py` | Uses `backup_to(str(DB_PATH), str(backup_path))` — **was `str(backup_filename)`**, so snapshot landed in CWD and the script always exited 1. Raw-copy fallback now gated by `--i-know-server-is-stopped` |
| `scripts/build3_source_registry_extend.py` | `do_undo()`/`run()` accept gate, call `restore_from()`; new `--i-know-server-is-stopped` arg |
| `scripts/build3_license_firewall.py` | Same gate; **fixed dry-run bug** that called `backup_to(DB_PATH, BACKUP_PATH)` and overwrote the restore point (now `verify_backup()` read-only) |
| `scripts/etl_entity_claims.py` | `backup_db(gate)`; fallback raw copy only with flag, otherwise `SystemExit(1)` |
| `scripts/cbeta_build_text_passages.py` | `cmd_apply(..., i_know_server_is_stopped)`; fallback gated |
| `scripts/bgis_spatial_join.py` | fallback `shutil.copy` only with flag; new CLI arg |
| `sync_to_vps.ps1` | DB step rewritten (snapshot → incoming upload → remote verify → atomic swap → conditional restart → `/api/health` check) |
| `tests/test_t387_db_safe_backup.py` | **new** — 10 tests |
| `tasks/T387-…md` | status `pending` → `in_progress`, checklist + outcome updated |

## 3. Verification (commands + output)

```
python -X utf8 -m pytest tests/test_t387_db_safe_backup.py -q
..........                                                               [100%]
10 passed in 0.82s

python -X utf8 -m py_compile scripts/db_safe_backup.py scripts/build3_source_registry_extend.py \
  scripts/build3_license_firewall.py scripts/etl_entity_claims.py \
  scripts/cbeta_build_text_passages.py scripts/bgis_spatial_join.py scripts/backup_db_daily.py
COMPILE OK

# PowerShell AST parse of the sync script
PS1 PARSE OK

# CLI smoke test on temp WAL DB (not production)
exit 0
[OK] Backup created: …\snap.db (0 MB, sha256=4638cab733a64408…)
exists True

python -X utf8 scripts/repo_guard.py
[OK] SSOT repo root = …\visjs-app
[OK] Khong co .git that trong Dai_Tang_Kinh/daoanh/
```

Not run (intentionally / impossible here): real VPS sync, SSH, `npm run pipeline` (npm shim prints nothing on this box).

## 4. Production/DB impact

None. No DB write, no SSH, no deploy. All tests use `tempfile` databases.
Rollback = `git checkout -- <file>` (nothing committed yet).

## 5. Open items

1. `daoanh-qa` independent check.
2. Admin confirmation → then commit `T387: … + docs`.
3. Real sync has only been AST-parsed, never executed — first scheduled run should be watched (log `sync_to_vps.log`).
