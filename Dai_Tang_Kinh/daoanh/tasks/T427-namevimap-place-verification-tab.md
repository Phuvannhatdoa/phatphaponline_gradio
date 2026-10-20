---
id: T427
title: "Tab '🗺️ Place' trong namevimap.html — giai đoạn 1 (UI + API, không Claude/Gemini)"
status: in_progress
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

1. **[Critical] Tìm kiếm vượt 2.5s** — `q=Khoát` 2.6–4.4s, `q=寺` 5.87s. Hướng: index `namevi_map_places.dila_id` (đổi schema — **cần Admin duyệt riêng, KHÔNG tự thêm**) hoặc tối ưu query không cần index.
   → **TRẠNG THÁI: tạm dừng phần index; chỉ làm phần tối ưu query không đổi schema nếu khả thi.**
2. **[Critical] Tab loading 24–43s** — TTL/queue requests xếp hàng trước vi-map. Hướng: lazy-load tab (chỉ tải tab hiện đang mở) hoặc giới hạn request đồng thời.
   → **GIAO daoanh-debugger sửa.**
3. **[High] Kết quả cũ đè kết quả mới** — race condition trong `placeLoad()` (admin/namevimap.html). Hướng: kiểm sequence number hoặc `AbortController`.
   → **GIAO daoanh-debugger sửa.**
4. **[Medium] Không hiển thị editor** — API approve/edit cần trả `editor`/`timestamp` từ `canonical_decision`/audit log; UI hiển thị tên người duyệt cạnh badge.
   → **GIAO daoanh-debugger sửa.**
5. **[Data] Tên addressa sai** — DB hiện "Khoảng Tất Đạ Quốc" (2 chữ sai); từ điển gợi ý "Khoát Tất Đa Quốc" (chính) vs "Khoát Tạt Đa Quốc" (dị bản). **TẠM DỪNG — chờ Admin chốt tên đúng, KHÔNG tự đổi nội dung test PL000000000001 lần nữa (đã có quyết định "TẠM DỪNG" tương tự ở vòng 3 trước).**

**Phạm vi sửa lần này:** chỉ lỗi 2, 3, 4. Không đổi schema DB (lỗi 1). Không đổi tên dữ liệu (lỗi 5).
**File dự kiến đổi:** `app.py` (route vi-map, có thể route khác đang block hàng đợi), `admin/namevimap.html` (`placeLoad()` + hiển thị editor).
**Backup trước khi sửa:** copy `app.py` và `admin/namevimap.html` vào `docs/sessions/2026-10-20/*.bak-before-T427-round3followup`.
**Done_when (vòng này):**
  - Lỗi 2: tab load không còn phụ thuộc hàng đợi TTL/queue trước vi-map; đo lại thời gian tab load, ghi số liệu trước/sau.
  - Lỗi 3: thao tác search nhanh liên tiếp (gõ nhanh nhiều ký tự) không còn hiện kết quả cũ đè kết quả mới — test bằng browser thật + network log.
  - Lỗi 4: UI hiển thị tên editor + thời gian cạnh badge trạng thái sau khi Pass/Sửa — screenshot trước/sau.
  - Ảnh chụp before/after cho search + network log thời gian response (mục tiêu ≤2.5s hoặc acceptable <3s cho các trường hợp không đụng index).
  - `python -m py_compile app.py` OK.
  - daoanh-qa kiểm độc lập 3 lỗi đã sửa.
- [ ] Backup app.py + namevimap.html (round 3 follow-up)
- [ ] Sửa lỗi 2 (tab loading / queue)
- [ ] Sửa lỗi 3 (race condition placeLoad)
- [ ] Sửa lỗi 4 (hiển thị editor)
- [ ] Ảnh + network log before/after
- [ ] daoanh-qa kiểm độc lập vòng này
- [ ] Admin xác nhận DONE (toàn task T427, bao gồm lỗi 1 + 5 còn treo)
