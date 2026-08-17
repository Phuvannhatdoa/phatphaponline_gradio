---
id: T14
title: Import DILA Time Authority (time_periods = 0)
module: DILA Authority
priority: high
status: done
depends_on: []
created: 2026-08-13
updated: 2026-08-17
done_when: time_periods có dữ liệu (lunar_month/era/emperor/dynasty) + API tra cứu niên hiệu ✅ ĐÃ THÍCH HỎA
---

# T14 — Import DILA Time Authority (time_periods = 0)

## Mục tiêu
DEV_HISTORY audit 2026-08-11: `time_periods` = 0 rows. Cần import DILA Time Authority (lunar_month / era / emperor / dynasty) — core missing module, JDN-based (Khoá 2 / DEV_HISTORY).

## Cách tiếp cận
- Xác định nguồn DILA Time Authority (DILA github Authority-Databases).
- ETL import vào bảng `time_periods` (JDN-based).
- API tra cứu niên hiệu / đổi lịch Trung-Hoa-Nhật.
- Tích hợp vào chronology / timeline nếu có.

## Acceptance criteria (checklist)
- [x] ETL import time_periods thành công
- [x] Bảng time_periods có rows (era/emperor/dynasty)
- [x] API tra cứu niên hiệu hoạt động
- [x] Đối chiếu JDN chính xác
