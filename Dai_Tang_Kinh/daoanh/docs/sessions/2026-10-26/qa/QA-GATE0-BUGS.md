# QA-GATE0-BUGS — Kiểm chứng độc lập (2026-10-26)

**Vai trò:** daoanh-qa (chỉ đọc) · Phạm vi: commit Gate 0 `6fc0d799`, đóng bug 048–051, rủi ro index.html.
**Scripts đã tạo:** `docs/sessions/2026-10-26/qa/verify_gate0.py`, `verify_gate0_extra.py` (Flask test_client, KHÔNG start server; DB mode=ro).

## Kết luận tổng: PASS (với 2 rủi ro cần Admin biết — R1, R2)

| # | Mục | Kết quả | Bằng chứng (SHA / số liệu / file:dòng) | Khuyến nghị |
|---|---|---|---|---|
| M1.1 | Commit đúng 2 file | **PASS** | `git show --stat 6fc0d799`: `app.py 98 +`, `index.html 137 +, 1 -`; `git show --numstat` = `98 0 app.py`, `137 1 index.html`; parent = `8bb48c41a8821d3b…` đúng như đề bài. | — |
| M1.2 | app.py diff CHỈ phần DILA | **PASS** | 2 hunk: `@@ -13228,11 +13228,78` (khối DILA trong `api_global_search` ~67 dòng) + 3 key `dila_works/dila_works_total/dila_people` vào `resp` + `@@ -13246,6 +13313,37` (route `public_dila_works`, 31 dòng). Tổng 98 = numstat. Toàn bộ diff ghi chú T453; **KHÔNG** thấy `codex_place_name` (T465) hay hunk T440/T446/T449. | — |
| M1.3 | index.html diff CHỈ phần DILA | **PASS** | 4 hunk: CSS `.dw-*` (+29), div `#dilaWorks` (+3), `handleSearch` thay 1 dòng redirect bằng fetch DILA-first (-1/+6, có `-window.location.href='/daoanh/places?q='`), hàm `renderDilaWorks/renderDilaPeople/loadAllWorks/_esc/_line` + nút "Xem tất cả". | — |
| M1.4 | Không file nào khác; vị trí HEAD | **PASS** | `git diff --stat 6fc0d799 HEAD` → rỗng ⇒ `6fc0d799` chính là HEAD hiện tại, chưa có commit nào phía sau. | — |
| M1.5 | Commit KHÔNG chứa fix T467/T469 | **PASS (đối với nhận định) — RỦI RO R1** | `git show 6fc0d799:Dai_Tang_Kinh/daoanh/index.html` **không chứa** "Khuy Cơ" lẫn "T469". Bản worktree _có_ (index.html:247 CSS sr-suggest, :1180 `closeSuggest()` T469, :1192 comment Khuy Cơ T467, :1217–1337 autocomplete, :1337 gọi route `/daoanh/api/search/suggest`). `git diff --stat HEAD`: `index.html 329 ±`, `app.py 394 ±` và 276 file khác (anomaly mass-deletion đã biết ở repo, không do Gate 0). Hậu quả: nếu checkout/restore/deploy từ commit này → HOME mất card monk "Khuy Cơ" (T467/BUG-052) và autocomplete T469; route `/daoanh/api/search/suggest` cũng chưa có ở commit → dropdown sẽ fetch 404. **Hiện chưa mất** vì worktree còn giữ. | R1: Session sau cần commit tiếp T467/T469 (+T465) đúng phạm vi từng file; trước mắt KHÔNG deploy/restore từ commit này. |
| M2.1 | GET dila_works A000294 | **PASS** | 200, `count=78`, `len_works=78`; mẫu #1 `T0220` — "Đại Bát-nhã Ba-la-mật-đa Kinh"; #2 `T1545` — "A-tì-đạt-ma Đại Tì-bà-sa Luận". | — |
| M2.2 | Thiếu person_id → 400 | **PASS** | 400, `{"error":"person_id required","success":false}`. | — |
| M2.3 | person_id=NOT_EXIST | **PASS** | 200, `count=0`, `len_works=0`. | — |
| M2.4 | search Huyền Trang đủ 3 key | **PASS** | 200; keys = `['dila_people','dila_works','dila_works_total','monks','places','success','works']`; `dila_works=10`, `dila_works_total=81`, `dila_people=1` (A000294 "Huyền Trang", works=78, juans=1341). | — |
| M2.5 | q=a không lỗi | **PASS** | 200 `success:true`, mọi nhóm = 0. | — |
| M2.6 | autocomplete Thiếu L | **PASS** | 200, dict `{"data":[...]}` (shape: dict[data], không phải list/count — frontend T404 đang đọc theo shape này). | — |
| M2.7 | Đối chiếu DB mode=ro | **PASS** | `dila_catalog_works`=**5 747** ✓ mốc; `dila_catalog_contributors`=**5 589** ✓ mốc; works A000294 trực tiếp SQL = **78** = khớp API `count=78`; SUM(juans)=**1 341** = khớp "1.341 quyển" trong tasktodo T453. | — |
| M3.1 | bugs.md đóng BUG-048..051 | **PASS** | `git show b1832c7f --stat`: `docs/bugs.md 94 +`. Điểm cần lưu: diff = **thêm mới 4 entry BUG-048/049/050/051** (không phải "2 dòng BUG-049/050 được đổi" như đề bài ghi — khối này chưa từng có trong bugs.md trước đó). 4 dòng trạng thái: BUG-048 "✅ DONE (2026-10-26) — Admin xác nhận DONE"; BUG-049 "✅ DONE (2026-10-26) — Admin xác nhận DONE. Báo cáo chi tiết gốc (2026-10-20): docs/BUG-049_ETL_PASS_BUTTON_FIX_REPORT.md"; BUG-050 "✅ DONE (2026-10-26) — Admin xác nhận DONE. Báo cáo chi tiết: docs/T436_T437_VERIFY_FIX_REPORT.md"; BUG-051 "✅ DONE (2026-10-26) — Admin xác nhận DONE; code đã sửa và test đạt, xem báo cáo nguồn." | — |
| M3.2 | T435–T438 có "Admin xác nhận DONE (2026-10-26)" | **PASS** | T435: commit `9bf4c021` — `tasks/T435-…md` +2 dòng, gồm "**Admin xác nhận DONE (2026-10-26).** Báo cáo: docs/T435_BUG048_FINAL_REPORT.md (BUG-048). Trạng thái DONE đã ghi trong docs/bugs.md (commit b1832c7f)." T436/T437/T438: commit `78418dfe` — `tasks/backup/T436-…md` (+80), `T437-…md` (+189), `T438-…md` (+59), mỗi file kết thúc "**Admin xác nhận DONE (2026-10-26).**" | — |
| M3.3 | Số liệu bugs.md vs báo cáo gốc | **PASS** | BUG-048: 49 335 / 48 646 (JOIN people) / 48 673 / pct 99.9 — khớp `docs/T435_BUG048_FINAL_REPORT.md:31,34,43,67-70`. BUG-049: `timeout=60`, TimeoutError tái hiện 5 lần 14:30:17→14:32:03 — khớp `docs/BUG-049_ETL_PASS_BUTTON_FIX_REPORT.md:19-39`. BUG-050: 311/311, per_page 50→30, 11 trang tuần tự, `ERR_ABORTED` — khớp `docs/T436_T437_VERIFY_FIX_REPORT.md:56,72,96`. BUG-051: inspector 437.48px, canvas 172.5×430px, camera x=4920, 80 node / 79 edge — khớp `docs/BUG-051_PLACES_LINEAGE_ARROWS_REPORT.md:22-32`. **Không thấy số bịa thêm.** | — |
| M4.1 | handleSearch ưu tiên DILA — truy vấn địa danh | **PASS (phần khôi phục) — RỦI RO R2** | Code commit: demo "Thiếu Lâm/少林" vẫn `showPlaceDemo()` trước; sau đó fetch `/daoanh/api/search` → nếu `dila_works/dila_people` ≠ 0 render DILA, else redirect `placesUrl`; fetch lỗi (catch) cũng redirect. Đo trực tiếp qua test_client: `q=Long Môn` → `dila_works=0, dila_people=0` → redirect `/daoanh/places` ⇒ **hành vi không đổi cho 2 case này**; `q=Long Môn Thạch Quật` tương tự. Nhưng nhánh DILA đứng TRƯỚC logic T467-v2 (`places.length → redirect` — worktree index.html:1206→1210): một địa danh trúng DILA (title/byline/dịch giả chứa tên) sẽ thay redirect địa danh. Đo ví dụ `q=Khuy Cơ` → `dila_works=10`, `dila_people=1`, `monks=1` (A001019) → panel DILA thay card monk. | R2: nếu cần hành vi T467-v2 chặt, kiểm tra `places.length` TRƯỚC nhánh DILA hoặc merge 1 panel chung; hiện chấp nhận được vì còn link phụ "Tìm địa danh →". |
| M4.2 | T454–T457 đủ mục AGENTS §21 | **PASS** | 4 file đều có `## Mô tả` + `### Trạng thái hiện tại` + `### Câu hỏi cần Admin quyết`: T454:22/25/30, T455:27/30/35, T456:25/28/33, T457:31/41/46 (worktree = bản đã commit trong `78418dfe`). T455 còn có `done_when:` frontmatter (dòng 12). | — |
| M4.3 | check-dup-ids | **PASS** | `python -X utf8 scripts/build_progress_data.py --check-dup-ids` → `[OK] Không có task ID trùng thật.` INFO: 5 ID có bản X- superseded + 1 ID docs-note (đều hợp lệ theo quy ước). | — |

