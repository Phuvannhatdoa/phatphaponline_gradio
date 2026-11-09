# OPEN-ITEMS — 2026-10-21

Danh sách mục chưa chắc / trùng lặp / chưa quyết / rủi ro để planner phân loại và phân phối.
File này chỉ ghi lại kết quả điều tra đã có; không kết luận thêm. Không commit.

Ghi chú: OI-20 (coordinator.md, dòng soudalert) đã xử lý xong, không đưa vào danh sách.

Thống kê theo loại (một mục có thể mang nhiều loại):
- chưa chắc: 8 (OI-3, 4, 5, 7, 8, 10, 11, 13)
- trùng lặp: 4 (OI-2, 7, 11, 18)
- chưa quyết: 11 (OI-1, 2, 6, 9, 12, 14, 15, 16, 17, 19, 21)
- rủi ro: 3 (OI-1, 12, 16)
- Tổng số mục: 20

---

### OI-1: Tệp evidence bị build ghi đè
- Loại: rủi ro, chưa quyết
- Mô tả: `docs/evidence/2026-10-08_T263_h3_conflicts.tsv` giảm từ 407 xuống 1 dòng; `..._summary.tsv` có summary 47/79/280 đổi thành 0/0/0. Nguyên nhân: `scripts/audit_h3_conflicts.py:214-222` mở file bằng `io.open(..., 'w')`, tên file hard-code theo ngày, không có guard.
- Bằng chứng: `scripts/audit_h3_conflicts.py:214-222`; số dòng 407→1 và summary 47/79/280→0/0/0 (báo cáo QA/build trong `docs/sessions/2026-10-21/build/`).
- Ai có thể xử lý: agent debugger để khôi phục bằng checkout từ HEAD và thêm guard (sau khi có duyệt). Admin cần quyết: có duyệt `git checkout` để khôi phục hai file evidence không.
- Đã biết: file đã bị ghi đè; nguyên nhân nằm ở script trên.
- Chưa biết: đã có bản backup ngoài git của hai file hay chưa; script có bị chạy thêm lần nào khác không.

### OI-2: Guard cho audit_h3_conflicts.py chưa có task
- Loại: trùng lặp, chưa quyết
- Mô tả: Chưa có task nào cho việc thêm guard vào `scripts/audit_h3_conflicts.py`. Nếu gộp với OI-1 thì trùng nội dung; nếu tách thì cần chọn task ID.
- Bằng chứng: `scripts/audit_h3_conflicts.py:214-222` (cùng vị trí với OI-1); không có task file tương ứng (chưa kiểm tra ID trống khi ghi file này).
- Ai có thể xử lý: planner quyết gộp vào OI-1 hay tách; agent debugger thực hiện sau khi chọn.
- Admin cần quyết: gộp hay tách task; cấp ID mới (kiểm 2 tầng theo AGENTS §16).
- Đã biết: script ghi đè không có guard.
- Chưa biết: số task phù hợp; có cần sửa tên file theo ngày hay không.

### OI-3: 4 bước FAIL trong pipeline (có thể do data/schema sẵn có)
- Loại: chưa chắc
- Mô tả: Pipeline có 4 bước đỏ: (a) `audit:honesty:strict` exit 1 với H1=41, H2=96, H3=969, H4=745, H5=55; (b) `test:t232` 1/20 fail, `candidate` != `incomplete`; (c) `test:translation` case 17c lỗi với tên 'Thiên Nhiên'; (d) `audit:t166` thiếu cột `identity_status` trong `translation_cache`. QA cho rằng có thể do data/schema có sẵn, nhưng CHƯA chạy lại trên HEAD để xác nhận.
- Bằng chứng: output pipeline của QA (chưa có file đính kèm trong prompt); cần kiểm trong `docs/sessions/2026-10-21/build/`.
- Ai có thể xử lý: agent QA chạy lại 4 lệnh trên HEAD để xác nhận trước; sau đó agent debugger nếu xác nhận là lỗi thật.
- Admin cần quyết: không cần quyết ngay; chỉ cần chấp nhận kết quả chạy lại trên HEAD.
- Đã biết: 4 bước đỏ với số liệu như trên.
- Chưa biết: 4 bước này có đỏ trên HEAD sạch hay chỉ đỏ với worktree hiện tại; nguyên nhân gốc chưa được xác nhận.

