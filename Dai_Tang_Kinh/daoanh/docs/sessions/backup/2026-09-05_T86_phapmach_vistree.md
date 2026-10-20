# Session: Pháp mạch — vis.js Hierarchical Tree

**Ngày:** 2026-09-05  
**Task:** T86 — Fix view "Pháp mạch" trong tab 🌳 TRUYỀN THỪA

---

## Vấn đề

View "Pháp mạch" (`_renderLineageChain()`) render dạng DOM list văn bản thụt lề
thay vì family tree thực sự có hierarchy UD (top-down).

---

## Thay đổi

### `places.html` — `_renderLineageChain()` (thay hoàn toàn body cũ)

**Cũ (DOM list):** mkFtRow() + mkAncestorPill() + mkSecHead() + mkCtrlBtn() → DOM list dạng text
thụt lề với toggle (+/−), pill, badge.

**Mới (vis.js Network):** 

1. **`_buildFtVisTree()`** — BFS cycle-safe, xây `visNodes`/`visEdges` cho visible subtree:
   - Nodes bỏ qua ancestors (hiện trong ancestor bar riêng)
   - Node màu vàng (#ad7c1c) cho center, xanh đậm (#1a2035) cho phần còn lại
   - Border đỏ (#ff7b72) nếu có `direction_disagreement` conflict
   - Label có `▸ N hậu duệ` (collapsed) hoặc `▾ N đệ tử` (expanded)
   - Edges: solid vàng nếu `has_ref`, dashed xám nếu chưa có dẫn chứng

2. **Layout container (flex column 100% height):**
   - `ancBar`: ancestor pills bar phía trên (horizontal, ẩn nếu không có ancestor)
   - `ctrlBar`: "Mở 2 đời" / "Mở toàn nhánh" / "Thu gọn" + info badge + "Nguồn: Marcus"
   - `visDiv`: vis.js Network container flex:1

3. **vis.js Network config:**
   ```js
   layout: { hierarchical: { direction: 'UD', sortMethod: 'directed',
       levelSeparation: 88, nodeSpacing: 175, treeSpacing: 220 } }
   physics: { enabled: false }
   ```

4. **Event handlers:**
   - `click`: toggle expand/collapse nếu có con, mở inspector nếu lá (debounce 200ms)
   - `doubleClick`: luôn mở inspector

5. **`_wireLineageControls()`** — cập nhật zoom/fit/center:
   - zoom-in/out: `_lineageNetwork.moveTo({ scale: s*1.2 })` khi mode='tree'
   - fit: `_lineageNetwork.fit({ animation: true })` khi mode='tree'
   - center: `_lineageNetwork.focus(centerId, { scale:1, animation:true })`

---

## Verified (A015811 — Đại Giác Phương Niệm / 慈舟方念)

Node Y positions sau "Mở 2 đời":
- A015811 (root): y=-88 ← top
- A015790, A005648 (direct disciples): y=0 ← middle
- 12 grandchildren: y=88 ← bottom

✅ Hierarchical UD layout đúng thứ tự
✅ Không có console errors
✅ Control buttons hoạt động (Mở 2 đời, Fit, zoom via vis.js API)
✅ Center node màu vàng gold, leaf nodes xanh đậm

---

## Ràng buộc đã tuân thủ

- Không hard-code ID nhân vật cụ thể
- Không dùng LLM/API dịch
- Không sửa schema DB
- `_lineageState._ftExpanded` persist across re-renders
- Cycle-safe BFS (ancestors excluded từ tree, đưa vào bar riêng)
