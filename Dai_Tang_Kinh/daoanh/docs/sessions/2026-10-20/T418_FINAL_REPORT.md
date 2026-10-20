# T418 FINAL REPORT — BUG-045: Cột Gemini/Claude trong namevimap

**Task:** `tasks/T418-gemini-translation-incomplete.md`
**Ngày đóng:** 2026-10-20
**Trạng thái:** done (Admin đã xác nhận "Cột Claude đã đủ (59,164) — Done", chọn hướng D — song song Part 1 + Part 2)

---

## Tóm tắt

Namevimap có 2 cột cần đầy đủ dữ liệu: **Claude** (phiên âm từ XML Claude Cloud) và **Gemini**
(phiên âm batch qua `ai_person_name`). Diagnosis ngày 2026-10-19 xác định 2 việc độc lập, không
liên quan nhau về schema:

- **Part 1 — Claude**: import toàn bộ XML Claude-translated vào bảng mới `codex_person_name`
  (không đụng bảng cũ).
- **Part 2 — Gemini**: chạy lại `scripts/ai_batch_transliterate.py` (không `--reset`) để resume
  9,404 ID còn thiếu trong `ai_person_name` (dừng ở 39,269/48,673 từ các lần chạy 2026-10-04/05/08
  do lỗi mạng/quota rải rác).

Cả hai đã hoàn tất và được xác minh trực tiếp từ DB (không chỉ dựa vào log).

---

## Part 1 — codex_person_name (Claude XML import)

Script: `scripts/t418_import_claude_xml.py` (idempotent, `--dry-run` / `--apply` / `--revert`,
parse bằng `iterparse` — Zero-RAM theo AGENTS.md).

| Mục | Giá trị |
|---|---|
| Nguồn XML | commit `0d2ea40`, `data/phien_am/vn_person_name_vi.xml` |
| XML SHA-256 | `c21bf281e00947a24c21cea5191d3f4db9aed985f36a45fa0aac37781004fa8c` |
| Số thẻ `<person>` parse được | 49,335 |
| Matched (có `dila_id` trong `people`) | 48,646 → `status='suggested'` |
| Orphan (không có trong `people`) | 689 → `status='orphan-chưa có ID Dila'` |
| name_zh lệch so với `people.name_zh` | 1,637 dòng (`name_zh_mismatch=1`) |
| model tag | `claude-xml-import@0d2ea40` |

**Verify trực tiếp DB (2026-10-20):**
```
SELECT COUNT(*) FROM codex_person_name;                                     -- 49335
SELECT COUNT(*) FROM codex_person_name WHERE status='orphan-chưa có ID Dila'; -- 689
SELECT COUNT(*) FROM codex_person_name WHERE status!='orphan-chưa có ID Dila';-- 48646
```
Khớp 100% với `part1_manifest.json` (`docs/sessions/2026-10-19/T418/part1_manifest.json`) và
danh sách orphan tại `docs/sessions/2026-10-19/T418/orphan_ids.csv`.

Bảng `people`, `name_vi_map`, `entity_claims`, `ai_person_name` — không bị sửa (chỉ `CREATE TABLE`
bảng mới, không `ALTER`).

---

## Part 2 — ai_person_name (Gemini batch resume)

Script đã chạy: `scripts/ai_batch_transliterate.py` (không `--reset`, resumable qua điều kiện
`NOT IN` trên `ai_person_name.name_vi_ai`). Log: `logs/ai_transliterate.log`.

**Lịch sử chạy thực tế ngày 2026-10-19** (đọc trực tiếp từ log, không suy diễn):

| Run | Bắt đầu | Kết thúc | Tổng lũy kế | Lỗi batch |
|---|---|---|---|---|
| Baseline (trước T418, 3 lần 10-04/05/08) | — | — | 39,269 | — |
| Run 1 | 15:09:52 | 15:11:08 | 39,769/48,673 | 0 |
| Run 2 | 15:11:24 | 16:01:23 | 42,554/48,673 | 123 (lỗi mạng `getaddrinfo failed`, không phải quota) |
| Run 3 | 17:31:38 | 17:49:35 | **48,673/48,673** | 0 |

