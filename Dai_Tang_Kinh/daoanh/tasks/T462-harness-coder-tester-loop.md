---
id: T462
title: "Harness: OpenCode GO code, OpenRouter test, vòng lặp debug đến DONE"
status: in_progress
owner: coordinator
module: Harness / Điều phối
created: 2026-10-25
updated: 2026-10-25
depends_on: []
former_ids: []
done_when: >
  Quy trình phân vai và vòng lặp test-debug được ghi lại và Admin xác nhận; opencode gọi được model coder rẻ nhất (mimo-v2.5) hoặc chuỗi fallback khi GO còn quota;
  tester OpenRouter gọi được model :free khác model coder; Dashboard hiển thị T462 và T445/T463.
---

## Mô tả

Ghi lại quy trình harness để mọi agent làm theo: Claude Code điều phối và viết tiêu chí DONE, OpenCode code, OpenRouter test, daoanh-debugger sửa bug, lặp đến khi test PASS và Admin xác nhận. Kèm chuỗi model ưu tiên và các ràng buộc không ghi DB, không commit khi chưa được Admin duyệt. Task này cũng là lần đầu áp dụng quy trình cho T445/T463.

# T462 — Quy trình harness: code, test, debug đến DONE

## Mục tiêu

Admin đã phê chuẩn quy trình phân vai và vòng lặp test-debug. Task này ghi lại quy trình
để mọi agent và session sau đều làm theo cùng một cách, và dùng nó cho T445.

## Phân vai

| Vai | Ai | Việc | Không làm |
|---|---|---|---|
| MA (Claude Code) | Claude Code | Phân công, tạo task, tiêu chí DONE, nội dung test; nhận bug từ tester và gọi `daoanh-debugger` sửa; chuyển lại cho tester test; kiểm chứng cuối | Không code thay coder, không tự test thay tester |
| Coder | OpenCode GO (`opencode`) | Code theo task do MA giao | Không tự đánh DONE, không sửa test |
| Tester | OpenRouter (`openrouter`) | Test theo nội dung test do MA viết; bug → báo MA | Không sửa code |
| Debugger | `daoanh-debugger` (do MA gọi) | Sửa bug MA chuyển | — |
| Coder | `opencode` (OpenCode GO) | Code theo tiêu chí DONE của task, báo DONE | Không tự đánh DONE, không sửa test |
| Tester | `openrouter` | Chạy test theo nội dung QA viết, báo bug | Không sửa code |
| Debugger | `daoanh-debugger` (Claude) | Sửa bug do tester phát hiện | — |
| Xác minh cuối | Admin | Verify sau khi tester báo DONE | — |

## Chuỗi model (ưu tiên theo thứ tự)

**Coder:**
1. OpenCode GO model rẻ nhất: `mimo-v2.5` (theo tài liệu chính thức, nhiều request nhất trên cùng ngân sách).
2. Khi GO hết quota: OpenCode model free còn quota (id `-free`, ví dụ `big-pickle`, `beam-free`).
3. Khi cả hai hết quota: OpenRouter FREE `nvidia/nemotron-3-ultra-550b-a55b:free`.

**Tester:** OpenRouter FREE `nvidia/nemotron-3.5-lightning:free`. Phải khác model coder dùng ở bước 3 để kết quả trung lập.

**Quy tắc chung:** mọi model OpenRouter phải là bản `:free`. Model không có bản free thì không dùng.

## Vòng lặp đến DONE

1. Claude Code viết task `T<id>` với tiêu chí DONE và nội dung test.
2. Coder code theo task, báo DONE.
3. Tester chạy test theo nội dung QA. Nếu lỗi, báo bug cho Claude Code.
4. Claude Code gọi `daoanh-debugger` sửa bug.
5. Quay lại bước 3: tester test lại 1 lần. Lỗi tiếp thì lặp lại bước 4.
6. Khi test pass, tester báo DONE cho Admin. Admin verify lần cuối.

## Ràng buộc

- Không commit khi chưa có duyệt của Admin.
- Không thao tác ghi DB; mọi thay đổi DB cần dry-run, Admin duyệt, rồi `--apply`.
- Sao lưu `data/lineage.db` và ghi đường dẫn vào `docs/ROLLBACK.md` nếu có thay đổi DB.
- Key nằm trong `Dai_Tang_Kinh/.env`, không ghi trong agent file hay chat.

## Tiêu chí DONE cho quy trình này

- [x] Định nghĩa agent `opencode` và `openrouter` đã ghi vai trò và chuỗi model.
- [x] Quy tắc chuỗi model và vòng lặp đã lưu vào memory.
- [x] Kiểm tra gọi được: OpenRouter `nvidia/nemotron-3.5-lightning:free` HTTP 200; `nvidia/nemotron-3-ultra-550b-a55b:free` HTTP 200.
- [ ] `opencode` gọi được với model rẻ nhất khi GO còn quota. Hiện GO báo hết quota tuần (429).
- [x] Dashboard hiển thị T462 và T445 (kiểm trên `http://127.0.0.1:8080/dashboard/dashboard_process.html`, snapshot 2026-10-25T13:12:50).
- [ ] Admin xác nhận quy trình.

## Ghi chú hiện trạng (2026-10-25)

- OpenCode GO: hết quota tuần. `mimo-v2.5` báo 429.
- OpenCode free: hết quota (`FreeUsageLimitError`).
- OpenRouter FREE: hoạt động.
- Định nghĩa agent `openrouter` và `opencode` trong phiên hiện tại vẫn có thể cache ID cũ. Cần phiên mới để nạp đúng.

## Liên quan

- T445 (Wizard UI placevn): task đầu tiên chạy theo quy trình này. Spec: `tasks/T445-placevn-wizard-ui-b0-b9.md`. WIP chưa commit ở `admin/placevn.html` và `app.py`, không revert về HEAD.
- Memory: `feedback_model_routing`, `feedback_harness_roles_loop`.
