# -*- coding: utf-8 -*-
"""
Sinh backlog task T283–T318 từ phân tích docs/integration (2026-10-10).
Mỗi task nhỏ, đánh số tuần tự để giao agent làm lần lượt.
Chỉ tạo file mới trong tasks/, không ghi đè file đã có.

Chạy (ở thư mục daoanh/): python -X utf8 scripts/t278_make_backlog_tasks.py  (đánh số bắt đầu từ T283)
"""
from pathlib import Path

TASKS = Path(__file__).resolve().parent.parent / 'tasks'

# (id, slug, title, module, priority, status, depends, goal, now, steps, verify, nothave)
T = [
('T283','m0-xoa-key-khoi-tai-lieu','M0 — Xóa chuỗi key Gemini khỏi docs/ và scripts/','Nền dev & an toàn','p0','pending','[]',
 'Không còn chuỗi giống key trong docs/ và scripts/.',
 '18 file docs/scripts còn chuỗi kiểu AIza…. app.py đã đọc key từ môi trường (0 chuỗi cứng).',
 '1) Liệt kê 18 file (chỉ đường dẫn, số dòng, không in giá trị). 2) Sao lưu từng file vào docs/sessions/2026-10-10/. 3) Thay bằng tham chiếu biến môi trường hoặc ghi chú. 4) Kiểm lại.',
 'grep -rl "AIza[0-9A-Za-z_-]\\{20,\\}" docs scripts → 0 file.',
 'Không xoay key (việc của Admin). Không in key ra log.'),
('T284','m0-agents-md-trong-claude-md','M0 — Thêm @AGENTS.md vào CLAUDE.md','Nền dev & an toàn','p0','pending','[T283]',
 'CLAUDE.md dưới 200 dòng, nhập AGENTS.md, giữ mọi quy tắc cũ.',
 'CLAUDE.md 98 dòng, không có @AGENTS.md.',
 '1) Sao lưu CLAUDE.md. 2) Thêm dòng @AGENTS.md ở đầu. 3) Đối chiếu từng quy tắc cũ còn đủ (ZQ source_id=5, backup, quyền, VPS).',
 'wc -l CLAUDE.md < 200; grep "@AGENTS.md" CLAUDE.md có kết quả.',
 'Không xóa quy tắc cũ.'),
('T285','m0-hook-chan-git-ghi','M0 — Hook PreToolUse chặn lệnh git ghi','Nền dev & an toàn','p0','pending','[T284]',
 'Lệnh git ghi (add/commit/reset/push --force) bị chặn bằng hook, có thông báo lý do.',
 '.claude/settings.json chỉ có permissions.deny; không có hooks.',
 '1) Viết script Python chạy được trên Windows (không giả định bash). 2) Đăng ký PreToolUse trong settings.json. 3) Thử: git add . bị chặn; git status chạy được.',
 'Thử trong phiên mới: git add bị chặn với thông báo; git status không bị chặn.',
 'Không bật lại thư mục .git. Không commit/push.'),
('T286','m0-rules-skills-agents-thieu','M0 — Rà và tạo nháp .claude/rules, skills/onboard-source, agents/source-reviewer','Nền dev & an toàn','p2','blocked','[T285]',
 'Có rule theo paths cho adapters/** và gate/**, skill onboard-source, subagent source-reviewer chỉ đọc.',
 'daoanh/.claude/ chỉ có launch.json và settings.json. Agents/skills nằm ở ../.claude/ (cần kiểm).',
 '1) Admin xác nhận nơi đặt. 2) Tạo nháp. 3) Thử subagent chỉ đọc.',
 'Subagent chạy được, không có quyền ghi.',
 'Không tự kích hoạt skill onboard-source.'),
('T287','m1-noi-gate-etl-con-lai','M1 — Nối LicenseGate vào 2 script ghi entity_claims còn lại','Data Governance / License Gate','p0','pending','[T231]',
 'Mọi script ghi entity_claims gọi LicenseGate trước khi ghi.',
 'scripts/etl_t109_provenance.py và scripts/wire_evidence_into_entity_claims.py chưa có gate (kiểm bằng grep, có thể bỏ sót).',
 '1) Xác định script nào thật sự INSERT entity_claims. 2) Theo mẫu scripts/etl_entity_claims.py (dòng 26–29). 3) Nhánh từ chối ghi en_audit_log.',
 'py_compile từng file; thử nguồn BLOCKED bị từ chối với dòng audit.',
 'Không đổi schema. Không chạy ETL thật.'),
('T288','m1-kiem-acceptance-cong','M1 — Kiểm acceptance cổng: BLOCKED bị từ chối, LEGACY không đổi','Data Governance / License Gate','p0','pending','[T287]',
 'Chứng minh cổng hoạt động: nguồn BLOCKED bị chặn, 5 nguồn LEGACY giữ nguyên số claims.',
 'Đếm claims theo source_id hiện có (DILA 293.177, ZQLOCAL 118.295, MARCUS 22.332, CBETA 13.933, Wikidata 148).',
 '1) Đếm trước. 2) Chạy dry-run các ETL đã nối. 3) Đếm sau, so sánh.',
 'Số claims trước = sau; có dòng audit cho nguồn bị chặn.',
 'Không nạp nguồn mới.'),
('T289','m1-trang-sources-kiem-trinh-duyet','M1 — Kiểm trang admin/sources.html trên trình duyệt','Data Governance / License Gate','p1','pending','[T288]',
 'Trang sources.html hiển thị 4 chỉ số, bảng lọc được, panel chi tiết, đổi trạng thái có audit.',
 'admin/sources.html có sẵn (31 chữ "source"); chưa kiểm đủ tiêu chí M1.',
 '1) Mở trang qua gateway 8080. 2) Kiểm từng tiêu chí M1. 3) Chụp màn hình điện thoại và máy tính.',
 'Chụp màn hình; đếm 25 nguồn đúng trạng thái.',
 'Không đổi trạng thái nguồn thật nếu không có Admin.'),
('T290','m5-credits-tu-data-sources','M5 — Sinh credits.html từ data_sources','Attribution','p1','pending','[T283]',
 'credits.html liệt kê mọi nguồn ACTIVE/REFERENCE đúng giấy phép từ DB.',
 'credits.html ở gốc daoanh/ đã có, chưa đối chiếu đủ nguồn.',
 '1) So danh sách trang với data_sources. 2) Sinh nội dung từ DB (không gõ tay). 3) Kiểm.',
 'Số nguồn trên trang = số dòng SQL.',
 'Không đổi giấy phép trong DB.'),
('T291','m5-chan-trang-ghi-nguon','M5 — Dòng ghi nguồn trên trang dữ liệu ngoài','Attribution','p1','pending','[T290]',
 'Trang có dữ liệu DILA, GeoNames, WHG có dòng ghi nguồn có link.',
 'Chưa kiểm vị trí hiển thị.',
 '1) Liệt kê trang hiển thị dữ liệu ngoài. 2) Thêm dòng ghi nguồn (chỉ thêm).',
 'Trình duyệt: dòng ghi nguồn hiện trên các trang đã liệt kê.',
 'Không đổi logic hiển thị.'),
('T292','m5-kiem-che-do-thuong-mai-cbeta','M5 — Script kiểm chế độ thương mại (không lộ văn bản CBETA)','Attribution','p1','blocked','[T291]',
 'Có script báo nếu HTML trả về ở chế độ thương mại chứa đoạn CBETA.',
 'Chưa có cờ chế độ thương mại. Điều khoản CBETA mâu thuẫn, chờ văn bản xác nhận.',
 '1) Admin quyết định cờ và điều khoản áp dụng. 2) Viết script quét HTML.',
 'Script trả 0 đoạn CBETA ở chế độ thương mại.',
 'Không đưa ra tư vấn pháp lý.'),
('T293','m3-quyet-dinh-schema-geo','M3 — Admin quyết định schema geo_cross_ref','Địa lý / GIS','p1','blocked','[]',
 'Có quyết định bằng văn bản: thêm những cột nào, có tạo bảng geo_review_queue không.',
 'geo_cross_ref 190 dòng, có confidence, chưa có cột độ chính xác riêng.',
 '1) Admin trả lời. 2) Ghi vào tài liệu quyết định.',
 'Có tệp quyết định.',
 'Không đổi DB trong task này.'),
('T294','m3-them-cot-do-chinh-xac','M3 — Thêm cột độ chính xác và audit (theo T293)','Địa lý / GIS','p1','blocked','[T293]',
 'Các cột mới có trong geo_cross_ref, dữ liệu cũ không đổi.',
 'Chưa có cột.',
 '1) Backup DB (SQLite backup API). 2) ALTER thêm cột (idempotent). 3) Kiểm số dòng.',
 'Số dòng trước = sau; PRAGMA quick_check = ok.',
 'Không xóa cột cũ.'),
('T295','m3-geo-review-queue','M3 — Trang geo_review.html và API hàng đợi duyệt','Địa lý / GIS','p1','blocked','[T294]',
 'Duyệt từng cặp ứng viên: Chấp nhận/Từ chối/Để sau, có audit.',
 'admin/geo_review.html chưa có.',
 '1) Theo mẫu admin/sources.html. 2) API GET/POST. 3) Thử 10 cặp mẫu.',
 'Mỗi thao tác có đúng 1 dòng audit.',
 'Không tự chấp nhận liên kết.'),
('T296','m3-danh-dau-33-bgis','M3 — Gắn admin_centroid cho 33 liên kết BGIS (T31)','Địa lý / GIS','p2','blocked','[T294]',
 '33 liên kết BGIS có cờ admin_centroid, không đổi tọa độ.',
 '33 khớp BGIS từ T31.',
 '1) Chọn 33 dòng theo bgis_id. 2) Đặt cờ.',
 'Đếm 33 dòng có cờ.',
 'Không nâng tâm huyện thành điểm.'),
('T297','m3-hieu-chinh-nguong-ghep','M3 — Hiệu chỉnh ngưỡng ghép trên ≥200 cặp gán nhãn tay','Địa lý / GIS','p2','blocked','[T295]',
 'Ngưỡng 2/10/25 km và điểm 0,5+0,3+0,2 được kiểm trên mẫu thật.',
 'Ngưỡng hiện là giả định. Cần Admin gán nhãn ≥200 cặp.',
 '1) Admin gán nhãn. 2) Chạy khớp thử. 3) Ghi báo cáo độ chính xác và độ phủ.',
 'Báo cáo có độ chính xác và độ phủ.',
 'Không tự động liên kết trên 25 km.'),
('T298','m2-quyet-dinh-relation-claims','M2 — Admin quyết định relation_claims và giấy phép biographies','Authority / Lineage','p1','blocked','[]',
 'Có quyết định: tạo bảng relation_claims (tên, cột) hay dùng chỗ có sẵn; DILA xác nhận biographies.',
 'Bảng relation_claims chưa có. Giấy phép biographies chưa xác nhận.',
 '1) Admin quyết định. 2) Ghi vào tài liệu. 3) Admin liên hệ DILA.',
 'Có tệp quyết định.',
 'Không nạp biographies khi chưa xác nhận.'),
('T299','m2-script-diff-authority','M2 — Script diff authority DILA (chỉ đọc, xuất TSV)','Authority / Lineage','p1','blocked','[T298]',
 'Script báo Thêm/Sửa/Xóa so với phiên bản trước, không ghi DB.',
 'Chưa có. Nguồn: DILA Authority-Databases (CC BY-SA 3.0).',
 '1) Lưu hash commit nguồn. 2) So sánh với bản trước. 3) Xuất docs/evidence/…T299_authority_diff.tsv.',
 'Chạy 2 lần: báo cáo giống nhau; số dòng entity_claims không đổi.',
 'Không áp dụng diff.'),
('T300','m2-trang-authority-sync-chi-doc','M2 — Trang admin/authority_sync.html (chỉ đọc diff)','Authority / Lineage','p2','blocked','[T299]',
 'Trang hiển thị diff theo nhóm, không có nút áp dụng.',
 'Trang chưa có.',
 '1) Đọc TSV của T299. 2) Hiển thị 20 dòng mẫu mỗi nhóm.',
 'Trình duyệt hiển thị đúng số dòng báo cáo.',
 'Không có nút ghi.'),
('T301','m2-kiem-wikidata-chi-id','M2 — Kiểm 148 claims Wikidata chỉ là EXTERNAL_ID','Authority / Lineage','p2','pending','[]',
 'Xác nhận 148 claims Wikidata chỉ là mã liên kết (P1187, P1188, P2477), không có tên.',
 'REALITY_CHECK ghi 148 claims Wikidata.',
 '1) Truy vấn entity_claims source_id=6. 2) Phân loại theo thuộc tính.',
 'Bảng đếm theo thuộc tính.',
 'Không đổi dữ liệu.'),
('T302','m4-quyet-dinh-buddhanexus-mitra','M4 — Admin quyết định BuddhaNexus hay MITRA; ghi DECISIONS.md','Đối chiếu kinh điển','p2','blocked','[]',
 'Có quyết định bằng văn bản trước khi viết code.',
 'Hai lựa chọn có rủi ro giấy phép (DharmaNexus cấm dùng API cho ứng dụng bên thứ ba; MITRA mâu thuẫn BY-SA/BY).',
 '1) Admin quyết định. 2) Tạo docs/integration/DECISIONS.md (chỉ tạo mới).',
 'Có file DECISIONS.md.',
 'Không viết code gọi API.'),
('T303','m4-tab-doi-chieu-chi-doc','M4 — Tab Đối chiếu đọc từ bảng có sẵn (chỉ đọc)','Đối chiếu kinh điển','p2','blocked','[T302]',
 'Tab hiển thị song song từ sat_crossref (2.913), toh_cbeta_crossref (10), kanripo_catalog (101), có nhãn mức Link/Metadata.',
 'Các bảng đã có dữ liệu; chưa có tab.',
 '1) API đọc bảng. 2) Tab trong trang đọc kinh. 3) Trạng thái rỗng nói rõ.',
 'Chụp màn hình có ít nhất 1 dòng song song đúng.',
 'Không hiển thị văn bản nguồn có giấy phép hạn chế.'),
('T304','m4-cache-va-nhan-du-lieu-cu','M4 — Cache 24 giờ và nhãn dữ liệu cũ','Đối chiếu kinh điển','p3','blocked','[T303]',
 'Khi nguồn ngoài không trả lời, vẫn hiện dữ liệu đã lưu và nhãn cũ.',
 'Chưa có.',
 '1) Cache theo nguồn. 2) Nhãn cũ.',
 'Tắt mạng thử: tab vẫn hiện dữ liệu cũ.',
 'Không gọi nguồn ngoài khi cache còn hạn.'),
('T305','t170-viet-test','T170 — Viết tests/ cho pipeline (SPEC §6, R1–R8)','Editorial / LLM Translation','p1','blocked','[T306]',
 'Ba file test T170 PASS 100%.',
 'tests/ chưa có file test T170. Script T170 đã có.',
 '1) Viết test theo SPEC. 2) Dùng DB tạm (T170_DB). 3) Test R3: 惠明 ≠ 慧明.',
 'pytest tests/test_dila_verifier_v3.py tests/test_dila_person_verifier.py tests/test_t170_redteam.py → 100% PASS.',
 'Không gọi API Groq trong test.'),
('T306','t170-bo-vang','T170 — Admin lập bộ vàng (25 place + 25 person)','Editorial / LLM Translation','p1','blocked','[]',
 'Có docs/evidence/T170_gold_set.tsv ≥50 dòng với đáp án Admin xác nhận.',
 'Chưa có bộ vàng.',
 '1) Admin lập. 2) Kiểm trùng ID.',
 'Đếm dòng ≥50, không trùng.',
 'Không tự tạo đáp án.'),
('T307','t170-pilot-place','T170 — Pilot 25 place (sau T287, T305, T306, có phê chuẩn Admin)','Editorial / LLM Translation','p1','blocked','[T287,T305,T306]',
 'Chạy --pilot 25 cho place; kết quả vào place_groq_audit; Admin duyệt.',
 'Bảng place_groq_audit có sẵn, 0 dòng. Lần chạy thật cần phê chuẩn.',
 '1) Sao lưu. 2) --validate-only. 3) --pilot 25. 4) Admin duyệt mẫu.',
 'Đối soát SQL theo SPEC §8.',
 'Không chạy production.'),
('T308','t170-pilot-person','T170 — Pilot 25 person (sau T307)','Editorial / LLM Translation','p1','blocked','[T307]',
 'Chạy --pilot 25 cho person; kết quả vào person_groq_audit; Admin duyệt.',
 'person_groq_audit có sẵn, 0 dòng.',
 'Như T307 cho person.',
 'Đối soát SQL theo SPEC §8.',
 'Không chạy production.'),
('T309','t275-kiem-cay-lam-te-tren-trinh-duyet','T275 — Kiểm cây Lâm Tế hiển thị nhãn TTL trên trình duyệt','Lineage / Generation','p1','pending','[]',
 'Mở cây Lâm Tế, thấy nhãn TTL <đời> hoặc TTL ? đúng.',
 'Hàm _t275ApplyTtl đã kiểm trên trang thật (DataSet mẫu). Canvas cây chưa chụp được.',
 '1) Mở tab cây Lâm Tế. 2) Chụp màn hình trước/sau. 3) Kiểm 5 nút.',
 'Ảnh chụp kèm bảng kết quả.',
 'Không đổi engine.'),
('T310','ttl-dila-lap-bang-quyet-dinh','Ánh xạ TTL↔DILA — Admin lập bảng quyết định','Lineage / Data Curation','p1','blocked','[]',
 'Mỗi dòng xung đột/rỗng có quyết định: A020018, A010511, A025951, A004146, 58 dòng ttl_filename rỗng.',
 'API anchor-by-dila báo conflict/unmapped đúng. Gỡ A025951 khỏi Kinh Triệu chưa làm (bị chặn quyền ghi).',
 '1) Admin điền bảng. 2) Lưu tệp quyết định.',
 'Tệp có đủ dòng.',
 'Không tự quyết định ID.'),
('T311','ttl-dila-ap-dung-quyet-dinh','Ánh xạ TTL↔DILA — Áp dụng quyết định (backup + transaction)','Lineage / Data Curation','p1','blocked','[T310]',
 'DB cập nhật đúng theo bảng quyết định; API không còn xung đột ngoài danh sách chấp nhận.',
 'Cần quyền ghi DB (trước đó bị chặn).',
 '1) Backup. 2) quick_check. 3) UPDATE trong transaction, kiểm số dòng. 4) COMMIT hoặc ROLLBACK.',
 'Gọi lại anchor-by-dila; số dòng vn_person_authority không đổi.',
 'Không xóa dòng.'),
('T312','t275-engine-doc-neo-ttl','T275 — Engine đọc neo TTL trước (bước 6)','Lineage / Generation','p1','blocked','[T309]',
 'generation_engine_v2 ưu tiên neo TTL; BFS DILA chỉ khi không có neo.',
 'Engine chưa đổi. Lâm Tế đời 30 vẫn unreachable/incomplete.',
 '1) Admin duyệt thay đổi engine. 2) Backup. 3) Sửa parents(). 4) Chạy test số đời.',
 'Lâm Tế: Nghĩa Huyền 38, Phương Hội 45 khớp TTL.',
 'Không đổi số của tông khác mà không kiểm.'),
('T313','arch-viet-lai-m98','Archive — Viết lại M98 (lưu dòng truyền, bỏ blockchain)','Lineage / Generation','p2','pending','[]',
 'Spec M98 mới chỉ gồm đối soát dòng truyền với T275, không có blockchain hay số liệu không nguồn.',
 'Bản gốc trong _archive/M-series/M98-automated-lineage-preservation.md có số liệu không nguồn và blockchain.',
 '1) Đọc bản gốc. 2) Viết spec mới ở docs/integration/. 3) Admin duyệt.',
 'Spec không có số liệu không nguồn.',
 'Không đưa blockchain vào.'),
('T314','arch-viet-lai-m27','Archive — Viết lại M27 (kết nối thầy–đệ, không số liệu)','Lineage / Generation','p3','pending','[]',
 'Spec mới bỏ "10.000+ practitioners", sửa lỗi mã hóa, nêu rõ quyết định về dữ liệu người dùng.',
 'Bản gốc có lỗi mã hóa và số liệu không nguồn.',
 '1) Viết lại. 2) Đánh dấu cần Admin quyết định về dữ liệu người dùng.',
 'Không còn ký tự lỗi; không số liệu không nguồn.',
 'Không xây tính năng.'),
('T315','arch-gop-kg-m12-m51-m97','Archive — Gộp M12, M51, M97 thành một spec knowledge graph','Lineage / Generation','p3','pending','[]',
 'Một spec KG, bỏ trùng ý.',
 'Ba file cùng chủ đề, có nội dung trùng.',
 '1) Đọc ba file. 2) Gộp. 3) Ghi nguồn gốc.',
 'Một file spec mới.',
 'Không tạo đồ thị mới.'),
('T316','arch-gop-dashboard-m70-m99','Archive — Gộp M70, M99 thành spec dashboard','Dashboard','p3','pending','[]',
 'Một spec dashboard chỉ đọc số liệu thật.',
 'Hai file trùng ý tưởng.',
 '1) Đọc hai file. 2) Gộp, bỏ phần không có nguồn.',
 'Một file spec mới.',
 'Không thêm chỉ số không đo được.'),
('T317','arch-m7-gis-noi-m3','Archive — M7 GIS, nối vào M3 (sau T295)','Địa lý / GIS','p3','blocked','[T295]',
 'Phần GIS của M7 được gộp vào M3 đã có hàng đợi duyệt.',
 'M7 nằm trong _archive/M-series.',
 '1) Đọc M7. 2) Gộp phần còn giá trị vào M3.',
 'Không trùng với T295.',
 'Không thêm nguồn ngoài chưa có giấy phép.'),
('T318','arch-dich-xac-minh-m44-m85-m94','Archive — Dịch và xác minh (M44, M85, M94) sau T308','Editorial / LLM Translation','p3','blocked','[T308]',
 'Spec ghi rõ quan hệ với T170 (xác minh tên) và T269 (quy tắc dịch).',
 'Ba file trong _archive/M-series.',
 '1) Đọc ba file. 2) Viết spec gộp, nối T170/T269.',
 'Không trùng quy tắc T269.',
 'Không gọi LLM mới.'),
('T319','arch-m16-route-api-that','Archive — M16: liệt kê route API thật, viết lại spec','API','p3','pending','[]',
 'Danh sách route thật (khoảng 313) và spec mới chỉ gồm route cần thiết.',
 'M16 trong _archive/M-series.',
 '1) Liệt kê @app.route. 2) Viết spec.',
 'Số route khớp lệnh đếm.',
 'Không mở API công khai khi chưa có license.'),
('T320','arch-xoa-m53-test','Archive — Admin xác nhận xóa M53-test.md (rỗng)','Docs','p3','blocked','[]',
 'File rỗng bị xóa khi Admin đồng ý.',
 'M53-test.md 4 byte, trong _archive/M-series.',
 '1) Admin xác nhận. 2) Xóa và ghi ROLLBACK.',
 'Không còn file.',
 'Không xóa nếu chưa xác nhận.'),
('T321','arch-admin-quyet-200-file','Archive — Admin quyết định giữ/xóa ~200 file không mục tiêu','Docs','p3','blocked','[]',
 'Có danh sách giữ/xóa do Admin ký.',
 '~200 file tính năng và bản Uu-Tien không có kế hoạch tích hợp.',
 '1) Admin đánh dấu từng nhóm. 2) Không xóa nếu chưa duyệt.',
 'Có tệp quyết định.',
 'Không xóa file trong _archive khi chưa duyệt.'),
('T322','docs-cap-nhat-reality-check-plan','Docs — Cập nhật REALITY_CHECK và 00_PLAN theo trạng thái thật','Docs','p2','pending','[T231]',
 'REALITY_CHECK và 00_PLAN ghi đúng: M1 đã có T231; số liệu DB/route mới.',
 'REALITY_CHECK ghi số cũ (DB 1,4 GB, 156 bảng, 313 route).',
 '1) Đo lại số liệu (chỉ đọc). 2) Sửa hai file (có sao lưu).',
 'Số trong tài liệu khớp lệnh đo.',
 'Không đổi số liệu bằng tay.'),
]


