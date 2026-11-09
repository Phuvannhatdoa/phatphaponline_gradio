# Quy trình làm việc Đạo Ảnh qua harness

> Tài liệu này là quy trình chuẩn cho Claude Code khi làm việc trong dự án Đạo Ảnh.
> Tên gọi: **phát triển theo đặc tả có cổng duyệt của người** (spec-driven development with human-in-the-loop).
> Claude điều phối. Agent thực hiện. Agent QA kiểm chứng độc lập. Admin quyết định ở các cổng.

## 0. Nguyên tắc cốt lõi

1. **Claude không tự làm hết trong luồng chính.** Claude lập kế hoạch, giao việc, theo dõi, và báo cáo.
2. **Người quyết định ở các cổng.** Cổng là điểm mà việc không được đi tiếp nếu chưa có duyệt rõ ràng.
3. **Kiểm chứng độc lập.** Người sửa không tự xác nhận kết quả của mình. `daoanh-qa` làm việc đó.
4. **Ghi lại mọi thứ.** Quyết định, backup, và lý do đều nằm trong file, không chỉ trong chat.
5. **An toàn trước.** Mọi việc ghi DB, đổi schema, deploy VPS, git, hoặc tốn chi phí đều cần duyệt riêng.
6. **Không hạ tiêu chuẩn để cho xanh.** Nếu điều kiện nghiệm thu chưa đạt thì task vẫn mở.

## 1. Vai trò

| Vai trò | Ai | Làm gì | Không được làm |
|---|---|---|---|
| Admin | Người dùng | Duyệt đề xuất, quyết định nghiệp vụ, xác nhận DONE | — |
| Điều phối | Claude (luồng chính) | Lập kế hoạch, giao agent, theo dõi, báo cáo, cập nhật tài liệu | Tự sửa code hàng loạt, tự xác nhận QA |
| Sửa | `daoanh-debugger` | Sửa code/tài liệu theo phạm vi đã duyệt | Ghi DB ngoài phạm vi, đổi nghiệp vụ, đánh DONE |
| Tích hợp | `tich-hop` | Nghiên cứu và tích hợp nguồn dữ liệu mới | Ghi DB khi chưa có duyệt |
| Kiểm chứng | `daoanh-qa` | Chạy lệnh, so bằng chứng với tiêu chí, báo ĐẠT/CHƯA ĐẠT | Sửa file, ghi DB |
| Tìm kiếm | `Explore` | Đọc, liệt kê, đối chiếu | Sửa file |

## 2. Các giai đoạn

```
Ý tưởng → Đề xuất → [Cổng 1: Admin duyệt] → Task file → Sao lưu
        → Thực hiện (agent) → Kiểm chứng (QA) → [Cổng 2: Admin xác nhận DONE]
        → Cập nhật tài liệu & dashboard
```

### Giai đoạn 1 — Ý tưởng

Admin mô tả việc cần làm bằng tiếng Việt, ngắn gọn. Claude không bắt đầu sửa gì.

### Giai đoạn 2 — Đề xuất

Claude viết một đề xuất ngắn gọn gồm:
- **Vấn đề:** hiện trạng, số liệu đo được (có lệnh chạy hoặc nguồn).
- **Mục tiêu:** điều kiện nghiệm thu rõ ràng, có thể kiểm bằng lệnh.
- **Phương án:** các lựa chọn, ưu nhược, và khuyến nghị.
- **Phạm vi:** file nào, bảng nào, route nào sẽ bị ảnh hưởng.
- **Rủi ro và hoàn tác:** cách quay lại.
- **Câu hỏi cho Admin:** những quyết định chỉ Admin được đưa ra.

Nếu việc có thể đọc được trước khi đề xuất (chỉ đọc), Claude làm trước để đề xuất dựa trên số liệu thật.

### Giai đoạn 3 — Cổng 1: Admin duyệt

Admin trả lời một trong các câu:
- "duyệt" / "ok" / "đồng ý": được làm đúng phương án đã trình bày.
- "duyệt lô X theo hướng Y": chỉ làm phần đó.
- "không duyệt" hoặc "chọn phương án Z": quay lại giai đoạn 2.

**Duyệt là theo từng việc, không tổng quát.** Duyệt một lô không có nghĩa là duyệt lô sau. Duyệt việc đọc không có nghĩa là duyệt việc ghi.

Một câu duyệt không tự động cho phép việc ghi DB, đổi schema, deploy hay git. Những việc đó luôn hỏi lại nếu chưa được nêu rõ.

### Giai đoạn 4 — Task file

