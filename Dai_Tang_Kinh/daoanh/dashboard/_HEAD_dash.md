# ADMIN REVIEW DASHBOARD — Items Cần Admin Xác Nhận

> **Ngày tạo:** 2026-09-10 | **Pipeline:** PASS | **Commits:** `9b91e2d8`
> **Cách dùng:** Admin (Lee) mở từng URL test → xác nhận → nói "done" → Agent đánh dấu hoàn thành.

---

## A. BUGS — Đã Fix, Chờ Confirm (7 items)

| # | ID | Mô Tả | Cần Xác Nhận | URL Test | Cách Đánh Dấu Xong | Ảnh Hưởng |
|---|-----|--------|---------------|----------|---------------------|-----------|
| 1 | **BUG-015** | Console `SyntaxError: Unexpected end of input` + `monk-resolve 404` | Gõ tên địa danh (vd "Thiếu Lâm Tự") trong search → 0 lỗi console mới; monk-resolve với person thật (A000001) vẫn resolve đúng | `http://127.0.0.1:8080/places.html` | Nói "BUG-015 done" | Unblock T100 alert closure |
| 2 | **BUG-011** | Map marker click → GPS/district/note/category không hiện trong panel | Click marker bất kỳ → panel trái hiện đầy đủ GPS, quận, quốc gia, mô tả DILA, tạm dịch AI | `http://127.0.0.1:8080/places.html?fly=34.5885,112.9343&select=PL000000023255` | Nói "BUG-011 done" | Unblock T100 alert closure |
| 3 | **BUG-012a** | Cluster marker click không update panel (persistent marker re-fire old ID) | Click cluster marker sau khi filter → panel cập nhật entity mới (không bị entity cũ) | `http://127.0.0.1:8080/places.html` → bật filter → click cluster | Nói "BUG-012a done" | Unblock T100 |
| 4 | **BUG-012b** | GPS/RAG state mismatch sau search entity mới | Click marker → search entity mới → khối "Vị Trí · 3 Lớp RAG" hiện data entity mới (không cũ) | `http://127.0.0.1:8080/places.html` → click marker → gõ search mới | Nói "BUG-012b done" | Unblock T100 |
| 5 | **BUG-014** | Nexus giật lag + cạnh chồng chéo khi click "Hồ Sơ DILA" | Mở Nexus tab → click node "Hồ Sơ DILA" → hiệu ứng mượt, cạnh không overlap | `http://127.0.0.1:8080/places.html` → Nexus tab | Nói "BUG-014 done" | Unblock T100 |
| 6 | **BUG-008** | Filter "Chùa / Tự viện" ẩn marker đang select | Click marker → apply filter "Chùa / Tự viện" → marker vẫn hiện (persistent layer) | `http://127.0.0.1:8080/places.html` → click marker → filter | Nói "BUG-008 done" | Unblock T100 |
| 7 | **MAP_SEMANTIC** | Markers dùng icon semantic theo loại địa điểm | Thiếu Lâm Tự → temple gate icon; selected marker nổi bật (32px + glow); tắt filter → root marker vẫn còn | `http://127.0.0.1:8080/places.html?fly=34.5885,112.9343&select=PL000000023255` | Nói "MAP_SEMANTIC done" | Unblock T100 |

---

## B. FEATURES — Đã Implement, Chờ Review (5 items)

| # | ID | Mô Tả | Cần Xác Nhận | URL Test | Cách Đánh Dấu Xong | Ảnh Hưởng |
|---|-----|--------|---------------|----------|---------------------|-----------|
| 8 | **T118-r1** | Audit trail API (GET /api/research/entity/<id>/audit-trail) | Gọi API với entity thật → trả audit log đầy đủ (action, editor, timestamp, notes) | `curl http://127.0.0.1:5000/daoanh/api/research/entity/PL000000023255/audit-trail` | Nói "T118-r1 done" | Unblock T118 closure |
| 9 | **T118-r2** | Citation export có audit_id xuyên export + signature sha256 | Gọi citation với audit_id=en-5 → có `audit` block + `signature` trong CSL; BibTeX có `SIG=` | `curl "http://127.0.0.1:5000/daoanh/api/public/export/citation?entity_id=PL000000023255&audit_id=en-5&format=csl-json"` | Nói "T118-r2 done" | Unblock T118 closure |
| 10 | **T119** | Editor Dashboard 6 tabs + bulk-review + editor-stats | Mở dashboard → 6 tabs hoạt động → bulk-review 1 claim → stats cập nhật | `http://127.0.0.1:5000/daoanh/admin/editor-dashboard.html` | Nói "T119 done" | Unblock T113, T100 alerts |
| 11 | **T121** | Geo Enrichment 9 candidate (P625/P2044) | Mở tab Geo Enrichment → thấy 9 candidate → approve 1 → verify GPS thay đổi | `http://127.0.0.1:5000/daoanh/admin/editor-dashboard.html` → Geo Enrichment tab | Nói "T121 done" | Unblock T120 |
| 12 | **T73** | Bio Review UI + 3 routes (pending/approve/apply) | Mở tab Bio Review → thấy pending list → approve 1 draft → apply → verify `people.bio_vi` thay đổi | `http://127.0.0.1:5000/daoanh/admin/editor-dashboard.html` → Bio Review tab | Nói "T73 done" | Unblock T74b |

