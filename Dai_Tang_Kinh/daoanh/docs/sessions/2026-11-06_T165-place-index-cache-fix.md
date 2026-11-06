# Session 2026-11-06 — T165 cache columns + index cho tab Place

## Task

Admin đã duyệt (1A, 2 OK): `data/lineage.db` thiếu 3 cột trong `translation_cache`
(`constitution_hash`, `selected_rule_codes`, `glossary_hash`) → route
`/daoanh/api/admin/translation-cache` trả 500, 2 ô thống kê tab Place hiện "—".
Truy vấn `/daoanh/api/dila/places` chậm ~1,27s (đo lại thực tế trên máy này: 6,5–6,9s)
vì `namevi_map_places` thiếu index trên `name_zh`.

## Root cause (đã xác minh bằng code đọc thật, không đoán)

1. **`app.py:23884`** (`api_admin_translation_cache_list`) — `SELECT ... constitution_hash,
   selected_rule_codes, glossary_hash FROM translation_cache` — 3 cột này **không tồn tại**
   trong `data/lineage.db` hiện tại (xác nhận qua `PRAGMA table_info(translation_cache)`,
   chỉ có 18 cột tới `identity_lock_hash`, migration T165 (`scripts/t165_rules_engine_migrate.py`)
   **chưa từng `--apply`** trên file DB này mặc dù `docs/tasktodo.md` ghi T165/T169 "DONE" —
   suy ra bản `lineage.db` đang dùng local là bản khác / đã bị khôi phục từ snapshot trước
   migration đó). Không có `try/except` quanh SELECT này → sqlite3.OperationalError
   → Flask 500.
2. Hệ quả dây chuyền: `write_cache()` (`style_constitution.py:719`) ở nhánh
   `elif _has_col(conn, 'translation_cache', 'identity_status')` (dòng 815-829) **cũng** INSERT
   thẳng `constitution_hash/selected_rule_codes/glossary_hash` — nếu không migrate, hành
   động "Dịch ngay" cho `place_note` cũng sẽ lỗi SQL (chưa quan sát trực tiếp vì chưa test
   nhưng đọc code xác nhận).
3. **`app.py:9478-9491`** (`api_dila_places_search`) — với mỗi dòng `places_dila` trả về
   (tối đa `limit`), chạy 2 correlated subquery `SELECT ... FROM namevi_map_places WHERE
   name_zh = pd.name_zh ...`. Index hiện có `idx_namevi_places_cover(name_vi, dila_id,
   name_zh)` không giúp vì `name_zh` không phải cột dẫn đầu → full scan 60.468 dòng mỗi
   lần → đo thật trước fix: **6,59s / 6,58s / 6,94s** (3 lần, `curl -w time_total`,
   `limit=50`).

## Fix đã áp dụng

### 1. Migration T165 cache columns (additive, KHÔNG xoá/suy data)

```
python scripts/t165_rules_engine_migrate.py --dry-run
python scripts/t165_rules_engine_migrate.py --apply
```

Dry-run xác nhận plan: 5 `ALTER TABLE ADD COLUMN` (2 `translation_rules`
`match_scope`/`match_terms` + 3 `translation_cache` `constitution_hash`/
`selected_rule_codes`/`glossary_hash`), không có tác động ngoài dự kiến (0 DELETE,
0 UPDATE dữ liệu hiện có ngoài backfill `match_scope` trên `translation_rules` và
set 3 cột cache về NULL — vốn đã là NULL do cột mới). Backup tự động trước apply:
`data/backups/lineage_t165_20261106_161759.db`.

Kết quả apply: `translation_rules` 140 dòng (94 `terms` / 46 `always`), `translation_cache`
1835 dòng (3 cột hash mới = NULL, đúng — "không đoán lịch sử").

**T165-P8.2 alignment migrate (`scripts/t165_phase8_alignment_migrate.py`) — KHÔNG chạy.**
Lý do (đọc code trước khi quyết): cột P8 (`entity_evidence`/`alignment_method`/
`entity_assertion_status`/`entity_types_covered`) chỉ được dùng khi pilot gate P8.3
bật (`_p8_pilot_active(request)`, mặc định OFF, cần header `X-T165-P8-Pilot:1`).
`write_cache()` đã có guard `_has_col(conn, 'translation_cache', 'entity_evidence')`
(style_constitution.py:783) — khi cột P8 chưa có, tự rơi xuống nhánh T166-only
(dòng 815) vẫn ghi đủ `constitution_hash` v.v. Vậy sau khi T165 migration áp dụng,
tab Place + action dịch hoạt động bình thường mà không cần P8. Không chạy để tránh
đổi schema ngoài phạm vi bug này.

### 2. Index `namevi_map_places(name_zh)` — script mới

Viết `scripts/t165_place_namezh_index.py` (idempotent, `--stats/--dry-run/--apply/--revert`,
backup tự động, pattern giống `t165_rules_engine_migrate.py`):

```sql
CREATE INDEX IF NOT EXISTS idx_namevi_places_name_zh ON namevi_map_places(name_zh)
```

Backup trước apply: `data/backups/lineage_t165idx_20261106_162218.db`.

