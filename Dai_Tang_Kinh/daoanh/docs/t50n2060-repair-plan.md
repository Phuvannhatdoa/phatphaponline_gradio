# T50n2060 — Kế hoạch sửa alignment

**Work:** T50n2060 · 唐高僧傳 (Đường Cao Tăng Truyện)  
**Passage test:** 0-0457a- (liên kết Thiếu Lâm Tự, PL000000023255)  
**Trạng thái:** Lệch alignment xác nhận — xem `alignment-audit-report.md`

---

## ⚠ Cập nhật chiến lược 2026-09-04

**Không re-translate lại từ đầu.** Lý do: lãng phí token/thời gian khi bản
dịch hiện có đủ dùng với cảnh báo `≈`. Chiến lược mới:

- Giữ `vi_text` hiện tại, hiển thị `≈` (đã deploy)
- Lazy translate tiếp các passages `NULL` qua T85
- Khi user báo sai passage cụ thể → admin fix thủ công → INSERT vào
  `passage_translation_alignment` với `alignment_type='manual_verified'`
- UI tự chuyển từ `≈` sang số thật khi có alignment record

**Kế hoạch 7 bước phía dưới chỉ áp dụng khi có budget re-translate
hoặc khi passage cụ thể được báo sai (fix từng passage thay vì batch).**

---

## 1. Không làm gì trong bản sửa này

| Không làm | Lý do |
|-----------|-------|
| Re-translate batch toàn bộ T50n2060 | Lãng phí token — dùng lazy + báo sai |
| Chỉnh số display để trông "có vẻ khớp" | Không sửa gốc vấn đề |
| Xóa vi_text hiện tại | Đang dùng, backup đã có |
| Re-segment Hán văn bằng rule mới mà chưa test | Rủi ro phá raw text |
| Deploy lên VPS | Cần test local xong trước |

---

## 2. Bước sửa (theo thứ tự bắt buộc)

### Bước 0 — Backup
```bash
cp data/lineage.db data/lineage.db.backup_$(date +%Y%m%d_%H%M%S)
```
Không chạy migration nếu chưa backup.

### Bước 1 — Kiểm tra raw text T50n2060

Query:
```sql
SELECT passage_id, loc_ref, length(raw_text) as han_len, length(vi_text) as vi_len,
       translation_draft, has_vi
FROM passage
WHERE source LIKE '%T50n2060%' OR text_id LIKE '%T50n2060%'
ORDER BY loc_ref;
```

Mục tiêu xác định:
- Tổng số passages T50n2060 trong DB
- Passages nào đã có vi_text, passages nào chưa
- raw_text có bị concat không (quá dài > 2000 chars = dấu hiệu)
- Ranh giới đoạn hiện tại (loc_ref pattern)

### Bước 2 — Xác định segmentation rule ổn định cho Hán

Ưu tiên theo thứ tự:
1. **TEI boundary** nếu có trong raw_text (CBETA XML tags)
2. **Paragraph break** (`\n\n` sau khi strip `\n` scan artifacts)
3. **Sentence group** (nhóm 3–5 câu, 80–150 chars/nhóm) — đang dùng hiện tại

Test rule trên passage 0-0457a:
- Rule phải cho kết quả stable (cùng input → cùng segments)
- Phải có unit test: `test_segment_han('0457a') → expected_segments`

### Bước 3 — Thiết kế prompt dịch segment-aware

Template prompt:
```
Bạn là dịch giả Phật kinh Hán-Việt chuyên nghiệp. Dịch từng đoạn sau sang tiếng Việt.
Trả về JSON với đúng passage_id từ input.

Input:
[
  {"passage_id": "daoanh:cbeta:T50n2060:0457a:p001", "original_zh": "竊聞。六爻..."},
  ...
]

Output format bắt buộc:
{
  "translations": [
    {"passage_id": "...", "translation_vi": "..."},
    ...
  ]
}

Quy tắc:
- Không đổi, không bỏ bất kỳ passage_id nào
- Mỗi translation_vi phải là bản dịch của original_zh tương ứng
- Không gộp hoặc tách đoạn
- Không dịch passage_id
```

