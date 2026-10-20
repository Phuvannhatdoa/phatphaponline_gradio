# M19 · Tích hợp Mobile cho Cử Nhân

**Spec · P1**

# M19 Ứng dụng Mobile

Cung cấp ứng dụng mobile đồng bộ cho trình độ Cử Nhân: native app (iOS/Android), offline-first, push notifications, và QR code sharing.

## Mục đích

Đoạn dựng trải nghiệm tra cứu Kinh Đạo Phật trên thiết bị mobile cho người dùng Cử Nhân: ứng dụng native, truy cập offline, và chia sẻ dễ dàng.

## UI/UX

- **Ứng dụng Native:**
  - **iOS:** SwiftUI, Dark Mode, VoiceOver 지원
  - **Android:** Jetpack Compose, Dark Mode, TalkBack 지원
  - **Giao chung:** Bottom navigation, Floating action button (search), Pull-to-refresh

- **Trang chính (Home):**
  - Search bar ở đầu, Quick access đến 4 mục: Monk, Lineage, Geography, Scripture
  - Widget: hiển thị ngày bài học, Monk of the day

- **Trang Offline:**
  - Cache local: 100+ kinh nổi tiếng, 50+ monk biography
  - Sync khi có mạng: background sync, conflict resolution

- **Push Notifications:**
  - Monk birthday anniversary
  - Scripture reading reminder
  - New content available

- **QR Code Sharing:**
  - Share profile monk, lineage chart, place details
  - Scan để xem thêm thông tin trên web

## Dữ liệu

- **Local storage:** SQLite encrypted (Zero-RAM principle)
- **Sync engine:** Delta sync (chỉ gửi thay đổi sinds last sync)
- ** offline cache:** 100 most queried entities, 50 most popular scriptures
- **Push service:** Firebase Cloud Messaging (FCM)

## Acceptance criteria

- [ ] App khởi động dưới 2s trên mobile trung bình
- [ ] Offline mode hiển thị được 100+ nội dung quan trọng
- [ ] Sync hoàn tất trong 30s cho thay đổi cơ bản
- [ ] Push notification test thành công trên 2 thiết备 (iOS + Android)
- [ ] QR code encoding/decoding không lỗi cho 90% sample

## File tương tự

- `docs/integration/M19-mobile-integration.md`
- `docs/Mimo-Flash/T94-m19-mobile-integration.md`