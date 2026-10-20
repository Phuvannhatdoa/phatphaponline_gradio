---
id: T223
title: "DILA-ID 29 nhóm trùng — phân loại, quyết gộp/tách, và thứ tự sửa (L7 → L1/L2 → dila_id)"
module: Data / Canonical Identity
priority: critical
status: blocked
undone_reason: "29 nhóm / 61 row có dila_id trùng chưa quyết gộp hay tách. Đã phân loại A/B/C/D kèm đề xuất, nhưng quyết định gộp/tách mang tính ontology nên không tự ý làm."
undone_until: "Khi (a) Admin duyệt nhóm C — 7 nhóm và nhóm D — 13 nhóm, và (b) L7/L1/L2 = 0. Hiện preflight BLOCKING 29 nên ETL chưa chạy được."
undone_action: "ADMIN duyệt nhóm C/D; sau đó mới áp dụng gộp/tách theo thứ tự L7 → L1/L2 → dila_id."
blocked_reason: "chỗ quyết định Admin: 29 nhóm gộp/tách + T198 soft-vs-hard + T98 UX; đồng thời sḚ L7 (13 file) → L1/L2 (24 nhãn) → mới tới dila_id"
owner: mimo-flash
created: 2026-10-03
updated: 2026-10-11
depends_on: [T200, T209, T211]
designed_by: mimo-flash
handoff_to: Admin
plan_approved_at: "2026-10-03 (Admin phê chuẩn đề xuất: T197 + T18 đóng, phần còn mở tách thành T223)"
revert: "docs-only + additive: git revert --no-edit <sha_T223>; DB xem §7"
---

# T223 — 29 nhóm `dila_id` trùng: phân loại, quyết gộp/tách, thứ tự sửa

## Mục tiêu

T223 vẫn blocked cho quyết định 29 nhóm định danh. Nhánh production ETL đã chuyển sang [T357](T357-vnpa-etl-safety-remediation.md), former_ids:[T223]: kế hoạch remediation approved, chưa triển khai/chạy ETL. Cảnh báo trùng ID dưới đây là lịch sử trước khi tracking được tách ngày 2026-10-11.

## Ghi chú lịch sử về trùng ID (2026-10-04)

> ⚠️ **CẢNH BÁO TRÙNG ID (2026-10-04) — chưa xử lý, để dành xem lại.**
> Hiện có **2 việc khác nhau cùng mang ID `T223`**:
>
> | # | File | Nội dung | Người sở hữu |
> |---|---|---|---|
> | 1 | `tasks/T223-dila-id-29-nhom-phan-loai-va-quyet-tach.md` (**file này**) | 29 nhóm `dila_id` trùng · phân loại A/B/C/D · thứ tự L7 → L1/L2 → `dila_id` | task này |
> | 2 | `docs/Mimo-Flash/T223-VNPA-PRODUCTION-ETL-CONTROLLED-EXECUTION-01.md` | VNPA production ETL controlled execution | **session khác** |
>
> **Trùng ở tầng 2 (prose), KHÔNG phải tầng 1 (file)** ⇒ `npm run dup:ids` **không bắt**,
> vì file `docs/` kia không có frontmatter `id:`. Đây đúng là bệnh đã gặp ở **T181**
> (`docs/Mimo-Flash/T181-geo-spatial-…` trùng `tasks/T181-cbeta-bulk-import-…`), chỉ là
> lần này chưa gây hậu quả vì hai việc chưa từng được giao chung.
>
> **Trạng thái worktree lúc phát hiện:** file `docs/…T223-VNPA-…` xuất hiện **đồng thời**
> là `D` (đã xoá khỏi đĩa nhưng còn staged) và `??` (bản untracked) ⇒ có nguy cơ **mất file**.
>
> **Cần xử lý khi nào:** lần chạm `T223` kế tiếp.
> **Cách xử lý:** đổi ID file `docs/` kia sang số trống (theo `AGENTS.md` §16: `dup:ids`
> **và** grep prose), rồi cập nhật `docs/tasktodo.md` + frontmatter + mọi cross-reference.
> **KHÔNG** tự ý sửa file của session khác.

---

