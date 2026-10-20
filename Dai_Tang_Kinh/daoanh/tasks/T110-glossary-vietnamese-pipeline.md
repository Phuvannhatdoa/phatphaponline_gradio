---
id: T110
title: "Glossary Vietnamese Pipeline — Việt hóa glossary_term (248,095)"
module: Localization / Glossary
priority: medium
status: done
depends_on: [T108]
created: 2026-09-08
updated: 2026-09-08
done_when: >
  glossary_term (248,095 rows) có đường Việt hóa khả dụng: tái dùng name_vi_map
  (51,141) + name_normalization (17) làm nguồn Vietnamese; xử lý heap-free (Zero-RAM,
  generator); output ghi additive (cột vi hoặc mapping riêng, KHÔNG drop bảng gốc);
  Tăng Ni tra cứu được nghĩa tiếng Việt; compliance metric 'glossary_vi_coverage'.

---

# T110 — Glossary Vietnamese Pipeline

## Mục tiêu (gap được trích từ đặc tả "25 nguồn → 13/5/8")
`glossary_term` 248,095 rows KHÔNG có cột tiếng Việt (cols: id/term/language/definition/
full_text/source_id/created_at). Nguồn Marcus glossary — bổ sung nghĩa tiếng Việt để
phục vụ Tăng Ni (người dùng chính, ngôn ngữ mẹ đẻ là tiếng Việt).

## Hướng tiếp cận (đề xuất chờ thảo luận full trước khi code)
- Tái dùng `name_vi_map`/`name_normalization` hiện có làm ánh xạ Hán→Việt.
- Pipeline generator (không nạp 248k vào RAM), match theo từ/ida, bỏ qua không match (trung thực).
- Ghi additive (cột mới hoặc bảng mapping) + `--dry-run/--apply/--revert` + backup.
- KHÔNG gọi LLM hàng loạt (chi phí + rủi ro bịa); ưu tiên từ điển sẵn có.

## Acceptance
- `glossary_vi_coverage` đo được; báo cáo số rows có Việt / không.
- Không đụng bảng gốc; revert 1 lệnh; `npm run pipeline` PASS.