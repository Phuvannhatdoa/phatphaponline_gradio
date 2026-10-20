# Kiểm chứng 10Case01-BigPickle (Design Plan)

**Ngày:** 2026-10-13 ~20:15 · **Người kiểm:** Claude Code (Remote Control) · **Chế độ:** chỉ đọc (SQLite `mode=ro`, đọc code).
**Đối tượng:** [`10Case01-BigPickle.md`](10Case01-BigPickle.md), đối chiếu đề bài [`10Case01.md`](10Case01.md).

> ⚠️ **Lưu ý về DB lúc kiểm.** Khoảng 20:09–20:10, `data/lineage.db` đang được một phiên khác chép đè (586 MB → 1,15 GB →
> 1,6 GB; khi đang chép, SQLite báo `database disk image is malformed`). App.py lúc đó đang tắt; có hoạt động T380 restore
> (19:34–20:02). Sau khi file ổn định, `integrity_check` 4 bảng chính = ok. Mọi số liệu dưới đây đo trên DB **sau** 20:10.
> `vn_person_authority` là 1.511 dòng (trước khi thay là 1.074). Cần xác nhận với phiên T380 rằng đây là DB đúng.

## Kết luận

**Phần phân tích đề bài và kiến trúc là đúng hướng.** Bản kế hoạch tóm tắt đúng 9 case, 3 chế độ, 5 nguyên tắc. Các tham
chiếu code chính đều có thật: `?level=` ở `app.py:18273-18278, 18352`; `generation_engine_v2.py` (`VERSION`, `validate_scheme:90`,
`schemes:172`, `parents:197`, `compute:235`); `places.html` `_daPersona:10395`. Answer Envelope và orchestrator chỉ đọc,
không gọi LLM là thiết kế tốt.

**Nhưng kế hoạch chỉ thiết kế lớp API/hiển thị, coi dữ liệu là đã sẵn.** Kiểm trên DB thật thì **6/9 case chưa thể trả lời
đúng chỉ bằng lớp API mới**, vì dữ liệu nền đang sai, thiếu hoặc chưa nối. Ngoài ra có 1 mâu thuẫn trong chính bản kế
hoạch (L1 ẩn candidate trong khi case 2 bắt buộc hiện candidate có cảnh báo).

## Kiểm từng case trên dữ liệu thật

