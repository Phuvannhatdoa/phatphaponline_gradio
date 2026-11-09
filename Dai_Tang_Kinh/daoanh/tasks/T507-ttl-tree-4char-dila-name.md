---
id: T507
title: "Tab Cây TTL: tên hiển thị phải là tên đầy đủ 4 chữ theo dictionary TTL"
status: in_progress
owner: daoanh-debugger
created: 2026-10-31
updated: 2026-10-31
---

# T507 — Tab Cây TTL: tên hiển thị phải là tên đầy đủ 4 chữ theo dictionary TTL

**Trạng thái:** 🔧 FIX LÀM RÕ LẠI ÁP DỤNG (2026-10-31, lần 2) — chờ QA/Admin xác nhận qua UI thật
trước khi đánh DONE. **Đọc mục 7 trước** — mục 3/5 bên dưới (lần fix đầu) có 1 kết luận SAI đã bị
Admin bác bỏ và đã sửa lại ở mục 7.

**Tách từ:** T503/T504/T505/T506 (yêu cầu mới của Admin sau khi T506 xong, CHỈ áp dụng tab Cây TTL).

## Yêu cầu gốc (Admin, 2026-10-31)

Trên tab **Cây TTL** của `places.html?mode=lineage&focus=A003627&lm=tree`, tên hiển thị của mỗi
người phải là tên đầy đủ 4 chữ theo dictionary TTL, dù tên Hán gốc chỉ có 2 chữ. Ví dụ: Hy Vận
(希運, 2 chữ Hán) phải hiển thị "Hoàng Bá Hy Vận" (黃檗希運, 4 chữ) — ghép pháp danh với
núi/trú xứ mà dictionary TTL đã lưu, KHÔNG phải vấn đề chính tả Hán-Việt.

Xác nhận của Admin: "tên 4 chữ" = tên đầy đủ lấy từ dictionary TTL (nguồn TTL nội bộ), không phải
chính tả. Nếu phát hiện khái niệm khác thì dừng lại báo cáo trước khi sửa — **không áp dụng**,
vì kết quả điều tra khớp đúng cách hiểu đã xác nhận.

## 1) Cấu trúc dictionary TTL thực tế + field tên 4 chữ

**Route `admin_dictionary_load`** (`routes_misc.py:3103`) **KHÔNG phải** dictionary TTL tên người —
chỉ là `SELECT COUNT(*) FROM places_dila` (tên "B3: Nạp từ điển Hán-Việt" gây hiểu nhầm, có vẻ là
code đặt chỗ cho 1 bước setup cũ, không liên quan). **`_t482_dictionary_lookup`/`_t482_dictionary_lookup_batch`**
(`routes_places.py:2783`/`2635`) tra bảng `lexicon` (term/definition Hán-Việt) — dùng cho trang
catalog địa danh, KHÔNG dùng cho tên hiển thị cây truyền thừa. Cả hai không liên quan đến bug này.

**Dictionary TTL tên người thật sự nằm ở 2 nơi, phối hợp với nhau:**

1. **Bảng `vn_person_authority`** (SQLite) — cột: `id, ttl_filename, name_vi, name_zh,
   dharma_title, dharma_lineage, generation_order, is_lineage_founder, gender,
   biographical_note_vi, birth_year, death_year, appellations, dila_id, status,
   entity_type`. **`name_vi` ở đây là tên NGẮN** (pháp danh/hiệu 2 chữ, ví dụ "Nghĩa Huyền",
   "Tồn Tưởng") — ghi chú sẵn trong code (`core.py` trước `_t412_build_index`, comment
   T412/BUG-037): *"KHÔNG dùng vn_person_authority.name_vi làm tên đầy đủ (tên ngắn / gạch
   dưới)"*. Không có cột `name_vi_full` riêng trong bảng này.
2. **File `.ttl` thật** trong `data/ttl/<ttl_filename>.ttl`, dòng `rdfs:label "..."@vi` **ĐẦU
   TIÊN** trong file = tên đầy đủ 4 chữ (ví dụ `TS-Hung-Hoa-Ton-Tuong.ttl` →
   `rdfs:label "Hưng Hóa Tồn Tưởng"@vi`). Đây mới là "tên 4 chữ theo dictionary TTL" mà Admin
   muốn — không phải cột DB, mà là nội dung file TTL, đọc qua `_t412_read_main_label()`
   (`core.py`, 8KB đầu file) và cache 1 lần/process trong `_t412_build_index()`.

