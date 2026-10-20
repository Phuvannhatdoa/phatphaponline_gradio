---
task: tasks/T230-source-catalog-audit.md
date: 2026-10-04
---

# T230 — P1 (bước audit): kiểm kê catalog nguồn, 0 ghi DB

## Phạm vi đã chốt

Admin chọn: **audit + docs, 0 DB**; danh mục chuẩn **lấy theo doc hiện có**
(`docs/trusted-sources.md` + bảng nguồn mở rộng đã duyệt).

## ID task

`npm run dup:ids` → OK, không trùng. Số cao nhất trong `tasks/` là T227; T228/T229 đã
dùng qua commit (`docs(T227)`, `feat(T229)`, `fix(T228)`); T222 bị đặt chỗ bằng prose
trong `docs/Mimo-Flash/` (39 lần). Vì vậy ID mới lấy **T230**.

## Kết quả đo (DB `mode=ro`, 2026-10-04)

- `data_sources` 14 · `source_authority` 14 · `dataset_sources` 10
- Mục nguồn đánh số trong `trusted-sources.md`: 16 + 1 dòng nguồn mở rộng (BGIS) = 17
- Bảng đầu `SOURCE_REGISTRY.md`: 13 dòng
- **Ba con số danh mục mâu thuẫn**: tiêu đề doc 20 · mục thực tế 16 · Admin nhắc 25 · DB 14
- Quyền: `license_verified` 0/14 · `license_url` 0/14 · `repository_url` 1/14
- Không có bảng artifact; `source_version` là text tự do (`2026.03`, `T50`, `Q`, `1.0`)

## Lỗi tự làm trong lúc code (đã sửa, ghi để không lặp)

1. Doc dùng gạch nối Unicode (`–`, `—`) không phải `-`, nên tách tiêu đề bằng
   `split("-")` rơi vào giữa tên → `DDBC / DILA` thành `DDBC`, `Tipitaka.org` thành
   `Tipitaka.` và DILA không dò ra được trong DB. Đã thêm `normalize_dashes()`.
2. Bảng "nguồn mở rộng đã duyệt" không có số mục nên regex mục đánh số bỏ qua, làm mất
   BGIS. Đã thêm `read_doc_expanded()`.
3. `SOURCE_REGISTRY.md` có **nhiều bảng**; regex bảng quá rộng nuốt 2 dòng của bảng khác
   (`UNKNOWN`, `45`) vào "registry only". Đã giới hạn vào bảng đầu có header
   `# | Source | Authority | ...`.
4. Row thống kê "thiếu DB" lặp BGIS 2 lần. Đã dedupe và tách mục `doc_duplicate_tokens`.

## Verify

- `python -X utf8 scripts/t230_source_catalog_audit.py` → chạy PASS, in bảng gap
- `--out docs/reports/T230-source-catalog-20261004` → ghi `README.md` + `catalog-audit.json`
- `--json` → JSON hợp lệ, `rights_summary` đúng 0/0/1 trên 14
- Read-only: DB mở bằng URI `file:...?mode=ro`; không có `INSERT/UPDATE/DELETE/commit`
  trong script; đối chiếu bằng cách đọc lại số dòng 14/14/10 trước và sau khi chạy
- Chưa chạy `npm run pipeline` trong phiên này (script tương tái 0 với app; T226 đã
  chạy pipeline exit 0 ở commit `fb9f39b`)

## Còn lại cho P1

Chốt danh mục chuẩn, chọn kiểu artifact (bảng additive hay gắn `data_sources`), phân vai
authority/text/network, giữ `UNKNOWN` cho nguồn chưa rõ quyền, không mở public.

## Về commit

Phiên này bắt đầu bằng việc commit phần WIP T226 còn nằm trong worktree
(`fb9f39b` code 17 file, `6196430` docs 28 file). `git commit` bị treo >120s (bệnh T196)
nên dùng `commit-tree` + ghi thẳng `refs/heads/master` có CAS thủ công; sau đó phải
`git read-tree HEAD` để đồng bộ main index, nếu không agent khác sẽ thấy 45 file `D` và
commit nhầm xoá sạch T226. Chi tiết ở báo cáo session T226 và task này.