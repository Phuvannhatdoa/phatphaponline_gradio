# Luận QA Offline — Báo cáo Nghiên Cứu (tạm ngừng)

**Ngày lập:** 2026-10-15
**Trạng thái:** TẠM NGỪNG — xem lại khi có thời gian
**Tác giả:** Plan Agent (Đạo Ảnh)

---

## 1. Mục tiêu & ràng buộc

- Mục tiêu: Q&A retrieval trên bộ **Luận Thư Phật Giáo** (Đại Thừa Khởi Tín Luận, Đại Trí Đổ Luận, Trung Luận, Bách Luận, ...), trả về đoạn + trích dẫn chính xác, chốt được tỉ lệ thành công.
- **100% offline** trên VPS 12 GB RAM, 100 GB HDD, không LLM API, không embedding API.
- Admin no-coding pipeline; Dev là Claude Code.
- SQLite FTS5 native, không Docker mới, không ES runtime.

---

## 2. Kết quả khảo sát từ repo Đạo Ảnh

DB `data/cbeta/cbeta.db` đã có 57 MB · 197 bản · 45.113 đoạn · FTS5 version 4 và **đã bật `remove_diacritics` native**. Còn có:
- 18 bộ từ điển (`data/indexed/combined_dict.json`, 58.836 muc)
- Trong đó Hán–Việt (`Tu Dien Han Viet - Nguyen Quoc Hung`, 21.635 muc) — **trích được ~21.562 пар Hán↔Hán-Việt** ngay.
- `scripts/hanviet_normalization.py` (378 dòng, "Fully local")
- `scripts/cbeta_translate_worker.py` (pipeline RAW→AUTO→MANUAL)
- `tests/test_t237_cbeta_corpus_search.py` (mẫu test)
- `data/cbeta/xml-p5-full/` (cây XML CBETA, không cần tải)

**Vai trò đảo ngược:** không xây mới, mà **mở rộng `cbeta.db` sang khối Luận**.

---

## 3. Vấn đề nghiêm trọng phát hiện

1. **10 Luận chưa có trong DB.** Đang có 197 bản, chỉ ở quyển T1–T4, T14, T50, T51. Các Luận nằm ở T26, T32, T45, T60 → **0 bản**.
2. **Dịch nghĩa offline là không khả thi:** Đại Trí Đổ Luận 100 quyển (~2M chữ) — local LLM 3B sẽ mất 50–200 ngày.
3. ** направлен've solution:** abandoning translation (2c) → giữ Hán + Hán-Việt + thuật ngữ (2b), tức **index song song 3 lớp**, chạy offline ngay, không cần AI.

---

## 4. Kế hoạch thực thi (thu gọn còn 3 tuần)

| Giai đoạn | Nội dung | Thời gian |
|---|---|---|
| 0 — Tiền kiểm | Xác minh ID Taishō, đếm ký tự, kiểm cách FTS5 xử lý Hán | 30 phút, chỉ đọc |
| 1 — Trích bảng đồng thuật | `t394_extract_luan_terms.py` → `cbeta_luan_terms.sqlite` từ 18 từ điển + thuật ngữ bổ sung | 1 ngày |
| 2 — Import 8 Luận | `t181_cbeta_download.py` + `import_cbeta.py`, backup DB trước, sinh `content_hv`, không chạm `lineage.db` | 2–3 ngày |
| 3 — Gold set | `t394_gold_set.csv`, 190 câu, phân bổ theo Luận | 2 ngày, song song |
| 4 — Đánh giá | `t394_eval_gold.py`: hit@1 / recall@5/10 / MRR; 3 cấu hình B0/B1/B2 | 1 ngày |

**Lưu ý:** Loại **Đại Trí Đổ Luận T1509** khỏi giai đoạn 1 (khối lượng gấp 20 lần), kaldı sau.

---

## 5. Ngân sách & rủi ro

- DB tăng ~+80 đoạn và ~+400 MB.
- RAM ~+150–400 MB.
- Thời gian ~5–7 ngày làm việc.
- Không dùng Docker / Elasticsearch / LLM / VPS mới.
- Rủi ro: FTS5 không tách Hán → thêm bảng `luan_fts_zh` trigram (additive); đồng thuật thiếu uncommon terms → gold set sẽ lộ ra; đo dưới 90% → báo cáo thẳng, không bịa.

---

## 6. Ba điều cần xác nhận (khi xem lại report này)

1. **Cho phép chạy Giai đoạn 0 không?** (chỉ đọc: đếm ký tự, xác minh ID, kiểm cách FTS5 xử lý Hán; không sửa file; báo số liệu thật trước khi sang GĐ1)
2. **Vị trí backup `cbeta.db` trước GĐ2?** Đề xuất: `data/cbeta/backup/cbeta.pre-T394_<ts>.db` (57 MB, copy là xong).
3. **Gold set — ai ký nhận phần đáp án?** Đề xuất giảng viên/đồng nghiệp Phật học; nếu không có ai, bộ 190 câu chỉ dùng cho tìm kiếm tương tác, không chứng minh được tỉ lệ.

---

## 7. Trạng thái tạm ngừng

Phần trước đây trong kế hoạch FoJin (`docs/FOJIN-TEST-RUNBOOK.md`, T393) unrelated — tang Buddha Đạo Ảnh offense không bị ảnh hưởng.

Khi xem lại: đánh dấu các todo sau bloated:
- [ ] Chạy Giai đoạn 0 (read-only)
- [ ] Xác nhận 3 điều §6
- [ ] Nếu pass → GĐ1 trích bảng đồng thuật
- [ ] GĐ2 import 8 Luận
- [ ] GĐ3 gold set
- [ ] GĐ4 đánh giá thật → báo cáo số đo, không bịa 95%

---

**Ghi chú:** Khi pick up lại, theo thứ tự §4. Không bỏ GĐ0.