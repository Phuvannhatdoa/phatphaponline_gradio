# Phiên âm Hán-Việt địa danh DILA (Place Authority) — âm Nam

Nguồn: `Buddhist_Studies_Place_Authority.xml` + `districts.xml` (2026-10).
- 59.375 địa danh `PL…`, trong đó **59.353** có tên Hán chính (`persName`/`placeName` không có `type`, ưu tiên zho-Hant) → `vn_place_name_vi.xml`.
- 16.907 đơn vị hành chính (`PLA` quốc gia 42, `PLB` 471, `PLC` 4.637, `PLD` 11.757) → `vn_district_name_vi.xml`.
- 4.325 chuỗi phân cấp trong từng địa danh (vd. `中國-雲南省-曲靖市-富源縣`) được dịch từng đoạn và ghi ở `<district_vi>`; phần chữ Latin (Balkh…) giữ nguyên.

## Trạng thái: CHƯA THẨM ĐỊNH HỌC THUẬT
Cách làm giống bản tên người (xem `README.md`): âm từng chữ do mô hình viết trực tiếp, đối chiếu máy với các từ điển trong repo
(Nguyễn Quốc Hùng, Thiền Tông Hán Việt, Duy Lực, Phật Quang, Đạo Uyển). Đối chiếu máy không thay thế người thẩm định.

| Tầng | Ý nghĩa | Địa danh | Đơn vị hành chính |
|---|---|---|---|
| 1 | Mọi chữ khớp từ điển (cho phép biến thể Bắc/Nam), không còn chữ đa âm chưa giải quyết | 53.963 | 15.984 |
| 2 | Có chữ chưa đối chiếu đủ, hoặc chữ chịu **quy ước địa danh của mô hình** (xem dưới; liệt kê trong `<rule>`) | 2.343 | 618 |
| 3 | Còn chữ đa âm / lệch từ điển / âm đoán — **admin cần duyệt** | 2.889 | 278 |
| 4 | Có chữ chưa có âm (giữ chữ Hán trong `name_vi`) — **admin cần duyệt** | 158 | 27 |

Tầng 3-4 vẫn có `name_vi` tạm. Danh sách duyệt: `review_needed_places.tsv` (3.047 dòng) và `review_needed_districts.tsv` (305 dòng);
cột `name_vi_da_duyet` để trống cho admin.

## Khác với bản tên người — cần biết
- **Không tự sửa theo từ điển ở cấp địa danh.** Từ điển có lỗi đánh máy (vd. 香泉寺 → "Tuyển") và có tiêu đề dịch nghĩa thay vì phiên âm
  (六波羅密 → "Sáu Ba La Mật", 須彌山 → "Núi Tu Di"). Dạng của từ điển chỉ được ghi ở `<review>` để người duyệt so sánh (48 tên).
- **Quy ước địa danh do mô hình soạn (không có số liệu từ điển trong repo):** 長 Trường, 台 Đài, 浦 Phổ, 藏 Tạng, 屏 Bình, 谷 Cốc, 衡 Hành,
  梵 Phạm, 祐 Hựu, 鷲 Thứu, 繁 Phồn, 邛 Cùng, 為 Vi, 刺 Thích, 沈 Thẩm, 沮 Thư, 賈 Giả, 耶 Da (xem `charmap_dia_danh.tsv`, `tinh_trang=quy_uoc_dia_danh_mo_hinh`).
  Chữ còn đa âm trong địa danh vẫn gắn cờ: 樂 Lạc/Nhạc, 蔚 Uất/Úy, 屯 Đồn/Truân, 行 Hành/Hạnh, 相 Tương/Tướng, 重 Trùng/Trọng…
- **Quy tắc ghép từ** (`<rule>`): 重慶 Trùng Khánh, 天台 Thiên Thai, 台州 Thai Châu, 番禺 Phiên Ngung, 蔚州 Uất Châu, 澳門 Áo Môn,
  龜茲 Khâu Từ, 月氏 Nguyệt Chi, 吐蕃 Thổ Phồn, 西藏 Tây Tạng, 般若 Bát Nhã, 伽耶 Già Da, 祇園 Kỳ Viên…
- **Kanji Nhật dạng giản** (区 県 浜 広 …) và chữ giản thể trong tên đơn vị hành chính: lấy âm Hán-Việt của dạng phồn thể tương ứng.
- **Tên nước hiện đại** (vd. 阿富汗 → A Phú Hãn) chỉ là phiên âm Hán-Việt của tên Hán, không phải tên tiếng Việt thông dụng (Afghanistan). Cần admin quyết định có dùng làm tên hiển thị hay không.
- Hiện có 2.305 tên khớp đúng cặp Hán–Việt trong từ điển, 1.261 tên có tiêu đề tiếng Việt trùng (Phật Quang…); phần lớn còn lại chỉ có chứng cứ cấp chữ.

## File
- `vn_place_name_vi.xml` — `<place dila_id tier>`: `name_zh`, `name_vi`, `category_zh`, `district_zh`, `district_vi`, `review`, `evidence`, `rule`, `alternatives`.
- `vn_district_name_vi.xml` — `<unit dila_id type tier>`: `name_zh`, `name_vi`, `review`.
- `review_needed_places.tsv`, `review_needed_districts.tsv` — tầng 3-4 để admin duyệt (UTF-8 BOM, mở được bằng Excel).
- `charmap_dia_danh.tsv` — bảng chữ dùng cho địa danh/đơn vị, âm sử dụng, tình trạng, âm trong từ điển.
- `import_name_vi.py` — dùng chung: `--element place --table <bảng> [--id-col dila_id] [--tier-column <cột>] [--district-column <cột>]`;
  `--element unit` cho đơn vị hành chính. Mặc định chạy thử, chỉ điền ô trống, nạp cả 4 tầng; tự sao lưu khi `--apply`.
