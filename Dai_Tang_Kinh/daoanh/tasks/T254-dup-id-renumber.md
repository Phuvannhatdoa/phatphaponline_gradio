---
id: T254
title: "Sửa 3 ID trùng có sẵn — đổi số theo AGENTS §16 (T188/T237/T238)"
module: Quản trị / Repo hygiene
priority: high
status: done
created: 2026-10-06
updated: 2026-10-06
owner: opencode
depends_on: []
plan_approved_at: "2026-10-06 (Admin chốt P0-1 = (a) cho T253; blocker pipeline dup:ids cần xử để mở Phase 1)"
done_when: >
  `npm run dup:ids` PASS (exit 0) — hết 3 ID trùng; 3 file đổi số có `former_ids`;
  tham chiếu trong repo đã cập nhật; `npm run pipeline` chạy qua bước dup:ids;
  ghi session log + tasktodo + ROLLBACK row.
revert: "git revert --no-edit <sha> — rename 3 file về tên cũ, khôi phục id/frontmatter/tham chiếu (docs-only, 0 code, 0 DB)."
former_ids: []
---

# T254 — Sửa 3 ID trùng có sẵn (blocker pipeline)

## 1. Vấn đề

`npm run dup:ids` FAIL từ trước khi T253 tồn tại (3 ID trùng thật, chặn
`npm run pipeline` ở bước 2 — AGENTS §13/§16):

```text
T188: tasks/T188-t171-spec-logic-fixes.md  ↔  docs/integration/T188-canonical-reference-integration.md
T237: tasks/T237-cbeta-corpus-search-reader.md  ↔  tasks/T237-gate-vpa-admin-confirmed-only.md
T238: tasks/T238-cbeta-text-browser-toc.md  ↔  tasks/T238-reject-ttl-mismatch-button.md
```

## 2. Phân tích đổi số theo AGENTS §16 (footprint nhỏ nhất)

Tiêu chí: (1) status kết thúc · (2) ít tham chiếu · (3) không có docs/plans|reports kèm ·
(4) **không** được `docs/tasktodo.md` công bố.

| Cặp | Giữ ID (không đổi) | Đổi số | Lý do |
|---|---|---|---|
| T188 | `tasks/T188-t171-spec-logic-fixes` (done, **nhiều tham chiếu**: tasktodo đã công bố, 2 row ROLLBACK có sha, `amended_by` X-T171, `depends_on` T190/T192) | `docs/integration/T188-canonical-reference-integration` → **T255** | Bên đổi: chỉ 2 tham chiếu (T189, tự nó), không tasktodo, không ROLLBACK/session. **Không sửa ROLLBACK/tasktodo lịch sử** (sha revert gắn với ID cũ). |
| T237 | `tasks/T237-cbeta-corpus-search-reader` (done, **công bố tasktodo**, `agents/SESSION.md`, test `test_t237_cbeta_corpus_search.py`) | `tasks/T237-gate-vpa-admin-confirmed-only` → **T256** | Bên đổi: 3 tham chiếu (T239 related, T257 related+text), không tasktodo. |
| T238 | `tasks/T238-cbeta-text-browser-toc` (done, **công bố tasktodo**, `agents/SESSION.md`, test `test_t238_cbeta_text_browser.py`) | `tasks/T238-reject-ttl-mismatch-button` → **T257** | Bên đổi: 3 tham chiếu (T239/T240 related, T257 tự), không tasktodo. |

> Ghi chú tiêu chí (1): cặp T188 bên `t171-spec-logic-fixes` mới `status: done` nhưng
> footprint tổng lớn hơn hẳn (tasktodo + ROLLBACK + amended_by) — ưu tiên tổng footprint
> như tiêu đề §16, **không** đụng lịch sử công bố/revert.

## 3. Thay đổi (docs-only)

| File | Thao tác |
|---|---|
| `docs/integration/T255-canonical-reference-integration.md` | rename từ `T188-…` + `id: T255` + `former_ids: [T188]` + sửa heading/bullet/revert |
| `tasks/T256-gate-vpa-admin-confirmed-only.md` | rename từ `T237-…` + `id: T256` + `former_ids: [T237]` |
| `tasks/T257-reject-ttl-mismatch-button.md` | rename từ `T238-…` + `id: T257` + `former_ids: [T238]` + `related: [T256]` + "Gate T256/T257" |
| `docs/integration/T189-viphu-tu-ca-cuu-tri.md` | ref lộ trình: `T188 (Canonical…)` → `T255` |
| `tasks/T239-xcm-tab-namevimap.md` | `related: [T237, T238]` → `[T256, T257]` (domain namevimap) |
| `tasks/T240-xcm-rejected-clickable.md` | `related: [T238, T239]` → `[T257, T239]` |
| `tasks/T253-person-import-phase0-audit.md` | ghi chú "đã sửa qua T254" tại §6 |
| report Cline §8 + session T253 §4 | ghi chú đã sửa qua T254 |

**Không đổi:** test `test_t237_cbeta_corpus_search.py` / `test_t238_cbeta_text_browser.py`
(thuộc bên giữ ID), mọi entry tasktodo/ROLLBACK lịch sử, mọi tham chiếu prose tới
`T188-t171-spec-logic-fixes`.

## 4. Acceptance

- [ ] `npm run dup:ids` → **exit 0** (không còn dòng `[FAIL]`)
- [ ] `npm run guard` + `npm run lint` PASS
- [ ] grep `T255|T256|T257` ra đúng file mới; `former_ids` có mặt
- [ ] `npm run pipeline` chạy **qua** bước dup:ids

## 5. Revert

`git revert --no-edit <sha>` — rename về tên cũ + khôi phục frontmatter/tham chiếu
(docs-only, 0 code, 0 DB — không mất dữ liệu).
