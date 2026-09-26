---
id: T170
title: "Hardened v4.1 Verify Pipeline — Place + Person (2 side-car) — Chuẩn hóa danh xưng tu sĩ DILA"
module: Editorial / LLM Translation
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T169]
created: 2026-09-25
updated: 2026-09-25
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
- **Revert:** `git revert --no-edit <sha>` · code sau: `scripts/t170_entity_groq_audit_migrate.py --revert --entity all`.
