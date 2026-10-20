# Session: Nexus Person-Type Grouped View

**Ngày:** 2026-09-05  
**Task:** T16 — person-type Nexus grouped view theo JSON spec (Minh Xán A007073)

---

## Thay đổi

### 1. `app.py` — `api_nexus()` (line ~5202)

Thêm person branch cho aliases + groups:

**`aliases`** (person): Từ `people.name_zh/name_vi` + `marcus_reference.label/label_vi`, dedup với center label.

**`groups`** (person):
```json
{
  "kinh_dien": {"CBETA": 1},
  "tang_nhan": {"Marcus": 0, "DILA": 1}
}
```
- CBETA = COUNT(DISTINCT sigla) từ `event_text_link`
- Marcus = COUNT(*) từ `marcus_networks WHERE teacher_id=? OR student_id=?`
- DILA = COUNT(*) từ `people WHERE id=?` (luôn = 1)

Marcus teacher/student relation nodes + edges thêm vào `nodes`/`edges` list.

### 2. `places.html` — `_nexusRenderGrouped()` (line ~5002)

Thêm person branch trước place branch:
- Default (collapsed): 3 nút — center + "Hồ sơ DILA" + "Truyền thừa Marcus"
- Marcus group node: label "(chưa có)" khi count=0, vàng khi count>0
- Click DILA group → expand place nodes (filter `n.group === 'place'`)
- Click Marcus group → expand person nodes HOẶC notice "Chưa tìm thấy\nquan hệ truyền thừa Marcus" nếu mPersons.length === 0

### 3. `places.html` — `_nexusGroupedFinalize()` (line ~5151) — MỚI

Extract inline finalize code từ place branch thành helper function riêng:
- Shared giữa person branch (return call tại line 5079) và place branch (call tại line 5148)
- Handles: vis.Network creation, click event (group/subgroup/person routing), empty state

---

## Verified (A007073 Minh Xán)

| Test | Kết quả |
|------|---------|
| API aliases | `["釋明璨", "Minh Xán"]` ✓ |
| API groups | `{kinh_dien:{CBETA:1}, tang_nhan:{Marcus:0, DILA:1}}` ✓ |
| Default 3-node view | center + DILA + Marcus ✓ |
| Alias chips header | "明璨 · Minh Xán" hiển thị ✓ |
| Marcus=0 notice | "Chưa tìm thấy quan hệ truyền thừa Marcus" ✓ |
| DILA expand | 7 place nodes từ `event_text_link` ✓ |

---

## Ghi chú

- `_nexusData` phải set trước khi gọi `_nexusRenderGrouped` (assigned ở outer fetch callback, không trong `_renderNexusMainPanel`).
- Restart server bắt buộc sau mỗi lần sửa `app.py`.
