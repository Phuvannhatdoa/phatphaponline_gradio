---
id: T151
title: "Pháp Mạch Ancestor Spine — Docs Closure (acceptance framework, additive)"
module: truyenthua
priority: high
status: done
depends_on: [T150]
created: 2026-09-17
updated: 2026-09-17
done_when:
  - "[x] Canonical hóa yêu cầu Pháp Mạch thành acceptance A1..A8 (spine đầy đủ · 2/3 đời chỉ đệ tử · Thu gọn không cắt tổ · stop-at-broken honest · chỉ cạnh non-rejected · safety 80 + cycle-safe)"
  - "[x] Đối chiếu code thật: renderer đã climb parents vô hạn; bug ở tầng dữ liệu (up=2 hardcode + clamp [0,6])"
  - "[x] Tách code thật sang T152 (docs closure 0 code / 0 DB / 0 Schema)"
---

# T151 — Pháp Mạch Ancestor Spine — Docs Closure (acceptance framework, additive)

> **Module:** `truyenthua` (Pháp Mạch · DILA · CBETA provenance)
> **Priority:** high · **Status:** pending (canonical docs — acceptance framework, docs-only)
> **Type:** docs closure (additive, 0 ALTER, 0 Schema, 0 DB, 0 API, 0 code)
> **Created:** 2026-09-17 · **Updated:** 2026-09-17
> **Depends on:** T150 (Lineage Integrity & Review Pipeline docs DONE) → T148/T149 (code rehab DONE)
> **SSOT canonical:** `tasks/T151-phap-mach-ancestor-spine-docs-closure.md` (1 unique, mirror T148/T149/T150)
> **Implements (docs):** User spec "Pháp Mạch luôn trace ngược về Bồ-đề Đạt-ma từ focus" (2026-09-17) — doc-spec RIÊNG, code ở T152.

---

## 1. Vấn đề (problem)

Pháp Mạch hiện giới hạn ancestor chain theo button **2 đời / 3 đời**. Khi người dùng
chọn một thiền sư ở đời sau, KHÔNG thấy trọn mạch ngược về Bồ-đề Đạt-ma.

Đối chiếu code THẬT (`Dai_Tang_Kinh/daoanh/places.html`, 9,054 dòng, 61;0 bytes):

| # | Điểm code | Hành vi thật | Ảnh hưởng |
|---|-----------|--------------|-----------|
| 1 | `loadLineageTree` :4865 | fetch `lineage-tree?up=2&down=2` hardcode | payload chỉ chứa ≤2 đời thầy |
| 2 | `centerLineageOn` :5032 | fetch `up=2&down=2` khi đổi tâm | re-center cũng mất spine >2 |
| 3 | `_renderLineageNetwork` :6226-6227 | `keep = reachable && (all || gen>=-above && gen<=below)` | display cắt ancestor khi `above<2` |
| 4 | `_t129NetCtrlBar` :6167 | 'Thu gọn' reset `{above:2, below:2, all:false}` | cắt spine tổ về 2 |
| 5 | `_renderLineageChain` :6032-6057 | ancestor loop vẽ mọi `ancestors` từ `parents` (đã cycle-safe `seenUp`) | renderer ĐÃ sẵn sàng vẽ deep spine — chỉ bị chặn ở DATA |
| 6 | BUG-011 comment :5052-5054 | refetch `_lineageExpandRefetch` khi vượt `d.up` | max `up=6` server clamp — vẫn không tới gốc nếu >6 đời |
| 7 | :6151-6156 | 'Mở thêm đời trên ↑' tăng `above` + refetch | network mode chỉ mở thêm 1 đời/cú click |

**Kết luận gốc sự cố:** renderer Pháp Mạch ĐÃ có khả năng vẽ spine vô hạn
(`_lineageBuildRows` climb `parents` `while` + `seenUp`), nhưng **payload** chỉ mang
`up=2` (max 6 theo server) → spine bị cắt ở **tầng dữ liệu**, không phải tầng vẽ.
"2 đời/3 đời" hiện chỉ điều khiển phần descend (đúng spéclược) nhưng ancestor
bị khóa cứng ở 2.

## 2. Nguyên tắc (principles)

