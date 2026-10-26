# Prompt chuẩn v3.2 (CHỐT 2026-10-22, đã đạt trên B) dịch kinh lục DILA cho Cloud session (T453)

> Script import còn tự sửa khi nạp: 疏 → "Sớ", viết hoa chữ đầu mỗi từ của title_vi.

Dùng cho mọi tạng: thay `<X>` (B, C, … T, X). Kết quả lưu
`data/dila_import/authority_catalog.2026-10/vn_dila_authority_catalog/<X>.vi.json`
(hoặc `<X>.part1.vi.json`, `<X>.part2.vi.json`… — khi đó xoá `<X>.vi.json` cũ).
Coordinator kiểm: `python -X utf8 scripts/t453_dila_catalog_import.py --dry-run --canon <X>` → dòng
`QA bản dịch: ĐẠT` mới xin Admin duyệt `--apply`.

Bài học từ lần dịch B đầu (QA CHƯA ĐẠT 206 lỗi): 83 tiêu đề để dạng "Trường/trưởng", 160 byline trống
vì vai trò ngoài bảng, 5 tiêu đề trống vì chữ hiếm. Prompt dưới đây cấm cả ba.

---

## PROMPT (dán nguyên văn, kèm nội dung `<X>.json`)

Bạn dịch file `<X>.json` — kinh lục DILA authority_catalog (經錄規範資料庫, CC BY-SA 3.0) — sang tiếng Việt
cho dự án Phật học. Đây là **phiên âm Hán Việt tên sách/tên người**, không phải dịch nghĩa.

