# N4 Plan — Kế hoạch thực thi 4 task T454 / T455 / T456 / T457

Ngày lập: 2026-10-26 · PLANNER (harness) · chỉ đọc code + số liệu từ task file, KHÔNG sửa code/DB.

## Gate 0 — code backend T453 đã mất (điều tra xong 2026-10-26, báo cáo docs/sessions/2026-10-26/gate0-report.md)
- Code T453 CHƯA TỪNG được commit (`git log -S "dila_works_total" -- app.py` rỗng, `git grep dila_works HEAD -- app.py` rỗng). Chỉ còn trong backup: docs/sessions/2026-10-25/T445-coder/backup/app.py (13511-13640), after-coder-app.py (13535+), docs/sessions/2026-10-21/T445-debugger-wip/app.py.
- 2 khối thiếu: (a) route `/daoanh/api/public/dila_works` 29 dòng (13596-13624); (b) khối DILA 64 dòng trong `api_global_search` (13511-13574) + 3 key vào `resp` (13575-13583).
- DB ĐÃ có đủ bảng: dila_catalog_works 5.747 · dila_catalog_contributors 5.589 · dila_catalog_places 765 ⇒ nhánh fallback không chạy.
- index.html hiện tại (WIP T467) đã BỎ luồng DILA (handleSearch chỉ đọc monks/works/places, renderDilaWorks không còn được gọi) ⇒ HOME không lỗi nhưng không hiện kinh/người DILA. Bản sao docs/sessions/2026-10-26/index.html còn gọi d.dila_works và /public/dila_works ⇒ nếu đưa lên, "Xem tất cả" sẽ báo "Không tải được danh sách".
- WIP app.py: 248 insertions / 18 deletions; không hunk nào dụng vùng chèn (13032, 13173-13283). Rủi ro lớn nhất là commit sweep, không phải xung đột text.
- Phương án: A) khôi phục bằng blob HEAD + 2 khối, commit plumbing, không nuốt WIP (khuyến nghị, sau khi Admin xác nhận T453 (B) đã duyệt) · B) chờ phiên sở hữu app.py commit WIP rồi áp trên HEAD mới · C) tách route sang Blueprint mới (khối (b) vẫn phải sửa api_global_search nên không giảm rủi ro).
- Cảnh báo: KHÔNG copy nguyên file backup T445 đè lên app.py (bản cũ, thiếu codex_place_name của T465). Phải assert số lượng khi test, vì sai cột sẽ bị `except sqlite3.OperationalError` nuốt im lặng.

## Bảng tổng hợp
| Task | Nội dung | Agent | QA | Độ lớn | Gate DB | Phụ thuộc |
|---|---|---|---|---|---|---|
| T454 | Làm sạch hậu tố "_ Huý"/"_ Ngoa" trong namevi_map_places.name_vi (8 dòng) | daoanh-debugger | daoanh-qa | Nhỏ (~0,5 phiên) | UPDATE 8 dòng: backup → duyệt → apply | T453; độc lập |
| T455 | Chuẩn hoá people.name_vi (794 lệch + 532 sót chữ Hán) | daoanh-debugger | daoanh-qa | Lớn (2-3 phiên) | UPDATE theo lô + bảng lịch sử additive | T453; độc lập |
| T456 | Autocomplete ô Search HOME (/daoanh/api/public/suggest) | daoanh-debugger | daoanh-qa | Trung-lớn (1-2 phiên) | Có thể tạo FTS5 additive (chờ Q4) | Gate 0 + T453 + T416 (xong) + T450 (pending) |
| T457 | Import DILA biographies → dila_bio_nexus (staging ĐÃ XONG 21.740 nexus / 11 sách) | tich-hop | daoanh-qa | Trung (1 phiên + apply) | CREATE bảng additive + INSERT 21.740 | T453; độc lập; → T458 |

