# Handoff — T232/T233, 2026-10-04

## 1. Bảng thông tin đọc nhanh

| Mục | Trạng thái và bằng chứng |
|---|---|
| HEAD quan sát |2fdc091 → 7fa546d6975395f4426dc10411426c313facbe11 (phiên khác); không stage/commit trong phiên. Git root là visjs-app |
| T232 |Engine/API/TTL/UI đã triển khai 9 hệ. Unit20/20 và UI thực PASS; các mốc còn dự kiến |
| T233 |Build/UI/API và prepare48.673 ID/1.522 request xong; **0 tên GPT**. Chờ OpenAI API |
| Pipeline |Lượt đầu chờ snapshot DB; đã sửa fixture giữ read transaction. Đọc pipeline-final.exit/log trước review |
| DB |6 bảng additive;5 bảng nguồn hash giữ nguyên. Gemini125→5.125 ngoài phạm vi |
| TTL |Không sửa TTL local/generationOrder. Export mới có proof nháp; chưa xuất lại gói1.037 TTL của T227 |
| Backup |Hai SQLite backup nhất quán, manifest8 file restore/16 code mới, guarded rollback mặc định dry-run |
| Server |Main20728; gateway8080/auth5001 đã chạy. Có late-readiness.json sau probe3s bị timeout |
| Preflight |Kiểm identity/self/cycle/đa đường/RDF trong tests; không chạy ETL hay apply preflight cũ |

## 2. Đọc trong hai phút