### OI-4: test:compliance báo PASS nhưng fail=2
- Loại: chưa chắc
- Mô tả: `test:compliance` in kết quả PASS nhưng có fail=2: `claims_assertion_level` 0% và `conflicts_resolved` 0%. Script này không làm pipeline đỏ nên lỗi bị bỏ qua.
- Bằng chứng: output của `test:compliance` (báo cáo QA; chưa có file đính kèm trong prompt).
- Ai có thể xử lý: agent QA xác nhận lại output; agent debugger nếu cần sửa logic PASS/FAIL của script.
- Admin cần quyết: có coi hai chỉ số 0% là lỗi cần chặn pipeline hay không.
- Đã biết: báo PASS với fail=2; hai chỉ số 0%.
- Chưa biết: 0% là do data thật hay do script đếm sai; ngưỡng nào được coi là đạt.

### OI-5: admin/namevimap.html — hunk @@1902 dilaLink (PL→placevn.html) không rõ task
- Loại: chưa chắc
- Mô tả: Trong `admin/namevimap.html` có một hunk ở @@1902 đổi dilaLink từ PL sang `placevn.html`. Chưa xác định được hunk này thuộc task nào.
- Bằng chứng: `git diff` của `admin/namevimap.html` tại hunk @@1902 (đường dẫn file đầy đủ: `Dai_Tang_Kinh/daoanh/admin/namevimap.html`).
- Ai có thể xử lý: planner tra task tương ứng; agent QA kiểm chứng link PL có đúng không.
- Admin cần quyết: giữ hay bỏ hunk này khi commit.
- Đã biết: nội dung thay đổi là dilaLink PL→placevn.html.
- Chưa biết: task sở hữu; lý do đổi link.

### OI-6: admin/namevimap.html — BUG-050 (T437) và T446 trộn trong cùng file
- Loại: chưa quyết
- Mô tả: File `admin/namevimap.html` chứa cả hunk của BUG-050 (T437, khoảng 10 hunk) và T446 (khoảng 7 hunk). Hai nhóm tách theo vùng dòng, chưa tách được sạch trong một commit.
- Bằng chứng: `git diff -- Dai_Tang_Kinh/daoanh/admin/namevimap.html` (phân vùng theo dòng); xem thêm OI-5 cho hunk @@1902.
- Ai có thể xử lý: planner quyết cách commit; agent debugger có thể tách hunk nếu được duyệt.
- Admin cần quyết: commit gộp một commit hay tách hai commit (tách hunk có rủi ro sót).
- Đã biết: file chứa hai nhóm thay đổi thuộc hai task.
- Chưa biết: việc tách hunk có làm hỏng file không (chưa thử).

### OI-7: places.html — hunk @@742 và @@1513
- Loại: chưa chắc, trùng lặp (khả năng)
- Mô tả: Hunk @@742 thêm min-width/max-width cho `#lineage-inspector`; chưa rõ thuộc task nào, nằm cùng vùng với BUG-051 (T438) nhưng không có comment. Hunk @@1513 thuộc T406, mà T406 đang ở trạng thái pending nên có thể là thay đổi của phiên khác.
- Bằng chứng: `git diff -- Dai_Tang_Kinh/daoanh/places.html` tại @@742 và @@1513; `docs/tasktodo.md` (T406 pending).
- Ai có thể xử lý: planner tra task; agent QA kiểm giao diện lineage-inspector.
- Admin cần quyết: hunk @@742 có thuộc T438 không; hunk @@1513 có đưa vào commit này không.
- Đã biết: nội dung thay đổi CSS min/max-width; T406 pending.
- Chưa biết: người tạo hunk; có trùng với BUG-051 hay không.

