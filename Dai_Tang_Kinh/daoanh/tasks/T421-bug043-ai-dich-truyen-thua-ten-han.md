---
id: T421
title: "BUG-043: AI Dịch không dịch tên Hán trong mục TRUYỀN THỪA (SƯ PHỤ/ĐỆ TỬ)"
status: done
created: 2026-10-19
updated: 2026-10-20
done_when: "Tại focus=A009447, click AI Dịch -> SƯ PHỤ (無學) và cả 14 ĐỆ TỬ hiện tên Việt kèm tên Hán phụ; tiểu sử vẫn dịch bình thường; không ghi DB; QA xác nhận bằng screenshot + network log."
---

## Triệu chứng

Route: `/daoanh/places?mode=lineage&focus=A009447&lm=tree`

Click "🌐 AI Dịch" chỉ dịch phần tiểu sử (biography). Tên Hán trong mục TRUYỀN THỪA
không được dịch:
- SƯ PHỤ: 無學
- ĐỆ TỬ (14): 招福, 思明, 巖俊, 敬慧, 二世, 龍福, 谷隱, 遵古, 天福, 澄照, 微, 感溫, 九嵕, 璨幽

## Nguyên nhân nghi ngờ

Handler click "AI Dịch" trong `places.html` (root, ~11600+ dòng) chỉ gửi/đổi text
tiểu sử tới endpoint dịch Gemini trong `app.py`, không thu thập node tên Hán từ
DOM mục TRUYỀN THỪA (SƯ PHỤ/ĐỆ TỬ) để gửi kèm hoặc gửi request riêng.

## Phạm vi dự kiến (UI-only, KHÔNG ghi DB)

1. Thu thập tên Hán chưa có tên Việt từ DOM mục TRUYỀN THỪA (SƯ PHỤ + ĐỆ TỬ) khi
   click "AI Dịch". Nếu node đã có `data-name-vi`/tên Việt sẵn (DILA/ZQLOCAL) thì
   dùng ngay, không gọi AI.
2. Gửi danh sách tên Hán cần dịch tới Gemini (gộp cùng request dịch tiểu sử hoặc
   endpoint riêng, ví dụ `/daoanh/api/translate_names`) với prompt phiên âm
   Hán-Việt Phật giáo/Thiền Tông, trả JSON `{ "漢字": "Tên Việt", ... }`.
3. Cập nhật DOM: hiển thị "Tên Việt (Hán tự)" — tên Việt nổi bật, tên Hán phụ nhỏ.
   Cache kết quả trong state JS (`_lineageState` hoặc biến cục bộ), không ghi DB.
4. Loading state khi đang dịch; lỗi → giữ nguyên tên Hán gốc + toast lỗi nhẹ.
5. Không đổi IDs, badge nguồn (DILA/MARCUS/CBETA), evidence links.

## File dự kiến thay đổi

- `daoanh/places.html` (root)
- `daoanh/app.py` (nếu cần endpoint dịch tên riêng)

## Backup

`daoanh/docs/sessions/2026-10-19/BUG-043/` — backup trước khi sửa.

## Test bắt buộc

- `focus=A009447`: SƯ PHỤ + 14 ĐỆ TỬ hiện tên Việt sau khi click AI Dịch.
- Regression: dịch tiểu sử vẫn hoạt động bình thường.
- Network log: request dịch tên trả 200 OK.
