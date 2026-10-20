id: T393
title: "Bàn giao FoJin Local Test Runbook + make_vn_drafts.py spec"
status: done
date: 2026-10-15
tags: [fojin, local-test, runbook, demo]
former_ids: []
---

# T393 — Bàn giao FoJin Local Test Runbook

## Mục tiêu
Tạo runbook tự chứa `docs/FOJIN-TEST-RUNBOOK.md` để agent Claude Code khác có thể dựng môi trường FoJin LOCAL, nạp 10 kinh CBETA + 10 kinh Việt, kiểm chứng 6 tiêu chí, dọn dẹp — mà không cần hỏi thêm.

## Phạm vi
- Chỉ tài liệu + đặc tả script; **chưa thực thi** (môi trường local chưa cài Docker).
- Không đụng repo FoJin, không đụng VPS, không đụng DB/data của Đạo Ảnh.

## Deliverables
- `docs/FOJIN-TEST-RUNBOOK.md` (runbook chính, 15 mục, toàn văn)
- Đặc tả §8.7 script `make_vn_drafts.py` (sinh nháp kinh tiếng Việt)
- Mô tả rollback/dọn dẹp riêng môi trường test

## Kiểm chứng (tài liệu)
- Guard PASS trên repo root visjs-app
- `dup:ids` baseline giữ nguyên (1 ID trùng T274, đã biết)
- Không thêm bất kỳ file nào ngoài `docs/`, không stage WIP cũ

## Commit & Revert
- Commit scope: **chỉ** thêm `docs/FOJIN-TEST-RUNBOOK.md` (và tasktodo/rollblack/handoff nếu committed)
- Revert: `git revert --no-edit <sha>` (doc-only, 0 DB, mất 0 dữ liệu)