---
id: T253
title: "Person Import (XML DILA authority → DB): Phase 0 audit + chốt plan Phase 1"
module: Import / Person Authority
priority: medium
status: done
created: 2026-10-06
updated: 2026-10-07
owner: opencode
depends_on: [T200, T223, T254]
designed_by: "Đề xuất: Cline · audit: opencode session"
plan_approved_at: "2026-10-06 (Admin đồng ý build báo cáo audit Phase 0 + đăng ký task) + 2026-10-06 (Admin chốt P0-1 = (a))"
done_when: >
  Phase 1 (sau khi Admin chốt P0-1 phương án (a)|(b)) build xong trang
  admin/person_import.html import được Buddhist_Studies_Person_Authority.xml
  vào DB có backup + manifest revert, duplicate check backend batch read-only
  theo VNPA_STATUS_RANK (KHÔNG auto-merge — thuộc T223), test nối vào
  package.json (test:t253), `npm run pipeline` xanh, và git diff app.py
  (nếu chọn phương án a) CHỈ có dòng +.
blocked_reason: >
  ĐÃ CHỐT 2026-10-06: Admin đồng ý P0-1 = (a) additive route (tiền lệ app.py:10167
  cbeta import-xml), nghiệm thu git diff app.py chỉ +; P0-2 backend batch read-only
  theo VNPA_STATUS_RANK (không auto-merge — T223). Phase 1 build khởi động;
  blocker còn lại là pipeline dup:ids (đã xử qua T254).
revert: "git revert --no-edit <sha> (docs-only: report + task + session + tasktodo + ROLLBACK + progress_data; 0 code, 0 DB)."
former_ids: []
---

# T253 — Person Import: Phase 0 audit (Cline) + plan Phase 1

## 1. Vì sao mở task

Cline đề xuất tính năng **import người** từ XML
`data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml`
(51.070.872 byte) qua trang admin mới `admin/person_import.html`, kèm báo cáo
Phase 0 claim nhiều thứ đã có sẵn trong `app.py`. Admin **đồng ý build phần audit**
(2026-10-06): kiểm chứng lại toàn bộ, đính chính, chốt blocker, đăng ký task,
lưu session log, commit — **chưa** build Phase 1.

## 2. Kết quả Phase 0 (HOÀN THÀNH — 2026-10-06)

Báo cáo đầy đủ + bằng chứng + lệnh tái chạy:
**`docs/integration/Cline/2026-10-06-person-import-phase0-audit.md`**

- **13 claim đúng** (route `persons/:19016`, `dila_full:20072`, `dila_translate:19475`,
  `adjacent:8548`, static admin `:2109`; 0 `ET.tostring`; 0 `.xsd/.rng`;
  XML 51.070.872 byte; 0 route `INSERT INTO people`; schema 2 bảng đích…).
- **6 đính chính (S1…S6)** — trọng tâm: S1 `app.py` = **24.221 dòng tổng**
  (Cline đúng; audit vòng trước dùng `Measure-Object -Line` nên ghi nhầm 22.487),
  S2 `xml.etree` import **5 chỗ** (`111, 126, 5635, 10304, 10465` — `_t148_ET` ở `:5635`).
- **2 blocker** P0-1 (§3 dưới) + P0-2 (§4 dưới) — chờ Admin.

## 3. P0-1 — ràng buộc "không đụng app.py" vs cần POST route (CHỜ ADMIN CHỐT)

- Tính năng gọi từ trình duyệt ⇒ cần POST route ⇒ phải đụng `app.py`;
  §2 #12 của báo cáo: **không** route nào tạo người mới.
- **(a) additive route (khuyến nghị):** tiền lệ `POST /daoanh/api/admin/cbeta/import-xml`
  (`app.py:10167`, load script ngoài bằng `importlib` `:10193`;
  `cbeta-import.html:263` fetch + `:270` refresh). Route mới chỉ **+**;
  nghiệm thu `git diff app.py` không có dòng `-`.
- **(b) offline script:** `scripts/…` chạy tay, không đụng `app.py`, không có UI tiến trình.

## 4. P0-2 — duplicate `dila_id` = backend batch read-only (đã chốt hướng, chờ T223)

Không route trả `vn_person_authority` theo lô ⇒ N+1 GET từ browser **không làm được**.
`dila_id` không unique (T200: **33 nhóm**; tie-break `VNPA_STATUS_RANK` chỉ chọn tên).
=> 1 endpoint read-only batch, **không auto-merge, không ghi DB** — Admin quyết (T223).

## 5. Checklist Phase 1

Xem §7 báo cáo: additive-only · script ngoài + test nối `package.json` (`test:t253`) ·
1 trang 1 framework · test/query acceptance viết trước · XML bất biến + backup DB ·
`npm run pipeline` xanh trước khi xin review.

