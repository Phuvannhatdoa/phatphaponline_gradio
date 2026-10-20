---
id: T345
title: "Archive Uu-Tien — lô 05: rà soát và phân loại (10 file)"
module: Archive review
priority: p3
status: pending
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phủ toàn bộ, T323+)
depends_on: []
done_when: |
  Mọi file trong danh sách được rà soát và có nhãn; Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Task chỉ đọc và ghi nhãn trong tài liệu; không xóa file, không đổi DB.
outcome: >
  2026-10-10: tạo task phủ folder docs/integration. Chưa bắt đầu.
---

# T345 — Archive Uu-Tien — lô 05: rà soát và phân loại (10 file)

## 1. Danh sách file phủ bởi task này

- `docs/integration/Uu-Tien-2-T45-mala-counter-consolidated.md`
- `docs/integration/Uu-Tien-2-T46-prediction-risk-consolidated.md`
- `docs/integration/Uu-Tien-2-T47-bookmarks-consolidated.md`
- `docs/integration/Uu-Tien-2-T48-decentralized-governance-consolidated.md`
- `docs/integration/Uu-Tien-2-T49-dashboard-finalization-consolidated.md`
- `docs/integration/Uu-Tien-2-T50-neural-network-consolidated.md`
- `docs/integration/Uu-Tien-2-T51-advanced-knowledge-graph-consolidated.md`
- `docs/integration/Uu-Tien-2-T52-blockchain-distributed-storage-consolidated.md`
- `docs/integration/Uu-Tien-2-T53-personalized-learning-paths-consolidated.md`
- `docs/integration/Uu-Tien-2-T54-quantum-computing-consolidated.md`

## 2. Việc cần làm

Với từng file: so với file M cùng số module; nếu trùng ý thì ghi ĐỀ-XUẤT-GỘP, nếu khác thì ghi nhãn như lô M-series. Không xóa.

## 3. Ràng buộc

- Không xóa file trong `docs/integration/_archive/`. Mọi thay đổi tên hoặc chuyển file phải có manifest.
- Không git commit/push.

## 4. Các bước

- [ ] **Bước 1 —** liệt kê file và đọc tiêu đề, mục đích
- [ ] **Bước 2 —** ghi nhãn từng file (bảng trong file này)
- [ ] **Bước 3 —** Admin xác nhận nhãn
