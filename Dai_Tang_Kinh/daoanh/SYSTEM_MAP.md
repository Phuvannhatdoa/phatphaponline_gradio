# System Map - Phật Pháp Online
**Phiên bản:** 2026-04-14
**Primary Key:** DILA ID (Axxxxx format)
**Status:** 100% HOÀN THÀNH

## Cấu Trúc 4-Lớp Dữ Liệu
- 01_raw/ - Nguồn thô (.docx, .txt, .xml)
- 02_external/ - Dữ liệu ngoài (BDRC, GraphDB)
- 03_processing/ - Scripts & ETL
- 04_production/ - Binary index & API

## Thống Kê
- persons.json: 48,803 entries (ID DILA)
- combined_dict.json: 58,836 entries (22 dictionaries)
- places.json: 5,000 entries (100% có GPS)
- indexed/entity_master.idx: Binary search ready
- sitemap.xml: 53,803 URLs
- schema_persons.jsonld: 1,000 persons

## Tính Năng Đã Hoàn Thành
- ✅ Primary Key: DILA ID (A000001 format)
- ✅ Zero-RAM: Streaming + Binary Index O(log n)
- ✅ GPS Mapping: 5,000 places
- ✅ SEO: Sitemap + Schema.org
- ✅ BDRC Linker: Ready (owl:sameAs)
- ✅ Place-Person Linker: Ready
- ✅ Final QA: QA_FINAL_REPORT.md

## Hướng Dẫn Team
- Upload file mới vào folder tương ứng
- Chạy lại ETL scripts nếu cần rebuild
- Không cần cấu hình lại hệ thống

## Zero-RAM Compliance
- Streaming generator cho large files
- Binary index cho O(log n) lookup
- Không load toàn bộ vào RAM