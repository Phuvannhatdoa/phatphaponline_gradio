---
id: T375
title: "Gỡ 9 task ID trùng (npm run dup:ids)"
status: done
created: 2026-10-13
updated: 2026-10-19
owner: claude-code (phiên housekeeping 2026-10-13)
plan_approved_at: "2026-10-13 (Admin duyệt qua chat)"
dispatch: approved
done_when: >
  (1) `npm run dup:ids` không còn báo các ID trùng đã xử lý; ID nào còn mơ hồ được liệt kê cho Admin.
  (2) Có bảng ánh xạ cũ → mới (hoặc cũ → nơi lưu trữ) trong file này.
  (3) Không xóa file: bản thừa chuyển vào _archive/ có MANIFEST.
  (4) Commit riêng, revert được bằng `git revert <sha>`.
  (5) Admin xác nhận DONE.
revert: >
  git revert --no-edit f806e912504f3705927bc5a5dafd4df67a08ecc8 (chỉ xoá 13 file .md gốc + sửa checklist
  trong chính file này, 0 code, 0 DB). Revert sẽ phục hồi 13 file gốc (archive ở _archive/2026-10-13-dup-ids/
  vẫn giữ nguyên dù revert hay không).
outcome: >
  2026-10-13: 8/9 ID trùng đã gỡ; T274 để Admin quyết. Nguyên nhân: đợt T222 (2026-10-02) đã đổi số/đổi tên X-,
  nhưng bản cũ bị hồi sinh (restore ea50089 / commit gộp b46f81b) nên trùng lại. Chuyển 13 bản cũ (nội dung cũ hơn
  bản hiện hành) vào _archive/2026-10-13-dup-ids/ + MANIFEST (sha256). `npm run dup:ids`: FAIL 9 → FAIL 1 (T274).
  2026-10-14: Đã xác minh 13 bản archive khớp sha256 với bản gốc rồi xoá 13 file gốc (archive giữ nguyên, không đổi).
  `npm run dup:ids` (daoanh/) chạy lại: vẫn FAIL 1 (chỉ T274, đúng như kỳ vọng). Commit: f806e912504f3705927bc5a5dafd4df67a08ecc8.
  Chờ daoanh-qa + Admin.
  2026-10-19: Admin xác nhận DONE. 8/9 ID trùng đã gỡ; T274 đã gộp thành 1 file (quyết định điều phối phiên
  2026-10-14, xem session log 2026-10-14). `npm run dup:ids` = PASS (EXIT 0).
---

# T375 — Gỡ 9 task ID trùng

## Bối cảnh

Trước khi sửa (`npm run dup:ids`, 2026-10-13): **FAIL 9 ID** — T158, T168, T169, T170, T171,
T177, T206, T215, T274.

## Các bước

- [x] Chạy `npm run dup:ids`, liệt kê 9 ID trùng
- [x] Đối chiếu từng cặp (frontmatter, lịch sử git, diff nội dung)
- [x] Xử lý các cặp rõ ràng; ghi bảng ánh xạ
- [x] Liệt kê cặp mơ hồ cho Admin
- [x] Chạy lại `npm run dup:ids`
- [x] Commit riêng, tiền tố `T375`
- [x] Admin xác nhận DONE (2026-10-19)

## Bảng ánh xạ (cũ → nơi lưu trữ, bản hiện hành giữ nguyên)

| ID trùng | Bản cũ bị hồi sinh (đã chuyển vào `_archive/2026-10-13-dup-ids/<cùng đường dẫn>`) | Bản hiện hành (giữ) |
|---|---|---|
| T158 | `tasks/T158-glossary-resolver-pre-translation-lookup.md` | `tasks/T218-glossary-resolver-pre-translation-lookup.md` (`former_ids: [T158]`); `T158` = `tasks/T158-lineage-consensus.md` |
| T206 | `tasks/T206-pl-corrupt-canonical-name-vi-fix.md` | `tasks/T219-pl-corrupt-canonical-name-vi-fix.md` (`former_ids: [T206]`); `T206` = mojibake |
| T215 | `tasks/T215-vnpa-dila-id-recovery.md`, `docs/Mimo-Flash/T215-VNPA-DILA-ID-RECOVERY-01.md` | `tasks/X-T220-vnpa-dila-id-recovery.md`, `docs/Mimo-Flash/X-T220-…-01.md`; `T215` = self-edges |
| T168 | `docs/Mimo-Flash/T168-rule-resolver-context-compiler-PLAN.md` (pending, cũ) | `docs/Mimo-Flash/X-T168-…-PLAN.md` (superseded); `T168` = `tasks/T168-t165-spec-v2-review-accepted.md` |
| T169 | `docs/Mimo-Flash/T169-groq-place-verify-pipeline{,-SPEC}.md` (ready-for-dev, cũ) | `docs/Mimo-Flash/X-T169-…` (built); `T169` = `tasks/T169-t165-engine-build.md` |
| T170 | `docs/Mimo-Flash/XX-T170-dila-place-person-v41-verify{,-SPEC}.md` | `docs/Mimo-Flash/X-T170-…` (built) |
| T171 | `docs/Mimo-Flash/T171-person-name-standard{,-SPEC}.md` | `docs/Mimo-Flash/X-T171-…` (có sửa đổi T188/T190) |
| T177 | `docs/Mimo-Flash/T177-directive-v2-…-REVIEW.md`, `T177-dynamic-filter-…-v2.md` | `docs/Mimo-Flash/X-T177-…` (T222 đã đổi tên X-T177, commit 4f71b12) |

Không đổi số ID nào (các ID mới T218/T219/T220 đã cấp từ T222). Nội dung bản cũ khác bản hiện hành chỉ ở các dòng
đã được sửa về sau (status/updated/former_ids/fixture) — đã đối chiếu `diff -w` từng cặp.

## Còn lại cho Admin

**T274** — `tasks/T274-vn-lineage-ttl-rule.md` (tạo 10-10, `parent: T270`, 12 tham chiếu) và
`tasks/T274-ttl-rule-design.md` (tạo 10-11, "Option B Implementation", 1 tham chiếu thật). Cả hai `in_progress`.
Bản sau có thể là pha tiếp theo của chính T274 chứ không phải task khác ⇒ mơ hồ, không tự đổi số.
Đề xuất: (a) đổi số `T274-ttl-rule-design` sang ID mới + `former_ids: [T274]` (mặc định theo AGENTS §16), hoặc
(b) gộp làm mục "Bước tiếp" trong `T274-vn-lineage-ttl-rule.md`. Admin chọn.
