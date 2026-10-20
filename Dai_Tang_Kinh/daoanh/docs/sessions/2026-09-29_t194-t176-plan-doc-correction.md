# T194 — T176 (Phase0C rev2) plan-doc correction + sync X-T174

**Ngày:** 2026-09-29 · **Agent:** claudecode · **Mode:** docs-only (0 code / 0 DB / 0 migration)

## 0. Yêu cầu của Admin

> "check và xác nhận vấn đề sau đúng logic chưa, nếu chưa hãy chỉ ra và đề xuất giải phích:
> `T175-phase0c-canonical-person-identity-audit.md`"

## 1. Verdict T175 — ~50% đúng, 5 P0 + 9 P1

### 5 P0
1. **§11 `RULES A–J` RỖNG** — directive gốc `T158-PHASE0C` không có trong repo
   (grep 0 hit) → các mục "giữ nguyên nguyên văn" (§3/§5/§7/§8/§12/§13/§15)
   trỏ vào tài liệu không tồn tại. Prompt **không tự chứa, không paste-ready**.
2. **`person_name_alias` không có trong DB** → "minimal fix PHẢI map vào đây,
   không bảng mới" tự mâu thuẫn với §13.
3. **Priority namevimap đảo sai** — doc: `final > people.name_vi > auto`;
   code thật `name_vi_final or name_vi_auto or name_vi`.
4. **Route "place note (17958)" bịa** — dòng đó là `_save_suggested_rules()`.
5. **Mâu thuẫn T174 về post-check** (dẫn tới phát hiện S1 bên dưới).

### 9 P1 (rút gọn)
`finalize_lock` không tồn tại · `_glossary_resolver` sai dòng · `public_transliterate`
sai dòng (hvdic gọi 4 chỗ) · "3 người auto 0.7" chỉ đúng 1/3 · "51 dup" → 52 ·
`name_vi` mismatch 5.557 (17× số 322) · A001984 0 row name_vi_map · evidence
`dynasty/sect` không phân giải được (3 ứng viên giống hệt) · §8 variants 0 row ·
session `2026-09-25_t175-…` không tồn tại.

## 2. Phát hiện quyết định — scope đổi

Trong lúc verify, phát hiện **`T176-phase0c-rev2-canonical-person-identity-audit.md`
chính là rev2 của T175**, và tại L22 ghi:

> "T175 (v1) **giữ nguyên, không sửa**" · T176 §3 **thay cho** T175 §3 khi chạy audit

→ Sửa T175 là sửa tài liệu chết. Đã **dừng** và hỏi lại Admin; Admin chốt:
**"Sửa T176 + sync X-T174, giữ T175 nguyên"**.

Ngoài ra: commit `dbb77ef` mà T176 trích **không tồn tại** (`git log` → fatal).

## 3. T176 — 4 fact sai + 6 line-ref stale + 1 P0 mới

| # | Claim | Thật |
|---|---|---|
| F1 | `name_vi_map` A001984 có row `conf 0.7` (L224) | **0 row**. 41.508 row conf=0.7 nhưng A001984 không có |
| F2 | `translation_cache` 1.761 row | **1.870** |
| F3 | `marcus_reference` theo `lookup_id` | cột khóa = **`node_id`** |
| F4 | `_glossary_resolver` ~16330 (L41, L304) | **17457** |
| S6 | TTL runtime đọc `{lookup_id}.ttl` 5 vị trí | `master_ttl_path` **12361/12407**; `TTL_OLD_DIR` 13815 = admin rebuild |
| P0 | §12b L621 "minimal fix map vào T171" | T171 = `person_name_alias` **chưa migrate** |

Line-ref refresh: `translate_hvdic` 13246→**14310** · `/api/translate/google`
13269→**14332** · `translate_all` 13289→**14353** · `admin_namevi_translate_local`
15011→**16075** · `n.name_vi LIKE` 3811→**3962**.

**Chỉ đích A/B/C thật** (thay cho `person_name_alias`): `person_display_names`
— 8 row, đã build, có `authority_name_vi` (B) + `display_name_vi` (C) +
`is_preferred` + `verification_status` + `appellation_vi` + `source_predicate`.
Cộng `person_name_correction` 2.433 row. A001984 = 0 row ở cả hai → pilot sạch.

**Hazard mới ghi thêm vào §5**: row A021462 có `name_vi_final` +
`confidence=1.0` nhưng `approved_by=NULL` và `name_zh` sai (香嚴智閑 vs
people 鏡堂覺圓) → rơi vào khoảng trống phân tầng (không tier A, không tier B).

## 4. X-T174 — 4 lỗi đồng bộ

- **S1 (P1-8)**: "place_note không có post-LLM guard" → **SAI**. Đã map đủ
  **6 call site** `_t166_post_check_translation`, gồm place (18890/18973).
  Nguồn gốc: T193 verify lúc app.py còn 3 call site; agent khác đã thêm
  2 route admin-person + 1 place trong lúc T193 chạy.
- **S2**: route table person 17587→**17727** · dila 17977→**18117** · place 18750→**18890** (2 bảng trong doc).
- **S3**: `_glossary_resolver` 17317→**17457** (3 chỗ).
- **S4**: mục AD trong prompt viết "place có thể chưa gọi — xác minh" → đã
  xác minh, có gọi.

Tên file T174 cũng đã bị agent khác đổi `T174-…` → `X-T174-…` (rename đang
staged-partial, chưa commit) — không đụng vào.

## 5. Files

| File | Việc |
|---|---|
| `docs/Mimo-Flash/T176-phase0c-rev2-…md` | sửa 4 fact + 6 line-ref + P0 chỉ đích A/B/C + hazard A021462 + header ghi chú T194 |
| `docs/Mimo-Flash/X-T174-t158-phase0-reuse-first-…md` | sửa P1-8 + route table ×2 + `_glossary_resolver` ×3 + mục AD |
| `tasks/T194-t176-plan-doc-correction.md` | task |
| `docs/sessions/2026-09-29_t194-t176-plan-doc-correction.md` | file này |
| `docs/tasktodo.md` · `docs/ROLLBACK.md` · `data/progress_data.json` | dashboard |
| `docs/Mimo-Flash/T175-…md` | **KHÔNG đụng** (giữ theo chốt Admin) |

## 6. Bài học rút ra

1. **app.py đang bị nhiều agent sửa song song** → line-ref trong doc **th decay
   rất nhanh** (trong 1 phiên T193: person 17587→17727, place 18750→18890,
   `_glossary_resolver` 17317→17457, hvdic 10861→11760). Doc nên ghi
   **tên hàm + route làm key chính**, line-ref chỉ là gợi ý, luôn kèm
   "verify lại lúc chạy".
2. **Doc trỏ tới schema chưa migrate là lỗi P0** — `person_name_alias` (T171),
   `finalize_lock` (T165/T168). Phải verify `sqlite_master` trước khi trích.
3. **Số đếm cũng decay**: `translation_cache` 1761 → 1867 → 1870 trong 4 ngày.
4. **"Giữ nguyên nguyên văn" trong doc mà directive gốc không tồn tại** = prompt
   không paste-ready (T175 §11 RULES A–J rỗng). T176 đã tránh lỗi này — §3
   liệt kê đủ 19 mục.

## 7. Commit

2-pass revertible: pass-1 placeholder → pass-2 hash-fill.
`git revert --no-edit b95d3008eef4a17527fe30c846e37cdd102288e1`.
