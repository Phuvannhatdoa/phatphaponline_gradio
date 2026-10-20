---
id: T275
title: "Neo số đời từ TTL: tra cứu đời theo neo, BFS DILA chỉ để xác nhận khi chưa có neo"
module: Lineage / Generation
priority: high
status: in_progress
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: T270
plan_approved_at: "2026-10-10 (Admin phê chuẩn: dùng neo số đời từ TTL; BFS chỉ xác nhận khi không có neo)"
done_when: >
  (1) Script scripts/t275_ttl_anchor.py đọc generationOrder + hasTeacher/hasDisciple từ TTL, không ghi DB,
      xuất docs/evidence/2026-10-10_T275_ttl_anchor_edges.tsv với thống kê khớp / lệch / thiếu.
  (2) Mỗi neo có nhãn hệ đếm (ví dụ ca_diep_1, linji) — không trộn số đời của hai hệ trong cùng một chuỗi.
  (3) Router: từ một vị, đi lên tới gốc và xuống đệ tử trực tiếp, trả về số đời. Đã kiểm 3 mẫu
      (Bổn Quả Khoáng Viên 69 → Nguyên Thiều Siêu Bạch 70; Mã Tổ 35; Nghĩa Huyền 38).
  (4) Admin quyết định 48 cạnh lệch (khớp +1 bị sai) trước khi dùng làm neo chính thức.
  (5) Engine đọc neo TTL trước; BFS DILA chỉ chạy khi vị đó không có neo. Thay đổi engine cần duyệt riêng, chưa làm.
  (6) QA độc lập bằng daoanh-qa trước khi Admin xác nhận DONE.
  (7) Admin xác nhận DONE — KHÔNG tự đánh DONE.
revert: >
  Chưa ghi DB. Script và file TSV là dẫn xuất; xóa là quay lại. Mọi sửa file hiện có
  (build_t263_status.py, dashboard_process.html, tasktodo.md) có bản sao trong
  docs/sessions/2026-10-10/ trước khi sửa.
outcome: >
  2026-10-10: Bước 1, 2, 4 xong (script + TSV + router đã chạy). Sửa regex nhận `a bkg:Monk` (không có ngoặc);
  thống kê sau sửa: 1.037 vị, 1.055 cạnh thầy→đệ; khớp +1: 936; lệch: 48; thiếu file đệ tử: 70; thiếu số đời: 1.
  Chuỗi hasTeacher từ Đạt Ma (28) đến Dương Kỳ Phương Hội (45) liên tục trong TTL (Nghĩa Huyền 38 → Phương Hội 45,
  7 bậc). Đoạn văn "đời 18 từ Nghĩa Huyền" chưa khớp chuỗi TTL, cần nguồn. Chưa ghi DB, chưa đánh DONE.
  2026-10-11: Bước 3 xong — thêm `dharma_lineage` (từ `bkg:dharmaLineageName`) vào TSV edges và lines.
---

# T275 — Neo số đời từ TTL

## 1. Vì sao làm

- Engine hiện tại (`parents()` trong `src_python/generation_engine_v2.py`) đi ngược cạnh DILA và BFS
  mọi nhánh. Với nhiều vị, kết quả là `incomplete` hoặc `unreachable` (ví dụ đời 30 sau Lâm Tế không
  chốt được một ID nào ở trạng thái sạch).
- TTL đã ghi sẵn `bkg:generationOrder` và `bkg:hasTeacher`/`hasDisciple` cho 1.037 file. Số này là neo
  có sẵn, không cần suy luận từ DILA.
- Ví dụ đã kiểm: Bổn Quả Khoáng Viên ghi 69, Nguyên Thiều Siêu Bạch ghi 70, quan hệ trực tiếp.

## 2. Quy tắc (đã phê chuẩn)

1. **Neo trước:** nếu vị có `generationOrder` trong TTL, dùng số đó và đi theo cạnh TTL để tra đường.
2. **BFS chỉ xác nhận:** chỉ chạy BFS DILA khi vị không có neo, hoặc để kiểm tra chéo.
3. **Cạnh lệch không tự gán:** cạnh TTL mà đệ ≠ thầy+1 đưa vào hàng chờ Admin, không tự sửa.
4. **Gắn hệ đếm:** mỗi neo ghi rõ thuộc hệ nào (Ca Diếp 1, Thích Ca 1, Lâm Tế…). Không cộng số giữa hai hệ.
5. **Quy tắc đếm đời (Admin làm rõ 2026-10-10):** Ma Ha Ca Diếp là đời 1 theo Truyền Đăng Lục và xuyên suốt cây truyền thừa. Vị khai tổ của một nhánh mới tính là đời 1 của nhánh đó. Công thức "đệ = thầy + 1" là đúng. Số lệch trong TTL do người nhập số có thể sai, không phải lỗi của tu sĩ. Vì vậy các cạnh lệch cần đối chiếu lại số nhập trong TTL với công thức, và xác định vị nào là khai tổ nhánh mới.

