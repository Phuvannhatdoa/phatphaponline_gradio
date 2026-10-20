# Session 2026-09-27 — T181 CBETA partial-clone: thay nguồn private bằng public + lazy fetch

## Bối cảnh
- T181 đang IN_PROGRESS, P1-P5 code đã xong (app.py routes + `admin/cbeta-import.html`), blocker duy nhất là **clone 2GB** `cbeta-git/cbeta-xml-p5a`.
- Khảo sát phát hiện: repo `cbeta-git/cbeta-xml-p5a` là **INTERNAL** — clone công khai bị từ chối (`Invalid username or token`, log `data/cbeta/clone_out.log`).
- Admin phê chuẩn: **"Làm luôn T181 partial-clone (Recommended)"** (lựa chọn từ câu hỏi).

## Việc đã làm

### 1. Xác minh nguồn CBETA PUBLIC
- `https://github.com/cbeta-org/xml-p5` — public, nhánh `master`, HEAD `dbdea41071e1e260ad84b72faefd4587333cf76d`, size ~1.4GB.
- `cbeta-org/cbeta-xml-p5` / `DILA-edu/cbeta-xml-p5` — KHÔNG tồn tại (timeout/404).
- Cấu trúc repo: `{canon}/{canon}{vol}/{sigla}.xml` — KHỚP `_t181_xml_path()` trong app.py.
- GitHub tree recursive API: 5661 entries, **5017 file XML**, `truncated=false` → có thể lấy index đầy đủ KHÔNG cần clone.

### 2. Script mới `scripts/t181_cbeta_download.py` (thay kế hoạch clone 2GB)
| Flag | Chức năng | Trạng thái test |
|------|-----------|-----------------|
| `--index` | Lấy GitHub tree recursive → `data/cbeta/xml_index.json` (5017 sigla) | ✅ 5017 XML |
| `--fetch <sigla>` | Tải 1 file XML theo sigla → `xml-p5a/{series}/{series}{vol}/{sigla}.xml` (lazy, Zero-RAM) | ✅ `T01n0001` 3.093.389 bytes, `xml:id="T01n0001"` |
| `--fetch-catalog` | Tải các sigla đã map trong cbeta_catalog_vn (giới hạn `--limit`) | ✅ smoke |
| `--status` | Báo XML trên disk + index count + cbeta.db import count | ✅ |
| `--verify-catalog` | Đối chiếu `cbeta_catalog_vn.sh_number+series` ↔ index | ✅ **2455/3122 = 78.6%** |
| `--apply-index` | Thêm sigla từ index vào `cbeta.db.cbeta_texts` (additive, NOT NULL sigla/canon) | ✅ schema khớp |
| `--clone` | In hướng dẫn `git clone --filter=blob:none --sparse` (không tự chạy) | ✅ |

### 3. Kết quả verify-catalog (miss 667/3122)
- **sh_number NULL**: 11 bộ (không map được qua index).
- **sh_number trùng**: giáo Mật tông Đà-la-ni (vd sh=974 có 6 bộ: Tối Thắng Phật Đảnh..., Phật Đảnh Tôn Thắng Đà La Ni...) — mapping 1:1 sh→sigla không đủ; cần review tay (đúng blocker ghi sẵn trong task).

### 4. App.py — KHÔNG đụng
- `app.py` có WIP agent khác (diff ~200/12 dòng nằm đúng vùng `t181_cbeta_catalog` L9514-9595 + L21885).
- `check-update` clone_cmd vẫn trỏ `cbeta-git/cbeta-xml-p5a` (sai nguồn) — **chưa sửa** để tránh conflict; đã ghi blocker trong task.

## Trạng thái dữ liệu local
- `data/cbeta/xml-p5a/`: 6 XML (5 cũ + T01n0001 mới), KHÔNG có `.git`.
- `data/cbeta/xml-p5a-manual-backup/`: backup 5 XML cũ (T/, X/) — giữ nguyên.
- `data/cbeta/xml_index.json` (mới): 5017 file, source cbeta-org/xml-p5.

## Update 2026-09-27 (tiếp theo phiên sau)

### ✅ git clone --depth=1 cbeta-org/xml-p5 THÀNH CÔNG

- Clone `https://github.com/cbeta-org/xml-p5.git` → `data/cbeta/xml-p5-full/` (depth=1)
- **2.6GB, 5017 XML files** — toàn bộ đại tạng offline
- Cấu trúc: `xml-p5-full/{SERIES}/{SERIES}{vol}/{sigla}.xml` — khớp hoàn toàn `_t181_xml_path()` trong app.py
- `app.py` line 9494: `_T181_XML_ROOT` đã đổi sang `data/cbeta/xml-p5-full`

### Trạng thái hiện tại
- `data/cbeta/xml-p5-full/`: **2.6GB full clone**, có `.git` (depth=1)
- `data/cbeta/xml-p5a/`: 6 XML cũ (backup thủ công) — vẫn giữ
- Batch import (`/api/admin/cbeta/batch-import`) sẵn sàng hoạt động với toàn bộ corpus

## Update 2026-09-27 (T183 — lazy-fetch fallback)

### Vấn đề 20% thiếu XML
- 583 bộ thiếu (sh_number 2185-2731) thuộc **volumes T56-T84**
- Repo public `cbeta-org/xml-p5` chỉ có **T01-T55 + T85** — T56-T84 chưa được phát hành XML public do copyright Nhật Bản
- **BM_u8** (Basic Markup, cbeta-org) cũng chỉ T01-T55+T85

### Giải pháp đã implement (app.py)
- Hàm `_t183_lazy_fetch_xml(sigla)` (gần _t181_xml_path, có comment đầy đủ):
  - T01-T55/T85: download từ GitHub raw → cache local → import
  - T56-T84: skip với message hướng dẫn thủ công chi tiết
- Route `t182_batch_import`: gọi `_t183_lazy_fetch_xml` khi không có XML local

### Hướng dẫn thủ công để hoàn thiện T56-T84 (khi cần trong tương lai)
1. Vào https://cbeta.org/download
2. Tải "CBReader 2X v0.9.9.2 經文資料檔" (bookcase_v0992_20260831.zip, 1.21 GB)
3. Giải nén → tìm thư mục XML T56-T84
4. Copy vào `data/cbeta/xml-p5-full/T/` theo cấu trúc `T56/T56n{num}.xml`
5. Chạy lại batch-import → tự động tìm được

## Workflow tiếp theo
1. Commit toàn bộ T181+T182+T183+t50-integration
2. Chạy batch import series T theo thứ tự sh_number để bắt đầu dịch
3. T56-T84: xử lý thủ công khi có nhu cầu thực tế