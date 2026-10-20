---
id: T190-t171-build-docs-correction
title: "T190 — T171 build-docs correction (bịt 2 lỗ hổng logic, docs-only 0 code/0 DB): verified-final NULL + stats phủ person không row map"
module: Editorial / Person Identity
priority: high
status: done
owner: claudecode
depends_on: [T171-person-name-standard, T188-t171-spec-logic-fixes]
created: 2026-09-28
updated: 2026-09-28
done_at: "2026-09-28 (docs-only; guard/test/pipeline PASS trừ e2e:runtime EPERM pre-existing; commit 2-pass hash-fill)"
plan_approved_at: "2026-09-28 (Admin: Đồng ý build — phê chuẩn audit 2 file T171 + 2 fix logic đề xuất; lưu logs, gitcommit, update .md, revert tiện lợi, Gọi pipip khi done)"
done_when: |
  D1: §5.2 strong + §6 mirror + rule 6.7 — verified mà name_vi_final NULL bị chặn: strong chỉ khi
      standard_status ∈ {reviewed,verified} VÀ name_vi_final IS NOT NULL; mirror people.name_vi := final
      CHỈ KHI final non-null (không xóa display); endpoint name_standard + 6.7 validate verified ⇒ final non-null (400).
  D2: §5 filter name_status + stats by_name_status phủ 100% person qua COALESCE(NULLIF(m.standard_status,''),'auto')
      → 6.905 person (14%) không row name_vi_map tự rơi hạng auto; tổng 4 key = 48.673; acceptance ⑥/⑩ cập nhật.
  D3: Banner [T190] + amended_by ở SPEC + pointer; task + session + tasktodo + ROLLBACK + dashboard regen.
  Verify: DB read-only (final non-null 5.205 · không-row-map 6.905) · npm run guard/test/pipeline.
  Revert: git revert --no-edit b912ea994e1b571ebbea6fbdc6e2c93e590602fd (docs-only, 0 DB).
---

# T190-t171-build-docs-correction — T171 build-docs correction (2 lỗ hổng logic)

## Bối cảnh

Admin yêu cầu check 2 file `docs/Mimo-Flash/T171-person-name-standard-SPEC.md` + `T171-person-name-standard.md`
(pointer) "xác nhận vấn đề sau đúng logic chưa". Bản worktree hiện tại = bản đã amend **T188** (agent song song,
chưa commit — file task untracked). Audit read-only đối chiếu DB `data/lineage.db` xác nhận **mọi claim số liệu
của T188 đúng** (46.711 row map · 51 dup dila_id · 48.673 people · rule >80 chết 0 row · non-Latin 1.555 · max len 79).

Đồng thời phát hiện **2 lỗ hổng logic còn lại** → sửa docs tại chỗ (đắp trên bản T188):

- **D1 — `verified` mà `name_vi_final` NULL:** rule 6.7 chỉ bắt `standard_source`, không bắt `name_vi_final`. DB thật:
  chỉ **5.205/46.711** row có `name_vi_final`. Nếu 1 row được set `verified` mà final NULL thì §5.2 strong render
  rỗng và §6 mirror `people.name_vi := NULL` **xóa luôn display**. → strong + mirror yêu cầu `name_vi_final` non-null;
  validate `status=verified ⇒ final non-null (400)`.
- **D2 — Filter/stats không phủ person không row map:** **6.905/48.673 person (14%)** không có row `name_vi_map`
  → `standard_status` NULL, không nằm trong 4 key của `by_name_status` (mặc dù filter "Tất cả" vẫn OK). → dùng
  `COALESCE(NULLIF(m.standard_status,''),'auto')` ⇒ họ gộp hạng `auto`, tổng 4 key = 48.673, không cần upsert ồ ạt.

## Thay đổi (docs-only)

| # | File | Sửa |
|---|------|-----|
| D1 | SPEC §5.2 · §6 endpoint `name_standard` · rule 6.7 · acceptance ⑥ | verified mà `name_vi_final` NULL → chặn: strong CHỈ khi final non-null; mirror chỉ khi final non-null; validate `verified ⇒ final non-null` (400) |
| D2 | SPEC §5 Filter · acceptance ⑩ · pointer bullet | filter + `by_name_status` dùng `COALESCE(NULLIF(standard_status,''),'auto')` → 6.905 person (14%) hạng auto; tổng 48.673 |
| Docs | SPEC banner `[2026-09-28 · T190]` + `amended_by` · pointer `amended_by` + bullet · `tasks/T190-...md` · session | log + commit 2-pass hash-fill |

## Việc đã làm

1. **SPEC**: banner `[T190]` mới + `amended_by` ghi T190 → §5.2 strong thêm `∧ name_vi_final IS NOT NULL`
   (+ meta cảnh báo khi verified–final NULL) → §6 `name_standard` validate thêm final non-null (400) + mirror
   chỉ khi final non-null → rule 6.7 mở rộng bắt final NULL → §5 Filter + acceptance ⑩ dùng COALESCE→auto →
   acceptance ⑥ thêm "verified thiếu final = 400".
2. **Pointer**: `amended_by` + bullet `[T190]` (tóm tắt D1/D2 + số liệu DB).
3. **Docs**: task `tasks/T190-...md` · session `docs/sessions/2026-09-28_t190-t171-build-docs-correction.md` ·
   tasktodo top entry · ROLLBACK row.
4. **Dashboard**: regen `scripts/build_progress_data.py` → `data/progress_data.json`.

> ⚠️ Tình huống hunk-granular/FS (giống T189): SPEC/pointer worktree = bản amend **T188 chưa commit**. Fix T190 nằm
> trong §5.2/§6 do T188 inline (HEAD pre-T188 không có) → **không reconstruct từ HEAD**; commit T190 đưa nguyên bản
> worktree LF-normalized tại path HEAD (bare). T188 agent commit sau sẽ đắp trên đó không xung đột.

## Verify

- DB read-only: 48.673 people · 46.711 map · 51 dup · `name_vi_final` non-null = 5.205 · people không row map = 6.905.
- `npm run guard` PASS · `npm run test` PASS · `npm run pipeline` PASS trừ `e2e:runtime` EPERM pre-existing.
- Docs-only — không chạm code/DB; T171 vẫn `ready-for-dev` (build code chưa bắt đầu).

## Revert

- `git revert --no-edit b912ea994e1b571ebbea6fbdc6e2c93e590602fd` — docs-only, 0 DB. Khôi phục SPEC/pointer về bản T188-amend biên tập
  trên worktree (nội dung T188 vẫn giữ vì commit T190 đưa nguyên bản worktree — revert chỉ quay lại trạng thái
  HEAD pre-T190, bản T188 vẫn còn nguyên trên đĩa và sẽ được T188 agent commit riêng).

## Còn lại (không thuộc T190)

- T188-t171-spec-logic-fixes: agent song song chưa commit (task file untracked) — họ đảm nhận.
- Build code T171 (migration/endpoint/UI/tests) = task chain T171: SPEC vẫn `ready-for-dev`.