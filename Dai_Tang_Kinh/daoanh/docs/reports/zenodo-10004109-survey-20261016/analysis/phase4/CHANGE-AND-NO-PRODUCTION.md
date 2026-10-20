# Phase4 — Báo cáo thay đổi và không tác động production

## Đã thay đổi

Chỉ tạo file ở thư mục analysis/phase4 của survey Zenodo 10004109. Tạo model, builder, các lớp dữ liệu riêng, fixture SIMULATED, preview tĩnh, ma trận/test runner và tài liệu. Danh sách đầy đủ ở README.

15 người được chọn gồm cặp A004166/A000587 và ba A027200/A027195/A027242 bắt buộc, sau đó chọn node kề nguồn theo thứ tự xác định. 23 observation là mẫu cảm sinh trên 15 người; việc không có cạnh trong mẫu không là phủ định lịch sử. Giữ riêng các UUID, hai witness và cảnh báo CSV.

## Input và integrity

Chỉ đọc mười một JSON đã giao: bốn Phase3, sáu Phase2 và manifest Phase1. Hash byte hiện tại được pin trong phase4-manifest.json; metadata hash cũ và observed hash là hai trường riêng.

**Observed Phase4 snapshot pending investigation, không frozen-chain PASS.** Sáu hash Phase2 dẫn trong metadata P3 không khớp input hiện tại, kể cả kiểm biến thể CRLF/LF. Các hash Phase3 được đối chiếu và ghi kết quả riêng. Không sửa, chuẩn hóa hoặc cập nhật nguồn/manifest upstream để làm chúng khớp.

Builder và tests so hash đầu vào trước/sau để xác nhận mười một input không đổi trong chính lần chạy. Đây không phải chứng nhận mọi file trên máy không đổi bởi phiên khác.

## Ranh giới ghi/đọc

- Builder chỉ ghi allowlist tên file có dirname đúng Phase4; không theo đường dẫn file từ record nguồn để mở raw corpus.
- Không mở DB, TTL, app.py hoặc code/data production. Không thêm route/API/HOME/public/export. Không gọi DILA/Marcus/CBETA mới hoặc trả phí.
- Không acceptance, owl:sameAs hoặc suy thế hệ. Mapping thật chưa có ứng viên/nhãn Việt được cung cấp thì null; fixture mapping riêng và simulated.
- Không source-label overwrite. Không coi CSV/GEXF cùng work là nguồn độc lập. Không biến directed thiếu chứng cứ thành có hướng.
- Preview dùng file://, script/CSS cạnh nó, CSP connect-src none; không fetch, CDN, browser storage, nhập/xuất hay nút duyệt.
- Kiểm UI trên origin giả ngoài máy được route-fulfill trong Chromium để kiểm guard; không có transport tới host thật.
- Không commit/stage và không ghi tasktodo/DB memory ngoài Phase4 trong phạm vi này. Báo cáo root để điều phối bước sau.

## Kết quả và việc còn lại

Xem test-results.json cho kết quả thực chạy, TEST-MATRIX.md cho acceptance. PASS kỹ thuật không xác nhận sự thật lịch sử, mapping, số đời hoặc quyền.

Cần điều tra recorded-vs-observed upstream hash, cần bộ quan hệ/định danh độc lập đúng phạm vi nếu muốn so DILA/Marcus thật, và cần xử lý quyền theo từng nguồn trước bất kỳ sử dụng khác ngoài preview local. Không tự mở các bước đó ở Phase4.
