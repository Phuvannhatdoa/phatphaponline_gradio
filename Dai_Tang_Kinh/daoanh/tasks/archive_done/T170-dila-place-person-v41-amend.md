---
id: T170-dila-place-person-v41-amend
title: "T170 AMEND — Re-check premise sau T169-BUILD (docs-only, 0 code/0 DB): sửa T170 SPEC+pointer cho đúng hiện trạng T169 đã build"
module: Editorial / LLM Translation
priority: high
status: done
owner: claudecode
depends_on: [T169-place-groq-audit-build]
created: 2026-09-28
updated: 2026-09-28
done_at: "2026-09-28 (Amend docs T170 SPEC+pointer theo hiện trạng T169 build; regression verify DB + pipeline PASS; commit 2-pass hash-fill)"
plan_approved_at: "2026-09-28 (Admin: 'Đồng ý build, hãy lưu logs, gitcommit... Gọi pipip khi done' — sau khi xác nhận premise 'T170 build mới từ zero' sai do T169 đã build)"
done_when: |
  Soi 2 file T170 (SPEC + pointer) so hiện trạng T169-BUILD → liệt kê S1–S10 path đúng/sai;
  amend SPEC tại chỗ (banner re-check + §2 P0-5 + §3.1 #8 行 absorbed + §3bis R1/R5 + §4 migrate person-only
  + §5 REFACTOR/EXTEND + §6 base tests + §7 place đã build + §9/§10/§11 + done_when);
  pointer updated; task + session + tasktodo + ROLLBACK + dashboard regen;
  npm run pipeline PASS; commit 2-pass hash-fill 61b1c0afe2637d2467525745c86dfea5cb0f1843;
  Revert 1 lệnh: git revert --no-edit 61b1c0afe2637d2467525745c86dfea5cb0f1843 (docs-only).
---