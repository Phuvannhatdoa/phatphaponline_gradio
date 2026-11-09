---
id: T475
title: "Tìm nguồn và tích hợp CBETA metadata (triều đại, tác giả, dịch giả) cho PTDA"
status: deferred
created: 2026-10-26
updated: 2026-10-26
owner: coordinator
module: Data / CBETA / Metadata
priority: low
depends_on: []
done_when: >
  (1) Xác định nguồn chính thức (repo hoặc bản tải) của CBETA metadata: tên file, phiên bản, giấy phép; ghi vào task.
  (2) Tải về vào data/dila_import/ kèm SHA256; không ghi DB ở bước này.
  (3) Đối chiếu với cbeta_catalog_vn (3.122 dòng) và dila_catalog_* để báo chênh lệch.
  (4) Đề xuất phạm vi tích hợp, chờ Admin duyệt.
  (5) daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  Xoá thư mục tải về. Không đụng DB.
---

## Mô tả
Để sau, chỉ kích hoạt khi có nhu cầu cụ thể (Admin, 2026-10-26).

CBETA có bộ metadata về tác giả, dịch giả, triều đại và phân loại kinh. Hiện PTDA có `cbeta_catalog_vn` (3.122 dòng) nhưng chưa biết có bao nhiêu trường triều đại và tác giả. Task này tìm nguồn chính thức trước, sau đó mới quyết định tích hợp.

## Nguồn
- **Chưa xác nhận.** Tìm kiếm web không thấy repo `cbeta-metadata` trực tiếp. Có thông tin về CBETA Research Platform với dữ liệu tác giả, dịch giả, niên đại: [CBETA](https://cbeta.org/en/faq), [Copyright Notice](https://cbeta.org/en?p=29137).
- Cần kiểm tra trực tiếp trên [github.com/DILA-edu](https://github.com/DILA-edu) hoặc [github.com/cbeta-org](https://github.com/cbeta-org).

## Phạm vi
- Trong: tìm nguồn, tải về, đối chiếu, đề xuất.
- Ngoài: ghi DB trong task này.

## Căn cứ hiện có
- WebSearch 2026-10-26: trang [github.com/DILA-edu](https://github.com/DILA-edu) liệt kê các repo cbeta-api, cbeta-metadata, cbeta-documentation. Chưa mở kiểm tra trực tiếp.

## Ghi chú
Giấy phép CBETA là CC BY-NC-SA 4.0 (theo ghi nhận trước đó). Cần ghi công khi dùng.
