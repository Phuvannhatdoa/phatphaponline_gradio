---
id: T437
title: "Bug verify: BUG-050: namevimap.html stuck on Đang tải… (loading) forever"
status: done
created: 2026-10-20
updated: 2026-10-21
done_when: "Trang namevimap.html load xong (không còn kẹt 'Đang tải…'), xác định rõ request/endpoint gây treo, fix đúng lớp (data/API/resolver/renderer), QA xác nhận bằng browser thật + network log trước/sau."
---

## Triệu chứng

- Route: `http://127.0.0.1:8080/daoanh/admin/namevimap.html`
- Trang hiện "Đang tải…" (Loading…) và không bao giờ hoàn tất, hang vô hạn.

## Case tái hiện

1. Mở route trên (hard refresh Ctrl+Shift+R nếu cần).
2. Quan sát: trang kẹt ở "Đang tải…".
3. Kiểm tra browser console: lỗi/warning gì?
4. Kiểm tra Network tab: request nào đang pending/hang (URL, method)?
5. Kiểm tra server logs: `app_local.log`, `gateway_local_err.log` — có lỗi 500/timeout không?
6. Kiểm tra server nào đang chạy: `app.py` (5000), `server.py` (5001), `local_gateway.py` (8080).

## Nguyên nhân nghi ngờ

- Tab ETL `loadEtlFlagLiveData()` trong `namevimap.html` bắn burst requests → backend quá tải → timeout → trang stuck.
- API endpoint trả 500/timeout.
- Có thể liên quan BUG-049 (ETL Pass Button — request timeout không được catch đúng cách), đã có task T436 xử lý riêng — cần xác minh có phải cùng nguyên nhân gốc hay độc lập.

## Phạm vi dự kiến

- Audit: browser console + network + server logs trước khi sửa.
- Xác định lớp lỗi: data / API contract / resolver / renderer / state / async.
- Fix nhỏ nhất đúng lớp gây lỗi. Không hard-code giá trị hiển thị trong component.
- Không git commit, không đổi schema DB, không deploy VPS khi chưa có lệnh.

## File liên quan (dự kiến, backup trước khi sửa)

- `daoanh/admin/namevimap.html`
- `daoanh/app.py`
- `daoanh/local_gateway.py`

## Kết quả audit + fix (2026-10-20)

- Root cause xác minh: tab ETL (mặc định) có 5 fetch nặng tự động, đã có AbortSignal
  nhưng KHÔNG có deadline theo thời gian — chỉ abort khi rời tab. Khi backend chậm
  (quan sát thực tế: tranh chấp khoá SQLite do một tiến trình khác ghi `places/vi-map`
  đồng thời), bảng "Bulk Flag Queue" (`flag-list`) có thể treo ở "Đang tải…" > 50s
  không tự thoát — tái hiện được bằng browser thật.
- Phụ: `codex-namevi.js`/`.css` vẫn include dù DOM target đã bị xoá ở commit a4397c2a
  (cleanup GPT Sol) — ném lỗi console mỗi lần tải trang, dead code, đã gỡ.
- Fix: thêm deadline cứng 45s trong `_etlNewAbortSignal()` — hết giờ tự abort + ghi
  thông báo lỗi rõ ràng vào bảng đang kẹt, nút "Load" vẫn dùng để thử lại. Không đổi
  API/DB/schema.
- Test: tái hiện hang thật > 50s trước fix; sau fix tự thoát đúng 45s ra thông báo lỗi;
  bấm Load phục hồi thành công; tab Queue và route `/daoanh/places` không regression.
- Vận hành: phát hiện `server.py` (port 5001) không chạy lúc bắt đầu audit — đã khởi
  động lại theo CLAUDE.md.
- Report: `daoanh/docs/BUG050_NAMEVIMAP_STUCK_LOADING_REPORT.md`
- Còn lại: chưa sửa nguyên nhân sâu (tranh chấp khoá SQLite dưới tải ghi đồng thời) —
  ngoài phạm vi task (không đổi schema/DB). Chờ Admin xác nhận DONE.

