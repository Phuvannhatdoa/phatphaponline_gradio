# Session 2026-10-02 — T208 (khoá tra cứu phụ lexicon) + G208 (quy trình revert an toàn)

**Ngày:** 2026-10-02 · **Agent:** opencode · **Admin:** "Đồng ý build… lưu logs, gitcommit, update .md, bảo đảm revert thuận tiện, gọi pipip khi done"

**Task:** `tasks/T208-lexicon-altkey-safe-lookup.md`, `tasks/G208-safe-commit-revert-procedure.md`

---

## 1. Đề xuất T208 của tôi ĐÃ bị bác bỏ bằng dữ liệu thật

Tôi đề xuất: tính lại `key_norm = normalize_text(term)` cho 53.384 row.
**Đo thật → nguy hiểm** (`scripts/probe_t208.py`):

| Hậu quả | Số lượng |
|---|---|
| Khoá mới bị trùng | **6.866 khoá** (15.453 row) |
| Khoá va chạm term **KHÁC NGHĨA** | **241** |

Bằng chứng (các mục Phật học khác nhau bị gộp):
```
dinh     ← Định / Đỉnh        nhưng đang có Dĩnh
tu do    ← Tứ Độ               nhưng đang có Tự Do
tam duc  ← Tam Đức             nhưng đang có Tam Dục
that dai ← Thất Đại             nhưng đang có Thật Dài
don giao ← Đốn Giáo            nhưng đang có Đổn Giáo
```
⇒ tra cứu sẽ trả **DỊCH SAI**. Trong từ điển Phật học, trả nhầm tệ hơn không trả.

### Phát hiện sâu hơn: dữ liệu HỎNG, không phải lệch quy ước
`probe_t208b.py` thử 3 giả thuyết normalizer — riêng 53.384 row chỉ **36,3%**
khớp giả thuyết khả dĩ nhất. Lý do: `key_norm` **tự mâu thuẫn trong cùng chuỗi**:
```
'Đuc lon. tu ton xung nhung nguoi đao đuc lon.'   ← Đ hoa rồi đ thường
'1.tu tanh khac : tam Đai bi lay vo si'          ← Đ giữ nguyên
```
⇒ Không normalizer nào sinh được ⇒ **dữ liệu hỏng**. Sửa hàng loạt là sai.

**Bài học:** trước khi ghi lại dữ liệu sinh ra khoá tra cứu, **phải đo va chạm
và kiểm tra có trả nhầm dịch không**. Tôi chỉ đo "số row lệch" rồi đề xuất.

## 2. Phương án đã build — additive, 2 lớp chặn

Thêm cột `lexicon.key_norm_alt`; **`key_norm` không đụng tới**.

| Lớp chặn | Điều kiện | Loại |
|---|---|---|
| 1 | khoá phụ trỏ tới **1 term duy nhất** | 2.214 row mơ rồng |
| 2 | khoá phụ chưa bị term nào chiếm | 0 (lớp 1 bao trọn) |

**Kết quả:** +51.472 row có khoá phụ; trong đó **19.661 row** có `term < 60` ⇒
đúng điều kiện `LENGTH(term) < 60` của `app.py:1250`.

**Verify DB thật 7/7:**
```
[OK] cột key_norm_alt tồn tại
[OK] số row có khoá phụ = 51472 (đúng kế hoạch)
[OK] trong đó term < 60 ký tự = 19661
[OK] mọi khoá phụ trỏ tới ĐÚNG 1 term   (0 vi phạm)
[OK] không khoá phụ nào trùng khoá hiện có của term KHÁC (0 trường hợp)
[OK] key_norm còn nguyên (166278 row)
[OK] PRAGMA integrity_check = 'ok'
```
Test **19/19 PASS** (fixture nhỏ), `test:t208` nối `test:translation`.

## 3. Chưa nối `app.py` — có lý do

`app.py` **đang có WIP của session khác** (`git status` = ` M app.py`) và line đã
trôi so với lúc khảo sát (`app.py:1226` nay là docstring). Sửa trong commit này
sẽ xung đột. Call site hiện tại đã xác minh: **`app.py:1250`** và **`app.py:2824`**.
Cách nối (cho T209) là truy vấn 2 bước: `key_norm` trước (giữ nguyên hành vi),
`key_norm_alt` sau khi trượt. Test đã chứng minh 2 bước này không trả nhầm.

## 4. G208 — Quy trình revert thuận tiện (yêu cầu của Admin)

Đã tài liệu hoá lỗi git đã làm hỏng 1 commit trong phiên trước:
`tasks/G208-safe-commit-revert-procedure.md` + **`AGENTS.md §14`**.

Điểm cốt lõi: khi lỗi `.git/index`, index tạm **phải tạo bằng `git read-tree
HEAD`** — **tuyệt đối không** `cp .git/index` (đó là nguyên nhân commit xoá nhầm
3 file). Kèm quy tắc: luôn kiểm `git diff --cached` sau `git add`; sau mỗi
commit kiểm `git diff --name-status HEAD~1 HEAD`; ưu tiên migration **additive**
để revert chỉ là `DROP COLUMN` — mất 0 dữ liệu.

## 5. Revert T208
```bash
git revert --no-edit <sha_T208>                                   # code + docs
python -X utf8 scripts/t208_lexicon_altkey_migration.py --revert  # DB, mất 0 dữ liệu
# hoặc restore: data/backups/lineage_t208_20261002_112520.db
```

## 6. Còn lại
- **L1 = 17, L2 = 15** (32 blocking) — nhãn sai, **ETL vẫn bị chặn**, Admin tự
  cập nhật theo `docs/Mimo-Flash/T203-ttl-quarantine-list.md`.
- **L5 = 25** nhóm `dila_id` trùng.
- **T209 (đề xuất):** nối truy vấn 2 bước vào `app.py:1250` + `:2824` — làm khi
  `app.py` không còn WIP.
- Gộp 3 file TTL trùng người (`phong_huyet_dien_chieu`, gen 69/70/71).