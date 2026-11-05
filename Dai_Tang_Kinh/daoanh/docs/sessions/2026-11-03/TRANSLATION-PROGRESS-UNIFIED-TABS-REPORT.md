# Gộp trang tiến độ dịch vào `translation_progress.html` (Tab T50 + Tab Dịch Nexus)

| | |
|---|---|
| Ngày | 2026-11-03 |
| Nhánh | `wt/t50-translation-tabs` (worktree `C:/Users/Nam Thien/.claude/worktrees/t50-translation-tabs`) |
| Base | `truyen-dang-the-pho-clean` @ `058c9631` |
| File sửa | `daoanh/admin/translation_progress.html` (chỉ sửa bằng Edit theo anchor, không Write toàn file) |
| File KHÔNG đổi | `daoanh/admin/t50-progress.html`, `daoanh/app.py` |
| Commit vào cây chính | **CHƯA** — chờ Admin duyệt rồi chạy `scripts/wt_integrate.py t50-translation-tabs` |

## 1. Đọc trong 2 phút

- `daoanh/admin/translation_progress.html` ở cây chính đã sẵn 2 Tab: "Tiến Độ Dịch"
  (Gemini địa danh) và "Dịch Nexus" (T458, chỉ đọc, API `/daoanh/api/admin/nexus-translate-status`
  — **đã tồn tại sẵn**, không cần tạo mới). Task này chỉ cần thêm Tab thứ 3.
- Đã thêm **Tab "T50 — Dịch Kinh"**: chuyển nguyên logic Tab 1 của
  `daoanh/admin/t50-progress.html` (Dịch/Dừng/job-status/dashboard số liệu) vào trang dùng
  chung, gọi đúng các route đã có sẵn: `/daoanh/api/admin/t50-progress`,
  `/daoanh/api/admin/t50/{run,stop,job-status,enqueue,dequeue}`. Không sửa `app.py`, không
  sửa route nào.
- Đã thêm **TAB_REGISTRY** (cấu hình JS) để thêm Tab mới (bộ kinh khác) sau này chỉ cần: 1 nút
  trong `.page-tabs`, 1 `<div id="tab-<id>">`, 1 dòng đăng ký `{id: {loaded:false, init:fn}}` —
  không phải sửa `switchPage()`.
- **KHÔNG** mang theo Tab phụ "Đại Tạng Kinh Catalog" + modal đọc kinh của
  `t50-progress.html` — ngoài phạm vi yêu cầu (Admin chỉ nêu Dịch/Dừng/job-status/dashboard).
- `t50-progress.html` cũ: **giữ nguyên, không đổi** (xem mục 6 — lý do + câu hỏi cho Admin).
- Đã kiểm UI thật qua proxy tạm (xem mục 4): Tab T50 render đúng dữ liệu sống (44.820 passage
  tổng, 1.735 đã dịch, 69 bộ kinh, nút "Dịch" theo từng bộ); Tab Dịch Nexus + Tab Tiến Độ Dịch
  không bị regression.

## 2. Thay đổi cụ thể trong `translation_progress.html`

4 patch bằng Edit (anchor), không ghi đè toàn file:

1. **CSS** — thêm khối `.t50-*` (prefix riêng để không đụng `.badge`, `.btn`, `.tbl` sẵn có
   của Tab "Tiến Độ Dịch"): `.t50-cards/.t50-card`, `.t50-job-panel`, `.t50-queue-panel`,
   `.t50-sigla-row`, `.t50-prog-bar`, `.t50-btn-run`, `.t50-tbl`, `.t50-badge`, v.v.
2. **Nút tab** — thêm `<button id="pagetab-t50" onclick="switchPage('t50', this)">T50 — Dịch Kinh</button>`
   vào `.page-tabs`.
3. **Pane** — thêm `<div id="tab-t50" class="tab-pane">` (queue panel, job panel,
   `#t50-main-content`) sau `</div><!-- /tab-nexus -->`.
4. **JS** — thay `switchPage()` cũ (hard-code `if (id==='nexus' && !_nxLoaded) nxLoad()`)
   bằng `TAB_REGISTRY` tổng quát; thêm toàn bộ hàm `t50Init/t50Refresh/t50RenderProgress/
   t50RenderSiglaRows/t50RenderQueuePanel/t50CheckJobStatus/t50Enqueue/t50Dequeue/
   t50StopJob/t50StartPolling/t50StopPolling` — namespace riêng (`t50` prefix), tránh đụng
   biến/hàm của 2 Tab cũ (`_nxLoaded`, `nxLoad`, `load`, `renderRows`, ...).