> **Vì sao tách task này:** T200 build xong nhưng **còn treo** *"không gộp/tách `dila_id`
> cho 33 nhóm — cần Admin duyệt từng nhóm"*. Đo lại 2026-10-03 thực tế là
> **29 nhóm / 61 row** (số 33 của T200 đã trôi). T223 đưa phần quyết định ra khỏi
> T200 để T200 có thể đóng, và đính kèm 2 việc còn mở khác (T198, T98).

---

## 1. Phát hiện quan trọng: **L1/L2 và `dila_id` trùng là CÙNG một chuỗi hỏng**

Kiểm chứng bằng dữ liệu thật: **11 / 23** file L1/L2 của T209 nằm **bên trong** các nhóm
`dila_id` trùng.

| File L1/L2 | Nhãn sai | Nhóm `dila_id` | Row trong nhóm |
|---|---|---|---|
| `TS-Dam-Chau-Bao-Cai-Uoc.ttl` | `Nam Nhạc Huyền Thái` | `A010511` | `dam_cha_bao_cai_uoc`, `nam_nhac_huyen_thai`, `the_nham_ton_tho` |
| `TS-The-Nham-Ton-Tho.ttl` | `Nam Nhạc Huyền Thái` | `A010511` | (cùng nhóm) |
| `TS-An-Hoa-Van-Nhat.ttl` | `Long Khánh Khánh Nhàn` | `A014491` | `an_hoa_van_nhat`, `long_khanh_khanh_nhan` |
| `TS-Bien-Dam-Hieu-Lieu.ttl` | `Tây Vực Quật Đa Tam Tạng` | `A002653` | `bien_dam_hieu_lieu`, `tay_vuc_quat_da_tam_tang` |
| `TS-Cuu-Danh-To.ttl` | `Long Hoa Đạo Sơ` | `A024897` | `cuu_danh_to`, `long_hoa_dao_so` |
| `TS-Dong-Son-Te-Vi.ttl` | `Giác A` | `A021350` | `dong_son_te_vi`, `giac_a` |
| `TS-Kinh-Trieu-Thi-Loi.ttl` | `Đàm Châu Hoa Lâm` | `A025951` | `dam_chau_hoa_lam`, `kinh_trieu_thi_loi` |
| `TS-Thach-Cung-Hue-Tang.ttl` | `Ngũ Đài Ẩn Phong` | `A009478` | `ngu_dai_an_phong`, `thach_cung_hue_tang` |
| `TS-Thai-Tu-Dong-Quang.ttl` | `Thái Tử Đạo Nhất` | `A038615` | `thai_tu_dao_nhat`, `thai_tu_dong_quang` |
| `TS-Tue-Nhat-Minh.ttl` | `Hoàng Bá Vĩnh Thái` | `A043012` | `hoang_ba_vinh_thai`, `tue_nhat_minh` |
| `TS-Thien-Dong-Pho-Giao.ttl` | `Long Nha Tông Mật` | `A020647` | `alias_A020647`, `thien_dong_pho_giao` |

### Chuỗi nhân quả

```
copy-paste khi sinh TTL  →  subject URI giữ từ người trước   [L7, 15 slug / 13 file]
                          ↓
nhãn rdfs:label bị ghi nhầm theo URI đó             [L1 11 + L2 13]
                          ↓
nhiền row cùng mang 1 dila_id                        [29 nhóm / 61 row]
```

### ⚠️ Hệ quả quyết định — **thứ tự sửa bắt buộc**

> **KHÔNG được sửa `dila_id` trước.** Nếu gộp/tách `dila_id` khi URI + nhãn vẫn sai
> thì lần ETL sau sẽ **tái tạo lại y hệt** 29 nhóm này từ nguồn TTL.
> Thứ tự: **L7 (URI) → L1/L2 (nhãn) → mới tới `dila_id`.**

Đây cũng là lý do T200 chưa nên đóng: đóng T200 bây giờ sẽ ghi "xong" trong khi phần
quyết định còn nằm ở T223.

---

## 2. Phân loại 29 nhóm (đo tự động 2026-10-03)

Tiêu chí: `alias_*` trong id · trùng `name_vi` · trùng `name_zh`.

### A. Có dòng `alias_*` **và** nhiều người khác nhau → **TÁCH** — 1 nhóm

| `dila_id` | Row | `name_vi` |
|---|---|---|
| `A021395` | `alias_A021395` | Ngũ Tổ Pháp Diễn (`法演`) |
| | `bao_an_phap_dien` | Báo Ân Pháp Diễn |
| | `tu_to_phap_dien` | Tứ Tổ Pháp Diễn |

