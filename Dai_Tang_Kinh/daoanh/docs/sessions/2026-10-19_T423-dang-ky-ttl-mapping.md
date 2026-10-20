# Session 2026-10-19 — T423: đăng ký nguồn TTL_LOCAL + người ptda: + mapping TTL (DRY-RUN)

> Bước 2/5 của chuỗi "3 cây": T422 (xong) → **T423** → T424 → T425 → T426.
> Đây là **CHẠY THỬ (chỉ đọc)**; ghi DB (`--apply`) chờ Admin duyệt.

## 1. Thông tin đọc nhanh

| Hạng mục | Giá trị |
|---|---|
| Task | T423 (`tasks/T423-register-ttl-source-and-mapping.md`) |
| HEAD | `5254b95` (T422) |
| Script | `scripts/t423_register_ttl_source_mapping.py` (`--dry-run` mặc định / `--apply` / `--revert`) |
| DB | `data/lineage.db` — **CHƯA ghi** (mọi query `mode=ro`) |
| Bằng chứng | `docs/sessions/2026-10-19/T423/` (4 file) |
| Trạng thái | Dry-run xong; chờ Admin duyệt `--apply` |

## 2. Đọc trong 2 phút

TTL chưa phải nguồn trong lớp định danh. Chạy thử đề xuất: thêm 1 nguồn `TTL_LOCAL`, tạo định danh
cục bộ `ptda:<slug>` cho 204 thiền sư chưa có DILA ID, và mapping **1.054 hồ sơ TTL non-alias**
(bỏ 457 dòng alias) vào `entity_source_ids`.

Ba việc Admin cần quyết:
1. Duyệt `--apply` (ghi: +1 `data_sources`, +204 `entity_hub`, +1.054 `entity_source_ids`, +1 UNIQUE index)?
2. 204 định danh `ptda:` — chấp nhận là `candidate` (chưa đối chiếu DILA) đúng chưa?
3. 26 nhóm N:1 + 3 ca BUG-038 (xem §3) — xử lý riêng sau, hay chặn T424?

## 3. Kết quả dry-run (đo được)

| Nhóm | Số | Ghi chú |
|---|---|---|
| Hồ sơ TTL non-alias | **1.054** | (tổng 1.511 − 457 alias) |
| `accepted` (khớp 1–1 rõ) | **794** | DILA ID chỉ 1 hồ sơ non-alias trỏ tới |
| `candidate` — N:1 | **54** | thuộc 26 DILA ID dùng chung |
| `candidate` — chưa có DILA ID | **204** | tạo `entity_hub(PERSON, 'ptda:<slug>')`, id 267007… |
| `candidate` — BUG-038 | **3** | `lam_te_nghia_huyen`, `ma_to_dao_nhat`, `hoang_ba_hy_van` (nằm trong nhóm 204) |
| Dòng alias (bỏ, chỉ báo cáo) | **457** | `docs/sessions/2026-10-19/T423/t423_alias_conflicts.tsv` |

**BUG-038 — đề xuất (chờ Admin):**
- `lam_te_nghia_huyen`: hiện A032162 (義玄 triều Joseon) → đề xuất **A003627** (Lâm Tế Nghĩa Huyền, Đường).
- `ma_to_dao_nhat`: hiện A038890 (道一/みちかず Nhật) → đề xuất **A003623** (馬祖道一).
- `hoang_ba_hy_van`: hiện rỗng → đề xuất **A000490** (希運); tên hiện 'Hơi Vận' sai, nên 'Hy Vận'.

**N:1 (26 nhóm)** — có ca là **cùng 1 người, 2 cách viết** cần Admin để ý:
- `A003636`: `phuc_chau_dai_an` | `phuoc_chau_dai_an` (Phúc/Phước — cùng người?).
- `A002188`: `da_da_xa_da` | `ma_ha_ca_diep` (Cùng Ma Ha Ca Diếp?).
- `A004981`: `phong_huyet_dien_chieu` | `nam_vien_hue_ngung` — theo T215, `phong_huyet_dien_chieu` ĐÚNG phải là A004982
  (風穴延沼), A004981 = 南院慧顒 (`nam_vien_hue_ngung`). ⇒ 1 trong 2 sai.
