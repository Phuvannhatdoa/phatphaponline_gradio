# Kiểm chứng ARCHITECTURE-REVIEW-2026-10-13

**Ngày:** 2026-10-13 · **Người kiểm:** Claude Code (Remote Control) · **Chế độ:** chỉ đọc. Không sửa code/DB/TTL, không gọi endpoint ghi.
**HEAD lúc kiểm:** `master` @ `8a5f1cc`. Số dòng `app.py` dưới đây là theo HEAD này.
**Đối tượng:** [`ARCHITECTURE-REVIEW-2026-10-13.md`](ARCHITECTURE-REVIEW-2026-10-13.md) (Codex/GPT review).

## Kết luận

Hướng của báo cáo **đúng**. Đa số phát hiện tái hiện được bằng code. Có 3 loại chỗ cần chỉnh:

1. **Đánh giá thấp mức độ** ở phần auth: không phải "có dấu hiệu" mà là **xác định**. Endpoint chạy ETL số đời (DROP bảng) công khai và không có auth ⇒ thuộc P0, không phải P1.
2. **Nói quá / chưa chính xác** ở 3 điểm: gateway local, "lấy nhầm version", "+37".
3. **Bỏ sót** 4 điểm: path traversal ở `/api/update_file`, workflow GitHub tự deploy, backup daily copy file WAL, gunicorn 2 worker.

## Bảng đối chiếu từng phát hiện

| # | Phát hiện của báo cáo | Kết luận | Bằng chứng đo được |
|---|---|---|---|
| P0-1 | Login cấp session từ email trong danh sách admin, không chứng minh sở hữu email | **ĐÚNG — nặng hơn báo cáo nêu** | `server.py:108-122`: `POST /api/login/verify {"email": ...}` ⇒ email có trong `admin_emails.txt` thì trả `session_token`. Không có mật khẩu, OTP hay Google ID token. `admin/login.html:237` chỉ gửi chuỗi email. Email admin mặc định viết cứng ở `server.py:46`. Ai biết email admin là có quyền admin. nginx chỉ giới hạn 3 req/phút. |
| P0-2 | Auth route ghi không thống nhất | **ĐÚNG — đo được** | AST scan `app.py`: 311 route, **111 route ghi** (POST/PUT/DELETE/PATCH), chỉ **16** có `verify_session`, **95 không có** (71 trong số đó dưới `/admin/`). Không có `before_request`. nginx `location /daoanh/api/` proxy thẳng vào app.py, không có lớp auth. Ví dụ không auth: `/daoanh/api/admin/run_etl_gen` (L24787), `monk_ttl` (L24748), `import_t265_decisions` (L24814), `cbeta/import-xml`, `cbeta/batch-import`, `t50/run`, `namevi-map-places/save`, `bio-review/bulk-approve`, `claims/bulk-review`, `keywords/bulk_delete`. Ngoài ra `verify_session` (`app.py:91`) chỉ kiểm token còn hạn, không kiểm lại danh sách admin: xoá một admin thì token cũ vẫn ghi được tới 24 giờ. |
| P0-3 | Lint che lỗi, test placeholder | **ĐÚNG** | `package.json:12` `lint … \|\| exit 0`. `tests/run-tests.js` chỉ có `console.log("✅ Tests passed")`. (Chưa kiểm `tester-agent.mjs`.) |
| P0-4 | Deploy/sync copy SQLite live, restart dù transfer lỗi | **ĐÚNG** | `sync_to_vps.ps1:68-106`: hash file `lineage.db` đang mở ở chế độ WAL; không checkpoint, không upload `-wal`. `sftp put -a` ghi **thẳng** lên `data/lineage.db` production khi service đang chạy. Bước 3 restart **vô điều kiện** (kể cả khi upload thất bại cả 10 lần). |
| P0-5 | Shared worktree bị orphan checkout | **ĐÚNG** | Chính phiên housekeeping chứng kiến (`docs/Handoff-2026-10-13-housekeeping.md` mục 4). Hiện đã về `master`. Hệ quả còn treo: phần sửa của T374/T376/T378 trong `app.py`/`AGENTS.md`/`CLAUDE.md`/`tasktodo.md` **chưa được áp dụng lại** (`app.py` vẫn còn route zenlineage ở L2530). |
| P1-1 | app.py monolith | **ĐÚNG** | 24.967 dòng, 311 route `@app.route` (+ blueprint). |
| P1-2 | Generation `+37`, DROP/rebuild, song song T232 | **ĐÚNG về rủi ro, SAI ở lý do** — xem C2 | `scripts/etl_gen_compute.py:18,39,43,150,416-417`. Endpoint kích hoạt `/daoanh/api/admin/run_etl_gen` **công khai, không auth** ⇒ nâng lên **P0**. |
| P1-3 | Loader DILA nạp toàn bộ XML vào RAM, không lọc run/hash | **ĐÚNG một nửa** — xem C3 | `app.py:5717-5734` `SELECT id, raw_text … WHERE kind='DILA_XML'` rồi `fetchall()`: **49.361 dòng, 49,1 MB** text, parse hết vào dict. Bảng có cột `version`, `sha256`, `import_run_id` nhưng loader bỏ qua. |
| P1-4 | Backup/revert copy file SQLite khi đang WAL | **ĐÚNG — rộng hơn báo cáo nêu** | `PRAGMA journal_mode = wal`. Có `shutil.copy2(DB_PATH, …)` ở `scripts/backup_db_daily.py:64` (**backup hằng ngày**), `etl_entity_claims.py:86`, `cbeta_build_text_passages.py:191`, `build3_*.py`. Restore bằng copy ngược đè DB (`build3_license_firewall.py:235`, `build3_source_registry_extend.py:199`). |
| P1-5 | Local gateway phục vụ mọi file; VPS chặn JSON Dashboard cần | **Vế 1 nói quá; vế 2 ĐÚNG** — xem C1 | `local_gateway.py:65-88` phục vụ mọi file trong `daoanh/` (kể cả `.env`, `lineage.db`) nhưng **mặc định bind 127.0.0.1** (L114); chỉ lộ ra LAN khi chạy `--lan`. Vế 2: `dashboard_process.html:644,1718,1860,1967,2047` fetch `../data/*.json` trong khi `deploy/nginx.conf:48` chặn `^/daoanh/data/.*\.json` ⇒ trên VPS các panel này nhận 403. |
| P1-6 | Dashboard đo inventory, chưa đo hành vi được chấp nhận | **ĐÚNG** | `build_progress_data.py` đếm claim endpoint trong docs và `@app.route` trong 4 file; không đọc kết quả QA. |
| Docs | SCHEMA.md ALTER/DROP vs quy trình curation | **ĐÚNG** | `SCHEMA.md:21-34`. |
| Docs | HARNESS_WORKFLOW vs SUBAGENT-WORKFLOW khác vai trò/ngữ nghĩa DONE | **ĐÚNG** | HARNESS: Điều phối/daoanh-debugger/daoanh-qa, Admin đóng task. SUBAGENT: root/code/debug/deep_research, "DONE chỉ dùng khi tiêu chí đã kiểm đủ" cho agent báo cáo. |
| Docs | HYBRID_DATA_ARCHITECTURE | **Chưa kiểm** | — |

