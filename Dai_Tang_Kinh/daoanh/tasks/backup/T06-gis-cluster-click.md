---
id: T06
title: GIS cluster click handler + tối ưu icon mật độ
module: GIS / Places
priority: medium
status: done
depends_on: []
created: 2026-07-29
updated: 2026-08-18
done_when: Click cluster → zoom-to-bounds; icon cluster tối ưu theo mật độ
---

# T06 — GIS cluster click handler + tối ưu icon mật độ

## Mục tiêu
Cluster trên bản đồ Đạo Ảnh chưa zoom-to-bounds khi click (Khoá 1 / GIS). Thêm handler click + tối ưu icon cluster theo mật độ (theo progress GIS 2026-08-13).

## Cách tiếp cận
- Gắn sự kiện click trên cluster → `map.fitBounds(cluster.getBounds())`.
- Đổi icon/badge cluster theo mật độ (màu/badge kích thước).
- Đảm bảo không ảnh hưởng progressive batch loading 800/lần.

## Acceptance criteria (checklist)
- [x] Click cluster zoom to bounds
- [x] Icon cluster thay đổi theo mật độ (badge/size/color)
- [x] Không break progressive loading (11.267 địa danh)
- [ ] Test cả mobile (375px)
- [x] Không break E2E console
