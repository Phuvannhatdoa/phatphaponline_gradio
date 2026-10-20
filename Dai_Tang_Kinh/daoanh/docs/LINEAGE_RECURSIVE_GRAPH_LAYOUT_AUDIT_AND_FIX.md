# Lineage Recursive Graph Layout — Audit & Fix Report

**Ngày:** 2026-09-06  
**Engineer:** Claude Code (Build Agent)  
**Task:** Fix "Pháp mạch" view — biến text outline thành visual tree thực

---

## 1. API Endpoint & Data Shape

**Endpoint:** `GET /api/lineage/<person_id>`  
**Backend:** `app.py` — route `/api/lineage/<id>` (hàm `t86_api_lineage()`)

**Response structure:**
```json
{
  "ok": true,
  "center": { "id": "A003623", "name_vi": "Mã Tổ Đạo Nhất", "name_zh": "馬祖道一", "dynasty": "...", "origin_place": {...} },
  "nodes": { "A003623": {...}, "A004015": {...}, ... },
  "edges": [
    { "from": "A003623", "to": "A001897", "direction": "student", "ref": "...", "has_ref": true },
    { "from": "A004015", "to": "A003623", "direction": "teacher", "ref": "...", "has_ref": false }
  ],
  "conflicts": [...],
  "up": { "nodes": {}, "edges": [] },
  "down": { "nodes": {}, "edges": [] }
}
```

**Nguồn quan hệ:** Marcus Bingenheimer lineage database.  
**Chuẩn hóa edge:** Frontend tự normalize từ raw `edges[]`. Không có server-side normalization riêng.

---

## 2. Edge Direction Semantics (Canonical)

Cả hai giá trị `direction` đều encode `from=teacher → to=student`:

| direction | from | to | Ý nghĩa |
|-----------|------|----|---------|
| `'student'` | Teacher của trò | Student | "from ghi nhận to là đệ tử" |
| `'teacher'` | Teacher | Student | "from được ghi nhận là thầy của to" |

**Ví dụ A003623 (Mã Tổ):**
- `from=A003623, to=A001897, direction='student'` → Mã Tổ là thầy, Hoài Hải là trò ✅
- `from=A004015, to=A003623, direction='teacher'` → Hoài Nhượng (A004015) là thầy, Mã Tổ là trò ✅

Canonical edge: `from (teacher) → to (student)` trong cả hai trường hợp.

---

## 3. Recursive Traversal Hiện Có (Trước Fix)

**Tồn tại:** Có đầy đủ recursive hierarchy:

| Hàm | Vị trí | Chức năng |
|-----|--------|-----------|
| `_lineageTreeFromEdges()` | line ~4347 | Xây `kidsOf[parent] = [{id: child}]` |
| `_lineageTreeParents()` | line ~4360 | Xây `par[child] = parent` |
| `_lineageBuildRows()` | line ~4370 | Trả `{ancestors, kidsOf, parents, generationsDown}` |
| `_buildFtVisTree()` | line ~4532 | BFS cycle-safe → `{visNodes, visEdges}` cho vis.js |
| `_countDesc()` | inside `_renderLineageChain()` | BFS count descendant cycle-safe |

---

## 4. Root Cause #1 — Text Outline (FIXED)

**Hàm cũ:** `mkFtRow()` trong `_renderLineageChain()` — render nested `div` có:
- Toggle button `+`/`−`
- Pill text node
- `● truyền pháp` / `○ cần khảo cứu` inline text
- Thụt lề bằng `padding-left: depth * 22px`

**Hệ quả:** Output là DOM list văn bản thụt lề, KHÔNG phải visual graph.

**Fix:** Thay toàn bộ `_renderLineageChain()` body bằng vis.js Network với hierarchical UD layout:
- `layout: { hierarchical: { direction: 'UD', sortMethod: 'directed' } }`
- `physics: { enabled: false }`
- Node màu vàng (center), xanh đậm (khác), viền đỏ (có conflict)
- Edge solid nếu có dẫn chứng, dashed nếu không
- Ancestor bar phía trên vis.js canvas

---

## 5. Root Cause #2 — Direction Inversion (FIXED)

**Bug:** `_lineageTreeFromEdges()` và `_lineageTreeParents()` xử lý `direction='teacher'` ngược:

```js
// TRƯỚC (sai):
if (e.direction === 'teacher') {
    kidsOf[e.to].push({ id: e.from });  // ❌ to là student, không phải parent!
    par[e.from] = e.to;                  // ❌ từ teacher trỏ tới student = ngược!
}

// SAU (đúng):
if (e.direction === 'teacher') {
    kidsOf[e.from].push({ id: e.to });  // ✅ from là teacher = parent
    par[e.to] = e.from;                  // ✅ child's parent = teacher
}
```

**Hệ quả của bug:** 
- Hoài Nhượng (A004015) xuất hiện trong `kidsOf[A003623]` — teacher bị liệt kê là học trò!
- `ancestors[]` = [] (rỗng) cho mọi nhân vật — không có ancestor chain nào hiển thị
- Mọi nhân vật đều là "root" trong cây — không có thầy phía trên

**Sau fix (A003623):**
- `ancestors` = ["Hoằng Nhẫn", "Huệ Năng", "Hoài Nhượng"] ✅
- `kidsOf[A003623]` = 141 học trò thực (Hoài Hải, Tề An, Vô Đẳng, ...) ✅
- Hoài Nhượng hiển thị trong ancestor bar, KHÔNG trong vis.js tree ✅

