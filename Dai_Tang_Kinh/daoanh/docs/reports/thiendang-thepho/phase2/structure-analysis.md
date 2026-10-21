# T429 — Giai đoạn 2: Phân tích cấu trúc sơ đồ (structure-analysis)

TASK: T429 · PHASE: 2 (structure-analysis) · DATE: 2026-10-21 · STATUS: DONE (phạm vi GĐ2)
Dữ liệu đo: `research/thiendang-thepho/derived/structure-inventory.json` (sinh bởi `scripts/thiendang_thepho/analyze_structure.py`, chỉ đọc XML nguồn).

## 1. Bức tranh chung

禪燈世譜 mã hoá phả hệ bằng **list/item lồng nhau** (TEI), không có bảng (`<table>` = 0).
Toàn file: `list` 1.147 · `item` 5.876 · `p` 187 · `note` 449 · `lb` 13.282 · `g` (gaiji) 87 ·
`app/lem/rdg` 107/107/107 · `cb:div` 22 · `milestone unit="juan"` 9.

## 2. 17 sơ đồ (`cb:div type="other"`) — inventory

| # | Sơ đồ (head) | Quyển | lists | items | depth item lồng |
|---|---|---|---|---|---|
| 1 | 三十三祖世系圖 | 1 | 37 | 72 | 3 |
| 2 | 諸祖旁出法派系圖 | 1 | 92 | 349 | **9** |
| 3 | 南嶽法派世系圖 | 2 | 89 | 613 | 7 |
| 4 | 南嶽第四世溈仰宗世系圖 | 3 | 13 | 95 | 6 |
| 5 | 南嶽第五世臨濟宗世系圖 | 3 | 87 | 480 | 7 |
| 6 | 南嶽下臨濟宗黃龍法派世系圖 | 4 | 99 | 644 | 6 |
| 7 | 南嶽下臨濟宗楊岐法派世系圖 | 5 | 170 | 737 | 8 |
| 8 | 南嶽下臨濟宗虎丘法派世系圖 | 6 | 208 | 652 | 7 |
| 9 | 南嶽第七世雲門宗法派世系圖 | 7 | 85 | 499 | 7 |
| 10 | 雪竇顯法派世系圖上 | 7 | 22 | 437 | 6 |
| 11 | 南嶽下雲門宗雪竇顯法派世系圖下 | 8 | 61 | 348 | 6 |
| 12 | 南嶽第九世法眼宗法派世系圖 | 8 | 40 | 303 | 5 |
| 13 | 大鑑下第十世 | 8 | 2 | 12 | 2 |
| 14 | 青原法派世系圖 | 9 | 45 | 229 | 5 |
| 15 | 青原第五世曹洞宗法派世系圖 | 9 | 87 | 396 | 8 |
| 16 | 青原下曹洞宗壽昌經法派世系圖 | 9 | 5 | 5 | 5 |
| 17 | 青原下曹洞宗雲門澄法派世系圖 | 9 | 5 | 5 | 5 |

Cộng với 2 bài tựa (`type="xu"`) và 3 div chú thích (`apparatus`/`xuzang-notes`/`add-notes`) = 22 `cb:div`.
Độ sâu lồng tối đa toàn tác phẩm = **9** (諸祖旁出法派系圖) — khớp thẩm định 2026-10-20.

## 3. Hai kiểu mã hoá quan hệ

### Kiểu A — item ngang hàng + nhãn 第N祖 (三十三祖世系圖)
34 item cấp đầu: 始祖 釋迦牟尼佛 (`itemX86p0320a2001`) + 33 tổ là **anh em hàng hàng** trong cùng
một list. Quan hệ nối tiếp nằm ở **thứ tự + nhãn 第N祖**, không ở markup lồng nhau.
Dãy nhãn đo được: 1→33 **liên tục, không khuyết** (`continuous_1_to_N = true`).
Lưu ý dạng nhãn không thuần nhất: `第一祖` nhưng `二祖`, `三祖`… (thiếu 第) — parser phải chấp nhận cả hai.

### Kiểu B — list lồng nhau + nhãn N世 (các 法派世系圖)
Con nằm trong `<list>` con của item cha; nhãn đời tăng dần theo cấp.
Ví dụ chuẩn: `itemX86p0335a0501` [一世] 南獄懷讓 ⊃ `itemX86p0335a0601` [二世] 馬祖道一
(chữ 南**獄** là chữ sai của nguồn — giữ nguyên văn; ở 三十三祖世系圖 itemX86p0324a1001 lại viết đúng 南**嶽**懷讓).

## 4. Kiểm chéo nhãn (toàn tác phẩm)

| Đo | Giá trị |
|---|---|
| Cặp (cha có nhãn, con trực tiếp) | 2.000 |
| Con có nhãn số | 121 — **100% khớp con = cha + 1, 0 lệch** |
| Con không nhãn | 1.879 (đồng môn R03 + tiểu sử R04) |
| Cha có ≥2 con cùng nhãn k+1 | **0** — mỗi đời chỉ 1 người mang nhãn trong một list con |

⇒ Quy tắc kiểm chéo "nhãn con = nhãn cha + 1" **không có ngoại lệ** trong toàn bộ 121 cặp có nhãn.
1.879 item không nhãn là phần phải xử lý bằng R03/R04/R06.

