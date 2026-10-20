# Thẩm định kế hoạch "Thiền Đăng Thế Phổ 禪燈世譜 (X86n1601)" (2026-10-20)

**Người thẩm định:** Claude Code (RC). **Chế độ:** chỉ đọc. Đã đọc thử XML thật trên máy; không ghi DB, chưa tạo task.

## Kết luận

Kế hoạch **đúng hướng và chặt về nguyên tắc**:

- Nguồn bất biến.
- Tách trích xuất khỏi mapping.
- Không tự accepted.
- Không suy số đời.
- Có mẫu chuẩn (gold set) và tập kiểm độc lập.
- Có cổng QA theo giai đoạn.

Tuy nhiên có **9 điểm logic cần sửa hoặc bổ sung**. Phần lớn lộ ra khi đọc XML thật.

## Số đo nhanh từ XML thật (phục vụ Giai đoạn 1–2)

| Mục | Kết quả |
|---|---|
| File | `data/cbeta/xml-p5-full/X/X86/X86n1601.xml`, 803.957 byte, đã có sẵn trên máy (không cần tải) |
| Tiêu đề / tác giả | 禪燈世譜 · 明 道忞編修、吳侗集 |
| Số quyển | 9 (`cb:juan` / `milestone unit="juan"`), khớp kỳ vọng |
| Quyền | `<availability>`: *"Available for non-commercial use when distributed with this header intact."* |
| Thẻ chính | `list` 1.147 · `item` 5.876 · `note` 449 · `p` 187 · `app/lem/rdg` 107 · `g` (gaiji) 87 · **không có `<table>`** |
| Độ sâu list lồng nhau | tối đa 9 |
| Phần sơ đồ | 17 sơ đồ: 三十三祖世系圖, 諸祖旁出法派系圖, 南嶽法派世系圖, 南嶽第四世溈仰宗…, 臨濟宗…, 黃龍 / 楊岐 / 虎丘, 雲門, 雪竇顯 (上 / 下), 法眼, 大鑑下第十世, 青原, 曹洞, 壽昌經, 雲門澄; cùng 2 bài tựa |
| Nhãn đời | `<note place="inline">一世 / 二世 …</note>`; có 10 nhãn bị mất chữ `□□世` |
| Chú thích chéo | 18 lần "別見" (ví dụ "派裔別見", "法嗣別見") |
| `note type` | add / orig / cf1 / cf2 (lớp hiệu đính) |

**Phát hiện quan trọng:**

1. Quan hệ được mã hoá bằng **list/item lồng nhau** (markup rõ ràng), không phải bảng.
2. Hai phần sơ đồ dùng **hai kiểu mã hoá khác nhau**:
   - **三十三祖世系圖:** các tổ là các item **ngang hàng** trong cùng một list (第一祖, 二祖…). Quan hệ nối tiếp nằm ở **thứ tự và nhãn "第N祖"**. List con dưới mỗi tổ là **tiểu sử**. Riêng dưới 慧能, list con gồm cả 1 item tiểu sử và 2 item đệ tử (南嶽懷讓, 青原行思).
   - **Các 法派世系圖:** list con = đệ tử. Nhãn đời tăng dần theo từng cấp (南獄懷讓 一世 → 馬祖道一 二世 → 百丈懷海 三世 → 黃檗希運 四世 → 臨濟義玄 五世). Các item ngang hàng không có nhãn đời (龍興尊宿, 千頃楚南…) là đồng môn cùng thầy. Tiểu sử nằm trong `<p>` của item.
3. **Nguồn có chữ sai:** "南獄懷讓" (獄 thay cho 嶽). Nếu mapping chỉ khớp tên chính xác thì sẽ trượt.

## 9 điểm cần sửa / bổ sung

### 1. Quy tắc "không suy cạnh từ thứ tự" cần sắc thái hơn

Ở 三十三祖世系圖, quan hệ truyền thừa thực sự được biểu diễn bằng **thứ tự item kèm nhãn 第N祖**. Ở các 法派世系圖 thì được biểu diễn bằng **list lồng nhau** (markup, không phải thụt dòng hiển thị). Cấm tuyệt đối "thứ tự / lồng nhau" sẽ làm mất toàn bộ trục tổ sư.

