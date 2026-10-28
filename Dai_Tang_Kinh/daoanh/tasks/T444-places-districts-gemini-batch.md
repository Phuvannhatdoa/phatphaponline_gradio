---
id: T444
former_ids: [T434, T431]
title: "T428 Part 2: Gemini batch transliterate places + districts (ai_place_name + ai_district_name)"
status: pending
created: 2026-10-20
updated: 2026-10-20
owner: null
module: Data / Places / Gemini
priority: high
depends_on: [T443, T418]
dispatch: null
plan_approved_at: "2026-10-20 (Admin phê chuẩn: Gemini script riêng, tuần tự sau T418 Part 2)"
done_when: >
  Yêu cầu: T430 import xong, T418 Part 2 hoàn tất (48.673/48.673 person).
  (1a) CREATE TABLE ai_place_name (dila_id, name_vi_ai, model, created_at, ...)
       CREATE TABLE ai_district_name (district, name_vi_ai, model, created_at, ...) — khóa theo district chuỗi
  (1b) Backup lineage.db → data/backups/T431-<ts>/, ghi docs/ROLLBACK.md.
  (2a) Viết script ai_batch_transliterate_place.py (riêng biệt, không sửa ai_batch_transliterate.py cũ):
       - Ưu tiên: review_needed_places.tsv + review_needed_districts.tsv (3.352 dòng)
       - Sau đó: places + districts còn lại
       - Gọi Gemini API (gemini-3.1-flash-lite), batch 50 tên/request
       - Retry MAX_RETRIES=5, sleep 70s nếu 429
       - Log riêng: logs/ai_transliterate_place.log
  (2b) Chạy --limit 500 test trước, nếu OK → resume phần còn lại (--limit không set).
  (2c) Trần 3 ngày (chia --limit theo ngày nếu gặp 429).
  (3) COUNT ai_place_name / ai_district_name sau xong (59.353 / 4.322 hoặc con số thực tế).
  (4) Kiểm: không overwrite codex_place_name (dữ liệu Claude), không UPDATE places/places_dila.
  (5) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
outcome: null
---

# T444 — Part 2: Gemini batch places + districts

> ID cũ: T434 (đổi 2026-10-21; former_ids: T434, T431). "T431" trong nội dung này = T444. "T430" = T443 (import).

Yêu cầu: T430 xong, T418 Part 2 hoàn tất.

Tạo script riêng, test 500, resume batch, trần 3 ngày, QA.

---
