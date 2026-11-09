# T429 — BÁO CÁO GIAI ĐOẠN 0–2: Thiền Đăng Thế Phổ 禪燈世譜 (CBETA X86n1601)

TASK: T429 · PHASE: 0–2 · DATE: 2026-10-21 · STATUS: DONE (GĐ0–2) — DỪNG chờ Admin chỉ đạo GĐ3

## 1. Mục tiêu

Khảo sát hệ thống (GĐ0), đóng băng nguồn + đánh giá quyền (GĐ1), giải mã cấu trúc sơ đồ và
chốt quy tắc R01–R07 bằng bằng chứng locator thật (GĐ2) — chuẩn bị dựng dataset phả hệ có
provenance. Chưa đưa vào DB chính, TTL, legacy hay HOME.

## 2. Input

| Input | Giá trị |
|---|---|
| Nguồn XML | `data/cbeta/xml-p5-full/X/X86/X86n1601.xml` — 803.957 byte, mtime 2026-09-27T19:34:02+07:00, **SHA-256 `0020c4847b8107260e8674233d7833fd590cccafba2210d0ac479edd88ff75eb`** |
| Nguồn có sẵn local | Có — không tải internet, không gọi API nào |
| Plan / thẩm định | `docs/plans/T429-thiendang-thepho-plan.md` · `docs/reports/THIENDANG-THEPHO-PLAN-REVIEW-2026-10-20.md` |
| Task files tham khảo | T410, T414, T422–T426 (T422/T423 ở `tasks/archive_done/`) |
| Baseline | HEAD `16f6d4a9370639327f88d18eafa3a4324f2f4517`; lineage.db 1.619.517.440 byte, SHA-256 `15baeffdf200503573fd4afd254b9014b9eed0410ff8e769e50b4d3681dada06` (đo trước khi làm) |

## 3. Việc đã làm

- **GĐ0:** truy vấn DB read-only (167 bảng, đếm `lineage_edge_assertions`/`entity_source_ids`/`data_sources`/VIEW), grep `app.py` xác nhận code thật, đọc task files → 3 báo cáo phase0.
- **GĐ1:** script `freeze_source.py` — hash SHA-256, trích `<teiHeader>` verbatim, manifest JSON, SHA256SUMS; xác nhận từ header thật: 禪燈世譜 / X86n1601 / 9 quyển / quyền non-commercial + header intact.
- **GĐ2:** script `analyze_structure.py` — inventory toàn cục + 17 sơ đồ, kiểm chéo nhãn toàn tác phẩm, chứng minh R01–R07 bằng `item/@xml:id` thật (đầu/giữa/cuối), lưu 10 fragment XML mẫu.

## 4. File tạo / sửa (toàn bộ mới, không sửa file có sẵn)

| File | Nội dung |
|---|---|
| `research/thiendang-thepho/README.md` | Bản đồ vùng nghiên cứu |
| `research/thiendang-thepho/manifests/source-manifest.json` | Manifest đóng băng nguồn |
| `research/thiendang-thepho/manifests/source-header.xml` | Header verbatim (hash `a8e08889d080b3bf…`) |
| `research/thiendang-thepho/manifests/SHA256SUMS.txt` | 3 hash, verify PASS |
| `research/thiendang-thepho/derived/structure-inventory.json` | Inventory GĐ2 |
| `research/thiendang-thepho/sources/sample-source-fragments/*.xml` | 10 fragment chứng cứ R01–R07 |
| `research/thiendang-thepho/logs/{baseline-git-status.txt,after-git-status.txt,baseline-db-metadata.json,analyze-structure-run.json}` | Baseline + log chạy |
| `docs/reports/thiendang-thepho/phase0/{environment-audit,reuse-map,scope-and-boundaries}.md` | GĐ0 |
| `docs/reports/thiendang-thepho/phase1/rights-assessment.md` | GĐ1 |
| `docs/reports/thiendang-thepho/phase2/{structure-analysis,extraction-rules}.md` | GĐ2 |
| `scripts/thiendang_thepho/{freeze_source.py,analyze_structure.py}` | Script tái lập (chỉ đọc nguồn) |

## 5. Số đo (và những gì chưa đo được)

| Đo | Giá trị |
|---|---|
| Hash nguồn tái tính | PASS — 2 lần chạy `freeze_source.py` cùng hash `0020c484…75eb`; SHA256SUMS verify 3/3 PASS |
| Header xác nhận | 禪燈世譜 (title level="m") · idno X/86/1601 · `<extent>9卷</extent>` + 9 milestone · availability non-commercial + header intact — **PASS hết** |
| Sơ đồ | 17 (`cb:div type="other"`), depth lồng tối đa 9 (諸祖旁出法派系圖) |
| R01 | 33 tổ, nhãn 1→33 liên tục — PASS |
| Kiểm chéo nhãn | 121/121 cặp có nhãn khớp con = cha+1, **0 lệch**; 0 cha có ≥2 con cùng nhãn |
| R03 | 107 list lẫn có nhãn/không nhãn; 1.809 item không nhãn |
| R04 | 122 item chỉ-tiểu-sử (heuristic) |
| R05 | 18 "別見" (派裔別見 2 · 法嗣別見 8) |
| R06 | 10 nhãn `□□世` — hết ở 2 sơ đồ cuối; 7/10 mất cả tên |
| R07 | app/lem/rdg 107; note add 107 / orig 10 / cf1 1 / cf2 1 |
| Gaiji | charDecl 34, `<g>` dùng 87 (34 ref) |
| Chưa đo được | Độ chính xác tách tên trên toàn 5.876 item (GĐ4 gold set); đối chiếu DILA/Marcus (GĐ7) |

## 6. Kiểm thử

