# CODER REPORT — T290 (M5 — Sinh credits.html từ data_sources)

- **Ngày:** 2026-11-01
- **Agent:** coder (harness Đạo Ảnh)
- **Task:** `tasks/T290-m5-credits-tu-data-sources.md`
- **Trạng thái sau khi làm:** `coding` → **`testing`** (chờ tester; KHÔNG tự đánh DONE)

## 1. Kết quả tóm tắt

| Hạng mục | Kết quả |
|---|---|
| Generator đọc DB | `scripts/build_credits.py` (chỉ đọc, `sqlite3 mode=ro`) |
| Trang sinh lại | `credits.html` — 16 nguồn: 7 **đang dùng** + 9 **chặn/chưa xác minh** |
| Kiểm chứng số mục = số dòng SQL | `--check` → **PASS** (16 = 16, mỗi nguồn đúng 1 mục) |
| Test tự động | `tests/test_t290_credits_generator.py` → **10/10 PASS** (chạy trực tiếp + `pytest`) |
| Cú pháp | `ast.parse` OK cho cả 2 file `.py` |
| Ghi DB | **KHÔNG** (0 INSERT/UPDATE/DELETE) |
| Sửa giấy phép trong DB | **KHÔNG** (đúng mục 5 của task) |

## 2. File đã đổi / tạo

| File | Loại | Ghi chú |
|---|---|---|
| `scripts/build_credits.py` | **tạo mới** | generator + `--check` + `--json`; `--db` (read-only) hoặc `--api` (GET chỉ-đọc) |
| `tests/test_t290_credits_generator.py` | **tạo mới** | 10 test, dùng DB fixture tạm (không đụng `data/lineage.db`) |
| `credits.html` | **sinh lại** | nội dung do generator sinh, không gõ tay |
| `tasks/T290-m5-credits-tu-data-sources.md` | sửa | tick Bước 1–4, `status: testing`, `updated: 2026-11-01`, `outcome` |
| `docs/sessions/2026-11-01/T290-coder/backup/credits.html.bak-before-coder` | **backup** | bản `credits.html` trước khi sinh lại (4418 byte) |

Không sửa file nào khác. Không commit, không git, không đụng `done_when`.

## 3. Cách làm (mục 3 của task)

1. **So danh sách trang với `data_sources`.** Trang cũ có 5 thẻ gõ tay (DILA, CBETA,
   MARCUS, Wikidata, ZQLOCAL). Bảng `data_sources` thật hiện có **16 dòng**; ngoài 5
   nguồn trên còn `ZENLINEAGE`, `TTL_LOCAL` đang dùng và 9 nguồn `BLOCKED`/`active=0`
   (BDRC, SAT, CHGIS, FoJin, Kanripo, SuttaCentral, 84000, TGAZ, DILA_CATALOG) không
   có trên trang.
2. **Sinh nội dung từ DB (không gõ tay).**
   - Trường lấy từ `data_sources`: `source_code`, `source_name`, `organization`,
     `legal_status`, `integration_mode`, `license_spdx`, `data_license`,
     `license_verified`, `origin_url`, `license_url`, `active`.
   - `claims` đếm thật từ `entity_claims GROUP BY source_id`;
     `authority_score` từ `source_authority`.
   - Phân nhóm (định nghĩa trong `select_groups`):
     - **Đang dùng** = `active = 1` và `integration_mode <> 'BLOCKED'`;
     - **Chặn / chưa xác minh** = phần còn lại → in danh sách kèm lý do
       (M5: "Nguồn bị chặn: hiện dòng giải thích, không lỗi").
   - **Không tự khẳng định điều khoản**: `license_verified = 0` → nhãn
     "Chưa xác minh giấy phép" + dòng giải thích `license_verified=0`.
     Chỉ CBETA có `license_spdx = CC-BY-NC-SA-4.0` với `license_verified = 1` nên được
     hiển thị điều khoản.
3. **Kiểm.** `--check` không ghi file, đối chiếu trang với dữ liệu DB.

## 4. Lệnh đã chạy (rút gọn kết quả)

```bash
# 1) cú pháp
python -X utf8 -c "import ast; ast.parse(open('scripts/build_credits.py',encoding='utf-8').read())"
#   → AST OK (cả scripts/build_credits.py và tests/test_t290_credits_generator.py)

# 2) test (DB fixture tạm)
python -X utf8 tests/test_t290_credits_generator.py   # → 10/10 PASS
python -m pytest tests/test_t290_credits_generator.py -q   # → 10 passed in 0.96s

# 3) sinh trang + kiểm
python -X utf8 scripts/build_credits.py --api http://127.0.0.1:5000/daoanh/api/admin/sources/list \
  --out credits.html --generated-at "2026-11-01"
#   → 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9
python -X utf8 scripts/build_credits.py --api http://127.0.0.1:5000/daoanh/api/admin/sources/list \
  --out credits.html --check
#   → PASS — credits.html khớp 16 dòng data_sources (mỗi nguồn đúng 1 mục)
```

