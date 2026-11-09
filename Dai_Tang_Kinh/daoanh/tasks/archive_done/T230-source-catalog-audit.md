---
id: T230
title: P1 — Kiểm kê catalog nguồn và bằng chứng quyền (read-only, 0 DB)
module: Data Governance / Source Registry
priority: high
status: done
depends_on: [T226]
created: 2026-10-04
updated: 2026-10-04
done_when: Có script kiểm kê read-only đối chiếu danh mục nguồn với 3 bảng registry, báo cáo gap bằng số đo thật, và danh sách việc P1 còn lại đã ghi rõ quyết định cần Admin; không ghi DB, không mở public.
---

# T230 — P1: kiểm kê catalog nguồn và pháp lý (phần audit)

Bước đầu tiên của P1 trong [roadmap T226](docs/reports/T226-academic-ttl-roadmap.md §7).
Phạm vi phiên này **chỉ đọc**: đo lại hiện trạng, không thêm bảng, không sửa `data_sources`,
không mở export. Quyết định của Admin trước khi bắt đầu: *"Chỉ audit + docs (0 DB)"* và
*"Danh mục chuẩn lấy theo doc hiện có"*.

## Vì sao phải làm trước

Roadmap T226 nêu 3 con số danh mục khác nhau và chưa cái nào là SSOT:

| Nguồn tuyên bố | Con số |
|---|---|
| Tiêu đề `docs/trusted-sources.md` | 20 |
| Mục đánh số thực tế trong file đó | 16 (+1 dòng "nguồn mở rộng đã duyệt" = BGIS) |
| Admin nhắc trong roadmap T226 | 25 |
| DB `data_sources` | 14 |

Không đối chiếu trước thì mọi thay đổi P1 về sau sẽ dựa trên một danh mục sai.

## Số đo đã kiểm (2026-10-04, `data/lineage.db` mở `mode=ro`)

| Chỉ số | Giá trị |
|---|---|
| `data_sources` | 14 |
| `source_authority` | 14 |
| `dataset_sources` | 10 |
| `license_verified = 1` | **0 / 14** |
| có `license_url` | **0 / 14** |
| có `repository_url` | **1 / 14** (chỉ ZENLINEAGE) |
| có bảng artifact (release/commit/SHA) | **không có** — chỉ `source_version` dạng text tự do |

Nguồn có trong doc nhưng **không** có trong `data_sources`: BGIS, BuddhaNexus, DSBC,
GRETIL, IDP, OCBS, PTS, THL, Tipitaka.org/VRI, Treasury of Lives.
Nguồn có trong DB nhưng **không** có mục riêng trong doc: MARCUS, ZQLOCAL, Wikidata,
CHGIS, FoJin, SuttaCentral, TGAZ, ZENLINEAGE.

## Cấu trúc đã thêm

| File | Vai trò |
|---|---|
| `scripts/t230_source_catalog_audit.py` | Kiểm kê read-only; `--out` ghi báo cáo, `--json` cho máy |
| `docs/reports/T230-source-catalog-20261004/README.md` | Báo cáo gap dạng đọc cho Admin |
| `docs/reports/T230-source-catalog-20261004/catalog-audit.json` | Cùng dữ liệu dạng máy đọc |

Script mở DB bằng URI `file:...?mode=ro` — không có đường ghi DB trong toàn bộ file.
Alias tiêu đề → mã nguồn nằm trong `ALIASES`; mục không resolve được sẽ in
`UNRESOLVED` chứ không đoán.

## Phát hiện cần lưu ý

1. **`DDBC / DILA` là một nguồn (DILA), không phải hai.** Nếu tách nhầm sẽ tạo hai row
   cùng trỏ một authority.
2. **`BGIS` xuất hiện hai lần** trong doc: mục `4.5` và bảng "nguồn mở rộng đã duyệt".
3. **`source_version` không phải phiên bản artifact**: `2026.03`, `T50`, `Q`, `1.0`.
   Không dùng được để truy vết hay kiểm checksum.
4. **Không nguồn nào có `license_url`.** Số 0/14 này là lý do gate public chưa thể mở,
   và cũng là lý do không được coi `software_license` là `data_license`.
5. `SOURCE_REGISTRY.md` có bảng đầu 13 dòng khớp DB, nhưng file còn chứa **bảng khác**
   ở dưới — script chỉ đọc bảng đầu (header `# | Source | ...`) để không đếm nhầm.

## P1 còn lại — cần Admin quyết

1. **Chốt danh mục chuẩn**: 16 / 17 / 20 / 25 — Admin đưa danh sách chính thức, script
   và `trusted-sources.md` cùng lấy danh sách đó. Không tự thêm dòng.
2. **Artifact-level**: bảng additive (release, commit, SHA256, ngày lấy, provenance,
   `license_url` + bằng chứng, quyền dịch/chia sẻ) hay gắn vào `data_sources`?
3. **Phân vai** authority / text / network cho từng nguồn — `SOURCE_AUTHORITY_MATRIX.md`
   đang là nguồn, cần xác nhận còn đúng.
4. Nguồn chưa rõ quyền giữ `UNKNOWN`/`draft`; **không mở public export**.

## Revert

Không có thay đổi code/DB. Xoá `docs/reports/T230-source-catalog-20261004/` và
`scripts/t230_source_catalog_audit.py` là revert trọn vẹn.

## Session

`docs/sessions/2026-10-04_T230-source-catalog-audit.md`