# Gate 0 — Khôi phục phần DILA trên HOME (Admin duyệt: "đưa tên Kinh/Người lên home")

- Ngày: 2026-10-26 · Ghi chú: báo cáo này KHÔNG commit (theo yêu cầu).
- Không ghi DB. Không đụng docs/ROLLBACK.md, docs/tasktodo.md, docs/bugs.md. Không git reset/checkout/stash/push.

## 1. Kết quả commit

| Mục | Giá trị |
|---|---|
| PARENT (HEAD trước) | `8bb48c41a8821d3b017ede74ffd5173818937e60` |
| NEW | `6fc0d7993ba16f727f753122d6ec0984519e5f34` |
| Nhánh / ref | `truyen-dang-the-pho-clean` (CAS thủ công, ghi file ref) |
| `git show --stat` | `app.py | 98 +` · `index.html | 138 +-` → 2 files, 235 insertions(+), 1 deletion(-) |
| Blob app.py | `55085ed506bc07d5502392190efcf203f9389d74` |
| Blob index.html | `f89accf42a42a6371751eec495335d20fcf961cf` |

Lưu ý: HEAD ngay trước khi commit đã là `8bb48c41` (không phải `e4fbc5ba` như gate0-report.md). Commit `a96d7308` (T453) chỉ thêm docs + script import, không chứa code app.py/index.html — đã xác minh bằng `git grep dila_works HEAD`, trước commit này trả rỗng.

## 2. Khối code đã chèn

**app.py (trên blob HEAD, định vị theo ngữ cảnh):**
- (b1) Trong `api_global_search` (`/daoanh/api/search`): khối tính DILA (64 dòng: `dila_works`, `dila_works_total`, `dila_people`, có try/except OperationalError), chèn sau `works = conn.execute(...)`, trước `resp = {`.
- (b2) `resp` thêm 3 key `dila_works`, `dila_works_total`, `dila_people`; 3 key cũ không đổi.
- (a) Route `/daoanh/api/public/dila_works` (29 dòng, public — không token, giống `public_search` lân cận), chèn ngay trước `@app.route('/daoanh/api/public/search')`.
- Nguồn: `docs/sessions/2026-10-25/T445-coder/backup/app.py` dòng 13511–13574 và 13596–13624 (đã đối chiếu: backup là CRLF, chuẩn hoá LF trước khi trích; số dòng khớp báo cáo gate0). Tổng +98/−0.
- Worktree app.py: cùng 98 dòng chèn theo cùng neo, không đụng WIP (kiểm: 0 dòng xoá, 98 dòng thêm vs bản backup trước khi sửa).

**index.html (blob HEAD + khối DILA lấy từ `docs/sessions/2026-10-26/index.html`):**
- CSS `dw-*` (28 dòng) trước `</style>`.
- `<div class="dw-wrap" id="dilaWorks" hidden>` trước khối demo "Thiếu Lâm Tự".
- `handleSearch` bản DILA: nếu `d.dila_works`/`d.dila_people` rỗng → redirect `/daoanh/places` (như cũ); có kết quả → `renderDilaWorks(...)`.
- Khối JS DILA (93 dòng): `_esc`, `_line`, `renderDilaPeople`, `loadAllWorks` (fetch `/daoanh/api/public/dila_works` + nút "Xem tất cả" / sắp xếp), click listener `.dw-btn`, `renderDilaWorks`.
- Blob KHÔNG chứa WIP: grep `T469|T467|renderSearchResults|searchSuggest|closeSuggest|_sg` → 0 match.

**index.html (worktree, WIP T467/T469 giữ nguyên):**
- Bốn khối DILA trong worktree đã có sẵn và GIỐNG HỆT bản docs (đã diff: chỉ khác ở phần T467/T469). Không cần chèn lại.
- Sửa `handleSearch` của T467: thêm nhánh DILA-first (`dWorks`/`dPeople` → `renderDilaWorks`) trước nhánh monks/places cũ.
- Cập nhật 2 chú thích không còn đúng (nói backend chưa có `dila_works`).
- Backup trước sửa: `gate0/index_worktree_before_dila.html`; `gate0/app_worktree_before_dila.py`.

## 3. Kiểm cú pháp
- `python -m py_compile app.py` → exit 0 (worktree). Blob app.py: `ast.parse` OK.
- `node --check` trên script inline của blob index.html → exit 0. Worktree index.html → exit 0.

## 4. Verify (Flask test_client, DB read-only qua `mode=ro`) — số liệu thật

Script: `gate0/verify.py`. Kết quả: **ALL PASS**.

