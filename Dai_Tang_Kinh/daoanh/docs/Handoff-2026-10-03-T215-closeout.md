# Handoff-2026-10-03-T215-closeout

## 1. Đọc nhanh

| Mục | Trạng thái |
|---|---|
| Task | T215; thao tác có chứng cứ xong, học thuật in_progress |
| HEAD lúc bàn giao | 0a662ebd5fbe6655cc3a165faaeed05f073b6d44; session này không commit/stage |
| Preflight / DB / TTL / rollback | PASS, verification.json/sync-report.json |
| API / Dashboard | 5+2 API PASS;8 filename/2 DONE/6 pending đúng |
| Pipeline | Đã chạy; runtime mạng chặn, retry có mạng2/2 PASS;click Mapping chưa kiểm |

## 2. Đọc trong 2 phút

Đã sync Phước Châu, hợp nhất Đại Ninh, sửa provenance Thạch Cữu/ID Mã Tổ/Phong Huyệt và metadata Phật Ý. Audit 1037/1037;0 self/URI trùng/vòng. Admin mở 8URI Dashboard, đọc chứng cứ pending, bổ sung nguồn khi có; không phải sửa code. Local DB, chưa deploy.

## 3. Vấn đề, sửa và bằng chứng

Mã Tổ A038890 道一/みちかず sai;DILA A003623 馬祖道一 đúng, thầy A004015. Phong Huyệt A004981 南院慧顒 sai;DILA A004982 風穴延沼 đúng, thầy A004981, trò A004983. Phước ChâuA003636 thầy A001897; Thạch CữuA019919 thầy A003623. XML/hash/source URL ở dila-evidence.json. Rút142assertionTTL, thêm72assertion/36 cặp,44 đề xuất bỏ qua. 40 ký tựÐ→Đ; số đời row cũ không đổi. [Report](reports/T215-closeout-20261003/README.md).

## 4. Cảnh báo bắt buộc

Worktree chung/HEAD di động: không git add cả docs/tasks. TTL không git track: backup bytes/manifest bắt buộc. Khôngrestore cả DB hoặcfull ETL bypass guard. Raw XML/assertionquốc tế bất biến. Khôngsuy đời thầy + 1, cần3dữ liệu độc lập, cùng hệ đếm. Khôngimport lại file cách ly chưa khóa danh tính.

## 5. Hoàn tác

~~~powershell
# cwd: Dai_Tang_Kinh
python -X utf8 daoanh/docs/reports/T215-closeout-20261003/apply_closeout.py --revert
~~~

| Phần | Mất dữ liệu? |
|---|---|
| DB | Restore từng row có guard, không restore cả DB |
| TTL | Restore bytes từng file, bản cách ly giữđối chiếu |
| Docs/Dashboard | Backup data/backups/T215-closeout-20261003/docs;so sửa mới trước khôi phục |

## 6. File tạo/sửa

Report T215-closeout-20261003: plan,prepare/apply/revert/verify,audit trước/sau, XML/API,1037dossiers/26 cặpđời/logs. Backup T215-closeout-20261003: change-plan,before/afterrows,TTLbytes,docs. Quarantine T215-closeout-20261003: 7 file/manifest. Dashboard:t215-eight-uri(.html/-cases.json),t215-other-ttl-bugs.html,t215-closeout-summary.json vàsection t215-review củaDashboard chính. Docs:tasktodo,task T215,plan,session,Handoff,ROLLBACK.

## 7. Sai lầm đã sửa / bài học

Script tạm inspect.py che stdlib inspect;đã đổi inspection_legacy.py. Runtime retry đầu khôngunlink log Windows;output riêng tránhxoá folder người khác. JS raw template chứa backtick Markdown gây lỗi parser;file chưađược ghi, đổi fence tilde rồi tạo lại. Dùng Graph.parse(data=UTF8), hash bytes để tránh lỗi Path trên Windows. Thiếu ID/quan hệ trong một bản DILA không chứng minh không tồn tại. Dẫn X1667_p0560a03 cho Đại Xa đã bị bác bỏ.

## 8. Chưa xong, ưu tiên

1. 6 pendingURI:Di Phong,Trí Bản,Đại Xa,Minh Hoằng,Tuyết Giàu,Linh Cưu;giữdossier,không gán ID suy đoán.
2. 783 fileflag và44 đề xuất thiếu căn cứ;chưa xác minhweb từng người,flagkhông đồng nghĩa lỗi.
3. 26 cặpđời cần3nguồn/cùng hệ đếm. DB Mã Tổ/Phong Huyệt đời NULL giữNULL,TTL 35/41 nguyên;row mớiPhước Châu37chỉ tham chiếu.
4. Runtime suite không tìm thấyMapping Tên Việt nên chưa kiểm click;không sửa testđểlàm xanh.

Không có câu hỏi buộc Admin sửa code hoặcquyết ID thiếu dữ liệu.

## 9. Kiểm tra nhanh

~~~powershell
python -X utf8 daoanh/docs/reports/T215-closeout-20261003/verify_closeout.py
node daoanh/docs/reports/T215-closeout-20261003/check_dashboard.cjs
~~~

Guard fail:đọc sửa mới,không ép snapshot cũ. Xemlogs pipeline/runtime retry trongreport.

## 10. Cho agent kế tiếp

Đọc change-plan,sync-report,verification,dossiers trước sửa. Khôngapply2lần hoặcpublish lại(chứng cứappend lặp). DILA canonical;TTL Việt tham chiếu. Sửa mới cầnsource/old-value/hash guard/backup/API/rollback. Memory37700được thử cuối phiên;nếu không chạy,đọc memory-save.json và tasktodo. Khôngcommit/stagephiênnày.
