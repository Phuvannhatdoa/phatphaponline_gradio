# M52 · Blockchain Phát tán cho Dữ liệu Phật Giáo

**Spec · P2**

# M52 Blockchain Phát tán

Áp dụng công nghệ Blockchain phác tán để lưu trữ và phân phối dữ liệu Phật giáo: IPFS, Filecoin, và các mạng lưới phác tán đảm bảo tính bền vững và chống kiểm chế cho dữ liệu kinh và tài liệu học thuật.

## Mục đích

Độ bao phác tán dữ liệu Phật giáo qua nhiều nút phác tán, đảm bảo dữ liệu không bao giờ bị mất vì điểm single point of failure, và cung cấp truy cập nhanh từ bất kỳ đâu trên thế giới.

## UI/UX

- **Trang Dashboard Phác tán:** `/daoanh/blockchain/distributed`
  - Tổng quan: Số nút phác tán, trạng thái đồng bộ, kích thước dữ liệu
  - Trạng thái IPFS: Da phác tán, Đang phác tán, Offline
  - Kích thước dữ liệu: Tổng kích thước, kích thước phác tán đang hoạt động

- **Trang Phát tán file:** `/daoanh/blockchain/distribute`
  - Tải lên file Kinh, văn bản, metadata
  - Chọn phác tán: IPFS, Pinata, Filecoin
  - Xem CID (Content ID) và trạng thái phác tán sau khi upload

- **Trang Xem file phác tán:** `/daoanh/blockchain/view/:cid`
  - Hiển thị nội dung file đã phác tán
  - Thông tin: CID, kích thước, số nút phác tán, ai upload, lúc nào
  - Tải về, Share CID, Kiểm tra trạng thái phác tán

## Dữ liệu

- **IPFS Network:** Phác tán dữ liệu qua mạng IPFS
- **CID:** Content Identifier cho từng file phác tán
- **Pinning Service:** Pinata, Infura, hoặc các dịch vụ phác tán khác
- **Metadata:** Tên file, mô tả, ngày upload, hash SHA-256, số nút phác tán

## Acceptance criteria

- [ ] Tạo CID cho file dưới 10MB hoàn tất dưới 30s
- [ ] Số nút phác tán hiển thị chính xác
- [ ] Trạng thái IPFS hiển thị đúng (Da phác tán/Offline)
- [ ] Truy xuất file qua CID hoạt động đúng 95% trường hợp
- [ ] Tích hợp metadata (tên Kinh, tác giả) lưu cùng file phác tán

## File tương tự

- `docs/integration/M52-blockchain-distributed.md`
- `docs/Mimo-Flash/T127-m52-blockchain-distributed.md`