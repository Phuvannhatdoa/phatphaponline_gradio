# Handoff — T390 endpoint section removal — 2026-10-14

## 1. Bảng thông tin đọc nhanh

T390 scoped follow-up; initial HEAD 1b19192d1391b58d1b5526560122773845b5a27d. Focused Node check PASS; 0 DB/TTL/progress JSON mutation.

## 2. Đọc trong 2 phút

Admin muốn bỏ section live, giữ lịch sử. Đã xóa markup và renderer endpointTable; các section khác và T358 nguyên vẹn. Root đã giao scoped commit.

## 3. Thay đổi và chứng cứ

HTML giảm 34 dòng. Test old-render thiếu table bị lỗi; new-render chạy được, giữ các renderer khác. 5 inline scripts parse PASS, toàn bộ ID khác và nút giữ nguyên.

## 4. Cảnh báo bắt buộc

Git chạy tại visjs-app; worktree dùng chung. Không xóa backup lịch sử, không stage progress JSON. Không claim browser/full pipeline PASS từ Node fixture.

## 5. Revert

git revert --no-edit <SHA> tại repo root; SHA xem Git log/commit receipt. Chỉ code/docs, không mất DB.

## 6. File tạo/sửa

HTML; tests/test_t390_endpoint_section_removal.cjs; task T390; session docs/sessions/2026-10-14_T390-endpoint-section-removal/; Handoff này.

## 7. Sai lầm và bài học

Chỉ xóa DOM sẽ làm renderer null-error; regression kiểm chứng điều đó. Không xóa các snapshot có cùng tiêu đề.

## 8. Việc chưa xong

Browser QA bổ sung và Admin nghiệm thu; common gates chưa được coi là full PASS. Không có migration hoặc importer cần chạy.

## 9. Kiểm tra nhanh

node tests/test_t390_endpoint_section_removal.cjs tại daoanh; Git log/diff tại visjs-app.

## 10. Agent kế tiếp

Đọc scoped session, giữ T358/local review semantics, không regenerate dữ liệu cho thay đổi HTML này. Chỉ restore/revert owned patch, không ghi đè WIP.