## 5. Nhãn đời toàn cục

| Nhóm | Số item |
|---|---|
| Có nhãn `第N祖` (kiểu A) | 33 |
| Nhãn `始祖` | 1 |
| Có nhãn `N世` (kiểu B) | 166 |
| Nhãn `N世` nhưng mất chữ `□□世` | 10 |
| Không có nhãn | 5.666 |

## 6. Các cấu trúc đặc biệt (đầu/giữa/cuối tác phẩm)

### 6.1 雪竇顯法派世系圖上 — nhãn là VĂN XUÔI, không phải nhãn đời
Item gốc `itemX86p0428a0301` 雪竇重顯 có note inline = *"卍進本雪竇為四世，已下遞次準之。"* (bản 卍進
tính 雪竇 là 四世, dưới đây lần lượt theo đó) — **không parse được thành số**. Toàn bộ 49 item con
không nhãn. ⇒ đời chỉ suy được từ **tiêu đề div + văn note**, không có nhãn số để kiểm chéo.

### 6.2 大鑑下第十世 — không nhãn nào
`itemX86p0455a2301` 承天昭 ⊃ 11 đệ tử không nhãn. Đời suy từ **tiêu đề div** ("đời 10 dưới 大鑑").
Cạnh từ lồng nhau ở đây chỉ đạt mức `proposed` (không có nhãn kiểm chéo).

### 6.3 壽昌經 & 雲門澄 — mất nhãn hàng loạt
10 nhãn `□□世` tập trung hết ở 2 sơ đồ cuối (5+5 item): 壽昌慧經 (`itemX86p0472a1301`),
愽山元來 (`itemX86p0472a1501`), 雲門圓澄 (`itemX86p0472a2201`)… trong đó 7 item **cả tên lẫn nhãn
đều rỗng/mất** (name = ""). ⇒ 2 sơ đồ này **không đủ thông tin trong XML** để trích cạnh có kiểm chéo.

### 6.4 Cấu trúc dưới 慧能 (cuối sơ đồ 1) — tiểu sử và đệ tử CÙNG CẤP
`itemX86p0324a0101` [三十三祖] 慧能 ⊃ list gồm: item tiểu sử (`itemX86p0324a0201`, không tên),
`itemX86p0324a1001` 南嶽懷讓, `itemX86p0324a1701` 青原行思. Hai đệ tử **không có nhãn đời** —
đúng mẫu R03 (đồng môn cùng thầy). Tiểu sử của mỗi đệ tử nằm trong list con riêng của họ,
kết thúc bằng chú "輪派裔別見。" / "派裔別見。" (R05).

### 6.5 Chú thích chéo 別見 — 18 chỗ
`派裔別見` 2 · `法嗣別見` 8 · dạng khác 8. Ví dụ: `itemX86p0324a0101` (慧能 — "輪派裔別見"),
`itemX86p0456a2101` ("法嗣別見。杏林"), `itemX86p0457a1901` ("法嗣別見之注").

### 6.6 Lớp hiệu đính (R07)
`note`: inline 330 (nhãn đời) · `type=add` 107 · `type=orig` foot 10 · `cf1` 1 · `cf2` 1.
`app/lem/rdg` 107 bộ, witness `#wit.cbeta`【CB】/`#wit.orig`【卍續】. Ví dụ đầu: lem 已 / rdg 巳;
cuối (index 106): lem 第 / rdg rỗng.

### 6.7 Gaiji
`charDecl` định nghĩa **34** ký tự CB (CB00589…CB15766); `<g>` dùng **87** lần, 34 ref phân biệt
— khớp nhau hoàn toàn. Một số char có `normalized form` (vd CB04636 → 璿), một số chỉ có composition.

## 7. Kết luận: XML có đủ để tái tạo quan hệ không?

| Phần | Đủ trong XML? |
|---|---|
| Kiểu A (三十三祖) — 33 cạnh trục | **Đủ** (nhãn liên tục 1→33) |
| Kiểu B — 12/17 sơ đồ có chuỗi nhãn | **Đủ** cho cạnh có nhãn kiểm chéo (121 cặp, 0 lệch); 1.879 item không nhãn xử lý bằng R03 (đồng môn) — cạnh R03 đạt mức candidate, cần kiểm mẫu rộng ở GĐ4–5 |
| 雪竇顯上 / 大鑑下第十世 | **Một phần** — cạnh từ lồng nhau chỉ `proposed`, không có nhãn kiểm chéo |
| 壽昌經 / 雲門澄 | **KHÔNG đủ** — nhãn mất (□□世), 7/10 item mất cả tên ⇒ cần **đọc ảnh trang** (p0472) hoặc nguồn khác; không đoán |
| Chú thích chéo 別見 | XML chỉ chứa chữ ghi chú, không có liên kết đích ⇒ ghi `cross_ref` chờ duyệt, không tự nối |

## 8. Số đo chưa thực hiện được

- Không đo được độ chính xác tách tên trên toàn bộ 5.876 item (chỉ kiểm mẫu — GĐ4 gold set sẽ đo).
- Không đối chiếu được với DILA/Marcus trong GĐ0–2 (thuộc GĐ7).