## Chỗ báo cáo chưa đúng hoặc chưa đủ

**C1 — Gateway local (P1-5) nên hạ xuống P2.** Rủi ro chỉ có khi chạy `--lan`. Vẫn nên làm allowlist vì máy dev có `.env` chứa API key. Rủi ro thật nằm ở **VPS**, nơi nginx `location /daoanh/` proxy mọi thứ còn lại vào app.py. Cần kiểm trên VPS rằng app.py không phục vụ file tuỳ ý (các route `send_from_directory` có `ALLOWED_DIRS`).

**C2 — "+37" không sai về số học.** Theo hệ đếm Ma Ha Ca Diếp = 1: Đạt Ma 28, Huệ Năng 33, Nam Nhạc 34, Mã Tổ 35, Bách Trượng 36, Hoàng Bá 37, **Lâm Tế 38** ⇒ offset 37 khớp. Lỗi thật gồm:

- (a) Gán cứng **một** hệ đếm, không ghi `scheme`, trong khi T232/BUG-027 đã có 9 scheme.
- (b) Giả định mọi `generationOrder` trong TTL là "đời Lâm Tế", không kiểm hệ đếm của từng file TTL.
- (c) DILA dùng BFS từ Thích Ca ⇒ lấy **đường ngắn nhất** trên đồ thị nhiều thầy. Đúng loại lỗi `conflict` mà BUG-027 mô tả, nhưng ở đây bị chốt im lặng.
- (d) `DELETE FROM lineage_founders` + `DROP TABLE person_gen_computed` không có backup.
- (e) Kích hoạt được qua HTTP công khai.

