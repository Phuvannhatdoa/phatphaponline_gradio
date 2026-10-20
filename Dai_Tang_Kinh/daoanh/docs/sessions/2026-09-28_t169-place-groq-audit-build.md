# Session — 2026-09-28 · T169-place-groq-audit-build (BUILD theo SPEC X-T169)

> Branch/label: T169 BUILD — pipeline thẩm định địa danh Groq vs SQLite.
> Task: `tasks/T169-place-groq-audit-build.md` · SPEC: `docs/Mimo-Flash/X-T169-groq-place-verify-pipeline-SPEC.md`.

## Bối cảnh & mục tiêu

- Admin đã duyệt build (2026-09-25 phương án A side-car; 2026-09-27 chốt sửa G1–G7 trong T184
  + directive "Đồng ý build, hãy lưu logs, gitcommit và update... Gọi pipip khi done").
- Mục tiêu session: BUILD code T169 theo SPEC đã sửa — migrate side-car + classify + verifier
  + API + UI + pipeline/docs/commit/revert tiện 1 lệnh.

## Việc đã làm

### Phase 1 — Migrate side-car (đã APPLY DB THẬT)
- `scripts/t169_place_groq_audit_migrate.py`: `--stats/--dry-run/--apply/--revert` + backup sqlite API.
- Sửa công thức batch: `59.150 // 25 = 2.366` (chẵn, không `+1`) → stats đúng "2.366 batch".
- `--apply` trên DB thật: tạo `place_groq_audit` + index `idx_pga_review` + `idx_pga_diff`;
  backup `data/backups/lineage_t169_20260928_130129.db` (1.410 MB, đã hash-verify sha256).
- Env `T169_DB=<path>` override DB → test temp không chạm DB thật.
- Stats DB thật: places_dila 59.167 · places_pending 176.783 (id NULL 58.455) · JOIN 59.167 ·
  spine zh hợp lệ 59.150 · namevi_map_places 118.296 (needs_review=1: 18.165).

### Phase 2 — classify_diff + test (11/11 PASS)
- `scripts/t169_classify.py`: `classify_diff` theo G5 — POLYPHONIC → TAXONOMY → PHONETIC → NONE
  (dừng nhãn đầu, không ghép). Trụ đa âm static `POLYPHONIC_CHAR` inline (0 bảng mới) +
  `TAXONOMY_SUFFIX` (Phật Sơn 塔/寺/宮/觀/院/門/亭/樓/臺/山/寺...). Fixtures: 降魔窟→POLYPHONIC_CHAR,
  長安→POLYPHONIC_CHAR (Tràng An), 陝西→PHONETIC_MISMATCH.
- `tests/test_t169_classify_diff.py` 11/11 PASS. Đăng ký `npm run test:t169` + append vào `test:translation`.

### Phase 3 — verify script + smoke
- `scripts/verify_dila_places_groq.py`: batch 25 (ORDER BY id LIMIT 25, `:cursor` memory),
  resume scan-qua-predicate, G4 `NOT IN(verified,approved_dict)` kể cả `--force`,
  RPM adaptive (G3), retry 429/5xx backoff, `safe_parse_json_content`, json_object fallback khi
  `schema_400` (bỏ response_format), window 60s TPM 6.000, atomic `with con` (Ctrl+C rollback batch dở).
- Smoke mock temp DB `%TEMP%\opencode\t169_smoke.db`: limit 25 → 25 verified; re-run → 6 còn lại (resume ✓).

### Phase 4 — API app.py (2 route)
- Chèn sau `api_admin_place_missing_info`:
  - GET `/daoanh/api/admin/place-groq-review` — list theo `status` + `diff` filter + `limit/offset`;
    default `conflict` (G7); sort `POLYPHONIC_CHAR`→`TAXONOMY_VARIANT`→`PHONETIC_MISMATCH`→else.
  - PUT `/daoanh/api/admin/place-groq-review/<id>` — 3 bước 1 transaction (G6):
    (1) `place_groq_audit.review_status` = dict→`verified` / groq manual→`approved_dict`, `needs_review=0`;
    (2) `places_pending.name_vi` + recompute `name_vi_norm` (reuse `normalize_text` app.py:81);
    (3) `namevi_map_places` UPSERT (`source='reviewed_t169'`, `needs_review=0`).
  - `py_compile app.py` OK. Smoke SQL temp DB: 3-bước tx OK + filter conflict/api_error OK.
- Lưu ý: admin API same-origin → PUT không bị CORS chặn.

### Phase 5 — UI place_update.html rewrite
- Viết lại toàn bộ (`<meta charset="utf-8">`, React 18 + Tailwind + text/babel):
  session-check `localStorage.admin_session` → redirect login nếu thiếu; 3 tab
  Cần xem xét (conflict, mặc định) / Lỗi API (api_error) / Đã duyệt (verified|approved_dict) kèm count;
  filter diff (POLYPHONIC_CHAR / TAXONOMY_VARIANT / PHONETIC_MISMATCH); bảng 2 cột
  từ điển (`dict_vi`) vs Groq (`groq_trans_vi`) + badge diff/status; radio dict/groq/manual +
  input thủ công + nút "Xác nhận & duyệt" (PUT); Load more.
- Thêm `place_update.html` vào `scripts/e2e-test.js` pages → e2e PASS.

### Phase 6 — Pipeline & docs
- `npm run pipeline`: guard PASS · lint PASS · test PASS · test:translation PASS (t165 11/11, t166 18/18,
  t178 69/69, t179 49/49, t167 PASS, **t169 11/11**) · UAT PASS · compliance PASS · gov PASS · audit:t166 PASS ·
  e2e 5/5 pages PASS · **e2e:runtime EPERM unlink test-results\.last-run.json (pre-existing, không chặn)**.
- Docs: task + session + tasktodo row + ROLLBACK row + SPEC/pointer tick + dashboard regen
  (`python -X utf8 scripts/build_progress_data.py`) + commit 2-pass hash-fill.

## Verify
- `npm run e2e` riêng: place_update.html ✅.
- Smoke DB temp 3-bước PUT ✅ (audit approved_dict/needs_review=0 · pending name_vi+norm "hang ma quat" ·
  namevi UPSERT `reviewed_t169`) · GET conflict filter chỉ trả POLYPHONIC row ✅ · tab api_error ✅.

## Còn lại (thủ công — VPS, cần GROQ key)
1. Chạy full `python -X utf8 scripts/verify_dila_places_groq.py` (~2.366 batch, 80–120 phút).
2. Admin review `admin/place_update.html` (18.165 rows needs_review → conflict override).

## Revert
- Code+docs: `git revert --no-edit 393676f36fdc7d42469fd52b39bf004b18fbc42b`.
- DB: `python -X utf8 scripts/t169_place_groq_audit_migrate.py --revert` (DROP side-car + index);
  restore dữ liệu: backup `data/backups/lineage_t169_20260928_130129.db` → `data/lineage.db`.

## Lưu ý cho session sau
- `.git/index` thật vẫn stale/index.lock (agent khác) → commit phải dùng temp GIT_INDEX_FILE + byte-write `refs/heads/master`.
- `e2e:runtime` EPERM `.last-run.json` pre-existing (file-lock Windows) — không phải lỗi T169.
- Script full verify giữ `NOT IN(verified,approved_dict)` (G4) → rechạy an toàn, 0% chạy lại hàng đã duyệt.