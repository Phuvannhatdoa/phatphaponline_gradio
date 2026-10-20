# M8 · Nền cộng đồng Phật học

**Spec · P2**

# M8 Cộng đồng Phật học

Cộng đồng Phật học: practice tracking, retreat records, dana management, community records.

## Mục đích

Xây dựng hệ thống theo dõi practice Phật học, quản lý retreat, dana và records cộng đồng.

## UI/UX

- **Trang practice tracking:** `/daoanh/practice/tracking`
  - Nhật ký méditation hàng ngày, giữ giới, tu practice
  - Theo dõi streak ngày/tháng/năm
  - Loại practice: méditation, kinh đọc, tuân giới, charity

- **Trang retreat management:** `/daoanh/retreat/management`
  - Đăng ký retreat, theo dõi tiến độ
  - Check-in/check-out tự động
  - Đánh giá retreat sau khi kết thúc

- **Trang dana management:** `/daoanh/dana/management`
  - Theo dõi tiền góp, chi phí, nguồn vốn
  - Báo cáo tài chính minh bạch
  - Phân loại: temple, individual, retreat center

- **Sangha directory:** `/daoanh/sangha/directory`
  - Danh sách thành viên, vai trò, lịch sử tham gia
  - Badge xác minh: thầy tọt, sư cao, practitioner

## Dữ liệu

- **BuddhaNexus** – Text reuse project, practice records (CC BY-SA)
- **DharmaNet** – Network các center, sangha toàn cầu (phi thương mại)
- **Retreat centers** – Data từ 108 retreat center nổi tiếng (mỗi center cung cấp dữ liệu)
- **Practice communities** – Online sangha, forum pratica (CC BY)

## Acceptance criteria

- [ ] Practice tracking ghi nhận streak ngày tháng, hỗn hợp practice type
- [ ] Retreat management hỗ trợ check-in/check-out tự động
- [ ] Dana tracking xuất báo cáo tài chính minh bạch
- [ ] Sangha directory liệt kê 50+ thầy tọt có badge xác minh
- [ ] Community reports hiển thị growth metrics tuần/tháng/năm

## File tương tự

- `docs/integration/M8-community-buddhist.md`