---
id: T171
title: "Chuẩn Hóa Tên Nhân Vật DILA — Standard Name Layer trên name_vi_map (SSOT)"
module: Editorial / Person Identity
priority: high
status: ready-for-dev
owner: claudecode
depends_on: [T166, T170]
created: 2026-09-25
updated: 2026-09-28
designed_by: mimo-flash
handoff_to: Claude Code Agent
plan_approved_at: "2026-09-25 (Admin: (1) A · (2) SSOT name_vi_map · (3) tạo T171) + 2026-09-28 (Admin approve T188 amend SPEC)"
amended_by: "T188 (2026-09-28) — 4 P0 + P1/P2 logic fixes, đồng bộ pointer này" + "T190 (2026-09-28 — docs-only: bịt 2 lỗ hổng logic verified-final NULL + stats phủ person không row map)"
done_when: |
  name_vi_map +4 cột + person_name_alias additive (backup/idempotent/--revert; revert export alias JSON);
  index ưu tiên name_vi_standard CHỈ khi reviewed/verified (còn lại legacy) + badge + filter name_status;
  search 4 nguồn + không dấu (normalized_ascii); CSV +8 / JSON names{} compat;
  person.html Tên và định danh + edit validate; dual-write 2 endpoint mirror people.name_vi
  KHÔNG overwrite name_vi_final đã duyệt; fixture A000006/7/8 PASS;
  COMPLETION_REPORT; npm run pipeline PASS.
---

# T171 — Task (pointer)

**SPEC đầy đủ:** [`docs/Mimo-Flash/T171-person-name-standard-SPEC.md`](T171-person-name-standard-SPEC.md)

> **[2026-09-28 · T188] AMEND** — Admin phê chuẩn sửa **4 P0 + 6 P1 + 5 P2** logic (docs-only):
> P0-1 §5 JOIN dedupe 51 dup · P0-2 `uq_pna`→`uq_pna_norm`+`uq_pna_display` · P0-3 enum `name_role`
> hợp nhất §14.2 · P0-4 display precedence (standard strong **chỉ khi** reviewed/verified) · P1: bỏ
> rule 4 dead, đánh lại 6.1–6.6/6.7/6.8, monogram 6.6, §6 conditional, line refs thật, soft-dep T172 ·
> P2: `normalized_ascii`, revert export alias JSON, seed `is_display_name`, stats acceptance.
> Chi tiết: `tasks/T188-t171-spec-logic-fixes.md`.

- **Chốt Admin:** **(1) Phương án A** · **(2) SSOT = `name_vi_map`** (không `person_names` mới đầy đủ) · **(3) T171** · SPEC gộp `IMPLEMENTATION_PLAN.md`.
- **Review → 4 P0 + 5 P1/P2** (2026-09-25; [T188] review lại 2026-09-28 → sửa thêm 4 P0 + 6 P1 + 5 P2, xem banner): ID 7 ký tự (`A000004`…) · 5 vd directive lệch DB (A000008=`Nhất Hàng`…) → **re-verify UI Phase 1** · rule >80 **chết** (0 row) → ngưỡng 55/3×/lặp · trùng 6 bảng tên sẵn → chỉ +4 cột alias-thin · dual-write `person/<id>/name_vi` + `namevi_map_update` · filter `name_status` tách status dịch · Latin-missing 1.555 row · init status deterministic · fixture TEST ONLY tách env — xem SPEC §2.
- **Schema A:** `name_vi_map` +`han_name_normalized/standard_status/standard_source/standard_note` · `person_name_alias` thin · `name_vi_final` = chuẩn · `people.name_vi` = legacy cache.
- **Flag 6.1–6.6** = cờ init (bỏ rule 4 dead ⊂6.2; thêm monogram 6.6 qua `hanviet_fallback`) · **6.7** write-validate · **6.8** upsert guard [T188 đánh lại] · resolver **P0** · T170 Groq → chỉ `needs_review`.
- **UI:** index “Tên Việt chuẩn” + logic §5.2 (đã inline) + CSS §5.5 + filter 5 mức · person.html “Tên và định danh” · **strong = standard CHỈ khi reviewed/verified, còn lại legacy** [T188 P0-4].
- **Phases:** 1 re-verify → 2 migration+test → 3 backend → 4 index UI → 5 detail → 6 export → 7 QA+pipeline → 8 COMPLETION_REPORT. Session: `docs/sessions/2026-09-25_t171-person-name-standard-plan.md`.
- **Revert:** `git revert --no-edit <sha>` · code: `t171_name_standard_migrate.py --revert` (export alias JSON trước DROP) + backup `lineage_t171_*.db`.
- **[2026-09-28 · T190] docs-only (bịt 2 lỗ hổng logic sau T188; Admin "Đồng ý build… Gọi pipip khi done"):** §5.2/§6/rule 6.7 — strong + mirror `people.name_vi` cần `name_vi_final` **non-null** (DB thật chỉ 5.205/46.711 row có final; `verified`+final NULL sẽ render rỗng / xóa display) → `verified ⇒ final non-null` (400, mở rộng 6.7) · filter + stats `by_name_status` phủ **6.905 person (14%)** không row `name_vi_map` qua `COALESCE(NULLIF(m.standard_status,''),'auto')` → hạng auto, tổng 4 key = 48.673. Chi tiết: `tasks/T190-t171-build-docs-correction.md`.

## ABSORB 2026-09-25 — Addendum "Gộp nhiều tên về một nhân vật" → SPEC §14
- **1 person = 1 `people.id` + 1 tiểu sử** — không tạo/sáp nhập record vì tên khác · không xóa legacy vì lệch số Hán tự.
- `person_name_alias` **+2 cột** (`is_searchable`, `source_type`) · **UNIQUE `(person_id, normalized_value)`** · partial unique 1 `is_display_name`/person · **+`normalized_ascii` search không dấu, không unique** [T188 P2] — toàn bộ schema hấp thụ §3.2, enum `name_role` hợp nhất (P0-3).
- **A000008 = 3 name record trên 1 id:** `一行` (DILA) · `Nhất Hành` (charwise T172, `characterwise_mapping`) · legacy `Nhất Hàng` (DB thật — "Đại Huệ Thiền Sư" **không tồn tại local**, T172 Phase 1 re-verify) → `legacy_name_unverified`/`needs_review`, chỉ nâng `verified` khi có citation.
- **Sửa acceptance search:** `一行` (LIKE) → **4 person distinct** (A000008 · A010168 · **A016240 `一行智嚴`** · **A023828 `釋一行`** — DB thật; exact `name_zh='一行'` = 2) [T191] — không gộp; `Nhất Hành`/legacy → đúng 1 `A000008` (sau seed) · `GROUP BY p.id`, không join `name_vi_map` (51 dup `dila_id`).
- **Guard P0:** không path nào INSERT `people` ngoài ETL (test people count before=after) · seed `is_display_name` rule [T188 P2].
- **Dual-write mở rộng:** app.py:**13926** (sync 13974) + **18308** (sync 18326) [T188 line refs] → mirror alias · endpoint name_vi **không overwrite** `name_vi_final` đã duyệt.
- **Display = legacy** (chốt Admin) — [T188 P0-4] chuẩn hóa: strong = `name_vi_final` **chỉ khi** `reviewed/verified`, còn lại legacy; charwise = khối debug T172, nhãn "phiên âm kỹ thuật".
- Soft-dep **T172** (seed `Nhất Hành` — test skip nếu chưa seed) [T188].
- Tests: `tests/test_t171_alias_search.py` (6 cases — +case không dấu [T188]).
