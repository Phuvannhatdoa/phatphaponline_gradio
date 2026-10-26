---
id: T453
title: Import DILA authority_catalog tạng A (A.json) + lớp dịch Việt + tra cứu trên HOME
status: done
created: 2026-10-22
updated: 2026-10-22
owner: coordinator
module: Data / DILA Catalog
priority: high
plan_approved_at: "2026-10-22 (Admin chốt phạm vi: import A.json, nối DILA Person/Place ID, Cloud session dịch toàn bộ A.json, coordinator import lớp dịch vào DB, search trên HOME). Ghi DB/schema: CHƯA duyệt riêng."
done_when: >
  (1) Cloud session dịch đủ 9/9 bộ → docs/sessions/2026-10-22/T453/A.vi.json — XONG (Admin dán kết quả 2026-10-22 05:52).
      Tên người: DB thắng (people.name_vi), tên bản dịch chỉ tham khảo.
  (2) [XONG 2026-10-22 12:58, backup data/backups/lineage_t453_20261022_125818.db] Script scripts/t453_dila_catalog_import.py --dry-run đếm: 9 works, 10 contributor links (10/10 khớp people.id),
      0 place links (A.json không có places); --apply chỉ sau khi Admin duyệt; backup DB trước; --revert = DROP 3 bảng mới.
  (3) /daoanh/api/search trả thêm works từ DILA catalog (q='華嚴' hoặc 'Hoa Nghiêm' ra A1057), có badge nguồn
      DILA (Hán) / claude_code draft (Việt) / ZQLOCAL (tên người); không đổi field cũ.
  (4) Kiểm trên http://127.0.0.1:8080 thật; daoanh-qa kiểm độc lập; npm run pipeline; Admin xác nhận DONE.
revert: >
  python -X utf8 scripts/t453_dila_catalog_import.py --revert (DROP dila_catalog_works / _contributors / _places — chỉ bảng mới, mất 0 dữ liệu cũ);
  code app.py: khôi phục bản backup docs/sessions/2026-10-22/T453/app.py.bak-before-T453.
---

## Mô tả
Import bộ catalog DILA tạng A (A.json, 9 bộ, 10 lượt contributor) vào ba bảng mới dila_catalog_works, dila_catalog_contributors và dila_catalog_places, kèm lớp bản dịch Việt do cloud session tạo. Tên người lấy từ people.name_vi (DB thắng), không ghép theo tên; đã áp dụng cho toàn bộ tạng và thêm tìm kiếm trên HOME. Đã apply 5.747 bộ và QA ghi nhận đúng số; Admin chưa xác nhận DONE.

# T453 — DILA authority_catalog tạng A

## Nguồn

- `data/dila_import/authority_catalog.2026-10/json/A.json` — 27/27 file trùng SHA256 với GitHub
  `DILA-edu/Authority-Databases` master (commit 2026-08-31). CC BY-SA 3.0, bắt buộc ghi công DILA.
- A.json: 9 bộ (Triệu Thành Kim Tạng 趙城金藏), 10 lượt contributors, **không có places**.

## Đo trước (chỉ đọc, `mode=ro`)

- contributors: 10/10 ID khớp `people.id`, 10/10 đã có `name_vi` (ZQ).
- Dị thể: A001713 catalog `慧菀` vs people `慧苑` ⇒ ghép theo ID, lưu name_zh catalog làm alias.
- ZQ sai: A000457 呂夷簡 = "Lã **Dì** Giản" ⇒ bản dịch dùng "Lã Di Giản" (nguồn claude_code); sửa ZQ = việc riêng.
- time_from/time_to cả 9 bộ = khung triều đại ⇒ `year_precision='dynasty_range'`.
- `canon_catalog` không có bộ nào của tạng A; tên gần giống là tác phẩm khác ⇒ **cấm ghép theo tên**.

## Lớp dịch (Cloud session)

- Prompt dùng lại cho mọi tạng: `docs/sessions/2026-10-22/T453/PROMPT-cloud-translate.md`.
- Kết quả A: `docs/sessions/2026-10-22/T453/A.vi.json` — cùng khóa với A.json, thêm `*_vi/_src/_status/_note`
  (`_src` ∈ table/ai/db_pending; mọi `_status`=unreviewed). (Ghi vào `data/` bị chặn quyền nên để ở thư mục session.)
- Import: `title_vi/category_vi/dynasty_vi` lấy từ bản dịch; **tên người lấy `people.name_vi` theo ID (DB thắng)**;
  `byline_vi` thay tên bản dịch bằng tên DB; toàn bộ lớp dịch lưu `vi_json`, `vi_source='cloud_session'`.