### Đầu ra
Một khối ```json duy nhất: **cùng khóa, cùng thứ tự, giữ nguyên 100% trường gốc** (không đổi, không xoá, không
định dạng lại giá trị). Chỉ THÊM các trường dưới đây. Trường gốc không có (vd. `dynasty`) → không thêm trường tương ứng.
Cuối object thêm khóa `"notes": [...]`.

### Trường cần thêm cho mỗi bộ
| Gốc | Thêm | Quy tắc |
|---|---|---|
| `title` | `title_vi`, `title_src`, `title_status` | Phiên âm Hán Việt **đủ mọi chữ**, **viết hoa chữ đầu MỌI từ** (Hoa Nghiêm Kinh Sớ Luận Toản Yếu). |
| `category` | `category_vi`, `category_src`, `category_status` | Theo bảng bộ loại; ngoài bảng → tự dịch. |
| `dynasty` | `dynasty_vi`, `dynasty_src`, `dynasty_status` | Theo bảng triều đại; ngoài bảng → tự dịch. |
| `byline` | `byline_vi`, `byline_src`, `byline_status` | Xem quy tắc byline. |
| `contributors[i].name` | `name_vi`, `name_vi_src`, `name_vi_status` | Phiên âm đúng chữ trong file (không thay bằng tên khác cùng ID). |

`*_src` = `"table"` nếu lấy từ bảng dưới, ngược lại `"ai"`. Mọi `*_status` = `"unreviewed"`.

**QUAN TRỌNG (v3.1):** KHÔNG dùng script hay bảng tra từng chữ (charmap) để phiên âm `title_vi` và `byline_vi`.
Hãy tự đọc CẢ CỤM như một người học Phật thông Hán văn, chọn âm theo nghĩa trong ngữ cảnh. Bảng ký tự chỉ dùng
để tra chữ hiếm mà bạn không biết. Mỗi chữ đa âm (般, 若, 藏, 長, 行, 梵, 數, 樂, 說, 傳, 重, 調, 降…) phải quyết định
theo nghĩa, không lấy cách đọc đầu. (Lý do: lần chạy B v3 Cloud tra charmap và lấy cách đọc đầu cho chữ đa âm.)

### BỐN LỆNH CẤM (vi phạm = làm lại) — PROMPT v3
1. **Không bao giờ để trống** `title_vi`, `byline_vi` (khi `byline` có chữ), `name_vi`. Chữ hiếm vẫn phải đọc
   (vd. 俎 trở · 箋 tiên · 騭 chất · 喫 khiết · 并 tịnh · 丏 miện · 霈 bái).
2. **Không bao giờ dùng "/"** hay liệt kê nhiều cách đọc. Chọn MỘT cách đọc theo ngữ cảnh Phật học:
   般若 Bát-nhã · 波羅蜜 Ba-la-mật · 梵 Phạm · 數 Số · 說 Thuyết · 長部/長阿含 Trường · 長老 Trưởng lão · 大藏/藏經/三藏 Tạng · 法句 Pháp Cú · 經 Kinh · 論 Luận ·
   疏 Sớ (bản chú giải, KHÔNG đọc "Sơ") · 鈔 Sao · 記 Ký · 義 Nghĩa · 行 Hành/Hạnh theo nghĩa
   (修行 tu hành, 行願 hạnh nguyện) · 樂 Lạc/Nhạc · 說 Thuyết · 見 Kiến · 識 Thức · 解 Giải · 傳 Truyện (sách)/Truyền (truyền thừa).
   Không chắc → chọn cách thông dụng nhất và ghi `title_note`.
3. **Không đổi** `id`, `authorityID`, số, năm; không bịa năm/triều đại/nơi chốn.
4. **Không ghi `*_note` chung chung** ("tên người nước ngoài…", "cần xác nhận"). Chỉ ghi khi có điều CỤ THỂ cần Admin rà, vd. "B.json ghi 范寄東, là tên tự của 范古農".

### Quy tắc byline
`byline_vi` = [triều đại nếu byline có] + tên người + vai trò (dùng ĐÚNG từ trong bảng, vd. 編 = "biên", không viết "biên soạn"), giữ thứ tự gốc. Nhiều người/vế ngăn bởi `　`
(khoảng trắng toàn góc), `．`, `、` → nối bằng `"; "`. Byline chỉ có tên (vd. `彌勒`) → chỉ ghi tên.
Vai trò: 著 trước tác · 譯 dịch · 造 tạo · 編 biên · 述 thuật · 撰 soạn · 集 tập · 輯 tập · 釋 thích · 註/注 chú ·
疏 sớ · 記 ký · 錄 lục · 講 giảng · 說 thuyết · 校 hiệu · 校釋 hiệu thích · 集註 tập chú · 纂 toản · 編纂 biên toản ·
編修 biên tu · 筆錄 bút lục · 修 tu · 譯註 dịch chú · 講述 giảng thuật · 同譯 đồng dịch · 口述 khẩu thuật · 提唱 đề xướng · 造頌 tạo tụng · 補 bổ · 證 chứng · 重 trùng · 改寫 cải tả · 繪圖 hội đồ · 等 đẳng. Vai trò khác → phiên âm Hán Việt.
Ví dụ: `均如著　金知見編` → `Quân Như trước tác; Kim Tri Kiến biên`; `唐 慧菀述` → `Đường Tuệ Uyển thuật`.

### Bảng bộ loại
事彙部類 Sự vựng bộ loại · 新編部類 Tân biên bộ loại · 大集部類 Đại tập bộ loại · 律部類 Luật bộ loại ·
論集部類 Luận tập bộ loại · 瑜伽部類 Du-già bộ loại · 阿含部類 A-hàm bộ loại · 華嚴部類 Hoa Nghiêm bộ loại ·
般若部類 Bát-nhã bộ loại · 法華部類 Pháp Hoa bộ loại · 寶積部類 Bảo Tích bộ loại · 涅槃部類 Niết-bàn bộ loại ·
經集部類 Kinh tập bộ loại · 密教部類 Mật giáo bộ loại · 禪宗部類 Thiền tông bộ loại · 淨土宗部類 Tịnh Độ tông bộ loại ·
史傳部類 Sử truyện bộ loại · 本緣部類 Bản duyên bộ loại · 中觀部類 Trung quán bộ loại · 毘曇部類 Tì-đàm bộ loại.
Nhiều giá trị cách bằng dấu phẩy → dịch từng cái, giữ dấu phẩy.

### Bảng triều đại
東漢/後漢 Đông Hán · 三國 Tam Quốc · 吳 Ngô · 西晉 Tây Tấn · 東晉 Đông Tấn · 劉宋 Lưu Tống · 蕭齊 Tiêu Tề · 梁 Lương ·
陳 Trần · 北魏 Bắc Ngụy · 隋 Tùy · 唐 Đường · 五代 Ngũ Đại · 宋 Tống · 遼 Liêu · 金 Kim · 元 Nguyên · 明 Minh · 清 Thanh ·
民國 Dân Quốc · 新羅 Tân La · 高麗 Cao Ly · 朝鮮 Triều Tiên · 日本 Nhật Bản.

### Tự kiểm trước khi trả (bắt buộc, ghi kết quả vào đầu `notes`)
- Số bộ vào = số bộ ra; mọi trường gốc giống hệt.
- Số `title_vi` trống = 0; số `title_vi` chứa "/" = 0.
- Số `byline_vi` trống (khi `byline` có chữ) = 0; số `name_vi` trống = 0.
- JSON hợp lệ.
Rà lại MỌI title có chữ đa âm. Dòng đầu `notes`: `"SELF-CHECK: in=N out=N title_empty=0 title_slash=0 byline_empty=0 name_empty=0 polyphonic_reviewed=K"`.
Cách làm đã đạt (B v3.1): **tự đọc và viết tay bản dịch theo nghĩa, script chỉ dùng để ghép vào bản ghi và tự kiểm.** Nếu dịch theo lô, cuối cùng **GỘP tất cả lô thành MỘT file `<X>.vi.json`** và trả file đó để tải xuống (không chỉ dán trong chat). Chữ thật sự không đọc được → giữ nguyên chữ Hán trong `_vi` + `*_note`.
Chỗ nào chưa đạt → sửa rồi mới trả. Các dòng `notes` sau: chỗ cần Admin rà (dị thể, biệt hiệu khác tên DB…).

### Tạng lớn
Nếu không trả hết một lần: dịch theo lô 60 bộ (theo thứ tự khóa), mỗi lô một khối JSON riêng có `notes` riêng,
đặt tên `<X>.part1.vi.json`, `<X>.part2.vi.json`, …

---

## Coordinator (không phải việc của Cloud)
- Tên người hiển thị: `people.name_vi` theo `id` (DB thắng); tên bản dịch lưu tham khảo trong `vi_json`.
- Tạng T: đối chiếu `canon_catalog` theo mã trước khi dùng `title_vi` AI.
- `--dry-run` phải ra `QA bản dịch: ĐẠT` (script kiểm đúng 4 điều kiện trên) mới xin duyệt `--apply`.
