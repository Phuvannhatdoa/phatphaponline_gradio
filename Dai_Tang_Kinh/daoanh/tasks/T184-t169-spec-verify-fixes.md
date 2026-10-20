---
id: T184
title: "T169 SPEC verify fixes — 8 sửa logic G1–G7 theo Admin duyệt (docs-only)"
module: Editorial / LLM Translation
priority: high
status: done
owner: claudecode
depends_on: [T169]
created: 2026-09-27
updated: 2026-09-27
done_at: "2026-09-27 (SPEC X-T169 sửa 8 điểm + pointer + tasktodo/ROLLBACK/session + dashboard regen + commit docs)"
plan_approved_at: "2026-09-27 (Admin: 'Đồng ý build, hãy lưu logs, gitcommit và update các thông tin... Gọi pipip khi done')"
done_when: |
  (G1) §2.2 Scope batch: SQL thay NOT IN-persist bằng predicate + :cursor memory
       (ORDER BY id LIMIT 25) — không persist cursor (tránh bỏ sót retry api_error);
       reset run → scan lại qua predicate.
  (G2) Ước batch chốt đúng 2.366 (59.150/25) không phải 2.367 — budget ~2,4k (+4%).
  (G3) §5 thêm RPM adaptive: x-ratelimit-remaining ≤5 → sleep 3s, còn lại 2,2s.
  (G4) --force vẫn giữ NOT IN(verified, approved_dict) — không bao giờ chạy lại hàng đã duyệt.
  (G5) §3 P1-1 classify_diff: thứ tự ưu tiên cố định POLYPHONIC → TAXONOMY → PHONETIC → NONE,
       dừng ở nhãn đầu, không ghép nhãn; trụ đa âm = static map inline (0 bảng mới).
  (G6) §6 PUT: 1 transaction 3 bước — audit + places_pending.name_vi + recompute name_vi_norm
       (reuse logic scripts/migrate_name_vi_norm.py) + namevi_map_places.name_vi (UPSERT).
  (G7) §7 UI: filter mặc định needs_review=1 AND diff_type IS NOT NULL AND
       review_status='conflict' + tab "Lỗi API" riêng (api_error).
  Frontmatter SPEC X-T169 updated 2026-09-27 + ghi 3 quyết định Admin.
  Pointer X-T169 cập nhật bullet P0/P1 + updated 2026-09-27.
  tasktodo + ROLLBACK + session + dashboard regen.
  Commit docs (2-pass hash-fill) + revert tiện 1 lệnh git revert --no-edit 3c4907e5d5823b31b20932b816de1ba79184d267.
---

# T184 — T169 SPEC verify fixes (docs-only)

## Bối cảnh

SPEC `docs/Mimo-Flash/X-T169-groq-place-verify-pipeline-SPEC.md` (docs-only, chưa build) được
review 2026-09-27 đối chiếu DB thật `data/lineage.db` + codebase → phát hiện 7 điểm logic
chưa đúng (G1–G7): resume-cursor thiếu ORDER BY, ước batch lệch 1, RPM chạm trần 30, `--force`
có thể chạy lại hàng đã duyệt, thiếu thứ tự ưu tiên classify, PUT thiếu recompute
`name_vi_norm`, UI filter hiện cả api_error/pending.

Admin phê chuẩn đề xuất sửa (3 điểm chốt: P1 cursor-memory, P4 recompute norm, P3 trụ static).

## Việc đã làm (8 sửa — chi tiết done_when)

| # | Vị trí SPEC | Sửa |
|---|-------------|-----|
| G1 | §2.2 | SQL → predicate + `:cursor` memory (ORDER BY id LIMIT 25); bỏ persist cursor; reset scan qua predicate |
| G2 | §2.2 ước lượng | 59.150/25 = **2.366 batch** (không 2.367) · budget ~2,4k request (+4%) |
| G3 | §5 | RPM adaptive: header `x-ratelimit-remaining` ≤5 → sleep 3s; còn lại 2,2s (~27 RPM) |
| G4 | §5 · §2.2 | `--force` vẫn giữ `NOT IN (verified, approved_dict)` — không bao giờ chạy lại hàng đã duyệt |
| G5 | §3 P1-1 | Thứ tự ưu tiên cố định POLYPHONIC → TAXONOMY → PHONETIC → NONE, dừng nhãn đầu; trụ đa âm = static map inline |
| G6 | §6 PUT | 3 bước 1 transaction: audit + `places_pending.name_vi` + **recompute `name_vi_norm`** + `namevi_map_places.name_vi` (UPSERT) |
| G7 | §7 UI | Filter `needs_review=1 AND diff_type IS NOT NULL AND review_status='conflict'` + tab "Lỗi API" |
| — | frontmatter SPEC | updated 2026-09-27 · pointer cập nhật bullet |

## Verify

- `npm run guard` PASS (SSOT repo-root) · pipeline PASS (e2e:runtime EPERM pre-existing).
- `scripts/build_progress_data.py` regen dashboard → `data/progress_data.json` có T184.

## Revert

- **1 lệnh:** `git revert --no-edit 3c4907e5d5823b31b20932b816de1ba79184d267` (docs-only) — khôi phục SPEC X-T169 cũ + docs.
- Cấm `cp *.bak` · cấm `reset --hard`.