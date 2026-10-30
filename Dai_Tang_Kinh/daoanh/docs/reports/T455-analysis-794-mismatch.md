# T455 — Phân tích 794 dòng `name_vi` lệch (bằng chứng để Admin quyết)

> Ngày: 2026-10-30 · HEAD khi đo: `0b938587` · **CHƯA ghi DB** (0 UPDATE)
> Bằng chứng thô: `docs/sessions/2026-10-28-t455/name_vi_mismatch_{A,B,C}.csv`
> Script: `scripts/classify_t455.py` (phân loại) · `scripts/t455_charmap_check.py` (đối chiếu charmap) · `scripts/t455_diff_analysis.py` (đo khác biệt)

---

## 1. Vấn đề là gì (nói ngắn)

Bảng `people` có cột `name_vi` = tên tiếng Việt của nhà sư. Hiện cột này được điền bởi **ZQ** — một máy phiên âm tự động chữ Hán sang Việt (confidence 0,5, theo `CLAUDE.md`).

So sánh `name_vi` (ZQ) với bản dịch Cloud của chính file kinh lục DILA, **794 người không khớp**. Nhưng 794 dòng **không phải cùng một loại lỗi** — và đó mới là điểm cần quyết.

## 2. Ba lô khác nhau về bản chất

| Lô | Số dòng | Tỉ lệ | Bản chất vấn đề | Hán còn sót | Có thể tự quyết? |
|---|---|---|---|---|---|
| **A** | 24 | 3 % | ZQ **hỏng nặng**: để tên Anh, hoặc để nguyên chữ Hán hiến | **17/24** | ✅ Có (tra từ điển) |
| **B** | 534 | 67 % | ZQ & Cloud **khác cách đọc cả từ** (ví dụ `Bát Nhã` vs `Bàn Nhược`) | 0/534 | ⚠️ **Không** — cần người |
| **C** | 236 | 30 % | ZQ **thiếu/sai 1 chữ**, hay thiếu tiền tố tôn kính `釋` (Thích) | 0/236 | ✅ Có (bằng chứng máy) |

### Lô A — 24 dòng: ZQ hỏng rõ ràng (không có bàn cãi)
```
A000095   不空      ZQ="Amoghavajra"   Cloud="Bất Không"     x183   ← để tên Anh
A010057   函昰      ZQ="Hàm 昰"        Cloud="Hàm Thị"        x4     ← còn chữ 昰
A001310   焦竑      ZQ="Tiêu 竑"       Cloud="Tiêu Hoành"     x4     ← còn chữ 竑
A000903   夏丏尊    ZQ="Hạ 丏 Tôn"     Cloud="Hạ Miện Tôn"    x1     ← còn chữ 丏
A001316   阿質達霰  ZQ="A Chất Đạt 霰" Cloud="A-chất-đạt-tản"  x3     ← còn chữ 霰
```
→ **Nguyên nhân**: các chữ hiến (`昰 竑 玘 霰 丏 讕`) **không có** trong bảng đọc Hán-Việt của dự án (`hanviet_char_map` 11.300 chữ) → ZQ không biết đọc → để nguyên chữ Hán lộ ra UI.
→ **Cách sửa**: tra từ điển, viết tay 24 dòng. Không cần máy.

### Lô B — 534 dòng: KHÔNG phải lỗi kỹ thuật, mà là khác quy ước đặt tên
```
A001482   龍樹      ZQ="Long Thụ"      Cloud="Long Thọ"        x24   ← 樹 trong tên đọc "Thọ"
A001342   善無畏    ZQ="Thiện Vô Uý"   Cloud="Thiện Vô Úy"     x26   ← 畏 đọc "Úy"
A001318   無著      ZQ="Vô Trứ"        Cloud="Vô Trước"        x14   ← 著 đọc "Trước"
A000996   般若流支  ZQ="Bàn Nhược Lưu Chi" Cloud="Bát-nhã Lưu-chi" x16 ← 般若 đọc "Bát Nhã"
A001583   鳩摩羅什  ZQ="Cưu Ma La Thập" Cloud="Cưu-ma-la-thập"   x54   ← chỉ khác dấu gạch nối
```
Đo được: **478/534 dòng khác nhau ≤ 1 từ** (sai 1 chữ âm đọc); **64/534** chỉ khác dấu gạch nối; **0/534** còn sót Hán.

**Đây không phải "sai", mà là 2 hệ quy ước:**
- **ZQ** đọc *theo nghĩa chữ* (樹 = cây → "thụ"; 著 = trứ; 般若 = "Bàn Nhược")
- **Cloud** đọc *theo cách gọi quen thuộc trong kinh lục Việt Nam* (Long Thọ, Bát Nhã, Cưu Ma La Thập)

**Vì sao không tự động quyết được?** Bảng `hanviet_char_map` là đọc **một chữ theo nghĩa thông thường**, không có ngoại lệ theo cả từ. Kiểm chứng:

| Chữ | charmap đọc | Đọc đúng trong tên Phật | Ai đúng? |
|---|---|---|---|
| 樹 | `thụ` | Long **Thọ** | Cloud |
| 畏 | `uý` | Thiện Vô **Úy** | Cloud |
| 著 | `trứ` | Vô **Trước** | Cloud |
| 頂 | `đỉnh` | Quán **Đảnh** | Cloud |
| 般若 | `bàn`/`Nhược` | **Bát Nhã** | Cloud |
| 錩 | `xuổng` | Phương Quảng **Cẩn** | Cloud |
| 閻 | `Diêm` | **Xà-na** Quật-đa | Cloud |

