# Session 2026-09-07 — ACADEMIC_16TABS_V1: Phê chuẩn + Task 0 inventory + Batch 1 docs + Batch 2 P0-SAFETY + Batch 3 P1-BACHELOR

> Trạng thái: ✅ Batch 1 (docs/task/dashboard data) + ✅ **Batch 2 (P0-SAFETY, 1d8770da)** + ✅ **Batch 3 (P1-BACHELOR)** hoàn thành. Còn lại P2–P4.
> Task: `tasks/T100-academic-16-tabs-framework.md` · Plan: `docs/ACADEMIC_16TABS_IMPLEMENTATION_PLAN.md` · Inventory: `docs/ACADEMIC_16TABS_INVENTORY.md`

---

## 1. Bối cảnh

Sau khi debug xong Nexus Line-1 (commit A `ad442caa` / B `088df714` / C `dfc87a4`), admin yêu cầu kiểm tra logic đề xuất "GIÁO LÝ tab" + SPEC `ACADEMIC_3_LEVELS_16_TABS_V1`. Tôi kiểm tra read-only: xác nhận tab GIÁO LÝ hiện = "Đối Chiếu Tam Tạng" (render `renderGiaolyTab` places.html:6232, `api_cbeta_compare` app.py:13940, Pali empty state 6274-6277, `pali_place_ref` 15 row thánh địa Ấn — Thiếu Lâm Tự = 0), DB evidence infra đã có sẵn (entity_claims 447,885 / event_evidence+events 3,530 / event_text_link 17,284 / glossary_term 248,095 / term_glossaries 18,127 / pali_place_ref 15), **chưa có** bảng doctrine/concept, **chưa có** nút "Chọn khái niệm/Mở Nexus".

## 2. Verdict logic (6 điểm rút gọn)

1. "16 tab" = target taxonomy, hiện tại thực tế **15 tab** (thiếu `entities`) — 3 tab thật của cbeta+daitang gộp = 1 Tripitaka.
2. Evidence contract trong đề xuất ~70% **đã tồn tại** trong DB (không phải viết mới từ đầu).
3. "Minh bạch quan hệ 3/10" hiểu thấp dữ liệu thật (marcus_networks, place_person_bibl toàn có source/ref).
4. Pali empty state nên là **NOT-INDEXED** (chỉ 15 record rà soát) chứ không "không có".
5. Header block "Chọn khái niệm/Mở Nexus" mô tả UI **chưa tồn tại** — chỉ nên thêm cùng code P2.
6. "5.5/10" chủ quan → thay bằng **chấm 2 trục** data-exists/UI-displays kèm bằng chứng.

## 3. Quyết định admin (chốt cứng)

- **Cả khung** (ACADEMIC_3_LEVELS_16_TABS_V1 cho toàn bộ 16 tab).
- **Phân đôi cùng tab** (GIÁO LÝ: khối giáo lý Phật học + khối Đối Chiếu Tam Tạng; không tab mới).
- **Chấm 2 trục** thay điểm chủ quan.

## 4. Việc đã làm (Batch 1 — chỉ docs/tasks/dashboard data, không code)

| Việc | Kết quả |
|---|---|
| Probe code + DB thật | tab list 15, render fn 10 thật/6 stub (`_renderPendingTab`), route ánh xạ, số row 20 bảng evidence, `entity_claims` 100% 'unverified', `events` 100% 'candidate' |
| Task file | `tasks/T100-academic-16-tabs-framework.md` (YAML chuẩn README, module `Hạ tầng / Docs`, status in_progress, acceptance 5 batch) |
| Plan chi tiết | `docs/ACADEMIC_16TABS_IMPLEMENTATION_PLAN.md` (16-tab mapping, mô hình 2 trục × 6 dimension, bảng reuse dữ liệu, phases P0→P4, dashboard spec 8 alert, 5 rủi ro) |
| Inventory baseline | `docs/ACADEMIC_16TABS_INVENTORY.md` (bảng 15 tab, số row DB, scorecard sơ bộ, alert đầu, định nghĩa NOT-INDEXED) |
| Session | file này |
| tasktodo.md | thêm block T100 (đầu file) |
| progress.md | thêm dòng Cập nhật 2026-09-07 |
| Dashboard | chạy `python scripts/build_progress_data.py` → `progress_data.json` (Task Board hiện T100) |
| ROLLBACK.md | Bổ sung khi có commit (commit 2 này+hash) |