### OI-8: app.py — nhóm "lexicon-perf" không rõ task
- Loại: chưa chắc
- Mô tả: Nhóm thay đổi trong `app.py` gồm import `bisect`, `_ensure_lex_cache`, `_LEXICON_BLOB`, `_warm_lookup_caches`. Nhóm này liên quan hiệu năng lexicon nhưng chưa xác định được task.
- Bằng chứng: `git diff -- Dai_Tang_Kinh/daoanh/app.py` (các symbol trên).
- Ai có thể xử lý: planner tra task; agent QA chạy kiểm tra route lexicon.
- Admin cần quyết: giữ trong commit này hay tách riêng.
- Đã biết: có 4 thành phần cụ thể như trên.
- Chưa biết: task sở hữu; có ảnh hưởng đến đường tra cứu nào không.

### OI-9: app.py — hunk @@11920 trộn T440 + T446
- Loại: chưa quyết
- Mô tả: Một hunk ở @@11920 trong `app.py` chứa cả thay đổi của T440 và T446. Hunk không tách an toàn bằng công cụ hiện có.
- Bằng chứng: `git diff -- Dai_Tang_Kinh/daoanh/app.py` tại @@11920.
- Ai có thể xử lý: agent debugger tách thủ công nếu được duyệt; hoặc commit gộp.
- Admin cần quyết: chấp nhận commit gộp T440+T446 hay yêu cầu tách thủ công.
- Đã biết: hunk trộn hai task.
- Chưa biết: mức độ phụ thuộc giữa hai phần thay đổi.

### OI-10: admin/index.html — di chuyển khối nav "Hệ thống"
- Loại: chưa chắc
- Mô tả: Khối nav "Hệ thống" bị xoá ở dòng 380 và thêm nguyên văn ở dòng 454. Đây là di chuyển, chưa rõ lý do hay task.
- Bằng chứng: `git diff -- Dai_Tang_Kinh/daoanh/admin/index.html` (dòng 380 và 454).
- Ai có thể xử lý: planner xác nhận task; agent QA kiểm nav trên trang admin.
- Admin cần quyết: giữ vị trí mới hay hoàn nguyên.
- Đã biết: nội dung khối nav giống nhau, chỉ đổi vị trí.
- Chưa biết: lý do chuyển vị trí.

### OI-11: ai_batch_transliterate_places_districts.py — thêm _checkpoint, trùng định nghĩa hàm
- Loại: chưa chắc, trùng lặp
- Mô tả: Script thêm hàm `_checkpoint()` (PRAGMA wal_checkpoint TRUNCATE) và xoá các định nghĩa `count_done`, `save_batch`, `reset_table` trùng ở cuối file. Chưa rõ thay đổi này thuộc task nào; T444 đang pending.
- Bằng chứng: `git diff -- Dai_Tang_Kinh/daoanh/scripts/ai_batch_transliterate_places_districts.py`; `docs/tasktodo.md` (T444 pending).
- Ai có thể xử lý: planner tra task; agent debugger kiểm xem các hàm còn lại có đúng bản cần giữ không.
- Admin cần quyết: có giữ thay đổi này trong commit hay không.
- Đã biết: có thêm `_checkpoint()` và xoá các định nghĩa trùng.
- Chưa biết: bản định nghĩa nào trong các bản trùng là bản đúng để giữ; task sở hữu.

