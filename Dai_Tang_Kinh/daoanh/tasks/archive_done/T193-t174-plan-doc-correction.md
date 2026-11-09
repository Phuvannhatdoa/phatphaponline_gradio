---
id: T193
title: "T174 plan-doc correction — thu hồi directive gốc (A…AH + report template) + sửa authority hierarchy + refresh toàn bộ line-ref/số đếm"
module: Docs / Mimo-Flash (plan-doc)
priority: high
status: done
owner: claudecode
depends_on: [T174]
created: 2026-09-29
updated: 2026-09-29
designed_by: claudecode
plan_approved_at: "2026-09-29 (Admin phê chuẩn đề xuất sau review độc lập T174: 'phê chuẩn đề xuất này')"
done_when: |
  docs/Mimo-Flash/T174-t158-phase0-reuse-first-canonical-guard.md đã sửa đủ 4 nhóm lỗi
  (thu hồi directive · authority hierarchy · refresh facts · 3 mục audit mới);
  prompt Phase 0 tự chứa (paste được, không cần file ngoài); docs-only 0 code/0 DB.
---

# T193 — T174 plan-doc correction

## 1. Vấn đề

Admin yêu cầu: *"check và xác nhận vấn đề sau đúng logic chưa, nếu chưa hãy chỉ ra và đề xuất giải pháp"*
cho `docs/Mimo-Flash/T174-t158-phase0-reuse-first-canonical-guard.md` (243 dòng, `status: ready-for-dev`).

Review độc lập trên source + DB thật (không tin doc): **verdict ~55–60% đúng về hướng thiết kế,
26 lỗi fact + 1 lỗi logic P0 + 1 blocker khiến Phase 0 không thể chạy.**

## 2. Kết quả verify (evidence)

| # | Loại | Mức | Bằng chứng |
|---|---|---|---|
| 1 | Prompt §3 **không tự chứa** | **P0 blocker** | Directive `T158-PHASE0-004` không tồn tại trong repo (chỉ là câu nhắc trong T174/T175). Danh sách 34 mục A…AH + mẫu report 18 mục **không có ở đâu** → agent không thể tạo report đúng mẫu ⇒ `done_when` không thể đạt |
| 2 | tier A predicate | **P0 logic** | `name_vi_final` khác NULL = **5.205** rows nhưng `approved_by` khác NULL chỉ **1** ⇒ 5.204 rows chưa duyệt. Implement literal sẽ HARD_FAIL oan — đúng lỗi P1-5 của doc cảnh báo phải tránh |
| 3 | tier B dead threshold | P0 logic | 41.508 rows có `name_vi_auto`, **0 rows** có `confidence ≥ 0.9` ⇒ ngưỡng 0.9 không phân biệt được gì |
| 4 | Ví dụ 少林寺 lọc sai cột | P1 | `places_dila(id='PL000000023255', name='少林寺', name_zh='少室寺')` → lọc `name_zh='少林寺'` ra 0 row, agent báo NOT FOUND oan |
| 5 | ID namespace lệch | P1 | `places_dila.id='PL000000023255'` vs `namevi_map_places.dila_id='PL023255'` |
| 6 | Thiếu tier cho PLACE | P1 | `namevi_map_places.vn_name_status` NULL 118.293/118.296 (`reviewed` chỉ 2) · `source`: auto_transliterate 118.259 / ttl_confirmed 31 / manual 5 ⇒ 少林寺 (ttl_confirmed 0.9) là tier B, **không phải tier A** |
| 7 | Chưa nói baseline assertion | P1 | `translation_cache.identity_status` NULL **1.867/1.867**; `translation_rules.identity_lock_policy` = `P-PARTIAL` **112/112** ⇒ guard đã wire nhưng chưa từng sinh dữ liệu |
| 8 | Coverage post-LLM | P1 | `post_check_translation` (T166) chỉ gọi ở app.py **:6583** (relation) · **:17640** (person) · **:18180** (dila). Route place_note (**:18750**) **không** gọi |
| 9 | Regression case bị bỏ | P2 | A009460: `people.name_vi='Đan Hà Thiên Nhiên'` vs `vnpa` verified `'Đơn Hà Thiên Nhiên'` → mâu thuẫn thật, LOCK phải thắng `people.name_vi` |
| 10-16 | Pointer NOT FOUND | P1 | `docs/sessions/2026-09-25_t174-phase0-audit-plan.md` ✗ · `T166-canonical-identity-guard-SPEC.md` → thật `X-T166-canonical-identity-guard-SPEC.md` (457 dòng, doc nói 586) · `T168-...-PLAN.md` → `X-T168-...-PLAN.md` (182) · `docs/sessions/2026-09-25_t165-build-phase0-1-2.md` ✗ (gần nhất `2026-09-25_t169-t165-engine-build.md`) · `style_constitution.py` ở **repo root** (738 dòng) không phải `scripts/` · `hanviet_normalization.load_glossary` thật `scripts/hanviet_normalization.py:227` |
| 17-26 | Line-ref sai (app.py thật 20.954 dòng) | P1 | `_t73_style_lock` 2660→**17301** · `_t73_build_style_prompt` 16633→**17432** · `_glossary_resolver` ~16330→**17317** · person translate 16792→**17587** · dila_translate 17145→**17977** · place 17958→**18750** · relation 6343→**6524** · `style_lock` 214→**234** · `build_style_prompt` 288→**552** · `finalize_lock` 145→**KHÔNG TỒN TẠI** (0 hit) · `data/ttl` 1.046→**1.092** · `ontology/monks` 7 + `ontology/ttl` 1 → **`data/ontology` không tồn tại** |
| 27-28 | Số đếm sai | P1 | `translation_cache` 1.761→**1.867** · `translation_rules` 97 (96/1)→**112 (111/1)** · source_type dila_translate "(dila bio)"→ thật **`dila_card`** |
| 29 | Rủi ro bỏ sót | P2 | Duplicate resolver chưa nêu: `app.py:17317 _glossary_resolver` vs `style_constitution.py:348 glossary_resolver` (2 impl, shape khác) |
| 30 | Phase order | P2 | T175 (`depends_on:[T174]`) + T176 đã tồn tại, T177 `done`, T165-P8.1 commit `82d595f` ⇒ nguy cơ build trùng |

