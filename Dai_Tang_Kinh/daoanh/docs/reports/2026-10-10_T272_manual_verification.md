# T272 — Xác minh bằng tay: TTL filename gắn nhiều mã DILA

**Ngày:** 2026-10-10
**Phạm vi:** Chỉ đọc DB (`data/lineage.db`, mode=ro, -X utf8). Không ghi DB, không git, không gọi API, không xóa file.
**File dữ liệu kèm:** `docs/evidence/2026-10-10_T272_ambiguous_ttl_names.csv`

> Báo cáo này **không kết luận ĐẠT**. Đây là tài liệu chuẩn bị cho Admin xác minh bằng tay; các quyết định (CÙNG NGƯỜI / KHÁC NGƯỜI / CHƯA RÕ) chưa được điền.

---

## 1. Tóm tắt số liệu

| Chỉ số | Giá trị |
|---|---|
| Tổng số dòng `vn_person_authority` | 1507 |
| Số dòng `ttl_filename` rỗng/NULL (xử lý riêng, không nằm trong 224 nhóm) | 58 |
| Số nhóm `ttl_filename` có `COUNT(DISTINCT dila_id) > 1` | 224 |
| Tổng số dòng `vn_person_authority` thuộc 224 nhóm trên | 646 |
| Nhóm mà mọi dòng cùng `name_vi` (nghi cùng người, nhiều mã DILA trùng) | 223 |
| Nhóm có `name_vi` khác nhau trong cùng file TTL (nghi file gộp nhiều người, hoặc lỗi ghép) | 1 |
| Số mã `dila_id` xuất hiện ở nhiều hơn 1 `ttl_filename` khác nhau | **27** (khác với số 29 nêu trong yêu cầu — xem mục 7, ghi nhận sai lệch, chưa rõ nguyên nhân) |

Nhóm có nhiều mã DILA nhất (top 10, đã có trong CSV, thứ tự ưu tiên):

| ttl_filename | số dila_id khác nhau | số dòng |
|---|---|---|
| TS-Mong-Son-Dao-Minh | 14 | 14 |
| TS-Khong-That-Tri-Thong | 11 | 11 |
| TS-Dang-Giac-Pho-Minh | 11 | 11 |
| TS-The-Thang-Ke-Sieu | 10 | 10 |
| TS-Quang-Hieu-Tri-Vien | 8 | 8 |
| TS-Cuu-Tong-Phap-Minh | 8 | 8 |
| TS-Tuong-Chau-Hue-Man | 7 | 7 |
| TS-Tan-La-Phap-Lang | 6 | 6 |
| TS-Tam-Giao-Tri-Tung | 6 | 6 |
| TS-Ngo-Hung-Phap-Hai | 6 | 6 |

58 dòng `ttl_filename` rỗng **không nằm trong file CSV này** — cần một đợt audit riêng (không thuộc phạm vi T272 bước xác minh tên trùng), vì không có tên file TTL để so khớp tiêu đề/hasTeacher.

---

## 2. Vì sao cần xác minh bằng tay (chưa đủ bằng chứng để tự kết luận)

Một `ttl_filename` gắn nhiều `dila_id` có thể là:

- **(a) Cùng một người, nhiều mã DILA trùng lặp** — DILA có thể có nhiều entry authority cho cùng một vị tổ do lỗi nhập liệu nguồn hoặc do cùng người được ghi nhận ở nhiều nguồn khác nhau trong CBDB/DILA.
- **(b) Một file TTL gộp nhiều người khác nhau** — người biên soạn TTL ban đầu có thể đã gộp nhầm nhiều vị có tên gần giống hoặc cùng hiệu vào một file.
- **(c) Lỗi ghép (mapping error)** — quá trình import/ETL gán sai `dila_id` vào `ttl_filename` do khớp tên mà không qua kiểm tra định danh ổn định.

