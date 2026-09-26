---
id: T51f
title: "Auto Hán-Việt — marcus_reference.label_vi (18,127 persons)"
module: Person Authority / Marcus SNA / ZQ Localization
priority: high
status: done
depends_on: [T51]
created: 2026-08-30
updated: 2026-08-30
completed: 2026-08-30
done_when: >
  Tất cả 18,127 rows trong marcus_reference có label_vi là phiên âm Hán-Việt
  thực sự (không phải copy Chinese label). Script idempotent, revertible.
  Dashboard hiển thị coverage 100% cho marcus_reference.label_vi.
---

# T51f — Auto Hán-Việt marcus_reference.label_vi

## Bối cảnh (từ debug session 2026-08-30)

MARCUS ChineseBuddhism_SNA (M. Bingenheimer, Temple University) chứa 18,127 thiền sư
với tên pháp hiệu chuẩn trong cột `marcus_reference.label` (ví dụ: 慧能, 菩提達磨, 馬祖道一).

**Vấn đề hiện tại với `label_vi`:**
- 14,678 rows (81%): `label_vi == label` — copy nguyên Chinese, không phải tiếng Việt
- 3,443 rows (19%): `label_vi` là tên Hán rút gọn (ví dụ `長水子璿` → `子璿`) — vẫn là Chinese
- 6 rows: NULL/empty
- **0 rows** có phiên âm Hán-Việt thực sự

**Tại sao `label` chuẩn hơn `people.name_zh`:**
DILA lưu `people.name_zh` bằng authority form (thụy hiệu, biệt danh, tên chùa):
- A001719 `name_zh`=大鑒真空普覺圓明禪師 (thụy hiệu) vs `marcus_reference.label`=慧能 ✓
- A001361 `name_zh`=壁觀婆羅門 (biệt danh) vs `marcus_reference.label`=菩提達磨 ✓
- A009582 `name_zh`=道秀 (sai) vs `marcus_reference.label`=神秀 ✓
Cột `marcus_reference.label` = **nguồn tên chuẩn nhất** cho display.

## Phạm vi

**Input:** `marcus_reference.label` — tên pháp hiệu chuẩn (Hán, 1–6 ký tự)
**Output:** `marcus_reference.label_vi` — phiên âm Hán-Việt
**Engine:** Lookup table Hán-Việt character-by-character (cùng approach với T62 person name fix)
**Confidence:** 0.5 (auto), source = ZQLOCAL
**Scope:** 18,127 rows — ưu tiên 14,684 rows chưa có Vietnamese thực sự

## Script

File: `src_python/db/t51f_hanviet_marcus.py`

```
Pseudocode:
1. Load hanviet_map (dict: char → vietnamese_reading)
2. SELECT node_id, label FROM marcus_reference
3. For each row:
   a. Convert label char-by-char using hanviet_map
   b. Handle multi-char words: 馬祖道一 → Mã Tổ Đạo Nhất
   c. Flag: label_vi_confidence = 0.5, label_vi_source = 'auto_hanviet_T51f'
4. UPDATE marcus_reference SET label_vi = ?, ... WHERE node_id = ?
5. Log: t51f_run_log.json — before/after sample, error count
6. --dry-run flag: print diff without writing
7. --revert flag: restore backup từ t51f_backup.json
```

**Backup trước khi chạy:**
```sql
CREATE TABLE marcus_reference_backup_t51f AS SELECT * FROM marcus_reference;
```

## Acceptance Criteria

- [ ] Script `src_python/db/t51f_hanviet_marcus.py` tồn tại và chạy được
- [ ] `SELECT COUNT(*) FROM marcus_reference WHERE label_vi = label` → 0 sau khi chạy
- [ ] Sample 20 rows spot-check: label_vi là phiên âm Hán-Việt hợp lệ
- [ ] 6 tổ sư trục chính correct: 慧能→Huệ Năng, 菩提達磨→Bồ Đề Đạt Ma, 神秀→Thần Tú
- [ ] Log file `data/t51f_run_log.json` ghi rõ rows updated / errors
- [ ] `--revert` flag hoạt động: restore về trạng thái trước
- [ ] Dashboard `build_progress_data.py` update sau khi chạy

## Ghi chú kỹ thuật

- Tên Marcus ngắn (1–5 ký tự) dễ transliterate hơn tên DILA dài
- Trường hợp tên có prefix địa danh (例: 黃梅弘忍): chỉ transliterate phần tên, không transliterate địa danh prefix → để T51g curate thêm
- Sau T51f xong → T51g manual curate top 200 nâng confidence 0.5 → 1.0

## Liên kết

- Phụ thuộc: T51 (Nhân Vật Học Portal parent task)
- Kế tiếp: T51g (manual curate top 200)
- Tương tự: T62 (person name_vi bulk fix — cùng engine)
- Source: `marcus_reference` table, `marcus_networks` (11,169 edges)