1. **Spine ancestor luôn đầy đủ** — từ focus ngược RA gốc (Bồ-đề Đạt-ma / đầu mạch có dữ liệu), độc lập với button 2/3 đời.
2. **2 đời / 3 đời CHỈ điều khiển độ sâu PHÍA DƯỚI** (descendant) — KHÔNG chạm phần tổ.
3. **'Thu gọn' KHÔNG cắt spine** — đổi ngữ nghĩa "Thu gọn nhánh dưới".
4. **Chỉ dùng quan hệ ĐÃ XÁC MINH** — spine đi qua `marcus_networks` + lọc `rejected` (`_t138_edge_assertions`), mirror `api_monk_lineage_tree`. KHÔNG vẽ cạnh disputed/rejected vào mạch chính.
5. **Stop-at-broken HONEST** — khi khúc cạnh thiếu/bị reject → banner lý do (Mạch thiếu cạnh đã xác minh / Quan hệ còn mâu thuẫn / Chưa map được nhân vật) + CTA; KHÔNG tự suy đoán vượt khúc đứt.
6. **Additive** — 0 ALTER, 0 Schema, 0 DB, 0 migration. Chỉ thêm endpoint đọc + UI.

## 3. Phạm vi (acceptance framework — docs closure, additive)

### 3.1 Resolution target

```text
Pháp Mạch (từ focus bất kỳ):
    col -(depth)  ... col -1  col 0(focus)  col 1..n (desc)
    ▲ spine đầy đủ                         ▲ chỉ đúng SỐ ĐỜI user chọn (2/3/thu gọn)
    mọi node 'verified' non-rejected        (KHÔNG bao giờ bị cắt phía trên)
    dừng ở đầu mạch / khúc cạnh thiếu
```

### 3.2 Acceptance criteria (định nghĩa DONE cho T152)

- [ ] A1. Mở Focus thiền sư bất kỳ có lineage → spine ngược tới đầu mạch đầy đủ (không còn cắt ở 2 đời).
- [ ] A2. Nút 'Mở 2 đời'/'Mở 3 đời' chỉ thêm/đổi số đời PHÍA DƯỚI — spine phía trên giữ nguyên.
- [ ] A3. Nút 'Thu gọn' (2 chế độ) → chỉ thu dãn phần descendant, KHÔNG xóa cột tổ phía trên.
- [ ] A4. Node đầu mạch: dán nhãn "⚠ đầu mạch" khi `has_more_up` sai (đã tới gốc dữ liệu).
- [ ] A5. Khi khúc cạnh phía trên bị thiếu/reject → hiện banner lý do trung thực + CTA (không vẽ cạnh giả).
- [ ] A6. Safety: tối đa 80 hops từ focus lên (chống loop/độ sâu vô hạn) + cycle-safe (`seen` set).
- [ ] A7. 0 thay đổi DB; endpoint mới read-only; chỉ renderer dùng spine; UI events giữ nguyên.
- [ ] A8. `npm run pipeline` PASS (lint · test · e2e) + reviewer xác nhận browser thật.

### 3.3 Điều kiện hoàn thành (done_when)

- [ ] Canonical task `tasks/T151-phap-mach-ancestor-spine-docs-closure.md` (1 unique, 0 dup) — docs-only, additive, mirror T150
- [ ] ROLLBACK row T151 (placeholder → hash-fill 2-pass real `git rev-parse`, 0 gõ hash tay) · dashboard json regen real (`scripts/build_progress_data.py` → `data/progress_data.json`)
- [ ] Canonical session `docs/sessions/2026-09-17_t151-*.md` (1, UTF-8 sạch) &nbsp;·&nbsp; tasktodo.md row T151
- [ ] Cleanup leftover scripts `*t151*` = 0 · verify git log T151 (closure commit + hash-fill)

## 4. Rollback

```bash
git revert --no-edit <sha_closure_T151>
# + revert T152 (code) nếu cần: git revert --no-edit <sha_code_T152>  — chỉ 2 file UI/endpoint
# = echo ROLLBACK row T151 (docs-only, additive — 0 code revert)
```

## 5. Checkpoints (ZQ review)

- [x] Spine phải đầy đủ tới đầu mạch — độc lập button 2/3 đời
- [x] 2/3 đời = chỉ depth chòm trò (descendant)
- [x] Thu gọn không cắt tổ
- [x] Chỉ dùng cạnh verified non-rejected cho mạch chính
- [x] Stop-at-broken + banner lý do HONEST (không suy đoán)

---

*Canonical docs closure T151 — additive, 0 ALTER, 0 Schema, 0 DB, 0 code. Code thật: T152 (spine endpoint + renderer). Nguồn: Marcus Bingenheimer · DILA · lineage_edge_assertions · places.html (thật).*