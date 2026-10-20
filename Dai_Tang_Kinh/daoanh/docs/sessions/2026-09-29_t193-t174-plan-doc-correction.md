# Session 2026-09-29 — T193 t174-plan-doc-correction

**Mode:** build · **Scope:** docs-only, 0 code / 0 DB / 0 migration
**Trigger:** Admin yêu cầu *"check và xác nhận vấn đề sau đúng logic chưa, nếu chưa hãy chỉ ra và đề xuất giải pháp"* cho `docs/Mimo-Flash/T174-t158-phase0-reuse-first-canonical-guard.md`, sau đó phê chuẩn đề xuất.

---

## 1. Review độc lập — verdict

**~55–60% đúng về hướng thiết kế; KHÔNG chạy được Phase 0 với bản doc cũ.**
26 lỗi fact + 1 lỗi logic P0 + 1 blocker.

## 2. Blocker — prompt §3 không tự chứa

Directive `T158-PHASE0-004` **không tồn tại trong repo**. Doc cũ tham chiếu nó 7 lần (§3, §7, §8, §11, §12, §13, §14, §16, §17, §18) nhưng không in nội dung:

| doc cũ nói | thực tế |
|---|---|
| `:137` "report exact A…AH" | danh sách 34 mục A…AH **không có ở đâu** (T175/T176 cũng không) |
| `:216-224` "18. REQUIRED REPORT (mẫu gốc + 2 mục mới)" | mẫu 18 mục **không tồn tại** (grep chỉ ra 3 hit, đều là câu nhắc) |
| `:185, :199, :212` "giữ nguyên nguyên văn directive gốc" | doc lại **viết lại** nội dung đó → tự mâu thuẫn |

⇒ Agent nhận prompt không thể tạo report đúng mẫu ⇒ `done_when` không thể đạt.

## 3. Lỗi logic P0

### 3.1 tier A predicate ≠ "admin approved"
Doc `:117-118`: tier A = `vn_person_authority.status='verified'` **HOẶC** `name_vi_map.name_vi_final (admin approved)`.

| điều kiện | rows |
|---|---|
| `name_vi_final` khác NULL | **5.205** |
| …`approved_by` khác NULL | **1** |
| …`approved_by` NULL (chưa duyệt) | **5.204** |

Implement literal ⇒ **HARD_FAIL oan 5.204 row** — đúng lỗi mà P1-5 của doc cảnh báo phải tránh.

### 3.2 tier B là dead threshold
Doc `:119` tier B = `auto_transliterate <0.9`. Thật: 41.508 row có `name_vi_auto`, **0 row** có `confidence ≥ 0.9` ⇒ ngưỡng không phân biệt được gì.

### 3.3 Thiếu tier cho PLACE
`namevi_map_places.vn_name_status` NULL 118.293/118.296 (`reviewed` chỉ **2**); `source`: auto_transliterate 118.259 / ttl_confirmed 31 / manual 5.
⇒ **少林寺 là tier B, không phải tier A** dù `confidence=0.9` + `ttl_confirmed`. Tên nghe "chắc" nhưng phải WARN. Case này bắt agent **không tự nâng tier**.

## 4. Ví dụ 少林寺 sẽ ra NOT FOUND oan

`places_dila(id='PL000000023255', name='少林寺', name_zh='少室寺')` — doc `:192` hướng dẫn lọc theo `name_zh` ⇒ ra 0 row.
Thêm: **2 ID namespace lệch nhau** — `places_dila.id='PL000000023255'` vs `namevi_map_places.dila_id='PL023255'`.

## 5. Baseline assertion chưa ai chạy (phát hiện mới)

- `translation_cache.identity_status` NULL **1.867/1.867**
- `translation_rules.identity_lock_policy` = `P-PARTIAL` **112/112**
- `post_check_translation` chỉ gọi ở app.py **:6583** (relation) · **:17640** (person) · **:18180** (dila). Route **place (`:18750`) không gọi**.
⇒ Guard đã wire nhưng chưa từng sinh dữ liệu. Code phase sẽ tưởng có sẵn để backfill.

## 6. 14 line-ref sai (app.py thật = 20.954 dòng)

