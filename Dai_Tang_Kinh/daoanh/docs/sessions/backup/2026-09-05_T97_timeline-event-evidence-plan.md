# 2026-09-05 — T97: Timeline / Event Evidence Layer — Phê chuẩn & Kế hoạch

## Phê chuẩn

**Ngày:** 2026-09-05  
**Admin:** namthien@gmail.com  
**Trạng thái:** APPROVED — tạo task T97, chờ Plan Agent chạy Phase 0

---

## Nguồn gốc

Từ thảo luận về prompt Plan Agent cho "Timeline / Event Evidence Layer".
Sau khi review logic prompt, đã xác định và sửa 4 vấn đề:

| # | Vấn đề | Sửa |
|---|--------|-----|
| 1 | Output dir "VPS-Task" không tồn tại | Đổi thành `docs/sessions/YYYY-MM-DD_T97_...md` |
| 2 | URL `localhost:8080` agent không browse được | Bỏ URL, dùng DILA Place ID |
| 3 | `time_mentions` ↔ `events` không có link | Thêm `time_mention_id` vào `event_evidence` |
| 4 | Không chỉ rõ CLAUDE.md cần đọc đầu tiên | Thêm vào mục A |

---

## Quyết định kiến trúc (đã phê chuẩn)

### ĐƯỢC làm ngay (Phase 0-1)
- Plan Agent đọc kiến trúc thật, kiểm kê data hiện hữu
- POC Thiếu Lâm Tự: tìm internal ID, raw desc, CBETA ref
- Đề xuất schema tối thiểu, ưu tiên adapter với bảng hiện có

### CHƯA làm (chờ Phase 0 xong và APPROVED lần 2)
- Tạo/sửa schema, migration
- Import bulk, gọi AI để extract
- Sửa UI hiện có

### Không bao giờ làm trong T97
- Full-corpus event extraction
- Crawl/import Phật Quang Sơn
- Ghi đè raw Hán văn gốc
- Tự tạo CE year không có authority

---

## Nguyên tắc evidence-first (bất biến)

```
"495年"          → precision=year      → CÓ THỂ chuẩn hóa (nếu source rõ)
"北魏太和19年"   → precision=reign_era → CHỈ map nếu có DILA Time Authority local
"32年後"         → precision=relative  → KHÔNG tự tính năm tuyệt đối
"唐朝時期"       → precision=dynasty   → KHÔNG tự chuyển thành event
```

---

## Dependencies

| Task | Mô tả | Trạng thái |
|------|-------|------------|
| T14 | Time Authority Import | pending |
| T23 | Entity Claims Provenance | ? |
| T69 | Wire Evidence Entity Claims | ? |
| T96 | Per-Segment Translation | in_progress |

---

## Prompt Plan Agent (đã sửa — sẵn sàng paste)

Xem nội dung đầy đủ trong file `tasks/T97-timeline-event-evidence-layer.md`.

**Thay đổi so với prompt gốc:**
1. Output dir: `docs/sessions/2026-09-05_T97_verified-findings.md`
2. Bỏ URL localhost, thêm "DILA Place ID PL000000000002"
3. `event_evidence` thêm field `time_mention_id (nullable)`
4. Mục A thêm: "Bắt đầu bằng đọc CLAUDE.md, docs/progress.md, docs/tasktodo.md"

---

## Gate: Sau khi Plan Agent xong

Gửi lại phần sau để Admin review trước khi Build:
1. **Verified findings** — bảng/API/file thực tế đã kiểm tra
2. **POC design** — inputs/outputs cho Thiếu Lâm Tự
3. **Proposed minimal architecture** — bảng nào reuse, bảng nào mới

**Chỉ sau khi Admin gõ "APPROVED" mới được chuyển sang Build phase.**
