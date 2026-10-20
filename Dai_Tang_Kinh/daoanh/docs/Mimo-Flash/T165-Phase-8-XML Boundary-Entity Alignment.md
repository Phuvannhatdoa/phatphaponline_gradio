---
id: T165-PHASE8-SPIKE
title: "T165 Phase 8 — XML Boundary / Source-Output Entity Alignment — Architecture Spike"
module: Editorial / LLM Translation / Identity
priority: high
status: spike-complete
owner: claudecode
depends_on: [T165, T166, T177]
created: 2026-09-27
spec_path: docs/Mimo-Flash/X-T165-rules-constrained-translation-engine-SPEC.md
related: docs/Mimo-Flash/X-T166-canonical-identity-guard-SPEC.md
note: |
  ARCHITECTURE SPIKE ONLY. Không có production code, DB schema, migration,
  cache rewrite, hay commit nào phát sinh từ tài liệu này. Không chọn winner
  giữa Option 1/2/3 — Admin quyết định trước khi mở task implement.
---

# T165 Phase 8 — XML Boundary / Entity Alignment — Architecture Spike

## 1. Current architecture (audit thật, không giả định)

Luồng dữ liệu thật hiện nay, xác nhận bằng code (không suy đoán):

```
SOURCE HAN (source_text)
    │
    ▼
build_canonical_lock(conn, source_text)     canonical_lock.py:1042
    │  → list[CanonicalLockEntry] (source_form, entity_type, canonical_value, status...)
    ▼
style_lock(conn, source_text, ...)          style_constitution.py §4
    │  → rules + glossary + exemplar + t166_lock_fingerprint → constitution_hash
    ▼
_t73_build_style_prompt(...)                app.py:16569
    │  → prompt string (rule text + glossary + lock section T166 + source_text)
    ▼
_t73_call_gemini(prompt, ...)               app.py:16583
    │  → call_llm_fn(prompt: str) -> str   (Groq qwen/qwen3.8-27b)
    ▼
output: PLAIN VI STRING                      (không span, không entity marker, không JSON)
    │
    ▼
_t166_post_check_translation(...)           canonical_lock.py:post_check_translation (app.py 4 call sites:
    │                                         6421 / 16778 / 17318 / 17895 = person_bio, dila_card,
    │                                         place_note, relation_evidence — mirror admin/app.py không
    │                                         tồn tại, chỉ 1 app.py thật)
    │  → post_assert(lock, output) dùng _extract_personlike_vi(output) (PERSON-only render detector)
    ▼
write_cache(..., identity_status, identity_issues, identity_lock_hash)   style_constitution.py:608
    │  → translation_cache.translated_text = PLAIN STRING (cột TEXT, không cấu trúc)
    ▼
CACHE (translation_cache)
```

**Batch flow** (`scripts/cbeta_translate_worker.py`): cùng contract `call_llm_fn(str)->str`, T166 wiring
là `needs_review + validation_report`, KHÔNG throw exception (SPEC §17 coverage ②) — cùng root gap.

### Gap chính xác cần thay đổi để có entity alignment

```
SOURCE ENTITY  (đã có: CanonicalLockEntry.source_form + entity_type + canonical_id)
    ↓
TRANSLATED ENTITY   ← KHÔNG TỒN TẠI — output chỉ là str, không có structure nào giữ
    ↓                  vị trí/entity nào trong output ứng với entity nào trong source
ENTITY/SPAN ASSERTION ← post_assert() hiện suy luận gián tiếp qua _extract_personlike_vi
    ↓                    (chỉ hoạt động cho PERSON nhờ honorific-anchor ngôn ngữ, không
    ↓                    tổng quát hoá được cho PLACE/DHARMA_NAME/TEMPLE)
T166
```

**Điểm chính xác cần đổi:** giữa bước `_t73_call_gemini` (nhận `prompt`, trả `str`) và
`_t166_post_check_translation` (nhận `output: str`) — đây là **1 điểm duy nhất** trong toàn bộ
pipeline nơi contract `str -> str` cần mở rộng thành `str -> (text, entity_evidence)`.

## 2. Root architectural gap