→ **Sửa:** chỉ cho phép suy cạnh từ thứ tự hoặc lồng nhau khi có **quy tắc đã chứng minh, kèm kiểm tra chéo bằng nhãn**. Cụ thể:
- Nhãn đời của con phải bằng nhãn của cha + 1.
- Hoặc dãy 第N祖 phải liên tục.

Vi phạm nhãn thì không tạo cạnh và đưa vào `unresolved`. Bảng quy tắc mẫu R01–R04 trong kế hoạch giả định có "bảng"; nên đổi thành:

| Mã | Kiểu cấu trúc | Ví dụ thật |
|---|---|---|
| R01 | Item ngang hàng có nhãn 第N祖 liên tục ⇒ tổ N truyền cho tổ N+1 | `itemX86p0321a0101` 第一祖 摩訶迦葉 → `itemX86p0321a1001` 二祖 阿難 |
| R02 | Item có nhãn đời k nằm trong list con của item có nhãn đời k−1 ⇒ cạnh thầy → trò | 馬祖道一 (二世) ⊂ 南獄懷讓 (一世), `itemX86p0335a0601` |
| R03 | Item ngang hàng **không nhãn** cùng list con ⇒ cùng thầy với item có nhãn trong list đó | 龍興尊宿, 千頃楚南 cùng cấp với 臨濟義玄 dưới 黃檗 |
| R04 | Item chỉ có văn tiểu sử (không có tên đứng đầu) ⇒ **không phải người**, không tạo cạnh | list con dưới 摩訶迦葉 |
| R05 | "派裔別見 / 法嗣別見" ⇒ chú thích chéo sang sơ đồ khác; **không tự nối**, ghi `cross_ref` chờ duyệt | 南嶽懷讓 "輪派裔別見" |
| R06 | Nhãn đời mất chữ `□□世` ⇒ không dùng kiểm chéo; cạnh ở trạng thái `direction_status = proposed`, cần người duyệt | 10 chỗ |
| R07 | Lớp `note type=orig / add / cf*` và `app/lem/rdg` ⇒ claim tách riêng theo lớp | 107 `app` |

### 2. Trích tên người: bước khó bị bỏ qua

Tên nằm ở text đầu item, sau nhãn đời và trước `<p>` / `<list>`. Tên có thể bị `<lb/>` cắt ngang, chứa gaiji `<g>`, hoặc kèm biệt danh (釋迦牟尼佛 kèm 釋迦文佛 trong note).

→ **Bổ sung** một quy tắc tách tên riêng:
- Giữ cả chuỗi nguồn gốc lẫn dạng chuẩn hoá gaiji (theo `charDecl normalized form`).
- Lấy `item/@xml:id` làm **locator ổn định**. Locator này tốt hơn tự sinh ID.

### 3. Số đời: thêm khái niệm "gốc đếm theo từng sơ đồ"

Nhãn 一世 ở mỗi sơ đồ đếm lại từ gốc của sơ đồ đó. Ví dụ 南嶽 = 一世; tiêu đề "南嶽第五世臨濟宗" lại đếm từ 南嶽.

→ `counting_root_raw` lấy từ **tiêu đề sơ đồ cộng item gốc**. Không được so nhãn đời giữa hai sơ đồ khác nhau. Kế hoạch đã có trường này; chỉ cần ghi rõ phạm vi là "theo từng `cb:div`".

### 4. Loại quan hệ: không nên ép phân 5 loại khi nguồn chỉ cho 1 loại

Sơ đồ "法派世系圖" chỉ khẳng định **pháp hệ** (法嗣). Văn tiểu sử đôi khi nói "參", "得法于"… nhưng đó là văn mô tả, không phải cấu trúc.

→ Loại quan hệ lấy từ **tiêu đề sơ đồ cộng quy tắc**, mặc định `dharma_successor`. Thế độ / thọ giới / tham vấn chỉ ghi khi có câu tiểu sử làm chứng tích, và đi theo luồng AI đề xuất cộng người duyệt, không theo parser cấu trúc.

Cũng cần nối với **T414** (nhãn nối pháp / tham học) để dùng chung một bộ từ vựng.

### 5. Khoá đối chiếu mâu thuẫn với quy tắc chồng cây đã chốt

Kế hoạch dùng khoá `subject + relation_type + object`. DILA và Marcus chỉ có "thầy–trò" chung; T410 / T425 đã chốt gộp theo `(thầy, trò, chiều)`, còn loại quan hệ là thuộc tính. Nếu giữ `relation_type` trong khoá, gần như **mọi cạnh 禪燈世譜 sẽ rơi vào nhóm "khác loại"** so với DILA.