| Case | Trả lời được ngay? | Bằng chứng (đo 2026-10-13) | Bản kế hoạch có xử lý? |
|---|---|---|---|
| 1 Diên Phúc Tuệ Thăng | **Gần được** | `vn_person_authority.dien_phuc_tue_thang` → `A008431` (延福慧升), status `verified`, "Dòng Lâm Tế Dương Kỳ", đời 50. Thầy `A007993` (Dục Vương Đoan Dụ 育王端裕) có từ DILA + MARCUS. Nhưng: `people.A008431.name_vi = "Tuệ Thăng"` (tên ngắn DILA 慧升), nên tìm tên đầy đủ trong `people` ra 0 kết quả; `bio_vi = NULL` (không có tiểu sử Việt); "dòng Dương Kỳ" chỉ có trong TTL, DILA không có. | Một phần. Thiếu: tìm qua lớp alias `vn_person_authority`; ghi rõ "chưa có tiểu sử Việt" thay vì để trống. |
| 2 Lâm Tế → vị Việt Nam | **Chưa** | (a) `lineage_edge_assertions` chỉ có nguồn **DILA (46.006) + MARCUS (11.169), 0 cạnh TTL**. (b) Cạnh Việt Nam nằm ở `dharma_lineage_ttl_vn` (784 cạnh), dùng URI `ex:monk/<slug>`, **0 cạnh** dùng DILA ID ⇒ không nối được với đồ thị DILA nếu không đi qua crosswalk `vn_person_authority.dila_id` (1.307/1.511 có). (c) `dharma_lineage_unified` = 0 dòng. (d) Anchor mơ hồ: 義玄 có 4 bản ghi DILA (A003627, A009248, A015797, A032162; một bản `name_vi = "Tổ Sư"`). Trùng với phát hiện T274. | **Không.** M2 tái dùng `lineage_edge_assertions` vốn không có cạnh Việt Nam. |
| 3 "Chùa đời Minh" | **Chưa — dữ liệu đang vi phạm đúng điều case cấm** | `place_timeline_events`: **1.551 dòng** `event_type='founding'` có `confidence` = `dynasty_range` (844) hoặc `era_name_midpoint` (707), `year` = **năm giữa khoảng**, `year_end` = NULL toàn bộ. Ví dụ `PL000000000352` "唐開元中 (713-741年間)" lưu `founding year=727`. Chỉ có 2 loại event: `founding` 3.647, `dissolved` 41; không có `relocated`/`era_mention`. Bản sửa T22 (`founding` 3.647→2.262, `era_mention` 1.385, `year_end` 684) **không còn trong DB** — có vẻ mất trong sự cố/restore. | Một phần. D1 chỉ "parse marker ra khoảng" ở tầng API; không nói phải **sửa dữ liệu đang lưu năm giả**. |
| 4 Ba "Tuyết Đậu Pháp Nhã" | **Chưa — có lỗi định danh thật** | DILA có 法雅 ×3: `A006731` (唐, "河東人"), `A015245` (北魏), `A020536` (北宋, "蔣山元禪師法嗣") + 竺法雅 `A002201`. Bản ghi TTL chính `tuyet_dau_phap_nha` → **A006731 (đời Đường)**, trong khi alias `alias_A020536` ghi 雪竇法雅 → **A020536 (Bắc Tống)**. Tuyết Đậu Pháp Nhã thuộc đời Tống ⇒ bản ghi chính nhiều khả năng **gán nhầm DILA ID**. Thêm: `A020536.birth_year=1564, death_year=14` là rác do parser đọc nhầm locator CBETA `X80n1564_p0014a11`. Cả 4 đều có `name_vi` "Pháp Nhã" ⇒ đúng là không thể dùng tên Việt làm khoá. | Có module M1 disambiguate nhưng không phát hiện mapping sai + năm rác; verdict sẽ dựa trên dữ liệu sai. |
| 5 Đại Ninh Đạo Khoan ↔ Thạch Sương Sở Viên | **Được một phần** | `A001439` 楚圓 (Sở Viên) → `A020545` 道寬: DILA + MARCUS, consensus `confirmed_2plus`, `ttl_asserted = 0`. TTL ghi Đạo Khoan "Tông Lâm Tế Trung Hoa", đời 45, nhưng cạnh TTL không nằm trong `lineage_edge_assertions`. **Không có assertion CBETA có cấu trúc.** Cạnh DILA bị **lưu 2 lần** (toàn bảng: 22.992 cặp DILA trùng). | Một phần. Thiếu: nạp cạnh TTL làm assertion; khử trùng cạnh DILA (nếu không, provenance per-edge đếm DILA 2 lần); nói rõ CBETA chưa có assertion. |
| 6 Khai sáng vs giải thể | **Chưa** | 37 chùa có cả `founding` và `dissolved`. Nhưng `founding` gồm 1.551 năm suy từ triều đại/niên hiệu (xem case 3). Không có cột locator riêng; locator nằm lẫn trong `label_zh`/`source_ref`. | Một phần (như case 3). |
| 7 Tái lập số đời | **Được phần lớn** | `generation_engine_v2.compute` trả `algorithm`, `target_identity`, path/hash trong `sourceSnapshot`, `version`. Không có bảng kết quả lưu sẵn (`person_gen_computed` không tồn tại — tốt, tránh lẫn với engine cũ `+37`). | Có (E1/E2). Cần thêm: ghi `dataset_version` (hash DB/run) vì DB vừa bị thay. |
| 8 Bias nguồn DILA/TTL/CBETA | **Chưa đo được TTL** | `data_sources` có 14 nguồn nhưng **không có nguồn TTL local**. `ZQLOCAL` (id 5, 118.295 claim) là tên Việt phiên âm tự động, không phải TTL. TTL chỉ nằm ở `vn_person_authority` (1.511) + `ttl_v2_source_records`. Trạng thái `vn_person_authority`: verified 14, pending 441, auto_ttl 599, alias_* 457. | Không. M5 dựa trên `entity_claims`/`data_sources`, nên sẽ bỏ sót hoàn toàn TTL. |
| 9 Xuất TTL liên thông | **Thiết kế được, công bố chưa được** | DILA trong `data_sources`: `redistribution_allowed = 0`, `data_license_status = AUDITING`, `license_verified = 0`, `terms_status = under_review` (trong khi `license_note` ghi "CC BY-SA 4.0" — tự mâu thuẫn). | Có nhắc "license gate" chung chung; cần nói rõ: chưa được phân phối lại dữ liệu DILA cho tới khi chốt license. |

## Chỗ kế hoạch chưa đúng / chưa đủ

1. **Mâu thuẫn L1 với case 2 và nguyên tắc 1.** Mục 4.4 và 5.2 cho L1 "chỉ accepted/verified". Nhưng case 2 (cấp Cử nhân)
   yêu cầu "cạnh candidate phải có cảnh báo", còn nguyên tắc 1 cấm hạ độ chính xác để đơn giản hoá. Ẩn candidate ở L1 sẽ
   cho ra cây truyền thừa thiếu nhưng trông như đầy đủ. Hơn nữa, `vn_person_authority` chỉ có **14** dòng `verified` ⇒ L1
   gần như rỗng với nhân vật Việt Nam.
   → **Sửa:** L1 vẫn hiện candidate/conflict nhưng gom lại, kèm nhãn cảnh báo một dòng; L1 chỉ rút gọn chi tiết provenance, không rút gọn tập claim.
