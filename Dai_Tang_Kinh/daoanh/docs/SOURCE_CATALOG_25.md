---
task: tasks/T232-p1-p2-catalog-and-identity-plan.md
catalog_version: 25
approved_by: Admin
approved_date: 2026-10-04
supersedes: docs/trusted-sources.md (danh mục 20)
---

# SOURCE CATALOG 25 — SSOT danh mục nguồn

**Đây là danh mục SSOT về nguồn của Phật Tổ Đạo Ảnh, do Admin phê chuẩn 2026-10-04.**

Thay thế tiêu đề "20 nguồn" của `docs/trusted-sources.md`. File đó giữ lại như tư liệu
lịch sử (chiến lược CORE/EXPAND/BRIDGE/ASSESS, ghi chú ưu/nhược điểm từng nguồn) nhưng
**không còn là danh mục chuẩn**.

## Vì sao cần một danh mục duy nhất

Roadmap T226 (P1) yêu cầu đối chiếu danh mục với 3 bảng registry. Trước khi có file này
có **5 con số cùng lúc**: 16 mục thực tế trong doc · 17 (16 + BGIS mở rộng) · 20 (tiêu đề
doc) · 25 (Admin) · 14 (`data_sources`). Không có SSOT thì mọi thay đổi P1/P2 đều mơ hồ.

Số đo đo lại 2026-10-04 (DB `file:...?mode=ro`): `data_sources` 14 · `source_authority` 14
· `dataset_sources` 10.

## Danh mục 25 nguồn

Cột "DB" là tình trạng trong `data_sources`; "Quyền" là `license_verified` /
`license_url` / `repository_url`.

| # | Nguồn | Mã | Vai trò đề xuất | DB | Quyền |
|---|---|---|---|---|---|
| 1 | CBETA (Chinese Buddhist Electronic Text Association) | `CBETA` | text + authority (Hán tạng) | có | 0 / NULL / NULL |
| 2 | Dharma Drum Buddhist College (DDBC) – Digital Archive | `DILA` (?) | authority (Hán truyền) | có (dưới tên `DILA`) | 0 / NULL / NULL |
| 3 | 84000 (Translating the Words of the Buddha) | `84000` | text (Tibetan) | có | 0 / NULL / NULL |
| 4 | Vipassana Research Institute (VRI) – Tipitaka.org | `VRI` | text (Pali) | **chưa có** | — |
| 5 | Kanripo (Digital Archive of Buddhist Studies) | `Kanripo` | text (Hán biến thể) | có | 0 / NULL / NULL |
| 6 | SAT Daizōkyō Text Database (Đại Tạng Kinh SAT) | `SAT` | text (Hán corpus) | có | 0 / NULL / NULL |
| 7 | The Treasury of Lives (Biographies of Himalayan Masters) | `TREASURY` | reference | **chưa có** | — |
| 8 | BuddhaNexus (Text Reuse Project) | `BUDDHANEXUS` | text (dùng lại) | **chưa có** | — |
| 9 | Pali Text Society (PTS) – Digital Editions | `PTS` | text (Pali, bản in) | **chưa có** | — |
| 10 | International Dunhuang Project (IDP) | `IDP` | text (Dunhuang) | **chưa có** | — |
| 11 | GRETIL (Göttingen Register of Electronic Texts in Indian Languages) | `GRETIL` | text (Sanskrit) | **chưa có** | — |
| 12 | THL (The Tibetan and Himalayan Library) | `THL` | text (Tibetan) | **chưa có** | — |
| 13 | Digital Sanskrit Buddhist Canon (DSBC) | `DSBC` | text (Sanskrit) | **chưa có** | — |
| 14 | BDRC (Buddhist Digital Resource Center) | `BDRC` | authority (Tibetan) | có | 0 / NULL / NULL |
| 15 | Oxford Centre for Buddhist Studies (OCBS) | `OCBS` | reference | **chưa có** | — |
| 16 | BGIS (Buddhist GIS) | `BGIS` | gis (chuyên biệt Phật) | **chưa có** | — |
| 17 | Marcus Bingenheimer's GIS | `MARCUS` | network (cạnh + phương pháp) | có | 0 / NULL / NULL |
| 18 | CHGIS (China Historical GIS) | `CHGIS` | gis (địa danh Hán tạng) | có | 0 / NULL / NULL |
| 19 | TGAZ (Harvard) | `TGAZ` | gis (gazetteer toàn cầu) | có | 0 / NULL / NULL |
| 20 | Wikidata P1188 | `Wikidata` | linking (cổng nối) | có | 0 / NULL / NULL |
| 21 | Dharmamitra / MITRA | `MITRA` | text | **chưa có** | — |
| 22 | READ / Gandhāran Texts | `READ` | text | **chưa có** | — |
| 23 | Gandhara Corpora | `GANDHARA_CORPORA` | text | **chưa có** | — |
| 24 | Chula-Nan | `CHULA_NAN` | text | **chưa có** | — |
| 25 | <https://zenlineage.org/lineage> | `ZENLINEAGE` | network (dòng dõi Thiền) | có | 0 / NULL / có repo |

