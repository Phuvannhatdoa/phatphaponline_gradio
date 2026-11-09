# Prompt chuẩn — Cloud session dịch điểm sự kiện Cao Tăng Truyện, trả XML kiểu DILA Authority (T458)

Nguồn: https://github.com/DILA-edu/biographies (commit 4e82453, 2024-01-30). **Giấy phép: repo KHÔNG ghi rõ**
(README, header TEI đều không có) — nội dung gốc là văn bản CBETA (CC BY-SA), markup của DILA. Theo
docs/LICENSE_FIREWALL.md: được dịch để nghiên cứu nội bộ, nhưng trước khi hiển thị công khai phải Admin xác nhận
giấy phép (hỏi DILA hoặc ghi nhận CC BY-SA theo CBETA). Đánh dấu `legal_status=AUDITING`.

Kết quả lưu: `data/dila_import/biographies.2024-01/vn_bio_nexus/<BOOK>.vi.xml`
Coordinator kiểm: script QA của T457/T458 (đủ nexus, ID giữ nguyên, không trống, không "/").

Số đo (2026-10-22): 2.971 truyện · 21.882 điểm nexus · 1.127.924 chữ Hán trong đoạn nexus.

---

```
NHIỆM VỤ
Dịch các "điểm sự kiện" (nexus) trong bộ Truyện Cao Tăng của DILA sang tiếng Việt, trả về XML.
Đây là DỮ LIỆU SỰ KIỆN cho dòng thời gian (ai – làm gì – ở đâu – năm nào), không phải bản dịch văn học cả tác phẩm.
Làm theo các bước dưới, không hỏi lại giữa chừng (trừ điểm dừng PILOT).

NGUỒN
git clone https://github.com/DILA-edu/biographies  (nếu bị chặn mạng: dùng bản clone có sẵn, ghi commit vào header).
Mỗi file TEI XML là một truyện. Trong <body> có mốc dòng <lb ed="T" n="0712a24"/>. Cuối file có nhiều
<linkGrp>, mỗi cái = 1 điểm nexus:
  <link targets="#<anchor_from> #<anchor_to>"/>
  <ptr target="#A......" type="person"/>      (DILA Person ID, có thể nhiều)
  <ptr target="#PL............" type="place"/> (DILA Place ID, có thể nhiều)
  <ptr target="#j<JD_from 7 số><JD_to 7 số>" type="time"/>  (ngày Julian, có thể không có)

THỨ TỰ SÁCH (nhỏ trước): Mingsengzhuanchao, biQiuNi, chuSanZangJiJi, OtherSources, Ming_GSZ, Jushi_Zhuan,
Liang_GSZ, Xinxu_GSZ, Song_GSZ, Buxu_GSZ, Tang_GSZ. Bỏ qua thư mục bin, Schema.

TRÍCH ĐOẠN (script làm, không dịch)
- text_zh = nối văn bản các dòng từ anchor_from đến anchor_to (gồm cả 2 dòng biên), bỏ thẻ XML và bỏ <note>.
- name_zh của person/place = chữ trong <persName key="…">/<placeName key="…"> đầu tiên trùng ID trong truyện (nếu có).
- JD → năm dương lịch: dùng công thức chuyển JD chuẩn (Julian trước 1582-10-15, Gregorian sau). Ghi cả jd và year.

DỊCH (tự đọc và VIẾT TAY theo nghĩa — script chỉ để trích, ghép, kiểm; KHÔNG dịch bằng bảng tra từng chữ)
Mỗi nexus có 3 phần tiếng Việt:
1. text_vi: dịch nghĩa đoạn text_zh sang tiếng Việt hiện đại, trung thành, không thêm thông tin ngoài đoạn.
   Tên người/chùa/địa danh/niên hiệu/tên kinh giữ dạng Hán Việt (Bất Không, Kim Cương Trí, Lạc Dương, Khai Nguyên…).
   Thuật ngữ Phật học theo cách dùng phổ biến ở Việt Nam (thọ Bồ-tát giới, quán đảnh, Tam tạng, a-xà-lê…).
   Đoạn bắt đầu/kết thúc giữa câu: vẫn dịch đủ, phần cụt để trong ngoặc vuông […].
2. summary_vi: MỘT câu ≤ 30 từ tóm sự kiện chính, dạng "<ai> <làm gì> <ở đâu> (<năm>)".
   vd. "Năm 15 tuổi, Bất Không theo học Kim Cương Trí tại Đông Quốc (719–720)."
3. event_type: chọn 1 trong: birth · origin · ordination · study · teaching · translation · residence · travel ·
   imperial · meeting · miracle · writing · death · other.

CẤM: để trống text_vi/summary_vi; dùng "/" hay nhiều cách đọc; đổi bất kỳ ID, anchor, JD; bịa năm/nơi/người
không có trong đoạn; ghi note chung chung. Chữ không đọc được → giữ chữ Hán trong text_vi + <note>.

ĐỊNH DẠNG XML ĐẦU RA — 1 file cho mỗi sách: <BOOK>.vi.xml  (UTF-8)
<?xml version="1.0" encoding="UTF-8"?>
<bio_nexus_vi source="DILA-edu/biographies" commit="<sha>" book="<BOOK>" translator="cloud_session" status="unreviewed">
  <nexus id="<BOOK>/<file>.xml#<seq>" file="<BOOK>/<file>.xml" seq="<thứ tự linkGrp, bắt đầu 1>" from="<anchor_from>" to="<anchor_to>">
    <person id="A000095" name_zh="不空"/>
    <person id="A000774" name_zh="金剛智"/>
    <place id="PL000000000083" name_zh="東國"/>
    <time jd_from="1983698" jd_to="1984080" year_from="719" year_to="720"/>
    <text_zh>…</text_zh>
    <text_vi src="ai" status="unreviewed">…</text_vi>
    <summary_vi src="ai" status="unreviewed">…</summary_vi>
    <event_type>study</event_type>
    <note>(chỉ khi có điều cụ thể cần rà)</note>
  </nexus>
  …
  <selfcheck in="N" out="N" text_vi_empty="0" summary_empty="0" slash="0"/>
</bio_nexus_vi>
Không có time → bỏ thẻ <time>. Escape &, <, > đúng chuẩn XML. File phải parse được (xmllint/ElementTree).

CHIA LÔ: mỗi lô 50 nexus theo thứ tự file → seq; dịch xong lô nào kiểm lô đó; hết sách → gộp 1 file <BOOK>.vi.xml.
TỰ KIỂM MỖI SÁCH: số nexus ra = số <linkGrp> trong nguồn; mọi ID/anchor/JD khớp nguồn; 0 trống; 0 "/"; XML hợp lệ.

PILOT — DỪNG ĐỂ KIỂM
Làm sách Mingsengzhuanchao (37 truyện, 188 nexus, ~9.800 chữ) rồi DỪNG: trả Mingsengzhuanchao.vi.xml +
BATCH-REPORT.md (số nexus, số lô, selfcheck, thời gian, ước token). Chờ tôi nói "tiếp tục".

ĐẦU RA CUỐI
11 file <BOOK>.vi.xml trong thư mục vn_bio_nexus/, nén vn_bio_nexus.zip + BATCH-REPORT.md (mỗi sách 1 dòng:
truyện, nexus vào/ra, có năm, lô, selfcheck, notes). Hết giới hạn phiên: trả ngay các sách đã đạt + ghi chỗ dở;
khi tôi nói "tiếp tục" thì làm tiếp từ chỗ dở.
```