## 3. Các bước

- [x] **Bước 1 — Đọc TTL (chỉ đọc):** `scripts/t275_ttl_anchor.py` đọc generationOrder, hasTeacher, hasDisciple của 1.021 vị.
- [x] **Bước 2 — Kiểm cạnh:** 1.007 cạnh; khớp +1: 911; lệch: 48; thiếu file đệ tử: 47; thiếu số đời: 1. Xuất `docs/evidence/2026-10-10_T275_ttl_anchor_edges.tsv`.
- [x] **Bước 3 — Gắn nhãn hệ đếm cho neo:** thêm trường `dharma_lineage` (từ `bkg:dharmaLineageName` trong TTL) vào TSV edges và lines (2026-10-11).
- [x] **Bước 4 — Router tra cứu:** `--chain <slug>` đi lên tới gốc và xuống đệ tử trực tiếp. Đã kiểm: Bổn Quả Khoáng Viên (69) → Nguyên Thiều Siêu Bạch (70); Mã Tổ (35); Nghĩa Huyền (38).
- [ ] **Bước 5 — Admin xử lý 48 cạnh lệch:** phân loại (đệ cùng số với thầy / số đặt lại 1–3 / nhảy số / lỗi file). Admin quyết định từng nhóm.
- [ ] **Bước 5b — ID cục bộ cho thiền sư Việt Nam không có DILA (Admin đề xuất 2026-10-10):** hiện DB có 48.673 người, tất cả đều có ID DILA (A…); không có ID nội bộ nào khác. Ánh xạ TTL→DILA có sẵn trong `vn_person_authority` (1.507 dòng; 1.296 có dila_id; 211 chưa có). Đề xuất: cấp số thứ tự cục bộ theo kiểu DILA cho nhóm này, giữ cột `local_id` riêng, ghi `ttl_filename` làm khóa; khi có DILA sau này thì gán `dila_id` và giữ `local_id` như bí danh. **Cần Admin duyệt trước khi thêm cột/bảng (đổi schema).**
- [ ] **Bước 6 — Engine đọc neo TTL trước:** sửa `generation_engine_v2.py` để ưu tiên neo, BFS DILA chỉ khi không có neo. Cần backup và duyệt riêng trước khi sửa.
- [ ] **Bước 7 — QA** bằng `daoanh-qa`: đối chiếu số đời sau khi sửa với bảng neo, không mất số của các tông khác.
- [ ] **Admin xác nhận DONE.**

## 3b. Trạng thái nhánh (lưu để đối chiếu sau)

- **Đã lưu — chuỗi Lâm Tế:** `docs/evidence/2026-10-10_T275_chuoi_lam_te.tsv`, 616 dòng là con cháu Lâm Tế Nghĩa Huyền trong TTL. Chuỗi từ Đạt Ma (28) đến Dương Kỳ Phương Hội (45) liên tục. Trong 616 dòng có 24 dòng lệch, cần rà.
- **Đã lưu — đường truyền toàn bộ TTL:** `docs/evidence/2026-10-10_T275_ttl_lines.tsv`, 1.037 dòng.
- **Đã build bước 1 (2026-10-10):** API chỉ đọc `GET /daoanh/api/ttl/anchor-chain?slug=<slug>` trong `api_ttl_anchor.py`, đăng ký trong `app.py` (2 dòng). Kiểm thử bằng Flask test client: Dương Kỳ Phương Hội = 45, Nghĩa Huyền = 38 nằm trong chuỗi, slug lạ → 404, thiếu slug → 400. Log: `docs/sessions/2026-10-10/T275-build.log`. Chưa chạy server thật, chưa kiểm trên trình duyệt.
- **Đã build bước 2 (code, chưa kiểm trình duyệt):** endpoint `GET /daoanh/api/ttl/anchor-by-dila?ids=...` (trạng thái ok / conflict / unmapped, không đoán); `places.html` gắn nhãn `TTL <đời>` hoặc `TTL ?` lên nút cây sau khi vẽ (hàm `_t275ApplyTtl`, 2 lời gọi renderer). Kiểm: API qua Flask test client PASS; `node --check` JS OK. Chưa kiểm trên trình duyệt vì cổng 5000 đang chạy tiến trình cũ, cần khởi động lại server. Log: `docs/sessions/2026-10-10/T275-step2-build.log`.
- **Dữ liệu cần Admin xử lý (ánh xạ TTL↔DILA):** Phương Hội A004146 sai chính tả tên file; A020018 và A010511 có nhiều file (xung đột); 58 dòng tên file rỗng, gồm Lâm Tế Nghĩa Huyền A003627.
- **Chờ upload:** các tông chưa có file TTL local, gồm khoảng 22 dòng tiếng Việt của Tào Động, Vân Môn và các nhánh khác. Khi nạp file, chạy lại `scripts/t275_ttl_anchor.py --lines` để đối chiếu.
- **Chưa đối chiếu:** các dòng lệch do gốc bị cắt (Ba Xà Tư Đa, Vô Tận Tuệ Hải) và lỗi tự trỏ của Võ Chuẩn Sư Phạm.

