---
id: T13
title: CBDB → chatling.AI viết mượt + ghi chú Việt
module: CBDB
priority: low
status: pending
depends_on: []
created: 2026-08-13
updated: 2026-08-24
done_when: Nút "Gửi cho chatling.AI viết mượt" xuất dữ liệu CBDB + lưu vào ghi chú Việt ngữ
---

## ⚠️ ĐỀ XUẤT HỦY — 2026-08-24

**Lý do:** CBDB (China Biographical Database) không nằm trong 20 nguồn ưu tiên TGS. Chức năng "AI viết mượt" bị superseded bởi T11 (RAG Việt) khi mở lại. Phụ thuộc Gemini key (như T11/T12 đang treo). Scope CBDB (nhân vật lịch sử TQ) không phải ưu tiên của PTDA hiện tại.

**Quyết định cần admin:** Confirm hủy task này → sẽ đổi status thành `cancelled`.

---

# T13 — CBDB → chatling.AI viết mượt + ghi chú Việt

## Mục tiêu
Progress CBDB: thêm nút "Gửi cho chatling.AI viết mượt và lưu vào ghi chú Việt ngữ" cho kết quả CBDB.

## Cách tiếp cận
- Nút bên cạnh khối CBDB trong sidebar.
- Gửi dữ liệu CBDB cho chatling.AI (prompt viết mượt tiếng Việt).
- Lưu kết quả vào ghi chú Việt ngữ của entity (DB ghi chú).

## Acceptance criteria (checklist)
- [ ] Nút "Gửi cho chatling.AI" hiển thị
- [ ] Xuất được dữ liệu CBDB ra chatling.AI
- [ ] Kết quả lưu vào ghi chú Việt ngữ
- [ ] Không break has_cbdb/cbdb_places[]
