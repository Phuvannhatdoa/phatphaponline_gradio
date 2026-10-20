# SOURCE REGISTRY — TGS (T78)

> **Ngày:** 2026-08-31 · **Bảng:** `data_sources` (13 nguồn) + `dataset_sources` (10)
> **Nguyên tắc:** audit 13 nguồn THẬT trong DB (không phải 20 theo docs kế hoạch). Không giả định
> license; Authority tách khỏi Legal.

## 1. Schema mở rộng (T78, additive)
Cột THÊM vào `data_sources` (không drop/sửa cột cũ):
`license_spdx · software_license · data_license · corpus_license · documentation_license ·
image_license · derivative_allowed · sharealike_required · noncommercial · noderivatives ·
license_verified · license_verified_at · license_verified_by · license_url · terms_status ·
version_policy · integration_mode · data_license_status · data_redistribution · data_commercial ·
legal_status · freeze_reason · legal_status_at_ingest · repository_url · updated_at`
(T77 trước đó đã thêm: source_version, adapter_version, schema_version, last_sync, last_verified,
enabled, health, capabilities, base_url, attribution_required, redistribution_allowed,
commercial_use, api_terms.)

## 2. Audit 13 nguồn (legal status sau T78)

| # | Source | Authority | Legal | Data status | Mode | Note |
|---|--------|-----------|-------|-------------|------|------|
| 1 | DILA | cao | AUDITING | AUDITING | INGEST | historical giữ (LEGACY), cần verify để ACTIVE |
| 2 | BDRC | – (active=0) | UNKNOWN | UNKNOWN | BLOCKED | T18 skip, legal chưa rõ, không ingest |
| 3 | CBETA | cao | AUDITING | AUDITING | INGEST | historical giữ, cần verify để ACTIVE |
| 4 | MARCUS | trung | AUDITING | AUDITING | INGEST | historical giữ, commercial chưa rõ |
| 5 | ZQLOCAL | nội bộ | AUDITING | AUDITING | INGEST | historical giữ, nội bộ |
| 6 | Wikidata | ref | AUDITING | AUDITING | INGEST | historical giữ (CC0 cần xác minh) |
| 7 | SAT | trung | UNKNOWN | AUDITING | BLOCKED | legal chưa xác minh -> không ingest mới |
| 8 | CHGIS | GIS | UNKNOWN | UNKNOWN | BLOCKED | Harvard GIS, redistribution chưa rõ |
| 9 | FoJin | trung | UNKNOWN | UNKNOWN | BLOCKED | license corpus chưa xác minh |
| 10 | Kanripo | trung | UNKNOWN | AUDITING | BLOCKED | CC BY-SA cần xác minh phạm vi |
| 11 | SuttaCentral | trung | UNKNOWN | AUDITING | BLOCKED | CC BY-NC-SA (phi thương mại) |
| 12 | 84000 | trung | UNKNOWN | AUDITING | BLOCKED | CC BY-NC-SA (phi thương mại) |
| 13 | TGAZ | GIS | UNKNOWN | UNKNOWN | BLOCKED | Harvard Gazetteer, redistribution chưa rõ |

> **Historical (5 nguồn đã ingest — DILA/CBETA/MARCUS/ZQLOCAL/Wikidata):** giữ nguyên 447,885 claims,
> gắn `legal_status_at_ingest='LEGACY'`, **KHÔNG freeze/xoá**. Muốn tiếp tục ingest mới → admin xác
> minh license → set `ACTIVE` (không tự động).

## 3. Giá trị mặc định (chính sách)
- Source mới khi thêm qua Legal Check → `legal_status=AUDITING`, `integration_mode` theo kết luận
  (INGEST/REFERENCE_ONLY/BLOCKED), `data_license_status=UNKNOWN`, `license_verified=0`.
- `integration_mode` mặc định = `BLOCKED` (không tự INGEST).
- `commercial_use`/`data_commercial` không bao giờ tự = 1 khi chưa xác minh.

## 4. Thêm source mới (Source 21+)
1. Admin dùng **Legal Check** (`admin/source_check.html`) → nhập tên + repo URL → Check.
2. Hệ thống phân tích public repo (rule SPDX) → kết luận + notes + provenance draft.
3. Admin xác nhận → `source-add` INSERT (AUDITING, mode, repository_url, audit log).
4. Dashboard card source mới tự xuất hiện. Admin tự bật ACTIVE khi đủ pháp lý.
=> KHÔNG sửa code/if-else per-source; KHÔNG rebuild B1/B2.

## 5. Quyết định T112 — 8 nguồn `implemented=0` (draft 2026-09-09, chờ Lee Tổng duyệt)

