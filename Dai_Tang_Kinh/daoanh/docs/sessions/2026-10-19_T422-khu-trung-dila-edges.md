# Session 2026-10-19 — T422: khử trùng cạnh DILA (46.006 → 23.014) + UNIQUE index

> Phiên này cũng hoàn tất **T410** (màu nét theo nguồn) — commit `7b787e8`. Log T410:
> `docs/sessions/2026-10-19_T410-mau-theo-nguon.md`.

## 1. Thông tin đọc nhanh

| Hạng mục | Giá trị |
|---|---|
| Task | T422 (`tasks/T422-dila-edge-dedupe-unique.md`) — bước 1/5 của "3 cây" |
| HEAD trước phiên | `eb5bf9e3e320b34dfb0dbdf20de457bb9ee70da3` |
| HEAD sau T410 | `7b787e8` (T410/BUG-035) |
| File code | `scripts/t422_dedupe_dila_edges.py` (mới), `scripts/t422_screenshot.js` (mới) |
| DB | `data/lineage.db` — **CÓ ghi** (DELETE + CREATE UNIQUE INDEX) |
| Backup DB | `data/backups/T422_20261019_201110/lineage.db` (1.535,6 MB, quick_check OK) |
| Trạng thái | Đã ghi DB + verify; chờ `daoanh-qa` + Admin DONE |
| Kết quả | DILA 46.006 → **23.014**; MARCUS **11.169** không đổi; TOTAL 34.183 |

## 2. Đọc trong 2 phút

Khử trùng cạnh DILA: mỗi cặp thầy–trò bị lưu 2 lần. Đã xoá 22.992 dòng dư và thêm UNIQUE index
để chặn trùng về sau. **Phát hiện quan trọng:** mọi dòng trùng **giống hệt nhau ở tất cả các cột trừ `id`** —
nên thao tác an toàn tuyệt đối (không mất thông tin nào), và cây truyền thừa **giữ nguyên 100%**
(bằng chứng: 6/6 ảnh trước/sau pixel-identical).

Ba việc Admin cần làm:
1. Giao `daoanh-qa` kiểm độc lập T422.
2. Xác nhận DONE → đổi `status: done`, rồi sang **T423** (đăng ký TTL_LOCAL + mapping).
3. Quyết định gộp `T419`/`T420` (trùng BUG-041) — vẫn treo từ phiên trước.

## 3. Đề suất phần chữa (root cause + cách sửa)

**Vấn đề:** `lineage_edge_assertions` lưu DILA mỗi cặp thầy–trò 2 dòng (46.006 dòng / 23.014 cặp).
Không có ràng buộc chống trùng → nguồn nạp lại sẽ nhân bản tiếp.

**Cách sửa (script `scripts/t422_dedupe_dila_edges.py`):**
- Khóa trùng: `(source_code, subject_person_id, object_person_id, relation_type)`.
- Giữ dòng `id` nhỏ nhất; gộp `ref` nếu các dòng trong nhóm khác ref (đo được: **0 nhóm** cần gộp).
- `--dry-run` (chỉ đọc, `mode=ro`) → TSV + báo cáo; `--apply` → backup API + quick_check → DELETE → UNIQUE index;
  `--revert --backup <...>` → khôi phục + DROP index.

**Bằng chứng đo được:**

| Chỉ số | Trước | Sau |
|---|---|---|
| DILA rows | 46.006 | **23.014** |
| DILA distinct pairs | 23.014 | 23.014 |
| MARCUS rows | 11.169 | **11.169** (không đổi) |
| TOTAL | 57.175 | 34.183 |
| Nhóm trùng | 22.992 | **0** |
| UNIQUE index | không có | `uq_lea_src_pair` (unique=1) |

- API `/daoanh/api/monk/A003623/lineage-tree` → **200** (415 edges / 416 nodes).
- **6/6 ảnh TRƯỚC (T410) vs SAU (T422)** cho A004980/A009460/A047924 × dark/light = **PIXEL-IDENTICAL** (0 px khác, `PIL.ImageChops`).
- Spot-check 3 cặp từ TSV đều còn đúng 1 dòng.

## 4. Cảnh báo bắt buộc

- **DB đã đổi thật.** Bảng `lineage_edge_assertions` giờ chỉ còn 23.014 dòng DILA. Mọi script đọc bảng này
  phải chịu được việc **không còn dòng trùng** (trước đây có thể đã "quen" với 2 dòng/cặp).
  Nếu phát hiện chỗ nào đếm sai do giả định 46.006 → báo ngay.
- **`data/backups/T422_20261019_201110/lineage.db` là 1,5 GB** và **đã bị gitignore** (`data/backups/*.db`).
  Không commit; nếu dọn ổ đĩa thì phải giữ lại cho tới khi Admin DONE.
- **UNIQUE index `uq_lea_src_pair` giờ chặn INSERT trùng.** Bất kỳ script nạp cạnh DILA nào
  (kể cả T424 nạp cạnh TTL nếu dùng cùng khóa) phải dùng `INSERT OR IGNORE` / `ON CONFLICT`, nếu không sẽ lỗi.
- **`npm` shim hỏng** → chạy node thẳng: `& "C:\Program Files\nodejs\node.exe" scripts/...`.
- **PowerShell here-string làm hỏng tiếng Việt** khi chạy `-File`. Dùng `Set-Content -Value ... -Encoding UTF8`
  chạy thẳng trong lệnh, hoặc Python/`edit`.
