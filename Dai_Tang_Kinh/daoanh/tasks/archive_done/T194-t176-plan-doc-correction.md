---
id: T194
title: "T176 (rev2 của T175) plan-doc correction + sync X-T174 — sửa 4 fact sai, chỉ đích A/B/C thật, 12 line-ref stale"
module: Docs / Plan Review
priority: high
status: done
owner: claudecode
depends_on: [T193, T176, T174]
created: 2026-09-29
updated: 2026-09-29
designed_by: claudecode
handoff_to: Claude Code Agent (đã xong — docs-only, 0 code/0 DB)
plan_approved_at: "2026-09-29 (Admin duyệt scope: sửa T176 + sync X-T174, GIỮ T175 nguyên)"
done_when: |
  T176 §3 tự chứa 100% (không mục rỗng) · 4 fact sai đã sửa · chỉ đích A/B/C
  = person_display_names (đã build) thay vì person_name_alias (chưa build)
  · X-T174 đồng bộ (place ĐÃ có post-check, 6 call site) · 0 code/0 DB/0 migration
  · guard/lint/test PASS · 2-pass revertible.
---

# T194 — Sửa T176 (Phase0C rev2) + đồng bộ X-T174

> **Bối cảnh:** Admin review `T175-phase0c-canonical-person-identity-audit.md`.
> Verify phát hiện **T176 chính là rev2 của T175** và tại L22 ghi:
> _"T175 (v1) **giữ nguyên, không sửa**"_ → scope đổi sang **T176 + X-T174**.

## 0. Vì sao không sửa T175

| Bằng chứng | Nội dung |
|---|---|
| `T176…md:22` | "T175 (v1, commit `dbb77ef`) **giữ nguyên, không sửa**" |
| `T176…md:24` | "T176 §3 **thay cho** T175 §3 khi Admin chạy audit" |
| `git log dbb77ef` | `fatal: ambiguous argument` → **commit tham chiếu không tồn tại** |

→ T176 là prompt **thực sự sẽ paste**. Sửa T175 là sửa tài liệu chết.

## 1. Verdict T175 (đã verify, dùng làm input cho T194)

**~50% đúng — 5 P0 + 9 P1.** 5 P0: (1) §11 `RULES A–J` **rỗng**, directive gốc `T158-PHASE0C` không có trong repo → các mục "giữ nguyên nguyên văn" (§3/§5/§7/§8/§12/§13/§15) trỏ vào directive không tồn tại; (2) `person_name_alias` không có trong DB; (3) priority namevimap đảo sai; (4) route "place note 17958" bịa; (5) mâu thuẫn với T174 về post-check.

## 2. T176 — 4 fact sai + 12 line-ref stale + 1 P0 mới

### 2.1 Fact sai (đã verify bằng SQL/code)

| # | Claim T176 | Thật | Hậu quả |
|---|---|---|---|
| F1 | L224 `name_vi_map` A001984 có row `conf 0.7` | **0 row** (41.508 row conf=0.7 nhưng A001984 không có row nào) | Agent sẽ tìm 1 bản ghi không tồn tại → báo sai |
| F2 | L55 `translation_cache` 1.761 row | **1.870** (T174 ghi 1.867 — cũng stale) | Số đếm sai |
| F3 | L92 `marcus_reference` theo `lookup_id` | Cột khóa thật = **`node_id`** (`app.py:2694`, `5349`) | Agent query sai cột |
| F4 | L41/L304 `_glossary_resolver` ~app.py:16330 | **17457** | Trỏ sai hàm |

### 2.2 Line-ref stale → đã refresh

| Claim | Cũ | Thật (2026-09-29) |
|---|---|---|
| `translate_hvdic` | 13246 | **14310** |
| `/api/translate/google` | 13269 | **14332** (`def` 14333) |
| `translate_all` | 13289 | **14353** |
| `admin_namevi_translate_local` | 15011 | **16075** |
| search `n.name_vi LIKE` | ~3811 | **3962** |
| TTL runtime đọc file `{lookup_id}.ttl` "5 vị trí 11359/11380/12387/12496/12520" | 5 vị trí | `app.py` **0 chỗ** `open(...*.ttl)` literal; thật là `master_ttl_path = TTL_MASTER_DIR/f"TS-{dila_id}.ttl"` (**12361**, **12407**) + vòng rebuild `TTL_OLD_DIR` (**13815/13817**, admin) |

### 2.3 P0 mới — chỉ đích A/B/C sai (giống T175 P0-2 nhưng T176 cũng dính)

- T176 §12b L621 nói "T171 (alias/name chuẩn hóa) — minimal fix map vào đâu".
- `person_name_alias` = **bảng TARGET** trong SPEC T171 §3.2, **chưa migrate** → `no such table` (verified).
- Bảng **đã build** và đúng cấu trúc A/B/C là **`person_display_names`** (8 row):
  `authority_name_vi` (B) + `display_name_vi` (C) + `is_preferred` + `verification_status` + `source_type` (ttl/manual) + `appellation_vi` (thụy hiệu) + `source_predicate`/`source_ref` (evidence).
- Cộng `person_name_correction` (2.433 row) cho hàng chờ sửa.
- A001984: **0 row** ở cả hai → đúng ứng viên pilot.
- `people` (15 col) **không có** cột title/posthumous/alias → khẳng định của T176 L94 là đúng.

## 3. X-T174 — đồng bộ (lỗi do T193, phát hiện khi verify T176)

| # | Claim X-T174 | Thật |
|---|---|---|
| S1 | P1-8 (L69): "Route place_note **không** có post-LLM guard … place (**:18750**) không gọi" | **SAI** — `_t166_post_check_translation` có **6 call site**, place đã có |
| S2 | Route table L49–52 + L312–315 | person 17587→**17727** · dila 17977→**18117** · place 18750→**18890** |
| S3 | `_glossary_resolver` 17317 (L57, L72, L279) | **17457** |
| S4 | L278 "place :18750 có thể chưa gọi — xác minh" | đã xác minh → **có gọi** (18973) |

### 6 call site `_t166_post_check_translation` (đã map về route)

| route | `@app.route` | call site |
|---|---|---|
| `/daoanh/api/relation/translate` | 6524 | 6583 |
| `/daoanh/api/person/<person_id>/translate` | 17727 | 17780 |
| `/daoanh/api/person/<person_id>/dila_translate` | 18117 | 18320 |
| `/daoanh/api/admin/person/<person_id>/bio_vi` | 18366 | 18400 |
| `/daoanh/api/admin/person/<person_id>/dila_vi` | 18466 | 18523 |
| `/daoanh/api/place/<dila_id>/translate` | **18890** | **18973** |

## 4. Files

- Sửa: `docs/Mimo-Flash/T176-phase0c-rev2-canonical-person-identity-audit.md`
- Sửa: `docs/Mimo-Flash/X-T174-t158-phase0-reuse-first-canonical-guard.md`
- Task này: `tasks/T194-t176-plan-doc-correction.md`
- Session: `docs/sessions/2026-09-29_t194-t176-plan-doc-correction.md`
- **Không đụng**: `T175-phase0c-canonical-person-identity-audit.md` (giữ nguyên theo chốt Admin)

## 5. Revert

Docs-only: `git revert --no-edit b95d3008eef4a17527fe30c846e37cdd102288e1`. Không DB/cache/code.
