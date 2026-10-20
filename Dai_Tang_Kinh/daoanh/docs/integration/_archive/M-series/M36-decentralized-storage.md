# M36 · Bộ phân tán dữ liệu cho Tiến sĩ

**Spec · P2**

# M36 Hệ thống lưu trữ phi tập trung (Decentralized Storage)

Cung cấp giải pháp lưu trữ phi tập trung cho dữ liệu Kinh Đạo Phật: IPFS, Filecoin, và các mạng lưới tập trung khác để đảm bảo tính bền vững và chống kiểm chế.

## Mục đích

Đảm bảo dữ liệu Kinh Đạo Phbat được lưu trữ bền vững, không bị mất trong dài hạn, và có thể truy xuất bất cứ lúc nào mà không phụ thuộc vào một server trung tâm.

## UI/UX

- **Trang Dashboard Lưu trữ:** `/daoanh/storage/dashboard`
  - Tổng quan: Kích thước dữ liệu, số file, trạng thái sync
  - Trạng thái IPFS: Da thêm, đang sync, offline
  - Kích thước lưu trữ: DILA-token còn lại, tỷ lệ sử dụng

- **Trang Thêm file:** `/daoanh/storage/add`
  - Tải lên file Kinh, văn bản, metadata
  - Chọn lưu trữ: IPFS, Pinata, Filecoin
  - Xem CID (Content ID) sau khi upload

- **Trang Xem file:** `/daoanh/storage/view/:cid`
  - Hiển thị nội dung file đã lưu
  - Thông tin: CID, kích thước, ai upload, lúc nào
  - Tải về, Share CID

## Dữ liệu

- **IPFS:** IPFS network (InterPlanetary File System)
- **CID:** Content Identifier cho từng file
- **Pinning:** Pinning service (Pinata, Infura) đảm bảo file không bị xóa
- **Metadata:** Tên file, mô tả, ngày upload, hash SHA-256

## Acceptance criteria

- [ ] Upload file dưới 10MB hoàn tất dưới 30s
- [ ] CID được tạo ra và hiển thị ngay sau upload
- [ ] Trạng thái IPFS hiển thị đúng (Da thêm/Offline)
- [ ] Truy xuất file qua CID hoạt động đúng 95% trường hợp
- [ ] Tích hợp metadata (tên Kinh, tác giả) lưu cùng file

## File tương tự

- `docs/integration/M36-decentralized-storage.md`
- `docs/Mimo-Flash/T111-m36-decentralized-storage.md`