def body(t):
    (tid, slug, title, module, prio, status, deps, goal, now, steps, verify, nothave) = t
    deps_list = deps
    return f"""---
id: {tid}
title: "{title}"
module: {module}
priority: {prio}
status: {status}
created: 2026-10-10
updated: 2026-10-10
owner: claude-code
parent: docs/integration (phân tích 2026-10-10)
depends_on: {deps_list}
done_when: |
  {goal}
  Admin xác nhận DONE. Không tự đánh DONE.
revert: |
  Chỉ thay đổi trong task này; hoàn tác bằng sao lưu trong docs/sessions/2026-10-10/ hoặc ROLLBACK.md.
outcome: >
  2026-10-10: tạo task backlog để agent code tuần tự. Chưa bắt đầu.
---

# {tid} — {title}

## 1. Mục tiêu

{goal}

## 2. Hiện trạng (đã kiểm 2026-10-10)

{now}

## 3. Các bước (agent làm lần lượt)

{steps}

## 4. Kiểm chứng

{verify}

## 5. Không làm trong task này

{nothave}

## 6. Các bước

- [ ] **Bước 1 —** xác minh hiện trạng và ghi log
- [ ] **Bước 2 —** chuẩn bị (sao lưu hoặc quyết định Admin)
- [ ] **Bước 3 —** làm việc chính theo mục 3
- [ ] **Bước 4 —** kiểm chứng theo mục 4
- [ ] **Bước 5 —** Admin xác nhận DONE
"""


def main():
    made, skipped = [], []
    for t in T:
        tid, slug = t[0], t[1]
        path = TASKS / f'{tid}-{slug}.md'
        if path.exists():
            skipped.append(path.name)
            continue
        path.write_text(body(t), encoding='utf-8')
        made.append(path.name)
    print(f'đã tạo {len(made)} task; bỏ qua {len(skipped)} (đã có)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