- (đầy đủ 26 nhóm: `t423_dry_run_report.txt`)

**Đối chiếu `ttl_mapping` (5 dòng verified):** `dai_hue_tong_cao`(A038686), `vien_ngo_khac_can`(A000453),
`duong_ki_phuong_hoi`(A004146), `bach_van_thu_doan`(A033489), `ngu_to_phap_dien`(A036842) — **tất cả đã nằm
trong nhóm 794 accepted** (không cần nạp riêng; xác nhận khớp, hết mâu thuẫn `verified` vs `pending`).

## 4. Cảnh báo bắt buộc

- **CHƯA ghi DB.** `--dry-run` mở `mode=ro`; không có INSERT/UPDATE/DELETE.
- Khi `--apply`: script tự backup SQLite API + `quick_check` trước; nếu `quick_check != ok` → **dừng**.
- **Cấp entity_id cho `ptda:`**: dùng `max(entity_id)+1 = 267007`. Nếu session khác ghi `entity_hub` giữa lúc này và lúc
  `--apply`, số sẽ lệch → script **đọc lại** `max(entity_id)` ngay trong `--apply` (không hard-code), nên an toàn.
- **UNIQUE partial index** `uq_esi_source_srcid_accepted` áp cho MỌI nguồn (không chỉ TTL_LOCAL). Hiện toàn bộ
  182.714 dòng là `candidate` → tạo index không xung đột. Nếu về sau nạp thêm `accepted` trùng khóa → lỗi (đúng ý đồ).
- `docs/sessions/2026-10-19/T423/` chứa TSV `utf-8-sig` — Excel mở đúng tiếng Việt.
- Vẫn còn WIP của phiên khác trong worktree; **không `git add -A`**.

## 5. Lệnh revert

```bash
python -X utf8 scripts/t423_register_ttl_source_mapping.py --revert --backup data/backups/T423_<ts>/lineage.db
```
Script lưu an toàn DB hiện tại → khôi phục từ backup → `DROP INDEX IF EXISTS uq_esi_source_srcid_accepted`.
| Task | Kiểu | Mất dữ liệu? |
|---|---|---|
| T423 | DB additive (thêm dòng) | Không — revert chỉ bỏ dòng đã thêm |

## 6. Bảng file tạo/sửa

| File | Hành động |
|---|---|
| `scripts/t423_register_ttl_source_mapping.py` | Tạo — script 3 chế độ |
| `docs/sessions/2026-10-19/T423/t423_entity_source_ids.tsv` | Tạo — 1.054 mapping |
| `docs/sessions/2026-10-19/T423/t423_entity_hub_new.tsv` | Tạo — 204 định danh ptda: |
| `docs/sessions/2026-10-19/T423/t423_alias_conflicts.tsv` | Tạo — 457 dòng alias |
| `docs/sessions/2026-10-19/T423/t423_dry_run_report.txt` | Tạo — báo cáo tổng hợp |
| `tasks/T423-register-ttl-source-and-mapping.md` | Sửa — status/outcome/checklist |
| `docs/tasktodo.md` | Sửa — dòng T423 |
| `docs/sessions/2026-10-19_T423-dang-ky-ttl-mapping.md` | Tạo — file này |

## 7. Bài học / sai lầm trong phiên

1. **PowerShell làm hỏng chuỗi `\"` trong `python -c`** (lỗi "Missing argument in parameter list")
   → chuyển sang ghi file `.py` tạm trong `%TEMP%\opencode` rồi chạy, tránh mọi vấn đề trích dẫn.