---

## C. TASK CLOSURES — Cần Đóng (3 items)

| # | ID | Mô Tả | Cần Xác Nhận | Cách Đánh Dấu Xong | Ảnh Hưởng |
|---|-----|--------|---------------|---------------------|-----------|
| 13 | **T112** | Source Pending Activation (8 nguồn đã phê duyệt) | Xác nhận 5 BLOCK/3 DEFER/1 REFERENCE_ONLY đúng ý | Nói "T112 done" | Unblock T120 |
| 14 | **T122** | Batch D driver (T118-r2 + T121 + T73 + docs) | Xác nhận tất cả sub-items đã review | Nói "T122 done" | Đóng Batch D |
| 15 | **T150b/T162** | Reseed name_vi post-T149 (DONE 2026-09-22) | Xác nhận số liệu apply (27,801 people changed + 22,738 map updated + 4,430 dup deleted; verify 0 pending, _ok_hanviet 27,792/27,801) và **155 ambiguous** (đổi từ trước, có rác A000006) — Agent KHÔNG tự quyết. Danh sách đầy đủ: `docs/t162_ambiguous_155.csv` | Nói "T150b done" | Đóng T150/T149 tracked side-effect |

---

## C2. TASK CLOSURES — QA BUILD MỚI CHỜ LEE (hiện thân trực tiếp)

| # | ID | Mô Tả | Cần Xác Nhận | Cách Đánh Dấu Xong | Ảnh Hưởng |
|---|-----|--------|---------------|---------------------|-----------|
| 16 | **T97** | Mở tab ⚡ Sự Kiện + ⏱ Niên Đại cho person (build `94a8c00`, additive UI 0 DB) | Trên :5000: mở person A000001 → click tab Sự Kiện + Niên Đại thấy timeline; nơi place (vd Thiếu Lâm Tự) → tab Sự Kiện giữ nguyên. Video 30s gửi Lee | Nói "T97 done" | Đóng T97 (Unblock tiếp theo) |
| 17 | **T97b** | Tab Sự Kiện place: section "Tu Sĩ Liên Quan · Timeline" (co-mention → vn_person_events, additive 0 DB; backend `ed03c86` + UI trong HEAD) | Trên :5000: search "Thiếu Lâm Tự" → tab Sự Kiện → thấy section "Tu Sĩ Liên Quan · Timeline" với 3 tu sĩ (giải thích: những người xuất hiện cùng nơi trong passage CBETA + có timeline vn_person_events). Dòng ghi chú co-mention rõ ràng (KHÔNG overclaim trụ tại nơi). Regression: person A000001 tab Sự Kiện giữ nguyên | Nói "T97b done" | Đóng T97b |

---

## D. DECISIONS NEEDED — Cần Quyết Định (2 items)

| # | ID | Mô Tả | Cần Quyết Định | Cách Đánh Dấu | Ảnh Hưởng |
|---|-----|--------|-----------------|----------------|-----------|
| 15 | **T34** | Xóa ~80 rows fake/test data | ✅ **DONE (2026-09-10, Lee xác nhận)** — commit `76d9914` (delete fake data, Phase A complete, admin approved). DB verified: `eight_four_thousand`=0 · `vri_tipitaka_catalog`=0 · `kanripo_catalog`=101 (real ETL). | Không cần action | Cleanup DB ✅ |
| 16 | **T28** | Server restart + route A/B | Chọn route A (localhost) hoặc B (VPS) | Nói "T28 route A" hoặc "T28 route B" | Deploy |

---

## E. Tiến Độ Xác Nhận

| Trạng thái | Số lượng | Items |
|------------|----------|-------|
| ⏳ Chờ confirm | 18 | Tất cả trừ T34 (✅ 18/19), T112 (✅ 19/19), T97 (item mới #16) và T97b (item mới #17) |
| ✅ Đã confirm | 2 | T34 (Lee 2026-09-10) · T112 (Lee 2026-09-10) |
| ❌ Cần fix lại | 0 | — |

**Tiến độ:** 2/19 (11%)

---

## F. Cách Thức Hoạt Động

1. **Admin (Lee)** mở từng URL test theo bảng trên
2. **Thực hiện hành động** cần xác nhận (click, curl, mở tab...)
3. **Nếu OK:** Nói "DONE: [tên item]" (vd "DONE: BUG-015")
4. **Nếu lỗi:** Nói "BUG: [tên item] — [mô tả lỗi]" → Agent sẽ fix
5. **Agent** cập nhật tasktodo.md + bugs.md + commit

---

## G. Impact Map

```
BUG-015/011/012a/012b/014/008/MAP_SEMANTIC ──→ T100 alert #4/#5 closure
                                                  └──→ T113 QA/UAT closure
T118-r1/r2 ──→ T118 closure
T119 ──→ T113 (claims_reviewed > 0%)
T121 ──→ T120 (unified lookup)
T73 ──→ T74b (Claude translate)
T112 ──→ T120 (dependency cleared)
```