> Nguyên tắc lộ trình **"Chuẩn hóa & Tái cấu trúc — không tìm data mới"**: chỉ kích hoạt
> khi dữ liệu đã tồn tại trong repo + license rõ. Trạng thái hiệu lực thật lấy từ
> `source_authority` (13 đăng ký / **5 active** DILA-ZQLOCAL-MARCUS-CBETA-Wikidata / 8 pending).

| Source | Legal (T78 audit) | Dữ liệu sẵn có | Đề xuất | Lý do / ghi chú |
|---|---|---|---|---|
| BDRC | UNKNOWN | Không (T18 skip) | **BLOCK** | Legal chưa rõ; T18 đã skip ingest; chỉ tham chiếu khi có tài liệu rõ |
| SAT | UNKNOWN | AUDITING (đang rà) | **BLOCK** | Legal chưa xác minh → không ingest mới |
| CHGIS | UNKNOWN | UNKNOWN | **BLOCK** | Harvard GIS, redistribution chưa rõ |
| FoJin | UNKNOWN | UNKNOWN | **BLOCK** | License corpus chưa xác minh |
| TGAZ | UNKNOWN | UNKNOWN | **BLOCK** | Harvard Gazetteer, redistribution chưa rõ (phụ thuộc T21) |
| Kanripo | UNKNOWN | AUDITING | **DEFER** | CC BY-SA cần xác minh phạm vi dẫn chiếu; giữ `implemented=0` |
| SuttaCentral | UNKNOWN | AUDITING | **DEFER** | CC BY-NC-SA phi thương mại — cần quyết định phạm vi dùng (Pali ref) |
| 84000 | UNKNOWN | AUDITING | **DEFER** | CC BY-NC-SA — tương tự SuttaCentral |
| Wikidata | CC0 (cần xác minh) | 148 claims ref | **REFERENCE_ONLY** | Không phải nguồn chính cho entity_claims; giữ role tham khảo ngoài |

> **Kết luận:** 5 BLOCK · 3 DEFER · 1 REFERENCE_ONLY (Wikidata). **0 kích hoạt mới,
> 0 ETL chạy.** Ghi `note`/`integration_mode` KHÔNG đụng bảng base — toàn bộ là quyết
> định + docs. Trạng thái: **draft — chờ admin duyệt để đóng T112**.

> ✅ **2026-09-10 (Batch A) — Lee Tổng phê duyệt đề xuất §5.** Giữ nguyên 5 BLOCK ·
> 3 DEFER · 1 REFERENCE_ONLY; `note`/`integration_mode` đã phản ánh đúng trong
> `source_authority` (không ingest mới, không ETL). Quyết định này đóng phần §5 của T112;
> phần D-Feedback (`data_gap_requests`) được BUILD trong cùng phiên.
>
> ⚠️ **Số liệu đối chiếu DB (sửa lệch):** trên thực tế `data/lineage.db` có **4 nguồn
> `implemented=1`** (DILA/CBETA/MARCUS/ZQLOCAL) và **9 nguồn `implemented=0`** (gồm cả
> Wikidata). Cụm "**5 active**" ở các docs cũ = **5 nguồn historical-ingested** (kể
> Wikidata, dù `implemented=0` theo T70). Xem §6.

## 6. Đối chiếu T115 — Authority Score & Precedence (2026-09-09)

Số liệu khớp với `docs/SOURCE_AUTHORITY_MATRIX.md` (luật trọng tài T115 — docs-only, 0 code):

| source_code | authority_score | precedence_order (0-based) | implemented | Level (khoảng score) |
|---|:---:|:---:|:---:|---|
| DILA | 100 | 1 | 1 | L1-Primary |
| CBETA | 80 | 2 | 1 | L1-Primary |
| SAT | 75 | 3 | 0 | L2 |
| Kanripo | 70 | 9 | 0 | L2 |
| MARCUS | 60 | 4 | 1 | L2 |
| CHGIS | 58 | 5 | 0 | L2-GIS |
| TGAZ | 55 | 10 | 0 | L2-GIS |
| ZQLOCAL | 50 | 0 | 1 | L2 (nội bộ) |
| SuttaCentral | 50 | 11 | 0 | L2 |
| 84000 | 45 | 12 | 0 | L2 |
| BDRC | 40 | 6 | 0 | L3 |
| FoJin | 40 | 7 | 0 | L3 |
| Wikidata | 25 | 8 | 0 | L3-REFERENCE_ONLY |

**Chuẩn tên:** GRETIL **chưa có** (phải qua T78 source-add) · dùng **Wikidata** (≠ Wikipedia) ·
ZQLOCAL = DILA local (tên admin duyệt) · `precedence_order` dùng **0-based** (đặc tả "1 = cao nhất" là sai).