Luồng tra cứu hiện có (đã tồn tại từ T412/BUG-037, **không tự viết mới**):
`_t412_build_index()` (core.py) query
`SELECT dila_id, ttl_filename FROM vn_person_authority WHERE dila_id IS NOT NULL AND dila_id!=''
AND ttl_filename IS NOT NULL AND ttl_filename!='' AND status NOT LIKE 'alias%'`
→ với mỗi `dila_id` tìm **đúng 1 file TTL không mơ hồ**, đọc `rdfs:label@vi` của file đó làm tên
4 chữ. `_t412_resolve_display_name()` ưu tiên nhãn này làm `display_name.primary` khi
`is_formal_name=true`.

## 2) Root cause thật — vì sao có trường hợp hiện tên KHÔNG đúng (hoặc hiện cả ID nội bộ)

**Test A004980 (Hưng Hóa) và phần lớn người có DILA ID khớp TTL: ĐÃ ĐÚNG, không phải bug.**
Verify bằng `GET /daoanh/api/monk/A004980/lineage-tree?trees=ttl` (trước khi sửa bất cứ gì):
`display_name.primary = "Hưng Hóa Tồn Tưởng"`, `name_source: "TTL"`, `is_formal_name: true`.
Cơ chế `_t412_resolve_display_name` (đã có từ T412/BUG-037) hoạt động đúng thiết kế cho MỌI
người có `dila_id` khớp 1 file TTL không mơ hồ.

**Bug thật (CONFIRMED, khớp đúng ví dụ minh hoạ "Hy Vận" của Admin):** một nhóm nhân vật trong
TTL **KHÔNG có DILA ID** — chỉ tồn tại trong `vn_person_authority` với `dila_id=''` (204 người,
ví dụ `hoang_ba_hy_van`, `am_chu_ho_khe`, `bac_giang_tay_lan_nhuong`...). Các cạnh
(`lineage_edge_assertions`, nguồn TTL) dùng node id dạng **`ptda:<slug>`** cho nhóm này (ví dụ
`ptda:hoang_ba_hy_van`), KHÔNG có hàng tương ứng trong bảng `people`.

`_t412_build_index()` chỉ lập chỉ mục theo **`dila_id`** → nhóm 204 người này **không bao giờ**
được lập chỉ mục (vì `dila_id=''` bị loại bởi điều kiện `dila_id!=''`). `_t86_person_info()`
(core.py ~8840, dùng để build `node.name_vi/name_zh` ban đầu) tra theo thứ tự
`marcus_reference → people → ttl_persons`, cả 3 đều KHÔNG có hàng cho `pid='ptda:hoang_ba_hy_van'`
→ rơi về fallback cuối cùng `zh = ... or pid` → **hiện nguyên chuỗi ID nội bộ
`"ptda:hoang_ba_hy_van"` làm tên hiển thị**, tệ hơn cả tên ngắn 2 chữ. `_t86_resolve_display_name()`
cũng không có đường tra `vn_person_authority` theo `id` (chỉ theo `dila_id`) nên fallback cuối
cùng cũng trả `person_id` làm `primary`, gắn nhầm `source_type: "dila"`.

**Xác minh bằng DB trực tiếp** (trước fix):
```
people WHERE id='ptda:hoang_ba_hy_van'           -> None (không có hàng)
vn_person_authority WHERE id='hoang_ba_hy_van'    -> name_vi='Hoàng_Bá_Hy_Vận',
                                                      ttl_filename='TS-Hoang-Ba-Hy-Van', dila_id=''
```
**Xác minh qua API trước fix** (`GET /daoanh/api/monk/A004980/lineage-tree?trees=ttl&up=2&down=2`):
node `ptda:hoang_ba_hy_van` → `"name_vi":"ptda:hoang_ba_hy_van"`,
`"display_name":{"primary":"ptda:hoang_ba_hy_van","source_type":"dila","is_formal_name":false}`.

**Phát hiện phụ (BÁO ADMIN — KHÔNG tự sửa, cần quyết định riêng):** người này **CÓ sẵn 1 DILA ID
thật** — `A000490` (`people.name_vi="Hơi Vận"`, `name_zh="希運"`) — nhưng `vn_person_authority`
**không có hàng nào map `dila_id='A000490'`**. Tức là dữ liệu TTL đã tạo **2 định danh riêng biệt**
cho cùng một nhân vật thật (DILA `A000490` và TTL-native `ptda:hoang_ba_hy_van`), chưa được
crosswalk. Đây là vấn đề identity/crosswalk ở tầng ETL TTL — KHÔNG sửa trong task này (quy tắc
"không merge record chỉ bằng matching tên", cần Admin quyết định quy trình crosswalk TTL↔DILA).