Mỗi việc được duyệt có một file trong `tasks/T<số>-<slug>.md`. Số task lấy số lớn nhất hiện có cộng 1, kiểm tra trùng với cả thư mục và tiền tố `T<số>` trong tài liệu.

Frontmatter tối thiểu:

```yaml
---
id: T<số>
title: "<tên ngắn>"
status: in_progress        # pending | in_progress | blocked | done
created: YYYY-MM-DD
updated: YYYY-MM-DD
owner: <người hoặc agent>
parent: T<số>             # nếu là task con
plan_approved_at: "<ngày> (<Admin duyệt cái gì>)"
done_when: >
  <điều kiện nghiệm thu bằng lệnh hoặc bằng chứng cụ thể>
revert: >
  <cách hoàn tác>
outcome: >
  <kết quả từng bước, cập nhật khi xong>
---
```

Thân file có mục **Các bước** dạng checklist `- [ ]` / `- [x]`. Dashboard đọc các checklist này để hiển thị tiến độ, nên không đổi định dạng.

### Giai đoạn 5 — Sao lưu

Trước mọi lần sửa file, copy vào `docs/sessions/YYYY-MM-DD/` với tên `*.bak-before-<tag>`.

Trước mọi lần ghi DB:
- Sao lưu DB bằng cơ chế sao lưu nhất quán (sqlite backup), không copy file thô khi DB đang mở.
- Kiểm tra toàn vẹn bản sao (`PRAGMA quick_check`). Với DB lớn, lệnh này có thể mất vài phút, nên chạy nền.
- Ghi đường dẫn bản sao vào task file và `docs/ROLLBACK.md`.

### Giai đoạn 6 — Thực hiện (agent)

Claude giao cho agent đúng vai, với một prompt tự đủ thông tin. Prompt phải có:
- Thư mục làm việc và đường dẫn file task.
- Phạm vi: được làm gì, không được làm gì.
- Ràng buộc: sao lưu trước, không ghi DB nếu chưa được duyệt, không git, không deploy VPS, không xóa file.
- Định dạng báo cáo.

Agent không được tự đánh dấu DONE và không được báo ĐẠT. Agent chỉ báo việc đã làm, file đã đổi, và lệnh đã chạy.

Nếu spec không đủ rõ hoặc việc cần ghi DB mà chưa được duyệt, agent phải **dừng và hỏi**, không tự đoán.

### Giai đoạn 7 — Kiểm chứng (QA)

Claude giao `daoanh-qa` kiểm tra. QA:
- Chạy lệnh thật, không suy đoán. Mỗi kết luận ĐẠT phải có bằng chứng (lệnh và output rút gọn).
- Đối chiếu với `done_when` của task.
- Kiểm tra số liệu DB trước và sau bằng SELECT.
- Trả về một trong ba kết luận: ĐẠT, CHƯA ĐẠT, KHÔNG KIỂM ĐƯỢC.

Nếu CHƯA ĐẠT, Claude giao lại cho agent sửa với lỗi cụ thể. Tối đa hai vòng. Quá hai vòng thì dừng và báo Admin.

### Giai đoạn 8 — Cổng 2: Admin xác nhận DONE

Claude báo cho Admin: việc đã làm gì, bằng chứng QA, phần chưa làm, và câu hỏi nếu có. Claude hỏi rõ: "Admin xác nhận task này DONE chưa?"

Chỉ sau khi Admin xác nhận, trạng thái mới được đổi thành `done`.

Nếu `done_when` chưa đạt (ví dụ lệnh kiểm tra vẫn đỏ), **không được đóng**, dù việc con đã xong. Việc con được ghi là đã xong, task cha vẫn mở.

### Giai đoạn 9 — Cập nhật tài liệu và dashboard

Sau mỗi bước được xác nhận:
- Cập nhật checklist trong task file và `outcome`.
- Cập nhật `docs/tasktodo.md` (block của task, giữa các marker `<!-- Txx:START -->` và `<!-- Txx:END -->`).
- Thêm dòng vào `docs/ROLLBACK.md` có đường dẫn sao lưu và cách hoàn tác.
- Ghi `docs/sessions/YYYY-MM-DD_<task>.md`.
- Chạy lại `scripts/build_t263_status.py` (cho panel T263/T265) và `scripts/build_progress_data.py`.

## 3. Các cổng cần Admin quyết định

Những việc sau luôn cần duyệt riêng, không được suy ra từ câu duyệt chung:

