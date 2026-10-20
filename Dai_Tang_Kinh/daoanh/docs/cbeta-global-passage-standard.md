# CBETA Global Passage Standard — Đạo Ảnh

**Ngày quyết định:** 2026-09-04  
**Quyết định kiến trúc:** Canonical CBETA anchor + internal immutable passage ID  
**Phạm vi:** TOÀN BỘ Hán văn CBETA được import, index, hiển thị hoặc dùng làm evidence

---

## 1. Nguyên tắc bất biến

1. **Không dùng số thứ tự render (ordinal index) làm khóa liên kết** bất kỳ pair nào:
   - Hán ↔ Việt
   - passage ↔ entity mention (citation)
   - passage ↔ lineage evidence
   - passage ↔ deep search result

2. **Passage ID là stable identifier**, không thay đổi sau khi tạo.

3. **Bản Việt không được map bằng array index** — phải có bảng `passage_translation_alignment`.

4. **Evidence trong Lineage/Graph phải trỏ:**  
   `evidence_record → daoanh passage_id → CBETA canonical anchor`

5. **Segmentation phải deterministic** — cùng input → cùng output mọi lúc.

---

## 2. Passage ID Standard

### Format
```
daoanh:cbeta:{work_id}:{page_anchor}:p{seq:03d}
```

### Ví dụ
```
daoanh:cbeta:T50n2060:0457a:p001
daoanh:cbeta:T51n2076:0220b:p041
daoanh:cbeta:X83n1592:0142c:p007
```

### Quy tắc đặt tên
| Trường | Nguồn | Ví dụ |
|--------|-------|-------|
| `work_id` | CBETA sigla | T50n2060 |
| `page_anchor` | CBETA loc_ref (strip dấu gạch) | `0-0457a-` → `0457a` |
| `seq` | Thứ tự trong block (0-padded 3 chữ số) | p001 |

**Không** dùng:
- `p1`, `p41` (không padding)
- `passage-001` (dư chữ)
- `T50n2060-p1` (thiếu page anchor)

---

## 3. Segmentation Priority

Ưu tiên theo thứ tự:

| Ưu tiên | Method | Khi dùng |
|---------|--------|---------|
| 1 | **TEI `<p>` tag** | CBETA XML có đủ TEI markup |
| 2 | **TEI `<lg>`/`<l>` tag** | Đoạn kệ, bài thơ |
| 3 | **CBETA lb anchor** | Có page-line markers (`<lb n="..."/>`) |
| 4 | **Semantic break** | `\n\n` sau khi strip scan artifacts |
| 5 | **Punctuation group** | Nhóm 3–5 câu theo `。；！？` (fallback hiện tại) |

**Không segment** bằng:
- Character count đơn thuần
- Random split
- LLM suggestion (không deterministic)

---

## 4. Trường bắt buộc trong `text_passages`

| Trường | Bắt buộc | Ghi chú |
|--------|----------|---------|
| `passage_id` | ✅ | Format daoanh:cbeta:... |
| `work_id` | ✅ | CBETA sigla |
| `source_system` | ✅ | 'CBETA' |
| `sequence_no` | ✅ | Thứ tự trong block, chỉ để sort |
| `original_zh` | ✅ | Bất biến sau khi tạo |
| `raw_zh_hash` | ✅ | SHA-256 |
| `segmentation_method` | ✅ | Tên method (tei_p, punctuation, ...) |
| `source_version` | ✅ | CBETA version ngày import |
| `canonical_ref` | Nên có | CBETA page/line ref |
| `tei_anchor_start` | Nếu có | Từ CBETA XML |
| `tei_anchor_end` | Nếu có | |

---

## 5. Evidence và Citation Rules

Mọi citation/evidence phải có:
```json
{
  "passage_id": "daoanh:cbeta:T50n2060:0457a:p041",
  "work_id": "T50n2060",
  "canonical_ref": "T50n2060_p0457a",
  "source_system": "CBETA",
  "source_url": "https://cbetaonline.dila.edu.tw/...",
  "confidence": 0.85
}
```

**Không** chấp nhận evidence với:
- `passage_id` null hoặc generated từ ordinal
- Chỉ có `loc_ref` không có passage_id
- `passage_id` không tìm thấy trong `text_passages`

---

## 6. Không thay đổi raw_zh sau khi import

Một khi `original_zh` đã lưu:
1. Không chỉnh sửa trực tiếp
2. Không append/trim
3. Nếu phát hiện lỗi: tạo `text_passages_corrections` record + audit log
4. Hash mismatch phải tạo alert

---

## 7. UI Rules

- **Số 01/02/03** chỉ là số đọc tiện lợi, không là định danh học thuật
- **Hiển thị CBETA reference và passage_id** khi mở chi tiết segment
- **Nếu chưa có alignment**: "AI draft phân phối tự động — số ≈ không khớp nội dung"
- **Nếu có alignment**: hiển thị đúng số và tooltip với passage_id
- **Click Hán ↔ Việt** chỉ theo alignment record, không theo ordinal

---

## 8. Áp dụng toàn cầu

Quyết định này áp dụng cho TẤT CẢ CBETA works hiện có và trong tương lai:
- T (Taisho)
- X (Xu zangjing)
- FOSIZHI
- Và mọi work khác được import vào hệ thống

Không exempt bất kỳ work nào khỏi yêu cầu passage_id và alignment record.

---

*Xem thêm: `bilingual-passage-alignment-design.md` · `cbeta-corpus-audit.md` · `cbeta-migration-rollout-plan.md`*
