---
id: T177
title: "Absorb DIRECTIVE v2 (Dynamic Filter/Trie + Dual-Hash + XML) vào T165 — plan chi tiết"
module: Editorial / LLM Translation
priority: high
status: done
owner: claudecode
depends_on: [T165, T166]
created: 2026-09-25
updated: 2026-09-26
closed_at: "2026-09-26 (Admin: 'commit, T177 done')"
renumbered: "2026-09-26: T167 → T177 (tránh collision với tasks/T167-rules-constrained-buddhist-translation-engine + theo series Mimo-Flash T170–T176)"
spec: docs/Mimo-Flash/T177-directive-v2-trie-xml-dualhash-REVIEW.md
parent_spec: docs/Mimo-Flash/X-T165-rules-constrained-translation-engine-SPEC.md
designed_by: opencode (mimo-v2.6) — review directive v2
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin — Phương Án D: ghi review ra /docs + tạo task Txx + cập nhật Dashboard)"
done_when: |
  8 bước D1–D8 hoàn tất: review doc + T165 §15 + acceptance D3/D8 vào T165 §8;
  7 P0 Bảng B được ghi cách sửa (không copy reference code nguyên trạng);
  XML → Phase 8, Trie gate n_terms≥1000; data NO_PINYIN/HANVIET_NAMES
  phục hồi rule_text (script --dry-run/--revert, Admin duyệt text) — D6 ✅;
  baseline prompt_tokens đo được (không hard-gate 150–250) — D7 ✅;
  tasktodo + ADMIN_REVIEW_DASHBOARD item 18 + dashboard regen;
npm run pipeline PASS; mọi thay đổi có revert path (git revert, không .bak).
   --- ✅ T177 DONE 2026-09-26 (Admin "commit, T177 done"): D1–D8 đầy đủ, D6 revert
   round-trip tested, pipeline PASS, commit + taskdone entry xong. Build T165 Phase 3–6 = task riêng.
---

# T177 — Absorb DIRECTIVE v2 (Trie + Dual-Hash + XML) vào T165

**Review (đọc 1 file → chốt):**  
`docs/Mimo-Flash/T177-directive-v2-trie-xml-dualhash-REVIEW.md`

| Mục | Ghi chú |
|-----|---------|
| Approve | Admin **2026-09-25 — Phương Án D** (8 bước) |
| Task ID | **T177** (đổi từ T167 2026-09-26 — collision `tasks/T167-rules-constrained-buddhist-translation-engine`; T170–T176 trong series Mimo-Flash) |
| Bản chất | **Docs + plan + data-fix**, KHÔNG phải engine mới |
| Layer trên | **T165** (đây là bổ sung scope/acceptance cho T165) · **T166** (fingerprint tham gia hash) |
| Owner build | Claude Code |
| BLOCK khi | (cũ) D6 chờ text — **đã hết 2026-09-26:** NO_PINYIN restored, HANVIET_NAMES deactivated |

## Checklist

### D1 — Absorb, không parallel engine
- [x] Review doc `docs/Mimo-Flash/T177-directive-v2-trie-xml-dualhash-REVIEW.md` (Bảng A/B/C/D)
- [x] T165 SPEC thêm **§15** trỏ review + nguyên tắc absorb (2026-09-25) — **bổ sung 2026-09-26:** §15 thực tế đã ghi vào `X-T165-…-SPEC.md` (trước đó chỉ có §14 → task doc tick sớm; nay verify có thật + fix link `X-Done-→X-`)
- [x] T165 `docs/Mimo-Flash/X-Done-T165-*.md` checklist thêm dòng tham chiếu §15/T177 — **bổ sung 2026-09-26:** file thật `X-T165-rules-constrained-translation-engine.md` (tick rename T167→T177 + dòng §15 ref §8/§7)

### D2 — Sửa 7 P0 Bảng B trước khi dùng code tham khảo
- [x] B1 field `rule_code/rule_type/rule_text` (cấm `code/type/content`) — verify: `style_constitution.py:select_rules` dùng đúng 3 cột; test T165 assert field (SPEC §8 mục 5b)
- [x] B2 hash có delimiter (`\x1f`), không `join` trống — verify: `constitution_hash` `'\n'.join(parts)` (style_constitution.py:199) — delimiter `\n` tách phần, không nối trống
- [x] B3 hash B đủ glossary ⊕ exemplar ⊕ label ⊕ json_mode ⊕ PFV ⊕ T166 fingerprint (sau `finalize_lock`) — verify: style_constitution.py:168-199 đủ 8 phần (rules/glossary/exemplar/FMT/label/json/known_pending/fp/extra_hash)
- [x] B4 **không** ghi đè `source_hash` (cột additive `constitution_hash`) — verify: T165 migration thêm cột additive `constitution_hash`, `source_hash` giữ UNIQUE(source_hash,source_type) (SPEC §2/§4)
- [x] B5 fixture thật (`丹霞天然` A009460 = vnpa `don_ha_thien_nhien` verified, match substring `天然`) — bỏ 達磨/面壁 — **verify 2026-09-26:** DB `A009460 → Đơn Hà Thiên Nhiên` status `verified`
- [x] B6 XML fragment có `<source>` + output contract — ghi vào REVIEW B6 → T165 Phase 8
- [x] B7 workflow `git revert` — **cấm** `cp *.bak` — tuân thủ (T177 revert §Revert, ROLLBACK.md)
- [x] B8 mọi code tham khảo dịch về `app.py`/`t50`/`style_constitution.py` — ghi vào REVIEW B8 + T165 §10