**Vì sao dùng `--api`:** trong worktree này `data/lineage.db` là file **0 byte**
(placeholder, `data/` không được git track). Các worktree khác
(`coder-t287`, `coder-t445`, `coder-t508`, `coder-model-v26`) cũng 0 byte — DB thật chỉ
có trên VPS. Máy local có app đang chạy ở `127.0.0.1:5000`, endpoint
`/daoanh/api/admin/sources/list` đọc trực tiếp `data_sources` bằng GET chỉ-đọc, nên
dùng làm nguồn dữ liệu. `scripts/build_credits.py --db <path>` sẵn cho VPS/test.

## 5. Kiểm chứng theo mục 4 của task

"Số nguồn trên trang = số dòng SQL":

- Marker ẩn trong trang: `<!-- t290:total=16 in_use=7 blocked=9 … -->`
- `--check` xác nhận: marker khớp (16/7/9), **16** thuộc tính `data-source-code` cho
  **16** dòng `data_sources`, không nguồn nào thiếu/lặp, không có nguồn "ma" (trang có
  nguồn không còn trong DB), và mọi nguồn `license_verified=0` có ghi rõ "chưa xác minh".
- Trang gõ tay cũ **bị `--check` bắt FAIL** (test `test_check_page_fails_on_handwritten_page`)
  → chứng minh kiểm chứng không phải hình thức.

## 6. Điều kiện dừng / câu hỏi cho Admin (MA)

1. **6/7 nguồn đang dùng có `license_verified = 0`** trong DB, nên trang ghi
   "Chưa xác minh giấy phép" (bản cũ gõ tay "CC BY-SA 3.0" cho DILA, "BY-SA" cho MARCUS,
   "CC0" cho Wikidata, "Nội bộ" cho ZQLOCAL). T290 **cấm sửa giấy phép trong DB**, nên
   tôi không tự nêu điều khoản. Muốn trang nêu điều khoản cho các nguồn đó thì cần một
   việc khác: điền `license_spdx` + `license_verified=1` (kèm căn cứ) vào `data_sources`.
   → Admin chốt: giữ trạng thái "chưa xác minh" (an toàn pháp lý) hay mở task điền DB?
2. **Đường dẫn phục vụ:** `/daoanh/credits.html` **không có route trong `app.py`** —
   gọi `127.0.0.1:5000/daoanh/credits.html` trả 404 là **bình thường**. Trang là file
   tĩnh ở gốc `daoanh/`, phục vụ bởi nginx (VPS) hoặc `local_gateway.py` (port 8080,
   `try_serve_static`). Tester nên kiểm qua `http://127.0.0.1:8080/daoanh/credits.html`
   hoặc mở trực tiếp file — không yêu cầu thêm route (ngoài phạm vi task).
3. **Nối `npm`:** chưa thêm script `credits:build` vào `package.json` (ngoài phạm vi
   T290). Nếu MA muốn, đề nghị task follow-up.

## 7. Việc KHÔNG làm (có chủ ý)

- Không đổi `done_when`, không sửa test của task, không đánh DONE.
- Không ghi DB / không chạy `--apply` / không git / không xoá file / không deploy.
- Không thêm route Flask, không sửa `app.py`, `package.json`.
- Không bật/tắt `active`, `integration_mode`, `legal_status` của bất kỳ nguồn nào.

## 8. Revert

```bash
# bản credits.html trước khi sinh lại
cp docs/sessions/2026-11-01/T290-coder/backup/credits.html.bak-before-coder credits.html
# file mới (không ảnh hưởng runtime khác): scripts/build_credits.py,
# tests/test_t290_credits_generator.py  → xoá/khôi phục theo git
```

---

# VÒNG 2 — Sửa theo TESTER-REPORT (2026-11-01)

- **Nguồn việc:** `docs/sessions/2026-11-01/T290-coder/TESTER-REPORT.md` → FAIL 2 điểm;
  task §7 có 4 mục "Sửa 1–4".
- **Trạng thái:** `coding` → **`testing`** (chờ tester kiểm lại). KHÔNG đánh DONE.

## 9. Đã sửa gì (khớp từng mục §7)

