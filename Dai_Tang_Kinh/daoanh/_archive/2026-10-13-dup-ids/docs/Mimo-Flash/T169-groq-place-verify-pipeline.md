---
id: T169
title: "Robust Batch Verification Pipeline (Groq Qwen vs SQLite) — Thẩm định địa danh DILA"
module: Editorial / LLM Translation
priority: high
status: ready-for-dev
owner: claudecode
depends_on: []
created: 2026-09-25
updated: 2026-09-25
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: Đồng ý build · Chốt A side-car + sync 2 bảng)"
done_when: |
  Side-car place_groq_audit --apply/--revert; script verify_dila_places_groq.py batch 25
  trên data/lineage.db; classify 3 fixture PASS; flush batch cuối; API GET/PUT
  place-groq-review; UI place_update.html 2 cột + filter TOP; admin edit sync
  places_pending.name_vi + namevi_map_places.name_vi; npm run pipeline PASS.
---

# T169 — Task (pointer)

**SPEC đầy đủ:** [`docs/Mimo-Flash/T169-groq-place-verify-pipeline-SPEC.md`](T169-groq-place-verify-pipeline-SPEC.md)

- **Quyết định Admin:** (A) side-car `place_groq_audit` PK `places_dila.id` · (2) edit sync 2 bảng `places_pending.name_vi` + `namevi_map_places.name_vi` cùng transaction.
- **P0/P1 review:** 6 P0 (path/table/column/id-NULL/scope/key) + 9 P1 (POLYPHONIC R_dict≠R_groq · taxonomy word-boundary · flush batch cuối · api_error · enum+approved_dict · json_object fallback · token window 60s · 3 fixture → unit test) — xem SPEC §2–§3.
- **Absorb v4.1 → T170:** COALESCE · batch schema failure · validate-only · pilot 25 · strict Sanskrit — tasktodo T170 · SPEC T169 giữ nguyên.
- **Phases:** 1 migrate → 2 classify+test → 3 script+smoke → 4 API → 5 UI → 6 pipeline. Session: `docs/sessions/2026-09-25_t169-groq-place-verify-plan.md`.
- **Revert:** `git revert --no-edit b53bf38` (docs) · code sau: migrate `--revert` DROP side-car.