2. **Console PS 5.1 hiển thị "B?c Giang"** khi `Get-Content` đọc file utf-8-sig → **tưởng hỏng**, nhưng
   kiểm bằng `io.open(...,encoding='utf-8-sig')` thì bytes ĐÚNG. Không tin mắt qua console; kiểm bytes.
3. **Write tool hiện GHI ĐÚNG UTF-8** (đã test lại — khác ghi chú cũ trong memory). Có thể dùng Write trực tiếp cho
   file tiếng Việt; chỉ cần tránh đọc lại qua `Get-Content` mặc định.
4. Sót code chết trong `apply_db` (gán `hub_rows` 2 lần, biểu thức `s_ if False else src_`) → đã dọn trước khi chạy.

## 8. Việc CHƯA xong (ưu tiên)

1. **[Admin]** duyệt `--apply` cho T423 (+ trả lời 3 câu §2).
2. **[Admin]** xử lý 26 nhóm N:1 + 3 ca BUG-038 (task riêng?).
3. `daoanh-qa` kiểm độc lập sau khi ghi DB.
4. claude-mem vẫn down (`127.0.0.1:37700` connection refused).

## 9. Lệnh kiểm tra nhanh

```bash
# Chạy lại dry-run (phải ra: accepted 794 / candidate 260 / new_local 204 / n1 26)
python -X utf8 scripts/t423_register_ttl_source_mapping.py --dry-run

# Xác nhận DB CHƯA đổi (TTL_LOCAL phải chưa có)
python -X utf8 -c "import sqlite3;c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);print(c.execute(\"SELECT COUNT(*) FROM data_sources WHERE source_code='TTL_LOCAL'\").fetchone()[0]);print(c.execute(\"SELECT COUNT(*) FROM entity_hub WHERE canonical_label LIKE 'ptda:%'\").fetchone()[0])"
```

Kết quả mong đợi: `0` và `0` (chưa ghi DB).

## 10. Ghi chú cho agent kế tiếp

1. **`--apply` chỉ chạy sau khi Admin duyệt rõ.** Trước khi chạy, xác nhận lại `max(entity_id)`.
2. Sau `--apply`: verify count `TTL_LOCAL` = 1.054, `ptda:` = 204, index tồn tại; ghi backup path vào `docs/ROLLBACK.md`.
3. T424 (nạp cạnh TTL vào `lineage_edge_assertions`) phụ thuộc T423 đã apply. Nhắc: bảng đó đã có UNIQUE index
   `uq_lea_src_pair` (T422) → INSERT phải idempotent.

## 11. CẬP NHẬT 2026-10-20 — ĐÃ `--apply` (Admin duyệt)

Admin chốt: (1) duyệt `--apply` ngay; (2) 204 định danh `ptda:` giữ `candidate`; (3) 26 nhóm N:1 + 3 ca BUG-038
**tách task riêng** (chưa sửa `dila_id`).

**Kết quả ghi DB (verify độc lập, `mode=ro`):**

| Hạng mục | Giá trị |
|---|---|
| Backup | `data/backups/T423_20261020_071129/lineage.db` (quick_check=ok) |
| `data_sources` | +1 `TTL_LOCAL` (source_id 15) |
| `entity_hub` | +204 `PERSON/active` `ptda:<slug>` (entity_id 267007–267210) |
| `entity_source_ids` | +1.054 `source='TTL_LOCAL'` (794 accepted / 260 candidate); 1.054 distinct src id |
| Index | `uq_esi_source_srcid_accepted` UNIQUE PARTIAL `WHERE match_status='accepted'` |
| `accepted` trùng khóa | **0** |
| `quick_check` | **ok** |

**Revert:** xem `docs/ROLLBACK.md` §T423 (`--revert --backup data/backups/T423_20261020_071129/lineage.db`).

**Còn treo (task riêng):** 26 nhóm N:1 (54 slug) + 3 ca BUG-038 (`lam_te_nghia_huyen`→A003627,
`ma_to_dao_nhat`→A003623, `hoang_ba_hy_van`→A000490) — hiện là `candidate`.

