# T429 — Kế hoạch dựng dataset phả hệ "Thiền Đăng Thế Phổ" 禪燈世譜 (CBETA X86n1601)

**Phê chuẩn:** Admin 2026-10-20 03:46. Phê chuẩn bản kế hoạch gốc (Admin gửi 2026-10-20 03:41) kèm 9 điểm sửa của bản thẩm định
`docs/reports/THIENDANG-THEPHO-PLAN-REVIEW-2026-10-20.md`.

**Phạm vi lượt đầu:** chỉ **Giai đoạn 0–2**. Xong thì báo cáo và **chờ Admin chỉ đạo** trước khi sang Giai đoạn 3.

## 1. Kết quả cuối (toàn dự án)

Admin mở một trang preview local để:
1. chọn nhánh;
2. xem tên Hán (và tên Việt ở lớp mapping riêng);
3. bấm cạnh để thấy đúng đoạn / sơ đồ nguồn;
4. xem DILA ID đề xuất;
5. đối chiếu với DILA, Marcus, TTL;
6. phân loại cạnh trùng / mới / khác chiều / chưa đủ bằng chứng;
7. ghi quyết định duyệt vào review store riêng;
8. xuất gói bàn giao có provenance.

Preview xong **không** có nghĩa dữ liệu đã được accepted hay được vào production.

## 2. Nguyên tắc bắt buộc

| Vấn đề | Quy tắc |
|---|---|
| XML nguồn | Bất biến; mọi xử lý tạo file dẫn xuất |
| Tên | Giữ nguyên tên Hán nguồn (cả chữ sai, ví dụ 南獄懷讓); tên Việt nằm ở lớp mapping |
| DILA ID | Không tự tạo; không gán chỉ vì tên giống |
| Quan hệ | Mặc định `dharma_successor` theo tiêu đề sơ đồ "法派世系圖". Thế độ / thọ giới / tham vấn chỉ ghi khi có câu tiểu sử làm chứng; dùng chung từ vựng với T414 |
| Chiều cạnh / cấu trúc | Chỉ suy cạnh từ thứ tự hoặc list lồng nhau khi theo **quy tắc R01–R07 đã chứng minh** VÀ **kiểm chéo bằng nhãn** (đời con = đời cha + 1, hoặc 第N祖 liên tục). Sai nhãn ⇒ không tạo cạnh, đưa vào `unresolved` |
| Số đời | Giữ nguyên văn; đếm theo **gốc của từng sơ đồ** (`cb:div`); không so nhãn giữa hai sơ đồ; không quy đổi sang đời PTDA |
| Mâu thuẫn | Giữ các khẳng định song song |
| Độc lập nguồn | 禪燈世譜 biên soạn từ 傳燈錄 / 五燈會元, cùng gốc với DILA và Marcus. **Không tính vào luật "≥ 2 nguồn khớp" (T410)** cho tới khi Admin duyệt `source-dependency-notes.md` |
| AI | Chỉ đề xuất và giải thích; không tự accepted; không gọi API trả phí |
| Production | Không ghi DB / TTL / legacy / HOME ở mọi giai đoạn khảo sát |
| Quyền | Header ghi *"Available for non-commercial use when distributed with this header intact"* ⇒ preview và gói bàn giao **kèm nguyên header**; Admin xác nhận PTDA có dùng thương mại hay không (tiêu chí QA bắt buộc) |
| Tên quan hệ | `dharma_successor` (không dùng `dharm_successor`) |

## 3. Vai trò (dùng agent sẵn có)

| Vai | Agent |
|---|---|
| Điều phối | Claude Code (RC / phiên chính) |
| Khảo sát nguồn, quyền | `tich-hop` |
| Parser, schema, preview | `daoanh-debugger` |
| Kiểm dữ liệu độc lập (chỉ đọc) | `daoanh-qa`, phải tự mở `item/@xml:id` trong XML để kiểm, không dùng kết luận của agent khác làm chứng cứ |

## 4. Thư mục

- Kế hoạch: `docs/plans/T429-thiendang-thepho-plan.md` (file này).
- Báo cáo: `docs/reports/thiendang-thepho/phase0` … `phase10/`.
- Bàn giao: `docs/Handoff-YYYY-MM-DD-thiendang-thepho.md`.
- Dữ liệu nghiên cứu (vùng cách ly): `research/thiendang-thepho/{sources,manifests,schemas,derived,mapping,review,comparison,preview,tests,logs,releases}/`.
- Script: `scripts/thiendang_thepho/`.
- Không đặt trong artifact Van Cutsem, không đặt trong thư mục app tự quét, không commit nguồn lớn.

## 5. Nguồn

| Mục | Giá trị (RC đo sơ bộ 2026-10-20, Giai đoạn 1 phải xác nhận lại) |
|---|---|
| File local | `data/cbeta/xml-p5-full/X/X86/X86n1601.xml` (803.957 byte, ngày file 2026-09-27) |
| Tiêu đề / tác giả | 禪燈世譜 · 明 道忞編修、吳侗集 |
| Số quyển | 9 |
| Cấu trúc | 17 sơ đồ (`cb:div`), list/item lồng nhau sâu tối đa 9, nhãn đời `<note place="inline">`, 18 chú thích chéo "別見", 107 `app/lem/rdg`, 87 gaiji, 10 nhãn mất chữ `□□世`, **không có `<table>`** |

## 6. Quy tắc đọc cấu trúc ban đầu (Giai đoạn 2 phải chứng minh hoặc bác bỏ)