→ **Sửa:** đối chiếu 2 tầng.
- (a) Khoá lỏng `(thầy, trò)` để biết có trùng cặp không.
- (b) Sau đó mới so loại và chiều.

Báo cáo dùng nhóm "cùng cặp, nguồn kia không ghi loại" thay cho "khác loại".

### 6. Độc lập nguồn: ảnh hưởng trực tiếp tới quy tắc màu "≥ 2 nguồn khớp = đen"

禪燈世譜 (đời Minh, 道忞) được biên soạn từ 傳燈錄, 五燈會元… Hồ sơ người của DILA và Marcus cũng dựa trên các đăng lục này. Như vậy "trùng với DILA" **không phải** xác nhận độc lập.

→ **Bổ sung quy tắc:** khi tích hợp về sau, nguồn này **không được tính** vào số nguồn khớp của màu chồng cây cho tới khi có ghi chú phụ thuộc nguồn (`source-dependency-notes.md`) được Admin duyệt. Kế hoạch có nhắc "độc lập nguồn" nhưng chưa nối với quy tắc màu T410.

### 7. Tái sử dụng: kế hoạch có nguy cơ dựng "hệ thứ hai" song song

Giai đoạn 0 yêu cầu tái sử dụng, nhưng Giai đoạn 3 lại quy định sẵn 7 đối tượng mới. Dự án đã có:
- `entity_hub` + `entity_source_ids` (mapping người, có candidate / accepted);
- `lineage_edge_assertions` (cạnh theo nguồn);
- chuỗi T422 → T426 (thêm nguồn mới chỉ cần 1 dòng `data_sources`).

→ **Sửa:** vùng nghiên cứu vẫn dùng JSONL riêng (đúng nguyên tắc cách ly), nhưng Giai đoạn 3 phải kèm **bảng ánh xạ trường** sang các bảng hiện có:
- `relation_claim` → `lineage_edge_assertions(source_code='CBETA_X1601', relation_kind, source_edge_ref)`;
- `identity_mapping` → `entity_source_ids(source='CBETA_X1601', match_status)`.

Khi đó task tích hợp production sau này chỉ là nạp dữ liệu, không phải thiết kế lại.

### 8. Quyền: "non-commercial, giữ nguyên header"

→ Gói bàn giao và preview phải **kèm nguyên header**. Cần ghi rõ PTDA có dùng thương mại không. Nếu có thì không được phát hành trích văn của nguồn này. Kế hoạch có mục quyền, nhưng nên đưa điều kiện này thành **tiêu chí QA bắt buộc**.

### 9. Lỗi nhỏ về tổ chức

- **Số giai đoạn lệch:** kế hoạch có Giai đoạn 0–10 nhưng cây thư mục chỉ có `phase0 … phase7`. Cần thêm phase8–10, hoặc đổi tên theo đúng số giai đoạn.
- **Task ID:** số trống tiếp theo là **T428** (T427 đã dùng cho tab Place).
- **Bộ nhớ / luồng:** file chỉ 0,8 MB nên đọc theo luồng là tốt nhưng không bắt buộc. Rủi ro thực sự là `xml:id` và gaiji, không phải RAM.
- **Mục 3 nhắc nhiều agent:** dự án đang có agent `daoanh-debugger`, `daoanh-qa`, `tich-hop`. Nên ánh xạ 3 vai (khảo sát nguồn → `tich-hop`; code → `daoanh-debugger`; kiểm dữ liệu → `daoanh-qa`) thay vì tạo agent mới.
- **"Hai agent không dùng kết luận của nhau làm chứng cứ":** đúng. Nên bổ sung "QA phải tự mở `item/@xml:id` trong XML", để kiểm được bằng máy.

## Đề xuất bước tiếp theo

1. Admin duyệt 9 điểm trên, hoặc chọn điểm nào sửa.
2. RC tạo **T428** "Thiền Đăng Thế Phổ — Giai đoạn 0–2", dùng bản kế hoạch đã sửa, `dispatch: approved` (chỉ vùng `research/`, không ghi DB).
3. Giai đoạn 2 có thể đi nhanh, vì XML đã cho thấy cấu trúc list lồng nhau đủ để trích tự động phần lớn cạnh. Phần cần người đọc chỉ gồm các ca R04–R07.
