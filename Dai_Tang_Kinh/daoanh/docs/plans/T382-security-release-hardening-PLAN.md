---
task: tasks/T382-security-release-hardening.md
---

# Kế hoạch T382 — Bảo mật & phát hành an toàn

**Ngày:** 2026-10-13 · **Trạng thái:** Admin đã phê chuẩn đề xuất ("phê chuẩn đề xuất này", 2026-10-13).
**Nguồn:** [`docs/reports/ARCHITECTURE-REVIEW-2026-10-13.md`](../reports/ARCHITECTURE-REVIEW-2026-10-13.md) →
kiểm chứng [`docs/reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md`](../reports/ARCHITECTURE-REVIEW-2026-10-13-VERIFY.md).
**Người thực hiện:** Hermes (root/điều phối) giao cho agent code/debug theo `docs/process/HERMES_DISPATCH_PROMPT.md`.

## 0. Cập nhật 2026-10-13 (sau phê chuẩn) — Admin hoãn phần bảo mật

Admin: *"ngừng các giao thức bảo mật, acc test dùng duy nhất gmail để login, khi nào ver chính thức ra mắt trên Net ta sẽ
config task security sau"*.

| Task | Trạng thái mới | Ghi chú |
|---|---|---|
| T383 auth tập trung | **deferred**, `dispatch: deferred` | Mở lại trước khi ra mắt |
| T384 run_etl_gen + update_file | **deferred**, `dispatch: deferred` | Mở lại trước khi ra mắt |
| T386 Google ID token | **deferred**, `dispatch: deferred` | Giai đoạn test: đăng nhập bằng Gmail như hiện tại |
| T388 dashboard JSON + gateway allowlist | **deferred**, `dispatch: deferred` | Mở lại trước khi ra mắt |
| T385 tắt deploy tự động | pending, `dispatch: approved` | An toàn phát hành, không phải auth |
| T387 backup/sync SQLite an toàn | pending, `dispatch: approved` | An toàn dữ liệu |
| T389 engine số đời cũ | pending, `dispatch: approved`, bỏ phụ thuộc T384 | An toàn dữ liệu (backup trước DROP, dry-run) |

Hermes chỉ nhận task có `dispatch: approved` ⇒ sóng kế tiếp: **T385, T387, T389** (file riêng, chạy song song được;
T389 cần helper backup của T387 nên nếu T387 chưa xong thì T389 chỉ làm phần dry-run/nhãn, chặn `--apply`).
Mở lại phần bảo mật: đổi `status` về `pending` và `dispatch` về `approved` ở 4 task trên.

## 1. Vì sao làm trước mọi tính năng mới

Đo ngày 2026-10-13 (read-only):

| Lỗ hổng | Số đo / vị trí | Hệ quả |
|---|---|---|
| Login chỉ cần chuỗi email admin | `server.py:108-122`, email viết cứng `server.py:46` | Ai biết email là có quyền admin |
| Route ghi không auth | 95/111 route ghi trong `app.py` (71 dưới `/admin/`), không có `before_request` | Ai cũng ghi/xoá được dữ liệu qua `/daoanh/api/` |
| ETL số đời công khai | `/daoanh/api/admin/run_etl_gen` → script có `DROP TABLE` | Một request xoá + tính lại bảng số đời |
| Path traversal | `/api/update_file` ghép `id` vào đường dẫn | Ghi file `.ttl` ra ngoài thư mục |
| Deploy tự động | `deploy.yml` deploy mỗi push master, không test | Một lần push đẩy 737 commit chưa kiểm lên production |
| Backup/sync DB | `copy2` trên DB WAL; `sftp put -a` đè DB live; restart vô điều kiện | Backup thiếu dữ liệu, DB production hỏng |

## 2. Thứ tự giao (sóng)

Ràng buộc "mỗi file một agent ghi trong một lượt": T383, T384 và một phần T386/T388 cùng sửa `app.py` ⇒ phải nối tiếp.

| Sóng | Task | Song song được với | Lý do thứ tự |
|---|---|---|---|
| 1 | **T383** chặn auth tập trung (app.py) | T385, T387 | P0 lớn nhất; nền cho T384/T386 |
| 1 | **T385** tắt deploy tự động (deploy.yml) | T383, T387 | File riêng, P0, nhỏ |
| 1 | **T387** backup/sync an toàn (scripts, ps1) | T383, T385 | File riêng; T389 cần helper backup |
| 2 | **T384** đóng endpoint nguy hiểm (app.py) | T388 (nếu T388 không sửa app.py) | Cần T383 xong (cùng app.py) |
| 3 | **T386** Google ID token | T388 | `blocked` tới khi Admin có GOOGLE_CLIENT_ID |
| 3 | **T388** dashboard JSON + gateway allowlist | — | P1/P2 |
| 3 | **T389** engine số đời legacy | — | Cần T384 (endpoint đã khoá) + helper T387 |

## 3. Quy tắc chung cho mọi task con

1. **Một task = một commit** tiền tố ID, stage theo đường dẫn tường minh; hoàn tác `git revert --no-edit <sha>`
   (`docs/process/REVERT_ONE_FIX.md`). Hermes chạy theo lịch **không** commit (HERMES_DISPATCH_PROMPT §4): agent chuẩn bị
   danh sách file + lệnh commit trong session log, Admin hoặc phiên có quyền git commit.
2. Sao lưu file trước khi sửa vào `docs/sessions/<ngày>/*.bak-before-T38x`.
3. Không ghi `data/lineage.db`, không đổi schema, không deploy VPS, không push. Test dùng DB tạm / Flask test client.
4. Bằng chứng nộp: lệnh + output rút gọn; với thay đổi UI/auth: ảnh chụp hoặc network log trên `http://127.0.0.1:8080`.
5. Agent báo DONE/PARTIAL/BLOCKED; `daoanh-qa` kiểm độc lập; chỉ Admin bấm ✔ Done trên Dashboard.

## 4. Nghiệm thu chung cho T382

- `tests/test_t383_admin_write_guard.py` xanh và chặn được route ghi mới thêm mà quên auth.
- Gọi không token tới mọi route ghi/`/admin/` (ngoài allowlist) ⇒ 401.
- `run_etl_gen` ⇒ 410; `update_file` với `../` ⇒ 400.
- `deploy.yml` chỉ `workflow_dispatch`, có job test.
- Login chỉ chấp nhận Google ID token hợp lệ của email admin.
- Backup daily dùng SQLite backup API + `quick_check`.

## 5. Việc Admin cần làm

| Khi nào | Việc |
|---|---|
| Trước T386 | Tạo Google OAuth Client ID (Web), origin `https://phatphaponline.org` + `http://127.0.0.1:8080`; ghi `GOOGLE_CLIENT_ID` vào `.env`; đổi T386 sang `pending` |
| Sau T385 | Thêm secret GitHub `VPS_KNOWN_HOSTS` (nội dung `ssh-keyscan` của VPS, Admin tự kiểm fingerprint) |
| Mỗi task | Xem QA, bấm ✔ Done trên Dashboard |
| Sau T383–T386 | Quyết lịch deploy lên VPS (deploy là cổng riêng) |

## 6. Ngoài phạm vi (giữ cho Phase 2–5 của báo cáo kiến trúc)

Migration ledger, connection read-only/read-write, sidecar versioned, tách monolith (T364/T378), T232 là engine số đời duy
nhất, Dashboard tách Implemented/QA/Accepted/Deployed, production manifest.