| Mã | Kiểu | Ví dụ | Tạo cạnh? |
|---|---|---|---|
| R01 | Item ngang hàng có nhãn 第N祖 liên tục (三十三祖世系圖) | `itemX86p0321a0101` 第一祖 → `itemX86p0321a1001` 二祖 | Có, nếu dãy liên tục |
| R02 | Item nhãn đời k trong list con của item nhãn đời k−1 (法派世系圖) | 馬祖道一 二世 ⊂ 南獄懷讓 一世 (`itemX86p0335a0601`) | Có |
| R03 | Item ngang hàng **không nhãn** cùng list con | 龍興尊宿, 千頃楚南 cùng cấp 臨濟義玄 dưới 黃檗 | Có (cùng thầy), cần kiểm mẫu |
| R04 | Item chỉ có văn tiểu sử, không có tên đứng đầu | list con dưới 摩訶迦葉 | **Không** (không phải người) |
| R05 | "派裔別見 / 法嗣別見" | 南嶽懷讓 "輪派裔別見" | **Không tự nối**; ghi `cross_ref` chờ duyệt |
| R06 | Nhãn đời mất chữ `□□世` | 10 chỗ | Chỉ `proposed`, người duyệt |
| R07 | Lớp `note type=orig/add/cf*`, `app/lem/rdg` | 107 `app` | Claim tách riêng theo lớp |

Quy tắc tách tên:
- Tên là text đầu item, sau nhãn đời và trước `<p>` / `<list>`.
- Nối các đoạn bị `<lb/>` cắt.
- Gaiji giữ cả dạng gốc lẫn dạng chuẩn hoá (theo `charDecl`).
- Locator ổn định là `item/@xml:id`.

Quy tắc dừng: cấu trúc nào XML không đủ thông tin ⇒ ghi *"Không đủ thông tin để trích cạnh tự động từ XML cho cấu trúc này"* và đề xuất đọc ảnh trang. Không đoán.

## 7. Các giai đoạn

| GĐ | Nội dung | Bàn giao chính |
|---|---|---|
| 0 | Khảo sát code / schema / docs; tái sử dụng gì | `phase0/environment-audit.md`, `reuse-map.md`, `scope-and-boundaries.md` |
| 1 | Đóng băng nguồn: header, SHA-256, quyền, manifest | `source-manifest.json`, `source-header.xml`, `rights-assessment.md`, `SHA256SUMS.txt` |
| 2 | Giải mã cấu trúc sơ đồ, chốt R01–R07 bằng ví dụ thật (cả ví dụ không được trích) | `structure-inventory.json`, `structure-analysis.md`, `extraction-rules.md`, `sample-source-fragments/` |
| 3 | Thiết kế dữ liệu (7 đối tượng) **kèm bảng ánh xạ trường** sang bảng hiện có | `schemas/` + `field-mapping-to-ptda.md` |
| 4 | Mẫu chuẩn (30–50 đoạn, 100–200 quan hệ); tách tập kiểm độc lập | `gold-*.jsonl`, `pilot-sampling-plan.md` |
| 5 | Parser local (luồng, `--dry-run`, checkpoint, chạy lại cho cùng kết quả), pilot | `relation_candidates.jsonl`, `unresolved_fragments.jsonl`, `extraction-report.md` |
| 6 | Đề xuất mapping DILA (candidate / ambiguous, không tự verified; xử lý dị thể như 獄 / 嶽 bằng bảng quy tắc) | `identity_mappings.jsonl` |
| 7 | Đối chiếu DILA / Marcus / TTL trên snapshot chỉ đọc. **2 tầng:** (a) cặp (thầy, trò); (b) loại và chiều. "Chưa có trong Marcus" ≠ "Marcus phủ nhận" | `comparison/*.jsonl`, `source-dependency-notes.md` |
| 8 | Preview local (127.0.0.1); không cắt cạnh để ép thành cây; review store riêng | `preview/` |
| 9 | QA pilot: precision ≥ 98% trên mẫu độc lập (báo cả cỡ mẫu và lỗi), 100% claim có đường truy nguồn | `quality-report.md` |
| 10 | Chạy đủ 9 quyển ở mức candidate (chỉ sau khi Admin QA pilot) | `coverage-report.md` |

**Bảng ánh xạ trường (Giai đoạn 3):**
- `relation_claim` → `lineage_edge_assertions(source_code='CBETA_X1601', relation_kind, source_edge_ref)`.
- `identity_mapping` → `entity_source_ids(source='CBETA_X1601', match_status)`.

Có bảng này thì task tích hợp production về sau (tách riêng, sau T422–T426) chỉ là nạp dữ liệu.

## 8a. Quy ước đặt tên task (Admin 2026-10-20 04:00)

Mọi task thuộc dự án này (các giai đoạn sau, task tích hợp production…) phải có tiền tố **"[Thiền Đăng Thế Phổ]"** ở đầu `title`, để Admin lọc và theo dõi trên Dashboard. Ví dụ: `[Thiền Đăng Thế Phổ] 禪燈世譜 — Giai đoạn 3–5: …`.

## 8. Mẫu báo cáo mỗi giai đoạn

TASK / PHASE / DATE / STATUS, rồi lần lượt:
1. Mục tiêu.
2. Input (đường dẫn, hash, snapshot).
3. Việc đã làm.
4. File tạo / sửa.
5. Số đo (và những gì chưa đo được).
6. Kiểm thử: lệnh thực chạy, PASS / FAIL; test chưa chạy và lý do.
7. Kiểm không tác động production.
8. Lỗi và giới hạn còn lại.
9. Commit và rollback.
10. 3 ví dụ đúng và 3 ca khó, có locator.
11. Đề xuất bước tiếp.
12. Câu hỏi cho Admin.

Không ghi "ALL PASS" khi pipeline repo còn lỗi.
