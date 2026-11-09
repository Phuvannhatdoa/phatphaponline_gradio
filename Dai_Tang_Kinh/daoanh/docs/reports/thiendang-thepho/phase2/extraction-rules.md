# T429 — Giai đoạn 2: Quy tắc trích xuất R01–R07 (extraction-rules)

TASK: T429 · PHASE: 2 (extraction-rules) · DATE: 2026-10-21 · STATUS: DONE (phạm vi GĐ2)
Mỗi quy tắc: **verdict + bằng chứng locator `item/@xml:id` thật** (đầu / giữa / cuối tác phẩm),
gồm cả ví dụ **KHÔNG được trích**. Fragment XML thật: `research/thiendang-thepho/sources/sample-source-fragments/`.

## R01 — Item ngang hàng có nhãn 第N祖 liên tục ⇒ tổ N truyền tổ N+1

**Verdict: CHỨNG MINH (PASS).**

- Sơ đồ 三十三祖世系圖: 33 tổ, nhãn đo được 1→33 **liên tục không khuyết**.
- Bằng chứng đầu: `itemX86p0321a0101` [第一祖] 摩訶迦葉 → `itemX86p0321a1001` [二祖] 阿難尊者.
- Giữa: `itemX86p0322a2501` [十七祖] 僧伽難提.
- Cuối: `itemX86p0324a0101` [三十三祖] 慧能.
- Điều kiện tạo cạnh: dãy số liên tục; **nếu khuyết một nhãn ⇒ dừng dãy tại đó**, không nối vòng qua chỗ khuyết.
- Lưu ý dạng nhãn: `第一祖` có 第, `二祖`…`三十三祖` không có — parser chấp nhận cả hai.
- Fragment: `r01_first_di_1zu_mohajiaye.xml`, `r01_middle_shiqizu.xml`, `r01_last_33zu_huineng.xml`.

## R02 — Item nhãn đời k nằm trong list con của item nhãn đời k−1 ⇒ cạnh thầy → trò

**Verdict: CHỨNG MINH (PASS).**

- Kiểm chéo toàn tác phẩm: 121 cặp (cha có nhãn, con có nhãn) — **121/121 khớp con = cha + 1, 0 lệch**;
  0 trường hợp cha có ≥2 con cùng nhãn k+1.
- Đầu: `itemX86p0325a0501` [一世] 二祖阿難 ⊃ `itemX86p0325a0601` [二世] 末田底迦 (諸祖旁出法派系圖).
- Giữa: `itemX86p0401a0501` [十六世] 虎丘紹隆 ⊃ `itemX86p0401a1001` [十七世] 天童曇華 (虎丘法派).
- Cuối (sơ đồ có nhãn cuối cùng): `itemX86p0462a0901` [五世] 洞山良价 ⊃ `itemX86p0462a1001` [六世] 曹山本寂 (曹洞宗).
- Ví dụ gốc chuẩn: `itemX86p0335a0501` [一世] 南獄懷讓 ⊃ `itemX86p0335a0601` [二世] 馬祖道一.
- **Không tạo cạnh khi nhãn lệch** (k ≠ k−1 + 1) ⇒ đưa `unresolved`. Đo được 0 lệch, nhưng quy tắc vẫn giữ để chống dữ liệu tương lai.
- Fragment: `r02_mazu_daoyi_2shi.xml`.

## R03 — Item ngang hàng KHÔNG nhãn cùng list con với item có nhãn ⇒ đồng môn cùng thầy

**Verdict: CHỨNG MINH (PASS) — nhưng cạnh chỉ mức candidate, phải kiểm mẫu rộng ở GĐ4–5.**

- Đo: 107 list con có cả item có nhãn lẫn không nhãn; 1.809 item không nhãn trong các list đó.
- Bằng chứng: `itemX86p0335a2801` [四世] 黃檗希運 ⊃ `itemX86p0335a3701` [五世] 臨濟義玄 (có nhãn)
  + 11 item không nhãn: 龍興尊宿 `itemX86p0335a4801`, 千頃楚南 `itemX86p0335a5601`, 烏石靈觀
  `itemX86p0335a5701`, … 丞相裴休 `itemX86p0336a0801`.
- **Ca khó bắt buộc người duyệt:** 丞相裴休 là quan lại tại gia theo nguồn ghi cùng cấp với đệ tử xuất gia —
  cấu trúc thuần tuý sẽ sinh cạnh 黃檗→裴休 loại `dharma_successor`, cần kiểm chéo vai (tiểu sử) trước khi chấp nhận.
- Fragment: `r03_huangbo_children.xml`.

## R04 — Item chỉ có văn tiểu sử, không tên đứng đầu ⇒ KHÔNG phải người, KHÔNG tạo cạnh

**Verdict: CHỨNG MINH (PASS — quy tắc loại trừ).**

- Đo (heuristic: không nhãn + (có `<p>` hoặc text đầu > 30 ký tự)): **122 item** kiểu này.
- Bằng chứng đầu: `itemX86p0321a0201` — con trực tiếp của `itemX86p0321a0101` 摩訶迦葉, text đầu =
  "摩竭陀國人，婆羅門氏。父飲澤…" (tiểu sử, không tên).
