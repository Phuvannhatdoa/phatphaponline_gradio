# T429 — Giai đoạn 0: Scope and Boundaries (phạm vi và ranh giới)

TASK: T429 · PHASE: 0 (scope-and-boundaries) · DATE: 2026-10-21 · STATUS: DONE (phạm vi GĐ0)

## Phạm vi LƯỢT 1 (task này — GĐ0–2)

| GĐ | Làm | Không làm |
|---|---|---|
| 0 | Khảo sát code/schema/docs, reuse map | Không sửa code, không sửa schema |
| 1 | Đóng băng nguồn: hash SHA-256, trích header verbatim, manifest, đánh giá quyền | Không tải lại nguồn từ internet (dùng bản local có sẵn); không ghi `data_sources` |
| 2 | Inventory cấu trúc, chứng minh/bác bỏ R01–R07 bằng locator `item/@xml:id` thật, lưu fragment mẫu | Không trích cạnh hàng loạt; không viết parser hoàn chỉnh (GĐ5); không suy DILA ID; không suy số đời |

## Ranh giới cứng (vi phạm = sai task)

1. **KHÔNG ghi** `data/lineage.db`, TTL, legacy, HOME — mọi output chỉ vào `research/thiendang-thepho/` và `docs/reports/thiendang-thepho/` (+ script trong `scripts/thiendang_thepho/` theo plan §4).
2. **KHÔNG gọi API trả phí** (Gemini/Claude/Groq…). GĐ0–2 không cần AI.
3. **KHÔNG tạo DILA ID mới**, không gán ID chỉ vì tên giống (kể cả dị thể 獄/嶽 — xử lý ở GĐ6).
4. **KHÔNG suy số đời** — nhãn đời giữ nguyên văn, đếm theo gốc của từng sơ đồ (`cb:div`), không so nhãn giữa hai sơ đồ, không quy đổi sang đời PTDA.
5. **KHÔNG trích cạnh hàng loạt** vào DB hay file production. Fragment mẫu chỉ để chứng minh quy tắc.
6. **KHÔNG sửa** `tasks/`, `docs/tasktodo.md`, code ứng dụng; **KHÔNG git add/commit/push**.
7. **DỪNG** ở cuối GĐ2 — chờ Admin chỉ đạo GĐ3.

## Ranh giới dữ liệu

- Nguồn XML **bất biến**: `data/cbeta/xml-p5-full/X/X86/X86n1601.xml` (SHA-256 `0020c484…75eb`, xem manifest). Mọi file dẫn xuất ghi rõ nguồn gốc + hash.
- Tên giữ nguyên văn nguồn (kể cả chữ sai 南獄懷讓 — 獄 thay cho 嶽); tên Việt chỉ ở lớp mapping riêng (GĐ6+).
- Quan hệ mặc định `dharma_successor` theo tiêu đề "法派世系圖"; thế độ/thọ giới/tham vấn chỉ ghi khi tiểu sử làm chứng (GĐ4+).
- Mâu thuẫn: giữ các khẳng định song song, không tự chọn.
- Độc lập nguồn: 禪燈世譜 biên soạn từ 傳燈錄/五燈會元 — cùng gốc với DILA/Marcus ⇒ **không tính vào luật "≥ 2 nguồn khớp" (T410)** cho tới khi Admin duyệt `source-dependency-notes.md`.
- Quyền: header CBETA ghi *"Available for non-commercial use when distributed with this header intact"* ⇒ mọi gói bàn giao/preview **kèm nguyên header**; câu hỏi PTDA có dùng thương mại không → dành cho Admin (xem rights-assessment.md).

## Định nghĩa xong việc GĐ0–2 (rút từ done_when của task)

- GĐ0: 3 file phase0 có thật, phân biệt được code thật vs docs-only, có đề xuất tái sử dụng. → PASS (xem 3 file phase0).
- GĐ1: manifest + header + SHA256SUMS + rights-assessment; xác nhận từ header thật: 禪燈世譜, X86n1601, 9 quyển; hash tái tính khớp. → PASS (xem phase1).
- GĐ2: structure-inventory.json + structure-analysis.md + extraction-rules.md + sample-source-fragments/; R01–R07 có verdict kèm locator thật đầu/giữa/cuối, gồm cả ví dụ KHÔNG được trích; kết luận XML đủ hay cần ảnh trang. → PASS (xem phase2).
- Không đổi production: baseline vs sau (xem báo cáo chính, mục 4).