`_t73_style_lock` 2660→**17301** · `_t73_build_style_prompt` 16633→**17432** · `_glossary_resolver` ~16330→**17317** · person 16792→**17587** · dila 17145→**17977** · place 17958→**18750** · relation 6343→**6524** · `style_lock` 214→**234** · `build_style_prompt` 288→**552** · `finalize_lock` 145→**KHÔNG TỒN TẠI** (0 hit) · `data/ttl` 1.046→**1.092** · `ontology/monks` 7 + `ontology/ttl` 1 → **`data/ontology` không tồn tại**.

## 7. 7 pointer NOT FOUND

`docs/sessions/2026-09-25_t174-phase0-audit-plan.md` ✗ · `T166-canonical-identity-guard-SPEC.md` → `X-T166-...` (**457** dòng, doc nói 586) · `T168-...-PLAN.md` → `X-T168-...` (182) · `docs/sessions/2026-09-25_t165-build-phase0-1-2.md` ✗ (gần nhất `2026-09-25_t169-t165-engine-build.md`) · `style_constitution.py` ở **repo root** (738 dòng) · `hanviet_normalization.load_glossary` → `scripts/hanviet_normalization.py:227`.

## 8. Số đếm sai

`translation_cache` 1.761→**1.867** · `translation_rules` 97 (96/1)→**112 (111/1)** · source_type dila_translate "(dila bio)" → thật **`dila_card`**.
Đúng: jobs 3 · items 12 · glossary_vi 248.095 · lexicon 166.278 · people 48.673 · places_dila 59.167 · namevi_map_places 118.296.

## 9. Regression case bị bỏ

A009460: `people.name_vi='Đan Hà Thiên Nhiên'` vs `vnpa` verified `'Đơn Hà Thiên Nhiên'` → mâu thuẫn thật. Doc chỉ nói A009460 là LOCK example, chưa nói **tier A phải thắng `people.name_vi`**.

## 10. Rủi ro build trùng

T175 (`depends_on:[T174]`) + T176 `ready-for-dev`, T177 `done`, T165-P8.1 commit `82d595f`.

---

## 11. Đã thực hiện (4 nhóm)

| Nhóm | Nội dung |
|---|---|
| **1. Thu hồi directive** | Dựng **34 mục A…AH** + **mẫu report 18 mục** ngay trong prompt §4; xóa mọi tham chiếu "giữ nguyên directive gốc"; prompt viết lại thành **paste-ready tự chứa** |
| **2. Authority hierarchy** | tier A có `approved_by` (→ 3 rows) · tier B theo vắng mặt `name_vi_final` (bỏ dead 0.9) · thêm **§2.2 tier PLACE** · chốt LOCK thắng `people.name_vi` · 3 regression case kèm số liệu thật |
| **3. Refresh facts** | 14 line-ref · 7 pointer · 4 số đếm · xóa `finalize_lock` → thay bằng `post_check_translation` · `data/ttl` 1.092 · xóa claim `ontology/*` · route table 4 route + source_type thật |
| **4. 3 mục audit mới** | **AD** identity baseline + coverage `post_check_translation` · **AE** resolver duplication (app.py:17317 vs style_constitution.py:348) · **AF** phase order T175/T176/T177 |

## 12. Files

- Sửa: `docs/Mimo-Flash/T174-t158-phase0-reuse-first-canonical-guard.md` (243 → ~380 dòng)
- Mới: `tasks/T193-t174-plan-doc-correction.md`
- Mới: session file này
- Sửa qua commit: `docs/tasktodo.md` · `docs/ROLLBACK.md` · `data/progress_data.json`

## 13. Hạn chế trung thực

Directive gốc **không thể phục hồi nguyên văn** (không trong repo, không truy được git history). A…AH + report template là **bản dựng lại có căn cứ** từ §2 verified facts của doc cũ + các nhắc dẫn còn sót + verify lại ngày 2026-09-29. Đã đánh dấu **RECONSTRUCTED** ngay trong doc T174 §3. Nếu Admin nhớ bản gốc khác → sửa **trước khi paste prompt**.

## 14. Revert

```bash
git revert --no-edit 41fda9c46879ec32ebd3fe0cd4c84100c61b3324
```

Docs-only, 0 code, 0 DB → revert 1 lệnh, không cần restore backup.

## 15. Còn nợ acceptance

- Paste prompt §4 cho Claude Code → Phase 0 report 18 mục (chưa chạy)
- Đọc mục 18 (AF phase order) trước khi quyết định `APPROVED FIX`, tránh build trùng T175/T176
- Bắt đầu từ mục **AD**: nếu `identity_status` vẫn NULL sau khi code phase chạy thì guard chưa thực sự hoạt động
