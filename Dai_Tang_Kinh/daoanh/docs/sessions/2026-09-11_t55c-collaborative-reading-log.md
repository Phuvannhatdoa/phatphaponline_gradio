# Session — T55c Collaborative Reading Log (Batch F, 2026-09-11)

## Bối cảnh

Sau khi xong T55b (Related Texts API, commit `aa9943c0`), Lee duyệt tiếp tục dev.
Đầu phiên phát hiện staged-index của agent ngoài có operation revert nội dung T55b
(app.py staged về blob pre-T55b, tasktodo −2, task T55 revert pending, ROLLBACK −10, session doc staged-delete).
Lee quyết định: **"Xóa staged index, giữ T55b"**. Đã backup staged intent ra
`%TEMP%\opencode\external_staged_20260911_102538.patch`, chạy `git reset` (mixed, KHÔNG `--hard`):
index về HEAD `c5b8b51`, T55b còn nguyên ở HEAD + worktree (verify: index blob app.py == HEAD == 8151e113, T55b grep 2).
Worktree của agent ngoài không bị đụng (36 file unstaged giữ nguyên).

## Chọn task

- T61 (Place Desc VI từ lexicon ĐỊA DANH): data đã có `place_desc_vi_draft` **14,000 rows** (source `dila_note_zh`,
  admin_approved=0) — core ETL đã làm, không còn delta đáng build.
- T60 (Bio VI lexicon Phase 2): query 48K people × 166K lexicon LIKE → **timeout** (>120s), không khả thi hiện tại.
- **Chọn T55c** (Gợi Ý Từ Hành Vi, OPTIONAL low-effort): backend-only, `app.py` sạch (không đụng file agent ngoài
  như places.html/home.html/search.js), additive, revert dễ.

## Build

### Bảng `text_reading_log` (app.py:4518-4561)
```sql
CREATE TABLE IF NOT EXISTS text_reading_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text_id TEXT NOT NULL,           -- short sigla chuẩn hoá ('T2076','X1524',...)
    session TEXT NOT NULL DEFAULT 'anon',
    ts TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session, text_id)
)
```
+ 2 index phụ (idx_t55c_text, idx_t55c_session). `_ensure_t55c_tables()` chạy lúc import.
0 ALTER bảng nền, 0 migration — đúng luật additive. Revert = bỏ route + `DROP TABLE`.

### Endpoints (app.py)
- **`POST /daoanh/api/cbeta/<sigla>/view`** (line 4586) — ghi 1 lượt xem:
  - chuẩn hoá sigla qua `_t55_normalize_sigla` (`T359`→`T0359`, `X77n1524`→`X1524`)
  - dedupe `INSERT OR IGNORE` theo `UNIQUE(session, text_id)`
  - session tuỳ chọn, ≤64 ký tự (thiếu → `'anon'` — bị loại khỏi gợi ý); quá dài → 400
- **`GET /daoanh/api/cbeta/<sigla>/related/behavioral`** (line 4611) — collaborative filtering:
  - lấy các session thật (≠ 'anon') đã xem kinh này
  - tìm text khác mà các session đó cũng xem, **chỉ xuất khi ≥2 session cùng xem cặp**
    (`HAVING COUNT(DISTINCT session) >= 2`), loại Self, order co_viewers DESC, top 5
  - resolve `title_vi` qua `_t55c_resolve_title` (`cbeta_catalog_vn.cbeta_ref GLOB 'T*n<num>'` — catalog lưu ref đầy `T51n2076`)
  - thiếu dữ liệu → `status: NO_DATA` + note giải thích (không bịa)

## Smoke test (Flask test_client — không cần cổng, tránh đụng server 5000 của agent ngoài)

| Case | Kết quả |
|------|---------|
| sesA xem T2076 + X77n1524; sesB xem T2076 + T359 | ghi đúng, normalize X1524 / T0359 |
| behavioral T2076 với X1524,T0359 mỗi cái chỉ 1 session | NO_DATA (đúng — guard ≥2 lọc) |
| sesC+sesD cùng xem T2076+T0359 + mỗi người 1 text riêng | behavioral T2076 → T0359 co_viewers=3 + title "Cảnh Đức Truyền Đăng Lục" |
| behavioral T0359 | → T2076 co_viewers=3 |
| duplicate session+text | dedupe (INSERT OR IGNORE) |
| session 80 ký tự | 400 |
| kinh chưa ai xem (X112233) | NO_DATA "Chưa có phiên người đọc thật" |
| regression `/related` T2076 | 200, 3 groups (crossref/persons/topic) |

Sau test: **xoá sạch test rows** (text_reading_log = 0 dòng — không để dữ liệu giả trong DB thật).
Tổ chức: server 5000 đang chạy bởi agent ngoài (PID 20240, code cũ, trả 404 với route mới) —
smoke bằng test_client, không đụng server đó.

## Files changed
- `app.py`: +~140 dòng (T55c block 4518-4660, sau `api_cbeta_related`)
- `tasks/T55-trich-dan-tu-dong.md`: +block ✅ T55c
- `docs/tasktodo.md`: dòng T55 → T55b + T55c DONE
- `docs/ROLLBACK.md`: row §1 (BUILD-T55c placeholder — hash-fill sau commit)
- `docs/sessions/2026-09-11_t55c-collaborative-reading-log.md` (file này)

## Revert
```bash
git revert --no-edit <hash-docs-T55c>
git revert --no-edit <hash-build-T55c>
# bảng chỉ chứa log người đọc (không phải dữ liệu nền) → nếu cần dọn:
#   sqlite3 data/lineage.db "DROP TABLE text_reading_log;"
```

## Todo tiếp theo
- Lee test 2 endpoint mới trên :5000 (sau khi agent ngoài restart server hoặc sau này).
- T55d panel UI "Gợi Ý Đọc" (places.html CBETA tab — LƯU Ý places.html đang có ~1095 dòng thay đổi external chưa commit).
- Hoặc task khác unblocked; luôn kiểm tra staged index trước khi commit (b4_commit.py).