| Mục | Việc làm | Bằng chứng |
|---|---|---|
| Sửa 1 | Tách ghi chú thành 2 tầng: `EDITORIAL_NOTES` (vai trò/ngữ cảnh, KHÔNG nêu giấy phép) + `LICENSE_TERM_NOTES` (điều khoản, chỉ render khi `license_verified=1`) | Trang sinh lại: cụm "chia sẻ tương tự" = **0 lần**; `class="note term"` = **1** (chỉ CBETA, verified=1) |
| Sửa 2 | `--check` thêm `find_license_claims()` + `card_segment()` + `NOTE_BLOCK_RE`: soi khối `<div class="note">` của mọi nguồn `license_verified=0`; thấy từ khóa giấy phép → FAIL | Test `test_check_page_flags_hardcoded_license_note`: chèn ghi chú cứng vào thẻ DILA → `--check` báo `Nguồn DILA: giấy phép chưa xác minh nhưng ghi chú trên trang nêu điều khoản (giấy phép, share-alike)` |
| Sửa 3 | Ghi rõ quy tắc lọc trong `outcome` — **không đổi** quy tắc | `outcome` §"Sửa 3" |
| Sửa 4 | Chạy lại test + `--check`, ghi output vào `outcome` | mục 10 dưới đây |

Chi tiết kỹ thuật:

