# 2026-10-02 — Audit toàn bộ TTL local

## Hoàn thành
- Thêm scripts/audit_ttl_lineage_local.py: đọc từng TTL, DB nguồn read-only, index SQLite riêng.
- Quét 1037 TTL; nhận diện 1036 file, 1238 khai báo cạnh.
- 9 self-edge, 3 multi-node cycle witnesses (tổng12), 30 generation-review.
- 101 định danh khác subject, 89 tên file khác subject, 10 nhóm subject trùng.
- 254 file chưa có DILA; 437 cạnh chưa được DILA local xác nhận (không kết luận sai).
- Preflight cũ: L1=12, L2=15, L7=9; khác số va chạm vì audit mới hỗ trợ cả bkg:Monk và <bkg:Monk>.
- Báo cáo docs/reports/ttl-lineage-audit-2026-10-02/README.md + JSONL + SQLite index.
- Chưa sửa TTL hay lineage.db.

## Đang dở
- Thiếu rdflib: chưa validate Turtle toàn bộ; 1 file chưa nhận diện.
- Pipeline validation đang chạy; kết quả ghi tiếp sau.

## Todo
- Xác minh DILA ID và các subject collision trước khi sửa quan hệ.
- Đối chiếu DILA chính thức / nguồn Việt từng case, kiểm quy ước số đời.
- Change-set có chứng cứ + backup/rollback, đồng bộ scoped TTL và verify API.

## Validation cuối phiên
- Audit chạy exit 0, trạng thái NEEDS_REVIEW (không phải corpus sạch).
- npm run pipeline exit 1: T178 67/68 PASS, import app thiếu flask.
- Memory service localhost37700 không kết nối được; đã lưu session local.