- Dry-run 2026-10-22: works=9, contributors=10 (10/10 khớp people), places=0, title_vi 9/9, 2 chỗ tên lệch → dùng DB:
  A001713 "Huệ Uyển" (dịch) vs "Tuệ Uyển" (DB); A000457 "Lã Di Giản" (dịch) vs "Lã Dì Giản" (DB, nghi sai — task chuẩn hoá tên xử lý).

## Schema đề xuất (additive, CHỜ DUYỆT)

```sql
CREATE TABLE dila_catalog_works (
  cbeta_id TEXT PRIMARY KEY,          -- 'A1057'
  authority_id TEXT UNIQUE,           -- 'CA0007981'
  canon TEXT, vol TEXT, type TEXT, orig_category TEXT, category TEXT,
  title_zh TEXT, alt TEXT, juans INTEGER, cjk_chars INTEGER, en_words INTEGER,
  byline_zh TEXT, dynasty_zh TEXT, time_from INTEGER, time_to INTEGER, fulltext INTEGER,
  year_precision TEXT,                -- 'dynasty_range' | 'specific'
  title_vi TEXT, title_vi_gloss TEXT, category_vi TEXT, dynasty_vi TEXT, byline_vi TEXT,
  vi_source TEXT, vi_status TEXT, vi_json TEXT,  -- cloud_session / unreviewed
  raw_json TEXT, source_file TEXT, source_sha256 TEXT, imported_at TEXT);
CREATE TABLE dila_catalog_contributors (
  cbeta_id TEXT, seq INTEGER, person_id TEXT, name_zh TEXT, name_vi TEXT, name_vi_src TEXT,
  role_vi TEXT, note TEXT, PRIMARY KEY (cbeta_id, seq));
CREATE TABLE dila_catalog_places (
  cbeta_id TEXT, seq INTEGER, place_id TEXT, name_zh TEXT, lat REAL, long REAL,
  PRIMARY KEY (cbeta_id, seq));
```

Thêm 1 dòng `data_sources` `DILA_CATALOG` (CC BY-SA 3.0, AUDITING) — cũng chờ duyệt.

## KHÔNG làm

- Không sửa A.json gốc, không sửa `people`/`places_dila`/`canon_catalog`.
- Không gọi Gemini/Groq. Không deploy VPS. Không git commit khi chưa có lệnh.
- Tạng khác (T/X/J…) là task sau.

## Nhật ký 2026-10-22 (chiều)

- Bản dịch chuyển về thư mục Admin chốt: `data/dila_import/authority_catalog.2026-10/vn_dila_authority_catalog/<tạng>.vi.json`
  (hoặc `<tạng>.partN.vi.json`); script đọc ưu tiên ở đây, fallback thư mục session. A nạp lại từ đây
  (backup `data/backups/lineage_t453_20261022_130406.db`).
- (B) Search HOME **đã làm** (Admin duyệt 06:01): `/daoanh/api/search` thêm key `dila_works`; `index.html` render
  `#dilaWorks` (badge DILA / Bản dịch AI chưa duyệt / ZQ), không có kết quả → `/daoanh/places?q=` như cũ.
  Backup: `docs/sessions/2026-10-22/T453/{app.py,index.html}.bak-before-T453`. Đã restart app.py.
- QA độc lập (vai daoanh-qa): **ĐẠT**; lint/test/e2e PASS; `audit:honesty:strict` FAIL H1–H5 có từ trước T453
  (không đọc bảng dila_catalog_*, số dòng các bảng audit = backup trước T453).
- B.vi.json (Cloud, 234 bộ) dry-run: 229/234 title_vi, **83 title còn dạng "X/y"**, 160 byline_vi trống,
  41 tên Hán là biệt hiệu/dị thể cùng ID (không lỗi). Chưa apply — đã gửi Admin prompt sửa cho Cloud.
- Phát hiện DB ngoài phạm vi: A000903 `people.name_vi`="Hạ 丏 Tôn" (sót chữ Hán) → task chuẩn hoá tên.
- 14:09 — Pilot Cloud (prompt v4, `docs/sessions/2026-10-22/T453/PROMPT-cloud-full-26.md`) 10 tạng 50 bộ QA ĐẠT; Admin
  "nạp bản mới" → `--apply --canon ALL`: 284 bộ (A,B,C,CC,GB,K,LC,M,S,U,ZS), 322 người, QA 0 lỗi. Backup
  `data/backups/lineage_t453_20261022_140911.db`. Còn 15 tạng (5.463 bộ) chờ Cloud "tiếp tục".
