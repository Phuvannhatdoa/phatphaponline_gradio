# Handoff — 2026-10-10 — Minh Hải Pháp Bảo TTL local

## 1. Thông tin đọc nhanh

| Mục | Trạng thái |
|---|---|
| Ngày / HEAD đo | 2026-10-10 / 03903d98055e00330a126fe5d851db8c4ab8c3bb |
| Phạm vi | Một TTL Minh Hải và docs theo chỉ thị Admin |
| TTL | Đã áp dụng có backup/CAS hash |
| RDF / reader T226 | PASS / conforms=true, không DILA-ID |
| Preflight | exit1: 23 flags ở file khác; Minh Hải không bị flag |
| Pipeline | guard PASS; dup:ids FAIL 8 ID có sẵn; phần sau chưa chạy |
| DB / DILA / registry / UI | Không ghi hoặc import |
| Task | T232 vẫn giữ phạm vi chung; hồ sơ local đã cập nhật |
| Claude-mem | Không kết nối port37700; request/result local |

## 2. Đọc trong 2 phút

TTL active trước sửa có URI Minh Hải nhưng nhãn chính là Nguyên Thiều, tiểu sử rỗng, đời71. Đã sửa nhãn thành Minh Hải Pháp Bảo, thêm tiểu sử Việt và nguồn Admin PTDA. Giữ71 và ghi Ma Ha Ca Diếp=1; không suy số mới. Hồ sơ chưa có DILA-ID, A000662 vẫn bị loại trừ.

[Báo cáo chi tiết](reports/Minh-Hai-local-TTL-20261010/README.md), [checks](reports/Minh-Hai-local-TTL-20261010/checks.json).

Ba hướng tiếp nối khi làm tiếp: (1) xem dữ liệu local đã chỉnh; (2) chọn luồng sync riêng local nếu cần UI/DB cập nhật; (3) kiểm chứng mốc và đường truyền trước accepted/đệ quy. Không cần Admin phê chuẩn lại sửa TTL này; đã được chỉ thị trực tiếp.

## 3. Vấn đề, cách sửa và kết quả đo

| Vấn đề | Sửa / bằng chứng | Kết quả |
|---|---|---|
| Sai nhãn chính | Admin và triple Minh Hải trong TTL Nguyên Thiều/đệ tử | Minh Hải Pháp Bảo @vi, 明海法寶 @zh-Hant |
| Tiểu sử trống | Soạn thông tin local theo xác nhận Admin, có nguồn và ngày | bkg:biographicalNote @vi đã điền |
| Mốc71 chưa ghi gốc đếm | Giữ số cũ, bổ sung RDF Statement / countingScheme | Ma Ha Ca Diếp1, Nguyên Thiều70, Minh Hải71 |
| DILA chưa khóa ID | Giữ local identifier / sourceNote | Không gán A000662, không owl:sameAs |

12→36 triples; removed2 chỉ là nhãn sai và biography trống. Các triple khác từ trước giữ nguyên. 0 self-edges, teacher đối ứng ở TTL Nguyên Thiều. Tính nhất quán local không đồng nghĩa chứng minh toàn đường truyền lịch sử.

## 4. Cảnh báo bắt buộc

- TTL ignored Git; git revert không khôi phục file này. Dùng file-level backup/manifest.
- Phân biệt nguồn tu học/pháp mạch Báo Tư với quê sinh; không đồng nhất hai nhân vật hay chùa cũ/Tân Tự.
- Metadata số đời source_asserted, không phải accepted v2. Không tạo ba nguồn giả từ các file lặp cùng thông tin.
- Chưa sync DB / UI; không lấy RDF PASS làm bằng chứng API đã hiện dữ liệu mới.
- Pipeline chưa xanh; 8 ID task trùng thuộc kho chung. Không rename task/session của người khác tự động.
- Preflight còn flags các TTL khác. Không full importer hoặc sửa 23 file theo scanner mà thiếu kiểm chứng.
- Worktree có session song song. Mọi git từ visjs-app; không stage cả docs/tasks. Không commit trong phiên này.

## 5. Revert từng phần

| Phần | Hoàn tác | Mất dữ liệu vận hành? |
|---|---|---|
| TTL Minh Hải | Script hash-guard dưới đây | Không; trả về bytes trước sửa, bảo vệ chỉnh sửa mới |
| DB / registry / UI | Không có mutation để revert | Không |
| Docs bổ sung | Thêm ghi nhận superseded/reverted sau khi hoàn tác, giữ lịch sử | Không |

