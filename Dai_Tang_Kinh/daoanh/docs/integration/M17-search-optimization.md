# M17 · T?i uu tra c?u cho C? ch?a nh?n

## Spec · P1

# M17 T?i uu hóa tìm ki?m

K? thu?t t?i uu tr?nh t?m ki?m: fuzzy, ranking, caching, k?t qu? nhanh.

## M?c đ?ch
T?ng t?c d?. & đ? ch?nh tra c?u: fuzzy matching, prioritize k?t qu?, caching th?ng minh.

## UI/UX
- **Trang Caching:** /daoanh/search/caching — truy v?n cache, hit ratio, Purge, hit/miss/th?ng
- **Trang Ranking:** /daoanh/search/ranking — test query, boost factors, relevance score + l?y do, thumbs up/down

## D? li?u
- Cache: LRU d?ng t?i 1000 entry (Zero-RAM)
- Fuzzy: Levenshtein c?p 3 (t?n Hán/Vi?t), d?ng index (Zero-RAM)
- Ranking: relevance + freshness + authority + user feedback
- Query log: top 10.000 query/ngày, rotate weekly

## Acceptance criteria
- [ ] Fuzzy g?n cung 90% query l?i sai đánh máy
- [ ] Cache hit 70% tr?n truy v?n l?p
- [ ] Top-3 ch?c 80% tro?n (golden 30)
- [ ] API d?i 200ms cached
- [ ] Feedback đ?i ranking 24h n?i

## File li?n quan
- docs/integration/M17-search-optimization.md
- tasks/T260-m17-search-optimization.md

## Hi?n trạng code (kh?i s?? 2026-10-07)
- admin/search_all.html c?ng d?n /daoanh/api/admin/search_all?q= | trung t?m M17
- FTS5 places_search_fts* + lexicon_fts 166.278 row | fuzzy/đ? ch?nh x?c
- monk_name_index.normalized, entity, lexicon.key_norm + index | fuzzy đa bảng
- normalize_text() @ app.py:102 | nh?t quy?n kh?p
- lexicon word-idx _LEX_WORD_IDX | m?u LRU search_opt.py
