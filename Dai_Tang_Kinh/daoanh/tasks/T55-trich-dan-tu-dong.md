---
id: T55
title: "Trích Dẫn Tự Động — Related Texts & Intelligent Recommendation"
module: CBETA / Commercial References / Recommendation
priority: medium
status: done
depends_on: [T36, T40, T42, T43]
created: 2026-08-26
updated: 2026-09-22
done_when: >
  Khi đọc 1 kinh/1 địa danh → gợi ý "Kinh liên quan theo chủ đề" + "Nhân vật xuất hiện",
  kết hợp cross-ref có sẵn + clustering chủ đề + gợi ý từ hành vi. Không ghi đè
  "Kinh Điển Liên Quan" hiện có trong `/api/places/<id>/cbeta`.
---

# T55 — Trích Dẫn Tự Động (Related Texts & Recommendation)

## Mục tiêu
Xây lớp gợi ý thông minh: khi đọc 1 text/địa danh/nhân vật → đề xuất nội dung liên quan.

## Hiện Trạng (Codebase)
- `app.py:4017-4045` — "Kinh Điển Liên Quan" tự sinh trong `/api/places/<id>/cbeta` (deterministic)
- `T36` DharmaNexus parallels — gợi ý parallel passages đa truyền thống
- `T38` Toh crossref, `T35` SAT crossref — gợi ý đối chiếu
- `T40` `place_person_bibl` (13,933) + `T42` ref pivot (1,945) — nhân vật ↔ kinh
- `T43` `place_person_bio_cache` (470,745) — pre-computed bio mentions
- Marcus network — gợi ý nhân vật liên quan qua thầy-trò

## Khoảng Trống (Gap)
- Gợi ý hiện **deterministic** (dựa cross-ref có sẵn), chưa có "liên quan theo chủ đề"
- Chưa có recommendation engine / embedding similarity
- Chưa có panel "Suggested Readings" trên trang chi tiết

## Subtasks

### T55a — Topic Clustering CBETA Texts
✅ DONE (2026-09-11, data-layer) — Topic Clustering 3,122 texts (addition)`cbeta_topic_clusters`:
- Bảng mới `cbeta_topic_clusters(text_id, topic, score)` — additive, `CREATE TABLE IF NOT EXISTS` + 2 index phụ, 0 ALTER bảng nền, 0 migration
- Script: `scripts/t55a_topic_clusters.py` (mới) — Zero-RAM page LIMIT/OFFSET `--page_size 200`, bulk-insert từng page; `--limit/--offset/--dry/--drop/--stats`
- `text_id` = `cbeta_catalog_vn.id` (PK) — vì `cbeta_ref` chỉ 6 rows (còn lại NULL), `q_number` gom 85 cụm, `sh_number` 2,915/11 NULL, `sigla`/`text_code` 0 rows
- Gán topic: lexicon genre keywords (Kinh/Luận/Luật/Đà La Ni/Thiền/Lục/Truyện/Niết Bàn/Hoa Nghiêm/Bát Nhã/...) + `dynasty_vi` (Đường/Nhật Bản/Tống/...) + translator nổi bật — deterministic, không bịa
- Kết quả thật: 8,168 rows · 2,977/3,122 texts có ≥1 topic · 742 topics (Kinh 1,249 · Đường 749 · Nhật Bản 550 · Tống 381 · Luận 304 · Giáo Pháp 292 · Thần Chú 219 · Bồ Tát 204 · Bất Không 165 · Kim Cang 142 · Ngữ Lục 113 · Giới Luật 112 · Thiền 109 ...)
- 145 texts zero-topic trung thực (dynasty/translator "Chưa rõ"/"Không rõ người" hoặc title không khớp VD "An Dưỡng Sao")
- Revert: `git revert --no-edit <commit T55a build>` + `DROP TABLE cbeta_topic_clusters` (bảng thuần add, an toàn)

### T55b — Recommendation API
- Route: `GET /daoanh/api/cbeta/<sigla>/related?limit=10`
- Trả về 3 nhóm: (1) cross-ref có sẵn, (2) cùng topic cluster, (3) nhân vật xuất hiện
- Add "source" tag cho từng suggestion (crossref / topic / mention)