## Audit lại 2026-10-20 (vòng 2) — root cause THỰC SỰ là bug JS, không chỉ backend chậm

Tái hiện trực tiếp bằng browser thật (route trên, đã login): bảng "Bulk FLAG Queue" kẹt
"Đang tải…" dù backend đang RẢNH lúc audit vòng 2 (không có tiến trình nào khác ghi DB đồng
thời) — nguyên nhân chính KHÔNG phải tranh chấp khoá SQLite như report vòng 1, mà là lỗi
state JS trong `switchTab()` (cùng root cause với T435 vòng 2, xem file
`T435-bug048-claude-column-no-count.md`):

- Vào tab ETL lần đầu → `_etlFullLoad()` gọi `etlFlagQueueLoad` (flag-list) dùng
  `AbortSignal` chung.
- Quay lại tab ETL lần sau (trước khi lần tải đầu xong) → nhánh `else` trong `switchTab()`
  (dòng 1041-1044) gọi `_etlNewAbortSignal()`, hàm này abort NGAY controller cũ — giết
  `etlFlagQueueLoad` đang chạy dở — nhưng nhánh `else` KHÔNG gọi lại `etlFlagQueueLoad`.
  Request `flag-list` bị abort vĩnh viễn, không có request thay thế → bảng kẹt
  "Đang tải…" mãi mãi, đúng y triệu chứng admin báo (không bao giờ hết dù không phải do
  timeout 45s).
- Deadline cứng 45s thêm ở vòng 1 (`_etlNewAbortSignal` dòng 1544-1552) có giúp (sau 45s tự
  ghi lỗi) nhưng KHÔNG sửa root cause — nếu Admin chuyển tab qua lại trước 45s (hành vi tự
  nhiên khi chờ lâu), bug tái diễn ngay.

Fix root cause (nhánh `else` gọi đủ `etlFlagQueueLoad`/`loadAiColStatus`/`loadCodexColStatus`)
đã giao `daoanh-debugger` xử lý chung với T435 vòng 2 (cùng file, cùng hàm `switchTab()`) —
không tách thêm 1 lượt sửa riêng để tránh 2 agent đụng cùng 1 vùng code cùng lúc.

## Redesign "progressive load" theo yêu cầu admin — ĐỀ XUẤT, CHƯA LÀM

Admin yêu cầu thay "chờ 45s → lỗi → thử lại" bằng tải tăng dần (hiện row ngay khi có, không
chờ hết). Đề xuất kỹ thuật (chưa code, chờ admin duyệt hướng trước khi giao `daoanh-debugger`):

1. **`etlFlagQueueLoad()` hiện tại**: gọi 1 API `GET /api/admin/namevi/flag-list?page=1&per_page=50`
   → nhận cả 50 dòng 1 lần → render cả bảng 1 lần. Đây là nguyên nhân "tất cả hoặc không gì"
   — không phải do thiếu AbortSignal (đã có) mà do API trả nguyên khối.
2. **Hướng A — phân trang nhỏ hơn + render từng trang ngay khi về (khuyến nghị, ít thay đổi
   nhất, không đổi API)**: giảm `per_page` xuống ví dụ 10, gọi tuần tự nhiều trang
   (`page=1`, `page=2`, ...), mỗi trang về tới đâu `appendRows()` tới đó thay vì chờ gộp đủ
   rồi mới render. Admin thấy dòng xuất hiện dần theo từng đợt 10 dòng. Không cần sửa
   `app.py`/API, chỉ sửa vòng lặp JS gọi fetch.
3. **Hướng B — infinite scroll thật**: chỉ gọi `page=1` lúc đầu, gọi `page=2` khi Admin
   scroll gần cuối bảng. Tải nhanh hơn lúc đầu (ít dữ liệu hơn) nhưng cần thêm scroll
   listener + "còn N trang, scroll để tải thêm" — đổi UX nhiều hơn hướng A.
