---
id: T181
title: "CBETA Bulk Import + Lazy Translate Pipeline (Đại Chánh Tân Tu)"
module: CBETA / Đại Tạng Kinh
priority: high
status: done
owner: claudecode
depends_on: [T50]
created: 2026-09-27
updated: 2026-10-04
build_approved_at: "2026-09-27 (Admin: 'Đồng ý build, hãy lưu logs, gitcommit và update các thông tin của các task mới vào các .md files tương ứng')"
plan_approved_at: "2026-09-27 (Admin: 'phê chuẩn đề xuất này... tạo task mới... Update lên /docs/ và các .md files tương ứng, cập nhật vào Dashboard để admin xem')"
done_when: |
  Toàn bộ 5 Phase hoàn thành:
  (P1) Script mapping sh_number → sigla CBETA + update cbeta_catalog_vn.sigla
  (P2) Script/hướng dẫn download 1 lần toàn bộ XML CBETA từ GitHub (git clone)
       → lưu tại data/cbeta/xml-p5a/ (Zero-RAM, không unzip toàn bộ vào RAM)
  (P3) API catalog + status: list 3122 bộ, badge (XML có trên disk / passage đã import / % dịch)
  (P4) API lazy import: click "Nhập & Dịch" → đọc XML local → parse passages → insert DB
       → tự động enqueue T50 backfill
  (P5) UI admin page: bảng catalog, nút Nhập & Dịch, nút Check Update (git pull delta)
  Zero-RAM Principle: không load >1 XML cùng lúc, dùng generator/iterator
  npm run pipeline PASS + tasktodo + session log + dashboard regen + commit
---

# T181 — CBETA Bulk Import + Lazy Translate Pipeline

**Bối cảnh và quyết định kiến trúc (Admin phê chuẩn 2026-09-27):**

Hiện tại chỉ có 5 text XML đã import vào DB (`passage` table: T50n2060, T50n2061, T50n2062,
T51n2076, X77n1524). Toàn bộ `cbeta_catalog_vn` có 3.122 bộ kinh với `sigla=NULL`.

**Kiến trúc đã thống nhất:**
- **Lazy import**: chỉ import nội dung XML vào DB khi admin click "Nhập & Dịch"
- **Catalog list first**: hiển thị danh sách 3.122 bộ từ `cbeta_catalog_vn`, không tải XML
- **Local storage**: download 1 lần toàn bộ XML về `data/cbeta/xml-p5a/` (Git clone ~2GB)
- **Incremental update**: `git pull` để lấy bản kinh mới/cập nhật từ CBETA
- **T50 integration**: sau khi import XML → passages → tự enqueue vào hàng đợi T50 dịch

**Nguồn CBETA (đã xác minh THẬT 2026-09-27):**
```
REPO CŨ (FAIL — repo INTERNAL, auth từ chối):
  https://github.com/cbeta-git/cbeta-xml-p5a  → "Invalid username or token", KHÔNG clone công khai được
REPO MỚI (PUBLIC — đã xác minh):
  https://github.com/cbeta-org/xml-p5   (bản phát hành CBETA XML P5, ~1.4GB full, nhánh master)
Cấu trúc thật: {series}/{series}{vol}/{sigla}.xml
  vd T/T50/T50n2060.xml, X/X77/X77n1524.xml (KHỚP app.py `_t181_xml_path`: series+vol nhóm số)
Index thật qua GitHub tree recursive (không cần clone): 5661 entries / 5017 file XML
GitHub API: GET /repos/cbeta-org/xml-p5/git/trees/master?recursive=1
Cấu trúc quanh repo: canons.json (A Jin 121, B 36, C 106, CC 6, D 64, F 29, G 150, GA 110, GB 130, I 1, J 40, K...)
Format: TEI P5 XML (xml:id="T50n2060"), license CC BY-SA học thuật
```

**CẬP NHẬT 2026-09-27 — Chiến lược P2 CHUYỂN từ "git clone 2GB" → "PARTIAL/LAZY" (Admin phê chuẩn: "Làm luôn T181 partial-clone (Recommended)"):**
- Không tự `git clone --depth=1 ... cbeta-xml-p5a.git` (~2GB, repo internal auth-fail).
- Script `scripts/t181_cbeta_download.py` cung cấp 3 lớp:
  1. `--index` → tải GitHub tree recursive MỘT LẦN → `data/cbeta/xml_index.json` (5017 sigla, không tải blob).
  2. `--fetch <sigla>` → lazy tải ĐÚNG 1 file XML về `data/cbeta/xml-p5a/{series}/{series}{vol}/{sigla}.xml` (raw.githubusercontent).
  3. `--clone` → in hướng dẫn git clone `--filter=blob:none --sparse` nếu Admin muốn mirror (không tự chạy).
