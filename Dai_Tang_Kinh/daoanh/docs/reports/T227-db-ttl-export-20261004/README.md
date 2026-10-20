# T227 — Xuất TTL v2 từ DB

Task: [T227](../../../tasks/T227-db-ttl-v2-export.md). **DONE trên localhost:8080**, main PID6032; tất cả bằng chứng dưới report này.

## Hệ thống mới

DB là nguồn đọc của exporter. Nạp theo DILA ID, ttl:filename.ttl hoặc slug:ten_slug; giữ hồ sơ nguồn XML DILA, bản Việt dịch, TTL legacy, CBETA mentions, Marcus và các assertion mạng trong những sourceSnapshot riêng. URI theo exact ID/slug; không gộp người theo tên. Dữ liệu chưa xác minh không được nâng thành accepted/fact.

## Dữ liệu được nhập bổ sung

Trước build: people có 48.673 rows; people_full rỗng, không có people_json/person_json; vn_person_authority có 1.507 rows/1.024 filename khác nhau; ttl_master chỉ có 2 rows. Vì vậy import cũ chưa giữ đủ XML và nguyên văn TTL.

Đã tạo SQLite backup nhất quán trước khi thêm hai bảng ttl_v2_source_import_runs và ttl_v2_source_records. Lần nhập T227 giữ 49.361 person XML từ archive DILA 2026-09 và 1.045 TTL: 1.038 active + 7 quarantine. Tổng 50.406 records mới; manifest SHA từng record. XML được serialize từng TEI person, không phải byte-for-byte toàn archive; archive gốc giữ nguyên và có SHA riêng. TTL UTF-8/BOM được giữ nguyên.

Năm bảng nền people/vn_person_authority/vn_person_relations/lineage_edge_assertions/person_gen_computed có số rows trước/sau lần lượt 48.673/1.507/2.088/59.059/19.961, không thay đổi. Importer chỉ ghi hai bảng mới; exporter chỉ đọc DB bằng transaction snapshot. Không chạy ETL cũ hoặc tính lại số đời.

## Dùng trang Admin

1. Mở http://localhost:8080/daoanh/admin/monk_ttl_add.html.
2. Nhập A000885 hoặc ttl:TS-Dien-Phuc-Tue-Thang.ttl, bấm **Nạp hồ sơ từ DB** để xem dữ liệu và nguồn.
3. Bấm **Xuất TTL từ DB** để tải bản đọc mới nhất từ DB, không phải thay đổi chưa lưu trong form. Có thể tải trực tiếp mà không cần nạp lại.
4. **Tải TTL đang biên tập** xuất nội dung form; **Lưu bản nháp v2** chỉ tạo revision staging, không sửa dữ liệu đang chạy.
5. Đăng nhập Admin, bấm **Xuất bộ TTL đã nhập**, chờ thống kê và bấm **Tải ZIP TTL v2**. Giữ job ID để truy xuất sau restart.

Nếu hồ sơ đang có dữ liệu, nạp lại bị chặn để tránh mất phần đang sửa; dùng Hồ sơ mới trước. Chuyển từ nút Tạo TTL ở person.html tự lấy cấu trúc DB rồi giữ riêng toàn bộ snapshot trang, tên Việt/tiểu sử đang biên tập và số đời cũ.

## Quy tắc ngữ nghĩa

- Việt dịch chỉ gắn vào DILA khi đúng một mapping status=verified, tên Hán khớp alias trong chính record XML và không có nhiều main verified cùng ID. Mapping khác giữ ở snapshot hoặc hồ sơ legacy, không tự suy.
- DILA/Marcus/TTL da:isTeacherOf là quan hệ thầy chung, không tự chuyển thành truyền pháp hay thụ giới. raw_relation_type/ref/status/mapping_verified vẫn được giữ.
- Số đời nguồn và số tính sẵn đều giữ làm tham chiếu với hệ đếm riêng; không cộng 37, không dùng thầy+1, không auto accepted. Giá trị không hợp lệ giữ trong snapshot, không giả sửa.
- Self-edge giữ trong originalTurtle/sourceSnapshot và report, không xuất thành assertion quan hệ typed. Hiện phát hiện hasTeacher tự nối ở TS-Dien-Phuc-Tue-Thang, TS-Dinh-Lam-Canh-Phuong, TS-Dong-Son-Trach-Ngon, TS-Vo-Chuan-Su-Pham; đây là trạng thái file ở lần nhập hiện tại, khác claim lịch sử T215. Không sửa nguồn hay DB truyền thừa trong T227.
- Bộ ZIP có TTL v2, manifest, summary và phụ lục nguyên văn .txt + source-evidence-manifest cho file mẫu sai/cách ly. Chứng cứ .txt không phải hồ sơ v2 đã xác minh.
- Gói nội bộ giữ quyền nguồn pending; chức năng chia sẻ công khai vẫn yêu cầu quyền đúng artifact, không tự nâng metadata license registry thành giấy phép đã xác minh.

## API

GET /daoanh/api/admin/ttl_v2/from_db/<identifier>
GET /daoanh/api/admin/ttl_v2/export_db/<identifier>
GET /daoanh/api/admin/ttl_v2/db_stats
POST /daoanh/api/admin/ttl_v2/batch {scope:ttl} (Admin)
GET /daoanh/api/admin/ttl_v2/batch/<job_id> (Admin)
GET /daoanh/api/admin/ttl_v2/batch/<job_id>/download (Admin)