## 3c. Phân vai nguồn (ghi theo yêu cầu Admin 2026-10-10)

- **TTL local:** neo số đời và thầy–đệ trực tiếp, kèm trích dẫn Truyền Đăng Lục. Là nguồn duy nhất có số đời cho dòng Việt Nam. Chưa đủ các tông (Tào Động, Vân Môn còn thiếu file).
- **DILA:** mã định danh chuẩn (A…), 46.004 cạnh thầy–đệ, trích dẫn CBETA. Dùng để xác định danh tính và đối chiếu văn bản gốc. Không dùng để đếm đời trực tiếp.
- **Marcus:** 2.733 cặp DILA có 法嗣, bằng chứng nối pháp độc lập. Thiếu với nhiều thiền sư Việt Nam, nên không dùng một mình cho dòng này.
- **Đường truyền (TSV):** chỉ là lớp dẫn xuất từ TTL, không phải nguồn riêng.

## 2026-10-11 — Phase 2 Analysis & Blockers Assessment

**Session Phase 2 execution attempt:** Kiểm tất cả task lô 1 để xác định có thể hoàn thành mà không cần T265 xong.

**Kết quả đánh giá T275:**
- Bước 1–4 ✅ DONE (2026-10-10): TTL read, 1.037 vị, 1.055 cạnh, thống kê khớp/lệch/thiếu
- Bước 5 (48 cạnh lệch): Admin phân loại cần thêm 1–2 lần sửa TTL hoặc quyết định nhận/bỏ
- **Phát hiện quan trọng:** 211 vị Việt Nam (vn_person_authority) không có DILA ID — cần cấp local_id
  hoặc strategy cho nhóm này (Admin 2026-10-10 đề xuất nhưng chưa duyệt schema change)
- **Phụ thuộc Kiến trúc T274:** T274 phát hiện base pool DILA không chứa cạnh Việt Nam → T275
  cần quyết định cách xử lý TTL → DILA ID mapping không có DILA baseline
- **Bước 6 (Engine sửa):** Cần duyệt riêng trước khi sửa `generation_engine_v2.py`
  (không tự sửa vì rủi ro regression)

**Status 2026-10-11:** Bước 5 chờ Admin phân loại 48 cạnh + xử lý 211 Việt Nam chưa có DILA ID.
Không ghi DB. Không merge sang engine. Chờ session sau.

## 3d. Kiểm chú thích nét trên tree (places.html, mục "Chú thích màu nét")

Kết quả kiểm: 4 loại nét trong chú thích khớp với code vẽ nét (`_t127EdgeStyle` và `_renderHierarchyTree`). Không xóa code.
- Chỗ không khớp T275: "≥2 nguồn xác nhận" chỉ đếm DILA và Marcus (`consensus_status`, `agreeing_source_count`). TTL không được tính là nguồn. Cạnh chỉ có TTL, theo quy tắc T274, sẽ hiện là nét đứt cam (1 nguồn) thay vì nét liền vàng.
- Trục tổ sư (nét cam đậm) lấy từ endpoint `ancestor-spine` (đi bộ DILA), không lấy từ TTL.
- **Đã sửa (Admin phê chuẩn 2026-10-10):** giữ 4 nét, chú thích ghi rõ tên nguồn: "≥2 nguồn xác nhận (DILA, Marcus, ZQ Local)" và "1 nguồn (DILA, Marcus hoặc ZQ Local)". Chỉ đổi chữ chú thích, không đổi logic vẽ nét. Sao lưu: `docs/sessions/2026-10-10/places.html.bak-before-legend-T275`. Chưa kiểm trên trình duyệt; cần kiểm tay khi mở trang.

## 4. Ràng buộc

- Không ghi DB trong task này. Không đổi schema.
- Không sửa TTL. Không git. Không deploy VPS.
- Mọi file sửa có bản sao trong `docs/sessions/2026-10-10/` trước khi sửa.

## 5. Liên quan

- T270 (nối pháp TTL + Marcus), T274 (quy tắc dòng Việt Nam), T263/T265 (xung đột năm H3).
- Bản đồ số đời kiểm chứng: `docs/evidence/2026-10-10_T275_ttl_anchor_edges.tsv`.
