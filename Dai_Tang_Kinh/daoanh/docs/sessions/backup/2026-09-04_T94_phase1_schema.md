# Session 2026-09-04 — T94 Phase 1: Alignment Schema Migration

**Task:** T94 — Phase 1  
**Phạm vi:** Tạo 3 bảng alignment schema + 3 columns additive trên `passage`  
**Files tạo mới:** `scripts/t94_create_alignment_schema.py`  
**DB thay đổi:** Additive only — không xóa/sửa data cũ  
**Rollback:** `python scripts/t94_create_alignment_schema.py --revert`

---

## Thực hiện

```bash
python scripts/t94_create_alignment_schema.py --dry-run   # OK
python scripts/t94_create_alignment_schema.py --apply     # Applied 6/6
python scripts/t94_create_alignment_schema.py --verify    # ĐẦYĐỦ ✅
```

## Kết quả

| Object | Loại | Trạng thái |
|--------|------|-----------|
| `text_passages` | TABLE | ✅ Created |
| `translation_segments` | TABLE | ✅ Created |
| `passage_translation_alignment` | TABLE | ✅ Created |
| `passage.raw_zh_hash` | COLUMN | ✅ Added |
| `passage.passage_id_ref` | COLUMN | ✅ Added |
| `passage.segmentation_method` | COLUMN | ✅ Added |

Backup: `data/lineage.db.backup_t94_20260904_225841` (1,241 MB)

---

## Rollback

```bash
# Revert schema (DROP tables mới, DROP columns nếu SQLite >= 3.35):
python scripts/t94_create_alignment_schema.py --revert

# Hoặc restore toàn bộ DB từ backup:
# cp data/lineage.db.backup_t94_20260904_225841 data/lineage.db
```

---

## Pending — Phase 2

Re-translate T50n2060 với segment-aware prompt. Chờ owner approval.

Xem: `docs/t50n2060-repair-plan.md`
