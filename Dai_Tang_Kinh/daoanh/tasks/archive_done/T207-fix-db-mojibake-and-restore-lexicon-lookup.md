---
id: T207
title: Sửa mojibake Ð (U+00D0) trong DB — 22 cột, 1469 row + khôi phục tra cứu lexicon
status: done
created: 2026-10-01
owner: agent
module: daoanh
depends_on: T206
commit: 95d02a0
revert: "python -X utf8 scripts/t207_fix_db_mojibake.py --revert data/backups/lineage_t207_20261002_083822.db"
---

# T207 — Sửa mojibake `Ð` (U+00D0) trong DB + khôi phục tra cứu lexicon

> **Admin đã chốt phương án B (2026-10-01) — ĐÃ BUILD XONG.** Xem mục
> [Kết quả build](#9-kết-quả-build) phía dưới.

## 1. Bối cảnh

T206 đã sửa 590 ký tự `Ð` (U+00D0) trong **302 file TTL** → L4 = 0. Nhưng
khảo sát read-only phát hiện `Ð` **đã lan sang DB**: **22 cột / 1.469 row**.

## 2. Phạm vi đã đo (read-only, đã kiểm chứng)

| Bảng | Cột | Row |
|------|-----|-----|
| `lexicon` | `definition` | 328 |
| `lexicon_fts` | `definition` | 328 (FTS index — xem §5) |
| `lexicon` | `term` | 162 |
| `lexicon` | `normalized` | 162 |
| `lexicon` | `key_norm` | 162 |
| `lexicon_fts` | `term` | 162 (FTS index) |
| `name_vi_map` | `bio_snippet` | 66 |
| `entity_monks` | `name` / `definition` | 24 / 7 |
| `entity_temples` | `name` / `definition` | 23 / 14 |
| `vn_person_authority` | `name_vi` / `biographical_note_vi` | 4 / 4 |
| `keyword_map` | `value` / `keyword` | 4 / 1 |
| `name_vi_map` | `name_vi` / `name_vi_final` | 3 / 3 |
| `vn_person_relations` | `target_label_vi` | 3 |
| `person_bio_vi_draft` | `bio_vi_draft` | 3 |
| `translation_exemplar` | `zh` / `vi` | 2 / 2 |
| `entity_works` | `definition` | 2 |

### Đã soi kỹ 2 điểm rủi ro trước khi lập kế hoạch

1. **`translation_exemplar.zh`** — tên cột gợi ý Hán tự, nhưng đã đọc nội dung 2
   row: **toàn văn tiếng Việt** (`vi='Theo từ điển Phật học Đạo Uyển'`). Không có
   Hán tự bị hỏng. Sửa `Ð`→`Đ` an toàn.
2. **`lexicon_fts`** — **FTS5 external-content** (`content=lexicon,
   content_rowid=id`) và **0 trigger**. `UPDATE lexicon` thẳng sẽ **lệch index**.
   Phải dùng lệnh FTS5 `delete` → update base → insert. Xem §5.

## 3. Phát hiện quan trọng: lỗi này **phá vỡ tra cứu**, không chỉ sai hiển thị

`app.py:96 normalize_text()` (dùng bởi **cả 2** call site đọc `lexicon`:
`app.py:1226 _translate_zh_term`, `app.py:2800` gợi ý từ điển) làm:

```python
s = unicodedata.normalize('NFD', s)                    # bỏ dấu
s = ''.join(c for c in s if category(c) != 'Mn')
s = s.replace('đ','d').replace('Đ','d')               # ← chỉ map Đ (U+0110)
return s.lower().strip()
```

**U+00D0 (ETH) không có canonical decomposition** (`decomposition=''`) và không
nằm trong `.replace()` ⇒ nó **sống sót** qua toàn bộ quy trình:

| Term | `normalize_text()` | key lưu trong DB | Khớp? |
|------|--------------------|------------------|-------|
| `Đoạn lạc` | `'doan lac'` | `'Ðoan lac, đoan kho…'` | ❌ |
| `Ðoạn lạc` | `'ðoan lac'` | `'Ðoan lac, đoan kho…'` | ❌ |
| `Đại Bi` | `'dai bi'` | — | ❌ 0 row |

⇒ **tra cứu từ điển với mọi mục có chữ Đ đều trượt**, kể cả sau khi sửa hiển thị.

## 4. Vì sao KHÔNG tính lại `key_norm` toàn bộ

Đo trên 166.278 row có `key_norm`:

| Nhóm lệch | Row | Ghi chú |
|------------|-----|---------|
| `key_norm` khớp `normalize_text(term)` | 112.430 (67,6%) | quy ước chuẩn |
| lệch vì có `Đ/đ` **đúng** | 53.384 | lỗi quy ước có sẵn, **không do T207** |
| lệch vì có `Ð` | **162** | phạm vi T207 |
| lệch vì lý do khác | 302 | ngoài phạm vi |

Tính lại `key_norm` cho 53.384+302 row sẽ **đổi hành vi tra cứu trên quy mô lớn**
— vượt xa phạm vi sửa mojibake, rủi ro cao. **T207 chỉ đụng 162 row có `Ð`.**

## MỐC QUYẾT ĐỊNH

Đo được bằng chứng quyết định (probe `scripts/probe_t207c.py`):

| Chiến lược | Row `Ð` khớp lookup sau khi sửa |
|------------|-------------------------------|
| **A** — chỉ thay `Ð`→`Đ`, giữ `key_norm` cũ | **0 / 162** ❌ tra cứu vẫn hỏng |
| **B** — thay `Ð`→`Đ` **và tính lại `key_norm = normalize_text(term)`** cho đúng 162 row đó | **162 / 162** ✅ |

**Cần Admin chốt: A hay B?** Đề xuất **B** — vì:
- Chỉ 162 row, có backup + `--revert`.
- Cả 2 call site đọc `key_norm` đều dùng `normalize_text()` ⇒ tính lại làm chúng
  **khớp lần đầu tiên**, không phá cái gì đang chạy.
- A chỉ sửa hiển thị, tra cứu vẫn 0 kết quả ⇒ công cốc.

## 6. Kế hoạch build (phương án B)

**Script**: `scripts/t207_fix_db_mojibake.py` — `--stats` / `--dry-run` /
`--apply` / `--verify` / `--revert`.

### B1. Bảo vệ
- Backup DB trước khi ghi: `data/backups/lineage_t207_<ts>.db` (`sqlite3` backup
  API, không copy file — tránh copy khi DB đang ghi).
- `--dry-run` in đầy đủ **danh sách dòng sẽ đổi** (id + giá trị trước/sau).
- Mặc định `--stats`/`--dry-run`; chỉ `--apply` mới ghi.
- Toàn bộ thay đổi trong **một transaction** + `WAL` + `busy_timeout`.
- `--revert`: khôi phục từ backup, có bảng snapshot ghi lại giá trị gốc.

### B2. Sửa 20 cột "văn bản" (thay thế thuần)
`UPDATE ... SET col = replace(col, 'Ð', 'Đ')` — chỉ khi `col LIKE '%Ð%'`.
Bao gồm `lexicon.term`, `lexicon.definition`, `lexicon.normalized`,
`name_vi_map.*`, `entity_*`, `keyword_map.*`, `vn_person_authority.*`,
`vn_person_relations.target_label_vi`, `person_bio_vi_draft.bio_vi_draft`,
`translation_exemplar.zh/vi`, `entity_works.definition`.

### B3. `lexicon.key_norm` (phương án B)
Với **đúng 162 row** có `Ð` trong `term`:
`UPDATE lexicon SET key_norm = normalize_text(fixed_term) WHERE id = ?`
Dùng **chính** `normalize_text()` từ `app.py` (import, không viết lại) để không
lệch quy ước.

### B4. `lexicon_fts` (FTS5 external-content, 443 row)
Theo đúng thứ tự FTS5 yêu cầu, cho từng id:

```sql
INSERT INTO lexicon_fts(lexicon_fts, rowid, term, definition)
  VALUES('delete', :id, :old_term, :old_def);   -- gỡ index cũ
UPDATE lexicon SET term=:new_term, definition=:new_def WHERE id=:id;
INSERT INTO lexicon_fts(lexicon_fts, rowid, term, definition)
  VALUES('delete', :id, :new_term, :new_def);   -- đẩy index mới
```

**Không** dùng `INSERT INTO lexicon_fts(lexicon_fts) VALUES('rebuild')` vì sẽ
dựng lại 166.278 row — chậm và khoá DB lâu.

### B5. Kiểm chứng sau `--apply`
1. `Ð` còn lại trong 22 cột = **0**.
2. `lexicon_fts` còn `Ð` = **0**, và `count(lexicon_fts) == count(lexicon)`.
3. **Round-trip**: với mỗi row đã sửa, `normalize_text(new_term) == new_key_norm`.
4. **Spot-check tra cứu thật**: sau khi sửa, `key_norm = normalize_text('Đại Bi')`
   phải khớp ≥1 row (trước khi sửa = 0).
5. Tổng row các bảng không đổi (trừ `updated_at` nếu có trigger — hiện **0 trigger**).
6. `PRAGMA integrity_check` = `ok`.
7. Không đụng Hán tự: đếm số ký tự CJK trước/sau phải bằng nhau.

### B6. Test + tài liệu
- `tests/test_t207_db_mojibake.py` — chạy trên **bản sao DB tạm**, không đụng DB thật.
- Assertion: 0 `Ð`; FTS đồng bộ; round-trip key_norm; tra cứu `Đ…` khớp;
  số row bảng không đổi; CJK không đổi; `--revert` khôi phục đúng.
- `package.json`: thêm `test:t207` vào `test:translation`.
- Cập nhật `docs/db_schema.md` (ghi chú mojibake + quy ước `key_norm`).

## 8.5 Kết quả build (2026-10-01) — ĐÃ APPLY DB THẬT

Admin chốt **phương án B**. Đã build + apply lên `data/lineage.db`.

### Đã tạo
| File | Vai trò |
|------|---------|
| `scripts/t207_fix_db_mojibake.py` | `--stats/--dry-run/--apply/--verify/--revert` |
| `scripts/probe_t207_fts.py` | FTS5 `integrity-check rank=1` (bằng chứng định danh) |
| `tests/test_t207_db_mojibake.py` | **21/21 PASS** trên DB fixture nhỏ |
| `package.json` | `test:t207`, đã nối vào `test:translation` |

**`normalize_text()` lấy bằng AST từ `app.py`**, không import cả Flask app và
không viết lại ⇒ logic chắc chắn giống hệt, kể cả khi `app.py` sửa sau này.

### Kết quả trên DB thật
```
[APPLY] lexicon=443 row (FTS đồng bộ), key_norm tính lại=162 row, text=165 row

[OK ] 1) 0 ký tự Ð còn lại (text=0, fts=0)
[OK ] 2) count(lexicon_fts) == count(lexicon) (166278 == 166278)
[OK ] 3) round-trip key_norm = normalize_text(term) — 162 row đã sửa
[OK ] 4) tra cứu chữ Đ qua đường app.py:1226 — 41 row mẫu:
            trước khoá khớp 0, sau khớp 41
[OK ] 5) PRAGMA integrity_check = 'ok'
[OK ] 6) tổng ký tự CJK toàn DB không đổi (trước 803893, sau 803893)
[OK ] 7) tổng row 11 bảng không đổi
=> PASS
```

**Tổng 2.041 ký tự Ð đã sửa** (443 row `lexicon` + 165 ô ở 16 bảng khác).

### Bằng chứng mạnh nhất — tra cứu thật
Điểm 4 dùng **term thật** lấy từ chính các row đã sửa (không đoán), và so
`key_norm` **gốc** trong snapshot với khoá mà `app.py:1226` sẽ dùng:

> **trước khoá khớp 0/41 → sau khớp 41/41**

(121 row bị bỏ vì `app.py:1226` có điều kiện `LENGTH(term) < 60`.)

### FTS5 external-content — kiểm định đúng cách
Không chỉ đếm row mà dùng lệnh định danh của FTS5 trên bản sao tạm:

```
[OK] INSERT INTO lexicon_fts(lexicon_fts, rank) VALUES('integrity-check', 1)
     ⇒ index lexicon_fts KHỚP hoàn toàn bảng nội dung lexicon
[OK] integrity-check rank=0 — cấu trúc index không lỗi
[OK] distinct rowid index = 166278 = count(lexicon)
[OK] rowid ghi trùng trong index: 0
[OK] MATCH 'Đại' / 'Đễ' / 'Đề' → trả dòng bình thường
```

### Backup + Revert
- DB: `data/backups/lineage_t207_20261002_083822.db` (sqlite3 backup API)
- Snapshot từng ô: `data/backups/t207_snapshot_20261002_083852.json`
  (443 row `lexicon` + 165 ô, kèm baseline `rowcounts` + `cjk_total`)
- Revert: `python -X utf8 scripts/t207_fix_db_mojibake.py --revert "<đường dẫn .db>"`

### Sai lầm của chính tôi trong quá trình làm (đã sửa)
1. `length(col) - length(replace(col, Ð, Đ))` = **0** vì cả hai đều dài 1 ký tự
   ⇒ phải thay bằng `''` mới đếm được số lần xuất hiện.
2. `translation_exemplar` **không có cột `id`** ⇒ phải dò `PRAGMA table_info` để
   tìm khoá chính thay vì hardcode.
3. Điểm verify "trước/sau" ban đầu truy vấn **cùng một DB đã sửa** cho cả hai vế
   ⇒ "trước" phải so với `key_norm` gốc trong snapshot.
4. Chọn từ tra cứu bừa (`Đại Bi`) không phải giá trị `term` nào ⇒ 0 row, tưởng
   sửa hỏng. Phải lấy term thật từ row đã sửa.
5. 4 assert của test fail lần đầu — tất cả là **lỗi kỳ vọng trong test**, không
   phải lỗi script (thiếu dấu phẩy cuối tuple 1 phần tử; đếm `key_norm` so với
   1 giá trị thay vì từng row; row thử nghiệm làm lệch số đếm revert).

## 7. Việc còn lại sau T207 (không thuộc task này)

- **L1 = 17, L2 = 15** (32 blocking): nhãn sai — Admin tự cập nhật theo
  `docs/Mimo-Flash/T203-ttl-quarantine-list.md`. ETL vẫn bị chặn tới khi xong.
- **L5 = 25** nhóm `dila_id` trùng.
- **Lệch quy ước 53.686 row** (`key_norm` không bỏ dấu) — đề xuất task riêng
  T208 sau khi T207 xong, vì đụng hành vi tra cứu trên quy mô lớn.
- Gộp 3 file TTL trùng người (`phong_huyet_dien_chieu`, generationOrder 69/70/71).

## 8. File liên quan
- `scripts/probe_t207.py` / `probe_t207b.py` / `probe_t207c.py` — bộ 3 probe
  đo lỗi (giữ lại làm bằng chứng, chạy read-only).
- `scripts/t206_fix_mojibake.py` — bản TTL, tham chiếu cho cách backup/revert.
- `app.py:96` `normalize_text()` — hàm chuẩn, **import** chứ không viết lại.
- `app.py:1226`, `app.py:2800` — 2 call site đọc `lexicon.key_norm`.