Diff đầy đủ: `git -C "<worktree>" diff -- Dai_Tang_Kinh/daoanh/admin/translation_progress.html`
(chưa commit tại thời điểm viết báo cáo).

## 3. Nguồn dữ liệu Nexus đã khảo sát

- `/daoanh/api/admin/nexus-translate-status` (app.py dòng 1154) **đã tồn tại** — trả về
  `total_nexus`, `total_translated`, `total_batches`, `books[]` (book/total_nexus/translated/
  batches/pct/note) đọc từ bảng staging JSONL T458 (`Mingsengzhuanchao` là sách duy nhất có
  batch thật, 10/188 đã dịch; các sách khác ghi chú "Chưa có batch JSONL cho sách này").
  → **Không cần bịa dữ liệu** — Tab Dịch Nexus hiển thị đúng trạng thái "chưa có dữ liệu" cho
  8/9 sách, đúng yêu cầu của Admin.
- Có 1 route Nexus khác cùng tên gây nhầm `nexus_events` (app.py dòng ~5507, 5608
  `/daoanh/api/nexus-find`) — đây là Nexus **đồ thị person-place** (dùng cho trang bản đồ/
  đồ thị), KHÁC với Nexus **tiến độ dịch** (T458 staging JSONL). Không đụng tới route này.
- Nhánh worktree khác `wt/nexus-translate-tab` (T514, local tại
  `C:/Users/Nam Thien/.claude/worktrees/nexus-translate-tab`) đang mở rộng Tab Dịch Nexus
  thành bảng so sánh 4 bản dịch (Gemini/Claude/Codex/Hán gốc) **trong `t50-progress.html`**,
  chưa merge vào cây chính. Không đụng tới nhánh đó trong task này — nếu Admin merge T514 sau,
  cần đối chiếu lại Tab Dịch Nexus ở `translation_progress.html` (đang là bản T458 đơn giản,
  chỉ đọc) để tránh 2 bản song song.

## 4. Bằng chứng kiểm tra (browser thật, không job dịch nào được bấm)

