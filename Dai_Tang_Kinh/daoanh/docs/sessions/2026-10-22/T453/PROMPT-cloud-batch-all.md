# Prompt dịch HÀNG LOẠT 24 tạng còn lại (T453) — dùng kèm PROMPT-cloud-translate.md (v3.2)

Đã xong: A (9), B (234). Còn 24 tạng, 5.504 bộ, sắp từ nhỏ đến lớn:
M 1 · ZS 1 · GB 2 · S 2 · U 2 · CC 6 · LC 7 · K 9 · C 11 · P 13 · L 21 · TX 21 · F 27 · YP 32 · N 38 · Y 42 ·
GA 51 · D 64 · G 65 · I 101 · ZW 202 · J 658 · X 1671 · T 2457.

Tên người: KHÔNG cần chuẩn — task khác chuẩn hoá; import luôn hiển thị tên theo DB (people.name_vi theo ID).

---

## PROMPT (dán nguyên văn)

Nhiệm vụ: dịch HÀNG LOẠT kinh lục DILA authority_catalog sang tiếng Việt, áp dụng ĐÚNG mọi quy tắc trong
"PROMPT CHUẨN v3.2" bên dưới cho TỪNG file. Không hỏi lại giữa chừng; tự làm tiếp tới khi hết.

NGUỒN: tải từ https://raw.githubusercontent.com/DILA-edu/Authority-Databases/master/authority_catalog/json/<X>.json
với <X> lần lượt: M, ZS, GB, S, U, CC, LC, K, C, P, L, TX, F, YP, N, Y, GA, D, G, I, ZW, J, X, T
(nhỏ trước, lớn sau). Bỏ qua A và B (đã xong).

CÁCH LÀM CHO MỖI FILE <X>:
1. Tự đọc và viết tay bản dịch theo nghĩa (như người học Phật thông Hán văn); script chỉ dùng để ghép vào bản ghi và tự kiểm. Không phiên âm bằng bảng tra từng chữ.
2. File > 60 bộ: dịch theo lô 60 bộ, rồi GỘP thành MỘT file <X>.vi.json.
3. Chạy tự kiểm (bắt buộc) và ghi dòng đầu notes:
   "SELF-CHECK: in=N out=N title_empty=0 title_slash=0 byline_empty=0 name_empty=0 polyphonic_reviewed=K".
   Chưa đạt → tự sửa rồi kiểm lại. Không chuyển sang file sau khi file trước chưa đạt.
4. Lưu <X>.vi.json vào thư mục đầu ra vn_dila_authority_catalog/.

ĐẦU RA CUỐI:
- Tất cả file <X>.vi.json trong một thư mục vn_dila_authority_catalog/, NÉN thành vn_dila_authority_catalog_batch.zip để tải về.
- File BATCH-REPORT.md: bảng mỗi tạng một dòng (tạng, số bộ vào/ra, SELF-CHECK đạt/không, số notes), và tổng.
- Nếu hết giới hạn phiên trước khi xong: trả ngay zip các file ĐÃ ĐẠT + BATCH-REPORT.md ghi rõ tạng nào đã xong,
  tạng nào đang dở (đến khóa nào). Lượt sau khi tôi nói "tiếp tục" thì làm tiếp từ chỗ dở, không làm lại file đã đạt.

[Dán toàn bộ PROMPT CHUẨN v3.2 ở đây]

---

## Coordinator (local)
1. Giải nén zip vào `data/dila_import/authority_catalog.2026-10/vn_dila_authority_catalog/` (không đè A.vi.json, B.vi.json).
2. `python -X utf8 scripts/t453_dila_catalog_import.py --dry-run --canon <X>` từng tạng → bảng QA tổng.
3. Admin duyệt một lần → `--apply` (gom tạng, 1 lần backup).
