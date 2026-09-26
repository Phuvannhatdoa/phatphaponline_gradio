---
id: T171
title: "Chuẩn Hóa Tên Nhân Vật DILA — Standard Name Layer trên name_vi_map (SSOT)"
module: Editorial / Person Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T166, T170]
created: 2026-09-25
updated: 2026-09-25
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: (1) A · (2) SSOT name_vi_map · (3) tạo T171)"
done_when: |
  name_vi_map +4 cột + person_name_alias additive (backup/idempotent/--revert);
  index ưu tiên name_vi_standard + badge + filter name_status; search 4 nguồn;
  CSV +8 / JSON names{} compat; person.html Tên và định danh + edit validate;
  dual-write 2 endpoint mirror people.name_vi; fixture A000006/7/8 PASS;
  COMPLETION_REPORT; npm run pipeline PASS.
---

# T171 — Task (pointer)

**SPEC đầy đủ:** [`docs/Mimo-Flash/T171-person-name-standard-SPEC.md`](T171-person-name-standard-SPEC.md)

- **Chốt Admin:** **(1) Phương án A** · **(2) SSOT = `name_vi_map`** (không `person_names` mới đầy đủ) · **(3) T171** · SPEC gộp `IMPLEMENTATION_PLAN.md`.
- **Review → 4 P0 + 5 P1/P2:** ID 7 ký tự (`A000004`…) · 5 vd directive lệch DB (A000008=`Nhất Hàng`…) → **re-verify UI Phase 1** · rule >80 **chết** (0 row) → ngưỡng 55/3×/lặp · trùng 6 bảng tên sẵn → chỉ +4 cột alias-thin · dual-write `person/<id>/name_vi` + `namevi_map_update` · filter `name_status` tách status dịch · Latin-missing 1.555 row · init status deterministic · fixture TEST ONLY tách env — xem SPEC §2.
- **Schema A:** `name_vi_map` +`han_name_normalized/standard_status/standard_source/standard_note` · `person_name_alias` thin · `name_vi_final` = chuẩn · `people.name_vi` = legacy cache.
- **Flag 6.1–6.8** chỉ cờ · resolver **P0** · T170 Groq → chỉ `needs_review`.
- **UI:** index “Tên Việt chuẩn” + logic §5.2 + CSS §5.5 + filter 5 mức · person.html “Tên và định danh”.
- **Phases:** 1 re-verify → 2 migration+test → 3 backend → 4 index UI → 5 detail → 6 export → 7 QA+pipeline → 8 COMPLETION_REPORT. Session: `docs/sessions/2026-09-25_t171-person-name-standard-plan.md`.
- **Revert:** `git revert --no-edit <sha>` · code: `t171_name_standard_migrate.py --revert` + backup `lineage_t171_*.db`.

## ABSORB 2026-09-25 — Addendum "Gộp nhiều tên về một nhân vật" → SPEC §14
- **1 person = 1 `people.id` + 1 tiểu sử** — không tạo/sáp nhập record vì tên khác · không xóa legacy vì lệch số Hán tự.
- `person_name_alias` **+2 cột** (`is_searchable`, `source_type`) · **UNIQUE `(person_id, normalized_value)`** · partial unique 1 `is_display_name`/person.
- **A000008 = 3 name record trên 1 id:** `一行` (DILA) · `Nhất Hành` (charwise T172, `characterwise_mapping`) · legacy `Nhất Hàng` (DB thật — "Đại Huệ Thiền Sư" **không tồn tại local**, T172 Phase 1 re-verify) → `legacy_name_unverified`/`needs_review`, chỉ nâng `verified` khi có citation.
- **Sửa acceptance search:** `一行` → **2 person distinct** (A000008 + A010168, cùng 唐) — không gộp; `Nhất Hành`/legacy → đúng 1 `A000008` (sau seed) · `GROUP BY p.id`, không join `name_vi_map` (51 dup `dila_id`).
- **Guard P0:** không path nào INSERT `people` ngoài ETL (test people count before=after).
- **Dual-write mở rộng:** app.py:13114 + 17523 → mirror alias.
- **Display = legacy** (chốt Admin); charwise = khối debug T172, nhãn "phiên âm kỹ thuật".
- Tests: `tests/test_t171_alias_search.py` (5 cases).
