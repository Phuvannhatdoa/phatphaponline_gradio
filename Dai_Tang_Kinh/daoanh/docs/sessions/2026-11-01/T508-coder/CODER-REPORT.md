# CODER REPORT — T508 (Đo số route chuẩn bằng `app.url_map` lúc runtime)

- Ngày: 2026-11-01
- Agent: coder (DeepSeek V4.1 Flash Free)
- Task: `tasks/T508-route-count-url-map.md` (priority P2)
- Trạng thái sau phiên: `coding` → **`testing`** (code/docs xong, **chờ Admin xác nhận số chuẩn**;
  coder KHÔNG tự đánh `done`)
- Môi trường đo: worktree `coder-t508`, HEAD `5cbbd86b`, Python 3.14.3, Windows

---

## 1. Tóm tắt kết quả

| Chỉ số (đo lúc runtime) | `app.py` (cổng 5000) | `server.py` (cổng 5001) |
|---|---|---|
| `len(app.url_map.iter_rules())` | **369** | **9** |
| Trừ rule nội bộ Flask `static` | **368** | **8** |
| Số view function (endpoint) khác nhau | **344** | **7** |
| Số path (rule string) khác nhau | **366** | **9** |
| Rule theo method | GET 245 · POST 124 · PUT 3 · DELETE 1 · PATCH 1 | GET 3 · POST 6 |

Đếm tĩnh cùng ngày (regex `@\w*\.route(`, cùng công thức T322):

| Phạm vi | Số decorator |
|---|---|
| `app.py` | 339 |
| `server.py` | 8 |
| **app.py + server.py** | **347** |
| Toàn bộ `*.py` trong `daoanh/` (bỏ bản backup `docs/sessions`, `.git`, `node_modules`) | 419 / 18 file |

**Chênh lệch 339 → 369 của `app.py` (+30) — cân đối đủ từng rule:**

| Nguồn | Số rule |
|---|---|
| `@app.route` decorator (regex bắt được) | 339 |
| `@ app.route('/api/admin/queue/list')` (dòng 15173 — có dấu cách sau `@`, regex trượt) | +1 |
| `app.route(...)(api_cbeta_compare)` (dòng 20220 — đăng ký kiểu gọi hàm) | +1 |
| `app.add_url_rule(...)` T130/T131 (dòng 25494–25496) | +3 |
| Blueprint `ttl_profile_v2`: 22 rule = `api_ttl_profile_v2.py` 13 + `api_codex_namevi.py` 4 + `api_generation_v2.py` 5 | +22 |
| Blueprint `ttl_anchor`: `api_ttl_anchor.py` | +2 |
| Rule `static` Flask tự thêm | +1 |
| **Tổng** | **369** |

`server.py` 8 → 9: 8 decorator + 1 `static`. (7 endpoint, trong đó `login_verify` và
`login_check` mỗi cái có 2 path `/api/...` + `/daoanh/api/...` → 8 rule.)

---

## 2. File đã tạo / sửa

| File | Loại | Nội dung |
|---|---|---|
| `docs/sessions/2026-11-01/T508-coder/measure_routes.py` | **tạo mới** (session artifact, KHÔNG phải code production) | Script đo `url_map` cho `app`/`server`, chặn ghi DB bằng cách chuyển `sqlite3.connect` sang sandbox tạm |
| `docs/sessions/2026-11-01/T508-coder/route-count.log` | tạo mới | Log đầy đủ: từng rule + method + endpoint của cả 2 app (84 KB) |
| `docs/sessions/2026-11-01/T508-coder/route-count-raw.json` | tạo mới | Kết quả máy đọc được (70 KB) |
| `docs/sessions/2026-11-01/T508-coder/live-server-check.log` | tạo mới | Dò cổng 5000/5001/8080 + giải thích vì sao phải import thay vì đọc tiến trình live + cách chống ghi DB |
| `docs/sessions/2026-11-01/T508-coder/backup/REALITY_CHECK.md.bak-before-coder` | tạo mới | Sao lưu trước khi sửa (4.302 bytes) |
| `docs/integration/REALITY_CHECK.md` | **sửa** | Cập nhật dòng "Cập nhật lần cuối"; thay hàng số route trong bảng "Số liệu đo trực tiếp" (giữ mốc 313 thành ghi chú lịch sử + thêm 2 hàng runtime); thêm mục "Số route đo lúc runtime" (§ dài: nguồn đo, bảng kết quả, bảng cân đối, cảnh báo "chưa phải số chuẩn") |
| `tasks/T508-route-count-url-map.md` | **sửa** | `status: coding → testing`, `updated: 2026-11-01`, `outcome` chi tiết, đánh `[x]` Bước 1–4 (Bước 5 chờ Admin) |

**Không sửa** `app.py`, `server.py`, route code, `done_when`, tiêu chí nghiệm thu.

---

## 3. Lệnh đã chạy