Run 3 là lần chạy đóng hoàn toàn khoảng trống còn lại (6,119 bản ghi từ 42,554 lên 48,673), không
còn lỗi batch.

**Lưu ý sửa chính xác:** mô tả ban đầu trong brief (("3 runs: 24.575 + 1.583 + 13.111")) là số liệu
của **3 lần chạy nền trước T418** (2026-10-04/05/08, tổng 39,269 — baseline gây ra bug), KHÔNG
phải 3 lần chạy resume trong phiên T418 này. 3 lần chạy thực sự thuộc T418 là Run 1/2/3 ở bảng
trên (2026-10-19, tổng cộng +9,404 bản ghi). Báo cáo này dùng số liệu đọc trực tiếp từ
`logs/ai_transliterate.log` và `ai_person_name.created_at` để tránh nhầm lẫn nguồn.

**Verify trực tiếp DB (2026-10-20):**
```
SELECT COUNT(*) FROM ai_person_name WHERE name_vi_ai IS NOT NULL AND name_vi_ai != ''; -- 48673
SELECT COUNT(*) FROM people;                                                           -- 48673
SELECT substr(created_at,1,10) d, COUNT(*) FROM ai_person_name GROUP BY d ORDER BY d;
-- 2026-10-04 | 24575
-- 2026-10-05 | 1583
-- 2026-10-08 | 13111
-- 2026-10-19 | 9404   (= Run1+Run2+Run3 trong phiên T418, 39269+9404=48673)
```
48,673/48,673 = 100%. Không có bản ghi cũ (`created_at` trước 2026-10-19) bị ghi đè — khớp
điều kiện `done_when (2c)`.

---

## UI — Cột Claude trên admin/namevimap.html

Admin đã xác nhận trực tiếp trong phiên làm việc: "Cột Claude đã đủ (59,164) — Done". Con số
59,164/59,167 là tổng số dòng namevimap hiển thị dữ liệu cột Claude (bao gồm cả nguồn khác ngoài
`codex_person_name`, ví dụ `name_vi_map`/`entity_claims` đã có từ trước).

**Giới hạn của báo cáo này:** không chụp được ảnh chụp màn hình UI trước/sau trực tiếp từ
`127.0.0.1:8080/daoanh/admin/namevimap.html` trong phiên đóng task này — trang yêu cầu đăng nhập
Google OAuth (`login.html` → "Đăng nhập với Google"), và theo quy tắc an toàn của agent, việc
đăng nhập thay người dùng vào một identity provider thật (Google) không được thực hiện tự động.
Bằng chứng "before/after" cho cột Claude trong báo cáo này dựa trên: (a) xác nhận bằng lời của
Admin trong phiên, (b) số liệu COUNT trực tiếp từ DB ở trên. Nếu cần ảnh chụp UI thực tế làm bằng
chứng bổ sung, Admin đăng nhập thủ công vào `admin/namevimap.html` rồi agent chụp lại sau.

---

## Files liên quan

- `scripts/t418_import_claude_xml.py` — script Part 1 (mới)
- `scripts/ai_batch_transliterate.py` — script Part 2 (đã chạy lại, resumable)
- `docs/sessions/2026-10-19/T418/part1_manifest.json` — manifest 49,335 dila_id đã insert (Part 1)
- `docs/sessions/2026-10-19/T418/orphan_ids.csv` — 689 ID orphan + lý do
- `docs/sessions/2026-10-19/T418/part2_run1_stdout.log` — log Run 1 (Part 2)
- `logs/ai_transliterate.log` — log đầy đủ Run 1/2/3 (Part 2)
- `data/backups/T418-20261019_150455/lineage.db` — backup trước khi chạy (không commit)
- `tasks/T418-gemini-translation-incomplete.md` — task file (status: done)

## Rollback (nếu cần)

- Part 1: `python scripts/t418_import_claude_xml.py --revert` (`DROP TABLE codex_person_name`,
  không ảnh hưởng bảng khác).
- Part 2: `DELETE FROM ai_person_name WHERE created_at >= '2026-10-19 15:09:52'` hoặc khôi phục từ
  `data/backups/T418-20261019_150455/lineage.db`.

---

*Report by: daoanh-debugger (Claude Sonnet 5), 2026-10-20.*