Đề xuất: không xoá ngay. (1) Khoá endpoint (auth + tắt mặc định). (2) Gắn nhãn `scheme='thientong_cadiep1', status='computed_legacy'` cho output. (3) T232 thay thế xong thì mới gỡ.

**C3 — "Lấy nhầm version" là rủi ro tiềm ẩn, chưa xảy ra.** Đo: chỉ 1 `import_run_id` (`T227-470dc799…`), 0 `record_id` trùng. Rủi ro sẽ thành thật ở lần import T227 thứ hai. Vế Zero-RAM thì đúng ngay bây giờ. Thêm một điểm: `deploy/gunicorn_config.py:11` chạy **2 worker** ⇒ cache này bị nhân đôi trong RAM. Mọi trạng thái job trong bộ nhớ của app.py (t50 run/stop, translation jobs) cũng không nhất quán giữa hai worker.

**C4 — Bỏ sót (thêm vào P0/P1):**

| Mức | Phát hiện | Bằng chứng | Đề xuất |
|---|---|---|---|
| P0 | `/api/update_file` không auth, `id` không lọc ⇒ path traversal, ghi file `.ttl` ra ngoài thư mục | `app.py:14261-14290` `os.path.join(TTL_MASTER_DIR, f"{file_id}.ttl")` | Kiểm `id` theo regex slug, `realpath` phải nằm trong thư mục cho phép, thêm auth. Theo `deploy/nginx.conf` trong repo, `/api/*` (không có `/daoanh`) không được proxy ra ngoài; **cần xác nhận cấu hình nginx thật trên VPS**. |
| P0 | Workflow GitHub tự deploy **mỗi push lên master**, không qua test, `StrictHostKeyChecking=no`, restart vô điều kiện | `.github/workflows/deploy.yml` | Deploy chỉ chạy bằng `workflow_dispatch` hoặc sau job pipeline xanh; pin host key; health check gọi API thật trước khi coi là xong. Lưu ý thêm: `master` đang ahead 737 commit so với origin ⇒ không biết production chạy commit nào. Củng cố cho Phase 0 (production manifest). |
| P1 | Token chỉ kiểm hạn, không kiểm lại admin; session lưu trong RAM của server.py | `app.py:91`, `server.py:32` | `require_admin` dùng chung, kiểm lại danh sách admin mỗi request; session lưu bền có rotation. |
| P1 | Backup **hằng ngày** cũng copy file WAL | `scripts/backup_db_daily.py:64` | Dùng `sqlite3.Connection.backup()` + `PRAGMA quick_check` trên bản sao. Ưu tiên sửa trước các script khác vì chạy mỗi ngày. |

## Thứ tự sửa đề xuất (điều chỉnh Phase 0–1 của báo cáo)

1. **Ngay (vài giờ, ít rủi ro):** thêm `@app.before_request` chặn mọi method ghi và mọi path `/admin/` khi không có token admin hợp lệ (allowlist tường minh cho vài POST công khai như `/daoanh/api/feedback`, `/daoanh/api/translate`). Kèm test quét toàn bộ `url_map`: route ghi không trong allowlist mà không có token phải trả 401. Đây là cách đóng 95 lỗ trong một chỗ, thay vì sửa từng route.
2. **Ngay:** tắt `run_etl_gen`, sửa `/api/update_file` (regex + realpath), tạm tắt workflow tự deploy (chỉ chạy tay).
3. **Phase 1:** login bằng Google ID token (đã dùng Gmail ⇒ Google Identity Services là con đường ngắn nhất, server kiểm `aud`/`email_verified`) thay cho email trần. OTP là phương án dự phòng.
4. **Phase 1:** `backup_db_daily.py` và `sync_to_vps.ps1` chuyển sang SQLite backup API → upload tên mới → kiểm hash + `quick_check` → swap nguyên tử → restart chỉ khi upload thành công → health check.
5. Phần còn lại giữ theo Phase 2–5 của báo cáo. Dashboard sửa đường dẫn JSON (đọc qua API hoặc nới đúng file trong nginx).

## Câu hỏi cho Admin (bổ sung cho mục "Quyết định Admin cần chốt")

1. Cho phép làm ngay bước 1–2 ở trên như một task riêng (sửa code, có backup, có test) không?
2. Workflow `.github/workflows/deploy.yml`: tắt tự deploy theo push ngay bây giờ?
3. Login: Google ID token (khuyến nghị) hay email OTP?
