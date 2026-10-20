# Handoff — T215 sửa lỗi TTL và đồng bộ (2026-10-02)

## 1. Thông tin đọc nhanh
TTL: sửa7file, gồm5case chính và2file hỗ trợ; RDF12/12PASS. DB:6case mới sync, Cảnh Phương hỗ trợ và metadata2thầy khôi phục; Trí Tài chỉ bỏ tự nối. Nguồn DILA/Marcus giữ nguyên bằng hash iterator. Không commit. Pipeline kết quả ghi cuối file.

## 2. Đọc trong 2 phút
9case không còn tự nối trong TTL/local DB. 8case định danh/thầy có chứng cứ (Tuệ Thăng/Phần Dương sync trước). Trí Tài chưa xác minh DILA, chỉ loại cạnh tự nối. Admin xem Dashboard, báo cáo từngcase, giữ các mục chưa xác minh cho lần tiếp theo.

## 3. Thay đổi và bằng chứng
Chi tiết docs/reports/T215-self-edges/fix-sync-2026-10-02.md và cases.json. Trạch Ngôn: bỏ nhãn phụ sai không dùng; IDtròA020683/thầyA020673 theo officialindex206 + trangthầy. Trạch Sùng: đóngquote, A020706 alias薦福擇崇/常菴擇崇, NinhQuốc/NhiêuChâu khớpbio; teacherA014665. Nguyên Liên: A014349 alias廣慧元璉 ngườiTuyềnChâu họTrần khớpbio, teacherA004983. VôChuẩn: URIevents mangsubjectđúng, A004697 teacherA004696, bio rỗng giữ nguyên. HưngHóa/CảnhPhương: tách định danh A014436/A026988, teacher của CảnhPhương sửa đúngNhânNhạc theo DILA hai chiều, tênCảnhPhương theo景芳 vàbio. KếThành: A026926 teacherA014617; khôi phục metadataĐạoBình từTTL riêng; PhổDung gỡ IDA014617 sai, pending chưa gán mới.

## 4. Cảnh báo bắt buộc
Không fullimportTTL. 15assertions TTL mapping sai/self bị rejected, không xóa lịch sử. Cạnh đệ tử chưa xác minh không tự tạo assertion quốc tế. Không tăngđời: TTLgenerationOrder giữ nguyên cả12file. DB46→45 tại slugNhânNhạc và48→47 tại slugĐạoBình là táchmetadata hai người bị chồng, số đời từngngười lấyTTL riêng; không suyra bằngthầy+1. Có phiên khác đang thay task216, không ghi đè. Alias_A004697 là cùngpersonalias giữ nguyên; VPAvo_chuan verified được APIchọn.

## 5. Revert
Từdaoanh: python -X utf8 data/backups/T215-fix-sync-20261002/sync_case.py --revert
Khôi phục7TTL vàrowDB trongsnapshot. Guard dừngnếuTTL/rowđãthay sau sync. Rollback SQLiteinmemory PASS. KhôngundoTuệThăng/PhầnDương phiêntrước. Không mất dữliệu ngoài phạmvi.

## 6. File tạo/sửa
7TTL: TrạchNgôn,TrạchSùng,NguyênLiên,TríTài,VôChuẩn; hỗtrợĐộngSơnPhạmNgôn,ĐịnhLâmCảnhPhương. Backup12file, ttl-change-plan.json, db-rows-before.json, sync-report.json, sync_case.py, API snapshots, api-verification.json, pipeline.log vàpython-deps riêng. Report/dashboard/casesJSON, taskT215/progress/roadmap/tasktodo/session vàHandoff này.

## 7. Sai lầm/bài học
Lầnapply đầu dừngguard vì Python read_text chuẩn hóaCRLF khác rawmanifest; chưa đổiDB/TTL. Đã sửacomparebyte decodeUTF8 vàapplyPASS. Không coi sửa9selfedges là toàncorpus sạch. Không kếtluậnA026976 khôngtồntại khiwebcachemiss. Parser/T178 thiếudependencies đãcài riêngworkspace, khôngđổi hệthống.

## 8. Chưa xong
IDTríTài vàID thaythếTạngChủPhổDung. Đệ tửPhầnDương/TịnhNhân vàmột sốcase khác còn cần khóaID, khôngđoán từtênngắn. Tiểu sửVôChuẩnrỗng chưa bổsung. AudittoàncorpusT215vẫnin_progress.

## 9. Kiểm tra nhanh
API200 tại /daoanh/api/monk/{ID}/lineage-tree?up=1&down=1 choA020683,A020706,A014436,A014349,A026926,A004697,A026988; tên/bio Việt khớpTTL, teacherđúng, thếhệtheoTTL. RDF12/12vàself0trongreport. Dashboard /daoanh/dashboard/t215-self-edges.html có9case kếtquả mới.

## 10. Agent kế tiếp
Đọc report + caseJSON + manifestbeforeafter; chạyrollbackguard trước muốnrestore. Nguồnquốc tếkhôngđổi; đừngđưaassertionrejected trởlại active quafullimport. Cài dependencies chỉ vào backup/python-deps, dùng run-pipeline.cmd đểpipeline cóPYTHONPATH. Xác minhIDPhổDung qua nguồnFaDiễnA000733linkA022046 nhưng directfetch chưađủ; khôngassignchưađọc. Sessionmemory37700 chưasẵn.


### Kiểm tra cuối
- ParserRDF12/12file scope PASS; trongpipeline T203 parsecorpus1037file/0lỗi PASS (khôngchứngnhận họcthuật toàncorpus).
- DB/API/rollback PASS; DB snapshotvẫnkhớpafter saupipeline.
- Cácstage pipeline trướcPlaywright PASS. Lệnhpipelineexit1 vìEPERMunlink filekếtquảcũ test-results/.last-run.json. Chạylạiriêngruntime với outputdir mới đạt2/2PASS, khôngxóakếtquảcũ. Nhưvậy mọi stageđãcó lượtPASS, nhưng khôngghilàlệnhpipeline banđầu exit0.
- Log: pipeline-final.log vàruntime-final.log trongbackupdir (PowerShellUTF16LE); pipeline-attempt1.log ghi môi trườngthiếurequests đãkhắcphục.
- Runtime không thấy nút MappingTênViệt nên khôngkiểmclicknútnày; pageload/APItestPASS.
- Sessionmemory37700 khôngkếtnối; tiếnđộđãlưu tasktodo + session/Handoff local.
