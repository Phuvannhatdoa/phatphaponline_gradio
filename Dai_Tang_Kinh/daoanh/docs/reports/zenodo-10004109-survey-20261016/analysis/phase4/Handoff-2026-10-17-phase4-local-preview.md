# Handoff 2026-10-17 — Phase4 local preview

## 1. Đọc nhanh

Chỉ analysis/phase4; không commit. Dữ liệu thật 15 người/23 observation, fixture riêng SIMULATED. Không DB/TTL/production; kết quả tests trong test-results.json.

## 2. Đọc trong hai phút

Mở preview.html bằng file://. Ba mode: nguồn, đối chiếu tác phẩm và chứng cứ. Root kiểm safety, test evidence và cảnh báo input hash trước mọi quyết định tiếp.

## 3. Thay đổi có chứng cứ

Tách dataset/version/representation/identity/observation/evidence/mapping. Hai GEXF witness + CSV discrepancy còn riêng. Đủ 41 low linkGrp, 71 mục inventory, ba 0/? và rights matrix bốn TEI. Manifest hash input/output dữ liệu; source label/raw record giữ nguyên.

## 4. Cảnh báo bắt buộc

Observed snapshot pending investigation: recorded/observed hash khác; không frozen-chain PASS. Chưa clearance quyền, không public/export. CSV/GEXF cùng work không độc lập; thiếu cạnh/cert không là phủ định/chắc chắn. Không accepted mapping hay suy đời.

## 5. Revert

Chưa commit hoặc production mutation. Nếu cần bỏ preview, lưu bản Phase4 cho review rồi chỉ dọn đúng thư mục này theo root; không đụng Phase1–3. Không có DB/TTL cần restore.

## 6. File

Xem bảng README và phase4-manifest.json. Tất cả file mới nằm Phase4; test artifact/ảnh local cũng ở đây. Không dùng tên fixture như claim nguồn thật.

## 7. Sai lầm / bài học

Builder đầu coi hash cũ là byte hiện tại nên dừng đúng gate. Root đã phê chuẩn snapshot observed riêng với cảnh báo; không âm thầm sửa hash upstream. Giữ lớp provenance để không nhầm PASS tái tạo với PASS chuỗi lịch sử.

## 8. Chưa xong

Root QA; điều tra integrity upstream; dữ liệu quan hệ DILA/Marcus thật chưa được giao; mapping nhãn Việt/target chưa được cung cấp; quyền chưa clearance. Không tự mở tích hợp.

## 9. Kiểm nhanh

Trong Phase4 chạy node build_phase4.mjs --verify và node test_phase4.cjs. Xem counts, recorded/observed hash và tests. Xem hai ảnh chỉ tại máy.

## 10. Agent kế tiếp

Đọc README, ma trận và change report. Chỉ ghi Phase4; không gọi API, importer, DB/TTL hoặc code production. Không stage/commit. Mọi bước nghiên cứu/acceptance/clearance tiếp theo cần scope riêng do root điều phối.
