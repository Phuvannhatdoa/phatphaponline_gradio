# Session — T55b Related Texts API (Batch F, 2026-09-10)

## Bối cảnh
Đang chọn task unblocked tiếp theo sau T120 Phase A (DONE). T55 (Trích Dẫn Tự Động)
có deps `T36/T40/T42/T43` đa phần có sẵn + `cbeta_catalog_vn` (3,122) ·
`place_person_bibl` (13,933) · `place_person_bio_cache` (675,225) · `sat_crossref` (2,913) →
chọn build **T55b** (Recommendation API) trước T55a/T55c/T55d vì là delta rõ, read-only,
0 bảng mới, revert 1 lệnh.

## Khảo sát dữ liệu (read-only)
- `cbeta_catalog_vn` 3,122 rows · `sigla` **NULL hầu hết** — không dùng làm key.
- `sat_crossref.cbeta_sigla` = short key (`T0001`…`T2059`) → match EXACT short.
- `toh_cbeta_crossref.cbeta_sigla` = short key (`T0251`…) → match EXACT short.
- `pali_cbeta_map.sh` = 4-digit zero-padded (`0251`, `0235`) → format `{:04d}`.
- `cbeta_person_mentions.cbeta_text_sigla` = **full ref** (`T50n2059`, `T51n2076`,
  `X77n1524`) → match GLOB `series*n<num>` (verified: `T*n2076`→22,275 mentions/4,238
  persons, `X*n1524`→14,637/4,130; `T*n2059`→0 → honest NO_DATA).
- `cbeta_person_mentions` 72,628 rows verified; `people` có `name_vi`/`dynasty`.

## Bug giữa chừng (đã sửa trong phiên)
`_t55_normalize_sigla` được đổi sang trả `(short_key, text_num)` nhưng thân endpoint còn
dùng `key` như string → `(key,)` vào SQL + `key.replace(...)` sẽ Throw. Sửa: destructure
`s_key, s_num`, GLOB theo series, `pali_sh='{:04d}'.format(int(s_num))`, topic loại self
bằng `cbeta_text_sigla NOT GLOB ?` (bản chất: `T2076` short → source thật `T51n2076`
không bị `NOT LIKE base%` loại; GLOB mới đúng).

## Commit Build (BUILD-T55b)
- `Dai_Tang_Kinh/daoanh/app.py`: `_t55_normalize_sigla` (norm CBETA short) +
  `api_cbeta_related` (3 nhóm, HITL-safe, 0 ALTER, 0 bảng mới).
- Smoke test_client 5 case PASS:
  - `T50n2059` → SAT T2059 · persons/topic NO_DATA (thật: không có person mention)
  - `T2076` → SAT + 12 persons + 4 topic (X77n1524, T50n2061/2060/2062)
  - `T0251` → SAT+Toh+Pali (Bát Nhã Tâm Kinh) · persons/topic NO_DATA
  - `X77n1524` → persons 12 + topic 4 (self loại trừ ✓)
  - `NOPE999` → 3 nhóm NO_DATA trung thực

## Docs đồng bộ
- `tasks/T55-trich-dan-tu-dong.md`: status pending→in_progress, updated 2026-09-10,
  batch T55b implemented (checklist + smoke + revert hướng).
- `docs/tasktodo.md`: dòng T55 ⏳ IN_PROGRESS (T55b DONE, còn T55a/c/d).
- `docs/ROLLBACK.md`: row §1 (BUILD-T55b placeholder) + §2 revert docs.
- Session này.

## Rollback
```powershell
git revert --no-edit <commit-docs-T55b>   # docs (tasktodo/task/ROLLBACK/session)
git revert --no-edit <commit-build-T55b>  # app.py (0 DB → không cần §3)
```

## Next
- T55d panel UI "Gợi Ý Đọc" (places.html CBETA tab) — cần Lee test API trước.
- Các task unblocked khác vẫn mở: T118 đợt 3, dashboard items chờ Lee.