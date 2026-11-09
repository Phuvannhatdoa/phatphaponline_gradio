# Handoff 2026-10-21 — T445 chuyển code sang OpenCode GO

## 1. Bảng thông tin đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày | 2026-10-21 (phiên làm việc kéo qua 2026-10-25) |
| HEAD lúc viết | `47c5ef71` (docs: T445 status in_progress) — kiểm lại bằng `git log --oneline -3` |
| Task | T445 — Wizard UI B0→B9 cho placevn.html (phụ thuộc T444) |
| Trạng thái T445 | `in_progress`, **chưa có code được commit** |
| Đã làm | Spec T445, tasktodo, summary; stop agent code bên Claude; lưu bản WIP |
| Chưa làm | Code T445 bằng OpenCode GO; QA; commit |
| DB | Không thay đổi |
| Commit | Chỉ `47c5ef71` (tasktodo). Không commit code. |

## 2. Đọc trong 2 phút

- **Quyết định của Admin:** code T445 đi qua **OpenCode GO** (VS Code). Hết quota thì dùng **OpenRouter** (tài khoản thứ hai). **Claude Code không code**: chỉ điều phối, test và debug sau khi OpenCode xong.
- **Chưa có code T445 hoàn chỉnh.** `placevn.html` và `app.py` đang có thay đổi dở do một lần code bằng Claude (daoanh-debugger, đã stop) để lại. Bản sao nằm ở `docs/sessions/2026-10-21/T445-debugger-wip/`.
- **3 việc Admin cần làm ngay:**
  1. Chạy OpenCode GO trong VS Code với T445 (xem mục 5).
  2. Xoá API key plaintext trong `.claude/agents/opencode.md` và xoay lại key (xem mục 4).
  3. ~~Xác nhận ID model OpenRouter~~ — đã có: `nvidia/nemotron-3.5-lightning:free`, đã ghi vào `.claude/agents/openrouter.md`.

## 3. Chi tiết kỹ thuật từng việc

**a) Thay đổi chưa commit trong worktree (không phải của session này toàn bộ):**
- `daoanh/admin/placevn.html`: có sửa `baseUrl` từ BUG-placevn-baseurl (đã verify trước đó, chưa commit, xem `tasktodo.md` dòng ~40) **và** phần WIP của debugger (Wizard dở). **Không revert về HEAD** vì sẽ mất sửa baseUrl.
- `daoanh/app.py`: WIP của debugger. Ghi chú từ debugger: process app.py đang chạy chưa nạp route mới, cần restart.
- `.claude/agents/opencode.md`: sửa `model: bigpicke` → `model: opencode-go/claude-haiku-5-5`. Chưa commit. Lưu ý: phiên Claude hiện tại vẫn nạp định nghĩa cũ.

**b) Lỗi đã đo:**
- Agent `opencode` (phía Claude) gọi model `bigpicke` → HTTP 404, 2 lần (lần 2 sau khi sửa file, vì định nghĩa agent được nạp lúc khởi động phiên).
- Agent `openrouter` khai báo `gpt-4-turbo` → HTTP 404.
- Kết luận: ID model trong định nghĩa agent Claude **không khớp** với tài khoản. Nguồn đúng cho OpenCode là `daoanh/.opencode/agents/*.md` (dùng `opencode-go/...`).

## 4. Cảnh báo bắt buộc

- **Lộ key:** `.claude/agents/opencode.md` có API key OpenCode dạng plaintext. File này nằm trong repo git. Cần xoá khỏi file và xoay key ở trang OpenCode. Chưa làm.
- **Không `git add` theo thư mục.** Worktree dùng chung nhiều session; chỉ add file cụ thể.
- `data/progress_data.json` bị `.gitignore`, không commit được. Dashboard đọc file này khi build (`scripts/build_progress_data.py`).
- Dashboard `dashboard/dashboard_process.html` **không tự cập nhật**: phải bấm Refresh hoặc build lại JSON.
- Không chạy `--apply` hay thao tác ghi DB mà chưa có duyệt của Admin.

