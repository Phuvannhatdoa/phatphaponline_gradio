---
id: T246
title: "M7 — WHG Client: reconcile (LPF 1.1) + tôn trọng rate-limit + HTTP 451"
module: GIS / Places
priority: medium
status: pending
depends_on: [T245]
created: 2026-10-06
updated: 2026-10-06
done_when: "Client WHG gọi /reconcile trả LPF 1.1, giới hạn 50/lô · 600/phút · 5000/ngày; dừng khi nhận HTTP 451 (quyết định renew)."
---

# T246 — M7 · WHG Client

> Nguồn đặc tả (Single Source): `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` (M7 toàn cầu).

## 📎 Liên kết các phần khác — MỞ TRƯỚC KHI DEV
| Phần | Đường dẫn | Dùng để |
|---|---|---|
| Đặc tả M7 | `docs/integration/Uu-Tien-1-T07-gis-buddhist-maps-consolidated.md` | §Data WHG + §Acceptance (rate-limit/451) |
| T245 | `tasks/T245-m7-reference-linkage-geo-cross-ref.md` | Lưu kết quả đối chiếu |
| Script dir | `scripts/` | Client WHG |

## Mục tiêu
Client **WHG (World Historical Gazetteer)** đối chiếu qua `/reconcile`, định dạng **LPF 1.1**,
chỉ dùng cho đối chiếu (không là nguồn chính), tuân thủ giới hạn tốc độ và **HTTP 451**.

## Cách tiếp cận
1. Gọi `WHG /reconcile` → parse **LPF 1.1**.
2. Rate-limit: **50 truy vấn/lô · 600/phút · 5.000/ngày** (chờ/backoff thích hợp).
3. Khi nhận **HTTP 451** → dừng toàn bộ, ghi trạng thái `renew` (quyết định gia hạn).
4. Chỉ dùng kết quả làm ứng viên đối chiếu → nạp vào `geo_cross_ref` (T245).

## Ràng buộc
- Zero-RAM, không vượt ngưỡng tốc độ, ghi nguồn WHG.

## Acceptance criteria
- [ ] Gọi `/reconcile` trả LPF 1.1 parse được.
- [ ] Tôn trọng giới hạn 50/600/5000; dừng sạch khi HTTP 451.
- [ ] Kết quả chỉ là ứng viên đối chiếu (không tự ghi nhận chính thức).