---
id: T12
title: Dịch Mượt & Cache Translation (Khoá 7)
module: Translation Pipeline
priority: low
status: pending
depends_on: [T02]
created: 2026-08-13
updated: 2026-08-24
done_when: POST translate-cbeta trả polished_text (3 bước Dịch Mượt) + cache DB + admin approve/reject + UI panel
---

## ⏸ TREO 2026-08-24 — Undone, chờ admin mở lại

**Lý do:** pipeline dịch (`TranslationService`, bước "Gemini dịch thô") cần **Gemini API key hợp lệ**
— key cũ đã bị Google revoke (cùng gốc blocker với [T02](T02-passage-vi-entity-summary.md), task đó
đã bị user chủ động skip 2026-08-24 vì lý do này). Về kỹ thuật T12 dùng DB riêng
(`translations_cache.db`) nên không thực sự cần dữ liệu output của T02, nhưng vẫn không chạy được
nếu thiếu key LLM để dịch thô ở bước 1. Không code tiếp cho tới khi có Gemini key mới.

Priority hạ xuống `low`. Admin muốn mở lại: cung cấp Gemini key mới (đặt `.env`, update `app.py`
lines 1413/1453/3672/4561), đổi `status` → `in_progress`, xoá block này.

# T12 — Dịch Mượt & Cache Translation (Khoá 7)

## Mục tiêu
Khoá 7 — Hệ thống "Dịch Mượt" (Translation Polish) chuẩn hóa tự động văn bản CBETA dịch tiếng Việt: cache translation để user load nhanh bản dịch đã duyệt.

## Cách tiếp cận
- DB mới `translations_cache.db`: `place_cbeta_translations` (UNIQUE place_id+cbeta_ref, translation_status draft/admin_approved/user_generated/auto_generated, confidence_score) + `term_normalization_log` + indexes.
- `TranslationService`: check cache → fetch CBETA Hán → Gemini raw → polish 3 bước (grammar correction LLM → normalize terms qua lexicon + RapidFuzz → auto-replace theo confidence).
- Endpoint `POST /api/translate-cbeta` (force_refresh), `PUT /api/admin/translations/:id/approve`, `GET /api/places/:id/translations`.
- UI `TranslationPanel` thay nút "CBETA DỊCH VIỆT"; admin panel duyệt + batch script + bulk approve.

## Acceptance criteria (checklist)
- [ ] DB translations_cache.db + migration
- [ ] TranslationService 3 bước Dịch Mượt
- [ ] Endpoint translate-cbeta (cache hit + new)
- [ ] Admin approve/reject + GET translations
- [ ] UI TranslationPanel + admin panel
- [ ] Batch translate script + cron
