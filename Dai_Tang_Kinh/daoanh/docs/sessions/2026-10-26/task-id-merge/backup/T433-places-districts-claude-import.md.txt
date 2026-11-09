---
id: T430
title: "T428 Part 1: Import Claude places + districts (codex_place_name + codex_district_name)"
status: pending
created: 2026-10-20
updated: 2026-10-20
owner: null
module: Data / Places / Import
priority: high
depends_on: [T429]
dispatch: null
plan_approved_at: "2026-10-20 (Admin phê chuẩn: tạo bảng mới codex_place_name + codex_district_name)"
done_when: >
  (1a) Backup lineage.db → data/backups/T430-<ts>/, PRAGMA quick_check=ok, ghi đường dẫn docs/ROLLBACK.md.
  (1b) Tạo script t430_import_claude_place_xml.py (dựa trên t418_import_claude_xml.py):
       - Fetch XML từ GitHub (commit theo T429 quyết định)
       - Parse bằng iterparse generator
       - CREATE TABLE codex_place_name (place_id, name_zh_xml, name_vi, tier, review, rule, evidence, alternatives, model='claude-xml-import@<commit>', status='suggested', name_zh_mismatch, xml_sha256, created_at)
       - CREATE TABLE codex_district_name (district_vi, name_zh, name_vi, tier, model, status, xml_sha256, created_at) — khóa theo district_vi (chuỗi Hán)
       - INSERT: 59.353 places + 16.907 districts (khoảng 59.353 places + 4.322 unique districts)
       - 1.637+ dòng lệch chữ Hán gắn flag name_zh_mismatch=1
       - CSV orphan + manifest dila_id
  (1c) Chạy dry-run (--dry-run flag), ghi output + số liệu, báo Admin.
  (1d) Admin duyệt → apply (--apply flag), verify count, snapshot manifest.
  (1e) Không UPDATE places, places_dila, namevi_map_places.
  (2) Ảnh / network log (nếu có UI preview).
  (3) Commit script + docs, không commit DB.
  (4) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
outcome: null
---

# T430 — Part 1: Import Claude places + districts

Yêu cầu: T429 phân tích xong, quyết định khóa district.

Viết script, dry-run, backup, apply, QA.

---

id: T430