2. **Thiếu bảng ánh xạ trạng thái thật → enum.** Mục 5.1 liệt kê enum nhưng không định nghĩa ánh xạ.
   → Cần chốt, ví dụ: `vnpa.verified → accepted`; `pending/auto_ttl → candidate`; `alias_vi_suffix/alias_zh_match → candidate (alias)`;
   `lineage_edge_assertions` theo `status` + `trust_level`; `consensus_status confirmed_2plus → source_asserted (đa nguồn)` — **không** tự thành accepted.
   Admin chốt bảng này.
3. **Thiếu "Phase 0 — dữ liệu nền".** Lớp API mới sẽ trả câu trả lời sai một cách rất tự tin nếu không sửa trước:
   - D0-a: **khôi phục/chạy lại T22** (`scripts/t22_ld1_fix_era_name_founding.py --apply`, có `--revert`) — đổi 1.385 founding suy từ niên hiệu thành `era_mention` + `year_end`.
   - D0-b: **nạp cạnh TTL vào `lineage_edge_assertions`** với `source_code='TTL'`, ánh xạ `ex:monk/<slug>` → DILA ID qua `vn_person_authority.dila_id`; slug không có DILA ID thì giữ ID PTDA local. Phụ thuộc T380/T381 (rebuild `dharma_lineage_ttl_vn`).
   - D0-c: **khử trùng 22.992 cặp cạnh DILA lưu 2 lần** (BUG-027 đã ghi nhận) hoặc ít nhất `DISTINCT` theo `(subject, object, source_code)` ở tầng đọc.
   - D0-d: **rà mapping trùng tên** kiểu `tuyet_dau_phap_nha → A006731` và năm rác `A020536 1564/14` (parser đọc nhầm locator CBETA).
   - D0-e: **khai báo nguồn TTL local** trong `data_sources` (hoặc M5 đọc thẳng `vn_person_authority` + `ttl_v2_source_records`).
4. **Anchor identity cho case 2.** Cần quy tắc chọn đúng một anchor (義玄 ×4 trong DILA), ví dụ dùng `canonical_decision`/`lineage_primary_teacher`, và
   hiển thị việc chọn này như một claim có nguồn.
5. **Chỗ đặt code.** Nên tạo blueprint `api_academic.py` (theo mẫu `api_ttl_anchor.py`, hướng T364), không thêm 6 module vào `app.py` (đã 24.967 dòng).
6. **Ghi `dataset_version` thật.** DB vừa bị thay khi đang kiểm ⇒ mọi envelope L3 phải ghi hash/mtime DB + import run, không chỉ phiên bản thuật toán.
7. **Case 9 / license.** Export chỉ là profile + dữ liệu PTDA tự sở hữu cho tới khi Admin chốt license DILA (`redistribution_allowed = 0`).
8. Nhỏ: số task đề xuất T390–T397 khớp hiện trạng (T382–T389 đã dùng); trước khi tạo vẫn phải chạy `npm run dup:ids` + kiểm tầng 2.

## Lộ trình đề xuất (bổ sung vào mục 6 của kế hoạch)

| Thứ tự | Việc | Case mở khoá | Ghi DB? |
|---|---|---|---|
| **Phase 0** (mới) | D0-a T22 era_mention; D0-b nạp cạnh TTL + crosswalk; D0-c khử trùng cạnh DILA; D0-d rà mapping trùng tên + năm rác; D0-e nguồn TTL trong registry | 2, 3, 4, 5, 6, 8 | **Có** — cần Admin duyệt riêng từng việc, backup bằng SQLite backup API |
| A | Envelope + bảng ánh xạ status (Admin chốt) + quy tắc L1 hiện candidate có cảnh báo | tất cả | Không |
| B–G | Như kế hoạch, đặt trong `api_academic.py` | — | Không (read-only) |
| Kiểm thử | 9 test case cố định dùng đúng 9 câu hỏi đề bài, với kết quả kỳ vọng đo ở trên (A008431, A001439→A020545, A020536 vs A006731, PL000000000352 phải trả khoảng 713–741 chứ không phải 727…) | tất cả | Không |

Sau Phase 0 + A–G: cả 9 case trả lời được. Case 9 chỉ dừng ở mức "profile + dữ liệu PTDA" cho tới khi chốt license DILA.

## Câu hỏi cho Admin

1. Duyệt thêm **Phase 0 (sửa dữ liệu nền)** trước lớp API không? Phase 0 có ghi DB nên mỗi việc cần duyệt riêng.
2. L1 (Cử nhân): đồng ý **hiện candidate có cảnh báo** (thay vì ẩn) không?
3. Bảng ánh xạ trạng thái (mục 2 ở trên): Admin chốt hay giao agent soạn để Admin duyệt?
4. Xác nhận DB hiện tại (thay lúc 20:10) là bản đúng sau T380?
5. Có tạo task T390+ theo kế hoạch đã sửa và giao Hermes (`dispatch: approved`) không?
