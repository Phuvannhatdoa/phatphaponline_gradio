# T322 — DEV-REPORT (2026-10-31)

Task: `tasks/T322-docs-cap-nhat-reality-check-plan.md`. Trạng thái: **in_progress** (chưa DONE —
chờ Admin xác nhận theo `done_when`).

Nguồn số liệu duy nhất dùng trong báo cáo này: `docs/sessions/2026-10-31/T322_measure_log.md`
(mọi số liệu đo chỉ-đọc) và `docs/qa_reports/QA-2026-10-31-T322.md` (báo cáo tester,
`final_status: EVIDENCE_INCOMPLETE`). Mỗi số liệu dưới đây ghi rõ nguồn; không bịa số nào ngoài
hai file này.

## 1. Mục tiêu phiên này

Xử lý các mục **không cần Admin quyết** trong QA-2026-10-31-T322 (mục 1.1–1.10 theo yêu cầu điều
phối): bổ sung DEV-REPORT, thêm block tasktodo, sửa frontmatter + checklist task, sửa 6 chỗ câu
chữ trong `REALITY_CHECK.md`. KHÔNG xử lý mục 2a/2b/2c (định nghĩa route chuẩn, mâu thuẫn T231,
cập nhật CLAUDE.md) — thuộc quyền Admin.

## 2. Việc đã làm trước đó (2026-10-31, trước lượt QA này)

Theo `T322_measure_log.md`: đo lại ở chế độ chỉ đọc (`sqlite3 mode=ro`, `os.path.getsize`,
regex `@\w*\.route(` qua `python -I`, không ghi DB/không sửa code) rồi sửa
`docs/integration/REALITY_CHECK.md` và `docs/integration/00_PLAN_OVERVIEW.md`, có sao lưu
`REALITY_CHECK.md.bak-before-t322` và `00_PLAN_OVERVIEW.md.bak-before-t322`.
(Nguồn: `T322_measure_log.md` mục đầu + mục "Kết luận đo".)

## 3. Số liệu đo (nguồn: `T322_measure_log.md`)

- DB `data/lineage.db`: 1.825.574.912 bytes (mục 1).
- Số bảng `sqlite_master type='table'`: 217 (mục 2).
- `data_sources`: 16 dòng (mục 3).
- `entity_claims` theo nguồn: DILA 293.177, ZQLOCAL 118.295, MARCUS 22.332, CBETA 13.933,
  Wikidata 148 — tổng 447.885, khớp số đo 2026-10-02 (mục 4).
- Route: tổng đếm bằng regex decorator = 448; trừ 11 route thuộc 5 file tooling dev/test còn 437 —
  đây là **cận dưới**, không phải số tuyệt đối (chưa đo `app.url_map` lúc runtime) (mục 5).
- T231: 2 bản file giống nhau, `status: done` nhưng Step 4 thân bài vẫn `⬜ TODO`;
  `ZENLINEAGE` đo được `NULL` thay vì `LEGACY` như task ghi (mục 6).

## 4. Kết quả QA độc lập (nguồn: QA-2026-10-31-T322.md)

- `done_when` #1 (M1 có T231) và #2 (số liệu DB/route mới) → **đạt**, mọi số đo lại độc lập khớp
  nội dung đã ghi trong `REALITY_CHECK.md`/`00_PLAN_OVERVIEW.md`.
- `done_when` #3 (Admin xác nhận DONE) → **chưa**, ngoài quyền tester.
- `npm run guard` → exit 0; `npm run dup:ids` → exit 0.
- Backup `.bak-before-t322` khớp `git show HEAD:<file>` (bỏ qua CRLF) → backup hợp lệ, revert được.
- `production_mutation_detected: false` — không ghi DB/TTL, chỉ sửa 2 file docs + thêm file
  trong `docs/sessions/`.
- `final_status: EVIDENCE_INCOMPLETE` vì: (a) thiếu DEV-REPORT, (b) frontmatter T322 vẫn
  `pending`/checklist chưa tick, (c) `docs/tasktodo.md` chưa có block T322, (d) dòng 1
  `REALITY_CHECK.md` vẫn ghi ngày cũ 2026-10-02.

## 5. Thay đổi trong lượt này (xử lý EVIDENCE_INCOMPLETE — chỉ phần không cần Admin)

- Sao lưu trước khi sửa: `docs/sessions/2026-10-31/tasktodo.md.bak-before-t322-qa`,
  `docs/sessions/2026-10-31/T322-docs-cap-nhat-reality-check-plan.md.bak-before-t322-qa`.
- `docs/integration/REALITY_CHECK.md`:
  - dòng 1: "Cập nhật lần cuối: 2026-10-02" → "Cập nhật lần cuối: 2026-10-31 (T322)".
  - Gap #2 (bảng "Khoảng cách lớn nhất"): giữ nguyên mức **P0**, sửa câu chữ để không còn mâu
    thuẫn với mục "entity_claims" (ghi rõ T231 Step 1–2 chỉ UPDATE cột `legal_status_at_ingest`
    thành `LEGACY` — là pass-through dữ liệu, không phải nối code gate vào ETL/route; Step 4 của
    T231 vẫn TODO; T322 chưa review code `LicenseGate`).
  - Các đoạn dòng 22–23, 92–93, 113, 180 (`.claude/settings.json`), 183 (DB size/số bảng trong
    CLAUDE.md) đã đối chiếu lại với `T322_measure_log.md` và nội dung QA xác nhận "đạt" ở
    `done_when` #1/#2 — **đã đúng từ trước, không cần sửa thêm** (nếu sửa thêm sẽ phá bằng chứng
    đã khớp số đo độc lập mà QA vừa xác nhận).
