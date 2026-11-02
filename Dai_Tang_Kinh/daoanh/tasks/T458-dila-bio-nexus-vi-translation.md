---
id: T458
title: "Dịch tiếng Việt toàn bộ nexus tiểu sử DILA (dila_bio_nexus) bằng Codex — theo quy tắc dịch AI của dự án"
status: in_progress
created: 2026-11-02
updated: 2026-11-02
owner: coordinator
module: Data / Biographies
priority: high
parent: T457
depends_on: [T457]
done_when: >
  (1) Đọc và áp dụng quy tắc dịch AI của dự án (bảng translation_rules, rules đang active + glossary) TRƯỚC khi dịch;
      ghi rules_version đã dùng vào mỗi bản dịch.
  (2) Dịch đủ 21.740 nexus của T457 (11 sách) theo từng đoạn (batch), tài nguyên chạy bằng Codex (tài khoản ChatGPT $20).
  (3) Mỗi batch qua validator (RULE-013) và cổng REVIEW (RULE-011/012); không có bản dịch nào tự thành canonical (RULE-014).
  (4) Có provenance đầy đủ theo RULE-015: model_name, provider, prompt_version, ruleset_id, created_by_job_id, source_hash.
  (5) Hết quota thì dừng đúng chỗ, lưu tiến độ; hôm sau chạy tiếp từ batch kế tiếp, không dịch lại batch đã xong.
  (6) Không ghi đè text Hán gốc của dila_bio_nexus. Bản dịch nằm ở lớp riêng (xem mục Thiết kế).
  (7) Admin duyệt từng đợt (sample) trước khi hiển thị; QA độc lập (daoanh-qa) trước khi báo DONE.
revert: >
  Giai đoạn staging (file JSONL): xóa thư mục output. Nếu đã nạp DB (chỉ sau khi Admin duyệt schema):
  DROP bảng lớp dịch mới (additive, không đụng dila_bio_nexus).
---

## Mô tả

T457 đã import 21.740 nexus tiểu sử DILA (`dila_bio_nexus`, chỉ có chữ Hán). T457 xác nhận DONE chỉ cho phần import;
phần dịch tiếng Việt được giao cho task này.

Yêu cầu của Admin (2026-11-02):
- Dịch toàn bộ nexus của T457, dùng tài khoản Codex $20 (không dùng API trả phí).
- Chọn model rẻ, dịch từng đoạn, giống cách đang dùng Gemini Free: hết quota thì dừng, hôm sau dịch tiếp.
- Chất lượng là ưu tiên: phải tuân thủ quy tắc dịch AI của dự án.

## Quy tắc dịch AI (nguồn bắt buộc)

- **Bảng DB `translation_rules`**: 139 quy tắc `is_active=1` tại thời điểm tạo task. Đây là nguồn chính, được ghép thành prompt
  bởi `build_style_prompt` (style_constitution.py). Ghi lại `rules_version` khi chạy.
- **Glossary**: `translation_glossary`, `glossary_term`, `term_glossaries` (thuật ngữ Hán-Việt cố định).
- **Exemplar**: `translation_exemplar` (ví dụ dịch mẫu đã duyệt).
- Quy tắc cổng bắt buộc: RULE-011 (thuật ngữ không có trong glossary → `[REVIEW: <Hán>]`), RULE-012 (tên không resolve
  được → `[REVIEW: <Hán>]`), RULE-013 (validator: tỉ lệ ký tự, echo Hán, thiếu đoạn), RULE-014 (AI không tự thành GOLD),
  RULE-015 (provenance).
- Ghi chú: tài liệu `docs/sessions/2026-09-12_t123-style-constitution.md` ghi 18 quy tắc; DB hiện có 139. Nguồn đúng là DB, không phải tài liệu.

## Phạm vi dữ liệu

- Bảng nguồn: `dila_bio_nexus` (21.740 dòng, cột `text_zh`), `dila_bio_nexus_person`, `dila_bio_nexus_place`.
- 11 sách (số nexus theo T457): Tang_GSZ 5.446 · Song_GSZ 5.242 · Buxu_GSZ 3.971 · Xinxu_GSZ 2.955 · Liang_GSZ 1.819 ·
  biQiuNi 373 · chuSanZangJiJi 473 · Ming_GSZ 587 · Jushi_Zhuan 523 · Mingsengzhuanchao 188 · OtherSources 163.
