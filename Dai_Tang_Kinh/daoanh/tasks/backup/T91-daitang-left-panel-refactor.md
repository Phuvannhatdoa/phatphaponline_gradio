---
id: T91
title: "Tab Đại Tạng — Refactor Panel Trái (Người Sáng Lập · Liên Quan · Nguyễn Minh Tiến)"
module: tab-daitang
priority: medium
status: done
depends_on: [T88]
created: 2026-09-04
updated: 2026-09-04
done_date: 2026-09-04
done_when: "Panel trái tp-daitang hiển thị đúng thứ tự: Nguồn Học Thuật → Bảng thống kê → Người Sáng Lập → Liên Quan → Nguyễn Minh Tiến placeholder"
---

## Mục tiêu

Tái cấu trúc panel trái (`#tp-daitang / #daitang-content`) để:

1. Bỏ các lớp nội dung CBETA/Hán văn chi tiết (đã có ở main panel 5-tab)
2. Thêm section Người Sáng Lập (curated persons từ place_person_link)
3. Thêm section Liên Quan (canonical persons + places co-mentioned)
4. Thêm placeholder "Đại Tạng Kinh Nguyễn Minh Tiến" cho tương lai

## Acceptance Criteria

- [x] Bỏ LỚP 1 (CBETA ref list) khỏi panel trái
- [x] Bỏ LỚP 2 (Hán văn passage cards) khỏi panel trái
- [x] Bỏ LỚP 3 (canon catalog) khỏi panel trái
- [x] Giữ Header + Bảng thống kê
- [x] Thêm section 👤 NGƯỜI SÁNG LẬP (async fetch /related, filter source='curated')
- [x] Thêm section 🔗 LIÊN QUAN (canonical persons + places)
- [x] Thêm section 📚 ĐẠI TẠNG KINH NGUYỄN MINH TIẾN (placeholder)
- [x] Main panel 5-tab (Dẫn Chiếu/Nguyên Văn/Quan Hệ) không bị ảnh hưởng

## Ghi chú kỹ thuật

- Field badge trong related API là `source` ("curated"/"canonical"), không phải `badge` ("CURATED")
- Related API không trả `success` field — guard phải check `rd.persons || rd.places`
- Dữ liệu Nguyễn Minh Tiến chưa có trong DB — cần task riêng (T92?) để import
