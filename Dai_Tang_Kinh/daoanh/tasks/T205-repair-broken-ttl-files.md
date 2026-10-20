---
id: T205
title: Sửa 10 file TTL không parse được (L3 = 0)
status: done
created: 2026-10-01
commit: f8d7727
revert: data/backups/t205_ttl_20261001_203559 + data/backups/t205_ttl_20261001_205612
---

# T205 — Sửa 10 file TTL hỏng cú pháp

## Vấn đề

Preflight T204 chặn ETL với **L3 = 10**: 10 file `.ttl` không parse được ⇒
`etl_ttl_full_import.py` dừng trước khi nạp. Trong đó 2 file
(`TS-Minh-Hoang-Tu-Dung.ttl`, `TS-Tuyet-Giau-Chon-Phac.ttl`) không có trong
`vn_person_authority`.

## Nguyên nhân gốc (KHÔNG phải chỉ thiếu prefix)

Thiếu `@prefix ex:` là lỗi phổ biến nhưng **không phải nguyên nhân** —
1.031/1.039 file cũng dùng `ex:` mà vẫn parse được. Có **5 loại lỗi độc lập**:

| # | Lỗi | Biểu hiện | Số file |
|---|-----|-----------|---------|
| 1 | Thiếu `@prefix ex:` | `Prefix "ex:" not bound` | 10 |
| 2 | Dòng CSV dính giữa file | `0-TS …, 0-TS …` chèn vào giữa block `@prefix`, tách file thành 2 khối | 3 |
| 3 | URI mất dấu `<` | `ex:monk/tay_thien_thu_tinh>` | 1 |
| 4 | `.` trùng | `"…"@vi . .` | 1 |
| 5 | Thiếu `.` / sai `,`→`;` | statement không đóng, objectList nối sai | 4 |

Lỗi 2 đáng chú ý: dòng CSV **chèn giữa file** (L468 và L934), nên 1 file TTL thực
ra là **2 khối TTL dính nhau** bằng dòng dữ liệu thô — nguyên nhân gốc sâu hơn hẳn
"thiếu prefix".

## Cách sửa

`scripts/t205_repair_broken_ttl.py` — **sửa theo vòng lặp lỗi-parse**, không đoán
pattern: rdflib luôn chỉ đúng dòng lỗi, vá xong parse lại, lặp tới khi sạch.

- `--stats` (mặc định): chỉ báo cáo, không ghi.
- `--dry-run`: xem kế hoạch sửa.
- `--apply`: backup file-level vào `data/backups/t205_ttl_<ts>/` rồi ghi.
- **Chỉ ghi khi rdflib parse được** — không sửa file mà sửa xong vẫn hỏng.
- File đánh dấu `[TRUNCATED]` = nghi bị cắt ngang, chỉ đóng cú pháp tối thiểu,
  **không bịa nội dung** ⇒ cần kiểm chứng lại trước khi kết luận. **Hóa ra 3
  file bị gắn nhãn này đều ĐỦ dữ liệu** — xem mục đính chính bên dưới.
  File **thực sự** cần bản gốc là file in `[BỎ QUA] sửa xong vẫn hỏng`.

## Kết quả

**L3: 10 → 0.** Corpus: **1.038/1.038 file parse OK** (trước: 1.028/1.038).

Backup: `data/backups/t205_ttl_20261001_203559`, `t205_ttl_20261001_205612`.

## Phát hiện thêm: 3 file trùng người

`TS-Dai-Xa-Nhu-Truong.ttl`, `TS-Minh-Hoang-Tu-Dung.ttl`,
`TS-Tuyet-Giau-Chon-Phac.ttl` là **3 bản của cùng một người**
(`phong_huyet_dien_chieu` / "Nam Viện Huệ Ngung"), chỉ khác `generationOrder`
(69/70/71) và 6 triple. Người này **đã có trong DB** (`dila_id=A004981`) nên không
mất dữ liệu — nhưng 3 file này là 3 record trùng, đáng gộp về 1.

## 3 file từng bị gắn nhãn `[TRUNCATED]` — ĐÍNH CHÍNH: KHÔNG bị cắt

Script t205 gắn nhãn `[TRUNCATED]` cho 3 file dưới đây khi phải chèn dấu `.` đóng
statement. **Đó là false positive của heuristic**, không phải mất dữ liệu.

