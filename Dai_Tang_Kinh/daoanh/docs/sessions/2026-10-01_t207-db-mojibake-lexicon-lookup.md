# Session 2026-10-01 — T207 build + apply DB thật (mojibake `Ð` → khôi phục tra cứu lexicon)

**Ngày:** 2026-10-01 · **Agent:** opencode · **Admin:** phê chuẩn đề xuất + chốt **phương án B**

**Task:** `tasks/T207-fix-db-mojibake-and-restore-lexicon-lookup.md` (status `done`)

---

## 1. Quyết định của Admin
**Phương án B** — thay `Ð`→`Đ` **và** tính lại `lexicon.key_norm = normalize_text(term)`
cho đúng **162 row** có `Ð` trong `term`.

| | Row `Ð` khớp lookup |
|---|---|
| A: chỉ thay | 0/162 ❌ |
| **B: thay + tính lại key_norm** | **162/162** ✅ |

## 2. Đã tạo

| File | Vai trò |
|------|---------|
| `scripts/t207_fix_db_mojibake.py` | `--stats/--dry-run/--apply/--verify/--revert` |
| `scripts/probe_t207_fts.py` | FTS5 `integrity-check rank=1` (kiểm định định danh) |
| `tests/test_t207_db_mojibake.py` | **21/21 PASS** trên DB fixture nhỏ |
| `package.json` | `test:t207` → nối vào `test:translation` |

**`normalize_text()` lấy bằng AST từ `app.py`** (`ast.get_source_segment` + `exec`
trong namespace sạch): không import cả Flask app, không viết lại ⇒ logic chắc chắn
giống hệt kể cả khi `app.py` sửa sau này. Test khẳng định điều này.

## 3. Đã apply DB thật — sửa 2.041 ký tự `Ð`
443 row `lexicon` (FTS đồng bộ) + 165 ô ở 16 bảng; tính lại `key_norm` 162 row.

**Verify 7/7 PASS:**
```
[OK] 1) 0 Ð còn lại (text=0, fts=0)
[OK] 2) count(lexicon_fts) == count(lexicon)  166278
[OK] 3) round-trip key_norm 162 row
[OK] 4) tra cứu chữ Đ qua app.py:1226 — trước 0/41 → sau 41/41
[OK] 5) PRAGMA integrity_check = ok
[OK] 6) CJK không đổi (803.893 = 803.893)
[OK] 7) tổng row 11 bảng không đổi
```

**Bằng chứng mạnh nhất (điểm 4):** dùng **term thật** lấy từ chính các row đã sửa
(không đoán), so `key_norm` **gốc** trong snapshot với khoá mà `app.py:1226` dùng.
121 row bị bỏ vì `app.py:1226` có điều kiện `LENGTH(term) < 60`.

**FTS kiểm định đúng cách** — không chỉ đếm row:
`INSERT INTO lexicon_fts(lexicon_fts, rank) VALUES('integrity-check', 1)` ⇒ **index
khớp hoàn toàn bảng nội dung**; `rank=0` cấu trúc OK; distinct rowid 166.278; 0
rowid trùng; `MATCH 'Đại'/'Đễ'/'Đề'` trả dòng bình thường.

## 4. Backup + Revert
- `data/backups/lineage_t207_20261002_083822.db` (sqlite3 backup API, không copy file)
- `data/backups/t207_snapshot_20261002_083852.json` — snapshot **từng ô** + baseline
  `rowcounts` + `cjk_total` ⇒ `--revert` khôi phục chính xác từng ô (test xác nhận).

## 5. Sai lầm của chính tôi (đều đã sửa + ghi vào task)
1. `length(col) − length(replace(col, Ð, Đ))` = **0** vì cả hai dài 1 ký tự ⇒ phải
   thay bằng `''` mới đếm được số lần xuất hiện.
2. `translation_exemplar` **không có cột `id`** ⇒ phải dò `PRAGMA table_info` tìm
   khoá chính thay vì hardcode.
3. Verify "trước/sau" ban đầu truy vấn **cùng DB đã sửa** cho cả hai vế ⇒ "trước"
   phải so với `key_norm` gốc trong snapshot.
4. Chọn từ tra cứu bừa (`Đại Bi`) — không phải giá trị `term` nào ⇒ 0 row, tưởng
   sửa hỏng. Phải lấy term thật từ row đã sửa.
5. 4 assert fail lần đầu: tất cả là **lỗi kỳ vọng trong test** (thiếu dấu phẩy
   cuối tuple 1 phần tử; đếm `key_norm` so với 1 giá trị thay vì từng row; row thử
   nghiệm làm lệch số đếm revert).

## 6. Verify toàn dự án
`npm run guard` OK · `test:t203` 24/24 · `test:t207` 21/21 · `test:translation`
(đã chứa test:t207) PASS · `npm run pipeline` PASS. Vẫn còn **có sẵn từ trước**:
metric governance `claims_assertion_level 0%` / `conflicts_resolved 0%`, và
`EPERM unlink test-results/.last-run.json` (file-lock Windows).

## 7. Còn lại
- **L1 = 17, L2 = 15** (32 blocking) — nhãn sai, Admin tự cập nhật theo
  `docs/Mimo-Flash/T203-ttl-quarantine-list.md`. **ETL vẫn bị chặn tới khi xong.**
- **L5 = 25** nhóm `dila_id` trùng.
- **Đề xuất T208:** 53.686 row `key_norm` lệch quy ước (lệch vì `đ/Đ` **đúng**) —
  đụng hành vi tra cứu quy mô lớn, cần task riêng + Admin duyệt.
- Gộp 3 file TTL trùng người (`phong_huyet_dien_chieu`, gen 69/70/71).

## Revert
```
git revert --no-edit <sha_T207>
python -X utf8 scripts/t207_fix_db_mojibake.py --revert data/backups/lineage_t207_20261002_083822.db
```