> Tạo bởi phiên Claude Code theo yêu cầu M0. Cập nhật lần cuối: 2026-10-02.

# REALITY CHECK — Số liệu thực tế DB & code

Tài liệu này là nguồn sự thật duy nhất cho các con số về hệ thống.
Mọi spec (M0–M5) và CLAUDE.md phải tham chiếu file này, không ghi cứng số liệu.

## Số liệu đo trực tiếp

| Chỉ số | Tài liệu cũ ghi | **Thực tế đo được** |
|--------|-----------------|---------------------|
| DB size trên đĩa | 664 MB | **1.4 GB** |
| Số bảng trong DB | 67 | **156** |
| Số `@app.route` trong app.py | 131+ | **313** |
| Số hàng `data_sources` | 13 | **14** |

> CLAUDE.md đã ghi 664 MB và 67 bảng — cần cập nhật sau khi xác nhận file này.

## data_sources — 14 nguồn hiện có

| source_id | source_code | legal_status | integration_mode | license_verified | active | implemented (source_authority) |
|-----------|-------------|--------------|------------------|------------------|--------|-------------------------------|
| 1 | DILA | AUDITING | INGEST | 0 | 1 | **1** |
| 2 | BDRC | UNKNOWN | BLOCKED | 0 | 0 | 0 |
| 3 | CBETA | AUDITING | INGEST | 0 | 1 | **1** |
| 4 | MARCUS | AUDITING | INGEST | 0 | 1 | **1** |
| 5 | ZQLOCAL | AUDITING | INGEST | 0 | 1 | **1** |
| 6 | Wikidata | AUDITING | INGEST | 0 | 1 | 0 |
| 7 | SAT | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 8 | CHGIS | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 9 | FoJin | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 10 | Kanripo | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 11 | SuttaCentral | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 12 | 84000 | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 13 | TGAZ | UNKNOWN | BLOCKED | 0 | 1 | 0 |
| 14 | ZENLINEAGE | INTERNAL_USE | INGEST | 0 | 1 | **1** |

**Nguồn trong plan 25 chưa có hàng trong DB:** Marcus SNA (nếu tách riêng khỏi MARCUS), GeoNames, World Historical Gazetteer, BGIS, IDP, Tipitaka.org/VRI, BuddhaNexus, MITRA-parallel, GRETIL, DSBC, PTS, OCBS, THL, Treasury of Lives.

## entity_claims — số claims thực tế

| source_id | source_code | claims |
|-----------|-------------|--------|
| 1 | DILA | 293,177 |
| 5 | ZQLOCAL | 118,295 |
| 4 | MARCUS | 22,332 |
| 3 | CBETA | 13,933 |
| 6 | Wikidata | 148 |

**Lưu ý:** Tất cả 447,885 claims này được nạp vào khi `license_verified=0` và `LicenseGate` chưa được nối vào đường nạp. Đây là rủi ro cần ghi nhận, không phải lỗi cần sửa ngay (xem M1).

## Cấu trúc file thực tế vs plan

### gate/ — có sẵn, chưa nối
- `gate/license.py` — `LicenseGate` class đầy đủ (T78)
- `gate/status.py` — `LegalStatus` enum
- `gate/provenance.py`
- `gate/analyzer.py` — `SourceAnalyzer` (được dùng ở 1 route admin)
- `gate/conflict_recorder.py`

### adapters/ — có sẵn, chưa nối
- `adapters/base.py` — `SourceAdapter` abstract class + `ExtractedEvidence` (T77)
- `adapters/registry.py`
- `adapters/bdrc/`

### .claude/ — **thiếu so với spec M0**
Hiện chỉ có: `launch.json`

Còn thiếu theo M0:
- `.claude/settings.json` (permissions + deny rules)
- `.claude/rules/*.md` (scoped rules cho adapters, gate, ETL, schema)
- Hook `PreToolUse` (chặn git ghi)
- `.claude/skills/onboard-source/`
- `.claude/agents/source-reviewer.md`

### Admin pages hiện có
`source_check.html` — trang Legal Check (M1 muốn mở rộng thành `sources.html`)

**Chưa có:**
- `admin/sources.html` (M1 — Source Hub)
- `admin/authority_sync.html` (M2)
- `admin/geo_review.html` (M3)
- `daoanh/credits.html` (M5)

## Khoảng cách lớn nhất cần xử lý (theo priority)

| # | Gap | Module | Độ khẩn |
|---|-----|--------|---------|
| 1 | Key Gemini hardcoded trong app.py (~dòng 1065, 1105) | M0 | **P0** |
| 2 | `LicenseGate` chưa nối vào bất kỳ ETL/route nào | M1 | **P0** |
| 3 | `.claude/settings.json` + hook PreToolUse chưa có | M0 | **P0** |
| 4 | 5 nguồn active có `license_verified=0` nhưng đã có 447K claims | M1+M5 | **P0** |
| 5 | `credits.html` và footer attribution chưa có | M5 | **P0** |
| 6 | `CLAUDE.md` ghi sai DB size (664MB) và số bảng (67) | M0 | P1 |
| 7 | `sources.html` admin page chưa có | M1 | P1 |
