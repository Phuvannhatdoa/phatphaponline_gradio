---
id: T165
title: "Rules-Constrained Translation Engine — Semantic Selective Rules + Constitution Hash Cache"
module: Editorial / LLM Translation
priority: high
status: in_progress
owner: claudecode
depends_on: [T73, T123, T158-glossary-resolver]
created: 2026-09-24
updated: 2026-09-25
spec: docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-24 (Admin — option B 1 SPEC; amend same-day: absorb directive A, phase2=XML+Trie, glossary_filter_text=1)"
done_when: |
  _select_rules always∪terms; glossary lock filter theo source_text;
  constitution_hash = full static+matched rule_text ⊕ filtered glossary
  ⊕ exemplar ⊕ PROMPT_FORMAT_VERSION ⊕ T166 fingerprint;
  wrappers _t73_* + admin/app.py + t50 cùng style_constitution.py;
  admin UI match_scope/match_terms; log prompt_tokens;
  npm run pipeline PASS; có revert. Phase 2 XML/Trie không gate phase 1.
---

# T165 — Rules-Constrained Translation Engine

**SPEC build (đọc 1 file → dev):**  
`docs/Mimo-Flash/T165-rules-constrained-translation-engine-SPEC.md`

| Mục | Ghi chú |
|-----|---------|
| Approve | Admin option **B** — gộp audit + SPEC thành 1 file Mimo-Flash |
| Amend | **2026-09-24** absorb “Trie+Dual-Hash+XML” directive: **A** · phase2 XML/Trie · **glossary filter text = phase 1** |
| Task ID | T165 free verified 2026-09-24 (T158 ×2 done; T162 missing file = debt) |
| Layer trên | — |
| Layer dưới / song | **T166** Canonical Lock ghép `style_lock` + `constitution_hash` |
| Owner build | Claude Code |

## Checklist
- [x] SPEC Mimo-Flash + task này + tasktodo + session log (handoff docs 2026-09-24)
- [x] Amend SPEC theo Admin 1A / phase2 / glossary_filter (2026-09-24)
- [x] Review §14 (SPEC ↔ DB/code) + **§15 absorb DIRECTIVE v2** (2026-09-25) → task **T177** (`docs/Mimo-Flash/T177-dynamic-filter-absorb-directive-v2.md` — renumbered từ T167 2026-09-26)
- [x] **§15 ref §8 + §7:** acceptance D3(a–d)/D8 + Trie gate `n_terms≥1000` + XML Phase 8 (2026-09-26, T177)
- [x] **§16 absorb T168** (2026-09-25) → cache regression A–I + benchmark + observability
- [ ] Đóng các P0 §14 + acceptance §15 D3/D8 **trước** Phase 3
- [x] **Phase 1** `scripts/t165_rules_engine_migrate.py` (`--stats/--dry-run/--apply/--revert`) — build 2026-09-25
- [x] **Phase 2** `style_constitution.py` + `tests/test_t165_style_constitution.py` (23 test PASS) — build 2026-09-25
- [x] **Phase 6 (đi trước)** `--apply` trên prod 2026-09-25 → backup `data/backups/lineage_t165_20260925_061718.db` (1376 MB) · backfill **71 terms / 26 always (15 extract-fail→always)** · cache 3 cột NULL
- [ ] **Phase 3** wrap `_t73_*` app.py (chờ P0 §14 đóng) → **blocked by review, không chặn Phase 2**
- [ ] **Phase 4** mirror `admin/app.py` + refactor `t50`
- [ ] **Phase 5** UI match fields + `invalidated_cache_count`
- [ ] **Phase 7** `npm run pipeline` PASS (chạy cuối build này)
- [ ] Phase 8 XML+Trie **optional sau** Admin QA phase 1 (không cùng commit phase 1)
- [ ] Session log build + tasktodo + commit `feat: T165 … + docs`
- [ ] Admin confirm → move `docs/taskdone.md`

## Build log 2026-09-25 (Admin: “Đồng ý build”)
| Việc | Output |
|------|--------|
| Migration `--apply` (additive 5 cột) | `match_scope/match_terms` + `constitution_hash/selected_rule_codes/glossary_hash` · stats `always=26 terms=71` · `terms rỗng=0` |
| Backup (Zero-RAM sqlite backup API) | `data/backups/lineage_t165_20260925_061718.db` (1376.0 MB) |
| Module SSOT | `style_constitution.py` (select_rules · constitution_hash · glossary_hash · filter_glossary · style_lock · build_style_prompt · invalidate · log_prompt_metrics) |
| Tests | `tests/test_t165_style_constitution.py` (18) + `tests/test_t165_migrate.py` (5) = **23 PASS** (gồm smoke `data/lineage.db` RO) |
| Sửa SPEC §6.2 regex lỗi | `[→->]+` → `re.error: bad character range` → dùng `(?:->|→|>)` (đã ghi nhận, module là SSOT) |
| Session | `docs/sessions/2026-09-25_t165-build-phase0-1-2.md` |

## Revert
`git revert --no-edit <sha>` + `python scripts/t165_rules_engine_migrate.py --revert` + backup DB path.
