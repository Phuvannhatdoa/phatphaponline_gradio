# Session — T151 Pháp Mạch Ancestor Spine — Docs Closure (2026-09-17)

> **Canonical docs closure — additive · docs-only · 0 code · 0 DB · 0 ALTER · 0 Schema · 0 ALTER TABLE · mirror chuẩn T148/T149/T150 (1 task = 1 commit, mirror 4-trụ SSOT).**
> Frame: xử lý bug "Pháp Mạch (tab 🌳 Truyền Thừa) không trace ngược hết chuỗi tổ sư về đầu mạch mà chỉ hiển thị 2/3 đời". Docs closure tách riêng; code thật ở T152.

---

## 1. Bối cảnh

Người dùng phản ánh: trong tab **🌳 Truyền Thừa (Pháp Mạch)** của `places.html`, khi focus một vị tổ sư bất kỳ, chuỗi **truyền thừa tổ sư (spine)** chỉ hiển thị tối đa ~2 đời ngược lên (thầy, sư ông) thay vì đi hết mạch về **đầu mạch** (Bồ-đề Đạt-ma / Mã Tổ Đạo Nhất… tuỳ tông). Nghi ngờ ban đầu là renderer cắt độ sâu.

**Audit thật (kết luận):** renderer đã sẵn sàng — `_renderLineageChain` và `_lineageBuildRows` climb `parents` **vô hạn** theo `seenUp` (cycle-safe). Bug nằm ở **TẦNG DỮ LIỆU**:

1. Client fetch hardcode `?up=2&down=2` — `loadLineageTree` (places.html:4865) và `centerLineageOn` (places.html:5032).
2. Server `api_monk_lineage_tree` (app.py) clamp `up = max(0, min(int(request.args.get('up',3)),6))` và `down` tương tự → payload chứa tối đa 6 đời, nhưng vì client xin `up=2` nên chỉ có ≤2 đời tổ.
3. Ở network mode còn bị display-cắt thêm bởi `keep = reachable.has(pid) && (st._netExpand.all || gen[pid] >= -st._netExpand.above && gen[pid] <= st._netExpand.below)` (places.html:6226) → chuỗi tổ bị `above` cắt.

## 2. Closure này (additive, docs-only)

| Trụ SSOT | File | Trạng thái |
|----------|------|-----------|
| Canonical task | `tasks/T151-phap-mach-ancestor-spine-docs-closure.md` | **1 unique** ✓ |
| Canonical session | `docs/sessions/2026-09-17_t151-phap-mach-ancestor-spine-docs-closure.md` | **1 unique** ✓ (file này) |
| tasktodo row | `docs/tasktodo.md` T151 | **DONE** ✓ |
| ROLLBACK row | `docs/ROLLBACK.md` T151 | hash-fill real 2-pass (placeholder → real `git rev-parse`) • xem `docs/ROLLBACK.md` |
| Dashboard | `data/progress_data.json` | regen real `build_progress_data.py` ✓ |
| Leftover | scripts/ `*t151*` | **0 cleaned** ✓ |

## 3. Acceptance (framework A1..A8 — yêu cầu nghiệp vụ, code thật ở T152)

- **A1 — Spine đầy đủ:** từ focus, chuỗi tổ sư luôn trace ngược **hết** về đầu mạch (không dừng ở 2/3 đời).
- **A2 — 2/3 đời chỉ điều khiển ĐỆ TỬ:** nút "Mở 2/3 đời" chỉ giới hạn độ sâu **phía dưới** (học trò), KHÔNG cắt tổ phía trên.
- **A3 — Thu gọn không cắt tổ:** "Thu gọn nhánh dưới" chỉ thu phần đệ tử, chuỗi tổ giữ nguyên.
- **A4 — Nhãn đầu mạch:** khi đã chạm đầu mạch (`has_more_up == false`) → hiển thị nhãn "Đầu mạch / tổ sư khai tông".
- **A5 — Stop-at-broken HONEST:** nếu chuỗi đứt thật (cạnh bị `rejected` hoặc chạm safety cap) → banner nói rõ lý do + CTA, KHÔNG bịa cạnh/đoán mắt xích.
- **A6 — Safety + cycle-safe:** cap tối đa 80 hops, phòng cycle bằng `seen`.
- **A7 — 0 DB change:** endpoint read-only, 0 ALTER, 0 Schema, 0 ghi DB.
- **A8 — Pipeline PASS:** `npm run pipeline` / tester:agent PASS trước khi review.

## 4. Liên hệ

- **Code thực thi:** T152 — `tasks/T152-phap-mach-spine-code-telemetry.md` (app.py endpoint `ancestor-spine` + places.html client/merge/filter/label).
- **Phụ thuộc dữ liệu:** `_t86_neighbors` (marcus_networks + marcus_people_link) và `_t138_edge_assertions` (lineage_edge_assertions — lọc `rejected`).
- **Revert:** `git revert --no-edit <sha_closure_T151>` (docs-only).