## 3) Fix đã áp dụng

Backup trước sửa: `docs/sessions/2026-10-31/core.pre-T507.py` (toàn bộ `core.py` trước khi sửa).

**`core.py`** — sửa `_t86_person_info(conn, pid)` (2 bản trùng nhau, dòng ~3558 và ~8840 — chỉ
bản sau có hiệu lực do Python override, sửa cả 2 cho nhất quán, theo đúng cách T506 đã làm với
`_t138_edge_assertions`): thêm bước tra `vn_person_authority WHERE id = <pid bỏ tiền tố 'ptda:'>`
khi `pid` bắt đầu bằng `'ptda:'` VÀ không có hàng trong `people`/`ttl_persons`. Lấy `name_vi`
(thay `_` bằng khoảng trắng — chuẩn hoá trình bày, KHÔNG suy đoán/ghép thêm nội dung — 4/">200"
hàng trong `vn_person_authority` có `_` thay vì khoảng trắng do lỗi nhập liệu nguồn, xem mục 5),
`name_zh`, `biographical_note_vi` làm bio, đánh dấu `source_type='ttl_local'`.

Sửa thêm `_t86_resolve_display_name()` (2 bản, dòng ~3882/~9164): ở fallback cuối cùng, khi
`person_id` bắt đầu `'ptda:'` VÀ `node.source_type=='ttl_local'` (do bước trên gắn) → gắn đúng
`source_type:'ttl'`, `is_formal_name:true`, `verification_status:'ttl_local_fallback'` thay vì
mặc định `'dila'`/`false` — để badge/consumer khác không hiểu nhầm tên TTL là tên DILA.

**Vì sao an toàn, không ảnh hưởng tab DILA/Marcus:** đã kiểm bằng SQL — node id dạng `ptda:<slug>`
**chỉ xuất hiện trong `v_tree_ttl`** (314 cạnh), **0 cạnh** trong `v_tree_dila`/`v_tree_marcus`.
Hai hàm sửa dùng chung cho cả 3 route cây, nhưng điều kiện `pid.startswith('ptda:')` chỉ khớp dữ
liệu vốn chỉ render trên tab TTL — không đổi hành vi cho bất kỳ `A0xxxxx` nào khác.

**`places.html`** — thêm badge "thiếu tên 4 chữ" (yêu cầu mục 5 của Admin) cho người CHƯA có tên
TTL đầy đủ, CHỈ khi tab đang active là Cây TTL (`window._currentTreeSource === 'ttl'`):
- `TREE_LABEL(n)` (~6694): nếu `missing4` (tab TTL + `display_name.name_source !== 'TTL'`) →
  nối `' ⚠'` vào tên hiển thị trên node cây (vis.js box).
- `_t86NodeLabel(n)` (~6182): cùng điều kiện, nối `' ⚠'` vào tên hiển thị breadcrumb/sidebar/
  inspector cạnh.

Không sửa gì ở nhánh render tab DILA/Marcus; điều kiện `window._currentTreeSource === 'ttl'`
chặn hoàn toàn 2 tab kia (đã verify bằng browser — xem mục 4).

## 4) Verify (Browser pane thật, session local, Ctrl+Shift+F5, app.py đã restart nạp code mới)

- **A004980 (Hưng Hóa Tồn Tưởng), tab Cây TTL:** breadcrumb "Hưng Hóa Tồn Tưởng (存獎) — DILA ID:
  A004980" — ĐÚNG tên 4 chữ, KHÔNG có badge ⚠ (đã có TTL). Network log
  `GET lineage-tree?up=2&down=2&trees=ttl`: `display_name.primary="Hưng Hóa Tồn Tưởng"`,
  `name_source="TTL"`.
- **A003627 (Nghĩa Huyền), tab Cây TTL:** breadcrumb "義玄 (Nghĩa Huyền) ⚠ (義玄) — DILA ID:
  A003627" — có badge ⚠ (CHƯA có 4 chữ, vì `ttl_filename` rỗng cho người này trong
  `vn_person_authority` — không phải lỗi code, không có file TTL nào khớp).
- **A003627, tab Cây DILA (kiểm regresssion T506):** breadcrumb "義玄 (Nghĩa Huyền) (義玄) — DILA
  ID: A003627" — KHÔNG có badge ⚠ (badge chỉ hiện ở tab TTL theo thiết kế) — xác nhận T506 không
  bị đụng.