- Đã có file dịch thử ở `data/dila_import/biographies.2024-01/vn_bio_nexus/` (biQiuNi 373, Mingsengzhuanchao 188,
  Buxu_GSZ 2.037). Báo cáo ghi các bản này là `unreviewed`, có đoạn bị cắt `[...]`. Dùng làm tham khảo, KHÔNG coi là đã đạt.
  Lưu ý: Buxu_GSZ có 2.037 trong khi T457 ghi 3.971, cần đối chiếu.

## Thiết kế đề xuất (chờ Admin duyệt)

1. **Giai đoạn 1 — staging, không ghi DB:** dịch theo batch (mỗi batch ~50–100 nexus, theo sách), lưu JSONL trong
   `data/dila_import/biographies.2024-01/vn_translate/<sách>/batch_NNNN.jsonl`. Mỗi dòng: `nexus_id`, `source_hash`,
   `text_vi`, `status`, `reason` (nếu có REVIEW), provenance.
2. **Tiến độ:** file `progress.json` ghi batch đã xong; chạy lại tự bỏ qua batch đã xong. Hết quota → dừng sạch, ghi lý do.
3. **Validator** chạy sau mỗi batch: đếm ký tự Hán còn sót, tỉ lệ độ dài so với nguồn, thiếu đoạn, REVIEW markers.
   Batch lỗi → đánh dấu, không ghi tiếp.
4. **Giai đoạn 2 — nạp DB (chỉ sau khi Admin duyệt schema):** bảng bổ sung `dila_bio_nexus_vi`
   (khóa `nexus_id`, `text_vi`, `translator`, `review_status='unreviewed'`, `source_hash`, `rules_version`, `model`, `created_at`).
   Không sửa `dila_bio_nexus`.

## Câu hỏi cần Admin quyết (trước khi chạy)

1. **Model rẻ nào** qua Codex CLI với tài khoản ChatGPT $20? Tôi chưa xác nhận được tên model có sẵn cho tài khoản này.
   Tham chiếu: `scripts/codex_namevi_session.py` đang đặt `SESSION_MODEL = 'gpt-6.1-sol'` cho việc khác — cần kiểm tra lại.
2. **Hạn mức Codex** (giới hạn theo giờ/tuần) quyết định tốc độ. Đo bằng batch thử trước khi chạy toàn bộ.
3. **Có nạp DB không?** Nếu có, cần duyệt schema bảng `dila_bio_nexus_vi` (thay đổi schema phải có duyệt riêng).
4. **Ai duyệt bản dịch?** Quy trình duyệt từng đợt (sample) do Admin làm, tránh bản dịch `unreviewed` hiện ra cho người dùng.

## Kế hoạch thực hiện (sau khi Admin duyệt)

1. Pilot: dịch 1 batch 50 nexus của `Mingsengzhuanchao`. Đo quota, thời gian, validator. Admin chấm chất lượng.
2. Nếu đạt: chạy theo sách, mỗi phiên dừng khi hết quota, ghi tiến độ.
3. QA độc lập (`daoanh-qa`, chỉ đọc): đối chiếu số lượng, validator, tỉ lệ REVIEW, provenance.
4. Admin duyệt từng đợt. Chỉ khi đủ mới báo DONE.

## KHÔNG làm

- Không ghi đè `dila_bio_nexus` hoặc `nexus_events`.
- Không dùng API trả phí nếu chưa có duyệt riêng.
- Không coi bản dịch AI là canonical (RULE-014).
- Không git commit/merge vào cây chính khi chưa có lệnh (tích hợp qua worktree `wt/t458-bio-vi` + khóa).

## Quyết định Admin (2026-11-02)

- **Phê chuẩn kế hoạch** trong task này và tạo T458 làm task dịch riêng (không gộp vào tab kinh CBETA).
- **Model:** gpt-6-luna (Admin chọn vì rẻ nhất). Trạng thái: chưa xác nhận có sẵn qua Codex CLI với tài khoản $20; CLI chưa cài.
- **Hạn mức:** dịch từng batch, dừng khi hết quota, chạy tiếp hôm sau từ batch kế tiếp.
- **Quy tắc:** bắt buộc áp dụng 139 quy tắc active trong `translation_rules` trước khi dịch.
- **Chưa được duyệt:** nạp DB (schema `dila_bio_nexus_vi`) và chạy pilot. Hai mục này vẫn chờ.

## Nhật ký

- 2026-11-02: Tạo task. Đã đọc quy tắc dịch từ DB (139 active). Chưa dịch gì.
- 2026-11-02: Admin phê chuẩn kế hoạch. Chuyển sang `in_progress` ở giai đoạn chuẩn bị (chưa chạy pilot, chưa ghi DB). Bàn giao: `docs/Handoff-2026-11-02-t458.md`.