**3 người khác nhau dồn 1 ID** ⇒ `dila_id` gán sai. Đây cũng là nhóm mà tie-break
quyết định thẳng **tên hiển thị**.

> **Admin quyết 2026-10-08: phương án D (hoãn).** Chờ tra DILA cho `A021395`
> (Báo Ân Pháp Diễn / Tứ Tổ Pháp Diễn / Ngũ Tổ Pháp Diễn) trước khi chọn A/B/E.
> Không ghi DB cho nhóm A cho đến khi có quyết định mới.
> Tham chiếu: `docs/Mimo-Flash/T218-A021395-CANONICAL-DECISION-GATE-01.md`.

### B. Nhãn VI trùng nhau → nghi trùng dòng — 8 nhóm

| `dila_id` | Chi tiết | Đọc |
|---|---|---|
| `A004697` | `vo_chuan_su_pham` + `alias_A004697` — **cùng tên** | alias thừa |
| `A004981` | `phong_huyet_dien_chieu` + `nam_vien_hue_ngung` — cùng "Nam Viện Huệ Ngung" | 2 dòng 1 người |
| `A008471` | `hoang_dinh_kien` + `hoang_long_tri_minh` — cùng "Cư Sĩ Thái Sử Hoàng Đình Kiên" | 2 dòng 1 người |
| `A021291` | `dai_hong_to_chung` + `lao_na_tu_dang_dai_hoang` — cùng "Đại Hồng Tổ Chứng" | 2 dòng 1 người |
| `A020456` | `alias_A020456` (Tam Giao Trí Tung) + `thiet_phat_tri_tung` (Thiết Phật Trí Tung) | ⚠️ 2 **người khác** |
| `A020647` | `alias_A020647` (Long Nha Tông Mật) + `thien_dong_pho_giao` (Thiên Đồng Phổ Giao) | alias **đúng** (1 người) |
| `A023045` | `alias_A023045` (Hồng Châu Pháp Đạt) + `duc_vuong_phap_dat` (Dục Vương Pháp Đạt) | alias **đúng** |
| `A043535` | `alias_A043535` (Đẳng Giác Phổ Minh) + `ky_ngan_pho_minh` (Kỳ Ngạn Phổ Minh) | alias **đúng** |

⇒ B **không đồng nhất**: 3 nhóm có alias đúng (không phải lỗi), 3 nhóm là dòng trùng,
1 nhóm (`A020456`) thực chất là 2 người khác nhau.

### C. Trùng `name_zh`, khác `name_vi` → kiểm chứng lại — 7 nhóm

`A010511` · `A002653` · `A008792` · `A009478` · `A038165` · `A045400` · `A045639`

### D. Cả VI lẫn ZH đều khác → nhiều khả năng là **người khác nhau** — 13 nhóm

`A026824` (3 dòng) · `A000108` · `A014491` · `A020018` · `A021084` · `A021326` · `A021350`
· `A024897` · `A025951` · `A030596` · `A038615` · `A043012` · `A047679`

Rõ nhất:
- `A021350` = `dong_son_te_vi` (Đông Sơn Tề Vĩ) + `giac_a` (Giác A) ⇒ 2 người
- `A038615` = `thai_tu_dao_nhat` + `thai_tu_dong_quang` ⇒ 2 người
- `A030596` = `chung_son_dao_long` + `hoa_nghiem_dao_long` ⇒ 2 người

---

## 3. Đề xuất xử lý theo nhóm

| Nhóm | Số | Đề xuất |
|---|---|---|
| **A** | 1 | **HOÃN (deferred, Admin quyết 2026-10-08)** — chờ tra DILA cho `A021395` trước khi chọn A/B/E; không ghi DB |
| **B.alias-đúng** | 3 (`A020647` `A023045` `A043535`) | **KHÔNG LÀM GÌ** — đây là alias hợp lệ, chỉ chấp nhận `dila_id` chung |
| **B.trùng-dòng** | 3 (`A004697` `A004981` `A008471` `A021291`) | **GỘP** — giữ 1 dòng chính, `dila_id` chung |
| **B.2-người** | 1 (`A020456`) | **TÁCH** — Tam Giao Trí Tung ≠ Thiết Phật Trí Tung |
| **C** | 7 | **Admin kiểm** — cần tra nguồn DILA để xác nhận cùng hay khác người |
| **D** | 13 | **TÁCH** — nhãn khác nhau ⇒ nhiều khả năng là nhiều người |

