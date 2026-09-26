---
id: T177
title: "Review DIRECTIVE v2 — Trie + Dual-Hash + XML Boundary (đối chiếu với repo/DB thật)"
type: review
status: done
reviewed_at: "2026-09-25"
absorbed_at: "2026-09-26 (D1–D5, D8 hoàn tất; D6/D7 data+runtime đã xong; T177 closed — Admin 'commit, T177 done')"
renumbered_to: "2026-09-26 (T167 → T177 — tránh collision với tasks/T167-rules-constrained-buddhist-translation-engine)"
reviewed_by: opencode (mimo-v2.6)
source: "TASK DIRECTIVE: REFACTORING TRANSLATION ENGINE TO DYNAMIC FILTER (TRIE) + DUAL-HASH CACHE + XML BOUNDARY (bản v2 — full architecture + reference code + acceptance)"
absorbed_into: [T165, T177]
task: docs/Mimo-Flash/T177-dynamic-filter-absorb-directive-v2.md
---

# REVIEW — DIRECTIVE v2 (Trie + Dual-Hash + XML Boundary)

> Audit **read-only** trên `data/lineage.db` (mở `mode=ro`) + `app.py` (21.232 dòng, 2026-09-26) +
> `scripts/t50_passage_vi_backfill.py` + `style_constitution.py`.
> **Không sửa code trong review này.** Toàn bộ kết luận = đề xuất để Admin chốt.
> Mức độ: **P0** = làm theo directive sẽ sai/crash/mất dữ liệu · **P1** = không đạt mục tiêu · **P2** = lệch nhỏ.
> Lưu ý: `admin/app.py` **KHÔNG tồn tại** (đã xác nhận trong T168) — stack thật là codebase đơn `app.py`.

---

## 0. KẾT LUẬN (đã Admin duyệt 2026-09-25 — Phương Án D)

**Không chạy directive như một task song song / engine mới.** Absorb vào T165
(`docs/Mimo-Flash/X-T165-rules-constrained-translation-engine-SPEC.md`) theo **8 bước Bảng D §5**,
giao quản lý bằng task mới **T177** (`docs/Mimo-Flash/T177-dynamic-filter-absorb-directive-v2.md`).

| Nguyên tắc | Chi tiết |
|------------|----------|
| Absorb, không parallel engine | Không tạo `translator.py` / `prompt_service.py` mới — mọi thay đổi nằm trong `app.py` + `scripts/t50_passage_vi_backfill.py` + module `style_constitution.py` (T165 §5) |
| Reference code **không được copy nguyên trạng** | 7 P0 Bảng B phải sửa trước khi dùng; code tham khảo chỉ là ý tưởng |
| XML boundary | = **Phase 8** của T165 (optional, sau Admin QA phase 1) — **không** hard-gate phase 1 |
| Trie | Gate `n_terms ≥ 1000` — hiện **89** term → chưa cần; giữ ngưỡng này làm điều kiện phase 2 |
| Token | **Không** hard-gate 150–250 token (con số directive đặt sai — xem §1). Đo `usage.prompt_tokens` thật rồi chốt ngân sách |

---

## 1. SỐ ĐO THẬT (bằng chứng — không ước lượng cảm tính)

Đo read-only 2026-09-25 trên `data/lineage.db`; **tái đo 2026-09-26** sau khi T165 seed thêm rules:

| Hạng mục | Số thật | Nguồn |
|----------|---------|-------|
| `translation_rules` active | **110 rows / 13.230 chars** `rule_text` (terminology **88** · style **10** · forbidden **6** · gate **3** · structure **1** · provenance **1** · grammar **1**) · 1 row `dismissed` (`TERM_NAMNHAC`) — cập nhật sau D6 (HANVIET_NAMES deactivate, NO_PINYIN restored) | `SELECT rule_type,count(*),sum(length(rule_text)) … WHERE status='active' AND is_active=1` |
| Rendered rule block (prompt thật) | ≈ 12.287 chars (raw + header/bullet formatting) | `_t73_build_style_prompt` app.py:16569 |
| Glossary block | raw `term_zh` 146 + `term_vi` 596 chars → render **≈ 1.373 chars** (79 locked, trong đó **14 term 1-char**) | `translation_glossary WHERE is_locked=1` |
| Exemplar block | 2.692 rows → inject **≈ 606 chars** (sample) | `translation_exemplar` |
| **Prompt đầy đủ hiện tại** | **≈ 14.874 chars ≈ 4.000–5.000 tokens** (12.287 + 1.373 + 606 + persona/chrome) | cộng dồn |
| Prompt "static-only" (11 rule 2.700 chars) + XML wrapper | **≈ 3.400 chars ≈ 750–950 tokens** | đo |
| Directive v2 khẳng định | "baseline 750–950 → target **150–250 token**" | — |