## 3. Giải pháp đã thực hiện (4 nhóm, docs-only)

| Nhóm | Nội dung | Đích |
|---|---|---|
| **1. Thu hồi directive gốc** | Dựng đủ **34 mục A…AH** + **mẫu report 18 mục** ngay trong T174 §3/§4; xóa mọi câu "giữ nguyên directive gốc"; prompt §5 viết lại thành **paste-ready tự chứa** | Chặn blocker #1 |
| **2. Authority hierarchy** | tier A = `vnpa.status='verified'` **HOẶC** (`name_vi_final` khác NULL **VÀ** `approved_by` khác NULL) → **3 rows**; tier B = có `name_vi_auto` **VÀ** `name_vi_final IS NULL` (bỏ dead 0.9); thêm tier PLACE theo `namevi_map_places`; chốt **LOCK thắng `people.name_vi`**; thêm A009460 làm regression CONFLICT | #2 #3 #6 #9 |
| **3. Refresh facts** | 14 line-ref · 7 pointer (thêm `X-` prefix, tạo session log T174) · 4 số đếm · xóa `finalize_lock` · `data/ttl` 1.092 · xóa claim `ontology/*` · route table 4 route + source_type thật | #10-#28 |
| **4. 3 mục audit mới** | AD baseline `identity_status`/`identity_lock_policy` + coverage `post_check_translation` · AE resolver duplication (app.py vs style_constitution) · AF phase order T175/T176/T177 | #7 #8 #29 #30 |

## 4. Files

- Sửa: `docs/Mimo-Flash/T174-t158-phase0-reuse-first-canonical-guard.md` (243 → ~430 dòng)
- Mới: `tasks/T193-t174-plan-doc-correction.md` (file này)
- Mới: `docs/sessions/2026-09-29_t193-t174-plan-doc-correction.md`
- Sửa (qua commit): `docs/tasktodo.md` · `docs/ROLLBACK.md` · `data/progress_data.json`

## 5. Revert

```bash
git revert --no-edit 41fda9c46879ec32ebd3fe0cd4c84100c61b3324
```

Docs-only, 0 code, 0 DB, 0 migration — revert 1 lệnh, không cần restore backup.

## 6. Ghi chú

- `finalize_lock` trong doc cũ là **claim không có thật** (0 hit toàn repo) — đã xóa, thay bằng `post_check_translation` (style_constitution) là hàm assertion thật.
- Doc cũ tự mâu thuẫn: nói "giữ nguyên nguyên văn directive gốc" ở §3 nhưng lại viết lại nội dung đó. Đã bỏ hết tham chiếu ngoài.
- Directive gốc T158-PHASE0-004 **không thể phục hồi nguyên văn** (không có trong repo, không có git history truy được). A…AH + report template trong T193 là **bản dựng lại có căn cứ** từ §2 verified facts + các nhắc dẫn còn sót trong doc cũ — đánh dấu rõ `RECONSTRUCTED` để Admin đối chiếu nếu nhớ bản gốc.