**Vì sao không test trực tiếp trên `127.0.0.1:8080`:** server đang chạy ở cổng 8080/5000/5001
phục vụ file tĩnh từ **cây chính** (`local_gateway.py` trỏ `BASE_DIR` = cây chính); file đã sửa
nằm trong worktree, chưa có trong cây chính (đúng ràng buộc #1 — không ghi cây chính). Để kiểm
UI thật bằng dữ liệu sống mà không đụng cây chính, đã dựng 1 proxy tạm
(`C:\...\scratchpad\t50tabs_test_proxy.py`, KHÔNG phải code dự án, không commit) chạy ở
`127.0.0.1:8732`: phục vụ tĩnh file từ worktree + proxy `GET /daoanh/api/*` sang
`127.0.0.1:5000` (app.py thật đang chạy, không qua gateway 8080 để không cần sửa CORS).
Đã tắt proxy ngay sau khi kiểm xong.

- Mở `http://127.0.0.1:8732/translation_progress.html` → 3 nút Tab hiện đúng: "Tiến Độ Dịch",
  "Dịch Nexus (T458)", "T50 — Dịch Kinh".
- Click Tab **T50 — Dịch Kinh**:
  - Network: `GET /daoanh/api/admin/t50-progress` → 200, `GET /daoanh/api/admin/t50/job-status`
    → 200 (proxy sang app.py thật port 5000).
  - UI render đúng: badge "● Live API", 6 card (Tổng passage 44.820, Đã dịch 1.735 (3.9%),
    Còn thiếu 43.085, Gắn địa danh 7.158 (24.2%), Bản nháp AI 1.735, Cache 1.726), danh sách
    69 bộ kinh với progress bar + nút "Dịch" (không bấm), bảng "5 passage mới nhất đã dịch"
    có Hán văn + bản dịch Việt + badge "Nháp AI".
  - `job-status` trả `"running": false` lúc kiểm → đúng là **không có job nào đang chạy**;
    job-panel/"Dừng" ẩn đúng logic (chỉ hiện khi `running: true`). Không bấm nút "Dịch" nào.
- Click Tab **Dịch Nexus (T458)**: vẫn hoạt động như cũ — 21.740 tổng nexus, 10 đã dịch,
  1 batch, bảng 9 sách với ghi chú "Chưa có batch JSONL" cho 8 sách. **Không regression.**
- Tab **Tiến Độ Dịch** (Gemini): báo lỗi `Unexpected token '<'...` — **lỗi có sẵn từ trước khi
  sửa** (route `/daoanh/api/admin/gemini-progress` không tồn tại trong `app.py`/`server.py`
  nhánh này — đã `grep` xác nhận không có định nghĩa route này ở cả 2 file). Đã test lại bằng
  bản backup gốc (`...before_integrate_backup`) qua cùng proxy: lỗi giống hệt → xác nhận
  **không phải do patch của task này gây ra**.
- Console: không có lỗi JS (TypeError/SyntaxError) nào khi mở trang hoặc chuyển Tab — chỉ có
  2 lỗi mạng 404 (route gemini-progress nói trên), không liên quan Tab T50/Nexus.
- Kiểm cú pháp: đếm ngoặc `{}`/`()` trong toàn bộ `<script>` — cân bằng (90/90, 297/297).
  (File là `.html`, không áp dụng `python -m py_compile`; không có file `.py` nào bị sửa.)

## 5. File đã đổi / tạo

| File | Loại |
|---|---|
| `daoanh/admin/translation_progress.html` | Sửa (4 Edit theo anchor) |
| `daoanh/docs/sessions/2026-11-03/translation_progress.html.before_integrate_backup` | Backup trước sửa |
| `daoanh/docs/sessions/2026-11-03/t50-progress.html.before_integrate_backup` | Backup trước sửa (không dùng, vì không đổi file này — giữ để đối chiếu) |
| `daoanh/docs/sessions/2026-11-03/TRANSLATION-PROGRESS-UNIFIED-TABS-REPORT.md` | Báo cáo này |

## 6. Câu hỏi cần Admin quyết

**`t50-progress.html` cũ — giữ nguyên hay chuyển hướng?**
Đã chọn **giữ nguyên, không đổi** trong lần này, vì 2 lý do:
1. Có nhánh worktree khác (`wt/nexus-translate-tab`, T514) đang sửa tiếp chính file
   `t50-progress.html` (thêm bảng so sánh 4 bản dịch), chưa merge. Nếu redirect ngay bây giờ,
   khi T514 merge sau sẽ đụng conflict không cần thiết trên file đang bị "khóa" bởi redirect.
2. Tránh phá route cũ đang có thể đang được người khác bookmark/dùng trong lúc 2 nhánh song song
   chưa hợp nhất.

Đề xuất: sau khi Admin xác nhận DONE Tab T50 trong `translation_progress.html` **và** quyết
định số phận nhánh T514, mới thêm 1 dòng JS redirect (`location.replace('translation_progress.html#t50')`)
vào đầu `t50-progress.html`, hoặc xóa hẳn nếu Admin không cần giữ URL cũ.

## 7. Lệnh revert

```bash
# Trong worktree (chưa đụng cây chính, nên chỉ cần thao tác trong worktree):
cd "C:/Users/Nam Thien/.claude/worktrees/t50-translation-tabs/Dai_Tang_Kinh/daoanh"
cp docs/sessions/2026-11-03/translation_progress.html.before_integrate_backup \
   admin/translation_progress.html
```
Nếu đã `wt_integrate.py` merge vào cây chính: `git revert --no-edit <sha-merge-commit>`.

## 8. Việc chưa làm / giới hạn

- Chưa test Nút "Dịch"/"Dừng" thật (đúng ràng buộc #4 — không chạy job lúc test).
- Chưa kiểm trên trình duyệt thật tại `127.0.0.1:8080` với file đã sửa (chỉ kiểm được qua proxy
  tạm vì file chưa có trong cây chính — xem mục 4). Sau khi `wt_integrate.py` merge, nên mở lại
  `http://127.0.0.1:8080/daoanh/admin/translation_progress.html` để xác nhận lần cuối trên route
  thật (khuyến nghị: lặp lại đúng kịch bản click 3 Tab + đọc network log như mục 4).
- Chưa tạo `tasks/T<id>-*.md` cho việc này (Admin chưa cấp số T, nêu rõ nếu cần task file theo
  AGENTS §16 trước khi merge).
- `t50-progress.html` cũ chưa redirect — xem câu hỏi mục 6.