**Hệ quả (P1, hai phía):**

1. Số "750–950 baseline" của directive **không khớp hiện trạng** — hiện trạng là **4.000–5.000 token**;
   750–950 chỉ đúng với *prompt tĩnh đã lọc*, tức directive đo nhầm mốc.
2. Mốc **150–250 token** là **không khả thi**: riêng persona + output-format chrome + XML wrapper
   đã ~1.000 chars, chưa kể block glossary/exemplar. Không có tokenizer library trong env
   (không `transformers`, không `tokenizers`) → số token hiện là **ước lượng theo chars**.
   ⇒ T165 log `usage.prompt_tokens` thật rồi chốt ngân sách; **cấm** ghi 150–250 vào acceptance.
3. Còn lại: **429 chưa từng xảy ra trong log** (`data/llm_config.json` `last_error=None`) — tức retry/backoff
   là **biện pháp phòng vệ**, không phải fix sự cố đang diễn ra. Model thật: `qwen/qwen3.8-27b` (Groq, app.py:16382).
   Không có file `app.log`/`translate.log` như directive nghĩ — log thật là `app_local.log` / `app_local_err.log` / `gateway_local*.log` / `server_local*.log` ở root daoanh.

**Data bug phát hiện kèm (P1):** `NO_PINYIN` (forbidden) và `HANVIET_NAMES` (terminology) đang có
`rule_text='_keep_'` (6 ký tự, `updated_at=2026-09-12T10:28`) → **nội dung rule đã mất**,
`HANVIET_NAMES` còn là rule terminology hay dùng. → Bước **D6** (Bảng D). **✅ ĐÃ FIX 2026-09-26**
(Admin phê chuẩn): `NO_PINYIN` restore text gốc seed T73 (cấm pinyin + ví dụ); `HANVIET_NAMES`
DEACTIVATE `is_active=0` (trùng CANONICAL_NAMES/HANVIET_PLACES). Script `scripts/t177_d6_rules_fix.py`.

---

## 2. BẢNG A — Directive v2 nói ĐÚNG (giữ nguyên, không sửa)

| # | Điểm directive | Đối chiếu repo |
|---|----------------|----------------|
| A1 | Static-hash chỉ theo `rule_code` là **không an toàn** | Đúng — T165 §14.2 #5 đã cấm `static_sig` chỉ-code; sửa 1 rule_text mà codes không đổi → HIT sai |
| A2 | Glossary + exemplar phải tham gia hash invalidation | Đúng — `_t73_rules_version` (app.py:16412) hiện chỉ hash `rule_text` → đổi glossary **không** miss cache |
| A3 | Phải đo `usage.prompt_tokens` | Đúng — từ T165 build đã gọi `_t165_log_prompt_metrics` tại app.py:16606 (đọc `usage.prompt_tokens/completion_tokens/total_tokens`, style_constitution.py:436); **gap còn lại**: 429 retry/backoff + viết prompt_tokens vào DB cho dashboard |
| A4 | Invalidate hàng loạt (1762 row) có thể gây burst/429 | Đúng — endpoint `POST /daoanh/api/admin/translate/invalidate` (app.py:18396) set `status='invalidated'` cho **toàn bộ 1.762 row** (`rv='ALL'`); 2 nút gọi ở `admin/translation_cache.html:280` + `admin/translation_rules.html:296` → lần "Dịch lại" sau đó = burst 1.762 lượt gọi LLM |
| A5 | Code-preservation (wrapper cũ → builder mới) | Đúng — trùng khớp T165 §5.1 (wrapper `_t73_*`, `t50`) |
| A6 | Acceptance "sửa rule → chỉ dòng dính rule đó MISS" | Đúng — đây chính Mục tiêu 2 của T165 (Test Case 2 của directive = mục tiêu này) |
| A7 | additive-only migration, không ALTER bảng nền | Đúng — đúng hard rule của repo |
| A8 | Cần retry/backoff khi 429 | Đúng nhưng **phòng vệ** (xem §1.3) — `_t73_call_gemini` (app.py:16575) hiện **return ngay** khi `rate_limit` (app.py:16602), không retry, không backoff, mọi prompt gửi `role='user'` đơn (không system role) |

---

## 3. BẢNG B — P0: reference code của directive sai (7 lỗi code + 1 lỗi stack)

**Không được copy nguyên trạng.** Sửa hết trước khi dùng làm nền:

