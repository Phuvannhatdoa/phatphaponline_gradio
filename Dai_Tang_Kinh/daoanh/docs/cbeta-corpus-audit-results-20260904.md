# CBETA Corpus Audit — Kết quả 20260904

**Chạy:** 2026-09-04 22:35  
**Script:** `scripts/audit_cbeta_corpus.py`  
**DB:** `data/lineage.db`  
**Trạng thái:** Read-only — không thay đổi dữ liệu

---

## 1. Tổng quan

| Chỉ số | Giá trị |
|--------|---------|
| total_passages | 7563 |
| has_vi | 218 |
| is_draft | 218 |
| empty_han | 0 |
| empty_vi | 7345 |
| avg_han_len | 210.2 |
| max_han_len | 8034 |
| min_han_len | 5 |

## 2. Phân phối theo work (text_id)

| text_id | total | translated | avg_han | max_han |
|---------|-------|-----------|---------|---------|
| T51n2076 | 3917 | 194 | 116.0 | 6306 |
| T50n2061 | 1346 | 7 | 241.9 | 2558 |
| T50n2060 | 1037 | 13 | 444.2 | 8034 |
| X77n1524 | 1016 | 3 | 291.3 | 3759 |
| T50n2062 | 247 | 1 | 214.6 | 1997 |

## 3. Rủi ro phát hiện

| Rủi ro | Số lượng | Mức độ |
|--------|---------|--------|
| Passages > 2000 chars (concat?) | 20 | HIGH |
| Duplicate raw_text | 0 | OK |
| Hán văn trong vi_text | 0 | OK |
| Orphan passage_entity | 0 | OK |
| Alignment schema (text_passages) | ❌ Chưa có | CRITICAL |
| Hash column (raw_zh_hash) | ❌ Chưa có | HIGH |

## 4. Hành động tiếp theo

- [ ] **Phase 1**: Tạo `text_passages` + `translation_segments` + `passage_translation_alignment` (additive, không đụng data cũ)
- [ ] **Phase 2**: Pilot T50n2060 — backup + approval trước khi chạy
- [ ] **Phase 3**: Validate + test TC-001 đến TC-011

---

*Xem: `docs/cbeta-corpus-audit.md` · `docs/cbeta-migration-rollout-plan.md` · `docs/t50n2060-repair-plan.md`*