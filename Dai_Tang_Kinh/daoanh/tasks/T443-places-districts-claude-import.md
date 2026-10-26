---
id: T443
former_ids: [T433, T430]
title: "T428 Part 1: Import Claude places + districts (codex_place_name + codex_district_name)"
status: done
created: 2026-10-20
updated: 2026-10-25
owner: null
module: Data / Places / Import
priority: high
depends_on: [T442]
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
outcome: >
  APPLIED 2026-10-23 (Admin chon "1"): codex_place_name 59.353 dong / codex_district_name 16.907
  (khong doi), 208 orphan, 7.047 lech name_zh. Backup data/backups/T443_20261023_152255/.
  Cho commit + daoanh-qa + Admin xac nhan DONE.
---

## Mô tả
Import phiên âm địa danh Claude (vn_place_name_vi.xml) và tên đơn vị hành chính vào hai bảng mới codex_place_name và codex_district_name, bằng script t430_import_claude_place_xml.py có dry-run, apply và backup. Đã apply 59.353 dòng vào codex_place_name, không sửa places, places_dila hay namevi_map_places; 7.047 dòng lệch chữ Hán được gắn cờ name_zh_mismatch. Còn commit, QA độc lập và Admin xác nhận DONE.

# T443 — Part 1: Import Claude places + districts

> ID cũ: T433 (đổi 2026-10-21; former_ids: T433, T430). "T430" trong nội dung này = T443. "T429" = T442 (analysis). Ghi chú: file gốc ghi `depends_on: [T429]` (không phải [T430, T418]) nên đổi thành `[T442]`.

Yêu cầu: T429 phân tích xong, quyết định khóa district.

Viết script, dry-run, backup, apply, QA.

## Quyết định Admin 2026-10-21

- Liên quan: tasks/T445-claude-place-name-import.md là dry-run riêng, KHÔNG gộp; T443 vẫn là bước import có gate.

## Kết quả dry-run 2026-10-23

Script: `scripts/t430_import_claude_place_xml.py` (iterparse generator, `--dry-run/--apply --yes/--verify`).

```
python -X utf8 scripts/t430_import_claude_place_xml.py --dry-run
```

| Chỉ số | Giá trị |
|---|---|
| places_xml / districts_xml | 59.353 / 16.907 |
| places khớp places_dila | 59.145 |
| places orphan (không có ID) | 208 → CSV |
| places lệch name_zh | 7.047 → CSV (spec ghi "1.637+") |
| places dup dila_id | 0 |
| districts đã có trong codex_district_name | 16.907 (0 orphan) |
| bảng gốc trước = sau | `places`=59.161, `places_dila`=59.167, `namevi_map_places`=118.298 |

- XML sha256: places `736f5ec62b822e61…`, districts `73b82b9e2b6f8845…`
- Output: `docs/sessions/2026-10-23/T443/` (manifest + orphans.csv + mismatch.csv)
- `--apply` tự backup → `data/backups/T443_<ts>/` + `PRAGMA quick_check=ok`, và **rollback nếu
  1 trong 3 bảng gốc đổi số dòng**.
- Sai lệch có chủ đích so với done_when: `codex_district_name` đã tồn tại (T428) khóa theo
  `dila_id` (`PLA…`), nên dùng `INSERT OR IGNORE` giữ nguyên schema thay vì tạo lại khóa
  `district_vi` — tránh DROP 16.907 dòng đã apply.

## Apply 2026-10-23 (Admin chọn "1")

```
python -X utf8 scripts/t430_import_claude_place_xml.py --apply --yes
python -X utf8 scripts/t430_import_claude_place_xml.py --verify
```

| Bảng | Trước | Sau |
|---|---|---|
| codex_place_name | — | **59.353** (59.353 có name_vi) |
| codex_district_name | 16.907 | 16.907 (+0, skip) |
| places | 59.161 | 59.161 |
| places_dila | 59.167 | 59.167 |
| namevi_map_places | 118.298 | 118.298 |

- Backup: `data/backups/T443_20261023_152255/lineage.db` (quick_check=ok) + manifest + 2 CSV.
- Phân bố: suggested tier1 53.769 / tier3 2.881 / tier2 2.337 / tier4 158; orphan 208 (194+8+6).
- `name_zh_mismatch=1`: 7.047 (lệch do `places_dila.name_zh` đang giữ tên thay thế, ví dụ
  PL000000000002 = 錫雅柯山 vs XML 興都庫什山) — **không sửa bảng gốc**, chỉ gắn cờ.
- Revert: `DROP TABLE codex_place_name;` — đã ghi `docs/ROLLBACK.md`.

**Còn lại:** commit script+docs, `daoanh-qa` kiểm độc lập, Admin xác nhận DONE. T444
(Gemini batch sang `ai_place_name`/`ai_district_name`) giờ đã đủ điều kiện `depends_on: [T443]`.


---