`call_llm_fn: callable(prompt: str) -> str` — không có cơ chế nào (JSON/XML/sidecar) để LLM trả về
bằng chứng entity-level. `constitution_hash` (style_constitution.py:168-199) được tính **TRƯỚC khi
gọi LLM**, dựa hoàn toàn vào lock/rules/glossary — **không phụ thuộc output** — nên về nguyên tắc
đổi output-contract không tự động đổi `constitution_hash`, TRỪ KHI ta chủ động thêm 1 phần tử hash
mới (giống cách `json_mode` đã là 1 phần tử hash sẵn có: `parts.append(f"json:{bool(lock.get('json_mode'))}")`)
— đây là tiền lệ kỹ thuật đã tồn tại cho đúng loại thay đổi này.

## 3. Option 1 — JSON structured output

```json
{
  "text": "Ông đến Thiếu Lâm Tự.",
  "entities": [
    {"source": "少林寺", "target": "Thiếu Lâm Tự", "entity_type": "PLACE"}
  ]
}
```

| Tiêu chí | Đánh giá |
|---|---|
| Deterministic evidence | Có, nếu LLM tuân thủ contract — nhưng LLM compliance không đảm bảo 100% |
| Parser reliability | JSON parser chuẩn, ổn định; lỗi rõ ràng khi malformed (`json.JSONDecodeError`) |
| LLM compliance | Qwen hỗ trợ JSON mode (đã thấy `json_mode` param có sẵn trong `style_lock`) — khả thi kỹ thuật, nhưng model nhỏ (qwen3.8-27b) có tỷ lệ lỗi JSON cao hơn model lớn, đặc biệt với văn bản dài chứa dấu ngoặc/trích dẫn Hán-Việt |
| Malformed output | Phải có fallback (parse fail → REVIEW_REQUIRED, không HARD_FAIL vì không phải lỗi identity) |
| Token overhead | Thêm field name (`"source"`, `"target"`, `"entity_type"`) lặp lại mỗi entity → overhead tuyến tính theo số entity/câu; ước tính +15-30% token so với plain text (NOT MEASURED — cần benchmark thật) |
| Prompt complexity | Trung bình — cần ví dụ JSON mẫu trong prompt (few-shot) → tăng thêm prompt_tokens tĩnh |
| Source span preservation | Có nếu contract yêu cầu instruct rõ, nhưng JSON tự nó không giữ **vị trí ký tự** trong `text` — chỉ giữ cặp (source, target) không có offset |
| Target span preservation | Tương tự — không có offset trừ khi thêm field riêng |
| Multiple entities/passage | Hỗ trợ tự nhiên (array) |
| Nested entities | Không hỗ trợ tốt (JSON phẳng, entity lồng nhau cần cấu trúc cây — phức tạp thêm) |
| Repeated entity | Hỗ trợ (nhiều phần tử array cùng `source`) nhưng không phân biệt được instance nào ứng với vị trí nào trong `text` nếu không có offset |
| Alias | Cần thêm field hoặc để nguyên `target` là bất kỳ chuỗi LLM chọn — canonical check vẫn ở T166, không đổi |
| Cross-type collision | Không tự giải quyết — vẫn cần T166 xử lý như hiện tại (`_allowed_vi_by_source_form`) |
| Cache compatibility | **Phá vỡ tương thích** — `translated_text` hiện là plain string hiển thị trực tiếp cho UI; JSON cần tách `text` ra riêng trước khi hiển thị/hash |
| constitution_hash | Cần thêm 1 phần tử hash mới (`output_contract:json_v1`) theo đúng tiền lệ `json_mode` |
| Identity fingerprint | `t166_lock_fingerprint` không đổi — vẫn tính từ LOCK, độc lập contract |
| Backward compat | Cache cũ (plain string) đọc được nếu code phân biệt bằng version marker |
| Rollback | Có thể — giữ `translated_text` = `text` field, `entities` lưu cột phụ optional |
| DB impact | Cần cột mới (vd `entity_evidence JSON`, additive) |
| RAM | Không đáng kể (per-request, không phải toàn universe) |
| Performance | Parse JSON nhanh; rủi ro chính là retry khi malformed → tăng latency/429 risk (đã biết 429 xảy ra 3/5 theo T177 D7) |

## 4. Option 2 — XML boundary

```xml
<text>
Ông đến <entity type="PLACE" source="少林寺">Thiếu Lâm Tự</entity>.
</text>
```

