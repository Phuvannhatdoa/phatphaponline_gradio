---
id: T66
title: "Place Description VI — Lexicon ĐỊA DANH 15,863 entries → place note_vi"
module: Place Authority / DILA
priority: medium
status: pending
depends_on: [T48]
created: 2026-08-27
updated: 2026-08-27
done_when: ≥5,000 DILA places được bổ sung note_vi hoặc description_vi từ lexicon ĐỊA DANH; bảng place_desc_vi_draft tồn tại
---

# T61 — Place Description VI từ Lexicon ĐỊA DANH

## Vấn đề

Hiện tại places chỉ có `name_vi` (tên Việt) nhưng không có mô tả tiếng Việt nào.
Người dùng tra "Thiếu Lâm Tự" nhận được tọa độ GPS + danh sách nhân vật nhưng không có
một dòng nào giải thích đây là ngôi chùa gì.

Lexicon ĐỊA DANH trong DB có **15,863 entries** với definitions tiếng Việt mô tả
các địa danh Phật giáo — đây là tài nguyên sẵn có chưa được dùng.

## Cơ chế

T48 (Done) đã build reverse index từ lexicon → DILA places.
T61 extends T48: thay vì chỉ verify tên, còn **copy definition làm description_vi draft**.

```sql
-- Tìm places có lexicon ĐỊA DANH match (via T48 đã làm)
SELECT p.id, p.name_vi, p.name_zh, l.definition, l.headword
FROM places_dila p
JOIN lexicon l ON l.headword = p.name_vi
WHERE l.source LIKE '%DIA_DANH%'
  AND l.definition IS NOT NULL
  AND LENGTH(l.definition) > 30
  AND p.note_vi IS NULL
```

## Schema

```sql
CREATE TABLE IF NOT EXISTS place_desc_vi_draft (
    place_id TEXT PRIMARY KEY,
    name_vi TEXT,
    desc_vi_draft TEXT,
    source_lexicon_id INTEGER,
    match_type TEXT,  -- 'exact_name' | 'alias' | 'note'
    char_count INTEGER,
    admin_approved INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
```

## Acceptance Criteria

- [ ] Script `t61_place_desc_vi_lexicon.py` chạy, tạo `place_desc_vi_draft`
- [ ] ≥5,000 places có description draft (ước tính từ 15,863 ĐỊA DANH entries)
- [ ] Avg char_count ≥80 characters per description
- [ ] Admin review 30 samples — xác nhận chất lượng phù hợp
- [ ] API endpoint `/places/<id>` cập nhật để trả về `note_vi` nếu có (sau admin approve)
- [ ] Frontend: hiển thị note_vi dưới tên địa danh trong Place Detail panel

## Timeline enrichment bonus

Nhiều entries ĐỊA DANH có ngày thành lập trong definition ("创建于唐代..." hoặc "建于宋...").
Nếu extract được: thêm vào `place_timeline_events` — synergy với T59.

## Liên quan

- T48 (Done): Reverse index lexicon → DILA places (foundation cho T61)
- T59: Wikidata timeline import — có thể kết hợp extract dates từ description
- T47 (Done): Place VI_NAME verification 
- `lexicon` table: source 'DIA_DANH' = 15,863 entries

## Phê Chuẩn

Được phê chuẩn trong chiến lược PTDA 2026-08-27 (Phase B — Khai Thác Lexicon Toàn Diện).
