# Handoff — T215 case7 Trí Tài đồng bộ theo DILA2026-09

## 1. Bảng đọc nhanh
Ngày2026-10-02; không commit. Trí Tài A026976 đã xác minh/sync. Sửa TTL thầy2 URI; TTL trò đã đúng nên giữ nguyên. RDF2, DB/API, rollbackPASS. Pipeline đang chạy.

## 2. Đọc trong2 phút
Tên đầy đủ瑞巖智才, thầy石門守進 A013875. Không còn lấy Diệp Huyện làm thầy trực tiếp. ĐờiTríTài44/ThủTấn43 giữ từTTL. Admin xem Dashboardcase7, báo cáo và nguồn XML2026-09 đã lưu.

## 3. Thay đổi và bằng chứng
DILA chính thức tải qua https://authority.dila.edu.tw/downloads/authority_person.2026-09.zip. Trích2 record bằng iterator, gói/hash/records nằm backup. A026976 teacherA013875; A013875 studentA026976, teacherA010933. Dẫn X78n1556p693a5-6 cho MinhChâu ThạchMôn→ThụyNham. TTL thầy subject rỗng vàdeathEventthiếu slug được sửa. DB2 authority metadata từTTL, localteacher relations và2verifiedTTL assertions; assertion58284 cũ rejected, self58285 giữrejected. peoplebirth1556/death693 được xóa vì là sốkinh/trangcitation, XML khôngcó birth/death. NguồnDILA/Marcus assertions giữ nguyênhash.

## 4. Cảnh báo bắt buộc
Không fullimport/đổi đời; không coi thầy43/trò44 là3 chứng cứđộc lập. Không sửa rawXML; chỉ sửa processed datefields rõ lỗi trích dẫn. Gói tải từ nguồn chính thức và hash để truy vết. Không dùng hết corpus RAM. Nhiều phiên làm song song; không stage cả thư mục.

## 5. Revert
Từ daoanh: `python -X utf8 data/backups/T215-tri-tai-sync-20261002/sync_case.py --revert`. Snapshot guarded, thử in-memoryPASS; không mất dữ liệu ngoài phạm vi. Guard dừng nếu TTL/row đã đổi. Cácrollback T215 trước có thể dừng vì hồ sơ đã được sync mới — cần đọc manifest rồi xử lý, khôngforce.

## 6. File tạo/sửa
TTL input/output: data/ttl/TS-Thach-Mon-Thu-Tan.ttl (2 URI). TríTài input data/ttl/TS-Thuy-Nham-Tri-Tai.ttl giữ nguyên. Backupdir:T215-tri-tai-sync-20261002 gồm archive, dila-evidence.json, ttl-plan, snapshotbeforeafter, script, API snapshots/check, pipeline log. Report docs/reports/T215-self-edges/tri-tai-sync-2026-10-02.md; caseJSON/dashboard/mainbanner/task/progress/roadmap/tasktodo/session.

## 7. Sai lầm/bài học
Websearch authority cachedmiss khiến trước đây bỏ qua; XML chính thức đủ xác minh, không đòi webpage phải mở được. urllib tải gói lỗiTLSverifySKI; chuyển requests với TLS mặc định verify=True, tảiPASS, không tắtTLS. Cùng nguồnXML thầy/trò là đối chiếuhai chiều, không phải2 nguồnđộc lập về số đời.

## 8. Chưa xong
T215 toàncorpus in_progress; cácIDđệ tử ngoài9case và IDTạngChủPhổDung vẫn cần xác minh. Case7 đã khép về danh tính/tiểu sử/thầy; không tự thêm đệ tử chưa thấy.

## 9. Kiểm tra nhanh
API /daoanh/api/monk/A026976/lineage-tree?up=1&down=1: nameThụyNhamTríTài, Han瑞巖智才, generation44, teacherA013875, nullbirth/death, bioVi đúngTTL. A013875: ThạchMônThủTấn, 石門守進, đời43, teacherA010933. Dashboard case7 confirmed;2 RDFvalid.

## 10. Agent kế tiếp
Đọc cases.json, tri-tai report vàsync-reportbeforeafter. Kiểm pipeline log cuối; giữ đúng source_version2026-09. Không suyDILA date từ citation. Chỉ đụng file/row xác định, snapshot/guard rollback trước apply.


### Kiểm tra cuối phiên
RDF2/DB/API/rollbackPASS; DBsnapshotafter vẫnkhớp saupipeline. Dashboardcase7liveconfirmed/header9PASS. Cú phápHTML/JS5pagePASS. Pipeline lầnđầu dừng T17867/68 vì readonlySQLite khiimport app; standaloneappimportPASS, chạy lại đúng T178 đạt69/69PASS (test được phiênkhác cập nhật). Không sửa app/test để épPASS. Không tuyên bốfullpipeline exit0 vì đãdừng trướcstage sauT178. Logpipeline.log/import-check.log/t178-retry.log trongbackupdir; PowerShellUTF16LE. Sessionmemory37700khôngkết nối, tasktodo + localHandoffđã lưu.
