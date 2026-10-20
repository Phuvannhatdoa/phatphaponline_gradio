# Session 2026-09-27 — T181 CBETA Bulk Import + Lazy Translate Pipeline

## Quyết định kiến trúc (Admin phê chuẩn)

**Bối cảnh:** Hiện chỉ có 5 text XML đã import (T50n2060/2061/2062, T51n2076, X77n1524).
`cbeta_catalog_vn` có 3.122 bộ với `sigla=NULL`.

**Kiến trúc đã thống nhất với Admin:**

| Điểm | Quyết định |
|------|-----------|
| Download | 1 lần `git clone cbeta-git/cbeta-xml-p5a` → `data/cbeta/xml-p5a/` (~2GB) |
| Update | Định kỳ `git pull` để lấy bản kinh mới |
| Import | Lazy: chỉ import XML vào DB khi admin click "Nhập & Dịch" |
| Dịch | Sau import → tự enqueue vào hàng đợi T50 → Groq dịch |
| Zero-RAM | ElementTree `iterparse()` — không load toàn bộ XML vào RAM |

**CBETA source:**
- GitHub: `https://github.com/cbeta-git/cbeta-xml-p5a` (public, CC BY-SA)
- Format TEI P5a, tổ chức theo series T/X/J/...
- Download bằng `git clone --depth=1` (~2GB), update bằng `git pull`

## Task tạo mới

**T181** — `tasks/T181-cbeta-bulk-import-lazy-translate.md`
- Status: `pending`
- Module: CBETA / Đại Tạng Kinh
- Depends on: T50 (hàng đợi dịch đã có)
- 5 phases: mapping sigla → download guide → catalog API → import API → UI

## Files thay đổi phiên này

| File | Loại | Mô tả |
|------|------|-------|
| `scripts/t181_map_sigla.py` | NEW | P1 mapping sh_number → sigla từ XML filenames |
| `data/cbeta/import_cbeta.py` | FIX | title_zh dùng `<title level="m">` + `_write_passage()` |
| `app.py` | NEW routes | `/api/admin/cbeta-catalog`, `/cbeta/import-xml`, `/cbeta/check-update`, `/cbeta/catalog-stats` |
| `admin/cbeta-import.html` | NEW | UI catalog + import + check update |
| `admin/index.html` | UPDATE | Thêm link "CBETA Import" |
| `tasks/T181-cbeta-bulk-import-lazy-translate.md` | UPDATE | status in_progress + Build Progress |
| `docs/tasktodo.md` | UPDATE | T181 entry |
| `data/progress_data.json` | REGEN | 97 tasks, done=71, 71% |

## Verify kết quả build

- ✅ `py_compile` app.py, t181_map_sigla.py, import_cbeta.py — PASS
- ✅ `t181_map_sigla.py --apply` → 5/5 sigla mapped
- ✅ `import_cbeta.py` title fix: T50n2060 → `續高僧傳`
- ✅ `pytest test_t178 test_t179 test_t167` — 13/13 PASS (không regression)
- ⚠️ `npm run pipeline` FAIL ở `audit:t166` — đây là bug PRE-EXISTING T166-bio-edit-write-path-guard, không do T181

## Todo tiếp theo

- [ ] Build P1: script mapping sh_number → sigla (`scripts/t181_map_sigla.py`)
- [ ] Build P2: download guide script (`scripts/t181_cbeta_download.py`)
- [ ] Build P3: route `/daoanh/api/admin/cbeta-catalog` với status disk check
- [ ] Build P4: route `/daoanh/api/admin/cbeta/import-xml` (lazy, Zero-RAM)
- [ ] Build P5: `admin/cbeta-import.html` UI
- [ ] Admin: chạy `git clone --depth=1 https://github.com/cbeta-git/cbeta-xml-p5a.git data/cbeta/xml-p5a` (thủ công, ~2GB)
- [ ] Git commit tất cả T50+T181 changes (blocked bởi git index anomaly — cần user confirm)
