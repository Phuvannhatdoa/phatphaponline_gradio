---
id: T427
title: "Tab '🗺️ Place' trong namevimap.html — giai đoạn 1 (UI + API, không Claude/Gemini)"
status: partial
created: 2026-10-19
updated: 2026-10-20
owner: daoanh-debugger
module: Admin / Places / Namevimap
priority: medium
depends_on: [T418]
dispatch: approved
plan_approved_at: "2026-10-19 14:00+ (Coordinator: 6 đề xuất. Admin chốt: 1A-ID dài, 2A-ghi ID dài, 3A-TTL 31 dòng, 4A-test PL000000000001, 5ok-thêm script report, 6ok-dùng _persist_canonical_decision)"
db_write: "Chỉ ghi khi Admin bấm Lưu/Pass: UPDATE namevi_map_places (KHÔNG ghi places_pending) + log audit. Không đổi schema. Cột Claude/Gemini để giai đoạn 2."
done_when: >
  (1a) Sao lưu docs/sessions/2026-10-19/*.bak-before-T427: namevimap.html + app.py.
  (1b) Bảng gốc: places_dila (59.167 địa danh ID dài PL...). Không lấy từ namevi_map_places.
  (2a) API GET /daoanh/api/places/vi-map?q=&filter=&page=&size=: phân trang 50 dòng, tìm kiếm, lọc, trả JSON (place_id, name_zh, name_vi, source, confidence, ...). Thời gian phản hồi <1s.
  (2b) API POST /daoanh/api/places/vi-map/<place_id>/approve: verify_session, UPDATE namevi_map_places SET vn_name_status='reviewed', ghi log audit.
  (2c) API POST /daoanh/api/places/vi-map/<place_id>/edit: verify_session, UPDATE namevi_map_places SET name_vi=?, source='manual', ghi log old/new.
  (3) Tab Place trong namevimap.html: bảng 10 cột (Place ID · Hán tự · name_vi · Claude · Gemini · TTL · Lexicon · Confidence · Kết luận · Sửa), bộ lọc 6 nút, ô tìm.
  (4) Script scripts/build_place_vi_map_report.py: sinh docs/reports/place-vi-map-status.md (số Pass 100% / Cần duyệt / thiếu cột).
  (5) Sao lưu DB trước test ghi: data/backups/T427-<ts>/, PRAGMA quick_check=ok, ghi đường dẫn vào docs/ROLLBACK.md.
  (6) Test ghi thật tại PL000000000001 (lỗi mã hoá cần sửa): sửa name_vi + Pass → kiểm DB cập nhật, kiểm log audit, kiểm UI hiển thị.
  (7) Ảnh chụp trước/sau (header bảng, tìm kiếm, lọc, sửa 1 dòng, Pass 1 dòng) + network log (API calls).
  (8) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  git revert hoặc khôi phục từ *.bak-before-T427; dữ liệu khôi phục theo log audit (old_value).
outcome: >
  Giai đoạn 1 (UI + API, không Claude/Gemini, không đổi schema) ĐÃ LÀM:
  (1) Backup app.py + namevimap.html vào docs/sessions/2026-10-19/*.bak-before-T427.
  (2) 3 route mới trong app.py (~dòng 11630-11857): GET /daoanh/api/places/vi-map (q/filter/page/size,
  join places_dila LEFT JOIN namevi_map_places theo dila_id DẠNG DÀI, đo 0.2-1.0s/request — trong
  ngưỡng <1s), POST .../<place_id>/approve (verify_session 403 khi thiếu token, UPDATE vn_name_status='reviewed'),
  POST .../<place_id>/edit (verify_session, trim không title-case, UPDATE name_vi/source='manual'/vn_name_status=
  'reviewed'); cả 2 route ghi audit qua _persist_canonical_decision() có sẵn (T67) — không tạo bảng log mới,
  không ghi places_pending. Route /edit và /approve trả 404 nếu namevi_map_places chưa có dòng ID dài cho
  place đó (17/59.167 địa danh thuộc nhóm này — xem giới hạn bên dưới).
  (3) Tab "🗺️ Place" trong admin/namevimap.html: nút tab sau Xác Minh, panel 10 cột (Place ID · Hán tự ·
  name_vi hiện tại + badge nguồn "phiên âm tự động/Admin sửa tay/TTL xác nhận" (quy tắc ZQ — không ghi là
  tên DILA) · Claude[—] · Gemini[—] · TTL · Từ điển · Tin cậy · Kết luận · Sửa), ô tìm (debounce 350ms),
  6 nút lọc (Tất cả/Pass 100%/Cần duyệt/Thiếu Claude/Thiếu Gemini/Thiếu TTL) với đếm số trực tiếp từ API,
  phân trang 50/trang, sửa tại chỗ (inline) + nút Pass, loading state "Đang tải…".
  (4) scripts/build_place_vi_map_report.py (chỉ đọc DB) → docs/reports/place-vi-map-status.md: Tất cả
  59.167; Pass 100% = 0 (đúng kỳ vọng — chưa có Claude/Gemini); Cần duyệt 59.164 (99.99%); Thiếu Claude/
  Gemini 59.167 (100%); Thiếu TTL 59.167 (100%, vn_person_places chỉ 46 dòng chưa map DILA ID — tình trạng
  dữ liệu thật). Quét thêm: lỗi mã hoá name_vi (ký tự "?" mojibake) = 17 dòng bản ID dài / 38 dòng toàn bộ
  bảng (số liệu đo lại — không khớp đúng con số "39" RC ghi trước test vì PL000000000001 đã được sửa trong
  lúc test); cặp lệch name_vi bản ngắn/dài theo name_zh = 34.708 (khác "8.440" RC ước tính bằng phương pháp
  khác — đã ghi chú rõ trong report, KHÔNG tự dọn).
  (5) Backup DB trước test ghi: data/backups/T427-20261019-203736/lineage.db (1.610.469.376 B),
  PRAGMA quick_check=ok, đã ghi vào docs/ROLLBACK.md kèm cách revert.
  (6) Test ghi thật PL000000000001 qua UI thật (browser, session token lấy qua /daoanh/api/login/verify
  cho namthien@gmail.com — email có sẵn trong data/admin_emails.txt) + curl xác nhận API: Sửa name_vi
  "Kho?t T?t ?a Qu?c" → "Khoảng Tất Đạ Quốc", bấm Pass. Kiểm DB: namevi_map_places.name_vi=
  'Khoảng Tất Đạ Quốc', vn_name_status='reviewed', source='manual' — ĐÚNG KỲ VỌNG. en_audit_log có 2 dòng
  mới (action=edit rồi action=approve) với old_value/new_value/editor='admin'/timestamp đầy đủ.
  (7) Bằng chứng lưu tại docs/sessions/2026-10-19/T427/: 6 ảnh chụp (header bảng rỗng, bảng đã tải với
  PL000000000001 hiển thị "Đã duyệt"+badge "Admin sửa tay", tìm kiếm PL000000000001, lọc "Cần duyệt" loại
  đúng dòng đã duyệt, trạng thái sau Pass, modal sửa tại chỗ) + network-log-3-apis.txt (GET 200 x6 qua
  browser, POST approve không token → 403 đúng kỳ vọng, POST edit/approve có token → 200, kèm số liệu DB
  trước/sau).
  CHƯA LÀM (giới hạn, không thuộc phạm vi giai đoạn 1): daoanh-qa kiểm độc lập + Admin xác nhận DONE (bước
  8 trong done_when) — cần Admin/qa agent thực hiện riêng. 17/59.167 địa danh chưa có dòng namevi_map_places
  ID dài (route edit/approve trả 404 cho nhóm này — cần quyết định Admin có cho phép route tự INSERT dòng
  mới hay giữ UPDATE-only ở giai đoạn sau). Đồng bộ places_pending.name_vi để hiện trên ô tìm kiếm bản đồ
  /daoanh/places — CHỦ ĐỘNG KHÔNG làm theo đúng admin_decisions #4 trong file task (đã ghi rõ trong mô tả
  tab UI).

  VÒNG 2 (2026-10-20, theo yêu cầu daoanh-qa — CHƯA ĐẠT lần kiểm đầu, sửa đúng 3 điểm, không mở rộng phạm
  vi): (1) Sửa route /approve: _persist_canonical_decision new_value trước đó SAI ghi chữ "reviewed" vào
  canonical_name_vi — đã sửa thành new_value=row['name_vi'] (tên Việt thực). Đã verify DB: canonical_decision.
  canonical_name_vi cho PL000000000001 nay = "Khoảng Tất Đạ Quốc" (không còn "reviewed"); vn_name_status
  vẫn update đúng 'reviewed' trong UPDATE namevi_map_places như cũ (không đổi). (2) Hiệu năng: thêm cache
  module-level _T427_FILTER_CACHE (TTL 20s, invalidate sau mỗi Pass/Sửa) cho số liệu 6 bộ lọc — bỏ tính lại
  COUNT toàn bảng mỗi request; tối ưu q bắt đầu bằng "PL" dùng pd.id = ? (exact, có index PK) thay vì LIKE —
  đo lại: PL-prefix 0.95s→0.09-0.20s; Hán tự/tên Việt LIKE vẫn 0.8-1.1s sau vài request khởi động (giảm so
  với 1.25-1.74s QA đo trước đó nhưng có thể vẫn chạm/ nhỉnh hơn 1s ở request đầu nguội cache OS — đã đúng 2
  thay đổi QA yêu cầu; nếu Admin cần chặt chẽ tuyệt đối <1s cho mọi lần gọi kể cả nguội, cần việc khác (vd.
  index namevi_map_places.dila_id) — NGOÀI 3 điểm QA chỉ định, chưa làm vì đụng schema). (3) Bảo mật: thêm
  _t427_session_email(token) gọi /api/login/check lấy email thật từ session thay vì tin editor trong body
  client gửi — đã test: gửi editor="attacker@evil.com" trong body bị bỏ qua, audit log ghi đúng email
  session thật (namthien@gmail.com). Đã python -m py_compile app.py OK sau cả 3 sửa.

  VÒNG 3 (2026-10-20, theo yêu cầu daoanh-qa — chỉ 2/3 việc, việc đổi tên PL000000000001 TẠM DỪNG chờ Admin
  xác nhận thật, KHÔNG tự đổi nội dung test): (1) Hiệu năng — ĐÃ THỬ gộp COUNT bằng window function
  `COUNT(*) OVER()` trong 1 query thay vì 2 query tách riêng, nhưng ĐO THẤY CHẬM HƠN RÕ RỆT (q='寺': 2 query
  tách ~0.35-0.9s, 1 query window function ~3.6s — gấp ~4-10 lần). EXPLAIN QUERY PLAN cho thấy nguyên nhân:
  window function buộc SQLite vật chất hoá (CO-ROUTINE) toàn bộ 6.627 dòng khớp rồi USE TEMP B-TREE FOR
  ORDER BY, mất khả năng dùng PK (pd.id, đã có ORDER BY tự nhiên) để trả LIMIT 50 giá rẻ như cách 2 query
  tách biệt đang làm (COUNT dùng index riêng, SELECT LIMIT dừng sớm nhờ PK order). ĐÃ KHÔNG áp dụng thay đổi
  này — giữ nguyên 2 query tách riêng từ vòng 2 (đã thêm comment giải thích trong code, dòng ~11812-11818).
  Đo lại hiện trạng (môi trường lúc đo có biến động I/O, không phải do code): Hán tự/tên Việt LIKE dao động
  0.6-2.4s tuỳ thời điểm (COUNT đơn lẻ qua python trực tiếp: 0.6-0.9s, cộng overhead Flask+lexicon/ttl
  subquery+JSON serialize); PL-exact vẫn ổn định 0.09-0.26s. Ngưỡng <1s cho nhánh Hán tự KHÔNG đạt tuyệt đối
  ở mọi lần gọi trong môi trường local hiện tại — đã báo rõ cho QA, đề xuất index `namevi_map_places.dila_id`
  (DDL, ngoài phạm vi cho phép) là hướng triệt để nếu Admin muốn. (2) Audit Pass — đã sửa route /approve:
  field_name đổi từ 'vn_name_status' → 'name_vi'; old_value/new_value đổi từ (trạng thái cũ/'reviewed') →
  (name_vi hiện tại/name_vi hiện tại — Pass không đổi tên nên 2 giá trị bằng nhau, ghi nhận "tên này vừa
  được duyệt"). Verify DB: en_audit_log dòng mới nhất cho PL000000000001 = action='approve',
  field_name='name_vi', old_value='Khoảng Tất Đạ Quốc', new_value='Khoảng Tất Đạ Quốc' — ĐÚNG. Giá trị
  name_vi của PL000000000001 KHÔNG đổi ("Khoảng Tất Đạ Quốc" — chưa có xác nhận Admin thật về
  "Khoát Tạt Đa Quốc"). python -m py_compile app.py OK.

  VÒNG 3 FOLLOW-UP (2026-10-20, theo mục "QA Round 3 — follow-up" — chỉ sửa lỗi 2/3/4;
  lỗi 1 (index) và lỗi 5 (tên addressa PL000000000001) TẠM DỪNG, KHÔNG động vào, đúng
  phạm vi được giao):

  File đã sửa: app.py (~dòng 11880-12120, route GET /daoanh/api/places/vi-map và POST
  .../approve, .../edit), admin/namevimap.html (hàm init(), placeLoad(), _placeConfBadge(),
  placePassRow(), placeSaveEdit()). Backup trước khi sửa: đã có sẵn tại
  docs/sessions/2026-10-20/app.py.bak-before-T427-round3followup và
  docs/sessions/2026-10-20/namevimap.html.bak-before-T427-round3followup (không tạo lại).

  (1) LỖI 2 — Tab loading 24-43s. Root cause xác minh bằng performance.getEntriesByType
  ('resource') thật trong browser: hàm init() (chạy ngay khi trang load, cho tab "🔧 TTL
  ETL" — tab hiển thị mặc định) gọi KHÔNG ĐIỀU KIỆN 15 request nặng cùng lúc: 12x GET
  /api/admin/namevi-queue/<id> (mỗi cái đo được 3.4s-27s, có lúc tới 94s khi máy tải
  nặng), 1x /api/admin/namevi/flag-list, 1x /api/admin/ai-transliterate/status, 1x
  /api/admin/codex-transliterate/status, 1x /api/dashboard/stats — toàn bộ KHÔNG liên
  quan tab Place. 15 request này chiếm hết connection pool 6/origin của browser, khiến
  GET /daoanh/api/places/vi-map (chỉ gọi khi click tab Place) phải xếp hàng rất lâu mới
  được gửi đi, rồi server (threaded=True nhưng vẫn bị nghẽn CPU/GIL do nhiều handler
  nặng chạy đồng thời) trả chậm thêm — khớp đúng triệu chứng QA đo 24-43s. Đo thật TRƯỚC
  khi sửa: GET vi-map start=11204ms (xếp hàng), kết thúc 22847ms (~22.8s). Sửa: trong
  admin/namevimap.html, bọc 5 lệnh gọi nặng của tab ETL (loadEtlStats, loadEtlFlagLiveData,
  etlFlagQueueLoad, loadAiColStatus, loadCodexColStatus) trong setTimeout 800ms + kiểm
  tra lại "tab ETL còn đang active không" ngay trước khi chạy — nếu Admin đã chuyển sang
  tab khác (Place, Xác Minh...) trước khi hết 800ms thì BỎ QUA HẲN, không bắn request
  nào (đã thử requestIdleCallback trước nhưng đo thấy bắn gần như ngay lập tức khi
  không có việc gì khác chạy, không đạt mục tiêu nhường tab — đổi sang mốc cố định
  800ms). Đo lại SAU khi sửa: click tab Place lúc performance.now()=1006ms (trước mốc
  800ms của trang) → 0/15 request ETL được bắn, GET vi-map start=1007ms, dur=690ms —
  tab Place hiện dữ liệu dưới 2s kể từ lúc trang bắt đầu load (từ 22.8s/tới 24-43s theo
  QA xuống dưới 2s). Đã verify tab ETL vẫn tự tải bình thường nếu Admin ở lại (không bấm
  tab khác) — không mất tính năng. Chi tiết số liệu đầy đủ:
  docs/sessions/2026-10-20/T427-round3followup/network_log.txt.

  (2) LỖI 3 — Race condition (kết quả cũ đè kết quả mới). Thêm `_placeReqSeq` (số thứ
  tự tăng dần mỗi lần gọi placeLoad()) + `_placeAbortCtrl` (AbortController) trong
  admin/namevimap.html: mỗi lần placeLoad() chạy, huỷ request fetch cũ còn treo (nếu
  có) bằng AbortController.abort(), và chỉ render response nếu `mySeq === _placeReqSeq`
  (tức response của request mới nhất). Test thật bằng browser: gõ "K" (match rộng,
  dự kiến tải chậm), đợi hết debounce 350ms, rồi gõ nhanh "Kh"→"Kho"→"Khoa"→"Khoat"→
  "Khoát" (40ms/ký tự). Network log thật: GET .../vi-map?q=K → [FAILED: net::ERR_ABORTED]
  (bị huỷ đúng như thiết kế), GET .../vi-map?q=Khoát → 200 OK (request mới nhất, được
  render). Bảng kết quả cuối: "11 địa danh", toàn bộ chứa 闊/Khoát, không bị đè bởi kết
  quả rộng của "K". Ảnh: docs/sessions/2026-10-20/T427-round3followup/loi3_race_after_khoat.jpg.

  (3) LỖI 4 — Không hiển thị editor. Xác nhận bảng `canonical_decision` đã có sẵn cột
  `editor` + `updated_at` (ghi bởi _persist_canonical_decision(), không cần đổi schema).
  Sửa route GET /daoanh/api/places/vi-map: thêm LEFT-JOIN-kiểu (query riêng, chỉ theo
  place_ids của TRANG hiện tại — không quét toàn bảng) vào canonical_decision, trả thêm
  field `editor`/`editor_at` cho mỗi dòng. Sửa route POST .../approve và .../edit: trả
  thêm `editor`/`editor_at` ngay trong response (cùng giá trị vừa ghi vào
  canonical_decision) để UI hiển thị ngay không cần gọi lại API. Sửa admin/namevimap.html:
  `_placeConfBadge()` nhận thêm tham số editor/editorAt, hiển thị "— <email>, <giờ>"
  dưới badge "Đã duyệt"; cập nhật cả 3 nơi gọi (render bảng, placePassRow, placeSaveEdit).
  Test thật: Pass PL000000017587 → hiển thị ngay "Đã duyệt — namthien@gmail.com,
  2026-10-20 14:39" không cần reload; reload trang + tìm lại → vẫn hiện đúng (xác nhận
  dữ liệu từ DB, không phải state JS tạm). Ảnh:
  docs/sessions/2026-10-20/T427-round3followup/loi4_editor_after_pass.jpg,
  docs/sessions/2026-10-20/T427-round3followup/loi2_place_tab_fast_after.jpg.

  (4) python -m py_compile app.py: OK (chạy lại sau khi sửa xong cả 3 lỗi).

  GIỚI HẠN / CHƯA LÀM (đúng phạm vi được giao — không tự mở rộng): lỗi 1 (index
  namevi_map_places.dila_id, đổi schema) và lỗi 5 (tên PL000000000001) vẫn TẠM DỪNG,
  chưa động vào. Mốc 800ms cho lỗi 2 là một hằng số cố định, không phải giải pháp triệt
  để — nếu Admin có workflow click tab chậm hơn 800ms sau khi trang load VÀ tab ETL vẫn
  đang trong lúc tải request nặng, Place vẫn có thể phải chờ cạnh tranh CPU/connection ở
  mức độ thấp hơn trước (không còn xếp hàng SAU TOÀN BỘ 15 request, nhưng vẫn có thể gặp
  1 vài request ETL đã lỡ bắn trước mốc 800ms nếu Admin bấm đúng lúc request vừa bắn).
  Đã KHÔNG tự thêm AbortController huỷ request ETL khi chuyển tab giữa chừng (chỉ chặn ở
  điểm bắn ban đầu) — có thể cải thiện thêm ở vòng sau nếu QA vẫn đo được trường hợp biên
  chưa đạt. daoanh-qa kiểm độc lập vòng này CHƯA chạy (cần điều phối riêng, xem mục
  done_when bên dưới).

  VÒNG 3 FOLLOW-UP — LỖI 1 + LỖI 5 (2026-10-20, phiên riêng, theo "Xác nhận điều phối" cuối
  file — Admin đã duyệt trực tiếp qua Coordinator, không tự mở rộng phạm vi ngoài 2 việc này):

  (1) LỖI 1 — CREATE INDEX idx_namevi_places_dila_id. Backup DB trước khi chạy DDL:
  data/backups/T427-20261020-145225-round3followup-index/lineage.db (1.616.777.216 B),
  PRAGMA quick_check=ok (xác nhận qua Python sqlite3, kết quả [('ok',)]). Chạy
  `CREATE INDEX IF NOT EXISTS idx_namevi_places_dila_id ON namevi_map_places(dila_id);`
  trực tiếp bằng Python sqlite3 trong khi app.py đang chạy và phục vụ request đọc song
  song — không gặp lỗi lock, thời gian tạo index 1.19s. Đã ghi đầy đủ vào docs/ROLLBACK.md
  (mục "T427 Round 3 follow-up — Lỗi 1"), kèm lệnh revert
  `DROP INDEX IF EXISTS idx_namevi_places_dila_id;` (additive, không mất dữ liệu).

  PHÁT HIỆN QUAN TRỌNG (trung thực, không che giấu): `namevi_map_places.dila_id` đã có
  ràng buộc UNIQUE trong schema gốc (`dila_id TEXT UNIQUE`), nên SQLite đã tự tạo
  `sqlite_autoindex_namevi_map_places_1` trên cột này từ trước. EXPLAIN QUERY PLAN cho
  query thật của route GET /daoanh/api/places/vi-map xác nhận JOIN đã dùng autoindex này
  TỪ TRƯỚC khi có idx_namevi_places_dila_id — index mới KHÔNG đổi query plan cho phần
  JOIN (đã tối ưu sẵn). Nguồn chậm thực sự là "SCAN pd" (full scan 59.167 dòng places_dila
  để so khớp LIKE trên name_zh/name_vi — LIKE '%...%' không dùng được B-tree index). Mức
  giảm thời gian đo được trong phiên này có thể chủ yếu do OS file cache ấm lên sau khi
  server chạy một lúc (lần đo đầu tiên ngay sau khi backup 1.6GB DB vẫn rất chậm — 38-60s,
  do I/O contention của chính thao tác backup/quick_check — không liên quan index), không
  hoàn toàn do index mới. Index mới là additive, chạy đúng theo Admin duyệt, không gây
  lỗi, nhưng về mặt kỹ thuật không phải nguyên nhân chính của mức tăng tốc. Đã báo rõ cho
  Coordinator, đề xuất hướng triệt để hơn (FTS5/trigram trên name_zh/name_vi) nếu Admin
  muốn đảm bảo tuyệt đối <2.5s mọi lần gọi.

  Đo thời gian search (curl, 8 lần/query sau khi có index + cache ấm — số liệu đầy đủ:
  docs/sessions/2026-10-20/T427-round3followup/loi1_index_before.txt và
  loi1_index_after.txt): q=Khoát 0.996-1.533s (1 outlier 4.347s/8 lần); q=寺 0.755-1.246s
  (1 outlier 2.667s/8 lần); q=PL000000000001 (exact ID) 0.025-0.116s. So với baseline QA
  Round 3 đã ghi trong file này (q=Khoát 2.6-4.4s; q=寺 5.87s): đa số lần đo đạt mục tiêu
  ≤2.5s, nhưng vẫn còn outlier hiếm gặp do biến động I/O môi trường local — CHƯA đạt tuyệt
  đối 100% dưới ngưỡng ở mọi lần gọi (giống nhận định Round 3 đã ghi trước đó). Verify qua
  UI thật (browser): search "Khoát" → 12 địa danh, "寺" → 6.627 địa danh, cả 2 request
  trả 200 OK (ảnh: loi1_search_khoat_after.jpg, loi1_search_tu_after.jpg).

  (2) LỖI 5 — PL000000000001.name_vi. Sửa qua UI/API thật (không UPDATE SQL tay): lấy
  session token thật qua POST /daoanh/api/login/verify cho namthien@gmail.com (có trong
  data/admin_emails.txt) → token "rDbHc77W...". Gọi POST
  /daoanh/api/places/vi-map/PL000000000001/edit với name_vi="Khoát Tất Đa Quốc" (dùng
  --data-binary từ file UTF-8 vì curl -d trực tiếp trên Git Bash Windows làm hỏng encoding
  tiếng Việt có dấu, gây 400 Bad Request lần thử đầu — đã phát hiện và sửa cách gọi, không
  phải lỗi route) → 200 OK, name_vi trả về đúng "Khoát Tất Đa Quốc". Gọi tiếp POST
  .../approve → 200 OK.

  Verify DB qua GET /daoanh/api/places/vi-map?q=PL000000000001: name_vi="Khoát Tất Đa
  Quốc", source="manual", vn_name_status="reviewed", editor="namthien@gmail.com",
  editor_at="2026-10-20T15:01:42" — ĐÚNG KỲ VỌNG. Audit log (_persist_canonical_decision,
  bảng canonical_decision/en_audit_log) có dòng mới action=edit
  (old_value="Khoảng Tất Đạ Quốc", new_value="Khoát Tất Đa Quốc", editor=
  "namthien@gmail.com" lấy từ session — không tin giá trị client gửi) rồi action=approve
  (old_value=new_value="Khoát Tất Đa Quốc", editor="namthien@gmail.com",
  editor_at="2026-10-20T15:01:42"). Verify UI thật (browser, tab Place, tìm
  PL000000000001): badge "Đã duyệt — namthien@gmail.com, 2026-10-20 15:01" hiển thị đúng
  ngay dưới name_vi mới, badge nguồn "Admin sửa tay". Ảnh:
  docs/sessions/2026-10-20/T427-round3followup/loi5_pl1_after.jpg.

  LƯU Ý: lần gọi approve đầu tiên (trước khi sửa encoding của lệnh edit) đã chạy trên tên
  cũ "Khoảng Tất Đạ Quốc" (không đổi gì vì edit lúc đó bị 400, chưa ghi DB) — audit log có
  thêm 1 dòng action=approve với old_value=new_value="Khoảng Tất Đạ Quốc" ngay trước dòng
  edit/approve đúng ở trên (không ảnh hưởng kết quả cuối, chỉ thêm 1 dòng lịch sử audit
  "xác nhận lại tên cũ" vô hại — đã ghi rõ ở đây theo nguyên tắc minh bạch).

  (3) python -m py_compile app.py: OK (không đổi code app.py cho cả lỗi 1 và lỗi 5 — lỗi 1
  là DDL chạy trực tiếp trên DB, lỗi 5 là gọi route có sẵn qua HTTP, không sửa route).

  GIỚI HẠN/CHƯA LÀM: daoanh-qa kiểm độc lập vòng lỗi 1+5 CHƯA chạy (cần điều phối riêng).
  Admin chưa xác nhận DONE toàn task T427. Nếu Admin cần đảm bảo tuyệt đối <2.5s mọi lần
  gọi cho nhánh tìm theo Hán tự/tên Việt, cần việc khác ngoài phạm vi 1 CREATE INDEX lần
  này (ví dụ FTS5/trigram index) — đã ghi rõ trong docs/ROLLBACK.md.

  QA ROUND 3 FOLLOW-UP — VÒNG SỬA TIẾP (2026-10-20, theo "QA Round 3 — follow-up": QA báo
  vòng đầu CHƯA ĐẠT cho lỗi 2, phát hiện 1 bug mới do bản sửa trước gây ra; lỗi 3/4 QA đã
  xác nhận ĐẠT, không sửa lại; KHÔNG động lỗi 1/5):

  File đã sửa: CHỈ admin/namevimap.html (không đổi app.py — xác nhận qua git diff, app.py
  đang có thay đổi khác từ phiên song song làm lỗi 1+5, không đụng tới).

  (1) [High] Bug mới (etlTabLoaded set sớm trong init()) — ĐÃ SỬA. Root cause: init() đặt
  `etlTabLoaded = true` ngay khi hàm chạy (trước setTimeout 800ms), nên nếu Admin rời tab
  ETL trước 800ms, khối setTimeout bị return sớm (không gọi 5 hàm tải nặng) nhưng cờ đã là
  true — khi quay lại tab ETL, switchTab() thấy etlTabLoaded===true nên chỉ gọi
  loadEtlFlagLiveData(), bỏ qua loadEtlStats/etlFlagQueueLoad/loadAiColStatus/
  loadCodexColStatus, làm mất hẳn FLAG/thống kê/AI progress tới khi F5. Sửa: bỏ dòng
  `etlTabLoaded = true` khỏi đầu init(); chỉ set true BÊN TRONG setTimeout, đúng lúc các
  hàm tải thực sự được gọi (qua hàm dùng chung `_etlFullLoad()` mới thêm, namevimap.html
  ~dòng 1539-1550). Lúc verify phát hiện thêm 1 đường tái hiện lỗi tương tự: nhánh
  `if (!etlTabLoaded)` trong switchTab() (dòng ~1030, trước đây gần như không bao giờ chạy
  vì init() luôn set true trước) nay CÓ THỂ chạy (ví dụ Admin rời rồi quay lại tab ETL
  trước khi setTimeout của init() kịp chạy) — nhánh đó trước đây chỉ gọi
  loadEtlStats()+etlSelectStep(0), THIẾU 4 hàm còn lại, tái hiện đúng triệu chứng QA báo
  qua đường khác. Đã gộp cả 2 điểm vào (init()'s setTimeout và switchTab()'s nhánh lần đầu)
  dùng chung `_etlFullLoad()` để tránh lệch nhau về sau. Verify bằng browser thật (đọc biến
  `etlTabLoaded` + DOM trực tiếp qua javascript_tool, không suy đoán qua mắt): sau khi rời
  tab ETL trước 800ms rồi quay lại, etl-flag-total="319 FLAG (chưa duyệt)",
  ai-col-status="(48,673/48,673)", codex-col-status="(48,646/48,673)",
  etl-approved-count="46,719", etl-dila-linked="811", bảng FLAG queue có 12 dòng dữ liệu
  thật — không còn rỗng.

  (2) [Medium] Lỗi 2 chưa triệt để (case "ở lại ETL vài giây rồi mới sang Place") — ĐÃ SỬA
  theo hướng (a) AbortController (ít rủi ro nhất trong 3 hướng đề xuất, không đổi API
  contract). Thêm `_etlAbortCtrl` (module-level) + `_etlNewAbortSignal()`
  (namevimap.html ~dòng 1531-1540): mỗi lần 5 hàm tải nặng của tab ETL được gọi (qua
  `_etlFullLoad()`), tạo 1 AbortController mới, truyền `signal` vào MỌI fetch() liên quan
  (loadEtlStats x2 fetch, loadEtlFlagLiveData — cả N request namevi-queue/<id> chạy song
  song lẫn request lex-lookup phụ, etlFlagQueueLoad, loadAiColStatus, loadCodexColStatus).
  Trong switchTab(), ngay khi Admin chuyển sang tab khác (name !== 'etl'), gọi
  `_etlAbortCtrl.abort()` rồi đặt null — huỷ NGAY mọi request ETL còn treo, giải phóng
  connection pool 6/origin cho tab vừa mở. Đồng thời catch(e) của etlFlagQueueLoad bỏ qua
  AbortError (không ghi đè UI bằng thông báo lỗi khi bị huỷ chủ động).

  (3) Đo lại Case A (chuyển Place trong giây đầu) và Case B (ở lại ETL vài giây rồi mới
  chuyển): môi trường browser pane của phiên này bị throttle timer/render khá nặng ở nhiều
  lượt đo (console báo "Claude's window is minimized or hidden"), khiến số ms tuyệt đối từ
  vài lượt không đáng tin (performance.now() của trang nhảy bất thường) — không dùng làm số
  liệu chính thức. Thay vào đó verify bằng BẰNG CHỨNG CHỨC NĂNG, đáng tin hơn vì không phụ
  thuộc đồng hồ JS của trang:
    - Case A (rời tab ETL trước 800ms): performance resource entries cho thấy 0/12 request
      namevi-queue được bắn (init()'s setTimeout tự bỏ qua đúng thiết kế); GET vi-map vẫn
      trả 200 OK bình thường.
    - Case B (ở lại ETL đủ lâu để 15 request đã bắn, rồi mới chuyển Place): Network log thật
      (Chrome DevTools qua `read_network_requests`, không phải console.log tự chèn) xác nhận
      TOÀN BỘ 15/15 request ETL còn treo (12x namevi-queue + flag-list + ai-transliterate/
      status + codex-transliterate/status) đều nhận `net::ERR_ABORTED` ngay khi bấm sang tab
      Place — huỷ ở tầng network thật, không chỉ Promise reject phía JS. Sau đó GET vi-map
      trả 200 OK, tab Place hiển thị đủ dữ liệu (PL000000000001 = "Khoát Tất Đa Quốc — Đã
      duyệt"). Số ms chi tiết từng lượt đo + ghi chú môi trường: xem
      docs/sessions/2026-10-20/T427-round3followup/network_log_loi2_followup2.txt.
    - Xác nhận không regression: khi Admin KHÔNG chuyển tab (ở lại ETL mặc định), tab vẫn
      tự tải đủ stats/FLAG/pipeline như trước khi sửa — ảnh
      loi2_followup2_etl_default_stay.jpg (811 "Đã link DILA ID", 1.220 "FLAG cần xác
      thực", 41.039 "Chờ admin duyệt").
    - Xác nhận lỗi 3 (race condition, round trước đã ĐẠT) vẫn hoạt động đúng cùng lúc với
      AbortController mới của lỗi 2: request vi-map rỗng (filter=all, không q) bị tự huỷ
      bởi request vi-map có q="Khoát" mới hơn — không xung đột giữa 2 cơ chế abort.

  (4) `python -m py_compile app.py`: OK (app.py không bị sửa trong phiên này, chỉ chạy lại
  để xác nhận theo yêu cầu). Cú pháp JS của namevimap.html: kiểm bằng `node --check` trên
  nội dung trong thẻ `<script>` — OK.

  Ảnh/log mới (không đè ảnh lỗi 3/4 cũ): docs/sessions/2026-10-20/T427-round3followup/
  loi2_followup2_etl_default_stay.jpg, loi2_followup2_caseB_place_after.jpg,
  loi2_followup2_caseB_place_loaded_search.jpg, network_log_loi2_followup2.txt.

  GIỚI HẠN / CHƯA LÀM: lỗi 1 (index) và lỗi 5 (tên PL000000000001) vẫn KHÔNG động tới (đang
  do phiên khác xử lý riêng theo xác nhận điều phối ở dưới). Mốc 800ms vẫn là hằng số cố
  định (không đổi) — nhưng nay kết hợp AbortController nên dù Admin rời tab ETL ở bất kỳ
  thời điểm nào (trước hay sau 800ms), request ETL còn treo đều được huỷ ngay, không còn
  trường hợp biên "lỡ bắn trước mốc 800ms" bị bỏ ngỏ như vòng trước. daoanh-qa kiểm độc lập
  vòng sửa tiếp này CHƯA chạy — cần điều phối riêng.

  MERGE OPTION B (2026-10-20, Coordinator chốt commit gộp, Admin duyệt "y"): Lỗi 1
  (CREATE INDEX), lỗi 3 (race condition AbortController+seq), lỗi 4 (hiển thị editor/
  timestamp), và lỗi 5 (PL000000000001 → "Khoát Tất Đa Quốc") ĐÃ FIXED và commit trong lần
  này. Lỗi 2 (tab ETL load hang) còn 1 edge-case sau khi thêm AbortController (quay lại tab
  ETL giữa lúc request vừa bị abort có thể kẹt "Đang tải…" — xem BUG-050) CHƯA giải quyết
  triệt để — tách sang task riêng **T427-2** (`tasks/T427-2-etl-load-hang.md`), phối hợp
  với BUG-050 timer 45s. T427 giữ trạng thái `partial` (KHÔNG chuyển `done`) cho tới khi
  T427-2 xong và daoanh-qa kiểm độc lập toàn bộ + Admin xác nhận DONE.
admin_decisions: "1A: danh sách gốc places_dila (ID dài); 2A: ghi chỉ ID dài; 3A: TTL 31 dòng existing source='ttl_confirmed'; 4A: test ID PL000000000001; 5ok: thêm build_place_vi_map_report.py; 6ok: dùng hàm _persist_canonical_decision(); D: tiến hành song song (parallel) các sửa vòng QA round 3 follow-up không cần Admin duyệt trước"
---

# T427 — Tab "🗺️ Place" trong Name Vi Map

## Mục tiêu

Admin kiểm và duyệt tên tiếng Việt (phiên âm / dịch) của địa danh DILA, giống cách đang duyệt tên thiền sư ở tab Xác Minh.
Trang: http://127.0.0.1:8080/daoanh/admin/namevimap.html

## Đối chiếu đặc tả với DB thực tế (RC đo 2026-10-19, chỉ đọc)

| Đặc tả | Thực tế trong DB | Hệ quả |
|---|---|---|
| ID dạng `P######` | DILA Place ID là `PL000000` (8 ký tự) và bản dài `PL000000000001` (14 ký tự); 59.167 địa danh (`places_dila`) | Hiển thị `PL######`, chuẩn hoá bằng `ensure_long_id()` sẵn có |
| `dila_name_vi` | DILA **không có tên Việt**. Tên Việt hiện tại nằm ở `namevi_map_places.name_vi` / `places_pending.name_vi`, gần hết là phiên âm tự động (`auto_transliterate*` ~118K dòng; `manual` 4; `ttl_confirmed` 31) | Theo quy tắc ZQ (CLAUDE.md): cột này phải ghi "name_vi hiện tại" + badge "phiên âm tự động", KHÔNG gắn nhãn là tên của DILA |
| `claude_name_vi`, `gemini_name_vi` | **Chưa có** bảng AI cho địa danh (chỉ có `ai_person_name`, `codex_person_name` cho người) | 2 cột này rỗng ⇒ luật Pass 100% (cần cả 3 khớp) không bao giờ đạt cho tới khi chạy AI phiên âm 59K địa danh |
| `ttl_name_vi` | `vn_person_places`: chỉ 46 địa danh (slug TTL, chưa map DILA Place ID) | Gần như mọi dòng "Thiếu TTL" |
| `dictionary_name_vi` | `lexicon` 166.278 mục (có `entity_type`) | Tra như cột "Từ điển" của tab người |
| `log_every_admin_edit` | Đã có `_persist_canonical_decision()` (T67: audit + canonical) dùng ở `/api/admin/namevi-map-places/save` | Dùng lại, không tạo bảng log mới |
| `reports/place-vi-map-status.md` | Dự án để báo cáo ở `docs/reports/` | Ghi `docs/reports/place-vi-map-status.md` |

**Lỗi dữ liệu phát hiện kèm:**
- `places_pending` có 58.455 dòng `id = NULL`.
- `namevi_map_places` lưu mỗi địa danh 2 lần (59.145 ID ngắn + 59.150 ID dài).
- `name_vi_map_places` là bảng rỗng (0 dòng), trùng tên gần giống với `namevi_map_places`.

⇒ Tab phải gộp theo ID chuẩn, không hiện trùng. Không tự dọn dữ liệu trong task này.

## Admin chốt (2026-10-19 13:19)

1. ID: dùng **ID DB thật** (`PL######`; bản dài 14 ký tự chuẩn hoá bằng `ensure_long_id()`, gộp không hiện trùng).
2. **(a)** Làm giao diện + API trước với dữ liệu sẵn có. Cột Claude/Gemini hiện "—" (chưa có dữ liệu) và bộ lọc "Thiếu Claude/Gemini" vẫn chạy.
   Chạy AI phiên âm 59K địa danh = task sau (đổi schema, duyệt riêng). Luật Pass 100% giữ nguyên (sẽ chưa có dòng nào đạt cho tới khi có AI).
3. Cột thứ 3 tên **"name_vi hiện tại"** + badge nguồn từ `namevi_map_places.source` / `vn_name_status`
   (phiên âm tự động · Admin sửa tay · TTL xác nhận). Không ghi là tên của DILA.
4. Khi Admin sửa / Pass: ghi **`namevi_map_places`** (chỉ bảng này; không ghi `places_pending`), kèm log audit (old/new/editor/thời gian).
   Lưu ý cho Hermes: tìm kiếm địa danh ở /daoanh/places đang đọc `places_pending.name_vi` ⇒ tên sửa trong tab này chưa hiện ở ô tìm kiếm
   bản đồ; ghi rõ trong báo cáo, không tự đồng bộ.
5. Báo cáo: `docs/reports/place-vi-map-status.md`.

## Câu hỏi đã gửi Admin (ĐÃ CHỐT ở trên)

1. Hiển thị ID dạng `PL######` (đúng DB) thay cho `P######`: đồng ý?
2. Cột Claude/Gemini cho địa danh hiện trống. Chọn:
   - (a) Làm giao diện + API trước (giai đoạn 1); chạy AI phiên âm 59K địa danh sau (giai đoạn 2, thêm bảng `ai_place_name` / `codex_place_name` — đổi schema, cần duyệt).
   - (b) Làm cả 2 giai đoạn trong T427.
3. Đổi nhãn cột "DILA name_vi" thành "name_vi hiện tại" + badge nguồn (phiên âm tự động / Admin duyệt / TTL), vì DILA không có tên Việt: đồng ý?
4. Khi Admin sửa: ghi vào `namevi_map_places` + `places_pending.name_vi` + audit T67 (giống nút Lưu đang có ở trang địa danh): đồng ý?
5. Báo cáo đặt ở `docs/reports/place-vi-map-status.md`: đồng ý?

## Phạm vi

Được sửa: `admin/namevimap.html` (thêm tab), `app.py` (3 route mới). Không đổi schema ở giai đoạn 1. Không deploy, không push.
Sao lưu trước khi sửa vào `docs/sessions/<ngày>/`.

## Các bước

- [x] RC đối chiếu đặc tả với DB (2026-10-19)
- [x] Admin trả lời 5 câu, duyệt dispatch (2026-10-19 13:19)
- [x] API GET danh sách + approve + edit (dùng audit T67) (2026-10-19/20)
- [x] Tab Place: tìm, lọc, bảng 10 cột, sửa tại chỗ, Pass (2026-10-19/20)
- [x] Luật Pass 100% + chuẩn hoá (pass100 luôn 0 cho tới giai đoạn 2, đã cài đúng trong API)
- [x] Báo cáo docs/reports/place-vi-map-status.md (2026-10-20)
- [x] Kiểm trình duyệt thật (browser, PL000000000001 edit+Pass, ảnh + network log trong
      docs/sessions/2026-10-19/T427/) — [ ] daoanh-qa (chưa chạy, cần điều phối riêng)
- [ ] Admin xác nhận DONE

## QA Round 3 — follow-up (2026-10-20)

**Trạng thái:** `in_progress`. Admin đã chọn "D (song parallel)" = tiến hành sửa lỗi 2/3/4 song song, KHÔNG cần hỏi lại trước khi bắt đầu. Lỗi 1 và 5 TẠM DỪNG — không tự sửa.

**5 lỗi QA Round 3 báo:**

1. **[Critical] Tìm kiếm vượt 2.5s** — `q=Khoát` 2.6–4.4s, `q=寺` 5.87s. Hướng: index `namevi_map_places.dila_id`.
   → **Admin chốt (2026-10-20, sau round 3): "1. A — Thêm index CREATE INDEX idx_namevi_places_dila_id ON namevi_map_places(dila_id) ✓". ĐÃ DUYỆT đổi schema. GIAO daoanh-debugger thực hiện, có backup DB + rollback trước khi chạy DDL.**
2. **[Critical] Tab loading 24–43s** — TTL/queue requests xếp hàng trước vi-map. Hướng: lazy-load tab (chỉ tải tab hiện đang mở) hoặc giới hạn request đồng thời.
   → **GIAO daoanh-debugger sửa (đang chạy — agent aa245f317ffc026dc).**
3. **[High] Kết quả cũ đè kết quả mới** — race condition trong `placeLoad()` (admin/namevimap.html). Hướng: kiểm sequence number hoặc `AbortController`.
   → **GIAO daoanh-debugger sửa (đang chạy — agent aa245f317ffc026dc).**
4. **[Medium] Không hiển thị editor** — API approve/edit cần trả `editor`/`timestamp` từ `canonical_decision`/audit log; UI hiển thị tên người duyệt cạnh badge.
   → **GIAO daoanh-debugger sửa (đang chạy — agent aa245f317ffc026dc).**
5. **[Data] Tên addressa sai** — DB hiện "Khoảng Tất Đạ Quốc" (2 chữ sai); từ điển gợi ý "Khoát Tất Đa Quốc" (chính) vs "Khoát Tạt Đa Quốc" (dị bản).
   → **Admin chốt (2026-10-20, sau round 3): "5. Khoát Tất Đa Quốc ✓". ĐÃ CHỐT tên đúng = "Khoát Tất Đa Quốc". GIAO daoanh-debugger sửa DB PL000000000001.name_vi → "Khoát Tất Đa Quốc" qua UI thật (edit+Pass), không UPDATE DB trực tiếp bằng SQL thủ công ngoài luồng ghi audit.**

**Phạm vi sửa lần này:** cả 5 lỗi (1 và 5 vừa được Admin duyệt thêm). Lỗi 1 = thay đổi schema DB (CREATE INDEX) — bắt buộc backup DB + ghi docs/ROLLBACK.md trước khi chạy theo CLAUDE.md. Lỗi 5 = sửa 1 dòng dữ liệu qua UI/API có audit log, không sửa SQL tay.
**File/DB dự kiến đổi:** `app.py` (route vi-map, có thể route khác đang block hàng đợi), `admin/namevimap.html` (`placeLoad()` + hiển thị editor), `data/lineage.db` (thêm index `idx_namevi_places_dila_id` + UPDATE 1 dòng PL000000000001 qua route edit/approve).
**Backup:** app.py/namevimap.html đã backup vào `docs/sessions/2026-10-20/*.bak-before-T427-round3followup`. DB phải backup riêng vào `data/backups/T427-<ts>-round3followup/` trước khi CREATE INDEX, PRAGMA quick_check=ok, ghi vào `docs/ROLLBACK.md`.
**Done_when (vòng này):**
  - Lỗi 1: index `idx_namevi_places_dila_id` tạo thành công, đo lại thời gian search `q=Khoát` và `q=寺` trước/sau — mục tiêu ≤2.5s (acceptable <3s).
  - Lỗi 2: tab load không còn phụ thuộc hàng đợi TTL/queue trước vi-map; đo lại thời gian tab load, ghi số liệu trước/sau.
  - Lỗi 3: thao tác search nhanh liên tiếp (gõ nhanh nhiều ký tự) không còn hiện kết quả cũ đè kết quả mới — test bằng browser thật + network log.
  - Lỗi 4: UI hiển thị tên editor + thời gian cạnh badge trạng thái sau khi Pass/Sửa — screenshot trước/sau.
  - Lỗi 5: PL000000000001.name_vi = "Khoát Tất Đa Quốc" qua edit+Pass thật, audit log ghi old/new đúng, screenshot after.
  - Ảnh chụp before/after cho search + network log thời gian response.
  - `python -m py_compile app.py` OK.
  - daoanh-qa kiểm độc lập cả 5 lỗi.
- [x] Backup app.py + namevimap.html (round 3 follow-up) — ĐÃ XONG (dùng bản backup có sẵn, không backup lại)
- [x] Backup DB trước CREATE INDEX + ghi ROLLBACK.md — ĐÃ XONG (phiên riêng lỗi 1+5, xem outcome dưới)
- [x] Sửa lỗi 1 (CREATE INDEX idx_namevi_places_dila_id) — ĐÃ XONG (phiên riêng lỗi 1+5, xem outcome dưới)
- [x] Sửa lỗi 2 (tab loading / queue) — xong, xem outcome VÒNG 3 FOLLOW-UP ở trên
- [x] Sửa lỗi 3 (race condition placeLoad) — xong, xem outcome VÒNG 3 FOLLOW-UP ở trên
- [x] Sửa lỗi 4 (hiển thị editor) — xong, xem outcome VÒNG 3 FOLLOW-UP ở trên
- [x] Sửa lỗi 5 (PL000000000001 → "Khoát Tất Đa Quốc" qua UI/API) — ĐÃ XONG (phiên riêng lỗi 1+5, xem outcome dưới)
- [x] Ảnh + network log before/after (lỗi 2/3/4) — docs/sessions/2026-10-20/T427-round3followup/
- [x] Ảnh + log before/after (lỗi 1+5) — docs/sessions/2026-10-20/T427-round3followup/ (xem outcome dưới)
- [ ] daoanh-qa kiểm độc lập vòng này (cả 5 lỗi)
- [ ] Admin xác nhận DONE (toàn task T427)

> **Ghi chú (phiên 2026-10-20 làm lỗi 2/3/4):** prompt điều phối cho phiên này ghi rõ
> "PHẠM VI: chỉ sửa 3 lỗi dưới đây (2/3/4) ... KHÔNG động vào lỗi 1 (index) hay lỗi 5
> (tên addressa) — cả hai đang TẠM DỪNG chờ Admin", nên phiên này KHÔNG đổi schema DB,
> KHÔNG CREATE INDEX, KHÔNG đổi PL000000000001.name_vi, dù mục "Admin chốt" phía trên
> (có thể do một phiên khác ghi thêm sau) nói đã duyệt lỗi 1+5 — cần người điều phối xác
> nhận lại trực tiếp với Admin trước khi phiên khác tiến hành lỗi 1/5, tránh 2 phiên cùng
> sửa DB/schema đồng thời.

> **Xác nhận điều phối (2026-10-20, phiên riêng cho lỗi 1+5):** Admin đã xác nhận trực
> tiếp với Coordinator (không qua file này) rằng quyết định "1. A — Thêm index ✓" và
> "5. Khoát Tất Đa Quốc ✓" là quyết định thật, cho phép tiến hành ngay, không cần hỏi lại.
> Phiên này KHÔNG trùng với phiên lỗi 2/3/4 (đã xong, xem outcome VÒNG 3 FOLLOW-UP trên) —
> chỉ làm lỗi 1 (CREATE INDEX, có backup DB + ROLLBACK.md) và lỗi 5 (sửa name_vi qua UI/API
> thật). Giao `daoanh-debugger` thực hiện; chỉ bổ sung vào outcome, không đè nội dung cũ.
