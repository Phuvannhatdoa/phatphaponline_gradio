# CBETA Corpus Audit — Hiện trạng và rủi ro

**Ngày:** 2026-09-04  
**Phạm vi:** Bảng `passage` trong `data/lineage.db`  
**Trạng thái:** Audit plan — cần chạy queries để có số liệu thực tế

---

## 1. Queries audit cần chạy (read-only)

### 1.1 Tổng quan corpus

```sql
-- Tổng passages và trạng thái dịch
SELECT 
    COUNT(*) as total_passages,
    SUM(CASE WHEN has_vi THEN 1 ELSE 0 END) as has_vi,
    SUM(CASE WHEN translation_draft THEN 1 ELSE 0 END) as is_draft,
    SUM(CASE WHEN raw_text IS NULL OR raw_text = '' THEN 1 ELSE 0 END) as empty_han,
    SUM(CASE WHEN vi_text IS NULL OR vi_text = '' THEN 1 ELSE 0 END) as empty_vi,
    AVG(length(raw_text)) as avg_han_len,
    MAX(length(raw_text)) as max_han_len,
    MIN(length(raw_text)) as min_han_len
FROM passage;
```

### 1.2 Phân phối theo source (CBETA work)

```sql
SELECT source, COUNT(*) as count, 
       SUM(CASE WHEN has_vi THEN 1 ELSE 0 END) as translated,
       AVG(length(raw_text)) as avg_han_len
FROM passage
GROUP BY source
ORDER BY count DESC;
```

### 1.3 Phát hiện raw_text quá dài (dấu hiệu concat nhiều blocks)

```sql
-- Passages dài hơn 2000 chars = có thể bị concat không đúng
SELECT passage_id, source, loc_ref, length(raw_text) as len, 
       LEFT(raw_text, 100) as preview
FROM passage
WHERE length(raw_text) > 2000
ORDER BY len DESC;
```

### 1.4 Phát hiện duplicate raw_text

```sql
-- raw_text trùng nhau giữa các passages
SELECT raw_text, COUNT(*) as cnt, GROUP_CONCAT(passage_id) as ids
FROM passage
WHERE raw_text IS NOT NULL AND raw_text != ''
GROUP BY raw_text
HAVING cnt > 1
ORDER BY cnt DESC;
```

### 1.5 Sequence gaps

```sql
-- Kiểm tra loc_ref pattern để phát hiện gap
SELECT source, loc_ref,
       LAG(loc_ref) OVER (PARTITION BY source ORDER BY loc_ref) as prev_ref
FROM passage
WHERE source IS NOT NULL
ORDER BY source, loc_ref;
```

### 1.6 vi_text count mismatch estimate

```sql
-- Passages có vi_text nhưng vi_text rất ngắn (có thể bị truncate)
SELECT passage_id, source, loc_ref, 
       length(raw_text) as han_len, length(vi_text) as vi_len,
       ROUND(CAST(length(vi_text) AS FLOAT) / length(raw_text), 2) as vi_han_ratio
FROM passage
WHERE has_vi = 1 AND vi_text IS NOT NULL
ORDER BY vi_han_ratio ASC
LIMIT 20;
-- vi_han_ratio < 1.0 = Vi ngắn hơn Hán (bình thường < 1.5)
-- vi_han_ratio < 0.5 = Vi có thể bị cắt
-- vi_han_ratio > 5.0 = Vi có thể bị duplicate hoặc lẫn text
```

### 1.7 Phát hiện Hán văn trong vi_text

```sql
-- vi_text chứa nhiều Hán tự (> 10 chars liên tiếp = suspicious)
SELECT passage_id, source, 
       substr(vi_text, 1, 200) as vi_preview
FROM passage  
WHERE vi_text REGEXP '[一-鿿]{10,}'
LIMIT 20;
-- Nếu SQLite không hỗ trợ REGEXP: dùng Python script thay thế
```

### 1.8 Orphan citations/entity mentions

```sql
-- Entity mentions trỏ vào passages không còn tồn tại
SELECT em.passage_id, COUNT(*) as orphan_count
FROM entity_mentions em
LEFT JOIN passage p ON em.passage_id = p.passage_id
WHERE p.passage_id IS NULL
GROUP BY em.passage_id;
```

---

## 2. Rủi ro đã biết

| Rủi ro | Mức độ | Nguồn |
|--------|--------|-------|
| Ordinal alignment Vi–Hán | CRITICAL | Confirmed (alignment-audit-report.md) |
| raw_text quá dài (có thể concat) | HIGH | Chưa verify |
| Duplicate raw_text | MEDIUM | Chưa verify |
| vi_text bị truncate | HIGH | Dấu hiệu từ 42–54 báo "chưa có dịch" |
| Hán văn lẫn vào vi_text | MEDIUM | Chưa verify |
| Orphan entity mentions | MEDIUM | Chưa verify |
| Missing passage_id hash | HIGH | Column chưa tồn tại |
| Sequence gap trong corpus | LOW | Chưa verify |

---

## 3. Điều chưa có trong DB hiện tại

| Cần có | Trạng thái |
|--------|-----------|
| `raw_zh_hash` column | ❌ Không có |
| `segmentation_method` column | ❌ Không có |
| `source_version` column | ❌ Không có |
| `import_run_id` column | ❌ Không có |
| `tei_anchor_start/end` columns | ❌ Không có |
| Bảng `text_passages` (stable IDs) | ❌ Không có |
| Bảng `translation_segments` | ❌ Không có |
| Bảng `passage_translation_alignment` | ❌ Không có |

---

## 4. Hành động tiếp theo

Sau khi chạy queries audit:

1. Document kết quả thực tế vào phần này
2. Prioritize repairs theo mức độ nghiêm trọng
3. Tạo migration plan với số records chính xác
4. Không batch migrate cho đến khi có approval

---

## 5. Script audit tổng hợp

File: `scripts/audit_cbeta_corpus.py`  
Cần tạo (chưa có). Sẽ chạy tất cả queries trên và output:
- `docs/cbeta-corpus-audit-results-{date}.json`
- `docs/cbeta-corpus-audit-results-{date}.md` (human-readable summary)

**Chạy:** `python scripts/audit_cbeta_corpus.py > docs/cbeta-corpus-audit-results-$(date +%Y%m%d).md`

---

*Xem thêm: `cbeta-global-passage-standard.md` · `cbeta-migration-rollout-plan.md`*
