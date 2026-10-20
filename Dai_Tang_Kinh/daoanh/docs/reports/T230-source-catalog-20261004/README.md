# T230 — Bao cao kiem ke catalog nguon va phap ly (P1)

- **Che do:** `read-only (khong ghi DB, khong ETL, khong export)`
- **Sinh luc:** 2026-10-04T13:34:00
- **DB:** `data/lineage.db` (chi doc)

## 1. So lieu

| Bang | So dong |
|---|---|
| `data_sources` | 14 |
| `source_authority` | 14 |
| `dataset_sources` | 10 |
| Mục nguồn đánh số trong `trusted-sources.md` | 17 |
| Dòng khai báo trong `SOURCE_REGISTRY.md` | 13 |

**Con số danh mục đang mâu thuẫn:** docs/trusted-sources.md (tieu de) = 20; docs/TGS-integration-masterplan.md (Admin nhan) = 25. Không cái nào là SSOT.

## 2. Bang chung quyen

| Chi so | Gia tri |
|---|---|
| `license_verified = 1` | 0 / 14 |
| Co `license_url` | 0 / 14 |
| Co `repository_url` | 1 / 14 |

| source_code | legal_status | mode | license_verified | license_url | repository_url | thieu |
|---|---|---|---|---|---|---|
| DILA | AUDITING | INGEST | 0 | - | - | license_verified, license_url, repository_url |
| BDRC | UNKNOWN | BLOCKED | 0 | - | - | license_verified, license_url, repository_url, adapter_version, base_url |
| CBETA | AUDITING | INGEST | 0 | - | - | license_verified, license_url, repository_url |
| MARCUS | AUDITING | INGEST | 0 | - | - | license_verified, license_url, repository_url |
| ZQLOCAL | AUDITING | INGEST | 0 | - | - | license_verified, license_url, repository_url, base_url |
| Wikidata | AUDITING | INGEST | 0 | - | - | license_verified, license_url, repository_url |
| SAT | UNKNOWN | BLOCKED | 0 | - | - | license_verified, license_url, repository_url, adapter_version, base_url |
| CHGIS | UNKNOWN | BLOCKED | 0 | - | - | license_verified, license_url, repository_url, adapter_version, base_url |
| FoJin | UNKNOWN | BLOCKED | 0 | - | - | license_verified, license_url, repository_url, adapter_version, base_url |
| Kanripo | UNKNOWN | BLOCKED | 0 | - | - | license_verified, license_url, repository_url, adapter_version, base_url |
| SuttaCentral | UNKNOWN | BLOCKED | 0 | - | - | license_verified, license_url, repository_url, adapter_version, base_url |
| 84000 | UNKNOWN | BLOCKED | 0 | - | - | license_verified, license_url, repository_url, adapter_version, base_url |
| TGAZ | UNKNOWN | BLOCKED | 0 | - | - | license_verified, license_url, repository_url, adapter_version, base_url |
| ZENLINEAGE | INTERNAL_USE | INGEST | 0 | - | https://github.com/echojoel/zenlineage | license_verified, license_url, adapter_version, base_url |

## 3. Gap nguon

- Chỉ có trong doc, chưa có trong `data_sources`: BGIS, BuddhaNexus, DSBC, GRETIL, IDP, OCBS, PTS, THL, Tipitaka.org / VRI, Treasury of Lives
- Token lặp trong doc (một nguồn nhiều mục): BGIS
- Chỉ có trong DB, chưa có trong doc: MARCUS, ZQLOCAL, Wikidata, CHGIS, FoJin, SuttaCentral, TGAZ, ZENLINEAGE
- Chỉ khai trong `SOURCE_REGISTRY.md`: không có

| # | Tieu de | token | trong DB | source_authority | dataset_sources | alias |
|---|---|---|---|---|---|---|
| 1. | CBETA — Chinese Buddhist Electronic Text Association | CBETA | co | co | co | resolved |
| 2. | BDRC — Buddhist Digital Resource Center (SKIPPED) | BDRC | co | co | - | resolved |
| 3. | DDBC / DILA — Dharma Drum Buddhist College | DDBC / DILA | co | co | - | resolved |
| 4. | Tipitaka.org / VRI — Vipassana Research Institute | Tipitaka.org / VRI | KHONG | - | - | resolved |
| 4.5. | BGIS — Buddhism Geographical Information System (bổ sung 2026-08-24) | BGIS | KHONG | - | - | resolved |
| 5. | IDP — International Dunhuang Project | IDP | KHONG | - | - | resolved |
| 6. | SAT Daizōkyō Text Database — Đại học Tokyo | SAT | co | co | - | resolved |
| 7. | PTS — Pali Text Society | PTS | KHONG | - | - | resolved |
| 8. | GRETIL — Göttingen Register of Electronic Texts in Indian Languages | GRETIL | KHONG | - | - | resolved |
| 9. | DSBC — Digital Sanskrit Buddhist Canon | DSBC | KHONG | - | - | resolved |
| 10. | OCBS — Oxford Centre for Buddhist Studies | OCBS | KHONG | - | - | resolved |
| 11. | BuddhaNexus — Text Reuse Project | BuddhaNexus | KHONG | - | - | resolved |
| 12. | Kanripo — Digital Archive of Buddhist Studies | Kanripo | co | co | co | resolved |
| 13. | 84000 — Translating the Words of the Buddha | 84000 | co | co | - | resolved |
| 14. | THL — The Tibetan and Himalayan Library | THL | KHONG | - | - | resolved |
| 15. | Treasury of Lives — Biographies of Himalayan Masters | Treasury of Lives | KHONG | - | - | resolved |
| MR | BGIS (Jiang Wu) | BGIS | KHONG | - | - | resolved |

## 4. Artifact

Chua co bang artifact cap release/commit/SHA; chi co cot source_version dang text tu do.

- DILA: `2026.03`
- BDRC: `1.0`
- CBETA: `T50`
- MARCUS: `2026`
- ZQLOCAL: `2024`
- Wikidata: `Q`
- SAT: `1.0`
- CHGIS: `1.0`
- FoJin: `1.0`
- Kanripo: `1.0`
- SuttaCentral: `1.0`
- 84000: `1.0`
- TGAZ: `1.0`
- ZENLINEAGE: `ec8357ed`

## 5. Phai lam tiep (P1 chua xong)

1. Admin chot danh muc chuan: doc 16 muc, DB 14, roadmap 25 — khong tu them dong.
2. `source_version` phai la release/commit/SHA cua artifact, khong phai nhanh hieu.
3. Moi source can `license_url` + `repository_url` + bang chung artifact-level; khong lay software_license lam data_license.
4. Nguon chua ro quyen giu `draft`/UNKNOWN, khong mo public export.

