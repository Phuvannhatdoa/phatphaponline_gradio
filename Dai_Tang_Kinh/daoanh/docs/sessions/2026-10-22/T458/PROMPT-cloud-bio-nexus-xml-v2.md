# Prompt chuẩn v2 — Cloud dịch file nexus đã trích sẵn (T458)

Khác v1: Cloud KHÔNG phải tải/parse TEI. Máy local đã trích sẵn (`scripts/t457_extract_bio_nexus.py`):
`data/dila_import/biographies.2024-01/nexus_src/<BOOK>.nexus.xml` — Admin tải file lên Cloud session.
Kết quả Cloud trả: `<BOOK>.vi.xml` → lưu `data/dila_import/biographies.2024-01/vn_bio_nexus/`.
Giấy phép: văn bản CBETA CC BY-NC-SA 4.0; PTDA phi thương mại (Admin xác nhận 2026-10-22).

---

```
NHIỆM VỤ
Tôi gửi file <BOOK>.nexus.xml: mỗi <nexus> là một "điểm sự kiện" trích từ Truyện Cao Tăng (CBETA, CC BY-NC-SA 4.0,
markup DILA). Hãy dịch sang tiếng Việt và trả về file <BOOK>.vi.xml. Đây là DỮ LIỆU SỰ KIỆN cho dòng thời gian
(ai – làm gì – ở đâu – năm nào), không phải bản dịch văn học. Không hỏi lại giữa chừng.

GIỮ NGUYÊN 100%: mọi phần tử và thuộc tính đã có (id, file, seq, from, to, <person>, <place>, <time>, <text_zh>),
cùng thứ tự. Chỉ THÊM vào mỗi <nexus>, ngay sau <text_zh>:
  <text_vi src="ai" status="unreviewed">…</text_vi>
  <summary_vi src="ai" status="unreviewed">…</summary_vi>
  <event_type>…</event_type>
  <note>…</note>   (chỉ khi có điều CỤ THỂ cần rà; không thì bỏ)
Đổi tên phần tử gốc thành <bio_nexus_vi …> (giữ mọi thuộc tính, thêm translator="cloud_session" status="unreviewed"
license="CC BY-NC-SA 4.0").

CÁCH DỊCH — tự đọc và VIẾT TAY theo nghĩa (script chỉ dùng để ghép và kiểm; KHÔNG dịch bằng bảng tra từng chữ)
1. text_vi: dịch nghĩa text_zh sang tiếng Việt hiện đại, trung thành, không thêm thông tin ngoài đoạn.
   Tên người/chùa/địa danh/niên hiệu/tên kinh giữ dạng Hán Việt (Cầu-na-bạt-đà, Trung Thiên Trúc, Kiến Khang, Nguyên Gia…).
   Thuật ngữ Phật học theo cách dùng phổ biến ở Việt Nam (thọ giới cụ túc, Tam tạng, Ngũ minh, quán đảnh, a-xà-lê…).
   Chú thích nhỏ trong ngoặc của nguyên văn (vd. "梁言功德賢也") dịch trong ngoặc tròn.
   Đoạn bắt đầu/kết thúc giữa câu: vẫn dịch đủ, phần cụt để trong […].
2. summary_vi: MỘT câu ≤ 30 từ: "<ai> <làm gì> <ở đâu> (<năm>)". Chỉ ghi năm nếu có <time> (dùng year_from–year_to).
   vd. "Cầu-na-bạt-đà, người Trung Thiên Trúc, thuở nhỏ học thông Ngũ minh, thiên văn, toán số."
3. event_type: 1 trong: birth · origin · ordination · study · teaching · translation · residence · travel ·
   imperial · meeting · miracle · writing · death · other.

CẤM: để trống text_vi/summary_vi; dùng "/" hay nhiều cách đọc; sửa/xóa bất kỳ ID, anchor, năm, text_zh;
bịa người/nơi/năm không có trong đoạn; note chung chung. Chữ không đọc được → giữ chữ Hán trong text_vi + <note>.

LÔ: mỗi lô 50 nexus theo thứ tự; xong lô nào kiểm lô đó; cuối cùng gộp đúng 1 file.
TỰ KIỂM: số <nexus> ra = vào; mọi thuộc tính và <text_zh> giống hệt file vào; 0 text_vi/summary_vi trống;
0 "/" trong text_vi/summary_vi; XML parse được (ElementTree). Thêm cuối file:
  <selfcheck in="N" out="N" text_vi_empty="0" summary_empty="0" slash="0"/>

ĐẦU RA: file <BOOK>.vi.xml để tải về (không chỉ dán trong chat) + 3 dòng báo cáo: số nexus, selfcheck, các note cần rà.
```
