# Báo cáo trạng thái tab "🗺️ Place" (namevimap.html) — T427

Sinh tự động bởi `scripts/build_place_vi_map_report.py` lúc 2026-10-20 07:36. Chỉ đọc DB, không ghi.

## Tổng quan

- Danh sách gốc: `places_dila` — **59,167 địa danh** (ID dài `PL` + 12 số).
- Địa danh chưa có dòng `namevi_map_places` (ID dài) nào: **17** (0.0%) — cột "name_vi hiện tại" hiện "—".

## Số liệu theo 6 bộ lọc (tab Place)

| Bộ lọc | Số dòng | % trên tổng |
|---|---:|---:|
| 📋 Tất cả | 59,167 | 100.0% |
| ✅ Pass 100% | 0 | 0.0% |
| 🟡 Cần duyệt | 59,164 | 100.0% |
| ⬜ Thiếu Claude | 59,167 | 100.0% |
| ⬜ Thiếu Gemini | 59,167 | 100.0% |
| ⬜ Thiếu TTL | 59,167 | 100.0% |

**Ghi chú luật Pass 100%:** giai đoạn 1 chưa có cột Claude/Gemini cho địa danh
(chưa có bảng `ai_place_name` / `codex_place_name`) nên **không dòng nào có thể đạt
Pass 100%** cho tới khi chạy AI phiên âm 59K địa danh (giai đoạn 2, ngoài phạm vi T427).

**Ghi chú cột TTL:** `vn_person_places` chỉ có 46 địa danh (slug TTL, chưa map DILA
Place ID) nên gần như mọi dòng đều "Thiếu TTL" — đây là tình trạng dữ liệu thật,
không phải lỗi API.

## Lỗi dữ liệu phát hiện khi quét (biết, KHÔNG tự sửa trong T427 giai đoạn 1)

### Lỗi mã hoá (mojibake — name_vi chứa ký tự `?` không phải dấu hỏi thật)

- Trên bản ID dài (dùng cho tab Place): **17** dòng.
- Trên toàn bộ `namevi_map_places` (ID ngắn + ID dài): **38** dòng.

| dila_id (dài) | name_vi (lỗi) |
|---|---|
| `PL000000002937` | Kim ? Truân |
| `PL000000005141` | Cho ? Bảo |
| `PL000000011293` | Linh Thạch ? |
| `PL000000016568` | Khuyết ? Tập |
| `PL000000022156` | Ván ? Doanh |
| `PL000000032492` | Thạch Khẩu ? |
| `PL000000032609` | Đại ? |
| `PL000000038415` | Duyên Hà ? Khê Ty |
| `PL000000039595` | Đại ? Thống |
| `PL000000039913` | Đại ? Ma |
| `PL000000039914` | Tiểu ? Thống |
| `PL000000045920` | Mộc ? Trấn |
| `PL000000048727` | Đại Tuyên ? |
| `PL000000048786` | Đại ? Dưỡng |
| `PL000000049594` | ( ? Thê ) Gắt Nhãi To Đặc Y |
| `PL000000053670` | Đại Vũ ? |
| `PL000000000314` | Th? S?t H?i |

### Cặp lệch name_vi giữa bản ID ngắn và bản ID dài (cùng `name_zh`)

- Tổng: **34,708** cặp (đối chiếu theo `name_zh` trùng khớp giữa 1 dòng ID
  ngắn và 1 dòng ID dài trong `namevi_map_places` — không phải đối chiếu theo số ID,
  vì 2 hệ ID ngắn/dài được đánh số độc lập, không suy ra nhau bằng phép toán chuỗi).
- Admin RC (2026-10-19) từng ghi nhận ước tính "8.440 cặp lệch" bằng phương pháp khác;
  số liệu ở đây đo lại bằng SQL join theo `name_zh` nên có thể khác do trùng tên
  (nhiều địa danh có cùng `name_zh` nhưng là 2 nơi khác nhau). Không dọn dữ liệu
  trong task này — chỉ ghi nhận để Admin quyết định có cần ETL đối soát riêng không.

| ID dài | ID ngắn | Hán tự | name_vi (dài) | name_vi (ngắn) |
|---|---|---|---|---|
| `PL000000000002` | `PL000002` | 興都庫什山 | Thiếc Nhã Kha Sơn | Hưng Đô Kho Thập Sơn |
| `PL000000000006` | `PL000004` | 厭怛國 | Ấp Đắn Quốc | Yếm Đắn Quốc |
| `PL000000000006` | `PL000006` | 厭怛國 | Ấp Đắn Quốc | Yếm Đắn Quốc |
| `PL000000000008` | `PL000008` | 縛喝國 | Lam Thị | Phược Hát Quốc |
| `PL000000000012` | `PL000012` | 忽懍國 | Phất Lâm | Hốt Lẫm Quốc |
| `PL000000000014` | `PL000014` | 土火羅 | Đâu Lắc | Thổ Hoả La |
| `PL000000000018` | `PL000018` | 梵衍那國 | Phạm Dương Quốc | Phạm Diễn Na Quốc |
| `PL000000000023` | `PL000023` | 屈浪拏國 | Câu Lạn Na | Khuất Lãng Noa Quốc |
| `PL000000000024` | `PL000024` | 波多叉拏 | Bát Đạc Sáng Na Quốc | Ba Đa Xoa Noa |
| `PL000000000025` | `PL000025` | 達摩悉鐵帝國 | Đạt Ma Thiết Tạt Đấy Quốc | Đạt Ma Tạt Thiết Đấy Quốc |
| `PL000000000033` | `PL000033` | 婆羅犀那大嶺 | Bà La Tê La | Bà La Tê Na Đại Lĩnh |
| `PL000000000035` | `PL000035` | 謝䫻國 | Tạ Việt Quốc | Tạ 䫻 Quốc |
| `PL000000000038` | `PL000038` | 提謂城 | Li Vị | Đề Vị Thành |
| `PL000000000038` | `PL049293` | 提謂城 | Li Vị | Đề Vị Thành |
| `PL000000000043` | `PL000037` | 瞢健國 | Măng Chương | Măng Kiện Quốc |
| `PL000000000043` | `PL000043` | 瞢健國 | Măng Chương | Măng Kiện Quốc |
| `PL000000000044` | `PL000044` | 活國 | A Hoãn Thành | Hoạt Quốc |
| `PL000000000050` | `PL000050` | 濫波國 | La La Châu Lạm Kiền Thành | Lạm Ba Quốc |
| `PL000000000052` | `PL000052` | 那揭羅曷國 | Na Yết La Hát Quốc | Na Yết La Hạt Quốc |
| `PL000000000053` | `PL000053` | 那呵利城 | Na Ha Lê Thành | Na Ha Lợi Thành |

---
_Script: `scripts/build_place_vi_map_report.py` — chạy lại bất cứ lúc nào để cập nhật số liệu._
