# T233 — Codex ChatGPT session, 2026-10-05

Admin xác nhận chỉ dùng Codex/Claude Code Cloud Session, **không API trả phí**. Cách Batch API của ngày 04/10 đã được thay bằng Codex CLI đăng nhập ChatGPT.

## Kết quả đã kiểm chứng

- Máy có codex-cli 0.159.2; login status: Logged in using ChatGPT. Phép thử thực với gpt-6.1-sol thành công, không dùng output giả.
- Mẫu 32 ID và nhóm 256 ID đã lưu: **288/48.673** tại mốc bàn giao ban đầu; 19 tên cần kiểm. Giá trị hiện tại đọc DB hoặc session-full.out.log vì runner đang chạy tiếp.
- Mẫu job cb3c56daeb984032860e7aeadab7fd58 (32 tên) và full job 39836c390adf4e9993649eacca7a546c (48.641 tên/191 nhóm). Đã xong nhóm 0 của full job trước khi bắt đầu chạy nền toàn bộ còn lại.
- Transport codex_chatgpt_session; auth_mode chatgpt; model_requested gpt-6.1-sol; CLI version, thread ID, SHA artifact, prompt và input hash lưu cùng output/revision. Model là lựa chọn được truyền cho CLI; không gắn nhãn output là Responses API.
- Đã chặn paid API trong CLI cũ và Admin API, kể cả môi trường có khóa. Child process bỏ OPENAI_API_KEY/CODEX_API_KEY/ANTHROPIC_API_KEY/OPENAI_BASE_URL, ignore-user-config, bắt forced_login_method=chatgpt. Không trích xuất token/auth.json.
- Sandbox read-only, schema JSON nghiêm ngặt, workspace tạm ngoài repo, không dùng tool/đọc repo trong prompt phiên âm. Nhóm tối đa 256, chạy tuần tự; tiết kiệm phần context lặp so với nhóm nhỏ.
- ID/chữ Hán/hash nguồn phải khớp toàn nhóm; thiếu/trùng/lạ ID từ chối. Nguồn đổi giữa chạy và nhập → rollback toàn nhóm. Chữ chưa chắc/không Hán → needs_review. Không tự duyệt tên.
- Chỉ ghi bốn bảng codex_*; giữ people/name_vi_map/VNPA/Gemini/TTL/quan hệ/số đời. Không có file TTL local bị sửa.

## Chạy, dừng và tiếp tục

Runner nền được khởi động hidden; PID marker session-full.pid, stdout session-full.out.log, lỗi session-full.err.log. Kết quả từng nhóm tại data/codex_names/23300000000000000000000000000002/group-N, manifest/request/provenance giữ lại. Chạy quota/lỗi → blocked_session, giữ nhóm đã nhập; **không tự chuyển sang API**. Không thể cam kết đủ 48k trong một hạn mức gói.

Chạy từ daoanh:

```powershell
python -B -X utf8 scripts/codex_namevi_session.py status
python -B -X utf8 scripts/codex_namevi_session.py run --folder data/codex_names/23300000000000000000000000000002 --max-groups 0 --timeout 600
```

Không chạy thêm runner cùng job khi process hiện tại còn sống: OS lock chặn chạy đồng thời. Muốn dừng nhẹ khi backend chưa reload:

```powershell
Set-Content -LiteralPath data/codex_names/23300000000000000000000000000002/stop-requested -Value 'Admin pause'
```

Lần resume explicit sẽ bỏ cờ dừng cũ; các request đã ingested được bỏ qua. Nếu phiên âm thiếu/tampered/stale, runner không nhập giả kết quả để tiến độ tăng.

## UI/API và bước còn thiếu

Cột Codex ngay sau DILA name_vi ở hai bảng; full corpus phân trang, tra ID/chữ Hán/tên, giữ cột Gemini. Controls mới: chuẩn bị, chạy/tiếp tục bằng Codex, dừng sau nhóm hiện tại, tải lại. API chỉ chạy job/folder đã quản lý và cần Admin session. Auth subscription được kiểm tra bằng login status, không đọc credentials.

