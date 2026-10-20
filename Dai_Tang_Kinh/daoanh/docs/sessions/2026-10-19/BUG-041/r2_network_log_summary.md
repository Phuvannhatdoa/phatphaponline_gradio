# BUG-041 vòng 2 — Network log summary (2026-10-19)

## Case (a): focus=A007928 → search "Thiên Nhiên" → click A009460
- GET /daoanh/api/admin/search_all?q=Thi%C3%AAn+Nhi%C3%AAn → 200 OK
- GET /daoanh/api/monk/A009460/lineage-tree?up=2&down=2&include_single=1 → 200 OK
- Kết quả: cây hiện trên canvas (không còn kẹt ở trạng thái "Chưa tìm thấy quan hệ truyền thừa Marcus").

## Case (b): focus=A009460 (có cây) → search "Thiên Nhiên" → click A007928 (không cạnh)
- GET /daoanh/api/monk/A007928/lineage-tree?up=2&down=2&include_single=1 → 200 OK
- Kết quả: #lineage-empty hiện đúng, #lineage-canvas ẩn, không còn sót cây cũ của A009460.

## Case (c) regression: focus=A001719 → search "Huệ" → click "Huệ Năng"
- GET /daoanh/api/admin/search_all?q=Hu%E1%BB%87 → 200 OK
- GET /daoanh/api/monk/A001719/lineage-tree?up=2&down=2&include_single=1 → 200 OK (x2, abort+retry do click)
- Kết quả: cây vẫn hiện đúng như trước, không regression.

Không có request nào trả 4xx/5xx trong cả 3 case.