| Việc | Vì sao |
|---|---|
| Ghi DB (INSERT/UPDATE/DELETE) | Có thể mất dữ liệu, cần sao lưu và duyệt |
| Đổi schema (CREATE/ALTER/DROP) | Ảnh hưởng toàn hệ thống |
| Deploy lên VPS | Ảnh hưởng người dùng thật |
| Git commit/push/reset | Repo có index bất thường, xem CLAUDE.md |
| Xóa file hoặc dữ liệu lớn | Không hoàn tác được |
| Tốn chi phí (LLM, API trả phí, batch dịch) | Ảnh hưởng ngân sách |
| Gửi dữ liệu ra dịch vụ bên ngoài | Quyền riêng tư và bản quyền |
| Quyết định nghiệp vụ (gộp/tách, soft/hard delete, nội dung dịch) | Chỉ Admin quyết |
| Đóng task (DONE) | Chỉ Admin xác nhận |

## 4. Mẫu prompt giao agent

```
Thư mục làm việc: <đường dẫn>
File task: <đường dẫn>

Việc: <một câu mô tả>

Phạm vi được làm: <file, route, bảng>
Không được làm: <ghi DB, git, deploy, xóa file, đổi nghiệp vụ>

Trước khi sửa: sao lưu vào docs/sessions/<ngày>/ với tên *.bak-before-<tag>.
Nếu spec không rõ hoặc cần ghi DB chưa được duyệt: dừng và báo câu hỏi cụ thể.

Báo cáo bằng tiếng Việt: file đã đổi (kèm backup), lệnh đã chạy và kết quả, phần chưa làm, câu hỏi.
Không báo ĐẠT. Việc đó do daoanh-qa làm.
```

## 5. Mẫu báo cáo QA

```
## QA: <task>

Kết luận: ĐẠT / CHƯA ĐẠT / KHÔNG KIỂM ĐƯỢC

| Hạng mục | Kết quả | Bằng chứng (lệnh + output rút gọn) |
|---|---|---|
| ... | ... | ... |

Lỗi cần sửa: (file:dòng)
Chưa kiểm tra: (nêu rõ)
```

## 6. Mẫu đề xuất gửi Admin

```
## Đề xuất: <tên>

Vấn đề: <hiện trạng + số liệu đo được>
Mục tiêu nghiệm thu: <lệnh hoặc bằng chứng>
Phương án:
  (a) ...  ưu: ...  nhược: ...
  (b) ...  ưu: ...  nhược: ...
Khuyến nghị: <chọn gì và vì sao>
Phạm vi: <file, bảng, route>
Rủi ro và hoàn tác: <cách quay lại>
Cần Admin quyết: <câu hỏi cụ thể>
```

## 7. Ví dụ đã làm: T263 → T265

- **Vấn đề:** 285 dòng năm không khớp niên hiệu, nhưng kiểm tra cũ vẫn đỏ/xanh lặng.
- **Đề xuất:** bảng quyết định bổ sung, duyệt theo lô B/C/A.
- **Cổng 1:** Admin phê chuẩn, chọn "review" cho lô C, duyệt lô A.
- **Thực hiện:** sao lưu DB hai lần, tạo bảng bổ sung, ghi quyết định theo transaction.
- **QA:** `daoanh-qa` xác nhận ĐẠT cho lô A và thay đổi audit.
- **Trạng thái:** 7/10 bước xong. Chưa đóng vì `--strict` vẫn đỏ (đúng kỳ vọng).

## 8. Điều không được làm

- Không tự đánh dấu DONE.
- Không đổi điều kiện `done_when` để cho task đạt.
- Không ghi DB chỉ vì một câu duyệt chung chung.
- Không dùng git nếu chưa có lệnh rõ ràng.
- Không để agent tự xác nhận QA của chính nó.
- Không bỏ qua sao lưu với lý do "thay đổi nhỏ".
- Không tự suy nghiệp vụ khi spec không rõ. Hỏi Admin.

## 9. Tóm tắt một dòng

**Đề xuất → Admin duyệt → Sao lưu → Agent làm → QA kiểm chứng → Admin xác nhận DONE.**

## Cập nhật 2026-10-20 — Hermes theo lịch đã huỷ

Admin: *"hủy lệnh gọi Hermes theo lịch, admin trực tiếp giao từng việc"*. Hermes (và agent khác) chỉ làm task khi Admin giao trực tiếp, nêu rõ T-id. `dispatch: approved` = Admin đã duyệt kế hoạch, KHÔNG tự động nhận việc. Chi tiết: `docs/process/HERMES_DISPATCH_PROMPT.md` (đầu file).