## T454 — hậu tố "_ Huý"/"_ Ngoa"
- done_when: đo lại name_vi chứa "_" (8 dòng, đo 2026-10-22) + xác định nghĩa hậu tố từ nguồn sinh dữ liệu → đề xuất sửa từng dòng (bỏ hậu tố / chuyển note_vi) — Admin duyệt → backup → sửa → ROLLBACK row → HOME "Huyền Trang" hiện "Hoằng Phúc Tự" không hậu tố → daoanh-qa ĐẠT → Admin DONE.
- File đụng: DB namevi_map_places (note_vi, source, confidence, needs_review — theo scripts/t428_import_claude_xml.py:178,190); đọc app.py:13028 (autocomplete), app.py:13232 (/daoanh/api/search JOIN), scripts/build_places_search_fts.py:86 (populate places_search_fts TỪ bảng này — nếu FTS materialized thì phải re-populate sau UPDATE), scripts/etl_entity_claims.py:159. Không sửa places_dila.
- Grep "Huý"/"Ngoa" trong scripts/*.py = 0 ⇒ hậu tố từ dữ liệu import, truy vết qua source/created_at.
- Bước: (1) đo lại `SELECT dila_id, name_vi, name_zh, source, note_vi, created_at FROM namevi_map_places WHERE instr(name_vi,'_')>0` (mode=ro) → (2) truy vết nguồn → trình Admin (Q5) → (3) đề xuất + CSV before docs/sessions/2026-10-26/T454/namevi_before.csv → (4) Gate: backup data/backups/lineage_t454_<ts>.db → duyệt → apply 1 transaction UPDATE theo dila_id → ROLLBACK.md → (5) re-populate FTS nếu có → (6) verify UI + npm run pipeline + daoanh-qa + Admin DONE.
- Verify: COUNT(*) WHERE instr(name_vi,'_')>0: N (kỳ vọng 8) → 0; PL000000042305 = "Hoằng Phúc Tự"; tổng dòng bảng không đổi.

## T455 — chuẩn hoá tên Việt người
- done_when: gộp task chuẩn hoá đang chạy nếu có (Q3a) → phân loại 794 dòng docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv thành (a) ZQ sai rõ / (b) alias cùng người (không sửa, ghi alias) / (c) khác quy tắc chính tả (Huệ/Tuệ, Thọ/Thụ, Trước/Trứ, Tì/Tỳ, hoà/hóa) → đề xuất âm cho 532 name_vi sót chữ Hán (A000002 "𧧌Chấn", A000047 "Vu 頔", A000903 "Hạ 丏 Tôn") → sửa theo lô Admin duyệt, additive giữ giá trị cũ, source ZQLOCAL=5 KHÔNG gán DILA, backup + ROLLBACK → HOME tự hiển thị tên mới → daoanh-qa ĐẠT → Admin DONE.
- File đụng: DB people (name_vi, name_zh — KHÔNG sửa name_zh); Cloud tham khảo data/dila_import/authority_catalog.2026-10/vn_dila_authority_catalog/<X>.vi.json; tham khảo không đụng app.py:16783 _suggest_name, :16839 admin_namevi_suggest, :16940 admin_namevi_batch_suggest. Script mới scripts/t455_name_vi_fix.py (--classify / --apply-batch / --revert-batch); bảng lịch sử additive đề xuất people_name_vi_history(person_id, old_name_vi, new_name_vi, batch, changed_at, reason) — schema chờ duyệt (Q3c).
- Bước: (1) phân loại 794 + đề xuất âm 532 (chỉ đọc, chạy song song được ngay) → (2) trình Admin (gộp task, thứ tự lô, schema, mẫu 20 dòng/nhóm) → (3) Gate từng lô: backup → duyệt CSV lô → apply (UPDATE + INSERT history, 1 transaction/lô) → ROLLBACK → (4) verify SQL + HOME + pipeline → (5) daoanh-qa (đếm lại + sample 30 dòng so CSV duyệt) → Admin DONE.
- Verify: đếm people.name_vi chứa Hán (U+4E00-9FFF + U+20000-2FFFF) 532 → ~0; COUNT(*) FROM people và name_zh không đổi.
- Rủi ro: phân loại nhầm alias ↔ sai (范寄東/范古農, 覺音/佛音, 了參/葉均); ký tự ngoài BMP (𧧌 U+219CC); tên trùng sau chuẩn hoá; session khác từng sửa people (T267); panel T453 đọc live.

## T456 — autocomplete ô Search HOME
- done_when: gõ ≥2 ký tự #heroSearch → dropdown debounce ~200ms, 3 nhóm icon 📖 kinh (dila_catalog_works) / 🧘 người (people + dila_catalog_contributors) / 📍 địa danh (tái dùng /daoanh/api/public/autocomplete) → gợi ý tên Việt + Hán + mã, ↑/↓/Enter/Esc, click → kết quả → API <200ms mọi chuỗi, không LIKE '%q%' quét toàn bảng khi có FTS → không regression "Tìm" T453 + luồng T404 → backup app.py/index.html, lint/e2e PASS → daoanh-qa → Admin DONE.
- File đụng: app.py route mới cạnh public_autocomplete (:13019-13081, tái dùng _t416_pending_index_hint :13006); tham chiếu /daoanh/api/search (:13160-13268), ensure_places_pending_fts (:498). index.html: #heroSearch :927, handleSearch :1152-1171, renderDilaWorks :1226-1265, renderDilaPeople :1183-1203, loadAllWorks :1205-1221. DB nếu FTS: bảng ảo additive dila_catalog_works_fts(title_vi, title_zh, cbeta_id) — đồng bộ batch Zero-RAM. Backup docs/sessions/2026-10-26/T456/{app.py,index.html}.bak-before-T456.
- Bước: (1) Gate 0 trước (Q1) → (2) đo timing hiện trạng + kiểm FTS5 khả dụng (PRAGMA compile_options trên bản COPY DB — ràng buộc T450) → (3) đề xuất phương án + mockup → Admin (Q4a/Q4b) → (4) code route /daoanh/api/public/suggest (3 nhóm ≤5, trả {works, people, places}); nếu FTS thì tạo bảng ảo + populate batch + đo <200ms trên bản copy trước khi ghi → (5) code frontend debounce + phím + CSS → (6) Gate DB nếu FTS: backup → duyệt → apply → ROLLBACK (DROP bảng mới) → (7) verify timing + regression + pipeline + daoanh-qa + Admin DONE.
- Verify: curl -w "%{time_total}" ≥10 chuỗi <0,2s; EXPLAIN QUERY PLAN không SCAN toàn bảng khi FTS khả dụng; /daoanh/api/search?q=Huyền Trang còn dila_works+dila_people; /daoanh/api/public/autocomplete?q=Thiếu L còn chạy.
- Rủi ro: IME/composition event tiếng Việt có dấu; chuỗi chỉ mã CBETA; nhóm rỗng; xung đột app.py/index.html với session song song; FTS5 thiếu → fallback LIKE prefix.

## T457 — import DILA biographies → nexus
- Trạng thái: snapshot data/dila_import/biographies.2024-01/ (commit 4e82453, SHA256SUMS.txt); parse ĐÃ xong — data/staging_final/t457_dila_bio_nexus.jsonl 21.740 nexus / 11 sách + manifest docs/manifests/T457-manifest.json; script có scripts/t457_extract_bio_nexus.py (chỉ đọc), t457_staging_*.py, t457_final*.py (KHÔNG ghi DB). Giấy phép đã chốt: markup DILA CC BY-SA, văn bản CBETA CC BY-NC-SA 4.0, PTDA phi thương mại (Admin 2026-10-22). Còn thiếu: scripts/t457_dila_bio_nexus_import.py (--dry-run/--apply/--revert) + bảng DB + dry-run report + backup/apply/ROLLBACK/QA.
- done_when: (1) snapshot + giấy phép đã xong → (2) kiểm chứng staging khớp done_when (đủ Liang/Tang/Song/Ming/Buxu/Xinxu GSZ, 居士傳, 比丘尼傳, 名僧傳抄, 出三藏記集) → (3) bảng additive dila_bio_nexus + bảng nối, KHÔNG sửa nexus_events (10.458 dòng) → (4) dry-run báo số truyện/điểm theo sách, % có năm, % person/place khớp → (5) backup → --apply → ROLLBACK → daoanh-qa ĐẠT → Admin DONE.
- File đụng: data/staging_final/t457_dila_bio_nexus.jsonl (schema: book, source_file, nexus_id, seq, from/to_anchor, text_zh, person_id, place_id, jd_from/jd_to, year_from/year_to, provenance, status), docs/manifests/T457-manifest.json, data/dila_import/biographies.2024-01/nexus_src/*.nexus.xml (11 file). Pattern import theo scripts/t453_dila_catalog_import.py. Bảng đề xuất: dila_bio_nexus(id, book, source_file, nexus_id, seq, from_anchor, to_anchor, text_zh, jd_from, jd_to, year_from, year_to, provenance, status, imported_at) + dila_bio_nexus_person(nexus_id, person_id) + dila_bio_nexus_place(nexus_id, place_id); index (book), (person_id), (year_from). JSONL hiện chỉ giữ person/place ĐẦU TIÊN — lấy ĐỦ phải parse lại nexus_src/ (Q2a). KHÔNG đụng nexus_events / scripts/t16_nexus_etl.py.
- Bước: (1) kiểm chứng staging: 11 sách vs done_when, checksum manifest vs đĩa, 142 nexus bỏ qua (anchor lỗi DILA) có danh sách → (2) viết import script --stats/--dry-run/--apply (INSERT batch 1.000, stream, Zero-RAM)/--revert (DROP bảng mới) → (3) trình Admin schema + dry-run (Q2) → (4) Gate: backup data/backups/lineage_t457_<ts>.db → duyệt → --apply → verify → ROLLBACK.md + row data_sources DILA_BIOGRAPHIES (CC BY-NC-SA 4.0) nếu duyệt → (5) pipeline + daoanh-qa → Admin DONE. Lớp Việt = T458.
- Verify: COUNT(*) FROM dila_bio_nexus = 21.740; GROUP BY book = 11 sách khớp dry-run; % có năm khớp manifest total_with_year; JOIN people khớp; JOIN places_dila khớp; COUNT(*) FROM nexus_events vẫn 10.458.
- Rủi ro: JSONL chỉ person/place đầu tiên (Q2a); JD âm/trước 1582 (công thức t457_final_v4.py:18-33; test Bất Không j1983698→719-720 + năm âm); nexus_id trùng giữa sách (duplicate_composite_key phải =0 trước apply); backup DB 1,4GB lâu; session song song.

## Thứ tự đề xuất
Gate 0 → T454 → T457 → T455 (apply) → T456 (FTS/đo cuối). Không task nào trong 4 chờ task khác trong 4. Serialize DB write: 1 session ghi tại 1 thời điểm. T455 phân loại (chỉ đọc) và T456 code (chưa ghi DB) chạy song song với T454/T457 được.

## Câu hỏi cần Admin quyết
Q1 Gate 0: duyệt khôi phục code T453 backend từ backup T445-coder — ai làm, khi nào? Và có muốn đưa lại luồng DILA trên HOME (đảo ngược T467) không?
Q2 T457: (a) bảng nối chỉ person/place đầu tiên (như JSONL) hay parse lại nexus_src/ lấy ĐỦ? (b) duyệt schema 3 bảng + row data_sources? (c) duyệt --apply sau dry-run?
Q3 T455: (a) gộp với task chuẩn hoá tên đang chạy nào? (b) ưu tiên lô so_lan cao hay nhóm 532 sót Hán? (c) duyệt bảng lịch sử people_name_vi_history?
Q4 T456: (a) FTS5 mới cho dila_catalog_works hay LIKE prefix? (b) T450 pending — T450 trước hay T456 đi trước?
Q5 T454: hậu tố "_ Huý"/"_ Ngoa" là ghi chú giữ (chuyển note_vi) hay rác xoá?
Q6 AGENTS §21: cả 4 file task đều thiếu mục "## Mô tả" (chỉ có done_when ở frontmatter) → Admin bổ sung trước khi lên Dashboard; không đổi status.

## Ghi chú vận hành
- 4 file task T454/T455/T456/T457 đều thiếu mục "## Mô tả" theo AGENTS §21.
- Thư mục `tasks/` hiện có ACE Everyone: DENY (DC) ⇒ agent KHÔNG rename/xoá được file trong tasks/ (đã gặp khi gộp T445/T463). Cần Admin cấp quyền nếu cần tổ chức lại file task.
- 4 task file T435/T436/T437/T438 đã bị phiên khác dời sang `tasks/backup/` (untracked); bản gốc trong HEAD bị xoá ở worktree. Cần quyết định nơi commit phần ghi chú "Admin xác nhận DONE (2026-10-26)".
- T453 có mâu thuẫn trạng thái: tasks/T453 ghi phần (B) đã duyệt 06:01, docs/tasktodo.md dòng 12 ghi "chờ duyệt" → cần Admin xác nhận.