1. `EDITORIAL_NOTES` viết lại thành mô tả thuần vai trò. Câu điều khoản của DILA
   ("cùng giấy phép chia sẻ tương tự") và CBETA ("phi thương mại / giữ thông báo bản
   quyền") chuyển sang `LICENSE_TERM_NOTES`. DILA đang `license_verified=0` nên **không
   render**; CBETA `license_verified=1` nên vẫn hiện.
2. `find_license_claims(text)` dò 8 mẫu: `giấy phép`, `license`, `bản quyền`,
   `copyright`, `thương mại|non-commercial`, `share-alike|chia sẻ tương tự`,
   `CC BY|CC0|CC SA|CC NC`, `public domain|công cộng`.
3. `--check` **bỏ qua** khối cảnh báo `class="note unverified"` (regex chỉ khớp
   `class="note"`), nên không tự báo lỗi chính câu "chưa xác minh giấy phép".
4. Thêm 4 test, tổng **10 → 14**:
   `test_unverified_source_shows_no_license_term_note`,
   `test_verified_source_shows_license_term_note`,
   `test_editorial_notes_have_no_license_terms` (chặn tái phát: mọi ghi chú trong
   `EDITORIAL_NOTES` phải sạch từ khóa giấy phép),
   `test_check_page_flags_hardcoded_license_note`.
5. Ghi chú `TTL_LOCAL`: bỏ 2 dấu backtick hiển thị thô (`nạp cục bộ local_dump`) —
   chỉ sửa ký tự, nội dung giữ nguyên (tester mục 5 "lỗi nhỏ").

## 10. Lệnh đã chạy vòng 2 + output thật

```bash
python -X utf8 -c "import ast; ast.parse(...)"            # → SYNTAX OK (2 file)
python -X utf8 tests/test_t290_credits_generator.py       # → 14/14 PASS
python -X utf8 -m pytest tests/test_t290_credits_generator.py -q
#   → 14 passed in 2.32s

python -X utf8 scripts/build_credits.py --api http://127.0.0.1:5000/daoanh/api/admin/sources/list \
  --out credits.html
#   → Đã sinh credits.html: 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9
python -X utf8 scripts/build_credits.py --api http://127.0.0.1:5000/daoanh/api/admin/sources/list \
  --check --out credits.html
#   → Dữ liệu: 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9
#   → PASS — credits.html khớp 16 dòng data_sources (mỗi nguồn đúng 1 mục).   exit=0
```

Kiểm lại nội dung trang:
`'chia sẻ tương tự'` xuất hiện **0** lần; `note term` **1** khối (CBETA).

## 11. CHƯA sửa — để MA/Admin quyết (ngoài danh sách Sửa 1–4)

1. **Footer vs marker:** footer còn câu cứng "Sinh từ `data_sources` trong `lineage.db`"
   trong khi marker ghi `db=Source Hub API`. Tester đề xuất #4 nhưng **không** nằm trong
   §7 của task nên tôi không sửa (tránh mở rộng phạm vi).
2. **Quy tắc "ACTIVE/REFERENCE"** vẫn chờ Admin chốt cột/giá trị. Hiện dùng
   `active=1 AND integration_mode<>'BLOCKED'`; đổi quy tắc chỉ cần sửa `select_groups()`.
3. **6/7 nguồn đang dùng vẫn `license_verified=0`** → trang ghi "Chưa xác minh giấy phép".
   Muốn nêu điều khoản phải điền `license_spdx` + `license_verified` trong DB (task khác;
   T290 không ghi DB).
4. `.opencode/agents/coder.md` vẫn untracked — không phải đầu ra của coder (MA sao chép
   vào worktree).

## 12. File đã đổi vòng 2

| File | Loại |
|---|---|
| `scripts/build_credits.py` | sửa (EDITORIAL_NOTES/LICENSE_TERM_NOTES/find_license_claims/check_page) |
| `tests/test_t290_credits_generator.py` | sửa (10 → 14 test) |
| `credits.html` | sinh lại từ data_sources (16 nguồn) |
| `tasks/T290-…md` | tick Sửa 1–4, `status: testing`, `outcome` |
| `docs/sessions/2026-11-01/T290-coder/backup/*.bak-before-coder-fix1` | 3 bản backup trước khi sửa |

Revert vòng 2:

```bash
cp docs/sessions/2026-11-01/T290-coder/backup/build_credits.py.bak-before-coder-fix1 scripts/build_credits.py
cp docs/sessions/2026-11-01/T290-coder/backup/test_t290_credits_generator.py.bak-before-coder-fix1 tests/test_t290_credits_generator.py
cp docs/sessions/2026-11-01/T290-coder/backup/credits.html.bak-before-coder-fix1 credits.html
```

---

# VÒNG 3 — Sửa theo TESTER-REPORT-2 (2026-11-01)

- **Nguồn việc:** `docs/sessions/2026-11-01/T290-coder/TESTER-REPORT-2.md` → Sửa 2 chưa đạt một phần (ghi chú cứng dạng khác lọt), footer nhỏ.
- **Trạng thái:** `coding` → **`testing`** (chờ tester kiểm lại). KHÔNG đánh DONE.

## 13. Đã sửa gì

| Mục | Việc làm | Bằng chứng |
|---|---|---|
| Sửa 5 | Mở rộng `--check`: soi mọi khối ghi chú có class chứa "note" (mọi tag), trừ `note unverified`. Thêm `NOTE_LIKE_RE` + `note_like_blocks()` + 2 test | Test A `<div class="note term">` và B `<p class="note">` đều bị bắt |
| Footer | Bỏ câu cứng "Sinh từ data_sources trong lineage.db" → "Sinh từ bảng data_sources", đồng bộ marker | `grep "lineage.db"` trong credits.html = 0 |
| Test tổng | 14 → **16** (thêm 2 test) | `16/16 PASS` |

## 14. Lệnh đã chạy vòng 3 + output

```bash
python -X utf8 -c "import ast; ast.parse(...)"   # → AST OK (2 file)
python -X utf8 tests/test_t290_credits_generator.py   # → 16/16 PASS
python -X utf8 -m pytest tests/test_t290_credits_generator.py -q   # → 16 passed in 1.31s
python -X utf8 scripts/build_credits.py --api http://127.0.0.1:5000/daoanh/api/admin/sources/list --out credits.html
#   → Đã sinh credits.html: 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9
python -X utf8 scripts/build_credits.py --api http://127.0.0.1:5000/daoanh/api/admin/sources/list --check --out credits.html
#   → Dữ liệu: 16 nguồn · đang dùng 7 · chặn/chưa xác minh 9
#   → PASS — credits.html khớp 16 dòng data_sources (mỗi nguồn đúng 1 mục).   exit=0
```

## 15. File đã đổi vòng 3

| File | Loại |
|---|---|
| `scripts/build_credits.py` | sửa (NOTE_LIKE_RE, note_like_blocks, check_page, footer) |
| `tests/test_t290_credits_generator.py` | sửa (14 → 16 test) |
| `credits.html` | sinh lại (16 nguồn) |
| `tasks/T290-…md` | tick Sửa 2 & Sửa 5, `status: testing`, `outcome` vòng 3 |
| `docs/sessions/…/backup/*-fix2` | 4 bản backup |

Revert vòng 3:
```bash
cp docs/sessions/2026-11-01/T290-coder/backup/build_credits.py.bak-before-coder-fix2 scripts/build_credits.py
cp docs/sessions/2026-11-01/T290-coder/backup/test_t290_credits_generator.py.bak-before-coder-fix2 tests/test_t290_credits_generator.py
cp docs/sessions/2026-11-01/T290-coder/backup/credits.html.bak-before-coder-fix2 credits.html
```

