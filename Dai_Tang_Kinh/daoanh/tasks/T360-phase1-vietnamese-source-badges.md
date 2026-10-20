---
id: T360
title: "Phase 1 Stabilization: Add Vietnamese Source Confidence Badges (PRIORITY 1)"
status: in_progress
created: 2026-10-12
updated: 2026-10-12
parent: null
former_ids: []
depends_on: []
done_when:
  - "Tất cả bảng person.html + places.html hiển thị source badge (DILA/ZQ/TTL/Admin)"
  - "Badge theo format: '[nguồn] confidence: X.X' (ví dụ: '[ZQ tự động] confidence: 0.5')"
  - "Admin có thể click badge để xem giải thích nguồn dữ liệu"
  - "QA kiểm chứng trên browser: 5+ monks/places khác nhau → source badge hiển thị đúng"
  - "Code + UI + docs hoàn thành, commit đầu tiên của Phase 1"
---

## Context

Sau audit kiến trúc (Plan agent), phát hiện **Issue #8: Vietnamese Translation Source Confusion**.

Vấn đề: DB trộn lẫn ZQ (tự động, confidence 0.5) với DILA (authority, confidence 1.0) mà không badge rõ.
→ User không biết tên nào là "verified" hay "auto-generated".

**T359 Fix 1-3** sắp complete, nhưng thiếu source badge → cần fix trước khi submit.

---

## Phạm Vi (Scope)

### 1. Code Changes (app.py + person.html + places.html)

**app.py** (API endpoints):
- Thêm field `source_of_name_vi` → `/api/persons/<id>`
- Thêm field `confidence_name_vi` → `/api/persons/<id>` + `/api/places/<id>`
- Query từ `people` table: `SELECT source_id, confidence FROM people WHERE id=?`

**person.html** (person detail page):
- Thêm badge dưới tên tiếng Việt: `[ZQ tự động] confidence: 0.5`
- onClick → popup giải thích: "ZQ = phiên âm tự động từ tên Hán"
- Áp dụng cho: name_vi, place names, work names

**places.html** (place detail page):
- Tương tự person.html
- Badge cho name_vi, related person names

### 2. Database Check (Read-only)

- Audit `vn_person_authority.source_id` (DILA=1, ZQ=5, etc.)
- Audit `people.name_vi` → origin (DILA vs ZQ)
- Audit `places.name_vi` → origin

### 3. UI/UX

- Badge design: Small, unobtrusive (không chiếm dung lượng)
- Tooltip on hover: "Tên này được tạo tự động bởi ZQ. Confidence: 0.5"
- Color code: Green (DILA, 1.0), Yellow (TTL/Admin, 0.8-0.9), Gray (ZQ, 0.5)

### 4. Documentation

- Update `AGENTS.md` §2 (source tagging rule)
- Add comment in code: `# Source: DILA=1, ZQ=5, TTL=3, Admin=7`
- Write doc: `docs/integration/SOURCE_TAGGING.md`

---

## Kế Hoạch Thực Hiện

1. **Audit DB** (30 phút)
   - Check `people.source_id` + confidence distribution
   - Check `places.name_vi` source

2. **Modify app.py** (1 hour)
   - Add `source_of_name_vi` + `confidence_name_vi` fields
   - Query `vn_person_authority.source_id` when available

3. **Update person.html** (2 hours)
   - Add badge HTML element
   - Add onClick → tooltip
   - CSS styling (color code)

4. **Update places.html** (2 hours)
   - Same as person.html

5. **Test + Screenshot** (1 hour)
   - Browser test: 5+ monks/places with different sources
   - Verify badge color, tooltip, layout

6. **Documentation** (1 hour)
   - Update AGENTS.md + add SOURCE_TAGGING.md

7. **Commit + Push** (30 phút)

**Total: 8-9 hours (1 working day)**

---

## Lợi Ích

✅ **Admin** (no-coding) → Hiểu rõ dữ liệu nào "official" (DILA) vs "auto-generated" (ZQ)  
✅ **T359 Fix 1-3** → Hoàn thiện trước khi submit  
✅ **Trust** → User thấy source → tin tưởng dữ liệu hơn  
✅ **Phase 1 Quick Win** → Nhanh, impact cao  

---

## Dependency

- Không phụ thuộc task khác
- Có thể start ngay sau khi T309 + T359 approve

---

## Người Phụ Trách

- **Code Fix**: daoanh-debugger
- **QA Verify**: daoanh-qa (browser test)
- **Điều Phối**: Coordinator (me)