| Lệnh thực chạy | Kết quả |
|---|---|
| `python -X utf8 scripts/thiendang_thepho/freeze_source.py` (×3) | PASS — idempotent (manifest trừ `frozen_at_utc` giống hệt giữa 2 lần) |
| `python -X utf8 scripts/thiendang_thepho/analyze_structure.py` (×2) | PASS — kết quả nhất quán |
| Verify SHA256SUMS (script tạm, chỉ đọc) | PASS 3/3 |
| Test chưa chạy | Parser hoàn chỉnh (GĐ5), gold set (GĐ4) — ngoài phạm vi lượt này |

## 7. Kiểm không tác động production (đo thật trước–sau)

| Mục | Baseline (trước) | Sau khi xong | Verdict |
|---|---|---|---|
| git HEAD | `16f6d4a9370639327f88d18eafa3a4324f2f4517` | `16f6d4a9370639327f88d18eafa3a4324f2f4517` (giống hệt) | **PASS — không commit gì** |
| lineage.db | 1.619.517.440 byte · SHA-256 `15baeffdf200503573fd4afd254b9014b9eed0410ff8e769e50b4d3681dada06` · mtime 2026-10-21T01:55:46.805063Z | **giống hệt cả 3 chỉ số** (đo lại bằng cùng script) | **PASS — DB không đổi** |
| git status | 218 dòng (lưu `research/thiendang-thepho/logs/baseline-git-status.txt`) | 222 dòng; diff = 4: `?? docs/reports/thiendang-thepho/` · `?? research/` · `?? scripts/thiendang_thepho/` (file mới của T429) + `M docs/tasktodo.md` | **PASS** — `tasktodo.md` bị sửa bởi **session song song** (T429 chỉ đọc file này, không ghi); 3 thư mục còn lại là untracked mới đúng phạm vi |

## 8. Lỗi và giới hạn còn lại

- Lỗi đã gặp và sửa: namespace `cb:div` ≠ `tei:div` (IndexError); hàm tách tên bỏ sót text sau note inline (thiếu tail); depth đo nhầm list>list thay vì list>item; `title type=main` là tên bộ, phải lấy `level="m"`.
- Giới hạn: R04 dùng heuristic (122 item) — cần gold set xác nhận; R03 chỉ kiểm được 1 mẫu sâu (黃檗) — cần kiểm mẫu rộng GĐ4–5; fragment là re-serialize lxml (trung thành nội dung, không phải byte verbatim — nguồn gốc vẫn là XML đã hash).
- DB đang bị process khác mở (server chạy) — hash DB đo được nhờ python open; nếu server ghi DB trong phiên thì hash sau có thể khác **không do T429** — so mtime để phân biệt.

## 9. Commit và rollback

- **Chưa commit** (không có lệnh từ Admin). Rollback: xoá `research/thiendang-thepho/`, `docs/reports/thiendang-thepho/`, `scripts/thiendang_thepho/` (chỉ chứa file của task này) — không mất dữ liệu production.

## 10. Ví dụ đúng (3) và ca khó (3) — có locator

**Ví dụ đúng:**
1. R01: `itemX86p0321a0101` 第一祖 摩訶迦葉 → `itemX86p0321a1001` 二祖 阿難尊者 (đầu tác phẩm).
2. R02: `itemX86p0335a0501` [一世] 南獄懷讓 ⊃ `itemX86p0335a0601` [二世] 馬祖道一.
3. R02 cuối: `itemX86p0462a0901` [五世] 洞山良价 ⊃ `itemX86p0462a1001` [六世] 曹山本寂.

**Ca khó:**
1. `itemX86p0336a0801` 丞相裴休 — item không nhãn đồng cấp với 臨濟義玄 dưới 黃檗希運; cấu trúc thuần sẽ sinh cạnh `dharma_successor` cho một quan lại tại gia ⇒ bắt buộc kiểm vai bằng tiểu sử.
2. `itemX86p0428a0301` 雪竇重顯 — note inline là văn xuôi "卍進本雪竇為四世，已下遞次準之。", không parse thành nhãn số được (đề xuất R08).
3. `itemX86p0472a1301` 壽昌慧經 — nhãn `□□世`; 7 item cùng sơ đồ mất cả tên ⇒ XML không đủ, cần ảnh trang p0472.

## 11. Đề xuất bước tiếp (GĐ3 — chờ Admin)

1. Thiết kế 7 đối tượng dataset **kèm bảng ánh xạ trường** sang `lineage_edge_assertions` + `entity_source_ids` (plan §7).
2. Bổ sung R08/R09 vào bộ quy tắc (nhãn văn xuôi; sơ đồ không nhãn).
3. Quyết định nguồn xử lý ảnh trang p0472 (2 sơ đồ mất nhãn) — cần nguồn ảnh CBETA hay đánh dấu unresolved vĩnh viễn.
4. Chốt bộ nhãn quan hệ với T414 (`noi_phap/khac/unknown` vs `tham_hoc`) trước GĐ4.

## 12. Câu hỏi cho Admin

1. **Quyền:** PTDA có dùng thương mại không? (quyết định bắt buộc trước GĐ3 — xem rights-assessment.md §4).
2. Ảnh trang p0472 (壽昌經/雲門澄): cho phép tìm nguồn ảnh để khôi phục 10 nhãn mất chữ, hay giữ `unresolved`?
3. R08/R09 có được đưa vào bộ quy tắc chính thức cho GĐ4–5 không?
4. Khi nào cho phép commit các file GĐ0–2 (hiện chưa commit gì)?

---

## ✅ Tuyên bố

**DỪNG tại cuối giai đoạn 2, chờ Admin chỉ đạo giai đoạn 3.**
Không tự đánh DONE cho T429 — chờ daoanh-qa kiểm chứng độc lập và Admin xác nhận.