> **Không đoán tên.** Với nhóm C và các nhóm D chưa chắc, tôi chỉ đề xuất mặc định;
> quyết định tách/gộp mang tính ontology là của Admin.

---

## 4. Điều kiện tiên quyết (blocker)

| Việc | Task | Trạng thái |
|---|---|---|
| Sửa 13 file URI sai (L7) | T211 | ⛔ **còn 13 file**, cần Admin duyệt |
| Sửa 24 nhãn (L1 11 + L2 13) | T209 | ⛔ còn 24 |
| Cấp lại 10 file TTL mất | T209 | ⛔ cần Admin |
| 3 file `phong_huyet_dien_chieu` — 3 người hay 1? | T209 | ⛔ cần Admin |

Preflight hiện **BLOCKING 29** ⇒ **ETL vẫn bị chặn**, và T223 không thể chạy trước khi
4 việc trên xong.

---

## 5. Phụ thuộc T200 (tie-break đã có)

Admin đã chốt 2026-10-01: **"a) ưu tiên theo status"**. Đã có test hồi quy chứng minh
deterministic (chạy 50 lần cùng kết quả). Phần còn lại của T200 là **chờ T223**.

→ **Đề xuất: chuyển T200 sang `blocked` với lý do "chờ T223"**, hoặc đóng T200 và mở
lại bằng task riêng. T223 là nơi quyết định.

---

## 6. Hai việc còn mở khác (gộp vào đây để Admin chốt một lần)

### 6a. T198 — soft-invalidate hay hard purge?

| | Hành vi | Hậu quả |
|---|---|---|
| `POST /daoanh/api/admin/translate/invalidate` | `UPDATE status='invalidated'` | Giữ audit trail |
| `invalidate_cache_all_semantic` | **`DELETE`** | **Mất audit trail** |

Cùng mục đích, hành vi khác nhau. **Đề xuất: giữ soft** — xoá cứng khó truy vết lỗi dịch.
Cần thêm migration/flag nếu chọn hard.

### 6b. T98 — 3 câu hỏi UX (không chặn, task đã `done`)

- **Q1** Nút *"Đọc đầy đủ"* mở modal **Hán văn**, không phải bản dịch Việt ⇒ label gây
  nhầm. Đổi thành *"📖 Đọc Hán văn nguồn"*? (2 chỗ: `app.py:2517`, `:2825`, không
  ảnh hưởng logic) — **đề xuất: có**
- **Q2** Warning *"⚠ phân phối tự động"* đã lỗi thời sau T96 units ⇒ **đề xuất: ẩn**
- **Q3** Panel tự đóng khi segment dịch xong (`_dtFullViReset()`) ⇒ giữ mở? Cần logic
  phức tạp hơn — **đề xuất: để sau, không làm lúc này**

---

## 7. Revert

- **Docs + script:** `git revert --no-edit <sha_T223>`
- **DB (khi nào đã áp dụng gộp/tách):** mọi thay đổi phải **additive hoặc có backup
  file-level** `data/backups/lineage_t223_<ts>.db`. Ưu tiên `UPDATE dila_id` có thể
  hoàn nguyên bằng `UPDATE ... SET dila_id=<old>` vì đã lưu bảng ánh xạ trước/sau.
  **Không** dùng `DELETE` hàng loạt.

## 8. Rollback mặc định (nếu Admin chọn "chưa làm gì")

`git revert --no-edit <sha_T223>` — task doc thuần, 0 DB, 0 TTL.

## Cập nhật 2026-10-11 — tách nhánh production ETL khỏi T223

Nhánh report production ETL đã chuyển tracking sang [T357](T357-vnpa-etl-safety-remediation.md), former_ids:[T223]; report giữ path lịch sử và frontmatter task-bound T357. Cảnh báo trùng prose ở trên là lịch sử đã được xử lý tracking. T223 file này vẫn blocked cho quyết định 29 nhóm định danh; approval remediation ETL không gộp/tách người, đổi DILA-ID hoặc duyệt A021395. Không refresh số corpus ở lượt docs-only.