## 6. Blocker pipeline CÓ SẴN — ĐÃ XỬ QUA T254

`npm run dup:ids` trước vốn FAIL với **3 ID trùng có sẵn**: `T188` (task ↔ docs/integration),
`T237` (`cbeta-corpus-search-reader` ↔ `gate-vpa-admin-confirmed-only`), `T238`
(`cbeta-text-browser-toc` ↔ `reject-ttl-mismatch-button`). Theo AGENTS §16 phải đổi số bên
footprint nhỏ nhất → **đã sửa qua T254** (`docs/integration/T188-canonical… → T255`,
`gate-vpa → T256`, `reject-ttl → T257`, `former_ids` + cập nhật tham chiếu T189/T239/T240)
⇒ `npm run dup:ids` giờ PASS.

## 7. Revert

`git revert --no-edit <sha>` — docs-only (report + task + session + tasktodo + ROLLBACK + progress_data);
**0 code, 0 DB**. Không có dữ liệu nào bị thay đổi.


---

## 8. Phase 1 — BUILD DONE (2026-10-07)

Admin duyệt build. TDD: test trước → code ETL → route → UI → pipeline.

- **ETL `scripts/person_import_etl.py`** (đặt `scripts/` vì `data/` bị `.gitignore:3` ⇒ không
  track được ⇒ không revert được bằng git; convention các ETL person khác cũng ở `scripts/`):
  `validate()` read-only · `commit()` additive idempotent (1 transaction ghi `vn_person_authority`
  + `person_import_manifest`, backup DB → `data/backups/person-import-<run_id>/`) ·
  `revert(run_id)` (DELETE theo manifest, `--restore-db` phục hồi nguyên DB) · `list_runs_at`.
  Map cột 1:1 (quy tắc KHÔNG BỊA — T252): `dila_id`, `name_zh`, `appellations` (JSON array),
  `gender` (sex 1→Male, 2→Female, 0/9→NULL); `status='pending'`, `ttl_filename=''`;
  name_vi/dharma_title/birth/death/dynasty = **NULL, không phỏng đoán**. Extra raw
  (dynasty/origin/works/bibl) chỉ vào `manifest.json` artifact, không vào DB.
- **Route** `POST/GET /daoanh/api/admin/person/import-xml` (app.py chỉ `+`, verified diff):
  `action=validate|commit|revert|runs`, `verify_session` (X-Session-Token → gateway :5001),
  importlib nạp ETL (tiền lệ `t181_import_xml`).
- **UI** `admin/person_import.html` (Tailwind vanilla 1 framework): summary cards, khung preview
  skip (dila_id đã có → T223), table runs + nút Revert.
- **Tests** `tests/test_t253_person_import.py` 4/4 (DB temp + fixture XML: validate / commit fields /
  idempotent / revert / list_runs) + wire `test:t253` vào `package.json` pipeline.
- **Pipeline XANH** `npm run pipeline` (guard → dup:ids → honesty → lint → test →
  t226/t227/t232/t233/**t253** → translation → uat → compliance → gov → audit:t166 → e2e → e2e:runtime).
- **Validate XML thật (51.070.872 B):** 48.803 person · 0 no_id · 0 no_name ·
  sex {1:46348, 2:1600, 9:280, 0:575} · skip 1.262 (dila_id đã có trong DB, gắn T223) ·
  skipped_dup=0 · sẽ thêm **47.541** · sha256 `e3f2b01b…`.
- **Chưa làm (Admin quyết lúc chạy):** bấm "Nhập vào DB" tại `admin/person_import.html`
  (hoặc CLI `--action commit`) để INSERT 47.541 hàng — build KHÔNG tự import vào DB.
  Revert khi đó = `scripts/person_import_etl.py --action revert --run-id <PI-*>`.

### Lệnh vận hành (chạy từ daoanh)

```bash
python -X utf8 scripts/person_import_etl.py --action validate   # quét lại, đếm sẽ thêm
python -X utf8 scripts/person_import_etl.py --action commit     # INSERT additive (idempotent)
python -X utf8 scripts/person_import_etl.py --action runs       # lịch sử run
python -X utf8 scripts/person_import_etl.py --action revert --run-id <id>   # xoá đúng hàng run
```

Verify nhanh trong 1 phút: `python -X utf8 tests/test_t253_person_import.py` → `T253 PASS 4/4`.


## Ranh giới với T357 — 2026-10-11

[T357](T357-vnpa-etl-safety-remediation.md) là kế hoạch an toàn TTL-person importer, không thay ownership person_import_etl.py. T357 tham khảo run manifest/idempotency của T253; không triển khai hoặc chạy person-import trong docs-phase. Scoped inverse/CAS rollback phải giữ writes khác; full --restore-db chỉ sau writer quiescence và scope approval riêng, không mặc định phục hồi DB sống/WAL.
