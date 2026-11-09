# Handoff 2026-10-22 — T453: DILA authority_catalog tạng A + lớp dịch Việt (kèm T452 deferred)

## 1. Bảng đọc nhanh

| Mục | Giá trị |
|---|---|
| Ngày | 2026-10-22 |
| Task | T453 (in_progress) · T452 (deferred) |
| HEAD / git | Không chạy git (CLAUDE.md: không tự `git add/commit`). Chưa commit. |
| DB | **Có ghi** (Admin duyệt "A"): 3 bảng mới + 1 dòng `data_sources`. Backup `data/backups/lineage_t453_20261022_125818.db` |
| TTL | Không đụng |
| Test | dry-run + apply/revert trên DB tạm PASS; `npm run pipeline` **chưa chạy**; daoanh-qa **chưa chạy** |
| Dashboard | `python scripts/build_progress_data.py` đã chạy → T453/T452 có trên board |

## 2. Đọc trong 2 phút

- Đã tích hợp **DILA authority_catalog** (經錄規範資料庫; 5.747 bộ / 26 tạng; CC BY-SA 3.0) — bước đầu tạng **A** (9 bộ).
- Luồng Admin chốt: **Cloud session dịch** (free credit) → file `<tạng>.vi.json` về local → **coordinator import**. Tên người **DB thắng**.
- Phát hiện phụ: bảng `time_periods` (117.429 dòng) **sai toàn bộ** (năm cộng thừa 1970 + lệch cột + mất ~2.300 dòng do trùng id) → T452, Admin hoãn.
- **Admin cần làm:** (1) duyệt **(B)** search HOME; (2) gửi B.json, C.json… cho Cloud dịch bằng prompt; (3) quyết A000457 "Lã Dì Giản" khi chuẩn hoá tên.

## 3. Chi tiết từng task

### T453
- **Nguồn:** `data/dila_import/authority_catalog.2026-10/json/` — 27/27 file SHA256 trùng GitHub `DILA-edu/Authority-Databases` master (commit 2026-08-31).
- **Đo khớp (DB thật, mode=ro):** toàn catalog: người 2.218/2.221 khớp `people.id`; nơi dịch 112/112 khớp `places_dila.id`; `canon_catalog` khớp 2.376/3.122 theo mã T (590 không khớp ở Taishō q.56–85, 145 ở q.≤55, 11 không mã).
- **Bản dịch A:** `docs/sessions/2026-10-22/T453/A.vi.json` (output Cloud, 9/9; cùng khóa, thêm `*_vi/_src/_status/_note`).
- **Script:** `scripts/t453_dila_catalog_import.py` — `--stats/--dry-run/--apply/--revert`, `--canon`, `--db`. Ghép người/nơi chỉ theo ID; tên người lấy `people.name_vi`; `byline_vi` thay tên theo DB; lớp dịch đầy đủ lưu `vi_json`.
- **Kết quả apply:** works 9 · contributors 10 (10/10 có name_vi DB) · places 0 · data_sources `DILA_CATALOG` id 16.
- **Lệch tên (đã dùng DB, ghi `note`):** A001713 dịch "Huệ Uyển" / DB "Tuệ Uyển"; A000457 dịch "Lã Di Giản" / DB "Lã Dì Giản".
- **Năm:** 9/9 = khung triều đại (Đường 618–907, Tống 960–1279) ⇒ `year_precision='dynasty_range'`.

### T452 (deferred)
- `scripts/etl_time_authority.py`: `int((x-1721119)/365.25)+1970` + đọc `values[5]` (era_id) làm start, `values[6]` (first) làm end. Kiểm chứng dòng 3135: gốc `first=1732452` (năm 31 CN, 建武 7) → DB `start=-2742, end=2001`.
- Mất dòng: emperor 570/692, era 815/1.503, month 115.921/117.428 (chung `id` + `INSERT OR IGNORE`).
- Chi tiết + đề xuất: `tasks/T452-dila-time-authority-reimport.md`.

## 4. Cảnh báo bắt buộc

- ⚠ **Ghi vào `data/` bị chặn quyền với Claude** → file dịch nằm ở `docs/sessions/2026-10-22/T453/`, script đọc từ đó. Đừng chuyển file mà không sửa `VI_DIR` trong script.
- ⚠ **Mỗi `--apply` backup 1,65 GB** vào `data/backups/` — gom nhiều tạng nhỏ trước khi apply.
- ⚠ **Không ghép tác phẩm theo tên** (vd. 新譯華嚴經音義 trong canon_catalog là trước tác Nhật, khác A1057).
- ⚠ **Tên Việt trong bản dịch không phải nguồn sự thật** — `people.name_vi` (ZQ, confidence 0.5) mới dùng hiển thị; badge ZQLOCAL.
- ⚠ `time_periods` hiện **sai** — không dùng cho năm của catalog (catalog có sẵn `time_from/time_to` Tây lịch).
- Session song song: `tasktodo.md` dùng chung — đã chèn block `<!-- T453:START/END -->`, không đụng block khác.

## 5. Lệnh revert

| Việc | Lệnh | Mất dữ liệu? |
|---|---|---|
| T453 DB | `python -X utf8 scripts/t453_dila_catalog_import.py --revert` | Không (chỉ DROP bảng mới + xoá dòng DILA_CATALOG) |
| T453 khôi phục toàn DB | copy `data/backups/lineage_t453_20261022_125818.db` → `data/lineage.db` | Mất mọi ghi sau 12:58 — chỉ dùng khi cần |
| tasktodo / ROLLBACK | bản `.bak-before-T453` trong `docs/sessions/2026-10-22/T453/` | Không |

## 6. File tạo/sửa