## 5. Rollback

- Batch 1 (docs/task/dashboard json): `git revert <commit Batch1>`. Batch 2 (P0-SAFETY): `git revert <commit Batch2>`.
- Không có DB thay đổi trong Batch 1/2 → không cần restore DB.
- Batch 3+ mỗi batch = 1 commit riêng; P2 schema additive kèm `--revert`/backup.

## 6. Việc tiếp theo

- **Batch 3 = P1-BACHELOR:** đủ 16 tab canonical ID + nguồn + empty-state đồng bộ · tab mới `entities` (thực thể tổng hợp) · 6 tab stub (thuvien/nghile/giaoduc/dulieu/hinhanh/nghethuat) có nội dung tối thiểu trung thực, đồng bộ `fix_tabs.js` 15→16 tab (alert #1) + giải 6 route stub (alert #6) · docs + commit riêng.
- Trước khi làm P2, confirm Risk R1 (giữ label nút tab — mặc định giữ) + version ngày index cho message Pali.
- Server :5000 cần restart khi có code live-test (hiện blocked).

## 7. Commits + kiểm thử (Batch 1)

| Commit | Nội dung |
|---|---|
| `4fe6f670` | Batch 1 — task T100 + plan + inventory + session + tasktodo + progress + data/progress_data.json (7 files, blob==HEAD 7/7 ✅) |
| `2559f285` | docs — ROLLBACK.md thêm T100 batch1 hash + revert 1 lệnh từng batch |

- **Kiểm thử:** `npm run test` ✅ PASS · `npm run e2e` ✅ (mọi trang pass) · `npm run lint` = **fail sẵn từ trước** (ESLint vs Node v24/Windows — env, không phải code, đã ghi chú ở docs/ROLLBACK.md §5) · Batch 1 chỉ docs/json → syntax test không dính JS.
- Dashboard sau revert tạo `data/progress_data.json`: **112 task, 15 module, 65%**, T100 = `in_progress` (4/23 criteria tick).

## 8. Batch 2 — P0-SAFETY (DONE 2026-09-07)

**Commit:** `1d8770da` (places.html + app.py + scripts/build_tab_readiness.py + data/tab_readiness.json + dashboard/tab_readiness.html + docs). Rollback: `git revert 1d8770da`.

### 8.1. Code (places.html — sau `_nexusSafeLabel`)

1. **Helpers chung:** `_daSafeLabel(label, id)` (fallback `label||label_zh||id`), `_daEmptyState({notIndexed, taxonomy, scope, count, note})` (render khối NOT-INDEXED trung thực bằng token `--da-amber`, dùng `_escHtml`), `_daEvidenceBadge(type)` (`DIRECT/THEMATIC/SCHOLARLY/CANDIDATE/UNVERIFIED/DERIVED`).
2. **Empty-state trung thực:** `_renderPendingTab` (stub) → `_daEmptyState({notIndexed:true, taxonomy:'Tab chưa có API nguồn', ...})`; Pali (trong `renderGiaolyTab`) → `NOT-INDEXED — 15 thánh địa Ấn` thay câu "chưa có kinh điển Pali" mờ.
3. **Dispatch fix:** `openTab` (places.html dispatch) xử lý `tab==='entity'` (nút 地 Thực Thể — trước chỉ có nhánh `cbeta` không có button → click không làm gì).
4. **Co-mention dashed:** `_renderVisGraph` — edge không `derived` và không có evidence (`_daEdgeHasEvidence`) → `coMention=true` → `dashes:[2,4]`, màu nhạt (`.33`/`.66`), tooltip "Đồng xuất hiện… shock" (nghi vấn: không phải quan hệ trực tiếp).

### 8.2. API mới (app.py, read-only)

- `GET /daoanh/api/evidence/<subject_id>` (`api_evidence`): trả `{meo_events, claims, co_mentions, data_status}`:
  - `meo_events`: `events` join `event_evidence` LIMIT 200 (3,530 rows schema `events.event_id`).
  - `claims`: `entity_claims` LIMIT 200 JOIN `data_sources` (resolve id qua `_resolve_entity_id` → `entity_hub.canonical_label` hoặc `entity.dila_id`).
  - `co_mentions`: `event_text_link` WHERE `entity_id=? OR related_id=?` LIMIT 300 (17,284 rows).
  - `data_status`: counts + note trung thực (100% unverified/candidate).
- Đúng SKILL: evidence response chỉ là **source của dữ liệu**, không tạo quan hệ mới.

### 8.3. Tab readiness (script + dashboard + JSON)

- `scripts/build_tab_readiness.py` → `data/tab_readiness.json`: quét `places.html` bar `#da-stabs` = **16 tab**; phát hiện 6 stub (`_renderPendingTab`); so `fix_tabs.js` (15 → alert #1); dispatch entity check (RESOLVED); helpers/route presence; ĐB counts zero-RAM (mở với SQLite đọc dòng, không load toàn bộ); 8 alert; score từng tab /12 (data-exists 6 + UI-displays 6).
- Kết quả: core 9 tab avg **10.33/12** ≥9 ✅ (entity 11, graph 11, nexus 11, giaoly 11, bandoo 10, persons 10, lineage 10, sukien 10, daitang 10); 6 stub = 2/12 (CHƯA ĐẠT); alerts: #1/#2/#4/#5/#6 OPEN (fix_tabs 15v16, 6 stub, entity_claims unverified, events candidate, 6 no route), #3/#7/#8 RESOLVED.
- `dashboard/tab_readiness.html`: dark-slate/amber, fetch `data/tab_readiness.json`, hiển thị chips + threshold + per-tab score bar.

### 8.4. Verify

- `py_compile app.py` ✅ · `node --check` (script places.html) ✅ · `npm run test` PASS ✅ · `npm run e2e` PASS ✅ · `npm run lint` fail sẵn (env).
- JSON hợp lệ (16 tab / 8 alert / core_avg 10.33); unit mirror `_resolve_entity_id` PL000000023255→181597, A003623→221794.
- Live :5000 blocked → không live-test (đã ghi chú).

### 8.5. Concurrency / git

- Commit riêng qua temp-index (GIT_INDEX_FILE + read-tree HEAD + add + write-tree + commit-tree -p 7d5a57b + ref-write guard), verify blob==HEAD cho mọi file.
- **Lưu ý:** backup agent đã đụng real index (staged M app.py/places.html + staged D các doc Batch-1 + thêm BUG TRACKER tasktodo). Bản commit này = HEAD + đúng các hunk Batch-2 (không trộn agent WIP: bản dịch Romanian→Việt của agent vẫn nằm riêng).

## 9. Batch 3 — P1-BACHELOR (DONE 2026-09-07)

**Commit:** `7ef6db0` (places.html + fix_tabs.js + scripts/build_tab_readiness.py + data/tab_readiness.json + dashboard/tab_readiness.html + docs). Rollback: `git revert 7ef6db0`.

### 9.1. Tab mới `entities` — 🧩 Thực Tổng Hợp (nút thứ 17)

- Button bar (`#da-stabs`, sau `nghethuat`): `<button class="da-stab" data-t="entities">🧩 Thực Tổng Hợp</button>`. **17 nút vật lý** (16 taxonomy; cbeta+daitang→Tripitaka về khái niệm → taxonomy 16; giữ label nút cũ theo R1).
- Panel `#tp-entities` (sau `#tp-nghethuat`): placeholder + `#entities-content`.
- Dispatcher `loadTabData`: `else if (tab === 'entities') loadEntitiesTab(placeId)`.
- `loadEntitiesTab(placeId)` → fetch `/daoanh/api/evidence/<subject_id>` → `renderEntitiesTab(d)`:
  - Header identity + 3 `_daMiniStat` (CLAIMS/EVENTS/CO-MENTIONS).
  - Claims list (predicate → object_text, badge UNVERIFIED qua `_daEvidenceBadge`, confidence) LIMIT 200.
  - Events list (title, năm, badge CANDIDATE, event_type) LIMIT 200.
  - Co-mention CBETA list (source_book/cbeta_ref/ref/related_name) LIMIT 100.
  - Empty state trung thực khi không có dữ liệu.

### 9.2. Real hóa 6 tab stub — nội dung tối thiểu TRUNG THỰC

- **`renderDulieTab(placeId)`** thay `_renderPendingTab('dulieu')` → fetch evidence → `renderDulieEvidence(d)` render `data_status` THẬT: claims total/by_type/verification (100% unverified thật), events reviewed, co_mentions distinct + notes trung thực. **10/12 Cao học.**
- **5 tab còn lại** (thuvien/nghile/giaoduc/hinhanh/nghethuat) dùng helper mới **`_daStubTab(tabKey, placeId, taxonomy, scope)`** = identity header (canonical ID `dila_id||id`, name_vi/name_zh, nguồn — từ `/daoanh/api/places/<id>`) + `_daEmptyState({notIndexed:true, taxonomy, scope})` đúng taxonomy từng tab. **6/12 Cử nhân.**
- Xoá mọi lời gọi `_renderPendingTab('key')` còn lại (dispatch cũ truyền `null` → `placeId` cho 6 tab).

### 9.3. fix_tabs.js — đồng bộ 15→**17** (đóng alert #1)

- Thêm `nexus` (sau `lineage`) + `entities` (cuối), khớp 1:1 với bar places.html. File không còn lỗi thời "15 tabs".

### 9.4. build_tab_readiness.py (Batch 3)

- TAB_INFO thêm **`entities`**: `{fn:'renderEntitiesTab', route:'/daoanh/api/evidence/<subject_id>', route_frag:'api/evidence/<subject_id>', table:'entity_claims'}`.
- **`dulieu`**: route → evidence API (cùng route_frag/table).
- 5 tab identity: route `/daoanh/api/places/<id>` (route_frag `api/places/<place_id>`), table None.
- `ui_evidence` thêm `dulieu` + `entities`.
- Docstring + alert #1 title cập nhật (17 tab).

### 9.5. Kết quả scorecard

- `tabs: 17 · stubs: 0 · fix_tabs.js: 17 · core_avg: 10.33/12`.
- dulieu **10/12 Cao học**; entities **10/12 Cao học**; 5 identity tab **6/12 Cử nhân**.
- **8 alert: #1/#2/#3/#6/#7/#8 RESOLVED · #4 (entity_claims 100% unverified) + #5 (events 100% candidate) OPEN = P3.**

### 9.6. Verify

- `node --check` extracted script places.html ✅ · `node --check fix_tabs.js` ✅ · `py_compile app.py + build_tab_readiness.py` ✅ · `npm run test` PASS ✅ · `npm run e2e` PASS ✅ · anchors 11/11 ✅ (helpers + panel + dispatcher + stub).
- DB field verify (đọc schema thật): entity_claims (predicate/object_text/confidence/verification_status) · events (review_status/title_zh/vi/start_year/end_year/event_type) · event_text_link (cbeta_ref/source_book/source_ref/related_name) — khớp field render ✅.
- Live :5000 blocked → chưa live-test UI (đã ghi chú trong ROLLBACK §5).

### 9.7. Concurrency / git

- Worktree index vẫn bị backup agent đụng (staged M/D many files). Commit = **temp-index từ b3_head_* bases** (HEAD blob + hunk Batch 3), parent `917be636`; không đụng real index; agent WIP (Nexus labels + `_graphNetwork.fit()`) không vào commit.
- `data/` git-ignored → stage thủ công gồm `data/tab_readiness.json` + `dashboard/tab_readiness.html` như batch 2.
- ROLLBACK.md ghi dòng batch 3 + hash khi commit xong.