### D3 — Bổ sung acceptance vào T165 §8
- [x] (a) log `usage.prompt_tokens/total_tokens` — log đã build (`_t165_log_prompt_metrics` app.py:16606); retry/backoff 429 + persist prompt_tokens = gap thật (429 3/5 đo) → **acceptance §8 mục 13** ghi: retry ≤2 lần backoff + persist, cấm hard-gate 150–250
- [x] (b) sửa rule → row `status='edited'` (6 rows) **không** bị REPLACE → **acceptance §8 mục 14**
- [x] (c) invalidate burst có giới hạn (bên cạnh nút full 1.762 row app.py:18396) → **acceptance §8 mục 15**
- [x] (d) badge `rules_outdated` + admin cache list đúng sau khi thêm cột hash (audit 15 read site app.py) → **acceptance §8 mục 16**

### D4/D5 — Phase gating
- [x] D4 XML boundary → T165 **Phase 8** (optional, sau Admin QA phase 1, không gate phase 1) — §7 Phase 8 + §15 table row
- [x] D5 Trie gate `n_terms ≥ 1000` (hiện **89** term) → ghi vào T165 §15 — §15 table row (substring đủ hiện tại; đo lại khi > 1000)

### D6 — Data fix ✅ (DONE 2026-09-26, Admin phê chuẩn đề xuất)
- [x] `--stats`/`--dry-run` in `rule_text` hiện tại (`'_keep_'`) của `NO_PINYIN` + `HANVIET_NAMES`
- [x] Admin duyệt (2026-09-26): **NO_PINYIN → restore text gốc seed T73** (cấm pinyin + ví dụ); **HANVIET_NAMES → DEACTIVATE** (`is_active=0`) vì trùng CANONICAL_NAMES/HANVIET_PLACES
- [x] Áp dụng: `scripts/t177_d6_rules_fix.py --apply` (backup `data/backups/lineage_t177_d6_fix_20260926_105027.db`) → verify: active rules **111 → 110** (terminology 89→88), `_keep_` active **2 → 0**, chars 13.041 → **13.230**; cache invalidate 0 (chưa có row semantic — legacy auto-miss qua rules_version)
- [x] `--revert` (lưu `'_keep_'` cũ) + verify `count` không đổi, 0 row bị xoá — **✅ TESTED 2026-09-26 round-trip:** revert → NO_PINYIN=‘_keep_’ + HANVIET_NAMES is_active=1, active 110→111, `rules_total` **112 không đổi**, cache 1762 không đổi (0 row xoá); re-apply → backup mới `lineage_t177_d6_fix_20260926_114927.db`, active 111→110. Script đáng tin cho rollback.

### D7 — Đo baseline token ✅ (DONE 2026-09-26 — số đo thật)
- [x] Chạy lần dịch thật qua pipeline production (`_t73_style_lock` → `_t73_build_style_prompt` → `_t73_call_gemini`, trap `log_prompt_metrics`) → **prompt_tokens = 3.422** (source 266 chars / prompt 10.092 chars / total 3.630; Groq `qwen/qwen3.8-27b`)
- [x] Chốt ngân sách token: **~3.400–3.700 tokens/lần dịch ngắn** — directive's 150–250 target **không khả thi** (gấp ~14×); **cấm** hard-gate. Ghi chú: 429 xịt thật 3/5 lần → retry/backoff là gap thật (A8)

### D8 — Acceptance chính
- [x] Test Case 2: sửa 1 rule → dòng dính rule đó MISS, dòng khác vẫn HIT (dùng fixture thật) — **bổ sung 2026-09-26:** acceptance §8 mục 17 (fixture `A009460 丹霞天然`, match substring `天然`); build theo khi T165 Phase 3–6 wrap code

### Đóng task
- [x] `docs/tasktodo.md` cập nhật trạng thái + `docs/ADMIN_REVIEW_DASHBOARD.md` item 18 — **✅ 2026-09-26:** tasktodo row T177 thêm D1–D8/done_when; dashboard item 18 ghi đầy đủ trạng thái hoàn tất
- [x] Session log `docs/sessions/2026-09-26_t177_directive_v2_absorb.md` — **✅ 2026-09-26:** mục 8 (D1–D5/D8 + fix §15 thật + link X-Done→X-) + mục 9 (D6 revert round-trip) + mục 10 (tracking). ROLLBACK row giữ nguyên (chưa commit) — bổ sung khi commit.
- [x] `npm run pipeline` PASS → commit `docs: T177 … + docs` — **✅ 2026-09-26:** guard/lint/test/UAT/compliance/gov/T166-audit/e2e PASS (e2e:runtime EPERM pre-existing — `test-results\.last-run.json` bị lock bởi dev servers); Admin yệu cầu commit → commit docs `0e5ec12` (9 files) + hash-fill pass 2.
- [x] Admin confirm → move `docs/taskdone.md` — **✅ 2026-09-26:** Admin "commit, T177 done" → entry taskdone + status done.

## Revert
- Docs: `git revert --no-edit 62b593b` (review + SPEC §15 + tasktodo + dashboard + session) → **bổ sung 2026-09-26:** commit docs D1–D8 sau đó đã xuất hiện — revert theo thứ tự: `git revert 0e5ec12` rồi `git revert 62b593b` (hoặc 1 commit gộp chứa toàn bộ docs T177).
- Data (D6): `UPDATE translation_rules SET rule_text='_keep_' WHERE rule_code IN ('NO_PINYIN','HANVIET_NAMES')` (hoặc script `--revert`).
- **Không** dùng `cp *.bak` (banned — xem review B7).
- Backup DB: `data/backups/lineage_t177_d6_fix_20260926_105027.db`.