| File | Loại |
|---|---|
| `tasks/T453-dila-catalog-a-import-vi.md` | mới |
| `tasks/T452-dila-time-authority-reimport.md` | mới (deferred) |
| `scripts/t453_dila_catalog_import.py` | mới |
| `docs/sessions/2026-10-22/T453/A.vi.json` | mới (output Cloud) |
| `docs/sessions/2026-10-22/T453/PROMPT-cloud-translate.md` | mới |
| `docs/sessions/2026-10-22/T453/*.bak-before-T453` | backup tasktodo, ROLLBACK |
| `docs/tasktodo.md` | thêm block T453 |
| `docs/ROLLBACK.md` | thêm mục T453 |
| `data/lineage.db` | +3 bảng, +1 dòng data_sources |

## 7. Sai lầm & bài học

- Tôi **tự dịch A.json** khi Admin muốn **Cloud session** dịch (để dùng free credit) → đã thay bằng output Cloud. Bài học: "Cloud session dịch" = đưa prompt, không tự làm.
- Tôi từng nêu "746 bộ không khớp phần lớn là kinh Nhật" **trước khi đo** — sau đo: 590 q.56–85 / 145 q.≤55 / 11 không mã. Bài học: đo trước khi nói.
- Script ban đầu ghi backup vào `data/backups/` cả khi `--db` trỏ DB tạm → đã xoá file backup tạm; nên sửa để backup cạnh `--db`.

## 8. Việc CHƯA xong (ưu tiên)

1. **(B) Search HOME** — sửa `app.py` `/daoanh/api/search` thêm works từ `dila_catalog_works` (badge DILA / Cloud draft / ZQLOCAL). **Chờ Admin duyệt.**
2. Tạng B…ZW: Admin gửi Cloud dịch → coordinator dry-run → Admin duyệt apply. Cân nhắc `--canon B,C,D`.
3. `npm run pipeline` + daoanh-qa kiểm độc lập → Admin xác nhận DONE.
4. A000457 "Lã Dì Giản" → task chuẩn hoá tên (ngoài T453).
5. T452 (deferred) — 3 câu hỏi Admin trong task file.

## 9. Lệnh kiểm tra nhanh

```bash
cd Dai_Tang_Kinh/daoanh
python -X utf8 scripts/t453_dila_catalog_import.py --stats        # 9 / 10 / 0
python -X utf8 scripts/t453_dila_catalog_import.py --dry-run --canon A
python -X utf8 -c "import sqlite3;c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);print(c.execute(\"select cbeta_id,title_vi,byline_vi from dila_catalog_works\").fetchall())"
npm run dup:ids
```

## 10. Ghi chú cho agent kế tiếp

- [ ] Đọc `tasks/T453-dila-catalog-a-import-vi.md` + block T453 trong `docs/tasktodo.md`.
- [ ] File dịch mới phải tên `<tạng>.vi.json` trong `docs/sessions/2026-10-22/T453/`.
- [ ] Luôn `--dry-run` trước, báo số + tên lệch; `--apply` chỉ khi Admin duyệt từng lô.
- [ ] Không sửa `people`/`places_dila`/`canon_catalog` trong T453.
- [ ] Sau mọi thay đổi: `python scripts/build_progress_data.py`.

---

## CẬP NHẬT 2026-10-22 chiều (đọc mục này trước)

- **Đã nạp ĐỦ 26 tạng: 5.747 bộ / 5.589 người / 765 nơi dịch.** QA độc lập (code đếm riêng): đúng 5.747, 0 lệch.
  Backup cuối `data/backups/lineage_t453_20261022_152039.db`. Revert `--revert`.
- Bản dịch Cloud ở `data/dila_import/authority_catalog.2026-10/vn_dila_authority_catalog/` (26 `*.vi.json`, prompt v4
  `docs/sessions/2026-10-22/T453/PROMPT-cloud-full-26.md`). Script `scripts/t453_dila_catalog_import.py` hỗ trợ
  `--canon ALL`, cổng QA (trống, "/", cụm Phật học, trường gốc), tự sửa 疏→Sớ + viết hoa; còn lỗi QA thì từ chối `--apply`.
- HOME `/daoanh/`: `/daoanh/api/search` thêm `dila_works`, `dila_people`; route `/daoanh/api/public/dila_works`;
  `index.html` thẻ người + "Xem tất cả" + badge DILA/AI/ZQ/"Chưa dịch". Backup code: `docs/sessions/2026-10-22/T453/*.bak-*`.
- Task con: **T454** (8 tên địa danh "_ Huý"), **T455** (chuẩn hoá tên người: 794 lệch DB, CSV
  `docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv`; 532 tên còn chữ Hán).
- Chưa làm: commit git (chờ lệnh); `npm run pipeline` vẫn đỏ ở audit:honesty:strict (lỗi có sẵn, không do T453);
  tab tác phẩm trên trang người, lớp bản đồ nơi dịch (đề xuất task sau); Admin xác nhận DONE T453.

## CẬP NHẬT 2026-10-22 16:10 — Deepsearch + task mới
- Đối chiếu web 5.747/5.747 OK (`docs/sessions/2026-10-22/T453/webqa/`). Thẻ kinh HOME: mỗi thông tin 1 dòng + biểu tượng; tổng kết quả thật.
- Task mới (pending): **T456** autocomplete HOME · **T457** DILA biographies nexus (năm + 4 sách) · **T458** Cloud dịch đoạn sự kiện ·
  **T459** SuttaCentral parallels. Lý do dịch AI thay vì dùng bản Việt lưu hành: bản quyền (LICENSE_FIREWALL) — xem T458.
- Báo cáo nguồn: `docs/sessions/2026-10-22/T453/DEEPSEARCH-next-sources.md`.
