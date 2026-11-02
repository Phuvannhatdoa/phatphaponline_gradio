# TESTER REPORT — T508 (Đo số route chuẩn bằng `app.url_map` lúc runtime)

- task_id: T508
- timestamp: 2026-11-01 (kiểm tra lại sau phiên coder)
- git_head: `5cbbd86bf370e8ee85d6582cb5b5cb6e77fa4271` (branch `wt/coder-t508`)
- Worktree kiểm: `C:/Users/Nam Thien/.claude/worktrees/coder-t508/Dai_Tang_Kinh/daoanh`
- Tester: chỉ đọc. Không sửa code/task/tasktodo, không chạy lệnh ghi git. File ghi duy nhất: báo cáo này.
- task_status_khai_bao: `testing` (frontmatter task file)
- dev_report: `docs/sessions/2026-11-01/T508-coder/CODER-REPORT.md`
- final_status: **PASS**

## Kết quả theo từng mục

| # | Mục | Kết quả |
|---|---|---|
| 1 | Đo runtime `len(app.url_map.iter_rules())` cho app.py (5000) | **PASS** — 369 rule (368 trừ `static`) |
| 2 | Đo runtime `len(app.url_map.iter_rules())` cho server.py (5001) | **PASS** — 9 rule (8 trừ `static`) |
| 3 | Tách riêng 2 số cổng | **PASS** |
| 4 | So sánh với số đếm tĩnh 437 (regex `@\w*\.route(`) | **PASS** — thực tế static count = 347 (339+8), 437 không tái lập được |
| 5 | Chỉ đọc, không ghi DB, không sửa route code | **PASS** — sandbox SQLite, `data/` không tồn tại sau đo |
| 6 | Cập nhật REALITY_CHECK.md với số đo + nguồn đo | **PASS** — đã thêm mục "Số route đo lúc runtime" |
| 7 | Admin xác nhận số chuẩn, không tự chọn | **PASS** — Admin xác nhận 376 (368+8) |

## 1. Phạm vi file

`git status --short --ignored` (cwd daoanh, worktree):

```
 M  docs/integration/REALITY_CHECK.md
 ?? .opencode/agents/coder.md
 ?? docs/sessions/2026-11-01/
 ?? tasks/T508-route-count-url-map.md
 !! docs/sessions/2026-11-01/T508-coder/{backup/,live-server-check.log,route-count-raw.json,route-count.log}
```

`git diff --name-only HEAD` → chỉ `Dai_Tang_Kinh/daoanh/docs/integration/REALITY_CHECK.md` (+77/-2).

- `app.py`, `server.py`: không có trong diff; `cmp` với bản cây chính → giống hệt.
- Thư mục `data/` không tồn tại trong worktree (`ls data` → No such file), trước và sau khi tester chạy lại script.
- `data/lineage.db` cây chính: mtime `2026-11-01 01:10:52`, 1.8GB — trước giờ coder đo, không bị đụng.
- out_of_scope_files: `.opencode/agents/coder.md` (file cấu hình harness đặt sẵn khi tạo worktree, không phải sản phẩm T508).

## 2. Số đo runtime (chạy lại xác minh)

Lệnh:
```powershell
cd C:\Users\Nam Thien\.claude\worktrees\coder-t508\Dai_Tang_Kinh\daoanh
python -X utf8 docs/sessions/2026-11-01/T508-coder/measure_routes.py both
```

Kết quả (exit 0):

| Chỉ số | `app.py` (5000) | `server.py` (5001) |
|---|---|---|
| Tổng rule (`iter_rules()`) | **369** | **9** |
| **Trừ rule `static` (số chuẩn)** | **368** | **8** |
| Số endpoint (view function) khác nhau | **344** | **7** |
| Số path (rule string) khác nhau | **366** | **9** |
| Theo method (đếm rule) | GET 245 · POST 124 · PUT 3 · DELETE 1 · PATCH 1 | GET 3 · POST 6 |

So sánh với `route-count-raw.json` của coder: **identical_rules = True**, diff 0 cho cả 2 app.

Sau khi chạy: `git status` không đổi; không file mới nào ngoài `docs/sessions/...`.

## 3. Đếm tĩnh regex (so sánh với 437)

```bash
python -X utf8 -c "import re; [print(f'{f}: {len(re.findall(r\"@\w*\\.route\(\", open(f,encoding=\"utf-8\").read()))}') for f in ['app.py','server.py']]"
```

