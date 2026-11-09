---
id: T447
title: Cổng dịch AI thống nhất theo quy tắc hàn lâm (translation_rules) + cache theo phiên bản quy tắc
status: in_progress
created: 2026-10-21
updated: 2026-10-26
done_when: >
  Mọi lệnh dịch AI Hán→Việt đi qua một cổng duy nhất nạp đủ quy tắc active;
  bản dịch lưu DB kèm rules_version, người đọc sau không gọi AI lại;
  đổi quy tắc → bản cũ được đánh dấu, không tự dịch lại; admin có nút Dịch lại trong Cpanel;
  _suggest_name giữ nguyên định dạng JSON; kiểm trên trình duyệt thật 127.0.0.1; daoanh-qa; Admin xác nhận DONE.
---

# T447 — Cổng dịch AI thống nhất theo quy tắc hàn lâm

Kế hoạch chi tiết và lý do: `docs/T447-translation-gateway-plan.md`.

## Phạm vi

- `app.py`: hàm cổng `translate_han_vi`, hàm `rules_version`, ghi/đọc cache dịch,
  chuyển các chỗ gọi AI trực tiếp (Groq, Gemini, Claude) sang cổng.
- `admin/translation_cache.html` hoặc Cpanel: nút "Dịch lại".
- Không đổi dữ liệu gốc, không ghi DB ngoài bảng cache dịch.

## Các bước

Xem mục "Các bước" trong `docs/T447-translation-gateway-plan.md`.

## Vòng 2 — sửa lỗi theo QA report (2026-10-26)

daoanh-qa kiểm độc lập, báo CHƯA ĐẠT 3 lỗi trong `api_admin_translate_retranslate`
(app.py, nút "Dịch lại" Cpanel):

**Lỗi 2 — "Dịch lại" hỏng dữ liệu cho `dila_card`/`relation_evidence`.**
`translate_han_vi()` tính lại `source_hash` từ chính `source_text` lưu trong
`translation_cache` (`_t73_source_hash(source_text.strip())`), nhưng với
`source_type='dila_card'` hash gốc được tính từ `json.dumps(source_data,
sort_keys=True)` (không phải `source_text`), và `source_text` lưu lại là bản
JSON KHÁC (không `sort_keys`, bị cắt `[:5000]`) — hash tính lại không bao giờ
khớp hash gốc. Với `relation_evidence`, hash gốc đôi khi là
`text_hash = sha256(excerpt.rstrip('；;'))[:24]` (khác `_t73_source_hash(excerpt.strip())`)
khi excerpt kết thúc bằng `；`/`;` — đã xác minh thực tế trên DB
(`data/lineage.db`): id=1746..1751 (30 dòng `dila_card`) và id=1284 (1 trong 2
dòng `relation_evidence`) đều mismatch; id=1758 (`relation_evidence` còn lại)
match.

Sửa trong `app.py` (`api_admin_translate_retranslate`, route
`/daoanh/api/admin/translate/retranslate`):
- Thêm hằng `_T447_RETRANSLATE_UNSUPPORTED_SOURCE_TYPES = {'dila_card'}` —
  chặn 422 ngay, không gọi `translate_han_vi()`, vì format/prompt của
  `dila_card` (JSON `relations_vi`...) không tương thích với prompt generic
  của cổng dù hash có khớp hay không.
- Sau khi gọi `translate_han_vi(force=True)`, so `result['source_hash']` với
  `source_hash` đã lưu của đúng dòng `id` — lệch thì trả 422 `HASH_MISMATCH`
  (không để dòng cache rác nằm im lặng, không báo `ok:true` sai sự thật). Bắt
  đúng ca `relation_evidence` id=1284 nêu trên mà không cần hard-code riêng
  từng id.
- `admin/translation_cache.html`: nút "Dịch lại" đã gửi `{id}` (= `row.id`,
  tức cache_id) từ trước — không cần sửa thêm phần này.

**Lỗi 3 — retranslate bỏ qua T166 post-check cho `person_bio`.**
Luồng chính (`/daoanh/api/person/<id>/translate`) chạy
`_t166_post_check_translation` sau khi AI trả bản dịch; nhánh retranslate
không chạy. Đã sửa: sau `translate_han_vi(force=True)` với
`source_type='person_bio'`, gọi `_t166_post_check_translation` giống luồng
chính; nếu bị chặn (HARD) → trả 422 `REVIEW_REQUIRED` kèm `identity_issues`;
nếu cột `identity_status` đã migrate (`_t166_has_col`), ghi lại
`identity_status/identity_issues/identity_lock_hash` vào đúng dòng cache mới.
Đã xác minh DB hiện tại CHƯA có cột `identity_status` trong `translation_cache`
→ nhánh ghi UPDATE tự bỏ qua (guard `_t166_has_col`), không lỗi, không đổi
schema trong vòng sửa lỗi này.

**Lỗi 4 (không bắt buộc, đã sửa) — `_suggest_name` không đọc lại cache của
chính nó.** Thêm 1 lượt `_t165_lookup_cache` (cùng khóa dual-key
`source_hash + constitution_hash + rules_version`, `source_type='name_suggestion'`)
trước khi build prompt + gọi AI; cache hit trả thẳng, không gọi AI.

### Giới hạn còn lại (ghi nhận, không mở rộng phạm vi vòng này)

- Các endpoint dịch khác (`person/<id>/translate`, `dila_card`,
  `relation_evidence`, `place_note`, `web_summary`) vẫn gọi AI/`_t73_*` trực
  tiếp, CHƯA đi qua `translate_han_vi()` — đúng như QA đã ghi nhận, nằm ngoài
  done_when của vòng sửa lỗi 2 này; cần task riêng nếu Admin muốn gộp.
- `dila_card` vẫn KHÔNG đi qua nút "Dịch lại" chung của Cpanel — Admin cần
  dùng nút riêng của tab dila_translate (`?force=1`) cho source_type này; đây
  là quyết định có chủ đích (không tương thích format), không phải bug.
- Chưa chạy lại full luồng click thật trên browser 127.0.0.1 cho nhánh
  `person_bio` + T166 blocked case (do DB hiện không có dòng `person_bio` nào
  đang bị T166 chặn để test end-to-end qua UI) — đã verify logic bằng truy
  vấn DB trực tiếp (xem báo cáo build summary) thay cho click thật.