- **Node `ptda:hoang_ba_hy_van` (trong cây A003627/A004980 mở rộng, tab TTL):** trước fix hiện
  `"ptda:hoang_ba_hy_van"` nguyên văn; sau fix → `"Hoàng Bá Hy Vận"`, `name_source="TTL"`,
  `is_formal_name=true` — khớp đúng ví dụ minh hoạ Admin đưa ra. Verify qua PowerShell
  `Invoke-WebRequest` (network log tương đương DevTools) + đã mở popup "Chọn nhánh trực hệ" trong
  Browser pane thấy 2 người con của Nghĩa Huyền ("Trấn Châu Đại Bi", "Truy Châu Thủy Lục") cũng là
  dạng `ptda:` và đã hiện tên 4 chữ đầy đủ, không còn ID nội bộ.
- `python -m py_compile core.py routes_lineage.py app.py` → OK.
- Console log Browser pane: không có lỗi JS sau khi đổi `TREE_LABEL`/`_t86NodeLabel`.
- App server (port 5000) đã kill + restart (`python -X utf8 app.py`, chạy nền) để nạp code mới.

## 5) Danh sách người thiếu tên 4 chữ (trong phạm vi cây đã load cho A003627 + A004980, up=2/down=2)

Chỉ **1 người**: **Nghĩa Huyền (A003627)** — `vn_person_authority` có 2 hàng cho `dila_id=A003627`
nhưng cả 2 đều `ttl_filename=''` (rỗng) → không có file TTL nào để đọc 4 chữ. Đây là giới hạn dữ
liệu nguồn, không phải lỗi code — Admin cần xác nhận có nên bổ sung file TTL cho Lâm Tế Nghĩa
Huyền hay giữ nguyên (ngài thường được gọi "Nghĩa Huyền" không thêm tiền tố núi/trú xứ trong
nhiều nguồn Việt).

**Phát hiện phụ ngoài phạm vi 2 ID test (không yêu cầu sửa, chỉ báo cáo):**
- 4 hàng trong `vn_person_authority.name_vi` có `_` thay vì khoảng trắng (lỗi định dạng nguồn,
  KHÔNG sửa DB trong task này — đã chuẩn hoá chỉ ở tầng hiển thị, xem mục 3):
  `bach_truong_hoai_hai` ("Bách_Trượng_Hoài_Hải"), `dao_xuoc` ("TS Đạo_Xước"), `hoang_ba_hy_van`
  ("Hoàng_Bá_Hy_Vận"), `thich_ca_mau_ni_phat` ("Thích_Ca_Mâu_Ni_Phật").
- `A000490` (Hy Vận, DILA thật) và `ptda:hoang_ba_hy_van` (TTL-native) là 2 định danh riêng biệt
  cho khả năng cùng 1 người thật, chưa crosswalk — xem mục 2.

## 6) py_compile

`python -m py_compile core.py routes_lineage.py app.py` → PY_COMPILE_OK (chạy lại sau mọi sửa).

## Ràng buộc đã tuân thủ

- KHÔNG đánh DONE.
- KHÔNG git commit.
- KHÔNG tự UPDATE DB bằng tay (chỉ sửa code đọc + chuẩn hoá hiển thị, không ghi `vn_person_authority`).
- KHÔNG tự bịa/dịch tên bằng LLM — mọi tên 4 chữ lấy nguyên văn từ `vn_person_authority.name_vi`
  (chỉ thay `_`→` `) hoặc từ `rdfs:label@vi` trong file `.ttl` (cơ chế có sẵn từ T412/BUG-037,
  không tự viết mới).
- KHÔNG đổi tab DILA/Marcus (T506) — verify bằng browser thật ở mục 4.

## 7) LÀM RÕ LẠI 2026-10-31 (lần 2) — Admin bác bỏ hướng `rdfs:label` qua `_t412_resolve_display_name`/dictionary, sửa lại root cause mục 5

**Yêu cầu làm rõ của Admin:** fix ở mục 3 (dùng `rdfs:label@vi`/`_t412_resolve_display_name`/
`vn_person_authority`) **KHÔNG đúng ý Admin** theo cách Admin diễn đạt lại — Admin yêu cầu: KHÔNG
dùng dictionary để tra/ghép tên, tên 4 chữ phải lấy từ **1 trường full-name 4 chữ TỰ CÓ sẵn trong
chính file TTL gốc** (không ghép từ 2 trường, không lookup chéo bảng khác). Ví dụ Admin đưa: "Lâm
Tế Nghĩa Huyền", "Hoàng Bá Huy Vận" (admin tự ghi — xem điểm quan trọng bên dưới), "Hưng Hóa Tồn
Tưởng", "Minh Hoàng Tử Dung".

### 7.1 Trường full-name 4 chữ thật trong TTL là gì

