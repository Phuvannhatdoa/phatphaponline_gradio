# T215 — Closeout có chứng cứ, 2026-10-03

Đã thực hiện các mục có căn cứ và cách ly file gây xung đột. Phần thiếu chứng cứ được bỏ qua; không tuyên bố toàn corpus đã được chứng nhận học thuật.

## Kết quả

| Kiểm tra | Kết quả |
|---|---|
| TTL đang dùng | 1037/1037 RDF hợp lệ, mỗi file một main subject |
| Tự nối / URI trùng / vòng thầy–trò | 0 / 0 / 0 |
| Trước xử lý | 1044 file; 2 rỗng, 1 main unsupported, 1 multiple main, 4 nhóm URI trùng, 2 vòng |
| File cách ly nguyên bytes | 7, có manifest và backup |
| Assertion TTL sai | 142 rejected, mapping_verified=0; giữ lịch sử |
| Assertion mới | 72 thuộc36 cặp có DILA xác nhận; các file có thể cùng xác nhận một cặp |
| Đề xuất remap bỏ qua | 44 source-edge thiếu căn cứ, không suy ID thay thế |
| Mã hóa | 40 ký tự Ð đổi thành Đ trong5 TTL; URI, Hán tự, quan hệ giữ nguyên |
| Số đời | Mọi row đã có giữ nguyên;26 cặp review |
| DB / API / rollback | PASS;5 hồ sơ API +2 kiểm người từng bị gán nhầm |
| Dashboard | 8 filename;2 DONE,6 pending status trống; mở chứng cứ PASS |
| Raw XML / nguồn quốc tế | Zip và hash toàn bộ assertion không thuộc TTL không đổi |

## Đã xử lý

| File | ID và hành động |
|---|---|
| TS-Phuoc-Chau-Dai-An.ttl | A003636 福州大安; thầy A001897. DB/API PASS. Row mới chép37 tham chiếu TTL, chưa tái chứng nhận số đời. |
| TS-Dai-Ninh-Dao-Khoan.ttl | A020545 大寧道寬; thầy A001439. Giữ45 và URI dao_ninh_dao_khoan; bản TS-Dao-Ninh trùng lưu cách ly. |
| TS-Thach-Cuu.ttl | A019919 石臼; thầy A003623. Đổi provenance DB TS-Linh-Cuu → TS-Thach-Cuu. Không tạo Linh Cưu từ Thạch Cữu. |
| TS-Ma-To-Dao-Nhat.ttl | A003623 馬祖道一, không phải A038890 道一/みちかず. Bổ sung owl:sameAs; rút TTL assertion Nhật Bản. DB đời NULL giữNULL; TTL 35 nguyên. |
| TS-Phong-Huyet-Dien-Chieu.ttl | A004982 風穴延沼, không phải A004981 南院慧顒. Thầy A004981; trò A004983. DB đời NULL giữNULL; TTL 41 nguyên. |
| TS-Phat-Y-Linh-Nhac.ttl | Phục hồi metadata/provenance Phật Ý sau file Trường Viễn ghi đè. Chưa gán DILA ID; row đời72 giữ nguyên. |

[DILA Mã Tổ](https://authority.dila.edu.tw/person/search.php?aid=A003623), [DILA Phong Huyệt](https://authority.dila.edu.tw/person/search.php?aid=A004982), [DILA Phước Châu](https://authority.dila.edu.tw/person/search.php?aid=A003636). Record XML/source/hash có trong [dila-evidence.json](dila-evidence.json).

## Cách ly / chưa xác minh

7 file lưu nguyên tại data/ttl_quarantine/T215-closeout-20261003, backup bytes tại data/backups/T215-closeout-20261003/ttl:

- TS-Dot-Khong-Tri-Ban.ttl: có tên 突空智板 trong X1667; chưa có DILA ID/thầy khóa đúng. Không khẳng định DILA không có ID.
- TS-Tuyet-Giau-Chon-Phac.ttl: chép2 block Phong Huyệt; chưa chứng minh 雪梪真發 ↔ 雪槱真樸 cùng người.
- TS-Dai-Xa-Nhu-Truong.ttl, TS-Minh-Hoang-Tu-Dung.ttl: admin đã để trống trước lượt này; giữ dossier, không import. Dẫn X1667_p0560a03 cho Đại Xa đã bị bác bỏ.
- TS-Truong-Vien.ttl: chép URI/biography Phật Ý; chưa xác minh Trường Viễn.
- TS-Phuc-Chau-Dai-An.ttl: template rỗng; không suy ID từ filename. Alias DB phuc_chau_dai_an giữ nguyên; API chọn row canonical Phước Châu verified.
- TS-Dao-Ninh-Dao-Khoan.ttl: bản trùng lưu nguyên; dùng bản Đại Ninh canonical.

TS-Di-Phong-Kinh-Ninh.ttl và TS-Linh-Cuu.ttl đã không có trước lượt này; không tái tạo/gán ID suy đoán. 6 hồ sơ URI pending vẫn có filename + chứng cứ, status trống.

[File-decisions.jsonl](file-decisions.jsonl) chứa một dossier cấu trúc/hash/quyết định cho mỗi file trong 1.037 file;783 file có cờ không đồng nghĩa sai. Kiểm DILA toàn corpus dùng DB local, mapping legacy có thể sai, chưa xác minh web từng người. Giữ101P1alias khácsubject và77 filename khácslug khi chưa chứng minh lỗi. [Generation-review.json](generation-review.json) có26 cặp; không sửa đời thiếu3dữ liệu độc lập, cùng hệ đếm.

## Kiểm thử

[Verification](verification.json), [API](api-verification.json), [Dashboard](dashboard-verification.json) PASS. npm run pipeline đã chạy: các bước trước runtime PASS, runtime bị ERR_NETWORK_ACCESS_DENIED ở CDN dẫn L is not defined. Chạy lại nguyên2runtime test với mạng và output riêng:2/2 PASS; không bỏ assertion. Logs: [pipeline](pipeline-utf8.log), [runtime retry](runtime-network-output-utf8.log).

Suite báo không tìm thấy nút Mapping Tên Việt và bỏ qua nhánh click theo logic hiện có: PASS chứng minh tải trang/API, chưa chứng minh nhánh click đó. Retry đầu bị Windows khóa test-results/.last-run.json; dùng output riêng, không xoá folder session khác.

## Kiểm tra / rollback

Chạy từ Dai_Tang_Kinh:

~~~powershell
python -X utf8 daoanh/docs/reports/T215-closeout-20261003/verify_closeout.py
node daoanh/docs/reports/T215-closeout-20261003/check_dashboard.cjs
python -X utf8 daoanh/docs/reports/T215-closeout-20261003/apply_closeout.py --revert
~~~

Rollback DB từng row và TTL từng file có guard: dữ liệu đã đổi thì dừng; không restore cả DB. Bản cách ly giữ lại để tra cứu. Docs/Dashboard backup riêng ở data/backups/T215-closeout-20261003/docs; so với sửa mới trước khôi phục. Không apply hai lần hoặc tự chạy publish_closeout.py lại vì sẽ append chứng cứ lặp. Chỉ local DB, chưa deploy server từxa.