## 5. Lệnh / thao tác để tiếp tục

Trong VS Code, chạy OpenCode GO với prompt:

```
T445: Đọc daoanh/tasks/T445-placevn-wizard-ui-b0-b9.md và
daoanh/docs/sessions/2026-10-21/T445-debugger-wip/ (bản WIP).
Rà soát phần đã có trong admin/placevn.html và app.py, giữ phần đúng,
sửa phần sai, code tiếp theo spec. Giữ sửa baseUrl hiện có.
Không commit. Khi xong: liệt kê file đã sửa + kết quả
`npm run pipeline` (chạy trong daoanh/).
```

Sau khi OpenCode xong, trong phiên mới của Claude:
1. `cd daoanh && npm run pipeline` — guard, dup:ids, lint, test, e2e.
2. Gọi `daoanh-qa` (chỉ đọc) kiểm chứng theo `tasks/T445`.
3. Test UI bằng trình duyệt tại `http://127.0.0.1:8080/...` (không dùng `localhost`).
4. Trình Admin kết quả QA. Admin duyệt rồi mới commit.

## 6. Việc CHƯA xong (theo ưu tiên)

1. Code T445 bằng OpenCode GO (hoặc OpenRouter nếu hết quota). **Chưa bắt đầu.**
2. Xoá key plaintext trong `.claude/agents/opencode.md`, xoay key. **Admin quyết.**
3. ~~Sửa model `openrouter.md`~~ — **đã sửa** sang `nvidia/nemotron-3.5-lightning:free` (ID do Admin cung cấp). Chưa kiểm chứng gọi thực tế; cần phiên mới để nạp lại định nghĩa agent.
4. QA + pipeline + test UI sau khi code xong.
5. Commit: `feat: T445 wizard UI placevn + docs`, kèm `Co-Authored-By` theo quy định.
6. Viết DEV-REPORT và cập nhật `docs/ROLLBACK.md` (không có thay đổi DB, nên ghi "không có").

## 7. Sai lầm đã mắc (để không lặp lại)

- Gọi agent code bằng Claude khi Admin muốn code qua OpenCode. Đã dừng; debugger để lại WIP chưa kiểm.
- Dispatch hai lần với model sai mà không kiểm định nghĩa agent trước.
- Báo "gọi được" trước khi xác nhận model tồn tại trên tài khoản.
- Đọc `progress_data.json` và báo "đã cập nhật dashboard" trong khi file này bị gitignore và dashboard không tự refresh.

## 8. Điều đã bị bác bỏ

- "Gọi OpenCode/OpenRouter bằng agent `opencode`/`openrouter` của Claude" → **sai**: model trong định nghĩa không khớp tài khoản. Phải dùng OpenCode trong VS Code, hoặc sửa model trước.
- "Hai agent chạy song song được vì khác nền tảng" → **đã kiểm**: cả hai cùng sửa `placevn.html`/`app.py`, nên không chạy song song.

## 9. Lệnh kiểm tra nhanh

```bash
cd "E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
git log --oneline -3
git status --short -- Dai_Tang_Kinh/daoanh/admin/placevn.html Dai_Tang_Kinh/daoanh/app.py Dai_Tang_Kinh/.claude/agents/opencode.md
ls -l Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-21/T445-debugger-wip/
```

Kỳ vọng: 3 file đang `M`; thư mục WIP có `placevn.html` và `app.py`.

## 10. Ghi chú cho agent kế tiếp

- Đọc `AGENTS.md`, `CLAUDE.md` (mục Harness: Claude điều phối, không code).
- Đọc file này và `tasks/T445-placevn-wizard-ui-b0-b9.md`.
- Không revert `placevn.html` về HEAD. Muốn bỏ WIP, hỏi Admin trước.
- Trước khi báo done: `npm run pipeline` phải xanh và có kiểm chứng trên trình duyệt.
