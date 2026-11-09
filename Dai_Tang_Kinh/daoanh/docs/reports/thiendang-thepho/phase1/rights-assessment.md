# T429 — Giai đoạn 1: Đánh giá quyền (rights-assessment)

TASK: T429 · PHASE: 1 (rights-assessment) · DATE: 2026-10-21 · STATUS: DONE (phạm vi GĐ1)

## 1. Nguồn đóng băng

| Mục | Giá trị (đo thật 2026-10-21) |
|---|---|
| File | `data/cbeta/xml-p5-full/X/X86/X86n1601.xml` (bản sao local có sẵn trong repo, **không tải mới**) |
| Kích thước | 803.957 byte |
| mtime | 2026-09-27T19:34:02+07:00 |
| SHA-256 | `0020c4847b8107260e8674233d7833fd590cccafba2210d0ac479edd88ff75eb` |
| Tái tính khớp | PASS — chạy lại `scripts/thiendang_thepho/freeze_source.py` 2 lần, hash nguồn giống hệt; `SHA256SUMS.txt` verify 3/3 PASS |

## 2. Xác nhận từ header thật (trích verbatim `research/thiendang-thepho/manifests/source-header.xml`)

| Kỳ vọng (done_when) | Bằng chứng trong header | Verdict |
|---|---|---|
| Tên tác phẩm 禪燈世譜 | `<title level="m" xml:lang="zh-Hant">禪燈世譜</title>` + `<title>…No. 1601 禪燈世譜</title>` | **PASS** |
| CBETA X86n1601 | `<idno type="canon">X</idno>.<idno type="vol">86</idno>.<idno type="no">1601</idno>` | **PASS** |
| 9 quyển | `<extent>9卷</extent>` + 9 `milestone unit="juan"` n=1…9 | **PASS** |
| Tác giả | `<author>明 道忞編修　吳侗集</author>` (Minh — Đạo Mẫn biên tu, Ngô Động tập) | PASS |
| Bộ | 卍新纂大日本續藏經 (Manji Shinsan Dainihon Zokuzōkyō) | PASS |
| Ngày phiên bản XML | `<date>2025-08-28 16:43:44 +0800</date>` | PASS |

## 3. Điều khoản quyền (trích nguyên văn)

```xml
<availability>
  <p>Available for non-commercial use when distributed with this header intact.</p>
</availability>
```

- **Điều kiện:** (a) chỉ dùng **phi thương mại**; (b) khi phân phối phải **kèm nguyên header**.
- Header đã được trích verbatim và hash (`a8e08889d080b3bf…`) — mọi gói bàn giao/preview của T429
  phải kèm file `source-header.xml` này (hoặc trích header nguyên vẹn kèm hash tham chiếu).

## 4. Hệ quả cho PTDA

| Câu hỏi | Trả lời hiện tại | Cần Admin quyết |
|---|---|---|
| PTDA có dùng thương mại không? | **Chưa xác định được từ code/docs** — app.py không ghi nhận mô hình thương mại; nhưng không loại trừ | ⚠ **Bắt buộc quyết trước GĐ3**: nếu PTDA phát hành/dịch vụ trả phí có chứa trích văn của nguồn này thì vi phạm điều khoản — khi đó chỉ được dùng nội bộ nghiên cứu, không phát hành trích văn |
| Trích fragment mẫu trong research/ có được không? | Có — dùng nội bộ nghiên cứu, kèm header, không phát hành | — |
| `data_sources` ghi license chung "CC BY-SA 4.0" cho CBETA | **Không phản ánh điều khoản riêng của X-series** (per-text availability). Khi đăng ký nguồn `CBETA_X1601` (GĐ3+) phải ghi đúng điều khoản per-text này | Ghi vào task tích hợp sau |
| Quyền của script/schema do agent tạo | Không áp license của nguồn cho file dẫn xuất do PTDA tự viết; nhưng **dữ liệu trích** vẫn chịu điều khoản nguồn | — |

## 5. Giới hạn của đánh giá này

- Đây là **đánh giá kỹ thuật dựa trên văn bản header**, không phải tư vấn pháp lý.
- Không tự áp kết luận license cho script/XSD do bên thứ ba tạo (theo cảnh báo QA 2026-10-21).
- Quyền từng artifact bàn giao phải duyệt riêng khi xuất (GĐ8+).

## 6. File GĐ1 đã tạo

| File | SHA-256 |
|---|---|
| `research/thiendang-thepho/manifests/source-manifest.json` | `d0605e420264d5d3…` (đủ trong SHA256SUMS.txt) |
| `research/thiendang-thepho/manifests/source-header.xml` | `a8e08889d080b3bf…` |
| `research/thiendang-thepho/manifests/SHA256SUMS.txt` | (danh sách 3 hash, verify PASS) |
| `scripts/thiendang_thepho/freeze_source.py` | script tái lập (idempotent — đã chạy 2 lần, nội dung manifest trừ timestamp giống hệt) |