| File | Status | Triple | Bio len | Predicate lõi | Kết luận |
|------|--------|--------|---------|----------------|-----------|
| `TS-Ban-Son-Bao-Tich.ttl` | ✅ **ĐÃ SỬA, ĐỦ DỮ LIỆU** | 15 | 3.590 | **12/12** | Không cần upload lại |
| `TS-Thanh-Dang-Minh-Luong.ttl` | ✅ **ĐÃ SỬA, ĐỦ DỮ LIỆU** | 26 | 3.748 | **12/12** | Không cần upload lại |
| `TS-Van-Cai-Thu-Tri.ttl` | ✅ **ĐÃ SỬA, ĐỦ DỮ LIỆU** | 16 | 3.169 | **12/12** | Không cần upload lại |

### Bằng chứng đã kiểm chứng

1. **12/12 predicate chuẩn** hiện diện (`label`, `type`, `biographicalNote`,
   `dharmaLineageName`, `generationOrder`, `P1_is_identified_by`, `birthEvent`,
   `deathEvent`, `hasTeacher`, `hasDisciple`, `gender`, `isLineageFounder`).
   Trong corpus, `hasTeacher` thiếu ở 2/1038 file và `hasDisciple` chỉ có ở
   31% file (đặc tính bình thường) — cả 3 file đều có đủ.
2. **Bio dài hơn median 3–4 lần**: 3.169–3.748 ký tự so với median 984
   (322%–381%). Bio ngắn bất thường mới là dấu hiệu cắt.
3. **Bios kết thúc bằng câu hoàn chỉnh** (có dấu `.`):
   - Bản Sơn Bảo Tích: `…Về thuật lại Mã Tổ, Tổ liền Ấn khả.`
   - Thành Đằng Minh Lương: `…xuống tới thế hệ chữ Lệ, Trung, Thiên.`
   - Vân Cái Thủ Trí: `…hoàng môn từ đây vào luân hồi.`
4. **Triple không lệch chuẩn**: 15 / 26 / 16 so với median corpus 14.

### Diff thực tế (bản gốc → sau sửa)

Cả 3 chỉ mất **1–2 dòng**, đều là lỗi chính tả, không mất nội dung:

- `TS-Ban-Son-Bao-Tich.ttl`: thêm `@prefix ex:`; thêm dấu `.` sau 1 dòng label.
- `TS-Thanh-Dang-Minh-Luong.ttl`: thêm `@prefix ex:`; thêm `.` sau
  `bkg:isLineageFounder "true"^^xsd:boolean`.
- `TS-Van-Cai-Thu-Tri.ttl`: thêm `@prefix ex:`; thêm `bkg:hasDisciple
  <ex:monk/thach_phat_tue_minh> ; .` cho 1 môn đồ bị thiếu dấu phẩy.

### Khuyến nghị cho Admin

**KHÔNG cần upload lại 3 file này.** Dữ liệu đã đủ và parse sạch.

Chỉ cần upload lại bản gốc cho các file **thực sự bị cắt ngang** (byte-offset
dừng giữa chừng, không có `.` kết thúc). Cách nhận biết: chạy
`python -X utf8 scripts/t205_repair_broken_ttl.py --stats` — nếu sau khi vá vẫn
in `[BỎ QUA] sửa xong vẫn hỏng` thì đó mới là file cần bản gốc.

Hiện **0 file** rơi vào trường hợp đó. Toàn bộ 10 file lỗi đã sửa xong, corpus
đạt **1.038/1.038 parse OK**.

Việc còn lại Admin cần làm là **nhãn (L1/L2)**, không phải file hỏng:

| Mã | SL | Nội dung | Tài liệu |
|----|----|----------|----------|
| L1 | 17 | Nhãn trùng tên 1 người khác trong file | `docs/Mimo-Flash/T203-ttl-quarantine-list.md` |
| L2 | 15 | Nhãn lệch, cần sửa theo triple `<ex:monk/SLUG>` | `docs/Mimo-Flash/T203-ttl-quarantine-list.md` |
| L4 | 302 | `Ð` (U+00D0) thay `Đ` (U+0110) — cảnh báo | script riêng, chưa có |
| L5 | 25 | `dila_id` trùng trong DB — cảnh báo | T203/T204 |

## Test

`tests/test_t203_ttl_guard.py`: **17/17 PASS**.
- Đổi assertion cũ "có cả L1, L2, L3" → "L3 = 0" (L3 đã hết sau T205).
- `npm test`, `npm run pipeline`: PASS.

## Còn lại (không thuộc T205)

- **L1 = 17, L2 = 15** (32 blocking): nhãn sai — Admin tự cập nhật theo
  `docs/Mimo-Flash/T203-ttl-quarantine-list.md`.
- **L4 = 302** (590 ký tự `Ð` U+00D0 thay `Đ` U+0110).
- **L5 = 25** nhóm `dila_id` trùng trong DB.