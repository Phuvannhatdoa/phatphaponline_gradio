# Quy tắc Graph Layout — Nexus & Lineage

## Stable node identity

- Node key = entity's canonical DILA ID — **không dùng array index**.
- Node position (x, y) được giữ theo ID khi expand.
- Không global relayout / fit / center khi click expand.
- Chỉ đặt node con mới gần parent node, không dịch cả graph.

---

## Expand / collapse

- Expand: thêm node con mới với position gần parent.
- Collapse: ẩn node con (giữ trong state), không xóa.
- Re-expand: restore node con từ state đã lưu — giữ nguyên vị trí.
- Click background / zoom / pan: không trigger relayout.

---

## Nexus graph (Tab Nexus)

Source: `nexus_events` (person-place co-mention) + `event_text_link`.

- Node màu: phân biệt place vs person vs text.
- Edge label: event_type hoặc cbeta_ref ngắn.
- Không render edge nếu không có source ref.
- Limit default: 50 edges/node để không quá tải vis.js.

---

## Lineage graph (Tab Truyền Thừa)

Source: `marcus_relations` / lineage tables.

- Layout: top-down tree (thầy trên, trò dưới).
- Không suy lineage từ co-mention — chỉ dùng `relation_type=teacher_of` đã xác minh.
- Recursive collapse: ẩn toàn bộ nhánh con, không chỉ cấp 1.

---

## Vis.js constraints (hiện tại)

- Không thêm dependency mới khi vis.js hiện có đủ.
- Dùng `network.setOptions({physics: {enabled: false}})` sau stabilize để freeze layout.
- Lưu node positions vào `localStorage` theo entity DILA ID để restore khi reload.
- Không dùng `network.fit()` sau mỗi data update — chỉ fit lần đầu load.

---

## Known issues (audit 2026-09-05)

- Nexus graph: unstable layout khi expand → fix bằng stable ID + disable physics post-stabilize.
- Lineage: recursive graph có thể loop nếu có cycle trong data — cần detect + break.
- Report: `docs/NEXUS_GRAPH_STABLE_EXPAND_FIX_REPORT.md`