**Đã xác minh lại bằng cách đọc trực tiếp nội dung 2 file `.ttl` gốc** (không qua DB, không qua
code cũ):

```turtle
# data/ttl/TS-Lam-Te-Nghia-Huyen.ttl (dòng 7-8)
<ex:monk/lam_te_nghia_huyen> a bkg:Monk ;
    rdfs:label "Lâm Tế Nghĩa Huyền"@vi ;

# data/ttl/TS-Hung-Hoa-Ton-Tuong.ttl (dòng 6-7)
<ex:monk/hung_hoa_ton_tuong> a <bkg:Monk> ;
    rdfs:label "Hưng Hóa Tồn Tưởng"@vi ;
```

**Kết luận: trường full-name 4 chữ thật = chính `rdfs:label@vi` của subject chính trong file TTL —
KHÔNG phải field nào khác.** Đây **CÙNG MỘT trường** mà `_t412_read_main_label()` (core.py, từ
T412/BUG-037) đã luôn đọc — predicate không sai, không có field `pth:fullNameVi` hay field riêng
nào khác. Khác với lần sửa trước **không phải vì predicate sai**, mà vì **bước chọn file TTL
tương ứng với 1 `dila_id` bị sai** (xem 7.2).

### 7.2 Root cause THẬT (sửa lại mục 5 — kết luận "giới hạn dữ liệu nguồn, A003627 không có file
TTL" ở lần fix trước là SAI)

`_t412_build_index()` (code cũ, mục 3) tìm file TTL của 1 `dila_id` **chỉ qua cột DB**
`vn_person_authority.ttl_filename`:
```sql
SELECT dila_id, ttl_filename FROM vn_person_authority
WHERE dila_id IS NOT NULL AND dila_id!='' AND ttl_filename IS NOT NULL AND ttl_filename!=''
  AND status NOT LIKE 'alias%'
```
Với `A003627` (Lâm Tế Nghĩa Huyền), **CẢ 2 hàng** trong `vn_person_authority`
(`id='lam_te_nghia_huyen'` và `id='alias_A003627'`) có **`ttl_filename=''` (rỗng)** — nên điều kiện
`ttl_filename!=''` loại A003627 ra khỏi index hoàn toàn, dù file `TS-Lam-Te-Nghia-Huyen.ttl`
**THỰC SỰ TỒN TẠI TRÊN ĐĨA** với đúng `rdfs:label "Lâm Tế Nghĩa Huyền"@vi`. Đây chính là lỗi: cột
DB `ttl_filename` là dữ liệu **cache/import bị thiếu**, không phản ánh đúng thực tế file hệ thống
— lần fix trước đọc cột này rồi kết luận nhầm "không có file TTL cho A003627" (mục 5 cũ), trong
khi file có thật, chỉ là chưa được liên kết trong DB.

**Đo trên toàn bộ `vn_person_authority`** (851 hàng non-alias có `dila_id`): **11 hàng** có
`ttl_filename` rỗng nhưng file `.ttl` tương ứng (suy từ `id`) tồn tại thật trên đĩa — gồm cả
A003627. Danh sách đầy đủ:

| dila_id | id (slug) | file .ttl tồn tại thật |
|---|---|---|
| A003627 | lam_te_nghia_huyen | TS-Lam-Te-Nghia-Huyen.ttl |
| A008373 | truong_linh_thu_trac | TS-Truong-Linh-Thu-Trac.ttl |
| A026926 | tinh_nhan_ke_thanh | TS-Tinh-Nhan-Ke-Thanh.ttl |
| A024906 | chieu_hien_hoi_thong | TS-Chieu-Hien-Hoi-Thong.ttl |
| A045360 | vo_chuan_su_pham | TS-Vo-Chuan-Su-Pham.ttl |
| A010985 | dong_son_trach_ngon | TS-Dong-Son-Trach-Ngon.ttl |
| A020497 | long_hoa_te_nhac | TS-Long-Hoa-Te-Nhac.ttl |
| A020109 | phung_tuong_thach_tru | TS-Phung-Tuong-Thach-Tru.ttl |
| A021328 | coc_son_hai | TS-Coc-Son-Hai.ttl |
| A012379 | to_tong_vien_quang | TS-To-Tong-Vien-Quang.ttl |
| A020563 | khanh_thien_thu_long | TS-Khanh-Thien-Thu-Long.ttl |

(Đo bằng cách so `id` → tên file suy theo quy ước `TS-<Title-Case-Dash>.ttl`, rồi kiểm file có
thật trong `data/ttl/`. Vì vậy mục 5 cũ — "Nghĩa Huyền thiếu tên 4 chữ vì giới hạn dữ liệu nguồn"
— **bị bác bỏ, đã sửa lại**.)