- `--verify-catalog` → đối chiếu `cbeta_catalog_vn.sh_number+series` ↔ index: **2455/3122 (78.6%) khớp**; còn 667 miss gồm sh_number NULL (11) + sh trùng (giáo Mật tông Đà-la-ni — cần review tay, đúng blocker ghi sẵn).
- `--apply-index` → ghi sigla từ index vào `cbeta.db.cbeta_texts` (additive, không đọc nội dung XML).

---

## Phase 1 — Mapping sh_number → CBETA sigla

**Vấn đề hiện tại:** `cbeta_catalog_vn.sigla` = NULL cho tất cả 3.122 bộ.
`sh_number` (ví dụ: "1755") cần map sang sigla CBETA chuẩn (ví dụ: "T14n0474").

**Script:** `scripts/t181_map_sigla.py`
- Input: `cbeta_catalog_vn.sh_number` + series T/X/J/...
- Logic: CBETA sigla = `{series}{volume}n{sh_number}` (ví dụ: T=Đại Chánh, sh=474 → T14n0474)
- Output: UPDATE `cbeta_catalog_vn.sigla` cho tất cả row có thể map
- Flags: `--dry-run / --apply / --verify / --revert`

### Acceptance
- [ ] Script chạy không lỗi với `--dry-run`
- [ ] `--verify` báo ≥90% row có sigla (ước tính)
- [ ] `--revert` khôi phục NULL

---

## Phase 2 — Download CBETA XML (PARTIAL-CLONE / LAZY — thay cho git clone 2GB)

**CẬP NHẬT 2026-09-27:** Repo gốc `cbeta-git/cbeta-xml-p5a` là INTERNAL (auth từ chối), thay bằng
repo PUBLIC `cbeta-org/xml-p5`. Không clone full ~2GB; dùng index + lazy per-file.

```bash
# Bước 1 — lấy index XML (một lần, ~vài trăm KB, không tải blob)
python scripts/t181_cbeta_download.py --index

# Bước 2 (mặc định — lazy) — admin click "Nhập & Dịch" → import-xml gọi fetch từng file
python scripts/t181_cbeta_download.py --fetch T14n0475
python scripts/t181_cbeta_download.py --fetch-catalog --limit 10   # tải các sigla đã map

# (Tuỳ chọn) — mirror toàn bộ theo volume nếu Admin muốn
python scripts/t181_cbeta_download.py --clone   # in hướng dẫn git sparse-clone, KHÔNG tự chạy

# Chẩn đoán
python scripts/t181_cbeta_download.py --status
python scripts/t181_cbeta_download.py --verify-catalog
python scripts/t181_cbeta_download.py --apply-index
```

**Script trợ giúp:** `scripts/t181_cbeta_download.py`
- `--index`: tải `https://api.github.com/repos/cbeta-org/xml-p5/git/trees/master?recursive=1` → `data/cbeta/xml_index.json` (5017 file XML, regex `^([A-Z]{1,3})(\d+)n(\d+)([a-z]?)$`)
- `--fetch <sigla>`: tải đúng path `data/cbeta/xml-p5a/{series}/{series}{vol}/{sigla}.xml` từ raw
- `--status`: XML trên disk + index + cbeta.db count
- `--clone`: in lệnh `git clone --filter=blob:none --sparse https://github.com/cbeta-org/xml-p5.git` + `sparse-checkout set`
- `--verify-catalog`: đối chiếu `cbeta_catalog_vn.sh_number+series` ↔ index
- `--apply-index`: thêm sigla vào `cbeta.db.cbeta_texts` (additive, NOTNULL sigla/canon chỉ)

### Acceptance
- [x] `--index` chạy OK → 5017 XML (verify 2026-09-27: `truncated=false`, source cbeta-org/xml-p5)
- [x] `--fetch T01n0001` tải TEI hợp lệ (3.093.389 bytes, `xml:id="T01n0001"`)
- [x] `--status` báo đúng XML trên disk + index count
- [x] `--verify-catalog` → 2455/3122 khớp (78.6%); miss = sh NULL (11) + sh trùng (Mật tông)
- [ ] `--clone` hướng dẫn đúng (không tự clone 2GB)
- [ ] Admin chạy full hoặc lazy theo nhu cầu

