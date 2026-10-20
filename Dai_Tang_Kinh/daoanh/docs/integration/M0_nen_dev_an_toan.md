> Spec cho phiên Claude Code. Chỉ mô tả yêu cầu, không chứa mã. Đọc cùng CLAUDE.md. Tick `[ ]` khi đạt từng tiêu chí.

Spec M0 · P0

# M0 Nền dev và an toàn

Dọn nền trước khi tích hợp: bí mật, số liệu thật, cấu trúc Claude Code và rào chắn cho các lệnh nguy hiểm.

[Quay lại Plan Overview](00_PLAN_OVERVIEW.md)

## Mục đích

Phiên Claude Code mở đầu phải có một nền sạch và đáng tin: không lộ key, biết số liệu thật của DB, đọc đúng hướng dẫn dự án và bị chặn khi định chạy lệnh nguy hiểm. Module này không thêm tính năng cho người dùng cuối.

## UI/UX

Không có giao diện. Đầu ra là tệp và cấu hình trong thư mục `daoanh/`.

| Tệp                                 | Vai trò                                                                                                                                                           |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `CLAUDE.md`                         | Ngắn (dưới 200 dòng): cổng server, đường dẫn DB, điều cấm, quy tắc ZQ, bước kiểm xong. Nhập thêm `@AGENTS.md` vì Claude Code bỏ qua AGENTS.md khi đã có CLAUDE.md |
| `.claude/rules/*.md`                | Quy tắc theo vùng, dùng khóa `paths`: adapters và gate, script ETL, thay đổi DB                                                                                   |
| `.claude/settings.json`             | Quyền cho phép, hỏi, cấm. Cấm `git add/commit/reset`. Hỏi trước khi deploy VPS hoặc đổi schema                                                                    |
| Hook `PreToolUse`                   | Chặn cứng git ghi và đường dẫn nhạy cảm (thoát mã 2). Viết cho Windows, không giả định bash                                                                       |
| `.claude/skills/onboard-source/`    | Quy trình thêm nguồn thứ 26 trở đi, chỉ gọi tay (không tự kích hoạt)                                                                                              |
| `.claude/agents/source-reviewer.md` | Subagent chỉ đọc: kiểm pháp lý và provenance trước khi hoàn tất một module                                                                                        |
| `docs/integration/`                 | Bản đăng ký 25 nguồn, ma trận giấy phép, quyết định đang chờ, nhật ký thay đổi                                                                                    |

## Dữ liệu

- Hai truy vấn chỉ đọc cần chạy đầu tiên: danh sách `data_sources` nối `source_authority` (source_id, source_code, legal_status, integration_mode, license_verified, implemented) và số claims theo `source_id` trong `entity_claims`.
- Đo lại: kích thước DB, số bảng, số route `@app.route` trong `app.py`. Ghi kết quả vào `docs/integration/REALITY_CHECK.md`.
- Hiện tài liệu ghi 664 MB, 67 bảng, 131+ route. Research đo thấy khoảng 1,5 GB và 311 route, chưa đo trực tiếp số bảng.

## Logic

- **Bí mật:** key Gemini nằm cứng trong `app.py` (khoảng dòng 10690 và 18580 theo research, CLAUDE.md ghi dòng 1065 và 1105 nên số dòng cần kiểm lại) và xuất hiện trong `docs/conventions.md`, `docs/pipelines.md`. Việc cần làm: user xoay key, chuyển sang biến môi trường, xóa khỏi tài liệu. Không chép key vào bất cứ đâu.
- **Git:** thư mục có `.git.disabled-20260917` và CLAUDE.md nói index bất thường. Phiên dev phải kiểm trạng thái git thật rồi mới viết rào chắn. Không tự khôi phục.
- **Rào chắn nhiều lớp:** CLAUDE.md chỉ là lời nhắc, quyền `deny` khớp theo chữ lệnh nên có thể bị lách (`git -C . push`, đường dẫn tuyệt đối), hook mới là lớp cứng nhất trong dự án. Dùng cả ba.
- **Nơi khởi chạy:** `.claude/settings.json` chỉ đọc từ thư mục khởi chạy, không kế thừa từ thư mục cha. Repo gốc là `visjs-app` cách hai cấp, nên luôn khởi chạy trong `daoanh/`.
- **Tài liệu mâu thuẫn:** không sửa hàng loạt. Tạo bảng đối chiếu và để user duyệt từng mục (số nguồn 13/14/20/25, giấy phép 84000, trạng thái DILA).
- Giữ nguyên toàn bộ tính năng đã chạy. Chỉ thêm tệp, không đổi hành vi app.

## Acceptance criteria

- [ ] Không còn chuỗi key nào trong `app.py`, `docs/`, `scripts/` (tìm theo mẫu, báo số lượng, không in giá trị).
- [ ] App khởi động bình thường với key đọc từ biến môi trường, thiếu key thì báo lỗi rõ.
- [ ] `REALITY_CHECK.md` có số liệu đo thật cho nguồn, claims, kích thước DB, số bảng, số route.
- [ ] CLAUDE.md dưới 200 dòng, nhập AGENTS.md, vẫn giữ mọi quy tắc cũ (ZQ source_id=5, backup, quyền, VPS).
- [ ] Thử gõ lệnh `git add .` trong phiên mới: bị chặn bởi hook, có thông báo nói rõ lý do.
- [ ] Có ít nhất một rule theo `paths` cho `adapters/**` và `gate/**`.
- [ ] Subagent `source-reviewer` chạy được và chỉ có quyền đọc.
- [ ] Danh sách mâu thuẫn tài liệu có người duyệt, chưa tự sửa.

## Việc cần user quyết

- Xoay key Gemini (chỉ user làm được).
- Có bật lại git hay giữ trạng thái disabled.