Batch dùng một hồ sơ mỗi vòng, không tải toàn corpus vào RAM; output thư mục mới và lỗi từng file. Main route đọc XML đã cache DB; fallback archive chỉ để tương thích khi chưa backfill. Nếu một nhân vật có hơn 500 records liên quan, báo cần adapter phân trang thay vì cắt mất dữ liệu. Nhân vật DILA không nhất thiết là tu sĩ.

## CLI

Chạy từ daoanh với PYTHONPATH dependency đã có ở T226/T215:

~~~powershell
python -X utf8 scripts/export_ttl_v2_from_db.py --scope ttl --output data/ttl_v2/db_exports/<folder-moi>
python -X utf8 scripts/export_ttl_v2_from_db.py --scope dila --limit 10 --output data/ttl_v2/db_exports/<folder-moi-khac>
~~~

Exit0: mọi hồ sơ trong scope xuất được; exit1: có needs_review nhưng lô hoàn tất; exit2: fatal. DILA toàn bộ được hỗ trợ CLI streaming; chưa chạy hết 49.361 hồ sơ trong phiên này. TTL active/cách ly nguyên bản không bị ghi đè.

## Kiểm chứng và bàn giao

Source import: [summary](../../../data/backups/T227-db-ttl-export-20261004/source-import/summary.json), manifest và lineage-before.db cùng thư mục. Unit T227 18/18 PASS trong pipeline-final.log; hồi quy T226 26/26 PASS. UI preview 11/11 PASS, 0 lỗi JavaScript. Bootstrap main schema/from_db/export/lineages HTTP200. Kết quả full pipeline, gói export cuối và origin8080 sẽ được bổ sung sau kiểm tra.

Rollback: scripts/t227_rollback.py --code (dry-run, --apply để áp); --sources-db riêng xóa đúng run nguồn mới, guard nếu có run khác. Giữ original XML/TTL/ZIP/backup; không restore whole DB làm mất cập nhật session khác. Chi tiết manifest/Handoff được lưu trong report.

## Kết quả lô cuối

Gói data/ttl_v2/db_exports/T227-db-export-v2-20261004/ttl-v2.zip: 1.038 active đã xử lý, 1.037 TTL v2 xuất được, 1 template sai cú pháp needs_review; phụ lục giữ 1 nguồn lỗi +7 nguồn cách ly. Tổng 1.045 nguồn TTL được bảo toàn trong hồ sơ/phụ lục. Có21 hồ sơ ghép DILA theo mapping verified và alias exact; các hồ sơ còn lại giữ định danh legacy, không đoán ID. CLI exit1 là báo needs_review của template, không phải batch crash.

Pipeline cuối exit0, runtime2/2; click Mapping Tên Việt không được kiểm vì button không có trên PlaceVN. ZIP kiểm1037/1037 parse_v2/schema/hash PASS,8/8 chứng cứ hash PASS,0 accepted claims,0 typed self relations,21 merged DILA profiles,0 duplicate profile keys,CRC ZIP không lỗi. DB journal_mode WAL,quick_check=ok; read snapshot không đổi journal_mode. Rollback dry-run guard PASS12file/50406 source records. Main app.py thay đổi do các task khác, guard reload đầu đã chặn trước khi kill; bootstrap lại app hiện tại HTTP200 cả4route.

Main ready lúc2026-10-04T14:04:01+07:00,PID30900/thayPID1076;gateway/auth giữ nguyên. UI chính8080 13/13 PASS,0JSerrors,APIstats/from_db/lineages/login200. Xem [Handoff](../../Handoff-2026-10-04-T227-db-ttl-export.md). Chưa test export lô bằng token Admin thật trên8080: auth/API worker/download được test bằng fixture18unit,auth gate UI thật và CLI lô thật đã kiểm;không tạo token giả hoặc bypass login.

## QA bổ sung trước bàn giao

Ảnh đã phát hiện rule .btn ghi đè hidden của nút ZIP. Đã thêm #download-db-batch[hidden] để ẩn cho đến khi job hoàn tất; UI8080 hiện13/13 PASS, gồm real auth401 và trạng thái jobdone bằng UI stub (không tạo token/jobproduction).

Main5000 đã mất listener sau lầnready30900,không có exception trong log;gateway502/auth200. Helper đã được mở rộng để start khi không có listener,bootstrap và kiểmport/PID trước start;main mới6032ready2026-10-04T14:17:58+07:00. Gateway/auth giữ nguyên.

Pipeline-release phát hiện test governance cũ giả địnhDILA không cóLEGACY,trong khiT231 vừa thaypolicy. Không đổi gate/license.py hayDBproduction: cập nhật tests/test_b25_authority_contract.py dùng SQLitebackup consistent và fixtureAUDITINGkhôngLEGACY (vẫndeny) / LEGACY(vẫnallow nhưngkhôngverifyrights),restorecopy saucase. Governance18/18 PASS. Pipeline-delivery đã exit0/runtime2/2; T227 DONE.

## Kết quả bàn giao cuối

Pipeline-delivery exit0, runtime2/2. T227 unit18/18, T226 regression26/26, governance18/18, UI8080 13/13 với0page errors. Main6032 ready, gateway/auth HTTP200. Nút tải ZIP ẩn đúng trước jobdone. Chứng cứ đầy đủ tại pipeline-delivery.log/.exit, live-ui/ui-result.json, export-verification.json và reload-status.json.