| Tiêu chí | Đánh giá |
|---|---|
| Deterministic evidence | Có, nếu well-formed — **và giữ được vị trí trong dòng chảy văn bản tự nhiên hơn JSON** (text vẫn đọc được trực tiếp, span suy ra từ vị trí tag) |
| Parser reliability | Cần XML parser dung sai lỗi (LLM có thể sinh tag không đóng đúng, ký tự đặc biệt Hán-Việt trong attribute cần escape) — rủi ro parse cao hơn JSON nếu không escape đúng |
| LLM compliance | Model nhỏ thường sinh HTML-like tag dễ hơn JSON lồng nhau (quen thuộc từ training data web), nhưng dễ quên đóng tag trong đoạn dài |
| Malformed output | Cần fallback + có thể dùng regex khoan dung để tận dụng phần well-formed, bỏ phần lỗi — nhưng regex-based repair lại gần giống "heuristic đoán mò" đã bị cấm ở phạm vi T166; ở đây chỉ là parser-repair, không phải identity-authorization nên khác bản chất |
| Token overhead | Tag `<entity type="PLACE" source="少林寺">...</entity>` dài hơn JSON key ngắn — overhead cao nhất trong 3 option (NOT MEASURED) |
| Prompt complexity | Cần ví dụ mẫu tương tự Option 1 |
| Source span preservation | **Tốt nhất trong 3 option** — text liền mạch, span = vị trí ký tự trong chuỗi đã parse |
| Target span preservation | Tốt (nội dung giữa open/close tag) |
| Multiple entities | Hỗ trợ tự nhiên |
| Nested entities | Hỗ trợ được (XML vốn phân cấp) nhưng Buddhist text hiếm khi cần nested identity — over-engineering nếu chỉ để giải Case C |
| Repeated entity | Hỗ trợ — mỗi occurrence là 1 tag riêng, giữ đúng vị trí |
| Alias | Không tự giải quyết — vẫn T166 xử lý |
| Cross-type collision | Không tự giải quyết |
| Cache compatibility | Cần tách `<text>` nội dung hiển thị khỏi `translated_text` lưu cache — tương tự Option 1 |
| constitution_hash | Cùng cơ chế thêm hash part mới |
| Identity fingerprint | Không đổi |
| Backward compat | Tương tự Option 1 |
| Rollback | Tương tự Option 1 |
| DB impact | Cột mới additive (lưu raw XML hoặc parsed entities) |
| RAM | Không đáng kể |
| Performance | Rủi ro malformed cao hơn JSON với model nhỏ — cần đo thật |

## 5. Option 3 — Sidecar alignment

Giữ `translated_text` plain string **y nguyên** (không đổi contract hiển thị/cache hiện tại),
LLM trả về **2 phần tách biệt trong 1 response** (hoặc 1 lời gọi phụ) chứa alignment metadata
(`source_span, target_span, source_entity_id, entity_type`) riêng khỏi văn bản dịch.

| Tiêu chí | Đánh giá |
|---|---|
| Deterministic evidence | Có, nếu sidecar chính xác khớp với text — nhưng đây là **điểm yếu nhất**: sidecar và text có thể lệch nhau (LLM sinh 2 phần không đồng bộ, không có ràng buộc cấu trúc buộc chúng khớp như tag-inline) |
| Parser reliability | Tùy hiện thực — nếu sidecar là JSON riêng thì parse dễ, nhưng **verify khớp với text** cần thêm bước (so `target_span` có đúng offset trong text không) |
| LLM compliance | Khó nhất — yêu cầu model tính offset ký tự chính xác trong 1 chuỗi UTF-8 có Hán+Việt hỗn hợp, model nhỏ rất dễ tính sai offset |
| Malformed output | Cần fallback mạnh nhất trong 3 option vì rủi ro lệch cao |
| Token overhead | Có thể thấp hơn Option 1/2 nếu chỉ cần offset (số) thay vì lặp lại chuỗi, NHƯNG bù lại cần 1 lời gọi/field riêng |
| Prompt complexity | Cao — cần giải thích khái niệm "offset" cho LLM, khó với model nhỏ |
| Source span | Có (field riêng) nhưng độ tin cậy offset thấp |
| Target span | Tương tự |
| Multiple entities | Hỗ trợ (array sidecar) |
| Nested/repeated entity | Hỗ trợ nhưng rủi ro offset trùng/lệch cao nhất |
| Cache compatibility | **Tốt nhất** — `translated_text` không đổi format, chỉ thêm cột sidecar riêng, hoàn toàn additive, không phá UI hiển thị hiện tại |
| constitution_hash | Cùng cơ chế thêm hash part |
| Backward compat | Tốt nhất trong 3 option (cache cũ không cần biến đổi gì) |
| Rollback | Dễ nhất — xóa cột sidecar, mọi thứ về nguyên trạng |
| DB impact | 1 cột JSON additive |
| RAM | Không đáng kể |
| Performance | Rủi ro accuracy (offset sai) cao hơn rủi ro parse-fail |

