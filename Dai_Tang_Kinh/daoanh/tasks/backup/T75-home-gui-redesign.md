# T75 — HOME GUI Redesign: Search-first Hero + 6 Module Cards

**Status:** [x] done — implemented 2026-08-30, commit e5dd4fc  
**Phase:** Bước 8  
**Approved:** 2026-08-30  
**Mockup artifact:** https://claude.ai/code/artifact/7c6fd489-47f7-4319-b41d-88b23bcff41e  
**Spec doc:** `docs/HOME-redesign-approved-2026-08-30.md`

## Mục tiêu

Viết lại `daoanh/home.html` theo thiết kế search-first: thay cấu trúc accordion + 15 TABs hiện tại bằng hero search + 6 module cards đơn giản, trực quan hơn. Sub-tasks T76–T79 triển khai từng phần.

## Acceptance criteria

- [x] Hero: input search chiếm trung tâm, placeholder "Nhập địa danh, tu sĩ, kinh điển…", nút submit
- [x] Search "Thiếu Lâm" / "少林" → hiện inline panel `#placeResult` (demo), không redirect
- [x] Search bất kỳ query khác → redirect `/daoanh/places?q=<query>`
- [x] 6 module cards layout đúng màu sắc: Địa Danh (gold), Đại Tạng (amethyst), Tu Sĩ (teal), Truyền Thừa (rose), Niên Đại (sky), Đồ Thị Quan Hệ (amber)
- [x] Panel Thiếu Lâm Tự: header multilingual (VN/HV/EN), 6-field info grid, SVG mini-map Hà Nam, CTA → `/daoanh/places?q=PL000000023255`
- [x] Dark-first token palette: `--da-bg: #0B0E17`, `--da-gold: #C9A84C`
- [x] Responsive: desktop + mobile, không horizontal scroll
- [x] Fonts: Noto Serif SC (display), Inter (UI) — Google Fonts CDN

## Liên quan

- T76: inline place panel `#placeResult`
- T77: 6 module cards grid
- T78: JS wiring `handleSearch` / `showPlaceDemo` / `closePlaceDemo`
- T79: verify + VPS sync (sau T24–T27)
