---
id: T511
title: "CLAUDE.md — bỏ số cứng, trỏ tới REALITY_CHECK"
module: Docs
priority: p3
status: pending
created: 2026-10-31
updated: 2026-10-31
owner: unassigned
parent: tasks/T322-docs-cap-nhat-reality-check-plan.md
depends_on: [T322]
done_when: |
  CLAUDE.md mục Database không còn ghi số cứng (1.4GB, 156 bảng, 313 route, 14 nguồn, 447K
  claims) mà trỏ thẳng tới docs/integration/REALITY_CHECK.md làm nguồn sự thật duy nhất.
  Commit hẹp, chỉ đổi đúng đoạn số liệu này, dựng từ HEAD blob (AGENTS §17) để không nuốt diff
  CodeGraph của session khác đang chạy song song. Admin xác nhận DONE.
revert: |
  git revert <sha-commit-này> (docs-only, 0 DB). Nếu cần khôi phục nhanh không dùng git: backup
  CLAUDE.md.bak-before-t511 tại docs/sessions/<ngày làm>/ trước khi sửa.
outcome: >
  2026-10-31: tạo task theo quyết định Admin (họp T322) — chọn phương án B cho CLAUDE.md, làm
  thành task riêng, CHỈ làm sau khi T322 đã DONE. Chưa bắt đầu.
---

# T511 — CLAUDE.md: bỏ số cứng, trỏ tới REALITY_CHECK

## 1. Bối cảnh

`CLAUDE.md` mục "Database" đang ghi số cứng lỗi thời (DB 1.4GB, 156 bảng; số liệu đo
2026-10-02: 313 routes, 14 nguồn, 447K claims) — các số này đã đổi theo T322 (DB mới đo
1.825.574.912 bytes/217 bảng/16 data_sources/437-448 route) và sẽ tiếp tục đổi theo thời gian,
nên ghi cứng trong CLAUDE.md dễ lạc hậu lại.

**Quyết định Admin (họp T322, 2026-10-31):** chọn phương án **B** — bỏ số cứng trong
CLAUDE.md, thay bằng câu trỏ tới `docs/integration/REALITY_CHECK.md` làm nguồn sự thật duy
nhất. Làm thành **task riêng** (task này, T511), thực hiện **SAU KHI T322 đã DONE** — không
làm song song, không làm trước.

## 2. Mục tiêu

Sửa mục "Database" trong `CLAUDE.md` (hiện có dòng:
`data/lineage.db — SQLite 1.4GB, 156 tables. ... Số liệu thực tế (đo 2026-10-02): 313 routes,
14 nguồn trong data_sources, 447K claims.`) thành câu ngắn trỏ tới
`docs/integration/REALITY_CHECK.md`, không nêu số cụ thể nào trong CLAUDE.md nữa.

## 3. Điều kiện bắt buộc trước khi làm

- **Chỉ bắt đầu sau khi task T322 đã chuyển trạng thái `done`** (Admin xác nhận DONE).
  Không làm trước, không làm song song với T322 đang mở.
- **Commit hẹp**: chỉ đổi đúng đoạn số liệu Database trong CLAUDE.md, không đụng đoạn khác.
- **Dựng commit từ HEAD blob (AGENTS.md §17)**: dùng `git show HEAD:<path>` để lấy bản gốc,
  sửa trên bản đó, rồi `git hash-object -w` + `git update-index --add --cacheinfo` — KHÔNG
  dùng `git add` trên cây thư mục (`git add -- docs tasks` kiểu đó) vì sẽ nuốt luôn diff
  CodeGraph/WIP của session khác đang chạy song song trên cùng worktree.

## 4. Không làm trong task này

- Không sửa khi T322 chưa DONE.
- Không dùng `git add -A`/`git add .` hoặc `git add` trên thư mục.
- Không đổi nội dung nào khác ngoài đoạn số liệu Database.

## 5. Các bước

- [ ] **Bước 0 —** xác nhận T322 đã `status: done` trong tasktodo.md trước khi bắt đầu.
- [ ] **Bước 1 —** backup CLAUDE.md vào docs/sessions/<ngày làm>/CLAUDE.md.bak-before-t511.
- [ ] **Bước 2 —** sửa đoạn số liệu Database, trỏ tới REALITY_CHECK.md.
- [ ] **Bước 3 —** commit hẹp theo đúng quy trình HEAD blob (AGENTS §17).
- [ ] **Bước 4 —** Admin xác nhận DONE.
