---
id: T481
title: "Nap lien ket DILA con thieu vao DB (places_of_origin, active_at_places, works_in_tripitaka, wikidata_qid) tu sidecar da extract"
status: pending
created: 2026-10-28
updated: 2026-10-28
done_when: "Dry-run (da xong, xem docs/sessions/2026-10-28/links/DILA-link-dryrun-report.md) duoc Admin duyet --apply cho tung muc A/B/C/D rieng; script etl_dila_links.py chay --apply trong 1 transaction, backup data/lineage.db bang sqlite backup API vao data/backups/T481_<timestamp>/ + dong ROLLBACK.md truoc khi ghi; CREATE TABLE IF NOT EXISTS 3 bang additive (dila_person_place_link, dila_person_work_link, dila_person_wikidata) khong DROP/ALTER bang cu; so dong truoc/sau tung bang khop voi so du kien trong bao cao dry-run (sai so do dedupe UNIQUE); co --revert (DELETE WHERE source='DILA_Person_Authority_sidecar'); daoanh-qa xac nhan doc lap; Admin xac nhan DONE. Muc E (birth_death_dates) va F (cbeta_citations) CHI bao cao, khong co co --apply trong task nay."
---

# T481 — Nạp liên kết DILA còn thiếu vào DB (từ sidecar đã extract)

## Mô tả

`data/dila_import/extracted/A*.json` (49.487 file, trích từ DILA Person Authority XML,
CC BY-SA 3.0) có các trường **liên kết** chưa được nạp vào `data/lineage.db`:
`places_of_origin` (12.188 người), `active_at_places` (1.227 người),
`works_in_tripitaka` (10.299 mục / 3.035 người), `wikidata_qid` (2.005 người). Ngoài ra
`birth_death_dates` (9.848 người) và `cbeta_citations` (53.929 mục) cần đối chiếu và
**chỉ báo cáo**, không ghi vào `people`/`cbeta_person_mentions`.

Kiểm kê gốc: `docs/sessions/2026-10-28/DILA-resource-inventory.md`.
Dry-run đầy đủ (toàn bộ 49.487 file, không sample) đã chạy xong — xem báo cáo:
`docs/sessions/2026-10-28/links/DILA-link-dryrun-report.md`.

## Phát hiện chính từ dry-run (ảnh hưởng thiết kế)

- `places_of_origin`/`active_at_places` là **tên địa danh chữ Hán** (không phải ID) → so
  khớp theo `places_dila.name_zh`/`name`, không theo ID như kế hoạch gốc giả định.
- `vn_person_places`/`vn_person_works` dùng namespace slug Truyền Thừa Thiền Tông
  (`bach_van_thu_doan`...), **khác hẳn** namespace DILA A-id của sidecar → xác nhận phải
  tạo bảng additive mới, không mở rộng 2 bảng này.
- `canon_catalog.cbeta_id` và `cbeta_catalog_vn.sigla` NULL 100% — không dùng được; bảng
  khớp chính cho `works_in_tripitaka` là `dila_catalog_works.cbeta_id`.

## Kết quả dry-run (số liệu đầy đủ trong báo cáo)

| Mục | Tổng dòng | Khớp | Tỉ lệ | Ghi chú |
|---|---|---|---|---|
| A. places_of_origin | 12.188 | 12.151 | 99,7% | 37 không khớp (địa danh Tây Vực cổ) |
| B. active_at_places | 3.436 | 457 | 13,3% | places_dila thiếu danh bạ tự viện |
| C. works_in_tripitaka | 10.299 | 5.596 có mã (100% mã khớp) | 54,3% có mã | 46% còn lại là tác phẩm thất lạc, đúng bản chất |
| D. wikidata_qid | 2.005 | — | — | 0 trùng QID với địa danh (sanity OK) |
| E. birth_death_dates (chỉ báo cáo) | 9.848 | mâu thuẫn 21–24% | — | KHÔNG ghi đè `people` |
| F. cbeta_citations (chỉ báo cáo) | 53.929 | mới 25.101/33.167 sigla | — | chưa rõ nguồn gốc `cbeta_person_mentions`, KHÔNG ghi |

## Việc cần làm khi Admin duyệt `--apply`

1. Viết `scripts/etl_dila_links.py` (generator, try-except, thông báo lỗi tiếng Việt theo
   AGENTS.md §ETL).
2. Backup `data/lineage.db` (sqlite backup API) → `data/backups/T481_<timestamp>/` +
   dòng `docs/ROLLBACK.md` + manifest trong `docs/sessions/2026-10-28/links/`.
3. `CREATE TABLE IF NOT EXISTS`: `dila_person_place_link`, `dila_person_work_link`,
   `dila_person_wikidata` (schema đầy đủ trong báo cáo dry-run).
4. Ghi trong transaction, dedupe theo UNIQUE constraint, in số dòng trước/sau.
5. Cung cấp `--revert`.
6. `daoanh-qa` kiểm chứng độc lập (đọc DB trước/sau, đối chiếu số liệu với báo cáo dry-run).
7. Admin xác nhận DONE.

## Ràng buộc

- Chỉ additive — không `DROP`/`ALTER` cột cũ, không sửa `people`, `places_dila`,
  `namevi_map_places`, `vn_person_*`, `dila_place_authority`.
- Không commit/push tự động — theo quy trình chuẩn, agent chỉ commit khi Admin yêu cầu rõ.
- Mục E/F không có cờ `--apply` trong task này — muốn ghi phải mở task riêng sau khi Admin
  xem mẫu mâu thuẫn.