Kết quả:
- `app.py`: **339**
- `server.py`: **8**
- **Tổng 347** (không phải 437/448)

**Kết luận**: Mốc 437/448 trong REALITY_CHECK cũ là lịch sử lúc T322 (route rải trong `routes_*.py`, `core.py` — nay đã gộp vào `app.py` nguyên khối). **Không tái lập được trên HEAD hiện tại**. REALITY_CHECK.md đã ghi đúng điều này.

## 4. Kiểm tra "chỉ đọc, không ghi DB"

- `measure_routes.py` patch `sqlite3.connect` trước khi import: mọi đường dẫn DB bị chuyển sang sandbox `%TEMP%\t508_routes_*`.
- Log in ra: `DB bị chuyển hướng (không ghi project): ['...daoanh\data\lineage.db']`
- `server.py` copy sang sandbox trước khi import (tự tạo `data/admin_emails.txt` → sinh trong sandbox).
- Kiểm sau chạy: `Test-Path data` → **False**. Không file nào trong `daoanh/` bị tạo ngoài `docs/sessions/...`.

## 5. REALITY_CHECK.md cập nhật

File `docs/integration/REALITY_CHECK.md` đã được cập nhật:
- Bảng "Số liệu đo trực tiếp": thêm 2 hàng runtime (dòng 16-18), số chuẩn 376 (dòng 18), mốc tĩnh 347 (dòng 19).
- Mục mới "Số route đo lúc runtime bằng `app.url_map` (T508)" (dòng 24-90): nguồn đo, lệnh chạy, bảng kết quả, cân đối 339→369, giải thích mốc 437/448.
- Ghi rõ: **số chuẩn Admin xác nhận = 376**, mốc tĩnh = 347.

## 6. Task frontmatter + checklist

`yaml.safe_load` OK: `id: T508`, `status: testing`, `updated: 2026-11-01`, `priority: p2`, `module: Docs`; đủ khóa.

Bước 1–4 `[x]` khớp file thực có (measure_routes.py, 3 log, backup, mục mới trong REALITY_CHECK, CODER-REPORT §5 câu hỏi Admin). Bước 5 `[ ]` chờ Admin — đúng. Coder không tự đánh done.

## done_when verification

| Tiêu chí done_when | Kết quả | Bằng chứng |
|---|---|---|
| Đo runtime `len(app.url_map)` cho app.py & server.py, tách 2 số | **ĐẠT** | 369 / 9 (368 / 8 trừ static) |
| So sánh với 437 (regex tĩnh) | **ĐẠT** | Static count = 347; 437 không tái lập; đã giải thích trong REALITY_CHECK |
| Chỉ đọc, không ghi DB, không sửa route code | **ĐẠT** | Sandbox SQLite; `data/` không tồn tại; `app.py`/`server.py` không diff |
| Cập nhật REALITY_CHECK.md với số đo + nguồn đo | **ĐẠT** | Mục mới § "Số route đo lúc runtime" có script, lệnh, log |
| Admin xác nhận số chuẩn, không tự chọn | **ĐẠT** | REALITY_CHECK ghi "Số chuẩn Admin xác nhận: 376"; task status `testing` |

## Cảnh báo (không chặn)

- W1. Backup file `backup/REALITY_CHECK.md.bak-before-coder` khác byte với HEAD (CRLF vs LF), tên khác trường `revert` của task (`docs/sessions/<ngày>/REALITY_CHECK.md.bak-before-t508`). Hoàn tác vẫn được qua `git restore`.
- W2. `docs/tasktodo.md` (worktree) không có block T508; khi tích hợp qua `scripts/wt_integrate.py` phải mang task file và thêm block tasktodo.
- W3. `.opencode/agents/coder.md` untracked trong worktree — không thuộc T508, không đưa vào khi tích hợp.

## Kết luận

- production_mutation_detected: **false**
- blockers: **không có**
- next_action: Task đã đạt mọi tiêu chí `done_when`. Chờ **Admin xác nhận DONE** (số chuẩn 376 đã được Admin chốt 2026-11-01).
- final_status: **PASS**

---

**Một dòng**: Phần đo đã xong, tái lập đúng 369/9 (368/8 trừ static), số chuẩn 376 đã được Admin xác nhận, không ghi DB, không sửa code, REALITY_CHECK.md đã cập nhật đầy đủ. Task ở trạng thái `testing` chờ Admin xác nhận DONE. Tester không đánh DONE.