223/224 nhóm có `name_vi` giống nhau trong toàn nhóm — thiên về khả năng (a) hoặc (c), nhưng **tên giống nhau không phải bằng chứng đủ để tự động gộp** (theo quy tắc `naming-and-identity.md`: display name không bao giờ là join key). 1 nhóm có tên khác nhau trong cùng file — cần xem xét khả năng (b).

Không có đủ dữ liệu trong `vn_person_authority`/`people` để tự phân loại — cần đối chiếu trực tiếp nội dung TTL và trang DILA gốc.

---

## 3. Quy trình xác minh bằng tay (cho từng nhóm trong CSV)

Với mỗi `ttl_filename` trong `docs/evidence/2026-10-10_T272_ambiguous_ttl_names.csv`, Admin thực hiện theo thứ tự:

**a. Mở file TTL tương ứng** trong `data/ttl/` (tên file = giá trị cột `ttl_filename` + phần mở rộng `.ttl`, ví dụ `TS-Mong-Son-Dao-Minh.ttl`). Đọc:
   - Tiêu đề / nhãn (label, tên Hán-Việt).
   - Quan hệ `hasTeacher` / `hasDisciple`.
   - Ghi chú hiệu núi, chùa trụ trì nếu có trong comment hoặc property.

**b. Mở trang DILA của từng `dila_id`** trong nhóm (DILA Authority Database — tra theo mã, ví dụ dạng `http://authority.dila.edu.tw/person/?pid=<dila_id>` hoặc URL mẫu tương ứng đã dùng khi import — **cần Admin xác nhận URL thực tế từ log import**, báo cáo này không tự suy URL vì không thấy cột URL lưu sẵn trong `vn_person_authority`/`people`). So sánh:
   - Tên Hán (`name_zh`).
   - Niên đại (birth_year/death_year nếu DILA có).
   - Nơi trụ trì / tông phái.

**c. Đối chiếu với Marcus** qua bảng `marcus_people_link` (cột `person_id` = `dila_id`, cột `marcus_node_id`). Nếu có link, mở record Marcus tương ứng để so lineage bổ sung. Đối chiếu `name_zh` trong `vn_person_authority` với tên Hán ghi trong Marcus nếu có.

**d. Quyết định** cho từng `dila_id` trong nhóm:
   - `CÙNG NGƯỜI` — nếu xác nhận các `dila_id` chỉ là bản ghi trùng của một người → đề xuất gộp (không tự thực hiện gộp trong báo cáo này).
   - `KHÁC NGƯỜI` — nếu xác nhận là người khác nhau trùng tên/hiệu → giữ tách, file TTL cần tách lại nếu đang gộp sai.
   - `CHƯA RÕ` — nếu chứng cứ không đủ → ghi rõ lý do (ví dụ: trang DILA không có thông tin niên đại, TTL không ghi hasTeacher, v.v.).

**e. Ghi kết quả** vào 2 cột cuối của CSV: `admin_quyet_dinh` (một trong 3 giá trị trên) và `admin_ghi_chu` (lý do/chứng cứ tham chiếu). Hai cột này hiện đang để trống, chờ Admin điền tay.

---

## 4. Thứ tự ưu tiên xác minh

CSV đã được sắp theo thứ tự ưu tiên yêu cầu:
1. Nhóm có nhiều `dila_id` nhất trước (ví dụ TS-Mong-Son-Dao-Minh với 14 mã).
2. Trong cùng mức số lượng mã, nhóm có `name_vi` giống nhau trong toàn nhóm được xếp trước nhóm có tên khác nhau.
3. Nhóm có tên khác nhau (hiện chỉ có 1 nhóm) xếp sau cùng trong thứ tự ưu tiên tương đối của nó.

---

## 5. Nhóm mẫu đã biết (nguyên văn từ dữ liệu)

