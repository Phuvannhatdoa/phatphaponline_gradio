# M32 · Buddhist Blockchain Research

**Status:** 📄 Consolidated Documentation  
**Module:** M32  
**Created:** 2026-10-02  
**Single Source:** Claude Code có thể "plant and code" từ file này duy nhất.

## Mục đích

Cung cấp blockchain cho nghiên cứu Phật học: sử dụng blockchain để lưu trữ và chia sẻ dữ liệu nghiên cứu Phật học, đảm bảo tính bền vững và không thể thay đổi (immutable) của dữ liệu nghiên cứu.

## UI/UX

- **Trang Lưu trữ nghiên cứu:** `/daoanh/research/storage`
  - Lưu trữ bài bản nghiên cứu: Tiêu đề, tác giả, bản tóm tắt, dữ liệu
   - Trạng thái: Đang lưu trữ, Đã xác minh, Cần kiểm tra lại

- **Trang Phát tán nghiên cứu:** `/daoanh/research/distribution`
  - Phát tán bài bản nghiên cứu: Chia sẻ qua blockchain, xem lượt xem, lượt tải
   - Xem chi tiết: Chi tiết bài bản, bình luận, tương tác

- **Trang Kiểm tra xác minh:** `/daoanh/research/verification`
  - Kiểm tra xác minh: Hash, chữ ký số, nguồn gốc
   - Xuất báo cáo: Xuất báo cáo xác minh ra file PDF

## Dữ liệu

- **Bài bản nghiên cứu:** 1000+ bài bản nghiên cứu Phật học đã lưu trữ
- **Thuật toán:** Hash (SHA256), chữ ký số (ECDSA)
- **Nền tảng blockchain:** Ethereum, Polygon
- **Thiết bị hỗ trợ:** Điện thoại, tablet, desktop

## Acceptance criteria

- [ ] Lưu trữ 1000+ bài bản nghiên cứu trên blockchain
- [ ] Xác minh đúng 95% bài bản nghiên cứu
- [ ] Phát tán bài bản đúng 80% qua blockchain
- [ ] Tương thích với các nền tảng blockchain: Ethereum, Polygon
- [ ] Bảo mật dữ liệu: Không lộ thông tin nghiên cứu nhạy cảm

## Implementation Notes for Claude Code

**Single-file implementation:** Claude Code có thể "plant and code" từ file này duy nhất mà không cần reference file Task khác.

**Key functions cần implement:**
1. `storeResearchPaper(paper)` - Lưu trữ bài bản nghiên cứu
2. `verifyResearchPaper(paperId)` - Xác minh bài bản nghiên cứu
3. `distributeResearchPaper(paperId)` - Phát tán bài bản nghiên cứu
4. `getVerificationDetails(paperId)` - Lấy chi tiết xác minh

**File path:** `docs/Mimo-Flash/M32-blockchain-research-consolidated.md`  
**Dependencies:** Module M0 (base foundation already created), blockchain platform (Ethereum/Polygon), smart contracts