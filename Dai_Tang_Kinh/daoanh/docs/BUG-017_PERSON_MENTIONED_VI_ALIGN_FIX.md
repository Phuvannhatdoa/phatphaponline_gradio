# BUG-017 — Canh lề sai "Được đề cập trong 🇻🇳": dòng 2 lệch 1 space so với dòng 1

**Báo cáo:** Admin, 2026-09-29  
**Trang:** `/daoanh/admin/person.html?id=A000001`  
**Trạng thái:** ✅ Fixed (chờ Admin confirm trên UI)

---

## Mô tả lỗi

Trong phần "Được đề cập trong 🇻🇳" của admin person page:

```
Phổ Tổ Thống Ký (佛祖統紀) quyển 46
 Tân Tục Cao Tăng Truyện Tứ Tập (新續高僧傳四集) quyển 1   ← lệch 1 space
```

Dòng 2 bị thụt vào 1 khoảng trắng so với dòng 1.

---

## Nguyên nhân gốc

Block "Được đề cập trong" trong `admin/person.html` build HTML **thủ công**, bỏ qua hàm `cellVi()`.

Hàm `cellVi()` (line 160-175) có logic:
```javascript
var display = MULTILINE_KEYS[key_vi] ? normMultiline(val_vi) : val_vi;
```

`mentioned_in_vi` nằm trong `MULTILINE_KEYS` nhưng block này không gọi `cellVi()` → không apply `normMultiline()` → leading space trong data được giữ nguyên → render với `white-space:pre-wrap` hiển thị lệch.

---

## Fix

**File:** `daoanh/admin/person.html`  
**Line 295:**

```diff
- var mentioned_vi = vi_.mentioned_in_vi || '';
+ var mentioned_vi = normMultiline(vi_.mentioned_in_vi || '');
```

`normMultiline()` trim từng dòng và loại dòng rỗng — nhất quán với cách `cellVi()` xử lý các field MULTILINE khác (`works_by_vi`, `bio_concise_vi`, v.v.).

---

## Phạm vi ảnh hưởng

- Chỉ `admin/person.html` — không chạm backend, không chạm DB
- Display fix thuần client-side
- Textarea edit cũng được normalize → nếu admin save lại sẽ tự clean data trong DB

---

## Backup

`docs/sessions/2026-09-29/person.html.bak`
