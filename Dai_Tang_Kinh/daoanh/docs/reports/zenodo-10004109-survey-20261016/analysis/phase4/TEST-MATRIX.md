# Phase4 — Ma trận kiểm thử

Các ca dưới kiểm thuật toán trình bày, không chứng nhận lịch sử, quyền hoặc đồng nhất DILA/PTDA.

| Ca | Dữ liệu | Kết quả bắt buộc |
|---|---|---|
| Agree | SIMULATED: hai work cùng người/loại/chiều | Một nhóm, hai observation và hai work; không mất bằng chứng |
| Different path | SIMULATED: A–B–C và A–D–C | Bốn cạnh, bốn người; không chọn đường đúng/thắng |
| Different type | SIMULATED: truyền pháp và thọ giới | Hai nhóm riêng dù endpoint trùng |
| Undirected | SIMULATED: vô hướng và có hướng | Hai nhóm; vô hướng không có mũi tên |
| Undefined direction | Chưa có chứng cứ chiều | Không chuyển thành directed dù trường direction ghi directed |
| Generation system mismatch | SIMULATED: hệ một 1 / hệ hai 71 | Cùng một người, hai nhãn hệ đếm; không cộng hoặc nhân đôi |
| Real witnesses | Hai GEXF locator và CSV lệch UUID/locator | Giữ cả ba observation; 0300b07 / 0412a05 cùng tồn tại |
| Source independence | CSV/GEXF cùng cụm ZTJ | Hai biểu diễn không thành hai nguồn độc lập |
| Unknown generation | Ba CSV “0” / workbook “?” | Giữ chuỗi gốc và locator; không coi 0 là gốc |
| Uncertainty | 41 linkGrp cert=low | Giữ đủ 41 và toàn bộ inventory 71; không thiếu-cert = chắc chắn |
| Mapping | 15 người nguồn | Bảy trường tách riêng; proposed/unreviewed; không accepted |
| Provenance | Hash cũ khác byte hiện tại | Lưu cả recorded/observed; hiện cảnh báo, không tự sửa Phase1–3 |
| Rights | Bốn TEI mixed declarations | Chưa clearance; không áp license lên PTDA/DILA/CBETA |
| Origin/network | file:// và origin ngoài máy | file:// hoạt động; origin ngoài máy không render; không HTTP/API |
| UI | Bàn phím, màn 375px, XSS text | Ba mode dùng được, bảng tự cuộn, script/HTML dữ liệu không chạy |

Chạy node test_phase4.cjs; kết quả thực tế ghi test-results.json. Chạy node build_phase4.mjs --verify để kiểm khả năng tái tạo dẫn xuất mà không ghi output. PASS ở đây chỉ áp dụng kiểm kỹ thuật nêu trên.
