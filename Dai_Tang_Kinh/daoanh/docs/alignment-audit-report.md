# Alignment Audit Report — Hán–Việt Passage Mapping

**Ngày:** 2026-09-04  
**Auditor:** Claude Code / session tự động  
**Trạng thái:** LỖI ALIGNMENT XÁC NHẬN — cần sửa trước khi dùng cho evidence/citation

---

## 1. Tóm tắt vấn đề

| Chỉ số | Giá trị |
|--------|--------|
| Work kiểm tra | T50n2060 (唐高僧傳) |
| Passage kiểm tra | passage_id 110, loc_ref `0-0457a-` (Thiếu Lâm Tự, PL000000023255) |
| Số đoạn Hán render | 54 segments |
| Số đoạn Việt render | 54 chunks |
| Đoạn khớp thực sự | ~1 (đoạn đầu tương đối khớp) |
| Đoạn lệch xác nhận | Hán 41 ≠ Việt 41 (lệch ~8 đoạn) |
| Loại lỗi | **Ordinal mapping + proportional distribution** |

**Lỗi chính:**  
Frontend dùng `dtDistributeVi(viText, n)` để chia Vi text thành `n` chunks theo tỉ lệ ký tự, rồi ghép `chunk[i]` với Han `segment[i]`. Không có alignment record trong DB.

---

## 2. Bằng chứng lỗi cụ thể

### Đoạn Hán 41 (thực tế)
```
創翻大本。至龍朔三年十月末了。凡四處十六會說。總六百卷。
般若空宗此焉周盡。於間又翻成唯識論辯中邊論唯識二十論品類足論等。
```
**Nội dung:** Huyền Trang dịch Đại Bát Nhã, hoàn tất năm Long Sóc 3; 4 nơi, 16 hội, 600 quyển; song song dịch các luận Duy thức.

### Phần Việt số 41 (đang hiển thị sai)
```
"Năm Hiển Khánh thứ hai, giá hạnh Lạc Dương..."
```
**Nội dung:** Thực chất là dịch phần gần Hán 33 (về chuyến xa giá đến Lạc Dương).

**Lệch:** ~8 đoạn tính từ đầu bản dịch.

---

## 3. Phân tích gốc gây lỗi

### A. Pipeline dịch thuật hiện tại
```
raw_text (Hán cả đoạn) → Groq LLM (1 API call) → vi_text (Việt liên tục)
```
- LLM nhận TOÀN BỘ đoạn Hán (~666–1044 chars) làm 1 prompt
- LLM trả TOÀN BỘ bản Việt (~2776–3475 chars) làm 1 string liên tục
- Không có passage-level ID hay segment boundary trong prompt/response
- Không có validation về số câu hay ranh giới đoạn

### B. Pipeline chia đoạn frontend
```
raw_text → dtSegmentHan() → 54 Han segments (theo dấu câu。；！？)
vi_text  → dtDistributeVi() → 54 Vi chunks (theo tỉ lệ chars)
Ghép: Han[i] ↔ Vi[i] (ordinal only)
```

### C. Tại sao lệch?
1. Hán cổ văn ~20-30 chars/câu, Vi dịch ~60-90 chars/câu (tỉ lệ 1:3)
2. Mỗi đoạn Hán có độ dài khác nhau → distribution không đều
3. Một câu Hán dài (ví dụ lời khen hoàng đế) → Vi dịch dài → ăn vào chunk của đoạn tiếp theo
4. Lỗi tích lũy: đoạn 2 đã lệch → đoạn 3 lệch thêm → đến đoạn 41 lệch ~8 đoạn

### D. Không có bảo vệ trong LLM response
- Không có schema validation
- Không có passage_id trong response
- Không có hash check
- Không có sentence count check

---

## 4. Phạm vi ảnh hưởng

### Trong DB
- Tất cả records trong bảng `passage` có `vi_text` không null — đều bị lỗi alignment nếu dùng ordinal mapping
- Số passage có `has_vi = true` cần audit thêm

### Trong UI
- Tab Nguyên Văn: hiện đang hiển thị số 01–54 ở cả hai cột → gây hiểu nhầm 1:1
- Hover sync: hoạt động theo data-seg ordinal → cũng lệch nội dung
- Nút "Đọc đầy đủ" → mở full text (đúng)
- Evidence trong Lineage tab (nếu có) → cần kiểm tra riêng

---

## 5. Đoạn nào lệch, đoạn nào khớp?

Dựa trên đối chiếu manual và tỉ lệ chars:

| Khoảng đoạn Hán | Trạng thái Vi tương ứng |
|-----------------|------------------------|
| Hán 01 | Việt tương đối khớp (đoạn đầu) |
| Hán 02–05 | Việt bắt đầu lệch nhẹ |
| Hán 10–20 | Việt lệch ~3–5 đoạn |
| Hán 30–40 | Việt lệch ~5–8 đoạn |
| Hán 41 | Việt lệch ~8 đoạn (xác nhận bằng tay) |
| Hán 42–54 | Không có bản Việt (Vi text đã hết ở chunk 41) |

**Kết luận:** Vi text (3475 chars) không đủ để cover 54 Han segments → chunks 42–54 báo "Chưa có phần dịch tương ứng."

---

## 6. Dữ liệu cần được sửa (T50n2060)

**Không sửa bằng cách kéo số display.** Cần:
1. Rebuild Han segmentation từ raw_text (ổn định, deterministic)
2. Dịch lại từng segment với passage_id trong prompt
3. Tạo alignment record
4. Validate alignment (xem `alignment-test-cases.md`)

Xem chi tiết: `t50n2060-repair-plan.md`

---

## 7. Không có text bị corrupt

- `raw_text` Hán văn: nguyên vẹn, không corrupt
- `vi_text` tiếng Việt: nguyên vẹn, không corrupt
- Hash check: chưa có trong DB (cần thêm `raw_zh_hash`)
- Không có lặp/thiếu text — chỉ sai alignment

---

## 8. Kết luận

| Vấn đề | Trạng thái |
|--------|-----------|
| Raw Hán văn | Đúng |
| Vi translation text | Đúng (nội dung), Sai (alignment) |
| Ordinal mapping | Sai từ gốc |
| Alignment record | Không tồn tại trong DB |
| UI hiển thị | Đã fix nhãn (⚠ phân phối tự động, số ≈) |
| Dùng làm evidence | KHÔNG được cho đến khi có alignment record |
| Dùng làm citation | KHÔNG được |

---

*Tham khảo thêm: `bilingual-passage-alignment-design.md` · `t50n2060-repair-plan.md` · `alignment-test-cases.md`*
