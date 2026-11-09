# Prompt chuẩn v3 — Cloud dịch HÀNG LOẠT 48 file nexus (T458)

Đơn vị giao/nhận: **1 file vào = 1 file ra**, cùng tên (đổi `.nexus.xml` → `.vi.xml`).
- Sách nhỏ: 1 file/sách (Mingsengzhuanchao, OtherSources, biQiuNi, chuSanZangJiJi).
- Sách lớn: chia `<BOOK>.partNN` ~500 nexus, **không cắt đôi truyện** (Buxu 8, Jushi 2, Liang 4, Ming 2, Song 11, Tang 11, Xinxu 6).
- Tổng 48 file, 21.740 nexus. Gói tải lên: `data/dila_import/biographies.2024-01/nexus_src_parts.zip` (2,6 MB).
- Không chọn "từng truyện" (2.971 file — quá vụn) và không chọn "cả quyển 1 lần" (Tang 5.446 nexus — dễ bị cắt cụt, khó làm lại).
Kết quả: lưu `data/dila_import/biographies.2024-01/vn_bio_nexus/`. Giấy phép: CBETA CC BY-NC-SA 4.0 + DILA markup CC BY-SA → bản dịch CC BY-NC-SA 4.0.

---

```
NHIỆM VỤ
Tôi gửi nexus_src_parts.zip gồm 48 file <NAME>.nexus.xml. Mỗi <nexus> là một "điểm sự kiện" trích từ Truyện Cao Tăng
(văn bản CBETA, CC BY-NC-SA 4.0; markup DILA, CC BY-SA). Dịch sang tiếng Việt: MỖI file vào → MỘT file ra <NAME>.vi.xml.
Đây là DỮ LIỆU SỰ KIỆN cho dòng thời gian (ai – làm gì – ở đâu – năm nào), không phải bản dịch văn học.
Không hỏi lại giữa chừng (trừ điểm dừng PILOT).

THỨ TỰ: Mingsengzhuanchao (PILOT) → OtherSources → biQiuNi → chuSanZangJiJi → Ming_GSZ.part01..02 → Jushi_Zhuan.part01..02
→ Liang_GSZ.part01..04 → Xinxu_GSZ.part01..06 → Buxu_GSZ.part01..08 → Song_GSZ.part01..11 → Tang_GSZ.part01..11.

GIỮ NGUYÊN 100%: mọi phần tử và thuộc tính đã có (id, file, seq, from, to, <person>, <place>, <time>, <text_zh>), cùng
thứ tự. Đổi tên phần tử gốc <bio_nexus_src …> thành <bio_nexus_vi …> (giữ mọi thuộc tính, thêm
translator="cloud_session" status="unreviewed" license="CC BY-NC-SA 4.0"). Chỉ THÊM vào mỗi <nexus>, ngay sau <text_zh>:
  <text_vi src="ai" status="unreviewed">…</text_vi>
  <summary_vi src="ai" status="unreviewed">…</summary_vi>
  <event_type>…</event_type>
  <note>…</note>   (chỉ khi có điều CỤ THỂ cần rà; không thì bỏ)

CÁCH DỊCH — tự đọc và VIẾT TAY theo nghĩa (script chỉ để ghép và kiểm; KHÔNG dịch bằng bảng tra từng chữ)
1. text_vi: dịch nghĩa text_zh sang tiếng Việt hiện đại, trung thành, không thêm thông tin ngoài đoạn. Tên người/chùa/
   địa danh/niên hiệu/tên kinh giữ dạng Hán Việt (Cầu-na-bạt-đà, Trung Thiên Trúc, Kiến Khang, Nguyên Gia…). Thuật ngữ
   Phật học theo cách dùng phổ biến ở Việt Nam (thọ giới cụ túc, Tam tạng, Ngũ minh, quán đảnh, a-xà-lê…). Chú thích
   nhỏ của nguyên văn dịch trong ngoặc tròn. Đoạn bắt đầu/kết thúc giữa câu: vẫn dịch đủ, phần cụt để trong […].
2. summary_vi: MỘT câu ≤ 30 từ: "<ai> <làm gì> <ở đâu> (<năm>)". Chỉ ghi năm nếu có <time> (year_from–year_to).
3. event_type: 1 trong: birth · origin · ordination · study · teaching · translation · residence · travel · imperial ·
   meeting · miracle · writing · death · other.
Thống nhất tên riêng trong cùng một truyện và giữa các file (cùng chữ Hán → cùng âm Hán Việt).

CẤM: để trống text_vi/summary_vi; dùng "/" hay nhiều cách đọc; sửa/xóa bất kỳ ID, anchor, năm, text_zh; bịa người/
nơi/năm không có trong đoạn; note chung chung. Chữ không đọc được → giữ chữ Hán trong text_vi + <note>.

LÔ: trong mỗi file, dịch theo lô 50 nexus; xong lô nào kiểm lô đó; cuối cùng ghi đúng 1 file <NAME>.vi.xml.
TỰ KIỂM MỖI FILE (bắt buộc, trước khi sang file sau): số <nexus> ra = vào; mọi thuộc tính và <text_zh> giống hệt file
vào; 0 text_vi/summary_vi trống; 0 "/"; XML parse được. Cuối file thêm:
  <selfcheck in="N" out="N" text_vi_empty="0" summary_empty="0" slash="0"/>

PILOT — DỪNG ĐỂ KIỂM
Làm Mingsengzhuanchao.nexus.xml (188 nexus) rồi DỪNG: trả Mingsengzhuanchao.vi.xml + 3 dòng báo cáo. Chờ tôi nói
"tiếp tục" mới làm 47 file còn lại.

ĐẦU RA SAU MỖI ĐỢT
Nén các file .vi.xml ĐÃ ĐẠT thành vn_bio_nexus_<đợt>.zip để tải về + BATCH-REPORT.md (mỗi file 1 dòng: tên, in, out,
selfcheck, số note). Hết giới hạn phiên: trả ngay các file đã đạt + ghi file đang dở; khi tôi nói "tiếp tục" thì làm
tiếp từ file dở, không làm lại file đã đạt.
```