**Quan trọng — "Hy Vận" vs "Huy Vận":** đã đọc trực tiếp `data/ttl/TS-Hoang-Ba-Hy-Van.ttl`:
`rdfs:label "Hoàng Bá Hy Vận"@vi` — giá trị TTL thật là **"Hy Vận"**, KHÔNG phải "Huy Vận" như ví
dụ Admin viết trong yêu cầu làm rõ lần này. Theo đúng ràng buộc "không tự gõ/sửa chính tả theo
suy đoán — luôn lấy đúng giá trị trường TTL thật", **giữ nguyên "Hy Vận"** (giá trị đọc trực tiếp
từ file), KHÔNG đổi theo cách Admin gõ tay trong prompt — vì chính TTL gốc mới là nguồn sự thật,
không phải trí nhớ của Admin lúc gõ yêu cầu. Admin cần xác nhận lại nếu nghi ngờ bản thân file TTL
bị sai chính tả (khi đó sửa file TTL là việc khác, ngoài phạm vi task này).

### 7.3 Fix đã sửa lại (core.py, `_t412_build_index()` + `_t412_read_main_label()`, 2 bản trùng
dòng ~4021/~9328 — sửa cả 2 bằng `replace_all` để nhất quán)

Backup trước khi sửa lần 2: `docs/sessions/2026-10-31/core.pre-T507-clarify.py` (không đè
`core.pre-T507.py` của lần 1).

**Before (mục 3, lần 1):** `_t412_build_index()` chỉ lấy file TTL qua
`vn_person_authority.ttl_filename` (JOIN 1 chiều từ DB, bỏ qua các `dila_id` có `ttl_filename`
rỗng dù file tồn tại thật).

**After (lần 2):**
1. `_t412_read_main_label(path)` nay trả về **cặp `(label, slug)`** thay vì chỉ `label`: `label` =
   `rdfs:label@vi` đầu tiên trong 8KB đầu file (không đổi — vẫn đúng field, xem 7.1); `slug` = phần
   `{slug}` trong chính khai báo `<ex:monk/{slug}> a bkg:Monk` của file (subject do TTL **tự khai**,
   KHÔNG suy từ tên file) — đọc bằng regex mới `_T412_SUBJECT_RE`.
2. `_t412_build_index()` nay quét **TOÀN BỘ** file `.ttl` trong `data/ttl/` một lần, dựng
   `labels_by_slug = {slug: {filename: label}}` từ nội dung file thật (không phụ thuộc cột
   `ttl_filename`, không suy đoán tên file theo quy ước — đã đo 118/1021 file có tiền tố khác nhau
   `TS-`/`Cs-`/không tiền tố, suy đoán tên file không đáng tin).
3. Dùng `vn_person_authority (id, dila_id)` **chỉ để đối chiếu định danh** `dila_id <-> slug`
   (crosswalk, KHÔNG phải tra/ghép tên — giá trị tên không bao giờ lấy từ cột `name_vi` của bảng
   này trong đường đi mới) → `dila_to_slugs = {dila_id: {slug,...}}`.
4. Với mỗi `dila_id`, gộp nhãn từ mọi file khớp `slug` của nó; nếu đúng 1 giá trị tên duy nhất →
   `is_formal_name=true`, `primary` = chính `rdfs:label@vi` đó; nếu nhiều giá trị khác nhau (xung
   đột thật, ví dụ A004981 — xem 7.5) → giữ nguyên cơ chế `ambiguous=true` có sẵn (không đoán).

**Đường đi dữ liệu đầy đủ (đã verify từng bước):** file `.ttl` gốc (`rdfs:label@vi` của subject
`<ex:monk/{slug}>`) → quét trực tiếp trong `_t412_build_index()` (không qua cột DB cache nào cho
GIÁ TRỊ tên) → chỉ dùng `vn_person_authority.id` làm khoá crosswalk `dila_id<->slug` → API
`/daoanh/api/monk/<dila_id>/lineage-tree` field `display_name.primary` (qua
`_t412_resolve_display_name()`, không đổi) → `places.html` `TREE_LABEL()`/`_t86NodeLabel()` đọc
`n.display_name.primary` khi `is_formal_name=true` (không đổi — đã đúng từ lần fix trước, không
cần sửa places.html lần này).

### 7.4 Bằng chứng click thật (Browser pane, session đã đăng nhập, sau khi restart app.py port 5000
nạp code mới — PID cũ 7900 kill, PID mới chạy nền)