## 6. EntityAssertion — conceptual contract (KHÔNG chốt schema)

```
EntityAssertion {
    source_entity_id      # = CanonicalLockEntry.canonical_id đã có sẵn trong LOCK
    source_surface        # = CanonicalLockEntry.source_form (Hán) — đã có
    source_span           # MỚI — cần LLM hoặc alignment layer cung cấp
    target_surface         # = chuỗi VI LLM thực tế sinh ra tại vị trí đó
    target_span            # MỚI — cần LLM hoặc alignment layer cung cấp
    entity_type            # = CanonicalLockEntry.entity_type — đã có
    canonical_value         # = CanonicalLockEntry.canonical_value — đã có, KHÔNG lấy từ LLM
    authority_source        # = CanonicalLockEntry.authority_source — đã có
    alignment_method         # MỚI — 'json'|'xml'|'sidecar'|'none' (provenance của assertion)
    assertion_status          # MỚI — kết quả so sánh target_surface vs canonical_value
}
```

- **Bắt buộc** cho HARD_FAIL: `entity_type`, `canonical_value`, `target_surface`, `assertion_status`
  (đây là 4 field T166 cần để giữ đúng nguyên tắc "canonical authority không đến từ LLM" —
  `canonical_value`/`entity_type`/`canonical_id` LUÔN lấy từ `CanonicalLockEntry` có sẵn, KHÔNG BAO GIỜ
  từ field LLM trả về — LLM chỉ cung cấp `target_surface`/`target_span`, là **candidate**, không phải
  authority).
- **Optional**: `source_span`, `target_span`, `alignment_method` (dùng cho debug/audit, không bắt buộc
  cho logic PASS/FAIL).
- **Phải hash** (vào `constitution_hash` hoặc `identity_lock_hash`): `alignment_method` (vì đổi contract
  = đổi ý nghĩa cache, giống `json_mode` hiện tại).
- **Phải lưu cache**: `assertion_status`, `entity_type`, `target_surface` (để audit sau — additive cột
  mới, tương tự cách `identity_status`/`identity_issues` đã làm ở T166).
- **Chỉ runtime, không lưu**: `source_span`/`target_span` thô nếu chỉ dùng để tính `assertion_status`
  ngay lập tức (có thể bỏ sau khi tính xong, tránh phình cache).
- **Provenance** (audit trail, không quyết định logic): `alignment_method`.
- **Dùng cho HARD_FAIL**: `assertion_status == 'mismatch'` (target_surface không khớp canonical_value
  AND alignment xác nhận entity này thực sự được LLM chỉ định tương ứng source entity đó).
- **Chỉ REVIEW_REQUIRED**: `assertion_status == 'unaligned'` (LLM không cung cấp alignment cho entity
  này — không đủ evidence để HARD_FAIL, giữ đúng nguyên tắc R4 hiện tại của T166 SPEC).

**Nguyên tắc bất biến (không đổi dù chọn option nào):** `canonical_value`/`entity_type`/`canonical_id`
luôn đọc từ `build_canonical_lock()` (nguồn authority hiện có — vn_person_authority/namevi_map_places/
translation_glossary...). LLM **không bao giờ** là nguồn của các field này — LLM chỉ trả về
`target_surface`/`target_span`/`source_span` (ứng viên), đúng nguyên tắc "LLM ≠ authority" đã có
trong T166 SPEC R2/R5.

## 7. T166 integration boundary

`post_assert(lock, output)` hiện nhận `output: str`. Với alignment, chữ ký sẽ cần mở rộng thành
`post_assert(lock, output_text: str, entity_assertions: list[EntityAssertion] | None = None)` —
khi `entity_assertions` có giá trị, dùng nó thay cho `_extract_personlike_vi` (deterministic, entity-aware
cho MỌI entity_type, không chỉ PERSON); khi `None` (fallback plain-string, cache cũ hoặc LLM không tuân
contract), **giữ nguyên hành vi hiện tại** (person-only detection, PLACE/DHARMA_NAME vẫn WARN như bây giờ)
— đây là thiết kế fail-safe, không phải fail-open.

