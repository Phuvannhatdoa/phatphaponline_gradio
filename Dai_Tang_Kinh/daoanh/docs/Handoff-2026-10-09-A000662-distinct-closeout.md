# Handoff — 2026-10-09 — xác nhận tách A000662

## 1. Bảng thông tin đọc nhanh

| Mục | Kết quả |
|---|---|
| HEAD quan sát09/10 | c5e3afba45a262afec0e104afbe1f48e60b99ce4; không stage/commit |
| Phạm vi | Hoàn tất bàn giao quyết định Admin ngày05/10; kiểm tra lại ngày09/10 |
| Định danh | A000662 明海 khác Minh Hải Pháp Bảo, khai tổ Chúc Thánh |
| DB hiện tại | Registry linji_chucthanh revision2, quyết định distinct_person còn nguyên, root/anchors rỗng |
| TTL/DB hôm nay | Read-only; không sửa TTL, DB, quan hệ hay số đời |
| Test | Pipeline retry05/10 exit0, runtime2/2; chưa chạy lại full pipeline ngày09/10 vì chỉ kiểm tra và sửa docs |
| Data quality | Báo cáo05/10 còn2metricFAIL; không claim all data PASS |
| Task tổng | T232 còn duyệt mốc/corpus; T233 đang bị giới hạn gói Codex |

## 2. Đọc trong 2 phút

Đã hoàn thành việc ghi xác nhận của Admin: A000662 và Minh Hải Pháp Bảo Chúc Thánh là hai nhân vật khác nhau. Bản ghi DILA A000662 giữ nguyên; không dùng làm khai tổ hoặc mốc số đời Chúc Thánh. ID riêng của Minh Hải Pháp Bảo vẫn chưa được chứng minh. Snapshot hiện tại: docs/reports/T232-A000662-followup-20261009/current-state.json.

Ba việc tiếp: xác minh ID riêng Minh Hải Pháp Bảo; duyệt mốc/truyền pháp theo chuẩn ba nguồn; tiếp tục T233 khi hạn mức Codex cho phép. T233 hiện1.312/48.673ID đã xử lý, job blocked_session vì usage limit. Log lỗi05/10 ghi thử lại Oct10th2026 10:21AM; đây là thời gian được log báo, không phải lời xác nhận hạn mức đã reset. Codex hiện vẫn đăng nhập ChatGPT; không gọi lại model hôm nay.

## 3. Thay đổi và bằng chứng

Ngày05/10 append revision1→2 của hệ Chúc Thánh, lưu identity_decisions/provenance_kind=admin_confirmation/nguyên văn lời Admin/recordXMLhash. Chỉ thay metadata registry, không ghi số đời. apply-result.json xác nhận tám hệ khác và hồ sơ DILA/name_vi_map giữ nguyên. Không có ánh xạ sai ở ttl_mapping/ttl_master/name_vi_map cần xóa trong lượt đó.

Ngày09/10 chỉ SELECT read-only và xác nhận decision_retained=true, incorrect_A000662_root_or_anchor=false. Cập nhật docs/tasktodo, trạng thái T233 và Dashboard để kết thúc bàn giao còn dở.

## 4. Cảnh báo bắt buộc

- Không ghép A000662 vào Minh Hải Pháp Bảo vì trùng tên 明海; không tạo sameAs hai người.
- Quyết định có nguồn là xác nhận Admin; không gọi đó là ba sử liệu độc lập hay tự gán số đời.
- Metadata registry ghi rõ quyết định; chưa có hard guard code riêng cho identity exclusion. Các sửa mốc tương lai phải tuân thủ quyết định đã lưu.
- Không restore toàn DB trong worktree nhiều phiên. TTL bị Git ignore; giữ backup file-level.
- T233 không API trả phí, không auto fallback hoặc retry liên tục khi còn usage limit.
- Kết quả pipeline được đọc lại ngày09/10 là lượt chạy05/10, không phải kiểm tra mới hôm nay.

## 5. Hoàn tác

```powershell
# Tại daoanh; chỉ dry-run:
python -B -X utf8 docs/reports/T232-A000662-distinct-20261005/revert_decision.py
# --apply chỉ khi Admin chủ động muốn rút quyết định.
```

Hoàn tác append một revision mới, giữ audit; guard chặn nếu có revision khác sau2. Backup: data/backups/T232-A000662-distinct-20261005/scheme-before.json. Không restore DB nguồn, không mất TTL/people/quan hệ/số đời. Dry-run05/10 PASS; chưa apply revert.

## 6. File đọc/tạo/sửa

Đã đọc pipeline-retry.log/exit, apply-result.json, registry DB read-only, log quota group5 và Codex login status. Đã tạo verify_current.py/current-state.json trong report followup09/10, Handoff này và session log. Cập nhật README quyết định05/10, tasktodo, T233 và Dashboard; không thay code ứng dụng hoặc DB hôm nay.

## 7. Sai lầm và bài học

Script tạm tên inspect.py ngày05/10 đè tên thư viện Python inspect; đã đổi thành audit_registry.py. Bản nháp task .md dưới docs/reports bị guard xem là task trùng; đã đổi thành .md.prepared, giữ nội dung và đổi manifest. Hai lỗi đã sửa trước pipeline retry exit0. Không cấp taskID mới để né guard.

## 8. Việc chưa xong

ID đúng hoặc thực thể local có chứng cứ cho Minh Hải Pháp Bảo Chúc Thánh; mốc số đời và cạnh truyền pháp; corpus generation. T233 còn47.361ID chưa xử lý và đang chờ quota. Backend controls Codex còn cần xác minh đã reload, chưa thực hiện restart trong lượt này.

## 9. Kiểm tra nhanh

```powershell
python -B -X utf8 docs/reports/T232-A000662-followup-20261009/verify_current.py
python -B -X utf8 scripts/codex_namevi_session.py status
Get-Content data/codex_names/23300000000000000000000000000002/group-5/events.jsonl -Tail 3
npm.cmd run dup:ids
```

Không tự chạy model lại khi log còn báo thời gian reset tương lai; không mua credit/API key thay Admin.

## 10. Ghi chú agent kế tiếp

Đọc tasktodo và report quyết định; bảo toàn revision2 và hồ sơ A000662. DILA dynasty明, birth/death NULL: không đoán ngày sinh/mất. Nếu xác minh được khai tổ Chúc Thánh thì khóa ID/tên/nguồn riêng, không dùng A000662. T233 fulljob39836c390adf4e9993649eacca7a546c, folder23300000000000000000000000000002; năm nhóm ingested, group5 failed usage limit. Khi quota cho phép mới resume job cũ, bỏ request đã nhập; không tạo giả kết quả để tăng tiến độ.

### Kiểm tra tài liệu cuối lượt09/10

Dup:ids hôm nay exit0, không có taskID trùng. Dashboard đang build khi ghi bàn giao; kết quả cuối xem dashboard.exit/dashboard.log trong report followup09/10, không claim PASS khi chưa có exit. Claude-mem37700 không truy cập được, observationJSON và error được lưu local. Các tác vụ quét chạy tiếp độc lập; tasktodo và trạng thái T233blocked đã được ghi với SHA guard.