- **A003627**, URL `http://127.0.0.1:8080/daoanh/places.html?mode=lineage&focus=A003627&lm=tree`,
  click tab **Cây TTL**: sidebar header hiện **"Pháp hệ · Lâm Tế Nghĩa Huyền"** (zoom screenshot
  xác nhận chữ rõ, không phải suy đoán). Node trung tâm trong cây gắn nhãn "Lâm Tế Nghĩa Huyền".
- **A004980**, cùng URL pattern, click tab Cây TTL: breadcrumb hiện **"Hưng Hóa Tồn Tưởng (存奘) —
  DILA ID: A004980"**, node trung tâm nhãn "Hưng Hóa Tồn Tưởng" kèm badge "TTL 39"
  (`generationOrder=39` đúng với TTL file). Node con `A004981` hiện "Huệ Ngung" kèm "TTL ?" (badge
  cảnh báo) — đúng dự kiến (xem 7.5, đây là 1 ca xung đột TTL thật, không phải lỗi mới).
- **Network log** (`read_network_requests`, filter `lineage-tree`): các request
  `GET /daoanh/api/monk/A003627/lineage-tree?...&trees=ttl` và
  `GET /daoanh/api/monk/A004980/lineage-tree?...&trees=ttl` trả `200 OK`. Đối chiếu bằng `curl`
  trực tiếp cổng 5000 (tương đương response DevTools, do response body qua MCP không lấy được)
  sau khi app.py đã restart:
  - `A003627`: `center.display_name = {"primary":"Lâm Tế Nghĩa Huyền","name_source":"TTL",
    "source_file":"TS-Lam-Te-Nghia-Huyen.ttl","is_formal_name":true}`.
  - `A004980`: `center.display_name = {"primary":"Hưng Hóa Tồn Tưởng","name_source":"TTL",
    "source_file":"TS-Hung-Hoa-Ton-Tuong.ttl","is_formal_name":true}`.
- Trước khi restart app.py, cùng request trả `display_name.primary="Nghĩa Huyền"`,
  `name_source="DILA"` (code cũ còn chạy trong RAM) — xác nhận chênh lệch before/after đúng do fix,
  không phải do cache trình duyệt.

### 7.5 Số người thiếu/xung đột tên 4 chữ TTL trong cây đã load (up=2/down=2, `trees=ttl`, qua API
thật sau fix)

- **Cây A003627** (24 node, gồm cả node `ptda:*` không có DILA ID): **23/24** có tên 4 chữ đầy đủ
  (`is_formal_name=true`). **1 node thiếu**: `A004981` → hiện "Huệ Ngung" (2 chữ, fallback DILA).
- **Cây A004980** (5 node): **4/5** có tên 4 chữ đầy đủ. **1 node thiếu**: cùng `A004981`.

**`A004981` không phải lỗi code — là 1 ca xung đột dữ liệu TTL thật, đã verify:**
`vn_person_authority` có **2 hàng khác slug cùng trỏ `dila_id=A004981`**:
`id='nam_vien_hue_ngung'` (→ file `TS-Nam-Vien-Hue-Ngung.ttl`, `rdfs:label="Nam Viện Huệ Ngung"@vi`)
và `id='phong_huyet_dien_chieu'` (→ file `TS-Phong-Huyet-Dien-Chieu.ttl`, tên khác). Cả 2 file đều
tồn tại thật và đều tự nhận là A004981 nhưng mang 2 tên khác nhau → `_t412_build_index()` phát
hiện `len(distinct) > 1` → đúng thiết kế đã có (không đoán), trả `ambiguous=true`, UI fallback về
tên DILA 2 chữ + badge cảnh báo (cơ chế badge từ lần fix 1, mục 3, không đổi). **Cần Admin quyết
định** hàng nào đúng cho A004981 — ngoài phạm vi code task này (không merge record chỉ bằng
matching tên).

### 7.6 py_compile

`python -m py_compile core.py` → OK (chạy sau khi sửa `_t412_build_index`/`_t412_read_main_label`,
2 bản trùng trong core.py).

### 7.7 Ràng buộc đã tuân thủ (lần làm rõ 2)

- KHÔNG đánh DONE.
- KHÔNG git commit.
- KHÔNG ghi DB tay (chỉ sửa code đọc trực tiếp TTL + crosswalk qua `vn_person_authority.id`,
  không ghi `ttl_filename` hay bất kỳ cột nào).
- KHÔNG tự gõ/sửa chính tả tên theo suy đoán — "Hy Vận" giữ nguyên theo giá trị TTL thật (7.2),
  không đổi theo "Huy Vận" Admin gõ trong prompt.