### Bước 4 — Validate response

Checklist tự động:
```python
def validate_translation_response(input_passages, output_json):
    input_ids = set(p['passage_id'] for p in input_passages)
    output_ids = set(t['passage_id'] for t in output_json['translations'])
    
    assert input_ids == output_ids, f"ID mismatch: {input_ids ^ output_ids}"
    
    for t in output_json['translations']:
        assert t['translation_vi'], f"Empty translation for {t['passage_id']}"
        assert not re.search(r'[一-鿿]{10,}', t['translation_vi']), \
            f"Possible Han text leak in Vi: {t['passage_id']}"
    
    return True
```

### Bước 5 — Lưu vào DB

Không overwrite `vi_text` cũ. Thêm vào bảng mới:
```sql
INSERT INTO translation_segments (translation_id, work_id, translation_text, 
    translator_type, model_name, source_passage_ids)
VALUES (?, 'T50n2060', ?, 'ai_draft', 'qwen/qwen3.8-27b', ?);

INSERT INTO passage_translation_alignment (passage_id, translation_id, 
    alignment_type, alignment_method, confidence)
VALUES (?, ?, 'exact_1_to_1', 'deterministic', 0.8);
```

### Bước 6 — Test alignment

Test bắt buộc (xem `alignment-test-cases.md`):
- TC-001: Hán 41 → Vi phải nói về dịch Đại Bát Nhã, Long Sóc 3, 600 quyển
- TC-002: Hán 41 → Vi KHÔNG được nhắc "Hiển Khánh 2, giá hạnh Lạc Dương"
- TC-003: Hover Hán 41 → highlight đúng Vi translation của Hán 41
- TC-004: Tổng số alignment records = số passages T50n2060 đã dịch

### Bước 7 — Update UI để đọc từ alignment table

Sau khi có bảng `passage_translation_alignment`:
1. API `/daoanh/api/passage/<id>/aligned-translation` trả translation theo alignment record
2. Frontend: nếu có aligned translation → hiển thị với số thứ tự thật (01, 02, ...)
3. Frontend: nếu chỉ có ordinal → hiển thị với `≈` như hiện tại

---

## 3. Test cases bắt buộc trước khi publish

```
Input: passage_id = T50n2060 · 0457a · p041
Han:   創翻大本。至龍朔三年十月末了。凡四處十六會說。總六百卷。般若空宗此焉周盡。...
Vi phải có:
  ✓ Đề cập Đại Bát Nhã (大般若經)
  ✓ Đề cập Long Sóc năm 3 (龍朔三年)
  ✓ Đề cập 600 quyển (六百卷)
  ✓ Đề cập bốn nơi, mười sáu hội (四處十六會)
  ✓ Đề cập Bát Nhã Không tông (般若空宗)
  ✗ KHÔNG được đề cập "Hiển Khánh 2" (顯慶二年)
  ✗ KHÔNG được đề cập "giá hạnh Lạc Dương"
```

---

## 4. Timeline ước tính

| Bước | Thời gian | Phụ thuộc |
|------|-----------|-----------|
| 0 Backup | 5 phút | — |
| 1 Audit raw text | 30 phút | — |
| 2 Xác định segment rule | 1 ngày | Step 1 |
| 3 Design prompt | 2 giờ | Step 2 |
| 4 Re-translate T50n2060 | 1 ngày (API time) | Step 3 |
| 5 Validate + lưu DB | 2 giờ | Step 4 |
| 6 Test alignment | 2 giờ | Step 5 |
| 7 Update UI | 1 ngày | Step 6 + alignment schema |

**Không thể hoàn thành trong 1 session.** Cần chia thành ít nhất 2–3 sessions.

---

*Xem thêm: `alignment-audit-report.md` · `bilingual-passage-alignment-design.md` · `alignment-test-cases.md`*
