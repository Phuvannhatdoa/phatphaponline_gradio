# T157 Phase 2C — Implementation: UI "Đối chiếu nguồn" post-fix (places.html)

> Ngày: 2026-09-17 · Sinh sau B-1 ETL fix (verify PASS) · Liên kết: `tasks/T157-dila-direction-inversion-fix.md`, `docs/lineage-relation-conflict-A004177-audit.md` §8.

## 1. Vấn đề

Sau B-1 (fix chiều DILA trong `lineage_edge_assertions`), UI "Đối chiếu nguồn" vẫn tô đỏ mọi quan hệ vì đọc NHẦM từ `lineage_conflicts_v2` (snapshot cũ đã LẬT CHIỀU, B-2 re-snapshot đang hoãn, chưa fix). Hệ quả:

- Node/edge bị đánh dấu ⚠ `direction_disagreement` từ dữ liệu legacy sai chiều → cây pháp mạch mất ý nghĩa (mọi cạnh A004177 tô đỏ).
- Inspector right-rail liệt kê "⚠ Quan hệ X: ngược chiều giữa nguồn" trực tiếp từ `n.conflicts` (legacy) → dẫn chứng SAI so với assertions mới đã chuẩn hoá.

## 2. Giải pháp (theo plan B-1 + Phase 2C đã chốt)

Chuyển nguồn render "Đối chiếu nguồn" sang **`lineage_edge_assertions` (post-fix)** — frontend đọc trên **edge `sources[]`** mà `api_monk_lineage_tree` đã gắn sẵn mỗi cạnh (gồm `source_code`, `raw_relation_type`, `ref`, `trust_level`, `direction_mismatch`). `lineage_conflicts_v2` chỉ còn vai trò **banner LEGACY** (thông tin, không phải cơ sở đánh giá).

### 2.1 Các thay đổi trong `places.html`

| # | Vùng | Trước (legacy conflicts_v2) | Sau (assertions post-fix) |
|---|------|------------------------------|---------------------------|
| 1 | Helper mới | — | `_t86EdgeMismatch(e)` (bất kỳ source có `direction_mismatch=true`); `_t86NodeDirMismatchCount(pid)` (đếm cạnh kề mismatch thật); `_t86SrcChip(s, srcKey)` (chip ✓ MARCUS / ✓/⚠ DILA + trust + ↗ ref + "○ Cần khảo cứu" khi DILA thiếu ref); `_linToggleResearch()` (mở/đóng +N vị ẩn). |
| 2 | `_t129NodeTitle` (:5535) | `n.conflicts.length` mâu thuẫn nguồn | `_t86NodeDirMismatchCount(n.id)` — chỉ ⚠ khi còn mismatch thật |
| 3 | `_renderLineageHeader` (:5842) | filter theo `n.conflicts` (direction_disagreement) | `edges.some(s => s.direction_mismatch)` |
| 4 | Filter conflict `_applyLineageFilters` (:5446) | `n.conflicts.some(issue_category===...)` | `_t86NodeDirMismatchCount(pid) > 0` |
| 5 | Edge marker `conflictTouched` (:6012) | node-conflict legacy | `_t86EdgeMismatch(edge)` (assertion thật) |
| 6 | Node color `hasConflict` (:6026) | `n.conflicts.some(...)` | `_t86NodeDirMismatchCount(pid) > 0` |
| 7 | Network mode `hasDirDis` (:6352) | `n.conflicts.some(...)` | `_t86NodeDirMismatchCount(n.id) > 0` |
| 8 | **Inspector "Đối chiếu nguồn"** (:6480) | list "⚠ ngược chiều" từ `n.conflicts` | **agreed-first** + 2-lane + evidence + Research + banner LEGACY (bên dưới) |
| 9 | Fallback `_renderLineageInspectorNode` (:6701) | `n.conflicts.length` mâu thuẫn dữ liệu | `_t86NodeDirMismatchCount(n.id)` |

### 2.2 Inspector "Đối chiếu nguồn" mới — agnostic theo edge assertion