## 8. Cache/hash impact (CRITICAL — đã yêu cầu phân tích kỹ)

- `constitution_hash` **hiện KHÔNG phụ thuộc output** — chỉ phụ thuộc lock/rules/glossary/exemplar/
  format-version/label/json_mode/known_pending/t166_fingerprint (xác nhận đọc code thật, style_constitution.py:168-199).
- Nếu thêm `alignment_method` như 1 phần tử hash mới (theo đúng tiền lệ `json_mode`): **mọi cache hiện
  có sẽ MISS 1 lần** khi bật field mới cho bất kỳ source_type nào (vì phần tử hash mới xuất hiện lần đầu)
  — **giống cảnh báo mass-miss đã ghi sẵn trong T166 SPEC §9** ("Bật fingerprint = mass-miss ước tính
  toàn bộ cache 1.762 row miss 1 lần").
- Ước lượng cache miss %: **NOT MEASURED** — nhưng theo tiền lệ T166 fingerprint, đây là **100% miss
  1 lần cho source_type được bật**, không phải tỷ lệ phần trăm nhỏ. Khuyến nghị (không phải quyết định)
  bật theo `source_type` từng cái một (pilot ≤5) đúng cách T165 Phase 7 đã làm.
- Existing cache compatibility: `translated_text` (TEXT column) đọc được nguyên vẹn dù dùng option nào,
  vì mọi option đều additive (cột mới), KHÔNG đổi cột cũ.
- Migration: **có cần** (cột mới additive) nhưng đây là quyết định của task implement, KHÔNG chạy ở spike này.
- Dual-read/dual-write: **cần**, vì sẽ có giai đoạn chuyển tiếp (cache cũ = plain string, cache mới =
  plain string + alignment optional) — pattern giống hệt cách T166 đã dùng `_has_col()` guard cho
  identity_status (pre-migration graceful degrade).
- Rollback về plain-string cache: **có thể**, vì `translated_text` không đổi ý nghĩa trong mọi option
  (Option 3 rõ nhất; Option 1/2 cần tách `text`/`<text>` ra để giữ y hệt ý nghĩa cột cũ).

## 9. Token/cost impact

Baseline thật (T177 D7, đã đo, KHÔNG bịa): `prompt_tokens ≈ 3.422` (source 266 chars / prompt 10.092
chars / total 3.630), ngân sách chốt ~3.400–3.700, cấm hard-gate 150–250.

Benchmark plain vs JSON vs XML vs sidecar: **NOT MEASURED** (spike này không chạy LLM thật để giữ đúng
"no runtime change"). Đề xuất cách đo (chưa thực hiện):
```
for contract in [plain, json, xml, sidecar]:
    run 5 lần cùng source_text qua _t73_call_gemini với prompt biến thể tương ứng
    record: prompt_tokens, completion_tokens, total_tokens, latency, malformed_count, parse_success_rate
```
Không có số liệu nào trong mục này là đo thật — toàn bộ đánh dấu **NOT MEASURED**.

## 10. Failure-state matrix (semantics only, chưa code)

| # | Trạng thái | Đề xuất semantics |
|---|---|---|
| 1 | Valid aligned output | Dùng `assertion_status` để PASS/HARD_FAIL bình thường |
| 2 | Malformed XML | FALLBACK → xử lý như plain-string (person-only detection hiện tại) |
| 3 | Malformed JSON | FALLBACK → tương tự #2 |
| 4 | Missing entity marker (LOCKED entity không xuất hiện trong assertions) | REVIEW_REQUIRED (giống `LOCKED_NAME_NOT_RENDERED` hiện tại — không HARD vì thiếu bằng chứng không đồng nghĩa sai) |
| 5 | Unknown source entity (LLM tự bịa 1 entity không có trong LOCK) | REVIEW_REQUIRED — KHÔNG để LLM tạo entity mới ngoài LOCK (giữ nguyên tắc LLM≠authority) |
| 6 | Wrong entity_type (LLM gán sai loại so với LOCK) | HARD_FAIL nếu entity_type ảnh hưởng severity (giữ nguyên `_HARD_MISMATCH_TYPES`); nếu không rõ → REVIEW_REQUIRED |
| 7 | Target khác canonical | HARD_FAIL (đây chính là Case C2 cần giải quyết) |
| 8 | Multiple candidates cho cùng source_entity_id | REVIEW_REQUIRED (giống CONFLICT hiện tại — không auto-pick) |
| 9 | Repeated entity (nhiều occurrence hợp lệ) | PASS nếu MỌI occurrence khớp canonical; HARD_FAIL nếu BẤT KỲ occurrence sai |
| 10 | Overlapping spans | REVIEW_REQUIRED (parser ambiguity — không đoán) |
| 11 | Hallucinated entity marker (tag/field không tương ứng gì trong LOCK thật) | REVIEW_REQUIRED, log riêng để audit LLM compliance |
| 12 | Plain-text fallback (LLM bỏ qua contract hoàn toàn) | FALLBACK → hành vi T166 hiện tại (person-only) — KHÔNG HARD_FAIL vì thiếu contract, không phải vì sai identity |
| 13 | LLM ignores contract nhiều lần (statistical) | Không phải per-request state — cần metric riêng (giống `log_prompt_metrics`), ngoài phạm vi failure-state của 1 request |
| 14 | Parser ambiguity (2 cách hiểu hợp lệ) | REVIEW_REQUIRED |

## 11. Backward compatibility

- Cache cũ (plain string, không có alignment): **đọc được** — `translated_text` không đổi cột/ý nghĩa.
- Có được coi là "aligned" không: **KHÔNG** — cache cũ phải được coi `alignment_method='none'`
  (hoặc NULL = legacy), tự động rơi vào FALLBACK (giống #12 ở trên), KHÔNG suy diễn ngược thành đã align.
- Cần invalidate không: **Đề xuất KHÔNG tự invalidate** — giữ nguyên nguyên tắc T166 §8 hiện tại
  ("draft vẫn serve, không tự re-LLM"); cache cũ tiếp tục PASS/serve như hiện nay (NULL = legacy pass),
  chỉ áp dụng alignment cho request MỚI.
- Version marker: **có**, cần (`alignment_method` chính là version marker, additive column).

## 12. Rollback design

- Toàn bộ 3 option đều **additive schema** (cột mới) — rollback = drop cột mới, code revert về
  `post_assert(lock, output)` 2-tham-số cũ, KHÔNG mất dữ liệu cache cũ.
- Backup trước khi migrate thật (khi tới lúc implement): theo đúng pattern `t166_identity_migrate.py`
  đã có (`--dry-run/--apply/--revert` + backup file).

## 13. Implementation phases (nếu Admin chọn 1 option — CHƯA làm)

1. Chốt 1 option (Admin) + chốt field bắt buộc/optional trong EntityAssertion.
2. Migration additive (cột mới trên `translation_cache`), theo pattern `t166_identity_migrate.py`.
3. Đổi `_t73_build_style_prompt` thêm output-contract instruction + ví dụ mẫu.
4. Đổi `_t73_call_gemini` (hoặc lớp gọi ngay sau nó) để parse output theo contract, có fallback.
5. Mở rộng `post_assert()` nhận `entity_assertions` optional, giữ fallback path cũ nguyên vẹn.
6. Đo benchmark thật (token/latency/malformed rate) theo mục 9 — pilot 1 source_type trước.
7. Wire 3 luồng dịch (interactive/batch — không có admin mirror vì `admin/app.py` không tồn tại).
8. Regression: T165 11/11, T166 18/18, matrix + Case C mới, real DB smoke.
9. Rollout dần theo `source_type` (như T165 Phase 7 đã làm) để giới hạn mass-miss.

## 14. Open questions (cần Admin trả lời trước khi implement)

1. Chọn Option 1/2/3 hay kết hợp (vd sidecar cho production, JSON cho fixture test)?
2. Chấp nhận mức cache mass-miss 1 lần (100% cho source_type được bật) hay bắt buộc pilot cực nhỏ trước?
3. `source_span`/`target_span` có bắt buộc lưu cache lâu dài cho audit không, hay chỉ runtime?
4. Case D (DHARMA_NAME) có nằm trong scope Phase 8 này không, hay vẫn tách riêng chờ nguồn dữ liệu thật
   (khuyến nghị: tách riêng — Phase 8 giải quyết CƠ CHẾ alignment, không tự tạo ra fixture DHARMA_NAME)?
5. Batch worker (`cbeta_translate_worker.py`) có cần alignment ngay hay chỉ áp dụng luồng interactive trước?

## 15. Exact files/functions that would change (nếu implement — CHƯA đổi)

| File | Hàm/vị trí | Thay đổi dự kiến |
|---|---|---|
| `canonical_lock.py` | `post_assert()` | Thêm tham số `entity_assertions` optional |
| `canonical_lock.py` | `translate_with_guard()` | Truyền `entity_assertions` nếu `call_llm_fn` hỗ trợ |
| `style_constitution.py` | `constitution_hash()` | Thêm phần tử hash `alignment_method` |
| `style_constitution.py` | `write_cache()` | Thêm cột optional lưu assertion/alignment_method (guard `_has_col`) |
| `app.py` | `_t73_build_style_prompt` (16569) | Thêm output-contract instruction theo option chọn |
| `app.py` | `_t73_call_gemini` (16583) | Parse response theo contract, fallback plain-string |
| `app.py` | 4 call site `_t166_post_check_translation` (6421/16778/17318/17895) | Truyền thêm assertions nếu có |
| `scripts/cbeta_translate_worker.py` | batch flow | Tương tự, nếu Admin chọn áp dụng batch |
| Migration mới | `scripts/t165_phase8_alignment_migrate.py` (tên đề xuất) | Cột additive, theo pattern `t166_identity_migrate.py` |

## 16. Estimated Cloud Session effort

- Thiết kế chi tiết + Admin chốt option: đã hoàn thành ở tài liệu này.
- Implement (nếu chọn Option 1 hoặc 2): trung bình-lớn — nhiều session, cần đo token/malformed-rate
  thật qua nhiều vòng thử (rủi ro chi phí building do LLM calls lặp lại để benchmark).
- Implement Option 3 (sidecar): rủi ro thấp hơn về cache/backward-compat nhưng rủi ro accuracy
  (offset sai) cần vòng test riêng — effort tương đương.
- Rủi ro chi phí lớn nhất nằm ở bước 6 (benchmark thật) và bước 8 (regression đầy đủ) — mỗi vòng
  cần chạy LLM thật nhiều lần, khác với các spike thuần đọc-code đã làm tới nay.

---

## FILES INSPECTED
`canonical_lock.py`, `style_constitution.py`, `app.py` (dòng 16569/16583/6421/16778/17318/17895/13066+
đã audit ở session trước), `scripts/cbeta_translate_worker.py` (tham chiếu), `docs/Mimo-Flash/X-T165-*-SPEC.md`
§7/§15, `docs/Mimo-Flash/X-T166-*-SPEC.md` §6/§14/§20, `docs/tasktodo.md` (T177/T178 entries).

## FILES CHANGED
Không có. Chỉ tạo file báo cáo này (`docs/Mimo-Flash/T165-PHASE8-XML-BOUNDARY-ARCHITECTURE-SPIKE.md`).

## FILES NOT CHANGED
`app.py`, `canonical_lock.py`, `style_constitution.py`, `data/lineage.db` (schema), mọi test file,
`docs/tasktodo.md`, `docs/ROLLBACK.md`, `docs/ADMIN_REVIEW_DASHBOARD.md`.

## EXACT ARCHITECTURAL GAP
`call_llm_fn: callable(prompt: str) -> str` không có cơ chế trả entity/span evidence; đây là điểm
duy nhất trong pipeline cần mở rộng contract để T166 detect substitution deterministic cho
PLACE/DHARMA_NAME/TEMPLE (không chỉ PERSON).

## 3 OPTIONS
Đã trình bày đầy đủ ở mục 3/4/5 — không xếp hạng, không chọn winner.

## DEPENDENCIES
T165 (`constitution_hash`, `write_cache`, `style_lock`), T166 (`canonical_lock.py`, `post_assert`),
T177 (đã ghi nhận trước đó rằng "XML boundary" thuộc T165 Phase 8 — spike này chính là Phase 8 đó).

## RECOMMENDED NEXT TASK TYPE
Task riêng (không phải sửa nhỏ trong T166): **T165 Phase 8 implementation** — sau khi Admin chọn
1 trong 3 option + trả lời 5 open questions ở mục 14.

---

**VERDICT: SPIKE-COMPLETE**

Không code production, không migration, không cache rewrite, không commit, không sang T177,
không đóng T166.