---

## 6. Layout Algorithm

**Library:** vis.js Network v10.0.1 (đã có trong project, không thêm dependency).  
**Config:**
```js
layout: {
    hierarchical: {
        direction: 'UD',          // top → down
        sortMethod: 'directed',
        levelSeparation: 88,
        nodeSpacing: 175,
        treeSpacing: 220
    }
}
physics: { enabled: false }       // static layout
```

**Ancestor chain** hiển thị trong anchor bar phía trên canvas (không trong vis.js graph để tránh confusion về direction).

---

## 7. Files Changed

| File | Lines | Thay đổi |
|------|-------|----------|
| `daoanh/places.html` | ~4347–4358 | Fix `_lineageTreeFromEdges()` direction='teacher' |
| `daoanh/places.html` | ~4360–4368 | Fix `_lineageTreeParents()` direction='teacher' |
| `daoanh/places.html` | ~4503–4735 | Rewrite `_renderLineageChain()` — vis.js thay DOM list |
| `daoanh/places.html` | ~4946–4982 | Update `_wireLineageControls()` — zoom/fit/center via vis.js API |

---

## 8. Before / After — Mã Tổ A003623

### Before
```
Pháp hệ - Mã Tổ Đạo Nhất
− Mã Tổ Đạo Nhất (A003623)
  − Hoài Nhượng (A004015)         ← SAIÌ sai (teacher → hiển thị như học trò)
    ● truyền pháp
    + Mã Tổ Đạo Nhất              ← cycle lặp lại!
  − Hoài Hải (A001897)
    ○ cần khảo cứu
    + [136 học trò khác]
  ...
```
Không có ancestor chain. Cây ngược chiều. Hoài Nhượng (teacher) ở dưới Mã Tổ.

### After (Initial State)
```
[ Ancestor bar: Hoằng Nhẫn (弘忍) ↓ Huệ Năng (慧能) ↓ Hoài Nhượng (懷讓) ]
[ Mở 2 đời | Mở toàn nhánh | Thu gọn | 141 đệ tử · 412 hậu duệ tổng | Nguồn: Marcus ]

[ vis.js canvas: 
    [Mã Tổ Đạo Nhất (馬祖道一) ★
     ▸ 412 hậu duệ]
]
```

Sau "Mở 2 đời": 293 nodes trong vis.js (center + 141 trực tiếp + 151 cháu đời 2).

---

## 9. Kết Quả Test

| Test | Kết quả |
|------|---------|
| Ancestor chain: Hoằng Nhẫn → Huệ Năng → Hoài Nhượng | ✅ |
| kidsOf A003623 = 141 (không có Hoài Nhượng) | ✅ |
| Hoài Hải, Tề An, Vô Đẳng là direct kids | ✅ |
| Không còn "− name / ● truyền pháp / + name" | ✅ |
| Zoom, pan, Fit, Tâm via vis.js API | ✅ |
| Mở 2 đời / Mở toàn nhánh / Thu gọn | ✅ |
| Click node → mở inspector | ✅ |
| Double-click → inspector | ✅ |
| No console errors | ✅ |

---

## 10. Limitations Còn Lại

### Wide Tree Problem (Critical UX Issue)

**Vấn đề:** Mã Tổ có 141 direct disciples. Sau "Mở 2 đời" → 293 nodes.  
vis.js hierarchical layout tính `nodeSpacing=175` × 141 siblings = 42,156px chiều ngang.  
Viewport = 560px → scale = 0.012 → các node rộng ~2px, **không đọc được**.

**Root cause:** vis.js `layout.hierarchical` không optimize cho sibling count lớn.

**Workaround hiện tại:** Người dùng phải zoom in thủ công sau "Mở 2 đời".

**Giải pháp đề xuất (chưa implement):**
1. **Pagination**: Giới hạn hiển thị 20 nodes/level, thêm "+N more" virtual node
2. **Dynamic nodeSpacing**: `nodeSpacing = max(20, viewport_width / (siblingCount * 2))`
3. **D3 hierarchy**: Thêm d3-hierarchy từ cdnjs — tidy-tree algorithm space-efficient hơn
4. **Clustering**: vis.js clustering để gom siblings ít dẫn chứng lại

### Multi-parent / Cross-lineage

- Nhân vật có > 1 thầy: cặp `(from=teacherA, to=person)` và `(from=teacherB, to=person)` đều đưa `person` vào `kidsOf[teacherA]` và `kidsOf[teacherB]`
- Trong cây rooted tại teacherA: person xuất hiện là con của teacherA ✅
- Trong kết quả `_lineageTreeParents()`: `par[person]` = teacherB (ghi đè) → ancestor chain chỉ đi theo 1 nhánh
- Cross-link không phá cây nhưng có thể bỏ mất 1 nhánh thầy

### Cycle Detection

- `_buildFtVisTree()` có cycle-safe BFS với `seen` Set
- `ancestors` chain có `seenUp` Set
- Cycle bị quarantine khỏi tree — không crash nhưng cũng không báo user rõ ràng

---

## 11. Canonical Edge Convention (Ghi nhớ)

```
from (teacher) → to (student)

direction = 'student': "from recorded to as their student"
direction = 'teacher': "from is recorded as teacher of to"
```

Cả hai đều là `from=teacher, to=student`. Không có trường hợp `from=student, to=teacher`.