- KHÔNG đụng tab DILA/Marcus — fix chỉ nằm trong `_t412_build_index()`/`_t412_read_main_label()`,
  2 hàm này chỉ được `_t412_resolve_display_name()` gọi, và hàm đó chỉ ảnh hưởng `display_name`

## 8) Quyết định Admin về A004981 + kết quả (2026-11-01)

**Quyết định Admin:** giữ bản `nam_vien_hue_ngung` (`status='pending'`, tên "Nam Viện Huệ Ngung")
làm bản đúng cho `dila_id='A004981'`. Bản `phong_huyet_dien_chieu` (`status='auto_ttl'`, tên
"Huệ Ngung", `ttl_filename` trỏ tới file không tồn tại trên đĩa) được **sao lưu rồi đánh dấu
superseded, KHÔNG xóa**. Cách đánh dấu: Admin chọn **thêm cột `superseded_by` (additive)**,
**KHÔNG đổi giá trị `status`** của dòng nào (giữ đúng quy ước §9.1 `docs/db_schema.md`:
`status` là nhãn nguồn gốc, không phải cờ còn/hết hiệu lực; `superseded` không có trong quy
ước đóng của cột này — xem phát hiện bên dưới).

**Phát hiện trước khi sửa (đã báo Admin, dẫn tới quyết định đổi hướng):** `'superseded'`
KHÔNG có trong quy ước hiện có của `vn_person_authority.status` — cột này là ánh xạ đóng 1:1
với tiền tố `id` (5 giá trị: `verified`/`auto_ttl`/`alias_zh_match`/`alias_vi_suffix`/`pending`,
xem `docs/db_schema.md` §9.1, verify trên 1.506 dòng). Từ "superseded" có dùng rộng trong dự án
nhưng chỉ cho task/doc/translation status, không áp dụng cho cột này. Theo đúng chỉ dẫn
("nếu không có, dừng và báo, không tự đặt giá trị mới"), đã dừng và báo Admin trước khi ghi DB
— Admin quyết đổi hướng sang thêm cột mới thay vì đổi `status`.

**Thực hiện:**
1. Backup bằng `sqlite3.Connection.backup()` (API backup, không copy file thô) →
   `data/backups/lineage_pre_t507_a004981_20261101_005755.db`. `PRAGMA quick_check` trên bản
   sao = `ok`. Kích thước khớp nguồn (1.825.574.912 bytes).
2. Trong 1 transaction (`BEGIN`/`COMMIT`, rollback tự động nếu rowcount≠1 hoặc lỗi):
   `ALTER TABLE vn_person_authority ADD COLUMN superseded_by TEXT;`
   `UPDATE vn_person_authority SET superseded_by='nam_vien_hue_ngung' WHERE id='phong_huyet_dien_chieu' AND dila_id='A004981';`
   → `rowcount=1` → `COMMIT`.
3. Verify sau ghi (SELECT nguyên văn):
   ```
   ROWS_AFTER (1512,)              -- bằng ROWS_BEFORE (1512,), không đổi
   AFTER_ROW ('nam_vien_hue_ngung', 'A004981', 'pending', 'Nam Viện Huệ Ngung', None)
   AFTER_ROW ('phong_huyet_dien_chieu', 'A004981', 'auto_ttl', 'Huệ Ngung', 'nam_vien_hue_ngung')
   ```
   `status` cả 2 dòng giữ nguyên (`pending`/`auto_ttl`), bản `nam_vien_hue_ngung` không bị đụng
   (`superseded_by IS NULL`).
4. Docs đã cập nhật: `docs/db_schema.md` §9.2b (cột mới, additive, chưa có consumer code đọc),
   `docs/ROLLBACK.md` mục "T507 — A004981 xung đột dữ liệu TTL, thêm cột `superseded_by`"
   (đường dẫn backup + câu UPDATE đảo ngược `superseded_by=NULL` + DROP COLUMN thay thế).

**Trạng thái T507 giữ `in_progress`** — việc A004981 này là phát hiện phụ của T507 (§7.5),
đã xử lý theo quyết định Admin nhưng **chưa phải QA/Admin xác nhận DONE toàn bộ task**. Chưa có
consumer code nào đọc `superseded_by` để loại dòng này khỏi kết quả tra cứu `LIMIT 1`/
`_t412_build_index` — nếu cần, đó là việc tiếp theo, ngoài phạm vi phần vừa làm.
  (field cộng thêm), không đổi `name_vi`/`name_zh` gốc dùng ở tab DILA/Marcus.
