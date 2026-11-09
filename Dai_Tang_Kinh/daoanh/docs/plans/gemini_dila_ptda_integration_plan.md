# Kế hoạch tích hợp Gemini: DILA Biographies (TEI/XML) → PTDA

- **Trạng thái:** DRAFT — chờ Admin duyệt. Không có code, không gọi Gemini, không sửa XML, không import.
- **Trạng thái:** ĐÃ DUYỆT 2026-10-26 — triển khai trong **T457** (gộp T74b, T266). T472 là bước dịch Gemini của T457.
- **Task:** T457 (`tasks/T457-dila-biographies-nexus-import.md`), T472 (`tasks/T472-gemini-dila-biographies-integration.md`). T471 đã thuộc task khác.
- **Liên quan:** T453 (cha), T457 (trích nexus, đã có script), T458 (dịch đoạn nexus bằng Cloud, đã có 48 phần).

---

## 0. Điều chỉnh so với bản nháp đầu

Bản nháp cũ đề xuất làm lại việc đã có. Phạm vi mới chỉ gồm phần **chưa có**:

| Việc | Trạng thái hiện tại | Quyết định |
|---|---|---|
| Parse `linkGrp` → sự kiện (người, nơi, năm JD) | Đã có `scripts/t457_extract_bio_nexus.py` (21.740 nexus) | **Dùng lại**, không viết parser mới |
| Dịch đoạn sự kiện nexus | T458, Cloud, đang chạy theo 48 phần | **Không làm lại** bằng Gemini |
| Dịch tiêu đề, tác giả (byline), tóm tắt cho 2.976 truyện | Chưa có | **Phạm vi Gemini** |
| Quan hệ ngoài `linkGrp` (ví dụ người–người) có bằng chứng | Chưa có | **Phạm vi Gemini**, chỉ là ứng viên |
| Đối chiếu authority | Có `people`, `places_dila` | Chỉ ghép khớp, không sinh ID |

---

## 1. Nguyên tắc bất biến

1. **XML DILA gốc chỉ đọc.** Ghi SHA256 trước và sau mỗi lần chạy; khác nhau là dừng.
2. **Gemini không sinh authority ID.** ID chỉ lấy từ thuộc tính `key` có sẵn trong TEI (dạng `A000146`, `PL000000055417`) và phải tồn tại trong bảng authority.
3. **Mọi quan hệ có bằng chứng.** `evidence_span` phải là chuỗi con đúng từng ký tự của văn bản chữ Hán gốc; không khớp → loại.
4. **Mặc định `needs_review`.** Không có bản ghi nào của Gemini được ở trạng thái `approved` khi mới tạo.
5. **Admin duyệt trước khi vào PTDA.** Không import tự động.
6. **Khóa API không nằm trong code.** Đọc từ biến môi trường; hiện `app.py` còn khóa cứng (theo ghi chú memory) — cần xử lý trước khi chạy.

---

## 2. Quy cách dữ liệu DILA thật (đã kiểm 2026-10-26)

- Repo: `biographies-master/biographies-master/<Bộ>/<file>.xml`, commit `4e82453`.
- Người: `<persName key="A000146">`. Nơi: `<placeName key="PL000000055417">`.
- Thời gian: `<date from-iso="+0977-01-19" to-iso="+0984-12-10">`. Có giá trị `key="unknown"` (373 lần) — phải xử lý, không coi là lỗi chung.
- Giấy phép: văn bản CBETA **CC BY-NC-SA 4.0**; markup DILA **CC BY-SA** theo trang chính thức. Admin đã xác nhận PTDA phi thương mại (2026-10-22). Ghi công CBETA và DILA trên mọi bản xuất.

---

## 3. Pipeline

```
Snapshot (SHA256) → Trích (dùng lại T457) → Gemini (từng truyện)
   → Validator → needs_review → Admin duyệt → Bảng staging (additive) → PTDA (quyết định riêng)
```

| Bước | Đầu vào | Đầu ra | Kiểm soát |
|---|---|---|---|
| 1. Snapshot | repo DILA | bản snapshot + hash | hash trước/sau |
| 2. Trích | XML | đoạn chữ Hán theo truyện, danh sách key | dùng script T457 |
| 3. Gemini | **một truyện mỗi request** | tiêu đề VI, byline VI, tóm tắt VI, quan hệ ứng viên | giới hạn token, thử lại tối đa 2 lần |
| 4. Validator | đầu ra Gemini | lỗi / cảnh báo | xem mục 5 |
| 5. Review | bản ghi `needs_review` | duyệt / sửa / loại | Admin |
| 6. Staging | bản ghi đã duyệt | bảng additive | backup + rollback |

