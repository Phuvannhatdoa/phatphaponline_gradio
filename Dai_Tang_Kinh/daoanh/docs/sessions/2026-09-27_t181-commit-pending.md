# T181 — Lệnh commit khi git index unlock

## Tại sao chưa commit được
Git index.lock bị giữ bởi process khác (nhiều git process đang chạy — có thể là Claude Code infrastructure).
Khi các process đó xong, chạy lệnh sau từ thư mục **visjs-app** (repo root):

## Lệnh commit (chạy từ visjs-app/)

```bash
cd "E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"

git add \
  "Dai_Tang_Kinh/daoanh/admin/cbeta-import.html" \
  "Dai_Tang_Kinh/daoanh/admin/t50-progress.html" \
  "Dai_Tang_Kinh/daoanh/admin/index.html" \
  "Dai_Tang_Kinh/daoanh/app.py" \
  "Dai_Tang_Kinh/daoanh/fix_tabs.js" \
  "Dai_Tang_Kinh/daoanh/scripts/t181_map_sigla.py" \
  "Dai_Tang_Kinh/daoanh/tasks/T181-cbeta-bulk-import-lazy-translate.md" \
  "Dai_Tang_Kinh/daoanh/docs/tasktodo.md" \
  "Dai_Tang_Kinh/daoanh/docs/sessions/2026-09-27_t181-cbeta-lazy-import.md" \
  "Dai_Tang_Kinh/daoanh/docs/sessions/2026-09-26/" \
  "Dai_Tang_Kinh/daoanh/data/progress_data.json"

git add -f "Dai_Tang_Kinh/daoanh/data/cbeta/import_cbeta.py"

git commit -m "feat: T181 CBETA Lazy Import Pipeline (P1-P5) + Alert#1 fix_tabs + T50 progress UI

T181 — CBETA Bulk Import + Lazy Translate:
- scripts/t181_map_sigla.py: P1 mapping sh_number→sigla từ XML trên disk
- data/cbeta/import_cbeta.py: fix title_zh (level=m) + _write_passage() cho lineage.db
- app.py: 4 routes mới (cbeta-catalog, import-xml, check-update, catalog-stats)
- admin/cbeta-import.html: UI catalog 3122 bộ, badge, Nhập & Dịch, Check Update
- admin/index.html: link CBETA Import

Alert #1 fix: fix_tabs.js thêm nexus + entities (17 tabs)
T50: admin/t50-progress.html (queue UI + live job log)

Verify: py_compile OK | t181_map_sigla 5/5 | pytest 13/13 PASS
Pipeline: guard OK | audit:t166 pre-existing FAIL (T166-bio-edit-write-path-guard)
Revert: git revert --no-edit <sha> + python scripts/t181_map_sigla.py --revert

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

## Files trong commit
| File | Loại |
|------|------|
| admin/cbeta-import.html | NEW — UI P5 |
| admin/t50-progress.html | NEW — T50 queue UI |
| admin/index.html | EDIT — link CBETA Import |
| app.py | EDIT — 4 T181 routes |
| fix_tabs.js | EDIT — Alert #1 (nexus+entities) |
| scripts/t181_map_sigla.py | NEW — P1 mapping |
| data/cbeta/import_cbeta.py | EDIT — title fix + passage write (dùng -f do .gitignore) |
| tasks/T181-*.md | NEW — task file |
| docs/tasktodo.md | EDIT — T181 entry |
| docs/sessions/2026-09-27_*.md | NEW — session logs |
| docs/sessions/2026-09-26/ | NEW — session 26 |
| data/progress_data.json | EDIT — regen 97 tasks |
