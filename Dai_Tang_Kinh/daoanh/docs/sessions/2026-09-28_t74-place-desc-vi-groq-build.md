# Session — 2026-09-28 · T74 BUILD (Place Desc VI — Groq)

Task: `tasks/T74-place-desc-vi-gemini-translate.md` (đổi premise Gemini → Groq)
Trạng thái: ✅ BUILD DONE (code + tests + docs; còn bước thủ công VPS chạy full 14.000 rows cần GROQ key)

## Bối cảnh

Sau commit T170 build (`66d758c`/`ebf4d2a`), user duyệt: `ok, hãy tiếp tục công việc của dự án bằng task khác`
→ chọn **T74 — Place Desc VI translate** (đang `status: pending` trong tasktodo).

## 1. Audit premise (trước khi build)

- `lexicon`: 166.278 entries, **0 entry source chứa 'DIA_DANH'** → premise T61 cũ (`tasks/T61-...` với frontmatter
  thật là `id: T66`) đã lỗi thời; **bỏ T61**, T74 là task đúng.
- `places_dila`: KHÔNG có cột `note_vi` (cols: id/name/name_zh/name_en/name_san/name_jpn/name_peo/name_other/
  location_xml/geo_lat/geo_long/place_key/district/note/note_category/listbibl/raw_xml/source_id).
- `place_desc_vi_draft`: **đã tồn tại** (do T66 tạo) — 14.000 rows, tất cả `desc_source='dila_note_zh'`,
  `admin_approved=0`, `desc_vi_draft` = bản gốc `places_dila.note` (chủ yếu Hán; vài row tiếng Anh,
  sample "Tháp Thụy" 塔瑞, "A Dục Vương Trụ" 阿育王柱). **Không row nào có tiếng Việt thật** → premise T74 đúng.
- Script cũ `batch_translate_places.py` dùng **Gemini key chết (T50: 403/404)** → không dùng.
- Chuẩn hoá: **Groq `qwen/qwen3.8-27b`** (như T165+) — tham chiếu `app.py` `_t73_call_gemini` (~17338),
  lazy `place_note` (~18640–18781, `source_type='place_note'` ghi `translation_cache`), `admin/translation_cache.html`.

## 2. Phase 2 — script `scripts/t74_groq_translate_places.py`

Rút từ skeleton hardened T169/T170 (`verify_dila_places_groq.py`):
- **batch 25 · `:cursor` (place_id TEXT) · RPM adaptive** (`x-ratelimit-remaining-requests` ≤5 → 3.0s, else 2.2s
  ~27 RPM < 30 free tier) · **retry 429/5xx/network backoff** · **atomic `with con`** (Ctrl+C giữ batch đã commit)
  · `--mock/--limit/--force/--stats/--samples/--dry-run` · env `T74_DB` override (test không đụng DB thật).
- **Resume = marker `desc_source='t74_groq'`** (không dùng detect-Hán — row tiếng Anh vẫn cần dịch).
- **`--force` = single-pass** (1 vòng duyệt, không cursor-loop): row vừa update vẫn khớp scope force
  → cursor-loop sẽ lặp vô hạn; test chứng minh.
- **Guard chất lượng**: `is_han()` (CJK \u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff); output còn Hán tự
  → `still_han`, **hủy bản dịch, giữ bản gốc**; `empty`/`too_long` tương tự.
- `normalize_vi()`: bỏ fence ```, bỏ nhãn `Dịch:`/`Bản dịch:` đầu, dồn khoảng trắng.
- **UPDATE guard**: `WHERE place_id=? AND desc_source IN ('dila_note_zh','t74_groq')` → không đè
  desc_source lạ (`other` → 0 row affected).
- Không schema change: ghi `desc_vi_draft`=VI + `desc_source='t74_groq'` + `char_count` + `updated_at`;
  bản gốc phục hồi = `places_dila.note` (JOIN place_id=id).

## 3. Phase 3 — test `tests/test_t74_groq_translate_places.py` (red-team, mock, DB temp)

**18 PASS / 0 FAIL**: is_han · normalize (fence/nhãn/Hán → still_han/rỗng → empty) · prompt build ·
stats (total 5/pending 4/done 1) · mock limit=2 → t74_groq · resume → dịch nốt (English row) ·
run lại = 0 (skip) · `--force` single-pass · UPDATE guard 0-row · revert SQL khôi phục Hán + English gốc.

`package.json`: `test:t74` → chained vào `test:translation` (sau `test:t170`).

## 4. Smoke + pipeline

- `npm run test:t74` → 18/18 PASS.
- `npm run pipeline`: **guard PASS** (SSOT repo root OK) · lint/test/test:translation/test:uat/
  test:compliance/test:gov/audit:e2e đều PASS, **gồm cả `test:t74`** · `e2e:runtime` EPERM `.last-run.json`
  (pre-existing, không phải lỗi T74).

## 5. Phase docs

- Task `tasks/T74-place-desc-vi-gemini-translate.md`: frontmatter status `pending` → `done`, title Gemini→Groq,
  append 🚀 BUILD section (premise audit, script/CLI, tests, chạy full VPS 3 bước, ROLLBACK SQL +
  lưu ý `UPDATE ... FROM` không alias target).
- `docs/tasktodo.md`: entry BUILD DONE đầu file (kèm khôi phục 2 entry T170-verify/amend bị agent khác
  revert nhầm trong `7bd30ab`) + sửa entry ACTIVE `T74 ⏳ PENDING` → DONE pointer (hunk-granular,
  KHÔNG commit WIP tasktodo T185/T186/T187 của agent khác).
- `docs/ROLLBACK.md`: row T74 `d8ff1691` (phía trên T187).
- `docs/taskdone.md`: entry T74 DONE.
- `data/progress_data.json`: regen.

## 6. Git (2-pass temp-index, parent `7bd30ab`)

- Pass 1: commit code+tests+docs (hash-fill `d8ff1691` → pass-1 sha).
- Pass 2: hash-fill trong tasktodo/ROLLBACK/task/session.
- Byte-write refs `master`/`daoanh`/`origin/master`/`origin/HEAD` → pass-2 sha · guard PASS · BLOB==DISK.

## Revert

1. `git revert --no-edit d8ff1691` (code+tests+docs; pass-2 = `git revert --no-edit <sha_T74_p2>`)
2. DB revert (khôi phục bản gốc Hán/Eng):
   ```sql
   UPDATE place_desc_vi_draft
   SET desc_vi_draft=d.note, desc_source='dila_note_zh', updated_at=datetime('now')
   FROM places_dila d
   WHERE d.id=place_desc_vi_draft.place_id AND place_desc_vi_draft.desc_source='t74_groq';
   ```
   (SQLite `UPDATE ... FROM` KHÔNG cho alias target — không viết `UPDATE ... pd SET`.)