**Lưu ý kích thước lô:** "lô 20–50" chỉ là cách nhóm công việc. Mỗi request vẫn chỉ gửi **một truyện**, không gửi cả quyển.

---

## 4. Schema đầu ra (JSONL, 4 lớp)

**Lớp dịch** (`translation_layer.jsonl`)
`dila_id, source_xml_id, book, title_zh, title_vi, byline_zh, byline_vi, summary_vi, review_status, model, source_hash, license`

**Lớp quan hệ** (`relation_layer.jsonl`)
`dila_id, subject_key, predicate, object_key, time_jd, year_from, year_to, evidence_span, confidence, authority_match_status, review_status`
- `predicate` chỉ thuộc danh sách cho phép: `person_was_at_place`, `person_belonged_to_dynasty`, `person_contributed_to_text`, `person_interacted_with_person`.
- `text_place`, `person_temple`, `text_temple` bị cấm nếu không có bằng chứng.

**Lớp RAG** (`rag_layer.jsonl`): `dila_id, lang, chunk_type, text_vi, source_span, license, embedding_ready`

**Lớp lỗi** (`error_layer.jsonl`): `dila_id, error_type, message, source_span, retry_count`

**Báo cáo** (`report.md`): số truyện đầu vào, số bản dịch, số ứng viên quan hệ, số đã duyệt, số `needs_review`, số lỗi, tỷ lệ khớp authority, danh sách mẫu, và xác nhận XML không đổi.

---

## 5. Checklist validator

- [ ] Hash XML trước = sau (SHA256).
- [ ] Mọi `xml:id` và `key` còn nguyên.
- [ ] Mọi `key` người/nơi tồn tại trong bảng authority.
- [ ] Mọi `evidence_span` là chuỗi con đúng từng ký tự của văn bản gốc.
- [ ] Mọi quan hệ thuộc danh sách cho phép.
- [ ] Mọi truyện có bản dịch hoặc có lỗi được ghi.
- [ ] Không có JSON hỏng.
- [ ] Bản ghi không chắc chắn (tên riêng, thuật ngữ Phật giáo, năm mơ hồ) → `needs_review`.

---

## 6. Pilot

- **Bộ:** BiQiuNi (16.001 chữ nexus; tránh trùng với pilot Mingsengzhuanchao của T458).
- **Mẫu:** 30 truyện.
- **Tiêu chí thành công:** diff XML = 0; độ phủ bản dịch ≥ 95%; tỷ lệ khớp authority được đo; tỷ lệ `needs_review` được đo; không có quan hệ thiếu bằng chứng.
- **Không import** vào PTDA trong pilot.

---

## 7. Rủi ro và kiểm soát

| Rủi ro | Kiểm soát |
|---|---|
| Gemini bịa quan hệ | Bắt buộc `evidence_span` khớp đúng ký tự; loại nếu không khớp |
| Gemini bịa ID | Chỉ dùng `key` có sẵn; không sinh ID |
| Trùng công việc với T458 | Gemini không dịch đoạn nexus; chỉ làm tiêu đề, byline, tóm tắt, quan hệ ngoài linkGrp |
| Chi phí | Batch nhỏ, cache theo `source_hash`, giới hạn thử lại |
| Khóa API lộ | Biến môi trường; xoay khóa nếu đã lộ |
| Giấy phép | Phi thương mại; ghi công; không đăng toàn văn |
| 142 anchor lỗi trong nguồn | Ghi vào error_layer, không tự sửa |

---

## 8. Câu hỏi cần Admin quyết định

1. **Duyệt phạm vi mới** (mục 0): Gemini chỉ làm tiêu đề, byline, tóm tắt và quan hệ ngoài linkGrp?
2. **Mô hình và ngân sách:** Gemini model nào, ngân sách tối đa cho pilot?
3. **Pilot:** BiQiuNi 30 truyện có đồng ý không?
4. **Quan hệ được vào PTDA:** danh sách nào trong mục 4?
5. **Có cần người duyệt chuyên môn Phật học** trước khi import không?
6. **Bảng staging PTDA:** schema nào, và duyệt trên dashboard hay file Markdown?
7. **Khóa Gemini:** đã xoay khóa đã lộ trong code chưa?

---

## 9. Tiêu chí DONE của kế hoạch

Admin đọc tài liệu này và trả lời mục 8. Khi đó mới tạo task T471 với `done_when` theo mục 5–6.