- Phiên song song: worktree vẫn còn WIP chưa commit của T411/T418/T419/T421. **Không `git add -A/-u`.**
- `docs/tasktodo.md` và `docs/ROLLBACK.md` là file dùng chung — có WIP của phiên khác.

## 5. Lệnh revert

```bash
# 1 lệnh, tự lưu an toàn DB hiện tại rồi khôi phục:
python -X utf8 scripts/t422_dedupe_dila_edges.py --revert --backup data/backups/T422_20261019_201110/lineage.db
```

| Task | Kiểu | Mất dữ liệu? |
|---|---|---|
| T422 | DB additive/xoá-dòng-trùng | **Không** — backup là bản đầy đủ 46.006 dòng; dòng bị xoá byte-identical |

## 6. Bảng file tạo/sửa

| File | Hành động |
|---|---|
| `scripts/t422_dedupe_dila_edges.py` | Tạo — script khử trùng (--dry-run / --apply / --revert) |
| `scripts/t422_screenshot.js` | Tạo — chụp ảnh SAU khử trùng (Playwright/Edge) |
| `tasks/T422-dila-edge-dedupe-unique.md` | Sửa — outcome + checklist |
| `docs/tasktodo.md` | Sửa — dòng T422 → ĐÃ GHI DB |
| `docs/ROLLBACK.md` | Sửa — thêm mục T422 |
| `docs/sessions/2026-10-19/T422/t422_duplicate_groups.tsv` | Tạo — 22.992 nhóm trùng |
| `docs/sessions/2026-10-19/T422/t422_dry_run_report.txt` | Tạo — báo cáo dry run |
| `docs/sessions/2026-10-19/T422/t422_after_*.png` (6 ảnh) | Tạo — ảnh SAU khử trùng |
| `docs/sessions/2026-10-19/T422/t422-screenshot-probe.json` | Tạo — probe DOM |
| `docs/sessions/2026-10-19_T422-khu-trung-dila-edges.md` | Tạo — file này |
| `data/backups/T422_20261019_201110/` | Tạo — backup DB (gitignored) |

## 7. Bài học / sai lầm trong phiên

1. **Đoán tên cột sai:** viết `assertion_id` trong khi bảng dùng `id` → `sqlite3.OperationalError`.
   Luôn `PRAGMA table_info` trước khi viết truy vấn.
2. **Thử "tách hunk" để commit riêng T410:** định dựng lại file từ HEAD + chỉ hunk của mình.
   **Sai** — unified diff trộn dòng `+`/`-` xen kẽ, lấy riêng `+` sẽ hỏng file. Đã bỏ cách này, chuyển sang
   commit chung (Admin đã chấp nhận).
3. **Quên sync index thật sau temp-index commit:** `git commit` bằng `GIT_INDEX_FILE` không cập nhật
   `.git/index` thật → `git diff --cached` sau đó hiện `M`/`D` sai (index còn ở HEAD cũ). Nguy hiểm:
   session khác chạy `git commit` sẽ **revert mất commit của mình**. Đã sửa bằng `git reset` (mixed).
   **Bài học: sau mỗi temp-index commit PHẢI chạy `git reset` (hoặc `git read-tree HEAD` vào index thật).**
4. **Đọc ảnh không được** (model không xem được ảnh) → dùng pixel-diff số học (`PIL.ImageChops`) thay vì "nhìn".

## 8. Việc CHƯA xong (ưu tiên)

1. `daoanh-qa` kiểm độc lập T422.
2. Admin xác nhận DONE T422 → `status: done`.
3. Sang **T423** (đăng ký TTL_LOCAL + người `ptda:` + mapping TTL — dry-run trước).
4. Gộp `T419`/`T420` (cùng BUG-041).
5. claude-mem vẫn down (`127.0.0.1:37700` connection refused).

## 9. Lệnh kiểm tra nhanh

```bash
# 1. Counts + không còn trùng
python -X utf8 -c "import sqlite3;c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);print(c.execute(\"SELECT source_code,COUNT(*) FROM lineage_edge_assertions GROUP BY 1\").fetchall())"

# 2. Index tồn tại
python -X utf8 -c "import sqlite3;c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);print([r[1] for r in c.execute('PRAGMA index_list(lineage_edge_assertions)')])"

# 3. Dry-run lại (phải ra 0 nhóm trùng)
python -X utf8 scripts/t422_dedupe_dila_edges.py --dry-run
```

Kết quả mong đợi: DILA=23014, MARCUS=11169; index có `uq_lea_src_pair`; dry-run 0 nhóm trùng.

## 10. Ghi chú cho agent kế tiếp

1. **T423 là task kế tiếp** — cũng cần dry-run trước, Admin duyệt rồi mới ghi DB.
2. **Từ giờ mọi INSERT cạnh vào `lineage_edge_assertions` phải idempotent** (`INSERT OR IGNORE` /
   `ON CONFLICT DO NOTHING`) vì đã có UNIQUE index `uq_lea_src_pair`.
3. **Sau temp-index commit phải `git reset`** để đồng bộ `.git/index` thật (xem bài học 7.3).
4. Backup cho revert: T410 = `git revert 7b787e8`; T422 = `scripts/t422_dedupe_dila_edges.py --revert`.
5. Giữ `data/backups/T422_20261019_201110/` cho tới khi Admin DONE.