## Lỗi cần sửa: 0 (không có lỗi sản phẩm phát hiện ở các hạng mục kiểm)

## Cảnh báo rủi ro (không sửa, dành cho Admin)
1. **R1** — `index.html`/`app.py` đã commit (Gate 0) KHÔNG chứa fix T467 (card monk "Khuy Cơ") và T469 (autocomplete, kể cả route `/daoanh/api/search/suggest`). File sửa của T467/T469 vẫn chưa commit (còn ở worktree). Ghi nhận rõ để phiên sau commit tiếp — KHÔNG để mất.
2. **R2** — `handleSearch`: nhánh DILA nằm trước nhánh `places.length → redirect` (đã hoặc chưa có ở bản commit T467-v2). Query trùng cả DILA lẫn địa danh sẽ ưu tiên DILA. Chấp nhận hiện tại; cân nhắc merge panel sau.

## Chi tiết không kể vào bảng
- API trả `dila_works_total=81` > `count` tác phẩm của người (78) vì bộ WHERE quét thêm title/byline/cbeta_id/contributors — đúng thiết kế (tổng thật cho chữ "hiển thị 10/N" trên UI).
- Bảng `namevi_map_places` dùng cột `dila_id` (không có `place_id`) — lần đầu script phụ của QA truy sai tên cột (lỗi của script, không phải sản phẩm).
- KHÔNG đánh DONE task nào — chỉ Admin được xác nhận DONE.

## Chưa kiểm tra
- Route `/daoanh/api/search/suggest` (T469) chưa verify bằng API (không nằm trong phạm vi commit).
- Hành vi UI thật trên trình duyệt (QA này đo bằng Flask test_client thay trình duyệt).
- DB trên VPS (chỉ kiểm DB local mode=ro).