| # | P0 | Directive viết | Thực tế (bằng chứng) | Sửa thành |
|---|----|----------------|------------------------|-----------|
| B1 | Sai field name | `rule.get("code") / rule.get("type") / rule.get("content")` | Schema thật = **`rule_code` / `rule_type` / `rule_text`** (`translation_rules`); `rule.get("code")` → `None` → mọi rule thành rỗng | Dùng đúng 3 cột; thêm assert `rule_code` non-empty khi build prompt |
| B2 | Hash code-only, không delimiter | `static_hash = sha256("".join(sorted(codes)))` | `["AB","C"]` và `["A","BC"]` cùng hash → **tránh né va chạm hash** (under/over-invalidation) | `sha256("\x1f".join(sorted(codes)))` (delimiter rõ) — và codes **không đủ** (xem B3) |
| B3 | Hash B thiếu thành phần | Hash B chỉ gồm rules + source_hash | Thiếu `glossary ⊕ exemplar ⊕ label ⊕ json_mode ⊕ PROMPT_FORMAT_VERSION ⊕ T166 fingerprint` → prompt đổi mà HIT cũ (đúng lỗi T165 §14.2 #5 đang fix) | Hash = **phần THẬT đã inject**, tính **sau** `finalize_lock` (T165 §3/§5) |
| B4 | Ghi đè cột có sẵn | Dual-hash lưu vào cột **`source_hash`** | `translation_cache` có `UNIQUE(source_hash, source_type)` + **15 chỗ `FROM translation_cache`** trong `app.py` đang đọc `source_hash` là khóa tra | Giữ `source_hash` nguyên vẹn (khóa tra cũ); hash mới là **cột additive** `constitution_hash` (T165 §4) |
| B5 | Test Case 1 không thể xảy ra | "rule 達磨/面壁 match với source chứa 達磨/面壁" | `達磨`, `面壁` **không nằm trong rule_text nào** và **không trong glossary** (79 locked) → case luôn MISS → test "xanh" giả | Chọn fixture **có thật**: `A009460 丹霞天然` (vnpa `don_ha_thien_nhien` status=`verified`, dila_id=`A009460`; people left `天然` → match theo **substring**) hoặc trích term thật từ `translation_rules.rule_text` |
| B6 | XML fragment thiếu input/output | Fragment XML chỉ có rules, **không có source text, không instruction dịch** | Prompt chỉ có rule → model không biết phải làm gì (và bị coi là chat rác) | XML block phải gồm `<source>`, output-format contract, và rule theo `match_scope` (T165 Phase 8) |
| B7 | Workflow `cp file.py file.py.bak` | Directive hướng dẫn backup bằng `.bak` | Repo **cấm** backup kiểu này — mọi revert qua **`git revert <sha>`** (AGENTS §9 Code Preservation + `docs/ROLLBACK.md`); `.bak` trôi nổi trong repo (đã có nhiều `*.bak` trong `docs/sessions/` phải dọn) | Revert = `git revert --no-edit <sha>` + script `--revert` cho DB; **không** tạo `.bak` |
| B8 | Đặt tên file/stack bịa | `translator.py`, `prompt_service.py`, FastAPI, Redis | **Không tồn tại** — stack thật: `app.py` (Flask, 21.232 dòng) + **SQLite** `lineage.db`; **`admin/app.py` KHÔNG tồn tại**; 12 site `app.py` + 3 site `style_constitution.py` ghi `translation_cache` (t50: 0 qua pattern INSERT/UPDATE) | Mọi code tham khảo dịch về file thật đã liệt kê (T165 §10 File I/O map) |

---

## 4. BẢNG C — P1 / P2 (đề xuất吸收 — không chặn)

| # | Mức | Vấn đề | Đề xuất |
|---|-----|--------|---------|
| C1 | **P1** | Retry/backoff 429 + log `prompt_tokens` — log **đã build** (T165: `_t165_log_prompt_metrics` app.py:16606, đọc usage tại style_constitution.py:436); **còn thiếu**: retry/backoff 429 (đang `return None` ngay) + viết `prompt_tokens` vào DB cho dashboard | Absorb vào T165 Phase 5/6: `_t73_call_gemini` (app.py:16575) thử lại tối đa 2 lần với backoff; persist `usage.prompt_tokens/total_tokens` |
| C2 | **P1** | Invalidate burst (A4) chưa có giới hạn | Thêm option "Dịch lại có giới hạn" (batch N row/request) bên cạnh nút hiện tại; giữ nút full là chủ đích (Admin bấm) |
| C3 | **P1** | Ngân sách token chưa có số đo | Ghi baseline **đo được** vào T165 §8 acceptance sau 1 lần chạy thật; không hard-gate 150–250 |
| C4 | **P1** | `NO_PINYIN` + `HANVIET_NAMES` = `rule_text='_keep_'` (content mất) | **✅ D6 (2026-09-26):** NO_PINYIN restore text seed T73; HANVIET_NAMES deactivate (`is_active=0`) — script `scripts/t177_d6_rules_fix.py --stats/--dry-run/--apply/--revert` |
| C5 | **P2** | Trie ở 89 term = thừa | Giữ gate `n_terms ≥ 1000`; đo lại khi glossary > 1000 |
| C6 | **P2** | 14 term 1-char trong glossary → filter theo text gần như luôn match (không giảm token) + noise post-assert T166 | Không chặn; T166 tách severity (T165 §14.2 #15) |

---

## 5. BẢNG D — KẾ HOẠCH 8 BƯỚC (Admin duyệt 2026-09-25) → **T177**

| Bước | Nội dung | Output | Chạy ở |
|------|----------|--------|--------|
| **D1** | Không chạy directive như task độc lập — absorb vào T165 | ✅ SPEC T165 **§15** trỏ review (added 2026-09-26) + checklist ref §15/T177 | docs |
| **D2** | Sửa **7 P0 Bảng B** (+ B8 stack) trước khi dùng code tham khảo | ✅ Checklist T177 §3 — B1–B8 verified vs code/DB (constitution_hash 168-199 · select_rules · migration additive · fixture A009460 verified) | docs/Mimo-Flash/T177 |
| **D3** | Bổ sung acceptance vào T165 §8: (a) `prompt_tokens` đo được · (b) sửa rule → row `edited` không bị ghi đè · (c) invalidate burst có giới hạn · (d) `rules_outdated` badge đúng sau khi thêm cột hash | ✅ acceptance §8 mục **13–16** (added 2026-09-26) | T165 §15 + §8 |
| **D4** | XML boundary → **Phase 8** T165 (optional, sau Admin QA; không gate phase 1) | ✅ §7 Phase 8 + §15 table row | T165 §7 Phase 8 |
| **D5** | Trie gate `n_terms ≥ 1000` (hiện 89) → phase 2, chưa build | ✅ §15 table row (substring đủ; đo lại khi > 1000) | T165 §15 |
| **D6** | Sửa data `NO_PINYIN` + `HANVIET_NAMES` (`rule_text='_keep_'` → nội dung thật) | **✅ DONE 2026-09-26** — script `--apply` (backup `lineage_t177_d6_fix_20260926_105027.db`); NO_PINYIN restored, HANVIET_NAMES deactivated; active 111→110, `_keep_` 2→0 |
| **D7** | Đo baseline `prompt_tokens` thật (1 lần chạy) → chốt ngân sách token (không bịa 150–250) | **✅ DONE 2026-09-26** — prompt_tokens = 3.422 thật (2 lần đo 3629/3630); ngân sách ~3.400–3.700, cấm hard-gate | runtime |
| **D8** | Giữ mục tiêu Test Case 2 (sửa rule → chỉ dòng dính rule đó MISS, dòng khác HIT) = acceptance chính | ✅ §8 mục 17 (fixture thật `A009460 丹霞天然`) | T165 §8 |

**Không có bước nào** tạo engine song song, file mới ngoài `style_constitution.py`, hay migration phá schema.

---

## 6. Boundary / Out of Scope

- **Không** đổi cột `source_hash`, không DROP, không ALTER bảng nền (additive-only).
- **Không** đụng T166 (layer trên) ngoài việc `fingerprint` participates vào hash (đã là T165 §3).
- **Không** build Trie/XML ở phase 1.
- **Không** commit khi chưa `npm run pipeline` PASS + Admin confirm.

---

## 7. Liên kết

| File | Vai trò |
|------|---------|
| `docs/Mimo-Flash/X-T165-rules-constrained-translation-engine-SPEC.md` §14 (review SPEC) · **§15 (absorb directive v2)** | SSOT đặc tả |
| `docs/Mimo-Flash/T177-dynamic-filter-absorb-directive-v2.md` | Task quản lý 8 bước Bảng D |
| `docs/Mimo-Flash/X-T166-canonical-identity-guard-SPEC.md` §20 | Review song song (identity guard) |
| `docs/tasktodo.md` · `docs/ADMIN_REVIEW_DASHBOARD.md` item 18 | Trạng thái cho Admin |
| `docs/sessions/2026-09-26_t177_directive_v2_absorb.md` | Session log |
