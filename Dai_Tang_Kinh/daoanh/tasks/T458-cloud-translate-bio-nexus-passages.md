---
id: T458
title: Cloud session dịch đoạn văn sự kiện (nexus) Cao Tăng Truyện sang Việt → lớp dịch cho dila_bio_nexus
status: pending
prompt: docs/sessions/2026-10-23/T458/PROMPT-cloud-bio-nexus-batch-v3.md
created: 2026-10-22
updated: 2026-10-22
owner: coordinator
module: Data / Biographies / Translation
priority: medium
parent: T453
depends_on: [T457]
plan_approved_at: "2026-10-22 (Admin phê chuẩn đề xuất deepsearch). Chi phí token Cloud: pilot trước, duyệt từng đợt."
done_when: >
  (1) Xuất từ dila_bio_nexus (T457) các đoạn văn theo sách → <BOOK>.nexus.json (khóa = nexus id, giữ person/place/time ID).
  (2) Prompt chuẩn (kế thừa v4 T453): dịch nghĩa ngắn gọn từng đoạn sang tiếng Việt, giữ tên riêng theo Hán Việt,
      KHÔNG thêm thông tin; trường *_src/*_status="unreviewed"; SELF-CHECK; chia lô 50; PILOT 1 sách nhỏ (名僧傳抄 37 truyện)
      → QA local → Admin duyệt → các sách còn lại.
  (3) QA script: đủ khóa, không trống, không còn chữ Hán thừa ngoài tên riêng, ID giữ nguyên.
  (4) Import additive (cột/bảng lớp Việt), tên người hiển thị theo people.name_vi (DB thắng).
  (5) Mỗi đoạn hiển thị kèm trích dẫn CBETA (sách, quyển, anchor dòng) và nhãn "Bản dịch AI · chưa duyệt".
  (6) daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  DROP bảng/cột lớp Việt của T458 (additive).
---

# T458 — Dịch đoạn sự kiện Cao Tăng Truyện bằng Cloud

## Vì sao dịch lại bằng AI khi đã có bản Việt lưu hành? (Admin hỏi 2026-10-22)
- Bản Việt đang lưu hành là **tác phẩm có bản quyền của dịch giả/nhà xuất bản** — PTDA không được chép vào DB khi
  chưa có giấy phép (docs/LICENSE_FIREWALL.md: "PUBLIC ≠ FREE").
- Dịch từ **nguồn Hán CBETA** bằng AI ⇒ bản dịch phái sinh hợp lệ theo **CC BY-NC-SA 4.0** (đính chính 2026-10-22: CBETA là BY-**NC**-SA, không phải BY-SA): phải ghi công CBETA + thông tin phiên bản, **phi thương mại**, bản phái sinh phát hành cùng giấy phép. **Admin xác nhận PTDA phi thương mại (không quảng cáo, không thu phí, không bán dữ liệu) — 2026-10-22.**
- Chỉ dịch **đoạn sự kiện ngắn** (nexus, vài câu/đoạn) làm dữ liệu cấu trúc cho dòng thời gian — **không** dịch lại toàn bộ tác phẩm.
- Bản Việt đã xuất bản có thể **dẫn tham khảo** (tên sách, dịch giả, trang) cạnh đoạn AI, không chép nội dung.

## Khối lượng (đo 2026-10-22)
2.971 truyện · **21.882 điểm nexus** · **1.127.924 chữ Hán** trong đoạn nexus (toàn văn 1.539.778).
Theo sách (chữ nexus): Tang 333.791 · Buxu 217.717 · Song 207.225 · Xinxu 146.243 · Liang 91.038 · Jushi 42.422 ·
chuSanZangJiJi 29.780 · Ming 27.888 · biQiuNi 16.001 · Mingsengzhuanchao 9.769 · OtherSources 6.050.

## Chi phí ước (giá API Anthropic, 2026-10)
Haiku 5.5 ($0,10/$0,50 per MTok): đoạn nexus ~$3–4 (batch ~$1,5–2); toàn văn ~$4–5. Sonnet 5.5 ≈ ×20.
Đợt Cloud session (free credit) không tính theo bảng này. Pilot đo token thật trước khi chạy hết.

## Prompt chuẩn (Admin duyệt 2026-10-22)
`docs/sessions/2026-10-22/T458/PROMPT-cloud-bio-nexus-xml.md` — Cloud tự clone repo, trích đoạn, dịch viết tay theo nghĩa,
trả **XML kiểu DILA Authority** `<BOOK>.vi.xml` (nexus: person/place ID, time JD+năm, text_zh, text_vi, summary_vi,
event_type), PILOT Mingsengzhuanchao (188 nexus) rồi dừng.

## Giấy phép (cập nhật 2026-10-22)
- Văn bản gốc: CBETA — **CC BY-NC-SA 4.0** (https://cbeta.org/copyright), trừ ngoại lệ là trước tác hiện đại
  (印順法師佛學著作集, 太虛大師全書, 呂澂佛學著作集…) — Cao Tăng Truyện không thuộc ngoại lệ.
- Markup DILA biographies: CC BY-SA (trang chính thức DILA, xem dưới) → ghi công DILA.
- Admin xác nhận **PTDA phi thương mại** (2026-10-22) ⇒ được dịch + hiển thị, kèm: ghi công "CBETA, phiên bản …",
  "DILA biographies commit 4e82453", nhãn giấy phép CC BY-NC-SA 4.0 trên UI và trong file xuất.
- ĐÃ SỬA 2026-10-23 (Admin duyệt): `data_sources` CBETA → `CC BY-NC-SA 4.0` (noncommercial=1, sharealike=1); ROLLBACK có ghi.

## Nguồn đã trích sẵn (T457, 2026-10-22)
`scripts/t457_extract_bio_nexus.py` → `data/dila_import/biographies.2024-01/nexus_src/<BOOK>.nexus.xml` (11 sách,
**21.740 nexus**; 142 nexus bỏ qua vì anchor trong nguồn DILA bị lỗi gõ, liệt kê khi chạy script). Snapshot repo:
`data/dila_import/biographies.2024-01/biographies-4e82453.tar.gz` + `SHA256SUMS.txt`.
Pilot: `Mingsengzhuanchao.nexus.xml` — 188 nexus, 26 có năm, 0 lỗi. Cloud chỉ cần dịch file này (không phải parse TEI).

## Ví dụ thật (Song_GSZ/0746shiBuKong.xml, truyện Bất Không)
- nexus 0712a26–a29: A000095 Bất Không + A000774 Kim Cương Trí · PL000000000083 Đông Quốc · JD → 719–720 ·
  "年十五，師事金剛智三藏…與受菩薩戒，引入金剛界大曼荼羅"
- nexus 0712b09–b10: … Lạc Dương · 741–742 · "厥後師往洛陽，隨侍之際，遇其示滅，即開元二十年矣"
- nexus 0712b11–b13: A008787 Lưu Cự Lân · Chế Chỉ Tự (Pháp Tính Tự) · 741–742 · "初至南海郡，採訪使劉巨隣懇請灌頂…"
- Lưu ý: people.name_vi của A000095 đang là "Amoghavajra" (ZQ) → thuộc T455.

- 2026-10-22 (Admin cung cấp): trang chính thức http://buddhistinformatics.dila.edu.tw/biographies/ ghi dữ liệu TEI/XML
  "published under a CC (Attribution Share-Alike) License" ⇒ markup DILA = CC BY-SA; văn bản CBETA = CC BY-NC-SA 4.0
  ⇒ bản phái sinh theo điều kiện chặt hơn: **CC BY-NC-SA 4.0** (PTDA phi thương mại — Admin xác nhận). Bỏ trạng thái AUDITING.
  Gói 名僧傳抄 trên trang DILA (2018-12-06, 37 file, 188 linkGrp) trùng số lượng với bản GitHub commit 4e82453 (2024) → dùng bản GitHub (mới hơn).

## 2026-10-23
- Admin hỏi giao Cloud "từng truyện" hay "cả quyển": chốt **1 file vào = 1 file ra**, sách lớn chia ~500 nexus không cắt
  đôi truyện → **48 file** (`data/dila_import/biographies.2024-01/nexus_src_parts/`, zip `nexus_src_parts.zip` 2,6 MB),
  tổng 21.740 nexus. Script: `t457_extract_bio_nexus.py --part-size 500`. Prompt v3 batch:
  `docs/sessions/2026-10-23/T458/PROMPT-cloud-bio-nexus-batch-v3.md` (PILOT Mingsengzhuanchao rồi dừng).
