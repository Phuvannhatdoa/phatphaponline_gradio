# Session 2026-10-01 — T205 / T206 (TTL repair + mojibake) + T207 (DB plan)

**Ngày:** 2026-10-01
**Agent:** opencode (daoanh-data-ui-debug workflow)
**Admin:** phê chuẩn sửa TTL (T205), sửa mojibake TTL (T206), và kế hoạch T207 (DB).

---

## T205 — Sửa 10 file TTL không parse được (L3 10 → 0)

### Trigger
Preflight T204 chặn ETL: **L3 = 10** (10 file `.ttl` không parse). Trong đó
`TS-Minh-Hoang-Tu-Dung.ttl` + `TS-Tuyet-Giau-Chon-Phac.ttl` không có trong
`vn_person_authority`.

### Đính chính premise ban đầu
Giả thuyết ban đầu của tôi: "thiếu `@prefix ex:`". **Sai.** Thiếu prefix là lỗi
phổ biến nhưng **không phải nguyên nhân** — 1.031/1.039 file cũng thiếu mà vẫn
parse được. Tìm ra **5 loại lỗi độc lập**:

| Lỗi | File |
|-----|------|
| Thiếu `@prefix ex:` | 10 |
| **Dòng CSV dính GIỮA file** (`0-TS …, 0-TS …`) | 3 |
| URI mất dấu `<` (`ex:monk/tay_thien_thu_tinh>`) | 1 |
| Dấu `.` trùng (`"…"@vi . .`) | 1 |
| Thiếu `.` / sai `,`→`;` (objectList nối lỗi) | 4 |

Lỗi thứ 2 đáng chú ý nhất: dòng CSV **chèn giữa file** nên 1 file TTL thực ra là
**2 khối TTL dính nhau** bằng dữ liệu thô.

### Cách làm
`scripts/t205_repair_broken_ttl.py` — sửa theo **vòng lặp lỗi-parse** (rdflib luôn
chỉ đúng dòng lỗi) thay vì đoán pattern. Chỉ ghi khi parse được; backup
file-level; `--revert`.

Quá trình: 4 vòng cải tiến rule (thiếu `ex:` → CSV giữa file → URI mất `<` →
`. .` trùng → statement không đóng). Hai lần lặp vô hạn do rule chèn dòng giả
placeholder — dừng lại bằng cách sửa đúng gốc rễ (sửa dòng trước thay vì chèn).

### Kết quả
- **L3: 10 → 0.** Corpus **1038/1038 parse OK**.
- Backup `data/backups/t205_ttl_20261001_203559`, `_205612`.
- Commit `f8d7727`, docs `e9678f6`.

### Phát hiện: 3 file trùng người
`TS-Dai-Xa-Nhu-Truong` / `TS-Minh-Hoang-Tu-Dung` / `TS-Tuyet-Giau-Chon-Phac` =
3 bản của **cùng một người** `phong_huyet_dien_chieu` ("Nam Viện Huệ Ngung"), chỉ
khác `generationOrder` 69/70/71 và 6 triple. Người này **đã có trong DB**
(`A004981`) ⇒ **không mất dữ liệu**, nhưng là 3 record trùng, đáng gộp.

### Đính chính #2: nhãn `[TRUNCATED]` là false positive
Tôi gắn `[TRUNCATED]` cho 3 file và khuyên Admin upload lại. **Sai.** Kiểm
chứng lại:

| File | Predicate lõi | Bio len | Kết thúc bio |
|------|---------------|---------|--------------|
| `TS-Ban-Son-Bao-Tich.ttl` | **12/12** | 3.590 (365% median) | câu hoàn chỉnh |
| `TS-Thanh-Dang-Minh-Luong.ttl` | **12/12** | 3.748 (381%) | câu hoàn chỉnh |
| `TS-Van-Cai-Thu-Tri.ttl` | **12/12** | 3.169 (322%) | câu hoàn chỉnh |

⇒ **KHÔNG cần upload lại.** Diff thực tế mỗi file chỉ 1–2 dòng, toàn lỗi chính tả.
Thêm `--verify` vào script để tự kiểm chứng 12 predicate + độ dài bio.
Commit `c1ef970`.

---

## T206 — Sửa mojibake `Ð` (U+00D0) → `Đ` (U+0110) (L4 302 → 0)

### Trigger
Preflight L4 = 302 mục / 302 file / 590 ký tự `Ð`.

### Nguyên nhân
Chữ Đ tiếng Việt là **U+0110**. 302 file bị ghi bằng **U+00D0 (LATIN CAPITAL LETTER
ETH)** — không tồn tại trong tiếng Việt, chỉ dùng cho tiếng Iceland. UI hiện
`Ðại sư` thay vì `Đại sư`.

### Kiểm chứng an toàn trước khi sửa cả lô
| Vị trí | Số `Ð` |
|--------|---------|
| URI `<...>` | **0** |
| `@prefix` | **0** |
| slug `ex:monk/...` | **0** |
| `rdfs:label@"zh"` | **0** |

