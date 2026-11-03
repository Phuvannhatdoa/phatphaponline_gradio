# T50 — Test khởi động chịu được DB rỗng (test-robustness)

**Ngày:** 2026-11-03 | **Task:** T50 (CBETA vi_text backfill) | **Nhánh:** `wt/t50-python314-windows-fix`

## Bối cảnh

Sau khi fix Windows/Python 3.14 đã merge (`64a966df` → merge-commit `5982845f`), chạy lại
`tests/test_t50_startup_windows.py` **trong worktree** ra **2/4 PASS**:

```
FAIL test_B_backfill_dry_run_exits_clean
FAIL test_C_backfill_verify_exits_clean
sqlite3.OperationalError: no such table: passage
```

Nguyên nhân **không phải** code fix hỏng:

| Đo | Kết quả |
|---|---|
| `data/lineage.db` trong worktree | 4096 byte, **0 bảng** (file rỗng do `data/` không được git track) |
| `data/lineage.db` cây chính | DB thật, có bảng `passage` ⇒ test `4/4 PASS` |
| Nội dung `data/` trong worktree | chỉ có `lineage.db` rỗng |

Rủi ro: agent sau checkout worktree mới sẽ thấy test đỏ và tưởng fix Windows đã hỏng.

## Thay đổi

1. `scripts/t50_passage_vi_backfill.py` — `DB_PATH` đọc env `T50_DB_PATH` trước:

   ```python
   DB_PATH = os.environ.get('T50_DB_PATH') or os.path.join(DAOANH, 'data', 'lineage.db')
   ```

   Không set env → hành vi **y hệt cũ**. đã đo: `DB_PATH=...\data\lineage.db`.

2. `tests/test_t50_startup_windows.py` — B/C tự chủ động dữ liệu:
   - `_real_db_ready()`: DB thật chỉ được coi là dùng được khi tồn tại **và** có bảng `passage`.
   - `_make_fixture_db()`: fixture tạm gồm 4 bảng tối thiểu (`passage`, `entity`,
     `passage_entity`, `translation_cache`), 1 passage chờ dịch gắn PLACE + PERSON.
     Bảng `passage` **cố ý thiếu `translation_draft`** ⇒ `ensure_schema()` phải ALTER
     (kiểm luôn migration additive).
   - `_db_for_run()`: DB thật nếu sẵn sàng, ngược lại fixture.
   - `_run_backfill()`: truyền `T50_DB_PATH` + `PYTHONUTF8=1`.
   - Assert thêm nội dung để tránh "xanh giả": `DRY RUN` / `Không còn passage chờ dịch`
     (B) và `== VERIFY T50 ==` (C). Thông báo lỗi in kèm nguồn DB (thật/fixture).
   - Runner in 1 dòng `[env] ... → B/C sẽ dùng DB thật|fixture DB tạm`.

## Bằng chứng đo được

| Lần chạy | Kết quả |
|---|---|
| Worktree, `data/lineage.db` rỗng | `T50-STARTUP-WINDOWS: 4/4 PASS` (B/C dùng fixture) |
| Runner tạm trỏ `DB_PATH` → DB thật cây chính | B + C `PASS` (`_real_db_ready() = True`) |
| `python -m py_compile` 2 file | OK |

## Không đụng gì

- Không đổi prompt, logic dịch, schema thật, giá trị Hán/Việt văn.
- Không chạy backfill, không gọi Groq, không ghi vào DB thật (`--dry-run`/`--verify` chỉ đọc;
  fixture là DB tạm trong `%TEMP%`).
- `T50_DB_PATH` chỉ được set trong test (grep toàn repo: 3 chỗ, đều thuộc test/doc).

## Rollback

```
git revert --no-edit <sha>
```

Mất dữ liệu: **không** — thuần code, 2 file, không migration.

## Còn lại

- Restart `app.py` thật (PID cũ chưa nạp fix `CREATE_NEW_PROCESS_GROUP`) + E2E bấm "Dịch"
  trên `t50-progress.html` (handoff `docs/Handoff-2026-11-03-T50-python314-windows.md` mục 8.3–8.4).