### OI-12: .opencode/opencode.json — thay đổi quyền (RỦI RO BẢO MẬT)
- Loại: rủi ro, chưa quyết
- Mô tả: Có 3 hunk không rõ nguồn: `"external_directory"` đổi thành `"ask"`; `"bash": "*"` đổi từ `ask` sang `allow`; thêm `"sudo *": "deny"`. Việc `bash "*": allow` đi ngược quy tắc không dùng wildcard allow.
- Bằng chứng: `git diff -- Dai_Tang_Kinh/daoanh/.opencode/opencode.json` (3 hunk).
- Ai có thể xử lý: không tự sửa; chờ Admin quyết. Agent QA có thể đối chiếu với quy tắc quyền trong AGENTS/CLAUDE.
- Admin cần quyết: giữ hay hoàn nguyên các thay đổi quyền; có chấp nhận `bash "*": allow` không.
- Đã biết: nội dung 3 hunk như trên; vi phạm quy tắc wildcard allow.
- Chưa biết: ai/what session đổi; lý do đổi.

### OI-13: Agent daoanh-debugger, daoanh-qa, tich-hop viết lại model và permission
- Loại: chưa chắc
- Mô tả: Ba file `.opencode/agents/daoanh-debugger.md`, `daoanh-qa.md`, `tich-hop.md` đã được chỉnh sửa (model + permission) sau commit T439. Không có task nào ghi nhận việc này. Có thể trùng với việc đã làm với coordinator/harness/daoanh-task.
- Bằng chứng: `git diff -- Dai_Tang_Kinh/daoanh/.opencode/agents/` (3 file); commit T439 trong `git log`.
- Ai có thể xử lý: planner tra xem việc đã làm ở coordinator/harness/daoanh-task đã bao gồm chưa; agent QA đối chiếu.
- Admin cần quyết: có ghi nhận thay đổi model/permission này vào task nào không; có giữ không.
- Đã biết: đã có chỉnh sửa model trong cả ba file; không có task ghi nhận.
- Chưa biết: nội dung permission cụ thể đã được duyệt chưa; có trùng với các thay đổi trước đó không.

### OI-14: docs/bugs.md — một hunk chứa BUG-049 và BUG-050; thiếu BUG-048 và BUG-051
- Loại: chưa quyết (thiếu)
- Mô tả: Một hunk trong `docs/bugs.md` gộp cả entry BUG-049 và BUG-050. BUG-048 và BUG-051 chưa có entry, cả trong HEAD lẫn worktree.
- Bằng chứng: `git diff -- Dai_Tang_Kinh/daoanh/docs/bugs.md`; `git show HEAD:Dai_Tang_Kinh/daoanh/docs/bugs.md` (không có BUG-048/051).
- Ai có thể xử lý: agent QA/planner bổ sung entry thiếu sau khi có nội dung; không tự suy diễn nội dung bug.
- Admin cần quyết: có viết bổ sung BUG-048 và BUG-051 không; tách hunk BUG-049/050 thế nào.
- Đã biết: BUG-048 và BUG-051 thiếu entry; hunk gộp hai bug.
- Chưa biết: nội dung chi tiết của BUG-048.

### OI-15: docs/ROLLBACK.md — dòng 2026-10-21 chưa commit
- Loại: chưa quyết
- Mô tả: Dòng ghi chú rollback ngày 2026-10-21 đã được chèn vào `docs/ROLLBACK.md`, nhưng chưa commit vì file đang trạng thái MM (có WIP phiên khác).
- Bằng chứng: `git status` (trạng thái MM của file); dòng 2026-10-21 trong `docs/ROLLBACK.md`.
- Ai có thể xử lý: planner quyết thời điểm commit; agent không commit khi chưa có lệnh.
- Admin cần quyết: commit chung với WIP phiên khác hay chờ.
- Đã biết: dòng đã có trong worktree; file đang MM.
- Chưa biết: WIP phiên khác là gì.

