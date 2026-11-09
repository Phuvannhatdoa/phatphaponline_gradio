# OI-QA-REPORT — Kiểm chứng OPEN-ITEMS (2026-10-21)

Người kiểm: daoanh-qa (chỉ đọc). Không sửa code/DB, không git ghi, không --apply/--revert.
File báo cáo duy nhất được tạo: thư mục `docs/sessions/2026-10-21/qa/`.
Chi tiết OI-3: xem `OI-3-rerun.md` cùng thư mục.

## Kết luận nhanh

| Mục | Kết quả | Bằng chứng (lệnh + output rút gọn) | Khuyến nghị (1 dòng) |
|---|---|---|---|
| OI-3a audit:honesty:strict | FAIL (xác nhận lại) | exit 1; FAIL 5/7: H1=41, H2=96, H3=969, H4=745, H5=55 — khớp OI-3; script sạch so HEAD, DB mở mode=ro | Là data có sẵn trong DB — giao debugger lên kế hoạch sửa data theo từng check H, không phải việc commit code |
| OI-3b test:t232 | FAIL (xác nhận lại) | exit 1; 1/20 fail: `AssertionError: 'candidate' != 'incomplete'` (test_09); test + engine đều sạch so HEAD; test dùng :memory: không đụng DB | Mâu thuẫn logic giữa engine và test đã commit — debugger quyết sửa engine hay cập nhật test, cần Admin chọn |
| OI-3c test:translation | FAIL (xác nhận lại) | exit 1; dừng ở t178 case 17c: DB `name_vi='Thiên Nhiên'` ≠ kỳ vọng `'Đơn Hà Thiên Nhiên'` (68/69 PASS); t179…t211 không chạy do chuỗi && dừng | Sửa data name_vi của A009460 trong vn_person_authority (cần Admin duyệt ghi DB); chạy lại chuỗi sau khi sửa |
| OI-3d audit:t166 | FAIL (xác nhận lại) | exit 1; `sqlite3.OperationalError: no such column: identity_status`; pragma_table_info(translation_cache) = 14 cột, không có identity_status; migration `t166_identity_migrate.py` đã commit nhưng chưa chạy | Admin duyệt chạy migration t166 (GHI DB — backup lineage.db trước, ghi ROLLBACK) |
| OI-4 test:compliance PASS nhưng fail=2 | FAIL (logic báo cáo gây hiểu nhầm) | Script `verify_design_compliance.py` main() luôn exit 0 (không sys.exit lỗi) ⇒ pipeline không bao giờ đỏ do bước này; SQL chỉ đọc: entity_claims 447.885 row / 15 row có assertion_level (0,0033% → round 2 số = 0,00%); lineage_conflicts_v2 17.999 row / 0 row resolved=1 | Script đếm ĐÚNG — 0% là do data; sửa script để exit 1 khi có metric status='fail' (hoặc đổi nhãn PASS→REPORT); giữ goal bootstrap 1% (cần ≥4.479 claims có assertion_level, ≥180 conflicts resolved) kèm kế hoạch backfill |
| OI-8 lexicon-perf trong app.py | KHÔNG KIỂM ĐƯỢC (task sở hữu) — đã xác định trạng thái git | `git log -S "_LEXICON_BLOB" -- app.py` và `-S "_warm_lookup_caches"`, `-S "import bisect"`: RỖNG — không commit nào chứa; `_ensure_lex_cache` thuộc commit `a4397c2a` (2026-10-20 14:21:05 +0700, "cleanup: Remove legacy GPT Sol…"); backup cho thấy nhóm xuất hiện 2026-10-21 giữa 09:52 (bak_T446 chưa có) và 12:08 (T412 backup đã có); grep tasks/ + docs/: không task nào nhận | 3/4 symbol là thay đổi chưa commit, không task sở hữu — planner cấp task hoặc yêu cầu tách commit riêng trước khi commit |
| OI-13 model/permission 3 file agent | PASS (đã commit, có chênh lệch cần Admin biết) | `git log --oneline -3` mỗi file: `776296a0` (2026-10-21 16:30:05, T448 docs) rồi `15b03e21` (T439); `git diff HEAD` 3 file: rỗng (chỉ warning CRLF) ⇒ không còn thay đổi chưa commit; 776296a0 THÊM model (debugger=claude-haiku-5-5, qa=glm-5.3-flash, tich-hop=glm-5.3-flash — T439 không có model) và ĐƠN GIẢN HÓA permission | Admin duyệt 2 điểm suy yếu: qa MẤT deny sqlite3 INSERT/UPDATE/DELETE/DROP; tich-hop edit từ {ask + docs/** allow} thành allow toàn bộ (mâu thuẫn quy tắc "không wildcard allow" của coordinator.md) |
| OI-5 namevimap.html dilaLink PL→placevn | PASS (code) | Dòng 2059-2067: `dilaLink()` có comment lý do rõ ("PL###### = địa danh… person.html chỉ gọi /api/persons/<id> nên PL sẽ 404"); regex `/^PL\d+$/i` → `/daoanh/admin/placevn.html?id=`; placevn.html tồn tại trong admin/; server 8080 phục vụ HTTP 200 + marker FOUND | Code đúng và có giải thích — planner chỉ cần gán task sở hữu cho hunk này |
| OI-7 places.html #lineage-inspector | PASS (code) | Dòng 745: `flex:0 0 300px;min-width:0;max-width:300px` có mặt; nằm trong vùng có comment T410 (dòng 732/735) nhưng dòng CSS không có comment riêng; server 8080 HTTP 200 + marker `max-width:300px` FOUND | CSS hợp lý (khóa inspector 300px) — planner xác nhận thuộc T438/BUG-051 hay task khác |
| OI-10 admin/index.html nav "Hệ thống" | PASS (code) | Grep "Hệ thống": nav-label đúng 1 lần (dòng 458); vị trí cũ ~380 hiện là kết thúc section trước + "Place VN" (dòng 383-384), không sót khối; khối mới nguyên vẹn (Làm mới, Legal Check, zenlineage_review); server 8080 HTTP 200 + marker FOUND | Di chuyển sạch, không duplicate — giữ nguyên, planner ghi task sở hữu |

## Phạm vi đã chạy (mỗi lệnh riêng lẻ, không pipe/ghép)

- `npm.cmd run audit:honesty:strict` — exit 1 (đo bằng wrapper subprocess trong %TEMP%)
- `npm.cmd run test:t232` — exit 1
- `npm.cmd run test:translation` — exit 1
- `npm.cmd run audit:t166` — exit 1
- `git diff HEAD --name-only -- <4 script/test + engine>` — rỗng (sạch so HEAD)
- `git log -S "<symbol>" --oneline -- Dai_Tang_Kinh/daoanh/app.py` — 4 lần (3 rỗng, 1 ra a4397c2a)
- `git log --oneline -3 -- <3 file agent>` — 3 lần
- `git show 15b03e21:<file>` — 3 lần (so T439 vs hiện tại)
- SQL chỉ đọc (mode=ro): pragma_table_info(translation_cache); COUNT entity_claims (447.885 / 15); COUNT lineage_conflicts_v2 (17.999 / 0)
- HTTP GET 127.0.0.1:8080 cho 3 trang — đều 200 + marker FOUND

## Đã kiểm tra nhưng không chạy được / không chạy có chủ đích

- `npm run test:compliance` KHÔNG chạy lại: script ghi `data/design_compliance.json`
  (vi phạm ràng buộc chỉ đọc của phiên này). Đã thay bằng đối chiếu code + SQL chỉ đọc.
- Không chạy lại 4 bước trên HEAD sạch (checkout bị cấm). Bù lại: đã chứng minh các
  file script/test/engine liên quan đều sạch so HEAD nên kết quả worktree ≡ HEAD cho các bước này.
- test:translation chỉ chạy tới t178 (chuỗi && dừng) — trạng thái t179…t211 trong lượt này: chưa chạy.

## Lỗi cần sửa (cho daoanh-debugger, sau khi Admin duyệt)

1. `tests/test_t232_generation_engine.py:40` vs `src_python/generation_engine_v2.py` —
   case thiếu cha trả 'candidate' thay vì 'incomplete' (cả hai đã commit; cần quyết sửa bên nào).
2. `vn_person_authority` A009460 丹霞天然 — `name_vi` = 'Thiên Nhiên', kỳ vọng
   'Đơn Hà Thiên Nhiên' (data fix, cần duyệt ghi DB).
3. `translation_cache` thiếu cột `identity_status` — chạy `scripts/t166_identity_migrate.py`
   (GHI DB: backup trước + ghi docs/ROLLBACK.md).
4. `scripts/verify_design_compliance.py` (main, dòng 199-220) — luôn exit 0 dù metric
   status='fail'; status tính trên percent ĐÃ round 2 số nên 15/447.885 (0,0033%) bị
   xếp 'fail' thay vì 'warn' — nên tính status trên ratio thô trước khi round.
5. `.opencode/agents/daoanh-qa.md` — mất deny sqlite3 INSERT/UPDATE/DELETE/DROP so với T439
   (bash "*": ask vẫn chặn mặc định nhưng mất lớp phòng thủ thứ hai).
6. `.opencode/agents/tich-hop.md` — `edit: allow` toàn bộ (T439: ask + chỉ docs/** allow),
   mâu thuẫn tinh thần quy tắc coordinator.md "Không dùng wildcard "*": allow".

## Chưa kiểm tra (rủi ro còn lại)

- OI-3: chưa chạy trên HEAD sạch (worktree có WIP phiên khác) — nhưng các file liên quan
  đều không nằm trong WIP nên rủi ro thấp.
- OI-4: chưa kiểm tra ai/đã backfill assertion_level bao giờ (15 row đầu tiên là của ai).
- OI-8: không xác định được session nào đã thêm nhóm lexicon-perf (chỉ khoanh thời gian
  09:52–12:08 ngày 2026-10-21 qua mtime backup).
- OI-13: chưa đối chiếu được với "bảng model trong AGENTS" — coordinator.md KHÔNG có
  bảng model (chỉ frontmatter riêng); đã so với frontmatter coordinator + .claude counterparts.
- Không đánh DONE task nào trong báo cáo này.