**Main reload chưa thực hiện bởi phiên này:** Start-Process RunAs trả The operation was canceled by the user; không có reload-status ready ngày 05/10. Main PID đã đổi do phiên khác; lần quan sát PID28552 tạo 07:46:05, trước API adaptation. UI fixture PASS không chứng minh backend live đã chuyển transport. Không lặp UAC hoặc kill PID không xác minh được. Sau Admin nạp main, status phải trả transport codex_chatgpt_session và paid_api_enabled=false. Helper scripts/reload-codex-session-main.ps1 có bootstrap/PID/app.py-SHA guard, yêu cầu Administrator. CLI nền không phụ thuộc việc reload này.

## Kiểm tra

Unit26/26: unit.exit0. Pipeline mới: pipeline.exit0; runtime2/2; governance18/18. Compliance exit0 vẫn có 2 metric FAIL (claims_assertion_level, conflicts_resolved); đây là dữ liệu cần giải quyết, không được ghi all data PASS. UI: ui.exit0, 0 pageerrors, Codex names là fixture chỉ trong browser; TTL/tree là dữ liệu thực. Bootstrap/DB source verification xem các log/JSON cùng thư mục.

## Hoàn tác

Backup file-level tại data/backups/T233-codex-session-20261005. **Không restore toàn DB** vì Gemini/session khác có sửa. Guard rollback chung ngày 04/10 hiện sẽ chặn vì Codex đã có dữ liệu; không reseal để lách guard. Hoàn tác gợi ý đúng run:

```powershell
python -B -X utf8 scripts/rollback_codex_session.py --run cb3c56daeb984032860e7aeadab7fd58
# Dry-run PASS; muốn áp mới thêm --apply. Chưa áp lần nào.
```

Script chặn run đang chạy và mọi tên đã thay đổi sau run; giữ revision audit, chỉ xóa/khôi phục đúng codex_person_name của run. Không động dữ liệu nguồn/số đời/Gemini. Run hoàn tác không được resume; tạo job mới nếu cần.

## Việc chưa xong

Toàn corpus **chưa DONE**, đang chạy; kiểm đủ 48.673 ID và tất cả request trước khi đóng T233. Review chất lượng các tên needs_review và chuẩn hóa qua Admin riêng. Nạp backend mới bằng quyền Windows, kiểm actual subscription status và controls. T232 giữ 9 hệ dự kiến; duyệt mốc/identity/truyền pháp và corpus-wide calculation còn tiếp.

[Codex non-interactive documentation](https://developers.openai.com/codex/noninteractive/) hỗ trợ saved auth, JSON schema, output file và read-only sandbox. Phiên dùng hạn mức Codex; không tuyên bố miễn hạn mức.

### Đối soát shared DB và tiến độ bổ sung

Nhóm1 đã nhập thêm256ID, tổng **544/48.673** ở lượt đo kế tiếp; fullrunner đang chạy tiếp. people-diff.json xác nhận chỉ hai name_vi đổi so backup (A001411, A002125), các trường khác giữ nguyên; verifier này chưa quy được writer. VNPA/VNrelations/lineage_edge_assertions/person_gen_computed giữ hash, Gemini24.625 ở lúc đo. Code Codex chỉ ghi bảng riêng; không dùng wholeDB restore. Rollbackfixture3/3 và Dashboard exit0; claude-mem37700 unavailable, observationJSON/error lưu local.

### Snapshot cuối phiên — 08:00 Bangkok 05/10

**800/48.673 ID đã xử lý,47needs_review**, fulljob running_session,3/191 nhóm ingested và188 chưa nhập. delivery-state.json xác nhận0 unknown ID/0 stale input/0 bad session provenance, paid_api_calls0, corpus_donefalse. PID24452 còn chạy. Không hứa hoàn tất trong một hạn mức, không tự chuyển API trả phí.