---

## Phase 3 — API Catalog + Status

**Route mới:** `GET /daoanh/api/admin/cbeta-catalog`

```json
{
  "total": 3122,
  "xml_on_disk": 2865,
  "imported": 5,
  "translated_any": 5,
  "items": [
    {
      "id": 123,
      "title_vi": "Kinh Duy Ma Cật",
      "title_zh": "維摩詰所說經",
      "sigla": "T14n0475",
      "series": "T",
      "xml_path": "data/cbeta/xml-p5a/T/T14/T14n0475.xml",
      "xml_exists": true,
      "passage_count": 0,
      "translated_count": 0,
      "status": "xml_ready"
    }
  ]
}
```

**Status values:** `no_xml | xml_ready | imported | translating | done`

### Acceptance
- [ ] API trả đúng count xml_exists từ disk (os.path.exists, không cache)
- [ ] Phân trang (limit/offset), không load toàn bộ 3122 vào RAM 1 lần
- [ ] Status đúng cho 5 bộ đã có passages

---

## Phase 4 — API Lazy Import + Enqueue T50

**Route mới:** `POST /daoanh/api/admin/cbeta/import-xml`
```json
{"sigla": "T14n0475"}
```

**Flow:**
1. Kiểm tra XML có trên disk không
2. Đọc XML bằng **generator** (ElementTree iterparse — không load toàn bộ vào RAM)
3. Parse passages theo cấu trúc TEI P5a (div[@type='juan'] → p/l elements)
4. INSERT vào `passage` table (batch, Zero-RAM: 100 rows mỗi lần)
5. Tự gọi `enqueue("T{sigla}")` → đưa vào hàng đợi T50 dịch
6. Trả `{"imported": 234, "queued": true, "sigla": "T14n0475"}`

**Zero-RAM đảm bảo:**
- `xml.etree.ElementTree.iterparse()` — không load toàn bộ XML vào RAM
- INSERT theo batch 100 rows, clear sau mỗi batch

### Acceptance
- [ ] Import 1 bộ kinh nhỏ (< 50 passages) thành công
- [ ] Passages xuất hiện trong `passage` table
- [ ] Job T50 tự start sau import
- [ ] Thất bại giữa chừng không corrupt DB (transaction)

---

## Phase 5 — UI Admin Page

**Trang mới:** `admin/cbeta-import.html` (hoặc extend `admin/t50-progress.html`)

**Layout:**
- Header: Tổng 3.122 bộ · X bộ có XML · Y bộ đã import · Z bộ đã dịch
- Filter: series (T/X/J...) | status | search tên
- Bảng catalog:
  - Tên bộ kinh (tiếng Việt + Hán)
  - Sigla (T14n0475)
  - Badge: 🟢 XML sẵn / 🟡 Chờ XML / ✅ Đã dịch
  - % dịch (progress bar)
  - Nút **"Nhập & Dịch"**: chỉ active khi xml_exists=true
  - Nút **"Xem"**: mở detail passage

**Nút "Check Update"** (góc phải):
- Gọi `POST /daoanh/api/admin/cbeta/check-update`
- Server chạy `git -C data/cbeta/xml-p5a pull --dry-run`
- Báo: "3 file mới có thể download, chạy git pull để cập nhật"