[namevimap](http://localhost:8080/daoanh/admin/namevimap.html) có cột Codex sau DILA name_vi trong cả hai bảng, cùng danh sách toàn corpus phân trang. **“—” nghĩa là chưa có kết quả GPT; chưa dịch48.673 tên.** Lô chuẩn bị là616ff1e05ab442819bc166fe6cfafb0d, model API gpt-6.1-sol. Prompt theo quy tắc phiên âm của dự án, không phải model đã fine-tune Phật học.

[Form TTL mẫu](http://localhost:8080/daoanh/admin/monk_ttl_add.html?db_id=A004980) tự tính9 hệ, cho nhập mốc/chứng cứ bằng textbox. [Cây mẫu](http://localhost:8080/daoanh/places?mode=lineage&focus=A004980&lm=tree) có panel phụ. Teacher chung của DILA chưa mặc nhiên là truyền pháp. Nguyên Thiều có nhiều đường khác số nên báo conflict. A000662 chưa được đồng nhất Minh Hải Pháp Bảo Chúc Thánh.

Ba việc Admin cần làm: chọn nguồn OpenAI API và cấu hình credential ngoài chat; kiểm nhóm mẫu trước khi gửi Batch đầy đủ; review định danh Minh Hải và chứng cứ của các mốc trước khi duyệt số đời.

## 3. Vấn đề, cách sửa và kết quả từng task

**T232:** Số đời cũ thiếu quy ước/đường căn cứ. Engine mới dùng registry có revision bất biến, exact DILA ID/tên Hán và hash XML. DFS bằng stack/memo/backpointer cộng1 cho mỗi cạnh trực tiếp. Không chọn đường ngắn nhất để che thầy khác hay số khác. Mốc checkpoint phải nối tới root. Vòng, tự nối, đứt đường và nhiều số khác nhau giữ trạng thái cần kiểm. Giới hạn tài nguyên không trả số chốt một phần.

Hai policy tách biệt: DILA teacher chung chỉ cho candidate; reviewed_transmission dùng cạnh truyền pháp đã duyệt có citation/version/người/ngày. Mốc accepted cần ít nhất3 gốc chứng cứ độc lập cùng rationale. Các website sao cùng tác phẩm không thành3 gốc. Tính độc lập học thuật vẫn cần Admin kiểm, không được suy từ URL.

Chín hệ: Thiền Tông Ca Diếp1; Thiền Tông Thích Ca1; Lâm Tế; Dương Kỳ; Chúc Thánh; Tào Động; Vân Môn; Pháp Nhãn; Quy Ngưỡng.8 hệ có mốc source_asserted, Chúc Thánh thiếu định danh root. Unit20/20 PASS; UI thực không đổi ô số legacy. Chín ID được tính lại cho81 kết quả hệ, xem generation-summary.json và JSONL trong reportT233.

Nguyên ThiềuA044921 cho Lâm Tế29/30/31/34 từ generic teacher, khác sử liệu33. Không chọn34 hay sửa nguồn để ép khớp33. Huệ Năng33/34 là hai quy ước khác nhau. Hưng HóaA004980存獎 là **Tồn Tưởng**, Lâm Tế đời2 dự kiến. [ReportT232](reports/T232-generation-engine-20261004/README.md) chứa nguồn và giới hạn lịch sử.

**T233:** Cột Codex giữ riêng, Gemini vẫn có cột cũ. Full list50 dòng/trang tìm theo ID/Hán/tên Việt. Lookup chia tối đa200 ID để không bỏ sót hơn200 dòng; dùng DOM textContent để tên không thành HTML. Prepare→submit→collect qua API Admin, endpoint cố định, folder giới hạn trong data/codex_names. Hash nguồn và strict JSON kiểm tập ID, chữ Hán, model, stale input, refusal, trùng/thiếu ID. Gợi ý lưu draft/needs_review; nhận lại không tạo revisions trùng.

Unit18/18 PASS. Chuẩn bị48.673 ID/1.522 nhóm32, không bỏ ID; manifest SHA6eeedd2c772f9143d1548ca58788fda05ae99657bf0de4e2d1948ead6c6b0732. **0 tên/0 Batch remote.** Read-only DB contract có auth fixture kiểm status/list/lookup và submit thiếu key409. UI Codex dùng fixture, không chép vào DB. [ReportT233](reports/T233-codex-namevi-20261004/README.md).

**Snapshot fixture:** SQLite backup theo page có thể restart khi DB dùng chung liên tục có writer. Đã xác minh pytestPID4040 thuộc pipelineT233 qua ancestor rồi mới dừng. Không dừng Python của ClaudePID19948. Fixture giữ BEGIN và đọc schema trước backup, không đổi18 assertions hay policy governance, không sửa DB production.

## 4. Cảnh báo bắt buộc — dễ bị bỏ sót

- **Không restore toàn lineage.db để revert:** kho Gemini125→5.125 có dữ liệu mới trong phiên song song. Công cụ chỉ xử lý6 bảng mới. “Năm bảng nguồn giữ nguyên” không có nghĩa toàn DB bất biến.
- Không gán A000662明海/X0613 thành Minh Hải Pháp Bảo chỉ vì trùng tên. TS-Minh-Hai-Phap-Bao.ttl còn nhãn Nguyên Thiều/tiểu sử rỗng/71; giữ nguyên cho audit identity riêng.
- Không dùng shortest path để chốt số khi DILA có nhiều thầy. Seed không có mốc accepted; đời khai tổ1 là quy ước công bố trong từng nhánh.
- TTL không Git track; raw XML và TTL nguồn không sửa. Gói1.037 TTL đã xuất của T227 chưa được xuất lại với generation proof.
- Shared HEAD có thể đổi. Không broad git add, không git init trong daoanh hay track nested repos. Git chỉ chạy từ visjs-app.
- File protected có thể báo EPERM/reparse hoặc copy no-op. Luôn checksum trước/sau. Main probe3s timeout dù response200; late-readiness kiểm thật, helper tương lai tăng20s.
- Không đưa API key vào chat/log. Lượt GPT trả phí chưa gửi; không dùng hạn mức chat như credential Batch API.

## 5. Lệnh hoàn tác và bảng mất dữ liệu

Chạy tại daoanh:

```powershell
python -B -X utf8 scripts/rollback-name-generation.py
# Chỉ khi guard PASS, đã dừng main/jobs mới và quyết hoàn tác:
python -B -X utf8 scripts/rollback-name-generation.py --apply
```

| Phần | Mất dữ liệu? |
|---|---|
|Restore8 file, gỡ16 code mới nếu hash đúng |Gỡ tính năng mới; dữ liệu nguồn không mất |
|Drop2 bảng generation đúng fingerprint |Mất9 seed revisions;0 calculation lúc seal |
|Drop4 bảng Codex đúng fingerprint |Mất2 jobs/1.522 request metadata;0 names/revisions lúc seal; JSONL vẫn giữ |
|people/VNPA/quan hệ/computed/Gemini/TTL |Không restore/update/drop;0 |

Nếu Admin đã thêm tên/mốc/job mới thì fingerprint thay đổi và script chặn. **Không reseal để lách guard.** Báo cáo, backups và JSONL luôn được giữ. Helper mới được dry-run, chưa apply. Snapshot toàn DB chỉ dùng trong kế hoạch phục hồi riêng, không dùng để revert hai task trong DB dùng chung. Sau hoàn tác khởi động main và chạy pipeline.

## 6. File tạo/sửa

| Phần | Files |
|---|---|
|Generation core mới |src_python/generation_engine_v2.py; api_generation_v2.py |
|Codex core mới |src_python/codex_namevi.py; api_codex_namevi.py; scripts/codex_namevi_batch.py |
|UI mới |admin/generation-ui-v2.js; admin/places-generation-v2.js; admin/codex-namevi.js/.css |
|UI/API/export sửa |admin/namevimap.html; admin/monk_ttl_add.html; admin/ttl-profile-v2.js; places.html; api_ttl_profile_v2.py; src_python/ttl_db_export.py |
|Tests/ops |tests/test_t232_generation_engine.py; tests/test_t233_codex_namevi.py; scripts/test-name-generation-ui.cjs; scripts/install_generation_v2.py; scripts/compute_generations_v2.py; scripts/t232_inspect.py; scripts/reload-name-generation-main.ps1; scripts/rollback-name-generation.py; package.json; tests/test_b25_authority_contract.py (snapshot only) |
|Docs |tasksT232/T233, tasktodo, ROLLBACK, hai reports, session và Handoff này |
|Generated |Dashboard/progress; pipeline UAT/compliance/runtime outputs; prepared JSONL/manifest; backup/rollback manifest |

app.py/local_gateway.py/server.py chỉ đọc/chạy, không sửa trong phiên. Không coi WIP của phiên khác là thay đổi của mình.

## 7. Sai lầm đã gặp, cách sửa và điều bác bỏ

Copy bước trước chưa kiểm hash sau ghi khiến UI chưa có script: đã sửa bằng checksum và kiểm trên trang thực. Prepare đầu lỗi SQL coalesce/encoding: giữ failed job, sửa rồi tạo lô mới. Verifier dùng tên bảng sai và snapshot AI trước khi bảng tồn tại: sửa đúng bảng và baselinepre-T233, báo rõ Gemini thay đổi. UI test thiếu chữ “Tông” trong label: sửa kỳ vọng, không sửa product chỉ để pass. Probe main3s quá ngắn: ghi late-ready, sửa timeout. Memo copy toàn path có nguy cơ RAM: chuyển backpointer và bound witness.

Đã bác bỏ các kết luận: A000662 tự sameAs Minh Hải; mọi DILA teacher đều truyền pháp; shortest path tự chọn đời; GPT đã fine-tune Phật học;48.673 tên đã dịch; toàn DB bất biến. Không lặp lại các kết luận đó.

## 8. Chưa xong, theo thứ tự ưu tiên

1. OpenAI API/model access chưa có; câu hỏi nguồn truy cập chưa được trả lời. Khi có: sample cùng prompt/model→kiểm chất lượng→Batch full→collect→đối soát đủ ID/errors→retry phần thiếu.
2. Chúc Thánh cần định danh Minh Hải Pháp Bảo đúng và chứng cứ gốc; không dùng A000662 mặc định.
3. Duyệt mốc với3 gốc độc lập; phân biệt xuất gia/tham học/truyền pháp, giải thích conflict Nguyên Thiều trước chốt33.
4. Tính toàn DB/TTL corpus sau registry review. Phiên này chỉ tính9 người mẫu, không báo toàn corpus đã xong.
5. Quyền artifact/crosswalk/semantic adapters và audit TTL legacy tiếp tục theoT226/T230/T215; không gộp thành “DONE9/9” cũ.

## 9. Lệnh kiểm tra nhanh

```powershell
$env:PYTHONPATH='data/backups/T226-ttl-profile-20261003/python-deps;data/backups/T215-fix-sync-20261002/python-deps'
python -B -X utf8 scripts/codex_namevi_batch.py status
python -B -X utf8 tests/test_t232_generation_engine.py
python -B -X utf8 tests/test_t233_codex_namevi.py
python -B -X utf8 scripts/rollback-name-generation.py
```

Mở ba URL ở mục2, đọc ui-result.json và pipeline-final.exit/log. Full fingerprint DB mất vài phút, không thuộc kiểm nhanh. Remote OpenAI chưa test vì thiếu key. Các lệnh đã chạy có bootstrap, installer dry-run/apply, extension4 schemes, Codex install/prepare, unit, pipeline, Playwright, fingerprint, rollback dry-run, PID ancestry, reload và build Dashboard/save observation.

## 10. Ghi chú cho agent kế tiếp

Đọc tasktodo/Handoff/log exit trước, lấy HEAD mới từ repo root. Kiểm Codex status0/48.673 và jobprepared; không in key. Đổi prompt/version phải prepare lô mới, không sửa manifest cũ. Model khác cần Admin chọn, không gán tên Gemini vào Codex. Collect chỉ tạo gợi ý; Admin vẫn phải duyệt. Mốc phải exact alias/hash hiện tại và expected_revisionCAS; review đường, hệ đếm và chứng cứ trước accepted. Giữ dữ liệu Gemini của phiên song song; không broad restore DB. Sau đổi code phải chạy pipeline, cập nhật tasktodo/Dashboard, Handoff theo convention và observation.

## Kết quả bổ sung cần giữ khi chốt

UI cuối ui-final-retry.exit=0, zero pageerrors; stylesheet đã xem ảnh thực. Lượt UI30s timeout khi chạy song song, timeout60s đã qua; không có cam kết hồ sơ lớn luôn tải nhanh. Rollback cuối dry-run exit0, khóa danh sách8 file restore/16 code mới/6 bảng; chưa apply. Năm bảng nguồn giữ nguyên, ai_person_name thay đổi được báo riêng trong db-verification.json. Compliance sinh9 metrics:7 pass,2 fail (claims_assertion_level và conflicts_resolved); đây là chỉ số dữ liệu còn tồn tại, không được gọi là đã giải quyết chỉ vì pipeline exit0. Main source vẫn khớp hash bootstrap tại lúc kiểm cuối.