✅ T55b — API endpoint (Batch F, 2026-09-10):
- Route: `GET /daoanh/api/cbeta/<sigla>/related` — `api_cbeta_related` app.py:4393-4498
- Nhóm 1 `crossref` — SAT URL (`sat_crossref`) + Toh 84000 (`toh_cbeta_crossref`) + Pali map (`pali_cbeta_map`)
- Nhóm 2 `topic` — kinh khác chia sẻ ≥3 DILA persons (co-mention, dùng `cbeta_person_mentions` verified 72,628 rows)
- Nhóm 3 `persons` — thiền sư/nhân vật xuất hiện trong kinh (kèm mentions + name_vi/dynasty từ `people`)
- Normalize sigla: `T50n2059`→`T2059`, `T0251`, `X77n1524`→`X1524` (chuẩn CBETA short)
- Hoàn toàn read-only: 0 bảng mới, 0 ALTER, 0 ghi DB → revert = xóa route
- HITL-safe & trung thực: nhóm không có data → trả `[{'status':'NO_DATA'}]` thay vì bịa
- Smoke PASS: `T2076`→SAT + 12 persons + 4 topic; `X77n1524`→persons + 4 topic (loại self);
  `T0251`→SAT+Toh+Pali; `T50n2059`→SAT (persons/topic NO_DATA); `NOPE999`→honest NO_DATA
- Roi đổi về trước: revert commit BUILD T55b

### T55c — Gợi Ý Từ Hành Vi (Collaborative)
- OPTIONAL (low effort): log lượt click text → gợi ý "người xem kinh này cũng xem..."
- Bảng: `text_reading_log(text_id, session, ts)` — appending cô lập, an toàn

✅ T55c — Collaborative Reading Log (Batch F, 2026-09-11):
- Bảng additive `text_reading_log` (id, text_id short sigla, session, ts) — `T55C_TABLES_DDL` + `_ensure_t55c_tables()` app.py:4518-4561; `CREATE TABLE IF NOT EXISTS` + 2 index phụ; 0 ALTER bảng nền, 0 migration
- `POST /daoanh/api/cbeta/<sigla>/view` — app.py:4586-4609: ghi 1 lượt xem, dedupe `UNIQUE(session, text_id)` (`INSERT OR IGNORE`), session tuỳ chọn ≤64 ký tự (thiếu → 'anon'), validate sigla qua `_t55_normalize_sigla`
- `GET /daoanh/api/cbeta/<sigla>/related/behavioral` — app.py:4611-4660: collaborative filtering "người xem kinh này cũng xem..."; loại phiên 'anon'; chỉ xuất khi ≥2 session thật cùng xem 1 cặp (`HAVING COUNT(DISTINCT session) >= 2`); loại Self (text_id != nguồn); top 5 theo co_viewers DESC; resolve title_vi qua `_t55c_resolve_title` (cbeta_ref GLOB 'T*n<num>'); thiếu dữ liệu → status NO_DATA trung thực
- Smoke PASS (test_client, clean-log sau test): T2076 → T0359 co_viewers=3 + title "Cảnh Đức Truyền Đăng Lục"; X77n1524 → normalize X1524; T359 → T0359; duplicate session+text dedupe; session>64 → 400; chưa xem/1-session → NO_DATA
- Revert: bỏ 2 route + `DROP TABLE text_reading_log` (bảng chỉ chứa log người đọc, không phải dữ liệu nền)

✅ T55d — Panel UI "Gợi Ý Đọc" (2026-09-22):
- Panel `<div id="cbeta-related-panel">` thêm ở cuối CBETA tab (sau Tự Chí section)
- `_loadCbetaRelated(sigla)` — lazy fetch với race guard `_cbetaRelatedSigla`; sigla từ `d.passages[0].sigla` (fallback: `T${sh_number}` từ related_texts[0])
- `_renderCbetaRelated(container, d)` — 3 nhóm: Đối Chiếu (SAT/Toh/Pali), Nhân Vật Trong Kinh, Cùng Chủ Đề
- KHÔNG ghi đè "Kinh Điển Liên Quan" — panel mới độc lập
- Verify: network log `GET /daoanh/api/cbeta/T49n2035/related → 200 OK`; panel innerText chứa "Gợi Ý Đọc Thêm · T2035 · SAT ↗"
- File: `places.html` lines 2467-2576

## API Changes
- New: `GET /daoanh/api/cbeta/<sigla>/related`

## Frontend
- Update trang chi tiết kinh (places.html CBETA tab) — thêm panel

## Không Xung Đột Với
- `/api/places/<id>/cbeta` hiện có (giữ nguyên Kinh Điển Liên Quan)
- T51 (Nhân Vật) — T55 chỉ gợi ý, không build portal
- T53 — dùng lại mention stats nếu có

## Estimated Effort: ~10 hours
