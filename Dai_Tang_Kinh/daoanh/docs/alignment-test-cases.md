# Alignment Test Cases — Bilingual Reader

**Mục đích:** Xác nhận alignment đúng trước khi publish bất kỳ bản dịch nào  
**Format:** Mỗi test case có: ID · Input · Expected · Fail condition

---

## TC-001 — Đoạn Hán 41 (T50n2060) phải khớp nội dung

**Input Hán:**
```
創翻大本。至龍朔三年十月末了。凡四處十六會說。總六百卷。般若空宗此焉周盡。
於間又翻成唯識論辯中邊論唯識二十論品類足論等。
```

**Expected Vi (phải chứa ít nhất 4/5 yếu tố):**
- ✅ Đề cập "Đại Bát Nhã" hoặc "大般若" hoặc "bát nhã"
- ✅ Đề cập "Long Sóc" hoặc "龍朔" hoặc năm hoàn thành dịch
- ✅ Đề cập "sáu trăm quyển" hoặc "600 quyển" hoặc số 600
- ✅ Đề cập "bốn nơi" hoặc "mười sáu hội" hoặc "bốn chỗ"
- ✅ Đề cập "Duy Thức" hoặc "Biện Trung Biên" hoặc "Phẩm Loại Túc"

**Fail condition (KHÔNG được xuất hiện trong Vi đoạn 41):**
- ❌ "Hiển Khánh" (顯慶) — thuộc Hán đoạn 33
- ❌ "Lạc Dương" hoặc "Lạc Dương" — thuộc Hán đoạn 33
- ❌ "giá hạnh" hoặc "xa giá" — thuộc Hán đoạn 33

---

## TC-002 — 1:1 mapping kiểm tra đơn vị

**Input:** 3 passage_id liên tiếp → 3 translation records  
**Expected:** alignment table có đúng 3 records, không duplicate, không gap

```sql
-- Verify
SELECT COUNT(*) FROM passage_translation_alignment 
WHERE passage_id IN ('p001', 'p002', 'p003');
-- = 3 (không hơn, không kém)

SELECT COUNT(DISTINCT passage_id) FROM passage_translation_alignment
WHERE passage_id IN ('p001', 'p002', 'p003');
-- = 3 (không duplicate)
```

---

## TC-003 — Hover sync dựa trên alignment record

**Input:** User hover vào Hán 41  
**Expected:**
- Vi column highlights translation có `alignment_id` tương ứng
- KHÔNG highlights Vi chunk theo ordinal
- Tooltip hiển thị passage_id và alignment method

**Fail:** Vi số 41 được highlight dù nội dung là "Hiển Khánh 2"

---

## TC-004 — Batch LLM trả sai thứ tự

**Input batch:**
```json
[{"passage_id": "p001", "original_zh": "A"}, {"passage_id": "p002", "original_zh": "B"}]
```
**LLM response (đảo thứ tự):**
```json
[{"passage_id": "p002", "translation_vi": "..."}, {"passage_id": "p001", "translation_vi": "..."}]
```
**Expected:** Validate phát hiện đảo thứ tự → vẫn lưu đúng theo passage_id (không theo array index)  
**Fail:** Lưu p001 translation của p002 vì chỉ dùng array index

---

## TC-005 — LLM thiếu passage trong response

**Input:** 3 passage_ids  
**LLM response:** Chỉ trả 2 passages (thiếu p003)  
**Expected:** Raise validation error, không lưu batch, đánh dấu needs_retry  
**Fail:** Lưu 2 records và tạo alignment thiếu p003

---

## TC-006 — LLM trả dư passage không có trong input

**Input:** 2 passage_ids: p001, p002  
**LLM response:** Trả 3 passages: p001, p002, p003  
**Expected:** Raise validation error ("unexpected passage_id: p003")  
**Fail:** Lưu p003 vào DB dù không có trong input

---

## TC-007 — Vi text rỗng

**LLM response:** `{"passage_id": "p001", "translation_vi": ""}`  
**Expected:** Raise validation error ("empty translation")  
**Fail:** Lưu empty string, has_vi=true

---

## TC-008 — Hán văn xuất hiện trong bản Việt

**LLM response:** `{"passage_id": "p001", "translation_vi": "Đây là bản dịch. 創翻大本至龍朔三年。Tiếp tục..."}`  
**Expected:** Warning ("possible Han text in Vi translation") + đánh dấu needs_review  
**Fail:** Lưu và publish mà không cảnh báo

---

## TC-009 — Many-to-one alignment (1 Vi dịch nhiều Hán)

**Trường hợp:** Hai câu Hán liên tiếp (p040, p041) được dịch làm 1 đoạn Việt  
**Input alignment:**
```
passage_id: p040 → translation_id: vi_040_041
passage_id: p041 → translation_id: vi_040_041
alignment_type: 'many_source_to_one'
```
**Expected UI:**
- Hover Hán 40 → highlight Vi "đoạn 40–41"
- Hover Hán 41 → highlight cùng Vi "đoạn 40–41"
- Hover Vi "đoạn 40–41" → highlight CẢ Hán 40 VÀ Hán 41

---

## TC-010 — Missing alignment record

**Trường hợp:** Hán passage có raw_text nhưng không có alignment record  
**Expected UI:**
```
[!] Đoạn Hán này chưa có bản dịch được căn chỉnh.
Không dùng để đối chiếu học thuật.
```
**Fail:** Hiển thị Vi chunk theo ordinal mà không cảnh báo

---

## TC-011 — Raw hash mismatch

**Trường hợp:** raw_text trong DB bị thay đổi nhưng vi_text chưa được cập nhật  
**Expected:** Detect hash mismatch, đánh dấu `alignment_status = 'stale'`, hiển thị cảnh báo  
**Fail:** Vẫn display như alignment đúng

---

## Chạy test

Chưa có automated test runner. Cần implement trong `scripts/test_alignment.py`:

```python
def test_tc001_han41_content():
    """Han 41 must mention Prajnaparamita translation, not Xiancheng 2"""
    vi_text = get_translation('daoanh:cbeta:T50n2060:0457a:p041')
    assert any(k in vi_text for k in ['Bát Nhã', 'Long Sóc', '600', 'Duy Thức'])
    assert 'Hiển Khánh' not in vi_text or 'thứ năm' in vi_text  # năm 5, không phải 2
    assert 'Lạc Dương' not in vi_text
```

Xem `t50n2060-repair-plan.md` §6 để biết cách chạy tests sau khi repair.