- Bằng chứng khác: `itemX86p0320a2101` (dưới 始祖 釋迦牟尼佛, có `<p>`), `itemX86p0321a1101`
  (dưới 二祖 阿難尊者 — "姓剎帝利，斛飯王子…").
- **Ví dụ KHÔNG được trích:** mọi item kiểu này phải bị loại khỏi danh sách người; nếu nhầm sẽ sinh
  cạnh "thầy → văn tiểu sử".
- Fragment: `r04_bio_only_under_mohajiaye.xml`.

## R05 — "派裔別見 / 法嗣別見" ⇒ chú thích chéo sang sơ đồ khác, KHÔNG tự nối

**Verdict: CHỨNG MINH (PASS — quy tắc dừng).**

- Đo: 18 chỗ "別見" (派裔別見 2 · 法嗣別見 8 · dạng khác 8).
- Bằng chứng: `itemX86p0324a0101` (慧能, tiểu sử 南嶽懷讓 kết thúc "輪派裔別見。"), `itemX86p0324a1701`
  (青原行思 — "派裔別見。"), `itemX86p0456a2101` ("法嗣別見。杏林"), `itemX86p0457a1901` ("法嗣別見之注").
- XML **không chứa liên kết đích** (chỉ chữ ghi chú) ⇒ ghi `cross_ref` chờ người duyệt; không tự nối cạnh.
- Fragment: `r05_huineng_paiyi_biejian.xml`.

## R06 — Nhãn đời mất chữ `□□世` ⇒ không dùng kiểm chéo; cạnh `proposed`

**Verdict: CHỨNG MINH (PASS — quy tắc dừng).**

- Đo: đúng **10** item, tập trung hết ở 2 sơ đồ cuối: 壽昌經 (5) + 雲門澄 (5).
- Bằng chứng: `itemX86p0472a1301` [□□世] 壽昌慧經, `itemX86p0472a1501` [□□世] 愽山元來,
  `itemX86p0472a2201` [□□世] 雲門圓澄; 7 item còn lại **mất cả tên** (name = "").
- Kết luận: 2 sơ đồ này XML không đủ thông tin ⇒ **cần đọc ảnh trang p0472**; không đoán.
- Fragment: `r06_missing_gen_label.xml`.

## R07 — Lớp `note type=orig/add/cf*` và `app/lem/rdg` ⇒ claim tách riêng theo lớp

**Verdict: CHỨNG MINH (PASS).**

- Đo: `app/lem/rdg` 107 bộ (witness `#wit.cbeta`【CB】 vs `#wit.orig`【卍續】); `note type=add` 107;
  `note type=orig` (foot text) 10; `cf1` 1; `cf2` 1.
- Bằng chứng đầu: app đầu tiên — lem 已 / rdg 巳 (wit.orig). Cuối: app index 106 — lem 第 / rdg rỗng.
- Quy tắc: văn bản trong `lem` = đọc theo 【CB】; `rdg` = dị văn 【卍續】; claim sinh từ vùng có app
  phải ghi lớp (base/variant) riêng, không trộn.
- Fragment: `r07_app_first.xml`, `r07_app_last.xml`.

## Quy tắc tách tên (đi kèm)

1. Tên = text đầu item, sau nhãn đời (note inline) và trước `<p>`/`<list>` đầu tiên; nối đoạn bị `<lb/>` cắt.
2. Nhãn đời nằm trong `<note place="inline">` — tách riêng khỏi tên.
3. Gaiji `<g ref="#CBxxxxx">`: giữ cả dạng gốc lẫn dạng chuẩn hoá theo `charDecl` (34 ký tự định nghĩa, 87 lần dùng).
4. Locator ổn định = `item/@xml:id` (div không có xml:id — định vị sơ đồ bằng head text + thứ tự).
5. Chữ sai của nguồn giữ nguyên văn (南獄懷讓) — chuẩn hoá chỉ ở lớp mapping (GĐ6).

## Cấu trúc phát hiện thêm (ngoài R01–R07) — cần quyết ở GĐ3

| Mã đề xuất | Cấu trúc | Bằng chứng | Xử lý |
|---|---|---|---|
| R08 (đề xuất) | Nhãn đời là **văn xuôi** trong note inline | `itemX86p0428a0301` 雪竇重顯 — "卍進本雪竇為四世，已下遞次準之。" | Không parse thành số; đời lấy từ tiêu đề div + note; cạnh chỉ `proposed` |
| R09 (đề xuất) | Sơ đồ **không nhãn nào**, đời nằm ở tiêu đề div | 大鑑下第十世 — `itemX86p0455a2301` 承天昭 ⊃ 11 đệ tử | Cạnh từ lồng nhau chỉ `proposed` |

## Kết luận chung

R01–R07 đều được chứng minh bằng locator thật (không bác bỏ quy tắc nào). Phần XML **không đủ**:
2 sơ đồ cuối (壽昌經, 雲門澄 — mất nhãn/tên) và các chú thích chéo 別見 (không có đích) ⇒ đề xuất
đọc ảnh trang p0472 và xử lý `cross_ref` bằng người duyệt. Không có cấu trúc nào bắt buộc phải đoán.