**Ưu / nhược điểm do Admin nêu (giữ nguyên ý, dùng khi cân nhắc ingest):**

| # | Ưu | Nhược |
|---|---|---|
| 16 BGIS | Chuyên biệt, học thuật | Dữ liệu phân tán, cần chuyển sang chuẩn chung |
| 17 Marcus | Độ chính xác cực cao, đã kiểm chứng | Dạng tệp tĩnh, cần API hóa |
| 18 CHGIS | Chuẩn quốc tế cho địa danh Hán tạng | Khổng lồ, phải lọc chùa/tự viện |
| 19 TGAZ | Liên thông tuyệt vời | Cần ID chuẩn (URI) để truy vấn |
| 20 Wikidata P1188 | Nối DILA ID với thế giới | Dữ liệu mở, phải lọc xác thực |

## Đối chiếu với DB (không tự sửa)

- **25 = 11 nguồn đã có trong DB + 14 nguồn chưa có.**
  Chưa có: `VRI`, `TREASURY`, `BUDDHANEXUS`, `PTS`, `IDP`, `GRETIL`, `THL`, `DSBC`,
  `OCBS`, `BGIS`, `MITRA`, `READ`, `GANDHARA_CORPORA`, `CHULA_NAN`.
- **DB 14 = 11 nguồn trong danh mục + 3 nguồn ngoài danh mục:** `ZQLOCAL` (dữ liệu Việt
  nội bộ), `FoJin`, `SuttaCentral`. Ba nguồn này **không bị xoá**; chỉ chưa có vị trí
  trong danh mục 25 → cần Admin chọn: coi là "nguồn nội bộ/ngoài danh mục" hay bổ sung
  thành 26–28.
- **Mục 2 (DDBC) đang map vào `DILA`.** Cần Admin xác nhận: `DDBC – Digital Archive` và
  `DILA Authority` là một nguồn hay hai. Nếu là hai, danh mục còn thiếu `DILA` và DB sẽ
  thiếu một row.
- Mã `DILA` không nằm trong danh mục 25 dưới tên riêng — nhưng là authority chính của dự
  án, nên **không được mất** khi chốt.

## Trạng thái quyền (đo 2026-10-04)

| Chỉ số | Giá trị |
|---|---|
| `license_verified = 1` | **0 / 14** |
| có `license_url` | **0 / 14** |
| có `repository_url` | **1 / 14** (ZENLINEAGE) |
| `redistribution_allowed = 1` | **12 / 14** — mâu thuẫn với `license_url` NULL |
| `legal_status` | AUDITING 5 · UNKNOWN 8 · INTERNAL_USE 1 |

Không nguồn nào đủ điều kiện phát hành công khai. Gate public (T78/T131) phải giữ nguyên
cho tới khi có bằng chứng artifact.

## Quy tắc dùng danh mục này

1. Không thêm nguồn ngoài danh mục mà không có Admin ghi vào đây.
2. Mọi dòng mới trong `data_sources` phải trỏ về số # của danh mục.
3. Vai trò trong bảng là **đề xuất**, chỉ chốt khi Admin ký (xem
   [DECISIONS-P1-P2](DECISIONS-P1-P2-2026-10-04.md) P1.5).
4. Bằng chứng quyền gắn theo **artifact**, không gắn chung một license cho cả nguồn.

## Liên quan

- Báo cáo đo gap: [reports/T230-source-catalog-20261004/README.md](reports/T230-source-catalog-20261004/README.md)
- Quyết định còn mở: [DECISIONS-P1-P2-2026-10-04.md](DECISIONS-P1-P2-2026-10-04.md)
- Kế hoạch chi tiết: [tasks/T232-p1-p2-catalog-and-identity-plan.md](../tasks/T232-p1-p2-catalog-and-identity-plan.md)
- Ngữ cảnh TTL v2: [reports/T226-academic-ttl-roadmap.md](reports/T226-academic-ttl-roadmap.md)