# T322 — Log lệnh đo (chỉ đọc, 2026-10-31)

Mọi lệnh dưới đây chạy ở chế độ đọc: SQLite mở bằng `mode=ro`, không `UPDATE/INSERT/DELETE`,
không `git add/commit/reset`, không sửa code. Backup file trước khi sửa docs nằm ở
`docs/sessions/2026-10-31/REALITY_CHECK.md.bak-before-t322` và
`docs/sessions/2026-10-31/00_PLAN_OVERVIEW.md.bak-before-t322`.

## 1. Kích thước DB trên đĩa

```bash
cd Dai_Tang_Kinh/daoanh
ls -la data/lineage.db
```
Kết quả: `1825574912` bytes (cột size của `ls -la`, Windows/Git Bash).

```python
import os
os.path.getsize(r"...\daoanh\data\lineage.db")
# -> 1825574912
```
Quy đổi: 1825574912 / 1024**3 = 1.700... GiB ; /1000/1000 = 1825.6 MB (decimal).

## 2. Số bảng trong DB

```python
import sqlite3
con = sqlite3.connect("file:.../data/lineage.db?mode=ro", uri=True)
con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()
# -> (217,)
```

## 3. data_sources — số hàng và chi tiết

```python
con.execute("SELECT COUNT(*) FROM data_sources").fetchone()
# -> (16,)
con.execute("SELECT source_id, source_code, legal_status_at_ingest, integration_mode, "
            "license_verified, active FROM data_sources ORDER BY source_id").fetchall()
```
Kết quả đầy đủ (16 dòng) đã chép vào `docs/integration/REALITY_CHECK.md` mục
"data_sources — 16 nguồn hiện có".

## 4. entity_claims theo nguồn

```python
con.execute("""
SELECT ec.source_id, ds.source_code, COUNT(*)
FROM entity_claims ec LEFT JOIN data_sources ds ON ds.source_id = ec.source_id
GROUP BY ec.source_id ORDER BY COUNT(*) DESC
""").fetchall()
```
Kết quả: DILA 293,177 · ZQLOCAL 118,295 · MARCUS 22,332 · CBETA 13,933 · Wikidata 148
— tổng 447,885 — **khớp số đo 2026-10-02**, không đổi.

## 5. Số route trong code đang chạy

`app.py` hiện 108 dòng, chỉ import `core` + 7 module `routes_*.py` + đăng ký blueprint
— không còn chứa route trực tiếp để đếm như bản 2026-10-02. Đếm bằng regex trên toàn bộ
`.py` đang hoạt động, loại các thư mục backup/session/archive:

```python
import re, pathlib
pat = re.compile(r'@\w*\.route\(')
exclude = ('docs/sessions', 'docs/reports', 'data/backups', '_archive', 'archive_done')
# quét toàn bộ *.py dưới daoanh/, bỏ qua các thư mục trên, cộng số match pat trong mỗi file
```
Kết quả (số route mỗi file) đã chép đầy đủ vào `docs/integration/REALITY_CHECK.md`
mục "Route — kiến trúc đã đổi". Tổng toàn bộ: 448. Trừ 5 file dev/test tooling
(`add_route.py`, `add_tasks.py`, `fix_all.py`, `scripts/t229_add_undone_endpoint.py`,
`tests/test_t178_gap_d3.py`, tổng 11 route) còn 437.

**Giới hạn của phép đo này:** đếm theo decorator trong source, không phải đếm theo
`app.url_map` lúc runtime (chưa chạy app.py trong T322 để lấy url_map thật — ngoài
phạm vi "chỉ đọc DB"). Có thể có route trùng tên, route đăng ký qua `add_url_rule`
(ví dụ dòng `app.route('/daoanh/api/cbeta/<sigla>/compare', ...)` trong `app.py` —
không khớp regex `@\w*\.route\(` vì không phải decorator) không được đếm. Vậy 437/448
là cận dưới, không phải số chính xác tuyệt đối.

## 6. Đối chiếu T231 (M1)

```bash
find tasks -iname "T231*"
# -> tasks/T231-m1-license-gate-wiring.md, tasks/archive_done/T231-m1-license-gate-wiring.md
```
Đọc cả 2 file: nội dung giống nhau, `status: done` trong frontmatter nhưng Step 4
trong thân file vẫn `⬜ TODO`. Đối chiếu Step 1 (DB) bằng SELECT ở mục 3 trên — khớp
5/6 nguồn (`ZENLINEAGE` đo được `NULL` thay vì `LEGACY` như task ghi).

## Kết luận đo

Không có số liệu nào trong tài liệu được tự bịa — mọi số trong REALITY_CHECK.md và
00_PLAN_OVERVIEW.md sau khi T322 sửa đều trỏ lại lệnh ở log này.
