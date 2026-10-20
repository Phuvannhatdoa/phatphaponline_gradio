# Session: Lineage Family Tree View

**Ngày:** 2026-09-05  
**Thay đổi:** Redesign `_renderLineageChain()` → collapsible vertical family tree

---

## Vấn đề

`_renderLineageChain()` cũ bung đệ quy toàn bộ cây ngay lập tức (depth≤8). Với tổ sư nhiều đệ tử (vd. 10 đệ tử trực tiếp × 76 hậu duệ), người dùng không nhận ra ai đời 1, đời 2 hay nhánh nào thuộc ai.

## Giải pháp

Viết lại `_renderLineageChain()` thành **collapsible top-down family tree**:

### Tính năng

| Feature | Mô tả |
|---------|-------|
| **Default view** | Root + toggle `+` + badge "N hậu duệ"; con cái ẩn mặc định |
| **Toggle +/−** | Click mở/đóng đúng 1 cấp con trực tiếp |
| **Badge hậu duệ** | Tổng descendants (BFS, cycle-safe); chỉ hiện khi collapsed |
| **Leaf nodes** | `·` button thay `+` khi không có con |
| **Edge evidence** | `● truyền pháp` (has_ref) hoặc `○ cần khảo cứu` (no ref) |
| **Control bar** | "Mở 2 đời" / "Mở toàn nhánh" / "Thu gọn" + stat line |
| **Ancestor chain** | Thầy truyền pháp vẫn hiện phía trên root (horizontal pills) |

### State management

- `_lineageState._ftExpanded = new Set()` — lưu set node IDs đang expanded
- Reset tự động khi `loadLineageTree()` tạo `_lineageState` mới
- Persist qua `_renderLineageChain()` re-renders (khi click +/−)

### Control buttons

- **Mở 2 đời**: `expanded.add(center)` + `expanded.add(k.id)` cho mỗi direct kid
- **Mở toàn nhánh**: add toàn bộ `Object.keys(st.nodes)` vào expanded
- **Thu gọn**: `expanded.clear()`

### descCounts computation

```js
const descCounts = {};
function _countDesc(pid, seen) {
    if (seen.has(pid)) return 0;
    seen.add(pid);
    const kids = kidsOf[pid] || [];
    let c = kids.length;
    kids.forEach(k => { c += _countDesc(k.id, new Set(seen)); });
    return c;
}
Object.keys(st.nodes).forEach(pid => {
    if (descCounts[pid] === undefined) descCounts[pid] = _countDesc(pid, new Set());
});
```

---

## Verified (A000084 - Tử Thuần 子淳, 10 đệ tử, 76 hậu duệ)

| Test | Kết quả |
|------|---------|
| Default collapsed | `+` Tử Thuần ★ · 76 hậu duệ ✓ |
| "Mở 2 đời" | 2 cấp mở, badges trên collapsed nodes ✓ |
| "Thu gọn" | Về 1 node duy nhất ✓ |
| Toggle +/− | Click mở/đóng 1 cấp ✓ |
| Edge markers | `● truyền pháp` / `○ cần khảo cứu` ✓ |
| Ancestor chain | Thầy phía trên với `↓` arrows ✓ |
| Reset on new person | _ftExpanded = new Set() khi loadLineageTree() ✓ |