4. **Badge "đang tải thêm…"** thay cho lỗi cứng: nếu 1 trang cụ thể chậm/lỗi, chỉ trang đó
   hiện badge lỗi + nút "thử lại trang này", các trang đã tải vẫn hiển thị — không xoá sạch
   bảng như hành vi lỗi hiện tại.
5. Giữ deadline 45s hiện có làm giới hạn CUỐI (an toàn) cho MỖI trang nhỏ, không cho cả lượt
   tải — vì mỗi trang nhỏ hơn nên thời gian chờ hợp lý cũng nên nhỏ hơn (đề xuất 15s/trang,
   admin có thể chỉnh).

Khuyến nghị: Hướng A (đơn giản, không đổi API, rủi ro thấp, đúng yêu cầu "hiện row ngay khi
có"). Hướng B tốn công hơn, chỉ nên làm nếu Admin muốn tối ưu thêm tải trang đầu.

## Kết quả triển khai Hướng A + verify switchTab() (2026-10-21)

- **switchTab() vòng 2:** audit lại bằng code + browser thật xác nhận fix đã được áp dụng
  TRƯỚC khi phiên này bắt đầu (cả 2 nhánh if/else gọi chung `_etlFullLoad()`, dòng
  1030-1050). Verify thực tế: chuyển tab đi/về liên tục nhiều lần ngay lúc đang tải →
  request cũ `ERR_ABORTED` nhưng luôn có request thay thế, bảng không kẹt, cuối cùng vẫn
  load đủ. Không sửa thêm phần này.
- **Progressive load Hướng A:** đã triển khai trong `daoanh/admin/namevimap.html`
  — `_ETL_FLAG_PER_PAGE` 50→30, hàm mới `etlFlagQueueLoadAll()` +
  `_etlFlagLoadPageSeq()` tải tuần tự từng trang và render ngay, badge "Đang tải trang
  N…", deadline riêng 15s/trang, lỗi 1 trang không xoá sạch bảng (badge lỗi + nút Thử
  lại tại `_etlFlagRetryPage()`). 6 điểm gọi tải-lại-từ-đầu đổi sang
  `etlFlagQueueLoadAll()`.
- **Test:** network log xác nhận 11 request tuần tự `page=1..11&per_page=30` đều 200 OK,
  badge cuối đúng tổng 311/311; chuyển tab liên tục trong lúc tải không làm kẹt bảng;
  cột Claude/Gemini header giữ đúng số; regression tab Xác Minh/Place/`/daoanh/places`
  đều OK. `node --check` JS syntax OK (không có `.py` nào bị sửa).
- **Backup:** `daoanh/docs/sessions/2026-10-21/T437/namevimap.html.before_progressive_load.bak`
- **Report:** `daoanh/docs/T436_T437_VERIFY_FIX_REPORT.md`
- **Còn lại:** chưa ép tái hiện được nhánh lỗi/retry 1 trang bằng network thật (môi trường
  local đang nhàn, không timeout tự nhiên) — logic đã review kỹ nhưng chưa có bằng chứng
  network log cho nhánh này. Không git commit. Chờ QA + Admin xác nhận DONE.

**Admin đã chọn Hướng A (2026-10-20, qua điều phối).** Giao `daoanh-debugger` triển khai:
per_page 100→30, gọi tuần tự nhiều trang, render từng trang ngay khi về, badge
"Đang tải trang N…" thay cho lỗi cứng 45s cho toàn bộ lượt tải (giữ deadline nhỏ hơn
mỗi trang, ví dụ 15s/trang, không chặn cả danh sách). Đồng thời vá chung root cause
vòng 2: nhánh `else` trong `switchTab()` (namevimap.html dòng 1041-1044) phải gọi lại
đủ `etlFlagQueueLoad`, `loadAiColStatus`, `loadCodexColStatus` khi quay lại tab ETL
— không chỉ `loadEtlFlagLiveData` — để tránh request bị abort vĩnh viễn không có
request thay thế (cùng file, cùng vùng code với T435 vòng 2, làm chung 1 lượt sửa).

