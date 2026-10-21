# research/thiendang-thepho/ — vùng cách ly T429 (Thiền Đăng Thế Phổ 禪燈世譜, CBETA X86n1601)

Vùng nghiên cứu cách ly của task **T429**. KHÔNG ghi DB / TTL / legacy / HOME từ vùng này.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `sources/` | Fragment XML mẫu trích từ nguồn (GĐ2) — `sample-source-fragments/` |
| `manifests/` | Đóng băng nguồn GĐ1: `source-manifest.json`, `source-header.xml`, `SHA256SUMS.txt` |
| `schemas/` | (GĐ3 — trống) |
| `derived/` | Dữ liệu dẫn xuất: `structure-inventory.json` (GĐ2) |
| `mapping/`, `review/`, `comparison/`, `preview/`, `tests/`, `releases/` | (GĐ3+ — trống) |
| `logs/` | Log chạy: `analyze-structure-run.json`, `baseline-git-status.txt`, `baseline-db-metadata.json` |

## Nguồn

`data/cbeta/xml-p5-full/X/X86/X86n1601.xml` — SHA-256 `0020c4847b8107260e8674233d7833fd590cccafba2210d0ac479edd88ff75eb`
(803.957 byte). Nguồn **bất biến**; file này không được sửa.

## Quyền

Header CBETA: *"Available for non-commercial use when distributed with this header intact."*
Mọi gói bàn giao phải kèm `manifests/source-header.xml`. Xem `docs/reports/thiendang-thepho/phase1/rights-assessment.md`.

## Báo cáo

- GĐ0: `docs/reports/thiendang-thepho/phase0/{environment-audit,reuse-map,scope-and-boundaries}.md`
- GĐ1: `docs/reports/thiendang-thepho/phase1/rights-assessment.md`
- GĐ2: `docs/reports/thiendang-thepho/phase2/{structure-analysis,extraction-rules}.md`
- Báo cáo chính: `docs/reports/thiendang-thepho/T429-PHASE-0-2-REPORT.md`

## Script

`scripts/thiendang_thepho/freeze_source.py` (GĐ1) · `analyze_structure.py` (GĐ2) — chỉ đọc nguồn, ghi đúng vào vùng này.
