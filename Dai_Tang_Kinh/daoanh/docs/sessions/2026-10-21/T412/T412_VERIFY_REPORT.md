# T412 (BUG-037) — Kiểm chứng: nhãn cây Pháp hệ dùng tên đầy đủ TTL

**Ngày:** 2026-10-21 · **Người kiểm:** coordinator (opencode)
**Trạng thái:** code ĐÃ CÓ trong working tree (do session khác viết ~13:44, **chưa commit**);
coordinator **kiểm chứng hoạt động**, không viết lại.

## Phát hiện

`app.py` đã có sẵn khối T412 (dòng ~6367+): `_t412_read_main_label`, `_t412_build_index`,
`_t412_get_index`, `_t412_resolve_display_name`, wired vào 4 chỗ:
- `api_monk_lineage_tree` (L7004)
- `api_monk_ancestor_spine` (L7123, L7175)
- `api_monk_ancestor_path` (L7262)

`places.html` có `_t412NameSourceNote(n)` — tooltip ghi nguồn tên (TTL / DILA phiên âm /
"nhiều hồ sơ TTL khác tên, chờ Admin chốt").

Thứ tự ưu tiên đúng done_when: (a) `rdfs:label@vi` của file TTL nối DILA ID → (b) tên DILA.
Nhiều hồ sơ TTL khác tên → dùng DILA + `ttl_conflict`. KHÔNG dùng `vn_person_authority.name_vi`.

## Bằng chứng (Flask test client)

| Node | primary | name_source |
|---|---|---|
| A004980 | **Hưng Hóa Tồn Tưởng** | TTL ✅ |
| A004981 | **Nam Viện Huệ Ngung** | TTL ✅ |
| A003627 | Nghĩa Huyền | DILA (không có TTL → fallback đúng) |
| A000490 | Hi Vận | DILA |
| A010916 | Lỗ Tổ Bảo Vân | TTL |

Routes: `/daoanh/api/monk/A004980/lineage-tree` 200 (13 nodes), `/ancestor-spine` 200 (21 nodes).

## Ghi chú

- Case Admin nêu "Lâm Tế Nghĩa Huyền"/"Bách Trượng Hoài Hải" hiện tên DILA ("Nghĩa Huyền",
  "Hi Vận") → nghĩa là các DILA ID đó **chưa nối file TTL** (hoặc TTL label khác) — thuộc phần
  (6) mapping DB, **cần Admin duyệt từng dòng** mới sửa. Đã liệt kê để trình riêng.
- Dữ liệu phát hiện phụ (ngoài phạm vi T412): vài node Hàn Quốc hiện tên Hangul
  (A032156 `침굉현변`, A032113 `소요태능`) và A032162 = "Tổ Sư" — thuộc BUG-038/identity, xử lý riêng.
- Phần code: **không cần sửa thêm**; chờ Admin xác nhận DONE + quyết định commit (file đang
  trộn WIP session khác).
