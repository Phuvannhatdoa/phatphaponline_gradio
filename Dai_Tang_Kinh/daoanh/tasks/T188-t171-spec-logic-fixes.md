---
id: T188
title: "T171 SPEC logic fixes — 4 P0 + 6 P1 + 5 P2 sửa mâu thuẫn SPEC/pointer (docs-only)"
module: Editorial / Person Identity
priority: high
status: done
owner: claudecode
depends_on: [T171]
created: 2026-09-28
updated: 2026-09-28
plan_approved_at: "2026-09-28 (Admin: 'Đồng ý build, hãy lưu logs, gitcommit và update các thông tin của các task mới vào các .md files tương ứng. Bảo đảm mọi bugs khi fix đều có thể commit back về version trước đó 1 cách thuận tiện. Gọi pipip khi done')"
done_when: |
  (P0-1) §5 SELECT: LEFT JOIN name_vi_map blind → subquery dedupe deterministic 1 row/dila_id
         (ROW_NUMBER ưu tiên verified>reviewed>approved_at mới nhất) + COUNT(DISTINCT p.id)
         — hết mâu thuẫn §5 ↔ §14.3 (51 dup dila_id).
  (P0-2) §3.2: bỏ uq_pna (person_id, name_value, name_role) → uq_pna_norm(person_id,
         normalized_value) + uq_pna_display partial 1 display/person — khớp §14.1.
  (P0-3) §3.2 enum name_role hợp nhất §14.2 (thêm primary_han_name|han_viet_reading|
         legacy_name_unverified|common_name) — endpoint validate không reject data mẫu.
  (P0-4) Display precedence chốt 1 công thức §5.2/§5.3/§5.5 inline + §7.1/§7.2/§14.5/
         done_when: strong = name_vi_final CHỈ KHI standard_status ∈ {reviewed, verified},
         còn lại strong = legacy + badge.
  (P1-1) §4 đánh lại 6.1–6.6 cờ init / 6.7 write-validate / 6.8 upsert guard; bỏ rule 4 dead
         (chứng minh ⊂6.2); mọi tham chiếu "6.1–6.8"/"rule 6.x" nhất quán.
  (P1-2) Rule monogram 6.6 (thay lời hứa §2 #7) — hanviet_fallback + custom_hanviet_override,
         skip khi map <50% ký tự name_zh, không AI/API.
  (P1-3) §6 person/<id>/name_vi conditional: KHÔNG overwrite name_vi_final đã duyệt — chỉ
         mirror alias legacy_api + note; không tự set reviewed.
  (P1-4) §8 sửa câu test mơ hồ "80+ không fire rule cũ" (56–80 mới-only · 81+ cả hai);
         fixture A000004/A000027 → chỉ Phase 1 re-verify.
  (P1-5) §12 soft-dep T172 + test skip khi chưa seed charwise; §14.6 #2 skip case Nhất Hành.
  (P1-6) Line refs thật (Phase 0 verify code): search 8201/8202 · namevi_map_update 13926
         sync 13974 · POST name_vi 18308 sync 18326 · glossary 17213 · stats 8329.
  (P2-1) Cột normalized_ascii (search không dấu, KHÔNG unique) trong §3.2 + §5 Search +
         §14.1 + acceptance ④ + test 14.6 #6.
  (P2-2) Revert: export person_name_alias → data/backups/t171_alias_<ts>.json TRƯỚC DROP
         (§3.3 + §11).
  (P2-3) Rule 6.4 nguồn birth_year/death_year = COALESCE(name_vi_map, people) — verify 2 bảng
         đều có (Phase 0).
  (P2-4) Seed is_display_name rule (§14.4): mirror legacy set display khi chưa có; đổi display
         = 1 transaction.
  (P2-5) Acceptance thêm ⑩ stats by_name_status 4 key khớp filter.
  Pointer T171-person-name-standard.md đồng bộ toàn bộ · frontmatter cả 2 file updated
  2026-09-28 + amended_by T188 · tasktodo + ROLLBACK + session + dashboard regen.
  Commit docs revert tiện 1 lệnh git revert --no-edit <sha>.
---

# T188 — T171 SPEC logic fixes (docs-only)

## Bối cảnh

Admin yêu cầu "check và xác nhận vấn đề sau đúng logic chưa" trên 2 file
`docs/Mimo-Flash/T171-person-name-standard-SPEC.md` (298 dòng) +
`T171-person-name-standard.md` (pointer, 42 dòng) → review phát hiện **4 mâu thuẫn P0 +
6 P1 + 5 P2**, chủ yếu do addendum §14 (ABSORB "Gộp nhiều tên về một nhân vật") chồng lên
§3–§5 mà không cập nhật body. Admin phê chuẩn toàn bộ đề xuất (mặc định 3 điểm: display
precedence, normalized_ascii, monogram rule).

**Phạm vi:** docs-only — 0 code/0 DB. Số task = **T188** (tiếp T187; tiền lệ tương tự:
T184 sửa SPEC T169, T182 sửa PLAN T168).

## Phase 0 — Verify thật (read-only, trước khi sửa)

| Fact | Kết quả |
|------|---------|
| `pipip` | = `npm run pipeline` (xác nhận session 2026-09-27_t167-orphan-cleanup.md) |
| `api_dila_persons_search` | route app.py:**8201** / def **8202** (SPEC cũ ~7996 drift) |
| `admin_namevi_map_update` | def **13926**, sync `people.name_vi` **13974** (cũ 13112/13154) |
| `POST admin/person/<id>/name_vi` | route **18308**, sync **18326** (cũ 17505/17523) |
| `_glossary_resolver` | **17213** (cũ 16518) · stats route **8329** (cũ ~8104) |
| `birth_year`/`death_year` | CẢ `people` VÀ `name_vi_map` đều có (rule 6.4 → COALESCE) |
| Bảng Hán-Việt (rule monogram) | `hanviet_fallback (ch,hv)` + `custom_hanviet_override (char,hanviet)` CÓ THẬT → 6.6 khả thi |
| Directive gốc §5.2/§5.5 | KHÔNG tồn tại file trong docs/ (grep) → inline vào SPEC |

## Việc đã làm (15 sửa)

### P0 (4 mâu thuẫn)

| # | Vị trí | Mâu thuẫn | Sửa |
|---|--------|-----------|-----|
| P0-1 | §5 SELECT ↔ §14.3 | §5 `LEFT JOIN name_vi_map` blind vs §14.3 "KHÔNG join — 51 dup `dila_id`" → fan-out sai phân trang/CSV, `name_vi_final` arbitrary | Subquery dedupe `ROW_NUMBER() OVER (PARTITION BY dila_id ORDER BY verified>reviewed>approved_at DESC)` + `COUNT(DISTINCT p.id)` + fallback GROUP BY cho engine <3.25 |
| P0-2 | §3.2 ↔ §14.1 | `uq_pna(person_id, name_value, name_role)` (cho phép tên khác role) vs `UNIQUE(person_id, normalized_value)` (cấm) | Bỏ `uq_pna` → `uq_pna_norm` + `uq_pna_display` partial; 4 index khi revert khớp §3.3 |
| P0-3 | §3.2 ↔ §14.2 | Enum thiếu `primary_han_name`/`han_viet_reading`/`legacy_name_unverified`/`common_name` → validate reject chính data mẫu | Hợp nhất enum vào §3.2 (nguồn duy nhất); task chưa code nên không có data cũ |
| P0-4 | §5/§7.2 ↔ §14.5 | "standard luôn strong" (kể cả `auto`) vs "display mặc định = legacy" → 2 UI khác nhau với ~46.711 row có `name_vi_final` | Chốt: strong = standard **CHỈ KHI** `reviewed/verified` — inline §5.2 render + §5.3 badge + §5.5 CSS; áp §7.1/§7.2/§14.5/done_when |

### P1 (6)

| # | Sửa |
|---|-----|
| P1-1 | §4 đánh lại 6.1–6.6 (cờ init) · 6.7 (write-validate — không thể fire lúc init, cột mới NULL) · 6.8 (guard output `auto`, không tính "trúng→needs_review") · **bỏ rule cũ #4** với chứng minh ⊂6.2 |
| P1-2 | Rule 6.6 monogram thay lời hứa §2 #7 (bảng Hán-Việt có thật, skip <50% map) |
| P1-3 | §6 `person/<id>/name_vi` conditional — không overwrite `name_vi_final` đã duyệt (trước: ghi đè + set `reviewed` = phá chuẩn); `admin_namevi_map_update` giữ nguyên (curated, intended) |
| P1-4 | §8 test "chuỗi 76 chars fire, 80+ không fire rule cũ" → "56–80 mới-only · 81+ cả hai"; fixture A000004/A000027 → chỉ re-verify Phase 1 |
| P1-5 | §12 soft-dep T172 + §14.6 #2 skip case `Nhất Hành` khi chưa seed |
| P1-6 | Line refs thật 5 vị trí (bảng Phase 0) + inline §5.2/§5.5 (directive không có file) |

### P2 (5)

| # | Sửa |
|---|-----|
| P2-1 | `normalized_ascii` (search không dấu, không unique) — §3.2 + §5 Search + §14.1 + acceptance ④ + test #6 |
| P2-2 | `--revert` export alias JSON trước DROP (§3.3 + §11) |
| P2-3 | Rule 6.4 nguồn `COALESCE(m.birth_year, p.birth_year)` — verify cả 2 bảng |
| P2-4 | Seed `is_display_name` (§14.4): mirror khi chưa có display; đổi display = 1 transaction |
| P2-5 | Acceptance thêm ⑩ stats `by_name_status` |

## Files đổi

| File | Sửa |
|------|-----|
| `docs/Mimo-Flash/T171-person-name-standard-SPEC.md` | ~20 điểm (frontmatter + banner + §2/§3/§4/§5(+5.2/5.3/5.5)/§6/§7/§8/§9/§11/§12/§13/§14) |
| `docs/Mimo-Flash/T171-person-name-standard.md` | frontmatter + banner + 8 bullet đồng bộ |
| `tasks/T188-t171-spec-logic-fixes.md` | mới (file này) |
| `docs/sessions/2026-09-28_t188-t171-spec-logic-fixes.md` | session log |
| `docs/tasktodo.md` · `docs/ROLLBACK.md` | registry + revert row |
| `data/progress_data.json` | regen dashboard |

## Verify

- [x] Đối chiếu lại 2 file sau sửa: 0 mâu thuẫn §3/§4/§5 ↔ §14 · đánh số 6.1–6.8 nhất quán (grep 2026-09-28: `uq_pna(` cũ chỉ còn dòng "THAY", enum hợp nhất, line refs 8201/13926/18308, precedence P0-4 nhất quán §5.2/§7.1/§14.5/done_when)
- [x] `python scripts/build_progress_data.py` → JSON có T188 (`in_progress` → sau đó `done`; 106 task, done=81)
- [x] `npm run pipeline` (pipip) PASS — log đầy đủ `docs/sessions/2026-09-28_t188-pipeline.log`; mọi khâu guard→e2e PASS, chỉ `e2e:runtime` EPERM pre-existing (đã ghi nhận từ T169/T170)

## Revert

- **1 lệnh:** `git revert --no-edit 89b9936b647a1ddf6108188f2c755ee1f6dbe089 11758a056751e891813f721b7bf26393623a82e2` (2-commit docs-only — hash-fill trước rồi pass chính) — khôi phục tasktodo + ROLLBACK + task + session + progress_data.
- Cấm `cp *.bak` · cấm `reset --hard`. Chưa build code/DB nên không có script revert.