Token nhiều ký tự duy nhất: `Ðoan` ×38 (= Đoàn), `Ðam` ×1 (= Đàm, "Đàm Nguyên Ứng
Chân") — đều tiếng Việt. Corpus đã có sẵn 11.087 chữ `Đ` đúng.

### Kết quả
- **L4: 302 → 0.** Corpus **1038/1038 parse OK** (không hồi quy).
- Kiểm chứng mạnh nhất: so từng ký tự bản gốc vs bản sửa trên cả 302 file —
  **mọi khác biệt đều đúng là `Ð`→`Đ`, tổng 590 vị trí, 0 đổi sai**.
- Backup `data/backups/t206_mojibake_20261001_222517`.
- Commit `88847b8`, docs `abb3f73`.

### Bài học phương pháp
Phép thử đảo ngược đầu tiên (`Đ`→`Ð` rồi so sánh) cho **18/302** vì nó cũng thay
luôn các `Đ` đúng sẵn có. Đó là lỗi của **phép thử**, không phải của bản sửa — thay
bằng so khớp **theo vị trí ký tự**. Tương tự: heredoc PowerShell làm hỏng UTF-8
(`Ð` → `?`) làm kết quả probe sai ⇒ viết probe ra **file** dùng escape `\uXXXX`.

---

## T207 — Kế hoạch sửa mojibake trong DB (CHƯA build)

### Phát hiện: lỗi này **phá vỡ tra cứu**, không chỉ sai hiển thị
`app.py:96 normalize_text()` dùng bởi **cả 2** call site đọc `lexicon.key_norm`
(`app.py:1226 _translate_zh_term`, `app.py:2800`) làm `.replace('đ','d').replace('Đ','d')`.
**U+00D0 không có canonical decomposition** (`decomposition=''`) ⇒ sống sót qua
NFD + bỏ Mn + `.lower()`:

| Term | `normalize_text()` | Kết quả |
|------|--------------------|---------|
| `Đoạn lạc` | `'doan lac'` | đúng |
| `Ðoạn lạc` | `'ðoan lac'` | **sai** |

⇒ tra cứu từ điển mọi mục có chữ Đ đều trượt. Probe thật: `Đại Bi` → key
`'dai bi'` → **0 row khớp**.

### Quy mô đo được
- DB: **22 cột / 1.469 row** chứa `Ð` (chi tiết trong task T207).
- `lexicon`: 162 row `term`, 328 row `definition`, 162 `normalized`, 162 `key_norm`.
- `key_norm` khớp `normalize_text(term)`: **112.430/166.278 (67,6%)**.
- 53.384 row lệch vì `đ/Đ` **đúng** → lỗi quy ước có sẵn, **không do T207**.
- Chỉ **162 row có `Ð`** là phạm vi.

### 2 điểm rủi ro đã soi kỹ
1. `translation_exemplar.zh` — tên cột gợi ý Hán tự, nhưng đọc nội dung 2 row =
   **toàn văn tiếng Việt**. An toàn.
2. `lexicon_fts` — **FTS5 external-content** (`content=lexicon, content_rowid=id`),
   **0 trigger** ⇒ `UPDATE lexicon` thẳng **lệch index**. Phải dùng lệnh FTS5
   `delete` → update base → insert (443 row). **Không** `rebuild` (166k row).

### Mốc quyết định — chờ Admin
| Chiến lược | Row `Ð` khớp lookup |
|------------|---------------------|
| A: chỉ thay `Ð`→`Đ` | **0/162** ❌ |
| B: thay **và** tính lại `key_norm = normalize_text(term)` cho 162 row đó | **162/162** ✅ |

**Đề xuất B.** Task: `tasks/T207-fix-db-mojibake-and-restore-lexicon-lookup.md`,
entry trong `docs/tasktodo.md` § ACTIVE, row placeholder trong `docs/ROLLBACK.md`.

---

## Việc còn lại (ETL vẫn bị chặn)
- **L1 = 17, L2 = 15** (32 blocking) — nhãn sai, Admin tự cập nhật theo
  `docs/Mimo-Flash/T203-ttl-quarantine-list.md`.
- **L5 = 25** nhóm `dila_id` trùng.
- Gộp 3 file TTL trùng người (`phong_huyet_dien_chieu`).
- T208 (đề xuất): 53.686 row `key_norm` lệch quy ước — đụng hành vi tra cứu quy
  mô lớn, cần task riêng.

## Revert
- T205: `git revert --no-edit c1ef970` / `f8d7727`; TTL: copy lại từ
  `data/backups/t205_ttl_*`.
- T206: `git revert --no-edit abb3f73` / `88847b8`; TTL:
  `python -X utf8 scripts/t206_fix_mojibake.py --revert data/backups/t206_mojibake_20261001_222517`.