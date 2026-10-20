> **Lịch sử 04/10. Phiên 05/10 đã thay cách API trả phí bằng Codex đăng nhập ChatGPT theo Admin.** Trạng thái hiện tại: [T233 Codex session](../T233-codex-session-20261005/README.md). Không yêu cầu API key.

---
task: tasks/T233-codex-han-viet-names.md
---
# T233 — Codex Hán Việt, 2026-10-04

**Build/UI sẵn sàng; dữ liệu GPT chưa chạy.** Đã chuẩn bị **48.673 ID / 1.522 request** (32 ID/request), đúng model API `gpt-6.1-sol`. DB `codex_person_name` hiện **0 kết quả**; không thay Gemini thành tên Codex. Chưa cấu hình OpenAI API. Task còn in_progress cho đến khi có kết quả thật và kiểm chất lượng.

## Admin sử dụng

Mở [namevimap](http://localhost:8080/daoanh/admin/namevimap.html), tab TTL ETL. Cả bảng đối chiếu và FLAG có Codex ngay sau DILA name_vi; bảng Gemini được giữ. Khung Codex cho phép tìm/phân trang toàn corpus, chuẩn bị ID, gửi Batch, nhận kết quả vào DB và tải lại. Nút gửi/nhận bị khóa khi thiếu API; “—” là chưa chạy, không phải tên bị thiếu trong DILA. Tên gợi ý không tự chép vào ô đang duyệt.

API riêng dưới `/daoanh/api/admin/ttl_v2/codex_name/`: status, list, lookup (≤200 ID/request), job prepare/submit/collect; đều cần session Admin. Không nhận filesystem path từ client.

## Luồng dữ liệu và bảo toàn

Streaming people theo ID → nhóm32 → Responses structured JSON → Batch → kiểm đúng tập ID/chữ Hán/model/input hash → gợi ý draft/needs_review riêng. Hash dùng ID/Hán/dynasty, không lấy tên Việt hiện tại làm đáp án. Chữ đa âm hoặc chuỗi không Hán cần Admin xét. Sai ID, thiếu/đúp ID, đổi Hán, refusal, stale input: không nhập như kết quả hợp lệ. Nhận lại cùng response không nhân đôi revisions. Không ghi people.name_vi, name_vi_map, VNPA, TTL, số đời hay quan hệ.

Bốn bảng additive: codex_person_name, codex_name_revision, codex_name_job, codex_name_request. Run chuẩn bị `616ff1e05ab442819bc166fe6cfafb0d`; thư mục `data/codex_names/23300000000000000000000000000001`. Manifest/file SHA: `6eeedd2c772f9143d1548ca58788fda05ae99657bf0de4e2d1948ead6c6b0732`. Không có batch_id/input_file_id; chưa gọi API trả phí. Lần chuẩn bị đầu lỗi SQL/encoding được giữ trong history failed, không che lỗi.

Prompt `daoanh-han-viet-names/1.0.0` là quy tắc phiên âm của dự án, **không phải mô hình đã fine-tune Phật học**. [Model chính thức](https://developers.openai.com/api/docs/models/gpt-6.1-sol) và [Batch API](https://developers.openai.com/api/docs/guides/batch): Batch là bất đồng bộ, không thể dùng session chat hiện tại thay credential API. Không đưa API key vào chat/log.

## Kiểm chứng

- Unit18/18 PASS: identity, strict output, hash drift, transaction rollback, idempotency, resume, auth, pagination, non-Han, unsafe title.
- UI thực trên8080 PASS, zero pageerrors; Codex dùng fixture rõ ràng, không lưu tên fixture: vị trí hai cột, nút thiếu key, ID link, phân trang, >200 rows, DOM textContent chống injection. `ui-result.json`, `codex-ui-fixture.png`.
- Actual DB read-only + auth fixture: status200, list page2 đủ50/48.673, lookup chưa có tên, submit thiếu key409 trước khi bắt đầu. `db-verification.json`.
- Bootstrap routes200 và Codex anonymous401. MainPID20728; helper probe3s bị timeout dù200, đã xác minh ready riêng `late-readiness.json` và tăng timeout cho lần sau. Gateway/auth khởi động vì không có listener, không thay cấu hình.
- Pipeline đang hoàn tất; kết quả cuối xem `pipeline*.log`/exit, Handoff. Không dùng exit0 để nói mọi chỉ số chất lượng dữ liệu đều đạt.

## DB song song — cảnh báo quan trọng

Năm bảng nguồn hash từng dòng giữ nguyên so với pre-T232: people48.673, vn_person_authority1.507, vn_person_relations2.013, lineage_edge_assertions59.059, person_gen_computed19.961. **ai_person_name thay đổi125→5.125** so với pre-T233 trong lúc có luồng khác chạy; đây không phải kết quả Codex. Vì vậy không khẳng định toàn DB bất biến. Không restore snapshot toàn DB để hoàn tác task này: sẽ mất dữ liệu phiên khác.

## Tiếp tục

1. Admin chọn nguồn OpenAI API/credential hợp lệ; kiểm model available của tài khoản, không dùng key trong tin nhắn.
2. Chạy một nhóm mẫu bằng cùng prompt/model, Admin kiểm chuẩn âm và trường hợp đa âm. Nếu cần sửa prompt, chuẩn bị lại lô với version mới, không sửa manifest/hash lô cũ.
3. Gửi lô đủ48.673 khi đã kiểm mẫu; nhận kết quả, đối chiếu requested/ingested/errors/needs_review, retry riêng phần thiếu. Chỉ đánh dấu toàn corpus hoàn tất khi có số đo thực.
4. Admin chuẩn hóa tên từ cột tham khảo qua quy trình duyệt hiện có.

## Hoàn tác

Backup consistent: `data/backups/T233-codex-namevi-20261004/lineage-before.db`; file backups + rollback manifest. `python -B -X utf8 scripts/rollback-name-generation.py` mặc định dry-run; `--apply` chỉ sau khi guard PASS và đã dừng main/job liên quan. Giữ báo cáo/backups/JSONL, chỉ drop6 bảng mới; nếu có tên Codex hoặc revision/mốc mới thì guard chặn để tránh mất dữ liệu. Xem Handoff10 mục và docs/ROLLBACK.md.
