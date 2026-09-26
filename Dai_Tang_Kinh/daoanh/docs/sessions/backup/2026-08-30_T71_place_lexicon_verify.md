# Session 2026-08-30 — T71: Place Name VI Lexicon Verify

## Tóm tắt

Session bắt đầu từ câu hỏi chiến lược: "22 bộ từ điển của tiền nhân đã được khai thác
tối đa chưa cho việc xác minh tên tiếng Việt của địa danh DILA?"

Audit phát hiện: **toàn bộ 109K rows trong `namevi_map_places` đều là `source=auto_transliterate`**
— không có row nào từ lexicon. T47/T48 đã thử match headword (name_vi=term) nhưng 0 matches
vì auto-transliteration và scholarly Vietnamese names dùng convention khác.

**Approach đúng:** extract CJK từ lexicon.definition (pattern `漢字. Explanation`) → build
CJK index {name_zh: vi_term} → match DILA places_dila.name_zh.

## T71 — Script t71_place_name_lexicon_verify.py

### Pass A: Lexicon CJK Index Match (precision ~87%)
- Load 166K entries → build index 25,604 unique CJK keys (cả term và definition)
- Match 58,985 DILA places.name_zh → 1,590 matches
- Normalized bằng NFD diacritic strip + no-space để tránh Hòa/Hoà false conflicts
- **1,529 places** upgraded conf 0.70→0.80 (lexicon xác nhận đúng)
- **222 lỗi thực** phát hiện → flagged needs_review=1

### Pass B: Suffix Rule Validation (deterministic)
- 16 Hán suffix → Sino-Viet equivalent (寺→Tự, 山→Sơn, 城→Thành...)
- **11,369 places** upgraded conf 0.70→0.72 (suffix consistent)
- 0 bad suffixes (mọi auto-transliteration đều kết thúc đúng suffix)

## Kết Quả

| Metric | Giá trị |
|--------|---------|
| Pass A upgrades (0.70→0.80) | 1,529 |
| Pass A conflicts flagged | 222 |
| Pass B upgrades (0.70→0.72) | 11,369 |
| Total T71 rows | 13,032 |
| namevi_map_places conf>=0.75 | ~10,491 places = **17.7%** |

## Lỗi Điển Hình Phát Hiện

| name_zh | Auto (sai) | Lexicon (đúng) | Nguồn |
|---------|-----------|----------------|-------|
| 獅子 | "Tép Tí" | "Sư Tử" | Tu Dien Han Viet |
| 歸仁 | "Quy Nhân" | "Quy Nhơn" | Tu Dien Han Viet |
| 甘露 | "Bả Lộ" | "Cam Lộ" | Tu Dien Han Viet |
| 定慧寺 | "Định Tuệ Tự" | "Định Huệ Tự" | Tu Dien Thien Tong |
| 白水 | "Bạch Héo" | "Bạch Thủy" | Tu Dien Han Viet |
| 板橋 | "Ván Kiều" | "Bản Kiều" | Tu Dien Han Viet |
| 洪福寺 | "Suyền Phúc Tự" | "Hồng Phúc Tự" | Tu Dien Thien Tong |

## Files Thay Đổi

- `scripts/t71_place_name_lexicon_verify.py` (NEW)
- `tasks/T71-place-name-lexicon-verify.md` (NEW, status: done)
- `data/t71_import_log.json` (NEW)
- `data/namevi_map_places` — 13,032 rows updated (conf + note_vi + needs_review)
- `data/progress_data.json` — rebuild (done=42, 71%)
- `docs/tasktodo.md` — T71 Done entry

## Revert

```bash
python scripts/t71_place_name_lexicon_verify.py --revert
```

Strips all `[T71:...]` tags, restores conf 0.80→0.70 và 0.72→0.70.

## Pending

- Admin review 222 conflict rows: `python scripts/t71_place_name_lexicon_verify.py --conflicts`
- Cho phép admin sửa name_vi của các conflict rows → set conf=0.85 thủ công
