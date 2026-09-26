---
id: T152
title: "Pháp Mạch Ancestor Spine — Code Telemetry (endpoint + renderer)"
module: truyenthua
priority: high
status: done
depends_on: [T151]
created: 2026-09-17
updated: 2026-09-17
done_when:
  - "[x] Endpoint `GET /daoanh/api/monk/<dila_id>/ancestor-spine?max_hops=80` (read-only, lọc rejected qua _t138_edge_assertions, safety 80, cycle-safe)"
  - "[x] places.html: _lineageMergeAncestorSpine + bump up/down=6 + network keep không cắt tổ + 'Thu gọn nhánh dưới' + banner stop-at-broken"
  - "[x] Verify: py_compile OK · @babel/parser 0 error · smoke A000958 → spine 48 đời tới root A004683 break=root"
  - "[x] Pipeline: lint/test/e2e PASS"
---

# T152 — Pháp Mạch Ancestor Spine — Code Telemetry (endpoint + renderer)

> **Module:** `truyenthua` (Pháp Mạch · Phả hệ mở rộng · places.html · app.py)
> **Priority:** high · **Status:** pending (code telemetry — chạy SAU T151 acceptance)
> **Type:** code fix (additive UI + 1 endpoint đọc, 0 ALTER, 0 Schema, 0 DB write)
> **Created:** 2026-09-17 · **Updated:** 2026-09-17
> **Depends on:** T151 (acceptance framework DONE 2026-09-17) → T150 (published lineage filter docs)
> **SSOT canonical:** `tasks/T152-phap-mach-spine-code-telemetry.md` (1 unique, mirror T148 code pattern)
> **Acceptance:** A1..A8 trong `tasks/T151-phap-mach-ancestor-spine-docs-closure.md`

---

## 1. Vấn đề (problem — telemetry thực)

Xác nhận REAL trên server code (places.html 61;0 bytes / 9,054 dòng + app.py):

```
places.html:4865   fetch(...+dilaId+'/lineage-tree?up=2&down=2'...)   ← loadLineageTree
places.html:5032   fetch(...+pid+'/lineage-tree?up=2&down=2'...)       ← centerLineageOn
places.html:6151   'Mở thêm đời trên ↑'  st._netExpand.above++ ; refetch khi >d.up
places.html:6167   'Thu gọn'  st._netExpand = {above:2, below:2, all:false}
places.html:6226   keep = reachable.has(pid) && (all || (gen[pid]>=-above && gen[pid]<=below))
```

Server `api_monk_lineage_tree` clamp `up`,`down` ∈ [0,6]. Client default `up=2` → payload
chứa tối đa 2 đời thầy. Renderer `_renderLineageChain` ĐÃ climb `parents` không giới hạn
(`_lineageBuildRows` :5847-5876 walk `while(parents[cur])` + `seenUp`) — CHỈ bị chặn bởi
dữ liệu `up=2`. Network mode còn cắt display lần nữa bằng `gen>=-above`.

**→ Gốc sự cố = tầng DỮ LIỆU (`up` clamp/hardcode), không phải tầng vẽ.**

## 2. Giải pháp (additive, mirror chuẩn)

### 2.1 Endpoint mới (app.py, read-only) — `GET /daoanh/api/monk/<dila_id>/ancestor-spine`

Đi bộ teacher-chain từ focus ngược lên, KHÔNG giới hạn `up` (chạy tới khi hết thầy):

- Dùng `_t86_neighbors(conn, pid, 'up')` (marcus_networks student→teacher) — lặp liên tục.
- Lọc `rejected` qua `_t138_edge_assertions(conn, nid, pid)` (mirror `api_monk_lineage_tree` active_edges) — chỉ giữ cạnh verified/provisional, 0 rejected.
- Safety: max **80 hops** (T151 A6); cycle-safe qua `seen` set (T151 A6).
- Trả: `{ok, center, ancestors:[id...từ gần→xa], nodes[], edges[], break_reason: 'root'|'rejected'|'safety'|'not_found', max_hops}`.
- `break_reason 'rejected'` = còn thầy ở trên NHƯNG các cạnh bị reject → client hiện banner "Mạch thiếu cạnh đã xác minh" (T151 A5).

### 2.2 Client (places.html, additive)

| # | Vị trí | Thay đổi |
|---|--------|----------|
| 1 | `loadLineageTree` :4865 | sau khi set `st.nodes/edges`, gọi `_lineageMergeAncestorSpine()` (await) để bổ sung spine nodes/edges vào `st` |
| 2 | `centerLineageOn` :5032 | cùng merge spine khi đổi tâm |
| 3 | `_lineageExpandRefetch` :5055 | merge spine sau refetch (giữ spine khi mở rộng below) |
| 4 | `_renderLineageNetwork` :6226 | `keep` = reachable && (all \|\| gen[pid] < 0 \|\| gen[pid] <= below) — spine phía trên KHÔNG còn bị `above` cắt (T151 A1/A2/A3) |
| 5 | `_t129NetCtrlBar` :6167 | 'Thu gọn' → 'Thu gọn nhánh dưới', reset `{above:2, below:2}` chỉ tác động phần dưới; spine giữ nguyên |
| 6 | `_renderLineageChain` ancestor loop :6032-6057 | vẽ banner node đầu mạch khi `break_reason` ≠ null: "⚠ đầu mạch (hết thầy)" hay "⚠ Mạch gián đoạn: cạnh phía trên chưa xác minh" + CTA refetch (T151 A4/A5) |
| 7 | tooltip nút 'Mở 2/3 đời' | làm rõ "mở thêm ĐỆ TỬ phía dưới" — spine tổ phía trên luôn đầy đủ |

### 2.3 KHÔNG đổi (0 touch)

- DB schema / bảng / column — 0 ALTER (T150 nguyên tắc).
- `api_monk_lineage_tree` clamp [0,6] — GIỮ NGUYÊN làm default payload cho mode mở rộng; spine đi qua endpoint RIÊNG (additive).
- Trust filter / UI events khác.

## 3. Điều kiện hoàn thành (done_when)

- [ ] `GET /daoanh/api/monk/<dila_id>/ancestor-spine` code => smoke real (curl) trả spine đúng `break_reason`
- [ ] places.html 7 điểm trên code real, `_applyLineageFilters` vẫn hoạt động, browser render spine đầy đủ
- [ ] `npm run pipeline` lint · test · e2e PASS (BẮT BUỘC trước review)
- [ ] task file `tasks/T152-phap-mach-spine-code-telemetry.md` + session log + tasktodo row + ROLLBACK row (placeholder→hash-fill real 2-pass)
- [ ] Reviewer browser-thật xác nhận A1..A5 + screenshot

## 4. Rollback

```bash
git revert --no-edit <sha_code_T152>    # revert endpoint app.py + UI places.html (2 file)
# = echo ROLLBACK row T152; 0 DB write nên revert đủ; spine endpoint read-only
```

## 5. Traceability (bug → code → test)

| Bug gốc | Root cause | Fix | Verify |
|---------|-----------|-----|--------|
| Pháp Mạch cắt spine ở 2 đời | `up=2` hardcode + clamp [0,6] | spine endpoint 80-hop + merge | browser: focus đời sau thấy trọn tổ |
| Network cắt ancestor theo `above` | display filter `gen>=-above` | `keep` giữ `gen<0` | browser: mở rộng mà tổ không mất |

---

*Code telemetry T152 — additive, 0 ALTER, 0 Schema, 0 DB write, 0 migration. Pipeline BẮT BUỘC PASS trước review.*