- `tasks/T322-docs-cap-nhat-reality-check-plan.md`:
  - frontmatter: `status: pending` → `in_progress`; `updated: 2026-10-10` → `2026-10-31`; thêm
    dòng `outcome` 2026-10-31 (không đổi `done_when`, `depends_on`, `id`).
  - checklist mục 6: tick Bước 1–4 (`[x]`); Bước 5 "Admin xác nhận DONE" giữ `[ ]`.
- `docs/tasktodo.md`: thêm block `<!-- T322:START -->`...`<!-- T322:END -->` giữa dòng trỏ archive
  (T376) và `<!-- T507:START -->`, trạng thái **⏳ IN_PROGRESS** (không DONE).
- Sau quyết định Admin ở mục 9: tạo 4 task mới `tasks/T508-route-count-url-map.md`,
  `tasks/T509-t231-step4-license-gate-route.md`, `tasks/T510-zenlineage-license-history-check.md`,
  `tasks/T511-claude-md-remove-hardcoded-counts.md` (đều `status: pending`); sửa `docs/ROLLBACK.md`
  thêm mục ghi lại việc thêm 4 block T508–T511 vào `docs/tasktodo.md` + lệnh revert tương ứng
  (sao lưu `docs/sessions/2026-10-31/tasktodo.md.bak-before-t508-511` và
  `docs/ROLLBACK.md.bak-before-t508-511` trước khi sửa cả hai file).
- File báo cáo này.

## 6. Việc KHÔNG làm trong lượt này (thuộc quyền Admin — mục 2a/2b/2c)

- (a) Chốt định nghĩa "số route chuẩn" (437 vs 448, có đo `app.url_map` không).
- (b) Quyết định mâu thuẫn T231 Step 4 vẫn TODO dù `status: done`, và `ZENLINEAGE` đo `NULL`
  thay vì `LEGACY`.
- (c) Cập nhật `CLAUDE.md` theo số đo mới (1,70 GiB / 217 bảng / 16 nguồn).
- KHÔNG sửa `CLAUDE.md`, KHÔNG sửa `tasks/T231-...`, KHÔNG ghi DB, KHÔNG `git add/commit/reset`,
  KHÔNG đánh DONE.

## 7. Lệnh kiểm chạy trong lượt này

- `npm run guard` — xem mục 8.
- `npm run dup:ids` — xem mục 8.
- Grep đối chiếu các điểm QA nêu ở mục 3 của QA report — xem mục 8.

## 8. Kết quả lệnh kiểm (output đầy đủ, chạy lại sau lượt sửa câu chữ 2026-10-31)

```
$ npm run guard
> python -X utf8 scripts/repo_guard.py
[OK] SSOT repo root = E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app
[OK] Khong co .git that trong Dai_Tang_Kinh/daoanh/
```

```
$ npm run dup:ids
> python -X utf8 scripts/build_progress_data.py --check-dup-ids
[DUP-ID] tasks/*.md + docs/**/*.md (đã loại trừ _book/)
[INFO] 10 ID có bản X- superseded (hợp lệ theo quy ước): T165, T166, T168, T169, T172, T173,
  T174, T175, T176, T220
[INFO] 1 ID có bản docs/ gắn liền task (`task: tasks/...`): T199 (2 file phụ)
[OK] Không có task ID trùng thật.
```

Cả hai lệnh exit 0 — không có ID trùng thật, không có anomaly repo root/`.git` lồng.

## 9. Quyết định Admin (2026-10-31, họp T322 — 3 việc ở mục 6)

Admin đã quyết rõ cả 3 việc nêu ở mục 6 (không còn mở nữa ở T322 — mỗi việc tách thành task
riêng để theo dõi và làm độc lập):

- **(a) Số route chuẩn — chọn phương án C**: đo bằng `len(app.url_map)` lúc app đang chạy
  thật, tách riêng app.py (5000) và server.py (5001); số tham chiếu tĩnh 437 giữ nguyên làm
  mốc so sánh. → tách thành `tasks/T508-route-count-url-map.md`.
- **(b) T231 — chọn phương án B**: giữ T231 ở trạng thái `done`; tách Bước 4 (nối LicenseGate
  vào route app — thân bài vẫn `⬜ TODO`) thành task riêng; đồng thời việc đọc lịch sử
  `legal_status_at_ingest` của ZENLINEAGE (đo được `NULL` thay vì `LEGACY`) cũng tách thành
  task riêng. → `tasks/T509-t231-step4-license-gate-route.md` (Bước 4) và
  `tasks/T510-zenlineage-license-history-check.md` (lịch sử ZENLINEAGE).
- **(c) CLAUDE.md — chọn phương án B**: bỏ số cứng, trỏ tới `docs/integration/REALITY_CHECK.md`;
  làm thành task riêng, thực hiện **SAU KHI T322 đã DONE**. → `tasks/T511-claude-md-remove-hardcoded-counts.md`.

Bốn task mới (T508–T511) đều `status: pending`, chưa bắt đầu làm trong lượt này.

## 10. Limitation / blocker còn lại

- Mục này **đã đóng theo §9** — xem `tasks/T508-route-count-url-map.md`,
  `tasks/T509-t231-step4-license-gate-route.md`, `tasks/T510-zenlineage-license-history-check.md`,
  `tasks/T511-claude-md-remove-hardcoded-counts.md`. Cả 3 việc Admin phải quyết ở mục 6 đã được
  Admin quyết (họp T322, §9) và tách thành 4 task riêng (T508–T511); T322 không còn bị các việc
  này chặn. Việc còn chờ duy nhất: Admin xác nhận DONE (Bước 5 checklist task).