## QA vòng 2 (2026-10-21) — 2 lỗi còn lại, đã sửa

QA kiểm tra bản progressive load Hướng A, báo CHƯA ĐẠT 2 lỗi cụ thể:

1. Deadline 45s chung (`_etlNewAbortSignal()`) vẫn abort + ghi đè `flagBody.innerHTML`
   của bảng `etl-flag-queue-body` dù bảng này đã có deadline riêng 15s/trang — xoá sạch
   bảng khi server chậm, trái mục tiêu BUG-050.
2. `runAiBatch()` dòng ~2672 vẫn gọi hàm cũ `etlFlagQueueLoad(_etlFlagPage || 1)` thay vì
   `etlFlagQueueLoadAll()` sau khi AI batch xong — chỉ hiện 1 trang (30/311 dòng) thay vì
   đủ 311.

**Fix:** tách bảng flag-queue khỏi `ctrl`/deadline 45s bằng `AbortController` riêng
(`_etlFlagTabCtrl`, không gắn timer, chỉ abort khi rời/quay lại tab ETL); đổi dòng
`runAiBatch()` sang gọi `etlFlagQueueLoadAll()`. Backup:
`daoanh/docs/sessions/2026-10-21/T437/namevimap.html.before_round2.bak`.
Test browser thật: progressive load 11/11 trang 200 OK → 311/311; chuyển tab liên tục
lúc đang tải không kẹt/không xoá bảng (network log xác nhận abort đúng lượt cũ, lượt
mới hoàn tất đủ); regression tab Xác Minh/Place/`/daoanh/places` đều OK. Chi tiết:
`daoanh/docs/T436_T437_VERIFY_FIX_REPORT.md` mục "Vòng 2 — sửa theo QA".
Còn lại: chưa ép tái hiện 45s-chậm-thật bằng network throttle (không có công cụ
throttle trong Browser pane) — verify bằng đọc code (2 AbortController tách biệt hoàn
toàn, không phải race condition phụ thuộc thời gian). Chờ Admin xác nhận DONE.

## Verify bằng browser thật (2026-10-21, điều phối tự mở browser do agent thiếu công cụ browser)

- Mô phỏng đúng race condition: chuyển tab ETL → Xác Minh → ETL → Xác Minh → ETL liên tiếp
  nhanh (trước khi lượt tải trước xong). Network log thật xác nhận progressive load Option A
  đã chạy: `GET /api/admin/namevi/flag-list?page=1&per_page=30...` qua `page=11` tuần tự,
  cùng `loadAiColStatus`/`loadCodexColStatus` gọi lại đúng (header Claude/Gemini vẫn hiện số
  48,646/48,673 và 48,673/48,673 sau khi chuyển tab qua lại nhiều lần — không mất số như bug
  cũ của T435 vòng 2).
- Do server cục bộ đang chậm thật lúc test (nhiều request dồn từ việc chuyển tab liên tục),
  trang 1 timeout đúng 15s và hiện lỗi rõ ràng "Lỗi: quá thời gian chờ (15s) ở trang 1 — server
  đang chậm" kèm nút "Thử lại" — ĐÚNG hành vi mong muốn (không còn kẹt "Đang tải…" vô hạn như
  bug gốc). Click "Thử lại" → tải lại thành công, bảng phục hồi đủ 310/310 dòng.
- Regression: Tab Place (`place-tab-btn`) vẫn load đúng 59,167 địa danh, banner "Cột
  Claude/Gemini đang trống (giai đoạn 2, chưa triển khai)" hiển thị đúng như code — xác nhận
  đây là placeholder cố ý, KHÔNG phải bug, không thuộc phạm vi T437/T435.
- Không console error.

## Xác nhận DONE

Admin xác nhận DONE 2026-10-21.

**Admin xác nhận DONE (2026-10-26).** Báo cáo: docs/T436_T437_VERIFY_FIX_REPORT.md (BUG-050). Commit docs xem git log.
