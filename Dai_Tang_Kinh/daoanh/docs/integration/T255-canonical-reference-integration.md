---
id: T255
former_ids: [T188]
title: "Canonical Reference Integration — Canonical Reference Integration (Canonical Reference Integration)"
module: Hạ tầng / Docs
priority: high
status: in_progress
owner: mimo-flash (docs) · claudecode (code gates)
depends_on: [M0, M1, M4, M5]
created: 2026-10-02
updated: 2026-10-02
---

# T255 — Canonical Reference Integration (Canonical Reference Integration)

**Status:** 🟠 IN-PROGRESS (2026-10-02 Admin phê chuẩn — tạo task Txx cho kế hoạch tích hợp 25 nguồn)
**Lane:** docs/logs = mimo-flash · code gates G0–G2 = Claude Code · G3 = ops (Admin/mimo-flash)
**Loại:** integration task — mô tả chức năng cần có, gõi cho Claude Code triển khai.
**Prompt sẵn có (không viết lại):** `M4_doi_chieu_kinh_dien.md` (review + SPEC) · `M5_ghi_nguon_tuan_thu.md` (review + spec) · `00_PLAN_OVERVIEW.md` (quyết định 25 nguồn) · `T185-source-hub-license-gate.md` (gate trước ETL) · `T187-geo-review-integration.md` (review + UI).

## Mục tiêu

Mô tả chức năng tích hợp **Kinh điển đa ngữ** (Hán – Pali – Sanskrit) bằng **ID và đường dẫn**, không sao chép văn bản có giấy phép hạn chế.

- Mỗi dòng ghi: **Link** (chỉ đường dẫn), **Metadata**, **Văn bản** (chỉ hiện khi nguồn ACTIVE + giấy phép cho phép).
- Trạng thái rỗng nói rõ: chưa có song song trong các nguồn đã bật, kèm nút **"Gửi yêu cầu dữ liệu"** (dùng `data_gap_requests` sẵn có).
- Khi nguồn ngoài không trả lời, vẫn hiện danh sách đã lưu trong **24 giờ** và đánh dấu cũ.
- Mỗi dòng có **badge nguồn** và **link gốc** hoạt động.

## Bối cảnh hệ thống (2026-10-02, read-only)

| Năng lực | Trạng thái |
|---|---|
| Tìm kiếm tên Kinh/Hán/Việt | ❌ API `/daoanh/api/search` trả 404 (không tồn tại) |
| Tìm kiếm ID Toh/SC uid | ❌ Không có endpoint hỗ trợ |
| Trang Credits / Badge nguồn | ❌ Chưa có giao diện集中式 |
| Mức Văn bản chỉ hiện khi ACTIVE | ❌ Chưa implement theo M5 |
| Quá trình gửi yêu cầu dữ liệu | ❌ Chưa có `data_gap_requests` workflow |

**Gốc nguyên:** 09-29 batch sync rơi vào working tree không qua git → làm rớt `adapters/` · `gate/` · `docs/integration/` · `data/`. Gần như toàn bộ chức năng integration được mô tả trong `docs/integration/` (M0–M5) **chưa được triển khai code**.

**Lộ trình khôi phục:**
1. **G0** (PROMPT-C0) → pipeline xanh → khóa `finalize_lock` → code chạy lại.
2. **T185** (Source Hub License Gate) → cổng trước ETL.
3. **T187** (Geography Review) → UI hàng đợi khớp tọa độ.
4. **T255** (Canonical Reference Integration) → UI tab Đối chiếu + badge + link + Văn bản.

## Acceptance

- [ ] G0: `npm run pipeline` **PASS** (test:rules hết ImportError `finalize_lock`).
- [ ] T185: Cổng License Gate tích hợp → `entity_claims` không ghi nếu cổng từ chối.
- [ ] T187: UI hàng đợi khớp tọa độ → Accept/Reject/Kể sau có dòng audit.
- [ ] T255: Tab Đối chiếu → badge nguồn + link gốc + Văn bản khi ACTIVE.
- [ ] T182: 4 số trang chủ = số query DB (comment nguồn+ngày trong HTML).
- [ ] G3: `:37700` trả JSON (hoặc Admin chốt phương án thay thế).

## Revert

Docs-only: `git revert --no-edit <sha_T255>` (row `docs/ROLLBACK.md`).
Code: xem mục Revert của G0/G1/G2 — không có thao tác DB trong integration này.