### OI-16: Index git thật lệch HEAD
- Loại: rủi ro, chưa quyết
- Mô tả: `.git/index` có 41 entry staged do phiên khác; trước đó có 35 entry D. Không commit được bằng index thật nếu chưa xử lý. Đề xuất `reset -- <paths>` cần Admin duyệt.
- Bằng chứng: `git diff --cached --name-only` (41 entry); lần kiểm trước có 35 entry D (không có file đính kèm trong prompt).
- Ai có thể xử lý: không tự reset; planner chuẩn bị danh sách path; Admin duyệt.
- Admin cần quyết: có duyệt `git reset -- <paths>` cho 41 entry không; quy trình đúng theo AGENTS §14.
- Đã biết: 41 entry staged; có 35 entry D trước đó.
- Chưa biết: 41 entry thuộc phiên nào; có trùng với 35 entry D không.

### OI-17: Nhánh truyen-dang-the-pho-clean chưa push, chưa merge
- Loại: chưa quyết
- Mô tả: Nhánh `truyen-dang-the-pho-clean` chưa push lên remote và chưa merge vào master. Admin đã chọn không merge trong lượt này.
- Bằng chứng: `git status -sb`; `git log master..truyen-dang-the-pho-clean --oneline`.
- Ai có thể xử lý: planner ghi nhận trạng thái; không merge/push khi chưa có lệnh.
- Admin cần quyết: khi nào push; khi nào merge.
- Đã biết: chưa push; chưa merge (quyết định của Admin).
- Chưa biết: số commit chưa merge.

### OI-18: Trùng ID và việc (T427-2, T437, T441, T442–T445)
- Loại: trùng lặp (đã xử lý một phần)
- Mô tả: T427-2 đã đóng vì trùng với T437. T445 (dry-run import Claude, phiên khác) có phạm vi gần T443, Admin quyết giữ riêng. T441 hiện là "etl-load-only-unpassed", trùng số với T441 plan trước đây; chuỗi places đã đổi sang T442–T444.
- Bằng chứng: `docs/tasktodo.md`; `tasks/` (frontmatter `id:`); chạy `npm run dup:ids` để kiểm tra trùng file (kết quả chưa đính kèm trong prompt).
- Ai có thể xử lý: planner rà soát tasktodo và đảm bảo không còn ID trùng ở prose (AGENTS §16 tầng 2).
- Admin cần quyết: xác nhận T445 giữ riêng với T443; xác nhận T441 mới là gì và có ghi former_ids không.
- Đã biết: T427-2 đóng trùng T437; chuỗi places đã đổi sang T442–T444; T445 giữ riêng theo Admin.
- Chưa biết: còn chỗ nào nhắc đến T441 cũ trong prose hay không.

### OI-19: tasks/archive_done/ — 175 task DONE chưa commit
- Loại: chưa quyết
- Mô tả: 175 file task đã DONE được chuyển vào `tasks/archive_done/` nhưng chưa commit; thay đổi này do phiên khác thực hiện.
- Bằng chứng: `git status` (thư mục `tasks/archive_done/`; số file 175 theo báo cáo).
- Ai có thể xử lý: planner quyết commit riêng hay gộp; không commit khi chưa có lệnh.
- Admin cần quyết: có commit việc archive này không; commit riêng hay gộp.
- Đã biết: 175 file đã chuyển; chưa commit.
- Chưa biết: script/phiên nào chuyển; có ảnh hưởng đến `build_progress_data.py` không.

### OI-21: Force-add log pipeline-132935.log
- Loại: chưa quyết
- Mô tả: File `pipeline-132935.log` bị `.gitignore` (`*.log`) chặn, đã được `git add -f`. Câu hỏi: có nên đổi `.gitignore` để cho phép `docs/sessions/*/build/` không.
- Bằng chứng: `.gitignore` (quy tắc `*.log`); `git ls-files -- docs/sessions/2026-10-21/build/` (sau khi add -f).
- Ai có thể xử lý: planner đề xuất; agent debugger sửa `.gitignore` nếu được duyệt.
- Admin cần quyết: giữ force-add, hay thêm exception `!docs/sessions/*/build/*.log` vào `.gitignore`.
- Đã biết: file bị ignore và đã force-add.
- Chưa biết: có các log build khác cần track không.