- **TS-Mong-Son-Dao-Minh** — 14 `dila_id` khác nhau, toàn bộ 14 dòng cùng `name_vi = "Mông Sơn Huệ Minh"` (xác nhận đúng như mô tả trong yêu cầu — lưu ý: `name_vi` lưu trong DB là "Mông Sơn Huệ Minh", không phải "Mông Sơn Đạo Minh"; Admin cần xác nhận lại tên chính xác khi đối chiếu TTL/DILA vì tên trong yêu cầu gốc ghi "Dao-Minh/Đạo Minh" khác với giá trị `name_vi` thực tế trong DB).
  - 14 mã: A001195, A002316, A002417, A003517, A004988, A006348, A010735, A013681, A014839, A021146, A023848, A042462, A042958, A043439.
  - Trong đó A001195 **không có** link Marcus (`marcus_people_link`); 13 mã còn lại có link Marcus (match_method ghi trong bảng, Admin tự xem chi tiết).

Nhóm có tên khác nhau trong cùng file (duy nhất, cần xem kỹ khả năng gộp nhầm — chi tiết nằm trong CSV, xếp cuối danh sách theo thứ tự ưu tiên).

---

## 6. Điều kiện DONE cho bước xác minh T272

- Mọi dòng trong CSV (646 dòng / 224 nhóm) có giá trị ở cột `admin_quyet_dinh`, hoặc nếu `CHƯA RÕ` thì `admin_ghi_chu` phải nêu lý do cụ thể (không để trống cả hai).
- Số liệu tổng (224 nhóm, 646 dòng, 58 dòng ttl rỗng) đã được đối chiếu lại với DB tại thời điểm Admin xác nhận (số liệu có thể đổi nếu DB thay đổi giữa lúc xuất báo cáo và lúc Admin xác minh — cần re-run query nếu có cập nhật DB).
- Báo cáo này **chưa đạt điều kiện DONE** — mới là bước chuẩn bị dữ liệu, chưa có quyết định nào được điền.

---

## 7. Lưu ý và các điểm chưa chắc / cần Admin xác nhận thêm

1. **Số mã dila_id xuất hiện ở nhiều file**: yêu cầu gốc nêu "29 mã", nhưng truy vấn thực tế trên `data/lineage.db` chỉ ra **27 mã** `dila_id` xuất hiện ở nhiều hơn 1 `ttl_filename` (không tính các dòng `ttl_filename` rỗng). Không rõ nguyên nhân sai lệch 2 đơn vị — có thể do nguồn số liệu "29" tính theo lần chạy DB khác, hoặc tính cả dòng ttl rỗng theo cách khác. Cần Admin xác nhận lại cách tính "29" ban đầu nếu cần khớp số.
2. Không tìm thấy cột lưu URL trang DILA gốc trong `vn_person_authority` hoặc `people` — bước 3b (mở trang DILA) cần Admin tự tra theo `dila_id` bằng công cụ tra cứu DILA hiện có, báo cáo này không tự tạo URL vì không có cột nguồn trong DB để xác nhận định dạng URL đúng.
3. Tên "Mông Sơn Huệ Minh" trong DB khác với tên "Đạo Minh" nêu trong yêu cầu gốc cho nhóm TS-Mong-Son-Dao-Minh — đây là điểm cần Admin xác nhận khi đọc TTL/DILA (không tự sửa tên trong báo cáo).
4. 58 dòng `ttl_filename` rỗng chưa được xử lý trong CSV này — đúng theo yêu cầu "ghi riêng số dòng rỗng", nhưng chưa có danh sách chi tiết các dòng này; nếu Admin cần audit luôn, cần một CSV riêng (ngoài phạm vi yêu cầu T272 lần này).
5. Cột `admin_quyet_dinh` / `admin_ghi_chu` trong CSV hiện để trống hoàn toàn — không có giá trị nào được agent tự điền, đúng yêu cầu "để Admin điền tay".
6. Báo cáo và CSV được tạo từ truy vấn **chỉ đọc** (`mode=ro`) tại thời điểm 2026-10-10; không có thay đổi nào được ghi vào `data/lineage.db`.
