---
id: T227
title: Xuất hồ sơ TTL v2 trực tiếp từ DB DILA và bản Việt dịch
module: TTL Thiền Sư VN
priority: high
status: done
depends_on: [T226]
created: 2026-10-04
updated: 2026-10-04
done_when: API và form nạp hồ sơ DB theo ID, tải TTL v2 và xuất lô đọc DB từng hồ sơ; bảo toàn nguồn, không tự duyệt mapping/quan hệ/số đời; kiểm thử và triển khai origin8080 đạt.
---

# T227 — DB là nguồn xuất TTL v2

Admin yêu cầu dùng XML DILA và TTL đã import vào DB để xuất lại profile v2, không nhập lại thủ công. Đã kiểm hai tầng trước cấp T227: dup:ids PASS, rg prose/docs/tasktodo và filename chưa thấy T227; tạo file exclusive để chặn race.

## Kế hoạch trước build

1. Kiểm kê DB people/people_json, VN authority/relations/events/places/works, lineage assertions và metadata nguồn; đối chiếu số1045 với active/quarantine và số hồ sơ DB.
2. Adapter đọc DB theo exact ID; DILA normalized fields/raw record riêng, Việt dịch/TTL riêng. Snapshot giữ đủ các trường DB; không suy dữ liệu bị mất trong import. URI ổn định theo ID, không gộp theo tên.
3. Nạp source states/review thật khi có bằng chứng; computed generations giữ tham chiếu, không dùng làm số đời verified; self edges/mapping ambiguity đi vào báo cáo.
4. API from_db/export, form nạp hồ sơ hệ thống và tải TTL; giữ importer/form v2 cũ cho biên tập.
5. CLI xuất lô readonly DB, iterator/transaction snapshot, manifest/hash; output thư mục mới, không ghi đè TTL active/DB, lỗi được báo theo hồ sơ.
6. Test các DB fields/nguồn/hướng quan hệ/duplicate/self/no auto generation, API/UI, pipeline; cập nhật tasktodo/Dashboard/session/Handoff/memory; reload main có guard và xác minh8080.

Không reimport TTL bằng ETL cũ hoặc tự tính đời. Nếu DB không giữ raw XML/TTL đầy đủ, báo rõ giới hạn và giữ snapshot dữ liệu thực có; quyết định backfill additive phải có backup/manifest trước áp.

## Kết quả đã kiểm

- Source archive DB:49.361 XML và1.045 TTL,SQLite backup +manifest;0 thay đổi bảng people/VN/lineage/generation từ importer.
- Xuất lô snapshotDB:1.037 TTL v2 +8 chứng cứ nguyên văn;template sai cú pháp được báo needs_review.21 mapping DILA exact/verified ghép được;không gộp theo tên.
- Kiểm1037/1037 RDF/profile/hash và8/8 source hashes,0 accepted claims/typed self/duplicate keys,ZIP CRC sạch,DB quick_check ok/WAL.
- UnitT22718/18,hồi quyT22626/26,UI8080 13/13,0 page errors,pipeline exit0/runtime2/2. Mapping PlaceVN click chưa kiểm.
- Main5000 PID6032 nạp xong;gateway8080/auth5001 giữ. Guard hai lần chặn app.py đổi từ phiên khác;helper bootstrap chính bản mới ngay trước reload.
- [Report](../docs/reports/T227-db-ttl-export-20261004/README.md),[Handoff](../docs/Handoff-2026-10-04-T227-db-ttl-export.md). Không commit/stage WIP dùng chung.

## Còn ngoài phạm vi

Không sửa bốn source TTL có self_teacher,không tăng đời,không cấp mapping còn thiếu/không verified,không xuất hết49.361 DILA. Nối các trường chưa semantic hóa vẫn qua snapshot; cần adapter và chứng cứ riêng cho công bố học thuật.

## QA giao diện cuối

Ảnh QA phát hiện .btn display:inline-flex ghi đè hidden của nút ZIP. Đã thêm rule theo ID để chỉ hiện khi jobdone, thêm kiểm UI trước/sau (job stub không tạo jobproduction). Pipeline-delivery exit0/runtime2/2; UI8080 13/13 PASS. Governance fixture AUDITING/LEGACY trên DB copy18/18 PASS, không sửa production policy. Main được phục hồi PID6032 sau khi mất listener.
