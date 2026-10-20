# Session — Build Batch E1 (T112 close + T120 unified lookup + Admin Review Dashboard) 2026-09-10

**Commit:** code=`3c50ec50` · docs=`07d24308` · **Mode:** build (Lee: "phê chuẩn đề xuất… thực hiện Batch E1")

## Bối cảnh
Sau Batch D (3b87ea32/5a8d9e3b/9b91e2d8), Lee yêu cầu đẩy toàn bộ items cần admin xác nhận lên
dashboard + thực hiện Batch E1 (đóng T112 + mở T120).

## Nội dung 1 — Admin Review Dashboard (docs-only)
- **File mới:** `docs/ADMIN_REVIEW_DASHBOARD.md` — 17 items cần admin confirm, nhóm 5:
  - **A. Bugs fix-applied WFC (7):** BUG-015 · BUG-011 · BUG-012a (persistent-marker) · BUG-012b
    (GIS/RAG) · BUG-014 · BUG-008 · MAP_SEMANTIC — mỗi item có URL test + cách đánh dấu,
    ảnh hưởng (mở khóa T100 alerts).
  - **B. Features WFR (5):** T118-r1 audit-trail · T118-r2 citation signature · T119 editor-dashboard
    · T121 geo-enrich · T73 bio-review — có curl/URL cụ thể.
  - **C. Task closures (2):** T112 (đã duyệt 8 nguồn) · T122.
  - **D. Decisions (2):** T34 xóa fake data · T28 route A/B.
  - **E. Deploy (1):** places.html → VPS 158.220.106.183.
- Đồng bộ: tasktodo T112 line → DONE, T120 line → IN_PROGRESS.

## Nội dung 2 — T112 → DONE
- Lee duyệt SOURCE_REGISTRY §5 (5 BLOCK / 3 DEFER / 1 REFERENCE_ONLY) 2026-09-10.
- `tasks/T112-source-pending-activation.md`: status `done` + ghi trạng thái done ở mục Xây dựng Batch B.
- 0 code, 0 DB. Unblock T120.

## Nội dung 3 — T120 Phase C (unified lookup endpoint) — code additive
- **Route mới:** `GET /daoanh/api/v1/entity/<entity_id>/lookup` (app.py, sau bio-review apply).
- **5-layer fallback** (đọc cache, 0 network tại call, 0 bảng mới, 0 ALTER):
  1. DILA core — entity_hub/entity + namevi_map_places + places/places_dila (+fallback short-ID)
  2. Wikidata ref — `geo_cross_ref` (QID + confidence + mapped_by; verified resets)
  3. Wikipedia cache — `place_wiki_snapshots`
  4. Web enrichment — `web_enrichment_cache` (verified ưu tiên)
  5. name_variant — bridge wikidata_qid (đã simplify khỏi query vô nghĩa)
- **Confidence:** 0.5 core + 0.1 name_vi + 0.2 wikidata-verified / 0.1 auto + 0.1 wiki-cache +
  0.1 enrich-verified / 0.05 auto → clamp 1.0.
- **2 bug schema phát hiện khi smoke:** `places` không có cột `note`; `place_wiki_snapshots` không
  có cột `id` → fallback lấy `province`, Layer 5 bỏ query alt_wiki.

## Smoke test (Flask test_client, 2026-09-10)
| Case | HTTP | sources_used | confidence |
|------|------|--------------|------------|
| PL000000023255 (Thiếu Lâm Tự, Q232771) | 200 | ['dila','wikidata_ref'] | 0.8 |
| PL000000000048 (candidate QID null T121) | 200 | ['dila'] | 0.7 |
| PL056722 (short ID, fallback places_dila) | 200 | ['dila'] | 0.6 |
| NOPE999 | 404 | — | — |

4/4 PASS.

## Verification
- Pipeline: lint/test/e2e **PASS** (chạy sau commit).
- Regen dashboard (script build_progress_data.py).
- ROLLBACK: row Batch E1 + §2 quick-revert block (3c50ec50 placeholder → fill sau).
- ROADMAP_META_UPDATE §5 bullet Batch E1 + §2 line commits count.

## Rollback
- Code: `git revert --no-edit 3c50ec50` (endpoint hàm mới, không xóa bảng).
- Docs: `git revert --no-edit 07d24308`.
- Batch E1 không đổi DB → không cần §3.

## Việc kế tiếp
- Lee xác nhận dashboard 17 items (BUG x Sample.feature → T100/T113; T118/T119/T121/T73 → done;
  T120 → done).
- Batch C (BUG-012/014, T101) khi agent ngoài bàn giao — chưa đụng.
- T34/T28 quyết định sau khi Lee xem dashboard phần D.