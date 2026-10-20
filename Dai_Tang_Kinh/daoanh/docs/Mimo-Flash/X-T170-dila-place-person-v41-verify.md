---
id: T170
title: "Hardened v4.1 Verify Pipeline — Place + Person (2 side-car) — Chuẩn hóa danh xưng tu sĩ DILA"
module: Editorial / LLM Translation
priority: high
status: built
owner: claudecode
depends_on: [T169]
created: 2026-09-25
updated: 2026-09-28
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: 2 side-car + T170 + UI person defer) + Red-team amend (Admin: gộp T170 · CJK tự seed · salvage YES)"
done_when: |
  2 side-car + script --entity absorb v4.1 + R1–R8 red-team;
  pytest ≥11+≥6+≥5 red-team PASS; validate-only + pilot 25/entity;
  npm run pipeline PASS; revert = git revert + migrate --revert DROP 2 bảng.
---

# T170 — Task (pointer)

**SPEC đầy đủ:** [`docs/Mimo-Flash/T170-dila-place-person-v41-verify-SPEC.md`](T170-dila-place-person-v41-verify-SPEC.md)

- **Quyết định Admin:** **(1) 2 side-car** `place_groq_audit` + `person_groq_audit` (CẤM ALTER `people`/`places_dila`/`places_pending`) · **(2) task mới T170** depends_on T169 · UI person **defer** · docs-only lần này.
- **Red-team 2026-09-25 → SPEC §3bis R1–R8 (Admin: gộp T170 · CJK tự seed · salvage YES):** R1 polyphonic word-set ∩ + `R_d≠R_g` · R2 bracket stack lồng · R3 `fold_cjk` seed 峯/羣/祕/惠 + config cứng cấm đoán cột · R4 title multi-token loop · R5 `busy_timeout=10000` (WAL đã bật) · R6 flat-JSON salvage · R7 truncation partial salvage · R8 log fold_unmapped/salvage_used · **strike** bug 3.2 (id đã TEXT).
- **Review 2 directive → 6 P0 + ~11 P1:** `database.sqlite`/`dila_places`/`trans_dict_vi`/`dila_persons` sai → `data/lineage.db` · spine person = **`people` 48.673** · POLYPHONIC/TITLE/enum — SPEC §2–§3.
- **Giữ v4.1:** COALESCE · reject batch invalid/unexpected/dup · validate-only · pilot 25 · stale reset · remainder flush · strict Sanskrit 2-bên.
- **Phases:** 1 migrate → 2 classify+**R1–R7 tests** → 3 place → 4 person → 5 API/UI place → 6 pipeline. Session: `docs/sessions/2026-09-25_t170-v41-review-plan.md` + `2026-09-25_t170-redteam-amend.md`.
- **Revert:** `git revert --no-edit <sha>` · code sau: `scripts/t170_entity_groq_audit_migrate.py --revert --entity person` (**place thuộc T169** → revert bằng `t169_place_groq_audit_migrate.py --revert`).
- **📌 [2026-09-28 · T169-BUILD re-check — AMEND docs]:** T169 **đã build** (`393676f`/`4c8228b`, 2026-09-28) → premise cũ "0 file tồn tại / build mới từ zero" **SAI**; SPEC đã amend: (a) `verify_dila_places_groq.py` + `test_t169_classify_diff.py` 11/11 = **REFACTOR/EXTEND**; (b) migrate **chỉ tạo `person_groq_audit`**, `place_groq_audit` giữ T169 (không DROP); (c) `行` + core R1 `R_d≠R_g` word-token **đã absorbed** (`t169_classify.py:22,98-110`); (d) place API/UI đã build → phase 5 = đối chiếu enum; (e) R2/R3/R4/R6/R7 + `--entity person` + `busy_timeout=10000` (bỏ WAL pragma T169:75) là phần THẬT SỰ mới của T170.
- **🚀 [2026-09-28 · T170-BUILD — BUILD DONE]:** Code theo SPEC §12 BUILD CLOSURE — Phase 1 `--apply` DB THẬT (`person_groq_audit` + backup `lineage_t170_20260928_150114.db`) · Phase 2–4 `verify_dila_places_groq.py --entity {place,person}` + `t170_classify.py` (R2/R3/R4 + Sanskrit) + R5/R6/R7 · fix 2 bug T169 phát hiện khi smoke mock (cursor `''`→`0` — **đính chính [T189]: id THẬT là TEXT** `PL000000000001…`, bug chỉ tái hiện ở test-harness INTEGER giả; TAXONOMY self-match `殿`) · Phase 5 đối chiếu enum = place **không cần sửa**, person UI defer · Tests 17/17 + 15/15 + `test:t170` vào `test:translation` · pipeline PASS trừ `e2e:runtime` EPERM pre-existing. Task: `tasks/T170-dila-place-person-v41-verify.md` · Session: `docs/sessions/2026-09-28_t170-v41-build.md`. **Acceptance §8 ②–④ (validate-only + pilot 25/entity + admin duyệt) còn NỢ** — chờ GROQ key chạy VPS (xem T189).