Charmap nghiêng về Cloud **314/534**, về ZQ **269/534**, hòa **113/534** → **không phân định được**, vì lỗi nằm ở tầng "đọc cả từ", không phải tầng "đọc chữ".

Chỉ **552/11.300 chữ (4,9 %)** là đa âm — nhưng chính các chữ đa âm này lại nằm trong tên.

### Lô C — 236 dòng: ZQ thiếu hoặc sai 1 chữ (có thể quyết bằng máy)
```
A001113   釋淨源    ZQ="Tịnh Nguồn"    Cloud="Thích Tịnh Nguyên"  x14  ← thiếu 釋 (Thích)
A000008   釋一行    ZQ="Nhất Hàng"     Cloud="Thích Nhất Hành"    x13  ← thiếu 釋 + sai Hàng/Hành
A004819   釋太虛    ZQ="Thái Hư"       Cloud="Thích Thái Hư"      x20  ← thiếu 釋
A001301   智顗      ZQ="Trí Ỷ"         Cloud="Trí Khải"           x45  ← 顗 đọc Khải
A001394   袾宏      ZQ="Vân Thê Châu Hoằng" Cloud="Chu Hoằng"     x25  ← dư chữ
```
Đối chiếu charmap (bảng chuẩn của dự án): **nghiêng về Cloud 188/236 (80 %)**, về ZQ 14, hòa 36.
→ Lý do nghiêng: charmap có `釋 → Thích` (tiền tố tôn kính) đúng, và nhiều chữ đọc đúng.

## 3. Câu hỏi thật cần Admin quyết

> **"Tên người trong Đạo Ảnh nên theo quy ước nào?"**
> Đây là quyết định **chính sách**, không phải quyết định sửa 794 dòng. Mọi lựa chọn dưới đây đều để lại giá trị cũ trong bảng lịch sử (additive).

### Phương án (A) — Sửa 260 dòng có bằng chứng rõ, giữ 534 dòng lô B
- Sửa: **lô A (24)** + **lô C (236)** = **260 dòng**
- Giữ nguyên lô B (534), ghi vào bảng lịch sử là "alias — đã đối chiếu, giữ theo ZQ"
- ✅ Ít xâm lấn nhất · có bằng chứng máy cho lô C · **không** cần người duyệt 534 dòng
- ❌ Lô B vẫn hiển thị "Long Thụ" (không phải "Long Thọ") — 24 lần xuất hiện cho riêng người này

### Phương án (B) — Sửa cả 794 theo Cloud
- ✅ Đồng bộ toàn bộ, tên khớp cách gọi phổ biến trong kinh lục VN
- ❌ Cloud cũng có lỗi riêng: `實叉難陀` → Cloud "Thật-xoa-nan-đà" (đúng ra **Thực** Xoa Nan Đà); `般若` → "Bát-nhã" là dạng viết tắt; và Cloud là bản dịch **unreviewed**
- ❌ Xâm lấn lớn: 534 tên đang được hiển thị sẽ đổi hết

### Phương án (C) — Sửa lô A + C theo Cloud, lô B tra từ điển theo lô
- Chia lô B thành 3 nhóm theo `so_lan` (xuất hiện nhiều trong kinh lục → ưu tiên)
- Ưu tiên ~50 người xuất hiện ≥ 20 lần (chiếm phần lớn lượt hiển thị)
- ✅ Chính xác nhất · ✅ Ưu tiên tác động thấy
- ❌ Cần thời gian + người duyệt, làm chậm T456

## 4. Quy tắc bắt buộc (không đổi được)

| Quy tắc | Nguồn |
|---|---|
| Tên Việt luôn `source_id = 5` (ZQLOCAL) — **không** gán tên Việt cho nguồn DILA (`source_id = 1`) | `CLAUDE.md` |
| **Không** sửa `people.name_zh` (chữ Hán gốc) | task T455 |
| Giữ giá trị cũ ở bảng lịch sử (additive), có backup + dòng `ROLLBACK.md` | task T455 |
| Tên Cloud chỉ **tham khảo**, không tự ghi đè (quyết định Admin 2026-10-22) | task T455 |

## 5. Đề xuất của tôi

**Phương án (A)** — sửa 260 dòng (lô A 24 + lô C 236), giữ 534 dòng lô B và ghi chú alias.
Lý do: đây là phần có bằng chứng khách quan (charmap 188/236 cho lô C; 17 dòng lô A hỏng rõ), rủi ro thấp, và **không** đụng vào 534 cách đặt tên đã có chủ đích. Lô B có thể mở task riêng (`T4xx — tra từ điển 534 tên theo lô so_lan`) để làm dần mà không chặn T456.

## 6. Lệnh kiểm tra lại

```bash
# phân loại lại từ CSV gốc
python -X utf8 scripts/classify_t455.py

# đo khác biệt từng lô
python -X utf8 scripts/t455_diff_analysis.py

# đối chiếu với bảng đọc Hán-Việt chuẩn của dự án
python -X utf8 scripts/t455_charmap_check.py

# ví dụ thật từng lô (xếp theo số lần xuất hiện)
python -X utf8 scripts/t455_examples.py

# đọc chữ đa âm trong charmap
python -X utf8 scripts/t455_polyphonic_check.py
```