- 15:15 — Admin duyệt "(2)": thẻ người trên HOME. `/daoanh/api/search` thêm key `dila_people` (person_id, name_vi DB,
  name_zh, số tác phẩm, tổng quyển, top 5 nơi dịch + tên Việt từ `namevi_map_places`); `index.html` render thẻ người
  đầu panel, kinh chưa có title_vi hiện badge "Chưa dịch". Backup `docs/sessions/2026-10-22/T453/*.bak-before-T453-personcard`.
  Thử trình duyệt: "Huyền Trang" → thẻ A000294 · 2 tác phẩm · 13 quyển + 2 kinh; console không lỗi mới
  (2 lỗi 404 có sẵn là của trang places khi test "Tâm Kinh"). lint/e2e PASS.
- 15:20 — Cloud trả đủ 26 file (prompt v4, `vn_dila_authority_catalog 2.zip` = 26/26 file trên đĩa). QA dry-run ĐẠT
  (0 lỗi QA; 3 person ID không có trong people; 7 contributor không ID; 794 người tên Cloud ≠ DB →
  `docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv`). Admin "All" → apply: works 5.747, contributors 5.589,
  places 765. Backup `data/backups/lineage_t453_20261022_152039.db`. Search "Huyền Trang" → thẻ A000294 · 78 tác phẩm ·
  1.341 quyển · Từ Ân Tự (37), Hoằng Phúc Tự (13), Ngọc Hoa Tự (12)…; API 0,25 s.
- Ghi nhận ngoài phạm vi: `namevi_map_places` có tên bẩn "Hoằng Phúc Tự _ Huý" (PL000000042305).
- Việc tiếp đề xuất: nút "xem tất cả N tác phẩm" (hiện panel giới hạn 10 kinh); tab tác phẩm trên trang người;
  lớp bản đồ nơi dịch kinh; daoanh-qa lần cuối → Admin xác nhận DONE.
- 15:35 — Admin duyệt (1): nút "Xem tất cả N tác phẩm" trên thẻ người. Route mới `/daoanh/api/public/dila_works?person_id=&sort=juans|year|title`
  (năm triều đại xếp sau năm cụ thể; kèm nơi dịch tên Việt). Backup `docs/sessions/2026-10-22/T453/*.bak-before-T453-allworks`.
  Thử trình duyệt: Huyền Trang → 78 bộ, đầu là Đại Bát-nhã (600 quyển, 660–663, Ngọc Hoa Tự). lint/e2e PASS.
- QA độc lập (code đếm riêng, không dùng script import): **ĐÚNG 5.747 bộ**; 0 thiếu/thừa/lệch ở title_zh, authority_id,
  juans, năm, contributors (5.589, đúng thứ tự), places (765, lat/long); title_vi 5.623 khớp nguyên văn + 124 chỉ khác
  viết hoa; 10 contributor không nối people (7 tổ chức không ID trong nguồn, 3 mã A049519–A049521 chưa có trong people).
- Đề xuất (2)(3) Admin phê chuẩn → tạo T454 (tên địa danh "_ Huý", 8 dòng) và T455 (chuẩn hoá tên người: 794 lệch + 532 sót chữ Hán).
- 15:45 — Đối chiếu qua web (API ô Search HOME `/daoanh/api/search?q=<mã>`, tra TỪNG bộ): **5.747/5.747 OK**
  (có trong kết quả, title_zh đúng nguồn, có title_vi), 430 s. Script + kết quả: `docs/sessions/2026-10-22/T453/webqa/`.
- Tiêu đề panel hiển thị tổng thật: API thêm `dila_works_total`; UI "N kết quả cho … (hiển thị 10)".
  Vd. "Huyền Trang" 81, "Bát-nhã" 187. Backup `*.bak-before-T453-count`. lint/e2e PASS.
- 16:00 — Admin duyệt (a): thẻ kinh hiện ĐỦ thông tin, mỗi thông tin 1 dòng có biểu tượng (📖 tên Việt · 🀄 tên Hán ·
  🔖 mã CBETA + DILA · 📚 tập/quyển/số chữ · 🗂️ bộ loại + nguyên phân loại · 🕰️ niên đại · ✍️ soạn dịch · 👤 người ·
  📍 nơi dịch); thẻ người 🧘/🆔/📚/📍. API search thêm vol, cjk_chars, category_zh, orig_category_zh/vi, places_vi.
  Backup `*.bak-before-T453-fulllines`. lint/e2e PASS, đã thử trình duyệt. (b) → tạo **T456** (autocomplete HOME).

## Admin Notes
- [2026-10-25 18:33] giao Tester xem Done chưa
