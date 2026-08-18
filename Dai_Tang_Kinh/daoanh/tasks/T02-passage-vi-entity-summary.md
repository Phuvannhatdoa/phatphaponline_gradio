---
id: T02
title: Passage_VI + entity summary API (LLM)
module: CBETA
priority: high
status: done
depends_on: []
created: 2026-07-29
updated: 2026-08-18
done_when: GET /daoanh/api/entity/{id}/passages trả count > 0 + endpoint summary trả tóm tắt tiếng Việt
---

# T02 — Passage_VI + entity summary API (CBETA)

## Mục tiêu
`/entity/PL000000023255/passages` trả `count=0`. Cần import thêm CBETA texts, build `PASSAGE_VI` translations, entity summary API via LLM (Khoá 1 + Khoá 5 phase 2+).

## Cách tiếp cận
- Kiểm tra dữ liệu CBETA hiện có trong cbeta.db.
- Import thêm texts nếu cần.
- Xây bảng `PASSAGE_VI(passage_id, vi_text, status, reviewer, ...)`.
- Endpoint `GET /daoanh/api/entity/{id}/summary` dùng LLM (bio/note DILA + passages liên quan).

## Blockers
- Gemini API key (`AIzaSy...ukiE`) bị Google deactivate do bị phát hiện trong code. Cần user tạo key mới và đặt vào `.env` hoặc secret store. Key mới cần update trong `app.py` lines 1413, 1453, 3672, 4561 (tìm `GEMINI_KEY =`).
- 14/46 passages đã có `vi_summary_clean` (copy từ vi_summary). 32 còn lại chờ key mới.

## Acceptance criteria (checklist)
- [ ] Kiểm tra & import CBETA texts thiếu
- [ ] Bảng PASSAGE_VI tạo & populate
- [ ] passages trả count > 0 với raw_text + vi_text
- [ ] Entity summary endpoint trả tóm tắt tiếng Việt
