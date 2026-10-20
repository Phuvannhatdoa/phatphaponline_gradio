# T215 — Kiểm lại Diên Phúc Tuệ Thăng sau Admin sửa TTL

Ngày 2026-10-02. **Chưa submit DB** vì quan hệ hasTeacher chưa đạt điều kiện. TTL và DB không sửa trong lần check này.

## Kết quả

- Subject, P1 và tên Diên Phúc Tuệ Thăng đã khớp; không còn self-edge.
- Tiểu sử Tuyền Châu, Hàn Nham, Kiến Ninh phù hợp dấu hiệu DILA 延福慧升 A008431.
- hasTeacher đang chứa4 người, nhưng DILA xác nhận thầy truyền pháp là Đoan Dụ A007993. Ba người còn lại có cùng thầy này; chưa có căn cứ làm thầy truyền pháp của Tuệ Thăng.
- Số đời50 giữ nguyên, không chứng nhận đúng vì chưa đạt gate3 chứng cứ.

| TTL target | DILA chính thức | Vai trò có căn cứ |
|---|---|---|
| duc_vuong_doan_du | A007993端裕 | Thầy truyền pháp |
| tinh_tu_su_nhat | A008424師一 | Đồng môn, cùng thầy Đoan Dụ |
| dao_trang_phap_toan | A008429法全 | Đồng môn, cùng thầy Đoan Dụ |
| thanh_luong_than | A008421清涼坦 | Đồng môn, cùng thầy Đoan Dụ |

## Đề nghị TTL

```ttl
bkg:hasTeacher <ex:monk/duc_vuong_doan_du> ;
```

Giữ3 triple nhãn tham chiếu, không ghi3 người ấy vào hasTeacher. Không tự thêm predicate đồng môn chưa được schema định nghĩa.

## DB cần xử lý sau khi TTL đạt

- Không có row dien_phuc_tue_thang
- Row duc_vuong_doan_du chứa tên/tiểu sử Tuệ Thăng, filename TS-Dien-Phuc-Tue-Thang, DILA A045939
- Đạo Tràng Pháp Toàn local A015860, chính thức A008429

Không đổi nhãn row thầy sang tên Tuệ Thăng. Cần snapshot từng row, kiểm claim/mapping, chuyển dữ liệu đúng người và vô hiệu assertions TTL sai; không ghi đè DILA/Marcus.

## Nguồn DILA đã đọc

- [DILA A008431](https://authority.dila.edu.tw/person/search.php?aid=A008431)
- [DILA A007993](https://authority.dila.edu.tw/person/search.php?aid=A007993)
- [DILA A008424](https://authority.dila.edu.tw/person/search.php?aid=A008424)
- [DILA A008429](https://authority.dila.edu.tw/person/search.php?aid=A008429)
- [DILA A008421](https://authority.dila.edu.tw/person/search.php?aid=A008421)

## Giới hạn

RDF parser CLI còn thiếu rdflib. Importer regex hiện lấy target đầu hasTeacher và có thể bỏ sót danh sách dấu phẩy; không dùng việc API chỉ hiện1 thầy để chứng minh TTL hiện tại sạch.
