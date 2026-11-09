---
id: T163
title: "Unify DILA Lineage Relation Card Format (places.html renderer)"
module: graph
priority: low
status: done
depends_on: [T148, T157, T161]
created: 2026-09-22
updated: 2026-09-22
done_when:
  - "[x] Audit vị trí thực tế: _renderDilaExtra (~6006-6165) vs _renderDilaAxis (~6207-6296)"
  - "[x] 0 change API/DB/Schema — chỉ hợp nhất renderer phía client (places.html)"
  - "[x] Thêm hàm dùng chung _linRelParseBibl + _linRelationCard (~6006)"
  - "[x] _renderDilaExtra dùng _linRelationCard (đồng nhất CSS với DILA L2)"
  - "[x] _renderDilaAxis/chip() trở thành wrapper mỏng — output HTML giữ nguyên"
  - "[x] Self-reference guard defensive: card ⚠ + khoá link khi r.person_id === d.person_id"
  - "[x] Test browser 4 case PASS (A009460, A010470, fallback self-ref, regression 2 tab)"
  - "[x] Docs report: docs/UNIFY_DILA_LINEAGE_RELATION_CARD_FORMAT_REPORT.md"
  - "[x] Backup: docs/sessions/2026-09-22/places.html.bak-fix-person-name-display"
---

# T163 — Unify DILA Lineage Relation Card Format

> **Module:** `graph` · **Priority:** low · **Status:** done
> **Created:** 2026-09-22

---

## Tóm tắt

Hợp nhất 2 hệ card hiển thị quan hệ thầy/trò của 1 tăng nhân trong inspector
Truyền Thừa: `_renderDilaExtra` ("THẦY"/"HỌC TRÒ", nguồn raw DILA XML `listRelation`)
và `_renderDilaAxis` ("THẦY THEO DILA"/"ĐỆ TỬ THEO DILA", nguồn `lineage_edge_assertions`
L2) đang dùng 2 template độc lập — lệch visual dù cùng biểu diễn 1 khái niệm.

**Triết lý:** Giữ nguyên contract (0 ALTER, 0 route mới, 0 schema), chỉ thống nhất
renderer phía client theo pattern "1 hàm dùng chung".

## Root cause

- `_renderDilaExtra` dùng `_relGroup()` cục bộ: CSS riêng (`border-radius:6px;
  background:rgba(255,255,255,.03)`), link `admin/person.html`, bibl thô không tách
  evidence/citation.
- `_renderDilaAxis` dùng `chip()`: `background:var(--da-panel)`, click `centerLineageOn`.
- 2 template song song → lệch visual.

## Fix (chỉ places.html)

1. Thêm `_linRelParseBibl(bibl)` — tách Chứng cứ/Nguồn từ `bibl`, tái dùng parser
   `_t128ParseRef` (không phát minh heuristic mới).
2. Thêm `_linRelationCard(person, options)` — 1 template card duy nhất:
   - tên + hán + DILA ID
   - `mapping_verified` (✓L2, cross-check qua `/dila-axis`)
   - `evidence_quote` / `source_locator`
   - `is_self_reference` (⚠ cảnh báo, khoá link nếu trùng DILA ID)
3. `_loadDilaExtra`: fetch thêm `/dila-axis` song song (Promise.all) để cross-check L2.
4. `_renderDilaExtra`: refactor `_relGroup()` build item bằng `_linRelationCard`.
5. `_renderDilaAxis`/`chip()`: wrapper mỏng gọi `_linRelationCard` — output giữ nguyên.

## Audit phát hiện (lệch data test-case so với prompt)

Prompt gốc dùng `A010470` = "Đơn Hà Thiên Nhiên" — SAI. Verify DB: `A010470.name_zh='希搡'`
(name_vi='Hơi Táng'); người thật **A009460** `name_vi='Đan Hà Thiên Nhiên'`, `name_zh='天然'`.
Toàn bộ test-case 3 thầy + 7 đệ tử khớp 100% với **A009460**. Self-reference guard giữ
nguyên (defensive), không trigger sai.

## Test evidence

| Case | Kết quả |
|------|---------|
| A009460 → inspector Truyền Thừa | 3 card THẦY + 7 card HỌC TRÒ, CSS đồng nhất với DILA L2 ✅ |
| A010470 (đảo chiều) | 2 card HỌC TRÒ, không self-ref sai ✅ |
| Fallback self-ref (console) | Card ⚠ viền cam, khoá link, giữ Chứng cứ/Nguồn ✅ |
| Regression section DILA L2 | HTML giữ nguyên cấu trúc ✅ · chuyển tab Địa điểm 0 console error ✅ |

## Files changed

- `daoanh/places.html` (~6006-6296) — renderer client, 0 API/DB/Schema.

## Backup / Revert

- Backup: `docs/sessions/2026-09-22/places.html.bak-fix-person-name-display`
- Revert: `git revert <commit-T163>` (chỉ places.html)