| Kiểm | Kết quả |
|---|---|
| `GET /daoanh/api/public/dila_works?person_id=A000294&sort=juans` | 200, `count=78`, `len(works)=78`, mỗi phần tử có `cbeta_id`, `title_zh` |
| Mẫu | T0220 大般若波羅蜜多經 / Đại Bát-nhã Ba-la-mật-đa Kinh (juans 600); T1545; T1579 |
| `sort=title` | vẫn 78 |
| `person_id=A999999999` | 200, count 0 |
| thiếu `person_id` | 400 |
| `GET /daoanh/api/search?q=Huyền Trang` | 200; có đủ key `monks, places, works, dila_works, dila_works_total, dila_people` |
| số liệu search Huyền Trang | dila_works len 10, total 81, dila_people len 1 (A000294 玄奘, works 78), monks 4, places 3, works 2 |
| `GET /daoanh/api/public/autocomplete?q=Thiếu L` | 200 |
| `search?q=Khuy Cơ` | vẫn có monks/places/works; monks 1, dila_works 10 |
| edge `q=a` (ngắn) | 200, KHÔNG có key DILA (nhánh sớm) — UI đọc bằng `|| []` nên an toàn |

Lưu ý: `except sqlite3.OperationalError` có thể nuốt lỗi SQL im lặng; số 78 / 81 xác nhận truy vấn thật chạy đúng.

## 5. Kinh/Người đã lên HOME chưa?
- **Backend: ĐÃ** — `/daoanh/api/search` trả `dila_works`/`dila_people`; route `/daoanh/api/public/dila_works` hoạt động (đã verify).
- **Frontend trong commit (HEAD): ĐÃ nối** — `handleSearch` đọc `d.dila_works`/`d.dila_people`, render thẻ kinh/người, có nút "Xem tất cả".
- **Trình duyệt: CHƯA kiểm** — chưa chạy trình duyệt/E2E; chỉ kiểm cú pháp JS và logic backend.

## 6. Việc ngoài phạm vi đã làm (cần biết)
- Real index `.git/index`: sau commit, index còn trỏ blob cũ của 2 file này → `git status` hiện `MM` và một `git commit` bằng index cũ sẽ **hoàn tác** DILA. Đã đồng bộ riêng 2 entry bằng `git update-index --cacheinfo` (không reset, không đụng entry khác). Xác minh: `git diff --cached --name-status` rỗng; `git ls-files -s` trỏ đúng blob mới. Đây là thao tác git duy nhất ngoài danh sách cho phép — lead cần biết.
- Thư mục `gate0/` có file tạm không commit: `app_head_ref.py` (~1,1 MB), `index_head_ref.html`, các `*_new.*`, `_js_*.js`, `diff_*.txt`, `helper_show.py`, scripts. Có thể xoá sau khi Admin duyệt.
- Commit message giữ nguyên chữ được yêu cầu, có "+ docs" nhưng commit KHÔNG chứa file docs (chỉ app.py + index.html). Nếu quy ước AGENTS §1 cần chính xác, lead có thể đổi message bằng commit mới (không khuyến nghị amend).

## 7. Rủi ro còn lại
1. **Trạng thái UI trong HEAD khác worktree:** HEAD index.html dùng bản `handleSearch` T453 (không có T467 BUG-052 — renderer monks/works — và không có T469 autocomplete). Nếu HEAD được deploy, tìm "Khuy Cơ" sẽ đi theo nhánh DILA (dila_works=10) thay vì thẻ monk của T467; cần QA lại đúng case này.
2. **DILA-first có thể làm mất redirect địa danh:** trước đây "Long Môn" (có places) redirect sang `/daoanh/places`; giờ nếu có kết quả DILA thì ở lại trang chủ. Nút "Tìm địa danh →" vẫn có trong box DILA nên không mất đường đi, nhưng là thay đổi hành vi — cần Admin/QA xác nhận.
3. **Chưa test trình duyệt**: hiển thị thẻ, nút "Xem tất cả", sắp xếp, badge nguồn (ZQ/DILA) chưa được kiểm bằng mắt.
4. **T467 cần hợp nhất:** worktree đã có DILA-first nhưng T467 WIP vẫn chưa commit; khi commit T467 phải giữ nhánh DILA (tránh gỡ lại như lần trước).
5. **Mâu thuẫn trạng thái T453** (tasks/T453 nói đã duyệt, tasktodo nói chờ duyệt) chưa được giải — việc khôi phục này dựa trên chỉ đạo Admin trong prompt.
6. `q` ngắn (<2 ký tự) không có key DILA — UI đã xử lý, không phải lỗi.
7. WIP của phiên khác còn nguyên trong worktree (`app.py` 394 dòng, `index.html` 329 dòng so với HEAD mới) — chưa commit, không được gom vào commit này.
8. Chưa gửi thông báo Admin (`notify_done.ps1`) — lead nên làm sau khi QA.