1. **Card ✓ tích cực (agreed-first):** "✓ N quan hệ hai nguồn cùng chiều (Marcus + DILA đồng thuận)" — chỉ khi N>0, màu xanh lá.
2. **Card ⚠ cảnh báo (chỉ khi còn mismatch thật):** "⚠ M quan hệ còn ngược chiều (cần khảo cứu — kiểm tra từng cạnh)".
3. **Dòng phụ:** "• K quan hệ chỉ 1 nguồn ghi nhận (không tính mâu thuẫn)".
4. **2-lane Marcus | DILA:** mỗi nguồn 1 khối — nêu rõ hướng `thầy:` / `trò:` với tên + chip nguồn (`MARCUS L1 ↗` / `DILA L2 ↗`/`○ Cần khảo cứu`). Lazy: default hiện 4 vị/nguồn, nút **🔬 Research** mở toàn bộ (+N vị ẩn).
5. **Banner LEGACY:** nếu node còn conflict cũ `issue_category==='direction_disagreement'` trong payload → hiện note: "Bản so sánh legacy (lineage_conflicts_v2, snapshot cũ chưa re-snapshot) — chiều đã được chuẩn hoá 2026-09-17; mức hiển thị sử dụng assertions mới."

Nguyên tắc: **mọi render conflict đổi từ `n.conflicts` sang edge `sources[].direction_mismatch`** — không còn bất kỳ chỗ nào dùng legacy để tô đỏ.

## 3. QA kết quả (live server :8080, playwright chromium)

Test real: `loadLineageTree('A004177')` → `_renderLineageInspector('A004177')`:

- `direct=14` cạnh kề trung tâm; **`withBoth=14`** (MARCUS + DILA cùng chiều), **`mism=0`**.
- Inspector phải chứa `"✓ 14 quan hệ hai nguồn cùng chiều (Marcus + DILA đồng thuận)"`.
- Lane Marcus: `thầy: Pháp Thận (法慎) ✓ MARCUS L1 ↗`, `thầy: Đại Lượng (大亮) ✓ MARCUS L1 ↗`, `trò: Trạm Nhiên (湛然)…` — đúng 14 (2 thầy + 12 đệ tử) khớp audit §8.
- **0 console error / pageerror** toàn phiên load + render.
- `node --check` từng inline script places.html: OK. `npm run pipeline`: guard ✅ · design compliance ✅ · lint ✅ (infra `node --check .tmp` noise nhưng `|| exit 0`) · test ✅ · e2e ✅ · e2e:runtime ✅ (bypass `.pw-tmp`, EPERM pre-existing trên `.last-run.json`).

Screenshot QA: lưu tạm `.pw-tmp/qa-t157-lineage.png` (đã cleanup).

## 4. Files thay đổi

- `places.html` — 9 hunk kể trên (xem bảng 2.1).

## 5. Revert

```bash
# UI phase 2C (sau khi đã commit):
git revert --no-edit <sha_T157_ui>
# DB (nếu muốn về pre-B-1):
python scripts/etl_t156_dila_direction_fix.py --revert data/backups/lineage_t157_20260917_135725.db
# Docs:
git revert --no-edit <sha_T157_docs_2c>
```

## 6. Inner-work của Phase 2C

- [x] Helper `_t86EdgeMismatch` / `_t86NodeDirMismatchCount` / `_t86SrcChip` / `_linToggleResearch`
- [x] Thay 6 render conflict → edge assertion (`_t129NodeTitle`, header, filter, edge marker, node color, network `hasDirDis`)
- [x] Inspector "Đối chiếu nguồn" agreed-first + 2-lane + Research + banner LEGACY
- [x] Fallback inspector node → assertion-based
- [x] Bỏ biến legacy `_cSetLabel` / list "⚠ ngược chiều" cũ
- [x] QA live (playwright): 14/14 đồng thuận, 0 mismatch, 0 console error
- [x] `node --check` + pipeline PASS

> Note: `lineage_conflicts_v2` vẫn là bảng authoritative cho **Admin dashboard** (T115/T138 v1) — banner LEGACY chỉ ở inspector lineage; B-2 sẽ re-snapshot để dashboard khớp assertions.