Từ daoanh:

```powershell
python -B -X utf8 docs/reports/Minh-Hai-local-TTL-20261010/revert_ttl.py --dry-run
python -B -X utf8 docs/reports/Minh-Hai-local-TTL-20261010/revert_ttl.py --apply
```

Backup: data/backups/Minh-Hai-local-TTL-20261010-d60a0689/TS-Minh-Hai-Phap-Bao.ttl. Script chỉ ghi đúng TTL này nếu current hash bằng after hash; nếu có sửa mới sẽ từ chối. Dry-run đã kiểm, chưa thực sự restore file đang đúng. Không restore toàn bộ tasktodo từ phiên cũ vì có thể đè session khác.

## 6. File tạo/sửa

| File | Vai trò |
|---|---|
| data/ttl/TS-Minh-Hai-Phap-Bao.ttl | Hồ sơ local đã sửa |
| data/backups/Minh-Hai-local-TTL-20261010-d60a0689/TS-Minh-Hai-Phap-Bao.ttl | Bản sao bytes trước sửa |
| tasks/T232-evidence-based-generation-engine.md | Thêm ghi nhận local, không đổi task ID |
| docs/tasktodo.md | Thêm status note local, giữ các note khác |
| docs/reports/Minh-Hai-local-TTL-20261010/ | README, candidate, before/plan/manifest/checks/logs/verifier/revert/observation |
| docs/sessions/2026-10-10_Minh-Hai-local-TTL.md | Log phiên |
| docs/Handoff-2026-10-10-Minh-Hai-local-TTL.md | Handoff |

File Nguyên Thiều và bản old Minh Hải giữ SHA từ trước tại kiểm tra cuối. Các hashes trong manifest.

## 7. Sai lầm thao tác và bài học

Lệnh rg tương đối daoanh chạy ở repo root nên không thấy module; chạy lại bằng đường dẫn repo root. Kiểm validator dùng nhầm khóa valid trong khi hàm trả conforms; sửa lệnh kiểm, không sửa hệ thống. Reader xác nhận conforms=true, errors0, 12 cảnh báo legacy theo thiết kế.

Không gọi source_asserted là accepted, không nói pipeline PASS khi dừng ở duplicate ID. Không phát âm thông báo pipeline thành công trong trạng thái fail.

## 8. Việc chưa xong

1. Đồng bộ riêng hồ sơ local vào DB nếu có yêu cầu tiếp; đọc mapping hiện tại, backup, dry-run, API readback trước apply.
2. Kiểm đầy đủ ba gốc chứng cứ độc lập và từng cạnh truyền pháp trước kích hoạt mốc số đời.
3. Xử lý 23 flags TTL khác theo từng danh tính, và duplicate task IDs trong phạm vi task riêng.
4. Bổ sung DILA crosswalk khi đúng người đã được xác minh; không đợi hoặc giả định ngày DILA cấp ID.
5. Claude-mem chưa nhận observation. Không có câu hỏi Admin cần quyết để hoàn tất sửa TTL local đã được chỉ thị.

## 9. Lệnh kiểm nhanh

Từ daoanh:

```powershell
python -B -X utf8 docs/reports/Minh-Hai-local-TTL-20261010/verify_change.py --active
python -B -X utf8 docs/reports/Minh-Hai-local-TTL-20261010/revert_ttl.py --dry-run
```

Kỳ vọng verifier ok=true, đời71, thầy70, root1, self_edges0, dila_id null, reference_hashes_unchanged true. Kiểm này có thể fail đúng nếu session khác sửa file tham chiếu; đọc lại và không áp backup cũ bừa bãi.

## 10. Ghi chú cho agent kế tiếp

- Đọc README/manifest/checks trước khi sync.
- Nguồn gốc local PTDA đã được Admin chỉ thị; DILA-ID chưa khóa vẫn là trạng thái riêng.
- TTL giữ legacy URI để các file thầy/trò tiếp tục tham chiếu.
- Chưa migration toàn profile2.0; metadata bổ sung được giữ qua original TTL, không tự chiếu thành accepted.
- Không tăng số đời, không đổi hasTeacher thành quan hệ truyền pháp đã duyệt chỉ từ chữ bối/cùng chùa.
- Nếu làm code/build về sau, cần pipeline xanh trước yêu cầu review; log lần này chỉ chứng minh guard chạy và dup:ids dừng.
- Nếu dịch vụ37700 hoạt động, gửi observation-request.json đã lưu; chưa có receipt.
