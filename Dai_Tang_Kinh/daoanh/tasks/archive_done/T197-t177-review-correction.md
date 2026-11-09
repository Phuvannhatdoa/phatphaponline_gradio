---
id: T197
title: "T177 REVIEW correction — line-refs lệch (app.py 21.232→22.896), P0-1 429 conclusion ngược, fixture 丹霞, số liệu snapshot trôi"
module: Docs / Review Audit
priority: high
status: done
closed_at: "2026-10-02 (verify 8/8 muc done_when; status `blocked` truoc do la CU — chi thieu 1 muc absorb correction log)"
owner: claudecode
depends_on: [T177]
created: 2026-09-30
updated: 2026-09-30
designed_by: claudecode
handoff_to: Admin
plan_approved_at: "2026-09-30 (Admin đồng ý: thêm Correction log, KHÔNG viết lại §1.3 — giữ lịch sử audit)"
done_when: |
  REVIEW.md có §8 "Correction log 2026-09-30" (giữ nguyên §1.3 lịch sử, chỉ sửa kết luận P0-1);
  line-refs 7/7 cập nhật (app.py 22896, style_constitution.py 863);
  P1-1 fixture đổi 天然 → 丹霞 (TERM_DANHA/TERM_DAN_HA);
  P1-2 "8 phần" → "10 phần", tham chiếu 211-234;
  P1-3 thêm mốc đo rendered≥raw + chú thích snapshot trôi;
  B4 15→18, B8 12+3→13+4, dual-hash 1/1900, cache 1900 invalidated, invalidate_all_semantic DELETE ghi rõ;
  absorb doc (X-T177-dynamic-filter-…) có correction log tương ứng;
  tasktodo + ROLLBACK + dashboard regen; guard/lint/test PASS; 0 code/0 DB.
---

# T197 — T177 REVIEW correction (docs-only)

> **Bối cảnh:** Review `X-T177-directive-v2-trie-xml-dualhash-REVIEW.md` viết tại mốc 2026-09-25 (app.py 21.232 dòng). Hiện trạng 2026-09-30: app.py **22.896**, style_constitution.py **863**, DB snapshot đã trôi (rules 119/19.014, cache 1900 invalidated). **P0-1:** §1.3 kết luận "429 chưa từng xảy ra → retry/backoff phòng vệ" **ngược** với D7/task/T178 (429 xảy ra thật 3/5). Admin đồng ý **thêm Correction log**, **giữ nguyên §1.3** (lịch sử audit), chỉ sửa kết luận.

## 1. Mục tiêu
Sửa các sai lệch số liệu/line-ref/fixture **mà không viết lại lịch sử** (§1.3 được bảo toàn). Thêm §8 Correction log 2026-09-30.

## 2. Các điểm cần sửa (verify-based)

| # | Vấn đề | File | Hành động |
|---|---|---|---|
| P0-1 | §1.3 kết luận ngược: "429 chưa từng xảy ra → phòng vệ" vs D7 "429 xịt thật 3/5", T178 đã có retry/backoff (`_T73_429_MAX_RETRY=2`, 0.5s→1s). | REVIEW.md | **Giữ nguyên §1.3**. Thêm §8 Correction log 2026-09-30: ghi rõ 429 là sự cố thật (D7 3/5), A8/C1 đã lỗi thời (T178 sửa), không xoá lịch sử. |
| P1-1 | B5/acceptance D8 ghi *match substring `天然`* nhưng `天然` 0 rule/0 glossary; thật là `丹霞` (TERM_DANHA, TERM_DAN_HA). | REVIEW.md + absorb | Đổi `天然` → `丹霞` (U+4E39U+971E). Giữ nguyên ý nghĩa Test Case 2. |
| P1-2 | "8 phần" vs code `constitution_hash` có **10** phần (thêm `p8:alignment_method` != 'none'). Tham chiếu 168-199 → 211-234. | REVIEW.md + absorb | Sửa "8 phần" → "10 phần"; line-ref 211-234 (style_constitution.py). |
| P1-3 | Rendered `12.287` < raw `13.230` mâu thuẫn (rendered ≥ raw). Snapshot trôi 2026-09-25 vs 2026-09-26. | REVIEW.md | Thêm chú thích **mốc đo khác nhau** (2026-09-25 vs 2026-09-26 sau D6), ghi rendered ≥ raw, thêm cột mốc đo. |
| P1-4 | 7 line-ref lệch toàn bộ: 16575→17713, 16569→17703, 16412→17520, 18396→19725, 16606 → import alias L44 (gọi L17771), style_constitution 436 → log_prompt_metrics 518. | REVIEW.md | Cập nhật bảng line-ref + thêm banner "Đã verify lại 2026-09-30 (app.py 22.896, style_constitution.py 863)". |
| P2 | B4 "15 chỗ FROM translation_cache" → **18**. B8 "12+3 site" → **13+4**. dual-hash **1/1900**, cache **1900 invalidated**, `invalidate_cache_all_semantic` là **DELETE** (mất audit trail) — chưa ghi rõ. | REVIEW.md + absorb | Cập nhật số liệu + cảnh báo hành vi DELETE (soft-invalidate vs hard DELETE) — nêu rõ khác với endpoint UPDATE `status='invalidated'`. |

## 3. Không làm
Code, DB, schema, T175/T194–T196. Chỉ docs correction.

## 4. Revert
`git revert --no-edit 9774ea4f1f3b43d07aa4c23064a71b50361788d4` (docs-only).