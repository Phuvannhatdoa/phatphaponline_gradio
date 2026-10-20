# T423/T424 — Audit cạnh TTL (chỉ đọc, chưa sửa gì)

Ngày: 2026-10-20
DB: `daoanh/data/lineage.db` (mode=ro)
Phạm vi: `lineage_edge_assertions WHERE source_code='TTL'`

## Tóm tắt số liệu

- Tổng cạnh TTL `mapping_verified=0`: **448**
  - Cả 2 đầu đã có A-ID hợp lệ (people), chỉ chưa gắn cờ `mapping_verified=1`: **133**
  - Có ít nhất 1 đầu còn là `ptda:<slug>` chưa gán A-ID: **315** (ứng với **187 slug duy nhất**)
- Tất cả 187 slug `ptda:` đều ĐÃ có bản ghi trong `entity_source_ids` (source=`TTL_LOCAL`), nhưng với `match_status='candidate'` (confidence ~0.3) — nghĩa là hệ thống đã phát hiện và chờ Admin xác nhận map sang người nào, KHÔNG phải lỗi import, mà là "chưa duyệt". Tổng `entity_source_ids` TTL_LOCAL: 794 `accepted` / 260 `candidate`.
  - Lưu ý: đề bài gốc ước tính "66 slug chưa map" — số thực tế đo được là **187 slug**, không phải 66.

## 1. Danh sách đầy đủ 448 cạnh `mapping_verified=0`

Đã xuất đầy đủ tại file kèm: `daoanh/docs/sessions/2026-10-20/T424/step1_full_list.txt` (448 dòng, format `id: subject(zh/vi) -> object(zh/vi) | ref_ttl`). Dưới đây trích các nhóm đáng chú ý nhất.

### 1a. BUG-038 — 16 cạnh gắn vào SAI người (A032162 thay vì A003627)

```
57704  A032162 -> A004980   TS-Hung-Hoa-Ton-Tuong.ttl
57705  A032162 -> A010423   TS-Lam-Te-Nghia-Huyen.ttl
57706  A032162 -> A013245   TS-Lam-Te-Nghia-Huyen.ttl
57707  A032162 -> A019866   TS-Lam-Te-Nghia-Huyen.ttl
57708  A032162 -> A020418   TS-Lam-Te-Nghia-Huyen.ttl
57709  A032162 -> A020421   TS-Dinh-Chau-Thien-Thoi.ttl
57710  A032162 -> A020423   TS-Lam-Te-Nghia-Huyen.ttl
57711  A032162 -> A020424   TS-Am-Chu-Dong-Phong.ttl
57712  A032162 -> A020425   TS-Lam-Te-Nghia-Huyen.ttl
57713  A032162 -> A020426   TS-Am-Chu-Phuc-Bon.ttl
57714  A032162 -> A024945   TS-Lam-Te-Nghia-Huyen.ttl
57715  A032162 -> A027011   TS-Am-Chu-Sam-Duong.ttl
57716  A032162 -> ptda:am_chu_ho_khe        TS-Am-Chu-Ho-Khe.ttl
57717  A032162 -> ptda:bao_tho_dien_chieu   TS-Bao-Tho-Dien-Chieu.ttl
57718  A032162 -> ptda:thuong_chau_me_thuong TS-Lam-Te-Nghia-Huyen.ttl
57976  ptda:hoang_ba_hy_van -> A032162      TS-Hoang-Ba-Hy-Van.ttl
```

### 1b. 2 cạnh đảo chiều xác nhận SAI (so với TTL gốc)

- `57181  A003868(宣鑑/Tuyên Giám) -> A010427(崇信/Sùng Tín)` — **SAI, đảo chiều.**
- `57489  A010427(崇信/Sùng Tín) -> A003868(宣鑑/Tuyên Giám)` — **ĐÚNG.**
- `57079  A000472(妙高/Diệu Cao) -> ptda:tinh_tu_van` — **ĐÚNG.**
- `58058  ptda:tinh_tu_van -> A000472(妙高/Diệu Cao)` — **SAI, đảo chiều, cạnh trùng/ngược.**

## 2. Phân tích BUG-038 chi tiết

| ID | name_zh | name_vi (DB) | dynasty |
|---|---|---|---|
| A003627 | 義玄 | Nghĩa Huyền | 唐 (Đường — đúng, Lâm Tế Nghĩa Huyền thật) |
| A032162 | 義玄 | **Tổ Sư** (tên giả/placeholder, không phải tên riêng) | 朝鮮 (Triều Tiên — SAI, trùng tên Hán nhưng là người khác) |

`vn_person_authority`:
```
lam_te_nghia_huyen | dila_id=A032162 | method=auto_ttl      | 2026-09-14
alias_A003627       | dila_id=A003627 | method=alias_vi_suffix | 2026-09-14
```

**Root cause:** bộ mapper tự động (`auto_ttl`) đã khớp theo Hán tự `義玄` mà không phân biệt triều đại/định danh, chọn nhầm bản ghi Triều Tiên (A032162, tên hiển thị chỉ là "Tổ Sư" — một placeholder generic, không phải tên dịch thật) thay vì bản ghi Đường (A003627, tên đúng "Nghĩa Huyền"). 16 cạnh TTL ở trên đã bị gắn theo `vn_person_authority` sai này khi import T424.

**Cần sửa:** cả 16 cạnh subject `A032162` phải đổi thành `A003627`, và sửa lại `vn_person_authority.lam_te_nghia_huyen.dila_id` → `A003627`. (Không thực hiện trong audit này — chỉ báo cáo.)

