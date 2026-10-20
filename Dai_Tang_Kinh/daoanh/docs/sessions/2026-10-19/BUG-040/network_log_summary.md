# BUG-040 — Network log summary (browser-verify 2026-10-19)

Nguồn: `mcp__Claude_Browser__read_network_requests` trong phiên browser-verify T417.

## Route 1: /daoanh/places?mode=lineage&focus=A007928&lm=tree

Tất cả request đều `200 OK`, không có 4xx/5xx:

- `GET /daoanh/places?mode=lineage&focus=A007928&lm=tree` → 200
- `GET /daoanh/styles/daoanh-design.css` → 200
- `GET /daoanh/admin/places-generation-v2.js` → 200
- `GET /daoanh/api/admin/ttl_v2/generation/calculate/A007928` → 200
- `GET /daoanh/api/monk/A007928/graph` → 200
- `GET /daoanh/api/places/search?q=&cate=&limit=800&offset=0` → 200
- `GET /daoanh/api/places/search?q=&limit=200` → 200
- `GET /daoanh/api/monk/A007928/lineage-tree?up=2&down=2&include_single=1` → 200 (trả 0 cạnh → nhánh no-edge trong `loadLineageTree`)
- `GET /daoanh/api/persons/A007928` → 200
- `GET /daoanh/api/monk/A007928/cbeta-mentions` → 200
- `GET /daoanh/api/evidence/A007928` → 200
- `GET /daoanh/api/monk/A007928/ancestor-spine?max_hops=80` → 200
- `GET /daoanh/api/monk/A007928/ancestor-path?root=A001719` → 200 (nguồn dữ liệu cho quicklist — `_fetchAndRenderQuicklist`)
- `GET /daoanh/api/person/A007928/translate` → 200
- `GET /daoanh/api/person/A007928/dila_full` → 200
- `GET /daoanh/api/person/A007928/dila_translate` → 200
- `GET /daoanh/api/person/A007928/dila-axis` → 200

## Route 2: /daoanh/places?mode=lineage&focus=A001719&lm=tree (regression case, có cạnh)

Tất cả request đều `200 OK`, không có 4xx/5xx — bao gồm `lineage-tree` (có cạnh, 47 đệ tử trực tiếp),
`ancestor-path?root=A001719`, và 2 request `ttl/anchor-by-dila` (batch ID lookup cho cây mở rộng).

## Kết luận

Không phát hiện lỗi mạng (4xx/5xx) trong toàn bộ phiên test (cả node không cạnh A007928 lẫn
node có cạnh A001719, cả lúc gõ ký tự tìm kiếm). Quicklist phụ thuộc vào
`/daoanh/api/monk/<id>/ancestor-path?root=A001719`, fetch độc lập với việc `lineage-tree` có cạnh hay không.
