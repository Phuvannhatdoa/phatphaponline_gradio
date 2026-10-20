---
id: T409
title: "Hồ sơ A032162: /api/persons, /api/evidence, /translate, /dila_translate trả 500 khi server bận"
status: pending
created: 2026-10-15
updated: 2026-10-15
owner: unassigned
parent: T404
module: API / Person profile
priority: medium
depends_on: []
done_when: >
  (1) Tái hiện 500 trên hồ sơ A032162 cho từng endpoint: `/api/persons`, `/api/evidence`,
  `/person/A032162/translate`, `/dila_translate` — ghi rõ điều kiện tái hiện ("khi server bận": tải cao,
  nhiều request đồng thời, hay timeout cụ thể nào).
  (2) Đọc log/traceback thật của app.py tại thời điểm 500 — xác định lỗi là timeout DB, race condition,
  exception chưa try/except, hay rate-limit từ Groq/Gemini (T73/T74 translate endpoints).
  (3) Fix đúng lớp: nếu lỗi do thiếu try/except/timeout handling → sửa route; nếu do DB lock dưới tải →
  xem xét connection pooling/retry; không che lỗi bằng cách trả 200 giả.
  (4) Không lộ API key Gemini (app.py lines 1065/1105) trong log/response khi sửa.
  (5) Test lại bằng cách tạo tải tương tự (nhiều request đồng thời) — không chỉ test 1 request đơn lẻ.
  (6) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
---

# T409 — API 500 trên hồ sơ A032162 khi server bận

## Nguồn phát hiện

Ghi nhận ngoài phạm vi khi làm T404: `tasks/T404-places-search-autocomplete-jank.md` mục "Phát hiện ngoài
phạm vi" #5.

## Phạm vi điều tra

Chưa biết root cause — audit trước khi sửa. Đọc log app.py/server.py thật tại thời điểm lỗi 500 cho 4
endpoint liên quan hồ sơ A032162. Phân biệt lỗi tầng nào: DB (lineage.db lock/timeout), resolver
(canonical_lock/vnpa_lookup), hay dịch thuật (T73/T74 Groq/Gemini call site tại app.py ~L20749, ~L1065/1105).

## Ràng buộc

Không commit/sửa `.env` hoặc lộ API key. Không đổi schema DB khi chưa Admin duyệt. Backup file sửa vào
`docs/sessions/<ngày>/T409/` trước khi edit.

## Các bước

- [ ] Tái hiện 500 trên cả 4 endpoint, thu log/traceback thật
- [ ] Phân loại nguyên nhân (timeout/race/exception/rate-limit)
- [ ] Backup file liên quan trước khi sửa
- [ ] Fix đúng lớp (route/resolver/DB handling) — không che lỗi
- [ ] Test lại với tải đồng thời, không chỉ 1 request
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