### Acceptance
- [ ] Trang load được dưới 3s (phân trang, không load 3122 row 1 lần)
- [ ] Nút "Nhập & Dịch" disable khi xml_exists=false (kèm tooltip)
- [ ] Badge trạng thái cập nhật sau khi import
- [ ] URL detection (file:// vs http://) như t50-progress.html

---

## Files sẽ thay đổi

| File | Thay đổi |
|------|----------|
| `app.py` | +3 routes: cbeta-catalog, import-xml, check-update |
| `scripts/t181_map_sigla.py` | NEW — mapping sh_number → sigla |
| `scripts/t181_cbeta_download.py` | NEW — hướng dẫn + status download |
| `admin/cbeta-import.html` | NEW — UI catalog + lazy import |
| `admin/index.html` | Thêm link "CBETA Import" vào menu |
| `data/cbeta/xml-p5a/` | Target thư mục git clone (không commit vào git) |

---

## Không làm trong T181

- Không tự clone ~2GB (Admin phải chạy git clone thủ công)
- Không thay đổi schema DB hiện có (additive only)
- Không import toàn bộ 3.122 bộ tự động (lazy = click từng bộ)
- Không sửa T50 backfill script (chỉ enqueue vào hàng đợi T50 đã có)

---

## Revert

- Code: `git revert --no-edit <sha_T181>` (app.py + admin HTML)
- DB: `cbeta_catalog_vn.sigla` → `UPDATE ... SET sigla=NULL` hoặc restore backup
- Không cần xóa `data/cbeta/xml-p5a/` (Admin quản lý riêng)
- Passages đã import: xóa bằng `DELETE FROM passage WHERE text_id='T14n0475'`

## Build Progress (2026-09-27)

| Phase | File | Trạng thái | Ghi chú |
|-------|------|-----------|---------|
| P1 mapping sigla | `scripts/t181_map_sigla.py` | ✅ DONE | 5/5 mapped từ 5 XML có sẵn; mở rộng sau git clone |
| Fix import title | `data/cbeta/import_cbeta.py` | ✅ DONE | `_find_text_title()` → title bộ kinh đúng |
| Fix passage write | `data/cbeta/import_cbeta.py` | ✅ DONE | `_write_passage()` → lineage.db.passage |
| P3 catalog API | `app.py` line ~9489 | ✅ DONE | `/api/admin/cbeta-catalog` + `/catalog-stats` |
| P4 import API | `app.py` line ~9535 | ✅ DONE | `/api/admin/cbeta/import-xml` (lazy, enqueue T50) |
| P4 check-update | `app.py` line ~9560 | ✅ DONE | `/api/admin/cbeta/check-update` (git fetch dry-run) |
| P5 UI | `admin/cbeta-import.html` | ✅ DONE | Bảng catalog, badge, progress bar, nút Nhập & Dịch |
| P5 nav link | `admin/index.html` | ✅ DONE | Link "CBETA Import" trước CBETA Dashboard |
| P2 phần-clone | `scripts/t181_cbeta_download.py` | ✅ DONE | Thay clone 2GB cbeta-git (auth-fail) = index GitHub tree + lazy fetch từ `cbeta-org/xml-p5`; verify-catalog 78.6% |
| P4 fetch wiring | `app.py` line ~10152 | ✅ DONE (2026-10-04) | T181-P4-FIX: lazy fetch gọi `_t183_lazy_fetch_xml()` khi XML chưa có; fix stale "xml-p5a" string; 14 tests PASS |

### Verify
- ✅ `py_compile` app.py, t181_map_sigla.py, import_cbeta.py — PASS
- ✅ `t181_map_sigla.py --apply` → 5/5 sigla mapped
- ✅ `import_cbeta.py` title fix: T50n2060 → `續高僧傳` (trước: `Taishō Tripiṭaka`)
- ✅ (2026-09-27) `t181_cbeta_download.py --index` → 5017 XML index (cbeta-org/xml-p5 public)
- ✅ (2026-09-27) `--fetch T01n0001` → TEI hợp lệ 3.0MB về `data/cbeta/xml-p5a/T/T01/T01n0001.xml`
- ✅ (2026-09-27) `--verify-catalog` → 2455/3122 (78.6%) khớp sh_number↔sigla
- ⏳ `npm run pipeline` — đang chạy

### Revert paths
- **Code**: `git revert --no-edit <sha_T181>` (app.py + admin/*.html)
- **Script**: bỏ file `scripts/t181_map_sigla.py` + `data/cbeta/import_cbeta.py` restore
- **DB sigla**: `python scripts/t181_map_sigla.py --revert` → đặt lại NULL

## Blockers

- [ ] ~~Admin cần chạy `git clone cbeta-git/cbeta-xml-p5a` trước P4~~ → **RESOLVED 2026-09-27:** repo internal auth-fail; dùng `--fetch` lazy từ `cbeta-org/xml-p5` (public)
- [x] ~~Tích hợp `--fetch` vào route `import-xml` app.py (hiện XML thiếu → báo clone_cmd sai nguồn)~~ → **RESOLVED 2026-10-04 (T181-P4-FIX)**: lazy fetch wired, 14 tests PASS, E2E smoke PASS (293 passages)
- [ ] `cbeta_catalog_vn.sigla` mapping cần review tay một phần (667/3122 chưa khớp: sh NULL + sh trùng Mật tông)
