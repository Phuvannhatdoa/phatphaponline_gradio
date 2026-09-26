# Place Graph Display Spec — Nexus / Đồ Thị Tab

**Version:** 1.0  
**Date:** 2026-09-07  
**Reference entity:** Thiếu Lâm Tự (少林寺) — `PL000000023255`

---

## 1. Root Node

```json
{
  "root": {
    "name": "Thiếu Lâm Tự (少林寺)",
    "type": "Địa danh",
    "id": "PL000000023255"
  }
}
```

**Rule:** Luôn hiển thị Việt trước - Hán sau: `Thiếu Lâm Tự (少林寺)`; chỉ dùng nhãn đã xác nhận từ record.

---

## 2. Aliases

```json
{
  "aliases": [
    "Trắc Hộ Tự (陟岵寺)",
    "Tăng Nhân Tự (僧人寺)",
    "Thiếu Lâm (少林)",
    "Thiếu Thất Tự (少室寺)"
  ]
}
```

**Rule:** Hiển thị alias dạng chips cạnh/dưới root; mỗi chip giữ nguyên tên nguồn, không tự dịch hoặc tự gộp.

---

## 3. Group Structure

```json
{
  "groups": {
    "kinh_dien": 3,
    "tang_nhan": {
      "Đường": 12,
      "Tống": 10,
      "Minh": 2
    }
  }
}
```

---

## 4. Display Rules

### 4.1 Default View
Hiển thị root + 2 group node: **Kinh điển** và **Tăng nhân**  
Tree mặc định mở 3 đời:
- Đời 0: Root
- Đời 1: Group nodes (Kinh điển, Tăng nhân)
- Đời 2: Subgroup theo nguồn/thời kỳ (ví dụ: Tăng nhân → Đường / Tống / Minh)
- Đời 3: Record con (nếu có) — chỉ khi người dùng expand subgroup

### 4.2 Expand (Lazy)
- Click group → mở subgroup theo nguồn
- Click subgroup → mở record con
- **Không tải/hiển thị toàn bộ graph ngay từ đầu**

---

## 5. Edge Types

| Type | Visual | Hiển thị mặc định | Điều kiện |
|------|--------|--------------------|-----------|
| `with_evidence` | Solid | Có | Phải có: subject ID, predicate, object ID, evidence record, source locator (hoặc lý do thiếu locator), review status |
| `partial` | Solid + badge PARTIAL | Có | Thiếu ≥1 trường evidence/provenance; badge hiển thị lý do thiếu |
| `co_mention` | Dotted | **Hidden** (default) | Chỉ hiện khi bật filter Research/Admin; không diễn giải là quan hệ trực tiếp |
| `unverified` | - | **Hidden** (default) | Chỉ hiện trong Research/Admin mode; không trình bày như kết luận |

---

## 6. Label Fallback Chain

```
name_vi > preferred_label_vi > display_name > name_han/name_zh > source_label > canonical_id
```

**Tuyệt đối không để node/card rỗng.**

---

## 7. Logging Rule (bắt buộc trước khi sửa)

Trước khi sửa bất kỳ bug nào liên quan đến Nexus/Đồ Thị:

1. Ghi vào `docs/bugs.md`: bug ID, URL/route, root entity ID, thời gian, ảnh/log console/API payload, expected vs actual
2. **Không đánh dấu DONE hoặc sửa log lịch sử** cho đến khi Admin xác nhận "fixed DONE"
3. Khi Admin xác nhận: thêm mục `resolution` gồm commit hash, changed files, test evidence, người xác nhận, timestamp

---

## 8. Audit — Current vs Spec

### ✅ Đã có

| Feature | Nơi implement |
|---------|--------------|
| Root display Vi-Hán | `renderNexusTab` → `nmp-name-vi/nmp-name-zh` |
| Alias chips | `_gmpRenderAliasChips()` (~line 3831) + `#nmp-aliases` |
| Group nodes Kinh điển / Tăng nhân | `_renderVisGraph` groups map |
| Subgroup expand (Đường/Tống/Minh) | `_gmpExpandPersonGroup()` + `_gmpExpandSubgroup()` |
| Co-mention hidden default | `_graphFilters.alias = false` (off by default) |
| Label fallback cơ bản | `label||label_zh||id` trong node render |

### ❌ Chưa có / Cần sửa

| Gap | Spec Rule | Priority |
|-----|-----------|----------|
| Edge `PARTIAL` badge khi thiếu provenance | §5 partial edge | HIGH |
| Edge `with_evidence` strict check (subject+predicate+object+source locator+review_status) | §5 evidence check | HIGH |
| `unverified` edges hidden default (Research/Admin only) | §5 unverified | MEDIUM |
| Label fallback đầy đủ (`preferred_label_vi > display_name > name_han > source_label`) | §6 full chain | MEDIUM |
| `bugs.md` logging workflow | §7 logging | MEDIUM |
| Default 3-đời tree view (root+group+subgroup load sẵn) | §4.1 default view | LOW* |

*Hiện tại collapsed mặc định — cần 2 click để thấy subgroup. Spec yêu cầu mở sẵn đến đời 2.

---

## 9. Next Steps

- Tạo `docs/bugs.md` để track bugs Nexus/Đồ Thị
- Implement PARTIAL badge edge
- Kiểm tra evidence completeness trong API `api_nexus` / `api_places_graph`
- Bổ sung `preferred_label_vi` vào label fallback chain