**A038890 (Mã Tổ Đạo Nhất) và A004981 (Tuệ Ngung):** kiểm tra 77 cạnh và 2 cạnh liên quan — tên Hán/Việt khớp đúng người, không phát hiện gắn nhầm như A032162. Có thể 2 ID này được nêu trong BUG-038 chỉ vì cùng xuất hiện trong chain truy vết (`chain=A004981,A006575,...`), không phải bản thân chúng bị lỗi.

## 3. Hai cặp đảo chiều — xác nhận bằng TTL gốc

### A003868 ⇄ A010427 (Tuyên Giám ⇄ Sùng Tín)
File `TS-Duc-Son-Tuyen-Giam.ttl` dòng 341: `<ex:monk/duc_son_tuyen_giam> bkg:hasTeacher <ex:monk/long_dam_sung_tin>`
→ Sùng Tín là THẦY của Tuyên Giám.
- Cạnh `57489 (A010427→A003868)` = ĐÚNG hướng (thầy→trò).
- Cạnh `57181 (A003868→A010427)` = SAI, đảo ngược quan hệ. **Cần xóa hoặc sửa hướng.**

### A000472 ⇄ ptda:tinh_tu_van (Diệu Cao ⇄ Tịnh Từ Văn)
File `TS-Tinh-Tu-Van.ttl` dòng 18-19: `<ex:monk/tinh_tu_van> bkg:hasTeacher <ex:monk/kinh_son_nhu_diem>, <ex:monk/kinh_son_dieu_cao>`
→ Diệu Cao (Kính Sơn Diệu Cao) là một trong các THẦY của Tịnh Từ Văn.
- Cạnh `57079 (A000472→ptda:tinh_tu_van)` = ĐÚNG hướng (thầy→trò).
- Cạnh `58058 (ptda:tinh_tu_van→A000472)` = SAI, đảo ngược. **Cần xóa.**

## 4. 187 slug `ptda:` chưa map — trạng thái thật

Không phải "66 slug không có ID" như giả định ban đầu — thực tế **187 slug**, và tất cả đã được ETL T423 đăng ký vào `entity_source_ids` (source=TTL_LOCAL) với `match_status='candidate'`, chờ Admin xác nhận map sang `people.id` nào. Ví dụ:

```
slug                         | source_label (ZQ)         | match_status
am_chu_ho_khe                | Am Chủ Hổ Khê              | candidate (confidence 0.3)
thich_ca_mau_ni_phat         | Thích_Ca_Mâu_Ni_Phật        | candidate (confidence 0.3)
tinh_tu_van                  | (chưa có — người mới)      | candidate
```

**Phát hiện đáng chú ý:** slug `ptda:thich_ca_mau_ni_phat` (Phật Thích Ca) RẤT CÓ THỂ trùng với bản ghi đã có sẵn `A002799 (釋迦牟尼佛 / Thích Ca Mưu Ni Phật, source_origin=DILA)` trong bảng `people`. Lý do candidate-matcher không tự khớp: tên ZQ ghi "Mâu" còn `people.name_vi` hiện tại ghi "**Mưu**" (dị bản phiên âm/lỗi chính tả 牟 = Mâu, không phải Mưu) → so khớp chuỗi thất bại. Đây là ứng viên map thủ công ưu tiên cao cho Admin, không nên để candidate trôi tự động.

Danh sách đầy đủ 187 slug (kèm source_label ZQ và match_status) nằm trong `daoanh/docs/sessions/2026-10-20/T424/step1_full_list.txt` và có thể truy vấn lại bằng:
```sql
SELECT source_entity_id, source_label, match_status, confidence
FROM entity_source_ids WHERE source='TTL_LOCAL' AND match_status='candidate';
```

## 5. Đánh giá — cần sửa trước DONE vs chấp nhận được

**CẦN SỬA trước khi đóng T423/T424 là DONE:**
1. 16 cạnh BUG-038 (`A032162` → đổi subject thành `A003627`) + sửa `vn_person_authority.lam_te_nghia_huyen.dila_id`.
2. Cạnh `57181` (A003868→A010427, đảo chiều) — xóa hoặc đảo lại.
3. Cạnh `58058` (ptda:tinh_tu_van→A000472, đảo chiều/trùng) — xóa.
4. Ưu tiên xác nhận thủ công slug `ptda:thich_ca_mau_ni_phat` → map vào `A002799` (nghi trùng do lỗi phiên âm Mưu/Mâu).

**CHẤP NHẬN ĐƯỢC (không phải lỗi, là trạng thái "chờ duyệt" đúng thiết kế):**
- 315 cạnh còn lại gắn `ptda:<slug>` — đã được flag `mapping_verified=0` đúng quy tắc, đang chờ Admin duyệt từng `candidate` trong `entity_source_ids`. Không phải bug, là backlog review (187 slug, trong đó trừ `thich_ca_mau_ni_phat` ở trên).
- 132/133 cạnh còn lại mà 2 đầu đã có A-ID hợp lệ nhưng `mapping_verified=0` — chưa phát hiện cạnh nào khác bị gắn sai ngoài các cạnh BUG-038 và 1 cạnh đảo chiều đã nêu; còn lại là đúng, chỉ chưa được Admin tick "verified".

## Không có thay đổi dữ liệu nào được thực hiện. Toàn bộ truy vấn là SELECT-only trên DB mode=ro và đọc file TTL gốc.
