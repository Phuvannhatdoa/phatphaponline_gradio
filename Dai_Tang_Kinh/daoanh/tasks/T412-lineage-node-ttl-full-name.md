---
id: T412
bug_id: BUG-037
title: "Bug verify: BUG-037: Cây Pháp hệ hiện tên DILA 2 chữ (Đạo Nhất) — phải hiện tên đầy đủ theo TTL (Mã Tổ Đạo Nhất), không có TTL mới dùng tên DILA"
status: done
created: 2026-10-15
updated: 2026-10-15
owner: code (Hermes giao)
module: TTL Thiền Sư VN
priority: high
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-15 (Admin: 'Trên tree hiện tên chỉ có 2 ký tự theo phiên âm Dila, hãy dùng tên 4 từ như trong TTL name, vd Đạo Nhất là tên Dila, nhưng full name cần show theo phong cách văn phong Việt Nam trước giờ là Mã Tổ Đạo Nhất, Hoàng Bá Hy Vận. Nếu không có TTL Full name thì dùng tên phiên âm Dila.')"
db_write: "Phần code (bước 1–4) KHÔNG ghi DB. Phần sửa mapping dữ liệu (bước 6) CÓ ghi DB → chỉ làm khi Admin duyệt từng dòng."
done_when: >
  (1) Nhãn nút trên cây Pháp hệ (và chuỗi tổ sư ở panel trái, quicklist) dùng thứ tự: (a) tên đầy đủ trong TTL
  (`rdfs:label …@vi` của file TTL nối với DILA ID của nút) → (b) tên phiên âm DILA hiện có. Không còn phụ thuộc cờ
  `is_formal_name` chỉ bật cho 14 dòng `verified`.
  (2) Không lấy `vn_person_authority.name_vi` làm tên đầy đủ (cột này đang chứa tên ngắn "Tồn Tưởng", "Đạo Nhất" hoặc có
  gạch dưới "Bách_Trượng_Hoài_Hải"); đọc `rdfs:label` từ TTL (file trong `data/ttl/` theo `ttl_filename`, hoặc
  `ttl_v2_source_records`) — chỉ đọc.
  (3) Một DILA ID nối tới ≥2 file TTL khác tên (28 DILA ID có >1 dòng không-alias) → KHÔNG đoán: dùng tên DILA, tooltip
  ghi "nhiều hồ sơ TTL, chờ Admin chốt", liệt kê trong session log.
  (4) Tooltip/nhãn phụ cho biết nguồn tên (TTL hay DILA phiên âm) — tuân CLAUDE.md (tên Việt phải rõ nguồn).
  (5) Kiểm trên trình duyệt thật: route Admin báo (A004980) hiện "Hưng Hóa Tồn Tưởng", "Nam Viện Huệ Ngung",
  "Lâm Tế Nghĩa Huyền", "Bách Trượng Hoài Hải"…; một nút không có TTL vẫn hiện tên DILA. Ảnh trước/sau.
  (6) Danh sách mapping sai/thiếu (bảng dưới) được trình Admin; chỉ sửa DB sau khi Admin duyệt từng dòng, có backup.
  (7) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  Code: git revert --no-edit <sha_T412> hoặc chép lại docs/sessions/<ngày>/*.bak-before-T412.
  Dữ liệu (nếu bước 6 được duyệt): backup SQLite API trước khi UPDATE, revert bằng UPDATE ngược theo snapshot từng dòng.
outcome: >
  2026-10-15: RC kiểm (chỉ đọc), tạo task. Chưa sửa.
---

# T412 / BUG-037 — Cây Pháp hệ phải hiện tên đầy đủ theo TTL

## Mục tiêu

Theo văn phong Việt Nam: hiện "Mã Tổ Đạo Nhất", "Hoàng Bá Hy Vận", "Hưng Hóa Tồn Tưởng"… thay cho tên DILA 2 chữ
("Đạo Nhất", "Hy Vận", "Tồn Tưởng"). Không có TTL thì dùng tên phiên âm DILA.

## Chẩn đoán (RC đo 2026-10-15, chỉ đọc)

Route: `/daoanh/places?mode=lineage&focus=A004980&lm=tree&chain=A004981,A006575,A020370,A020434,A020435,A026996,A026997`

1. **Logic hiển thị:** `places.html` `_t86NodeLabel()` (~dòng 6132) chỉ dùng `n.display_name.primary` khi
   `display_name.is_formal_name = true`; app.py chỉ bật cờ này cho TTL `verified` (app.py ~6231/6265/6291) — toàn DB
   chỉ **14/1.511** dòng `verified`. API `/daoanh/api/monk/A004980/lineage-tree` trả mọi nút `verification_status:
   authority_fallback`, `is_formal_name: false` ⇒ luôn rơi về tên DILA.
2. **`vn_person_authority.name_vi` không phải tên đầy đủ:** `hung_hoa_ton_tuong` → "Tồn Tưởng"; `ma_to_dao_nhat` → "Đạo Nhất";
   `nam_nhac_hoai_nhuong` → "Hoài Nhượng"; `bach_truong_hoai_hai` → "Bách_Trượng_Hoài_Hải"; `hoang_ba_hy_van` → "Hoàng_Bá_Hy_Vận".
   Tên đầy đủ đúng nằm ở **TTL `rdfs:label`**: `TS-Ma-To-Dao-Nhat.ttl` "Mã Tổ Đạo Nhất", `TS-Hoang-Ba-Hy-Van.ttl` "Hoàng Bá Hy Vận",
   `TS-Hung-Hoa-Ton-Tuong.ttl` "Hưng Hóa Tồn Tưởng", `TS-Nam-Vien-Hue-Ngung.ttl` "Nam Viện Huệ Ngung".
3. **Mapping TTL ↔ DILA sai/thiếu (cần Admin duyệt, ghi DB):**

| TTL | Hiện tại | Vấn đề |
|---|---|---|
| `ma_to_dao_nhat` (TS-Ma-To-Dao-Nhat) | dòng chính → `A038890` (auto_ttl); alias `alias_A003623` → `A003623` | Dòng chính nhiều khả năng nối nhầm; nút Mã Tổ trên cây là `A003623` (chỉ có dòng alias) |
| `hoang_ba_hy_van` | `dila_id` rỗng (pending) | Chưa nối `A000490` 希運 ⇒ Hoàng Bá không lấy được tên TTL; tên DILA hiện là "Hơi Vận" (phiên âm ZQ sai, nên là "Hy Vận") |
| `phong_huyet_dien_chieu` | 1 dòng name_vi "Huệ Ngung" → `A004981` | Trùng DILA ID với `nam_vien_hue_ngung` → `A004981`; Phong Huyệt Diên Chiểu ≠ Nam Viện Huệ Ngung (vấn đề URI cũ T209/T211) |
| `alias_A006056` (TS-Hung-Hoa-Ton-Tuong) | name_vi "Tưởng" → `A006056` | Alias trỏ thêm một DILA ID khác cho cùng file TTL — cần kiểm |
| (toàn bảng) | 28 DILA ID có >1 dòng không-alias | Theo bước (3): không đoán, dùng tên DILA + cảnh báo |

## Quyết định văn phong của Admin (2026-10-15)

- Admin (03:43, thay cho quy tắc "bỏ Tôn Giả" ghi lúc 03:38 — quy tắc đó **huỷ**): *"TTL có tên Tôn Giả thì giữ nguyên,
  còn tên 4 chữ thường thấy thì dùng y nguyên: Hoàng Bá Hy Vận, Mã Tổ Đạo Nhất; chỉ có nhất đại tổ sư thì mới dùng từ
  Tôn Giả, chỉ có 33 vị mới có từ Tôn Giả"*.
- Quy tắc áp dụng: **dùng nguyên văn `rdfs:label`@vi trong TTL, không thêm/bớt danh xưng.** Danh xưng "Tôn Giả" chỉ
  xuất hiện ở 33 vị Tổ sư (Tây Thiên + Đông Độ) và được giữ nguyên; các vị khác hiện đúng tên 4 chữ trong TTL.
- Admin chốt (03:45): huỷ lựa chọn rút gọn "Đại Giám Huệ Năng" lúc 03:38 — *"update thành lấy full name trong TTL file
  show lên tree"*. Huệ Năng hiện đúng như TTL: **"Tôn Giả Đại Giám Huệ Năng"**. Không có ngoại lệ nào.

## Phạm vi

- Code (không cần duyệt thêm): `app.py` — hàm dựng `display_name` cho node lineage (đọc TTL `rdfs:label` theo `ttl_filename`
  của dòng vnpa có `dila_id` = nút; tie-break theo `vnpa_lookup.VNPA_STATUS_RANK`; bỏ điều kiện chỉ `verified`, nhưng
  giữ `verification_status` để tooltip ghi rõ mức tin cậy); `places.html` `_t86NodeLabel` + tooltip nguồn tên.
  Đọc TTL có cache (không parse 1.000+ file mỗi request). Không ghi DB, không sửa file TTL.
- Dữ liệu (bước 6): chỉ trình bảng đề xuất; KHÔNG UPDATE `vn_person_authority` khi chưa có Admin duyệt từng dòng.
- Cấm: deploy, push, sửa TTL, đổi schema.

## Các bước

- [x] RC kiểm + chẩn đoán (2026-10-15)
- [ ] Sao lưu app.py, places.html
- [ ] Backend: display_name lấy TTL rdfs:label (cache), xử lý nhiều TTL / không có TTL
- [ ] Frontend: `_t86NodeLabel` dùng tên đầy đủ; tooltip nguồn tên (TTL / DILA phiên âm)
- [ ] Kiểm route A004980 + 1 route khác trên trình duyệt thật, ảnh trước/sau
- [ ] Trình Admin bảng mapping sai/thiếu (mục 3) — chờ duyệt, chưa ghi DB
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