## Đo trước / sau

| Endpoint | Trước | Sau |
|---|---|---|
| `GET /daoanh/api/dila/places?limit=50` | 6,59s / 6,58s / 6,94s (3 lần) | 0,094s / 0,019s / 0,020s (3 lần) |
| `GET /daoanh/api/admin/translation-cache?source_type=place_note&status=auto&limit=1` | HTTP 500 | HTTP 200, `{"ok":true,"total":35,"rows":[...]}` |

## Kiểm chứng UI (browser thật, không JS inject)

`http://127.0.0.1:8080/daoanh/admin/translation_progress.html#place` — `get_page_text`
sau khi trang tải xong:

```
Dịch ID Place (59.167)
59.167   Tổng Place (DILA)
53.962   Đã có name_vi (mapped)
35       Có bản nháp AI (draft)
5.170    Chờ dịch (có note)
0        Không có note DILA
```

Bảng load 59.167 dòng, 1184 trang, render đúng cột DILA ID / TÊN HÁN / TÊN VIỆT /
LOẠI / KHU VỰC / TRẠNG THÁI / HÀNH ĐỘNG. Trước fix: 5 tile đều "—", bảng kẹt
"Đang tải…" (do request `/daoanh/api/admin/translation-cache` 500 làm `plLoadStats()`
throw trong `try` → catch set `pl-err`, một phần UI không cập nhật).

Network log (`read_network_requests`):
```
GET /daoanh/api/dila/stats                                                    → 200 OK
GET /daoanh/api/admin/translation-cache?source_type=place_note&status=auto&limit=1 → 200 OK
GET /daoanh/api/dila/places?limit=50&offset=0                                 → 200 OK
```

## Regression check (không đổi route khác)

```
GET /daoanh/api/admin/translation-cache?source_type=person_bio&status=auto&limit=1 → 200, 0.026s
GET /daoanh/api/dila/stats                                                          → 200, 0.701s
GET /daoanh/api/translate-rules                                                     → 200, 0.023s
GET /daoanh/api/admin/translation-error-reports?limit=1                             → 200, 0.022s
GET /daoanh/api/dila/places?q=寺&limit=50                                           → 200, 0.178s
```

`python -m py_compile scripts/t165_place_namezh_index.py` → OK.

## Backup / Revert

- `data/backups/lineage_t165_20261106_161759.db` — trước migration cache columns.
- `data/backups/lineage_t165idx_20261106_162218.db` — trước khi thêm index.
- Revert cột: `python scripts/t165_rules_engine_migrate.py --revert` (DROP 5 cột +
  bảng `translation_prompt_metrics` nếu chưa tồn tại trước đó — **CHÚ Ý**: bảng
  này đã có từ trước phiên này với 1 dòng metrics thật, `--revert` sẽ DROP luôn bảng
  đó, mất 1 dòng log đo — không mất bản dịch nào).
- Revert index: `python scripts/t165_place_namezh_index.py --revert` (DROP INDEX,
  không mất dữ liệu).

## Lệch so với yêu cầu gốc — cần Admin xác nhận

1. **Backup vào `docs/sessions/2026-11-06/`**: lệnh `cp`/`shutil.copyfile` một bản
   `data/lineage.db` (1,83GB) vào `docs/sessions/2026-11-06/` bị **hook chặn ghi cây
   chính** (`PreToolUse:Bash hook error: CHẶN: lệnh ghi/git nhắm vào cây chính`).
   Hook cho phép chạy **script đã có sẵn trong repo** nhắm vào `data/` (gitignored),
   nhưng chặn lệnh ghi/ copy tùy biến (`cp`, `python -c` inline) nhắm vào cây chính —
   kể cả khi đích là thư mục `data/`. Đã dùng đúng 2 backup tự động của chính migration
   script (nằm trong `data/backups/`, đúng quy ước `data-integrity.md`) thay cho việc
   copy thủ công vào `docs/sessions/`. Ngoài ra `docs/sessions/` **không nằm trong
   `.gitignore`** — copy nguyên 1,83GB DB vào đó có nguy cơ bị `git add` lỡ tay sau
   này (kho phình to). Đề nghị: giữ backup ở `data/backups/` (đã làm), không copy
   full DB vào `docs/`. Nếu Admin vẫn muốn bản sao trong `docs/sessions/`, cần chạy
   lệnh đó trực tiếp (ngoài harness này) vì bị chặn ở đây.
2. File script mới + session log này được viết trong **worktree** `wt/t165-place-index`
   (`C:\Users\Nam Thien\.claude\worktrees\t165-place-index`) vì `Write`/`cp` vào cây
   chính bị chặn cho đường dẫn git-tracked (`scripts/`, `docs/`). Migration DB
   (`--apply`) chạy **trực tiếp** vào `data/lineage.db` thật (không bị chặn — DB
   gitignored, chạy qua script đã kiểm, không phải lệnh ghi tùy biến). Script mới
   sẽ được tích hợp vào cây chính qua `scripts/wt_integrate.py` sau khi commit trong
   worktree.

## Trạng thái

Chưa tự đánh Done — chờ Admin xác nhận theo đúng quy tắc dự án.