| # | Lệnh | Kết quả |
|---|---|---|
| 1 | `python -X utf8 docs\sessions\2026-11-01\T508-coder\measure_routes.py both --json docs\sessions\2026-11-01\T508-coder\route-count-raw.json` | exit 0 — app 369 rule, server 9 rule |
| 2 | `python -X utf8 -c "import ast; ast.parse(open('docs/sessions/2026-11-01/T508-coder/measure_routes.py', encoding='utf-8').read())"` | OK (cú pháp Python hợp lệ) |
| 3 | `python -X utf8 -c "...re.findall(r'@\w*\.route\('...)"` (đếm tĩnh) | app 339, server 8, toàn repo 419 |
| 4 | `python -X utf8 -c "...socket.connect..."` (dò cổng, chỉ đọc) | 5000 LISTEN, 5001 không listen, 8080 không listen |
| 5 | `Test-Path data` sau khi đo | **False** — project không sinh `data/lineage.db` |

Không chạy: `npm`, `git add/commit`, migration, `--apply`, deploy.

---

## 4. Bằng chứng tuân thủ "chỉ đọc, không ghi DB"

`app.py` ở module-level gọi 5 hàm `ensure_*()` chạy `CREATE TABLE IF NOT EXISTS` /
`ALTER TABLE` trên `data/lineage.db`. Worktree này **không có** `data/` → import thẳng sẽ
**tạo file DB mới** (vi phạm "không ghi DB").

`measure_routes.py` patch `sqlite3.connect` trước khi import: mọi đường dẫn DB bị đổi sang
thư mục sandbox `%TEMP%\t508_routes_*` rồi xoá sau khi đo. Log ghi lại đúng đường dẫn bị
chuyển hướng:

```
DB bị chuyển hướng (không ghi project): ['C:\\Users\\Nam Thien\\.claude\\worktrees\\coder-t508\\...\\daoanh\\data\\lineage.db']
```

`server.py` được copy sang sandbox rồi mới import (nó tự tạo `data/admin_emails.txt` khi
thiếu → file này chỉ sinh trong sandbox).

Đã kiểm chứng sau khi chạy: `os.path.exists('data')` → `False`; không file nào trong
`daoanh/` bị tạo ngoài thư mục `docs/sessions/2026-11-01/T508-coder/`.

---

## 5. Câu hỏi CHỜ ADMIN (Bước 4–5 của task)

1. **Số chuẩn chọn số nào?** Đề nghị các phương án để Admin chọn (coder không tự chọn):
   - (a) Chốt theo runtime, tách 2 cổng: **app.py = 369 rule** (368 nếu trừ `static`),
     **server.py = 9 rule** (8 nếu trừ `static`) — đúng tinh thần phương án C của T322.
   - (b) Chốt theo "route nghiệp vụ" = runtime trừ rule framework `static`:
     **app.py 368 + server.py 8 = 376**.
   - (c) Chốt theo view function: **app.py 344 + server.py 7 = 351**.
2. **Mốc tĩnh 448/437 ghi trong task không tái lập được** trên HEAD hiện tại: cả worktree
   `wt/coder-t508` và bản main repo đều cho `app.py` 339 / `server.py` 8 (tổng 347), toàn
   bộ `*.py` = 423 (bỏ `docs/sessions`) hoặc 419 (bỏ thêm `docs/reports`); đếm cả bản backup
   `app.py` trong `docs/sessions/` thì lên 2.639 (vô nghĩa). **Nguồn gốc thật của 448/437 (xác
   nhận bởi tester):** Lúc T322 (2026-10-31) code route nằm rải trong `routes_misc.py` (96),
   `routes_translate.py` (80), `routes_lineage.py` (72), `routes_places.py` (49),
   `routes_namevi.py` (33), `routes_pages.py` (19), `routes_ttl.py` (7), `core.py` (6),
   `t265_routes.py` (1)... Tổng ~448 decorator. Các file này **đã không còn** trong
   `Dai_Tang_Kinh/daoanh` (đã gộp vào `app.py` nguyên khối 25.963 dòng). Cần Admin cho biết:
   **bỏ mốc 437**, **đổi thành 347**, hay **giữ làm ghi chú lịch sử** (hiện tài liệu đang giữ làm
   ghi chú + nói rõ chưa phải số chuẩn).
3. Tiến trình live ở cổng 5000 hiện đang chạy **không có endpoint chẩn đoán** `url_map`.
   Nếu Admin muốn số đo "từ chính tiến trình đang chạy" thì cần task riêng thêm endpoint
   chỉ đọc (sửa route code → ngoài phạm vi T508).

---

## 6. Việc chưa làm / ngoài phạm vi (ghi để MA xử lý)

- Không thêm endpoint `/debug/routes` vào `app.py` (task cấm "sửa route code").
- Không sửa `CLAUDE.md` (dòng "313 routes" nằm trong `CLAUDE.md`/`AGENTS.md` — thuộc task
  khác; T508 chỉ cho sửa `docs/integration/REALITY_CHECK.md`).
- Chưa cập nhật `docs/tasktodo.md` / `docs/ROLLBACK.md` (thuộc MA/Admin).
- Chưa commit (coder không chạy git ghi).

---

## 7. Cách tự kiểm chứng trong 1 phút

```powershell
cd Dai_Tang_Kinh\daoanh
python -X utf8 docs\sessions\2026-11-01\T508-coder\measure_routes.py both `
    --json docs\sessions\2026-11-01\T508-coder\route-count-raw.json
# kỳ vọng: app.py 369 rule (368 trừ static, 344 endpoint, 366 path);
#          server.py 9 rule (8 trừ static, 7 endpoint)
Test-Path data   # kỳ vọng: False (script không ghi DB project)
```
