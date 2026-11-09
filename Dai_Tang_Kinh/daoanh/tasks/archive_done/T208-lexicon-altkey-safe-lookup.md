---
id: T208
title: Khoá tra cứu phụ cho lexicon (key_norm_alt) — additive, revert = DROP COLUMN
status: done
created: 2026-10-02
owner: agent
module: daoanh
depends_on: T207
commit: 6230c40
revert: "python -X utf8 scripts/t208_lexicon_altkey_migration.py --revert"
---

# T208 — Khoá tra cứu phụ cho `lexicon` (đề xuất cũ ĐÃ BỊ BÁC BỎ)

> **Kết luận quan trọng: đề xuất ban đầu của T208 (tính lại `key_norm` cho
> 53.384 row) là SAI và đã bị bác bỏ bằng dữ liệu thật.** Task này build lại
> theo hướng additive, không sửa một byte dữ liệu nào.

---

## 1. Đề xuất cũ và lý do bác bỏ

T207 phát hiện 53.384 row có `key_norm != normalize_text(term)`. Đề xuất ban đầu:
tính lại `key_norm = normalize_text(term)` cho nhóm đó.

**Đo thật → nguy hiểm** (`scripts/probe_t208.py`):

| Hậu quả | Số lượng |
|----------|----------|
| Khoá mới bị trùng | **6.866 khoá** (15.453 row dính) |
| Khoá va chạm với term **KHÁC NGHĨA** | **241** |

Bằng chứng va chạm (các mục Phật học khác nhau bị gộp làm một):

| Khoá sau khi tính lại | Nhóm bị gộp | Row đang có sẵn |
|---|---|---|
| `dinh` | `Định`, `Đỉnh` | `Dĩnh` |
| `tu do` | `Tứ Độ` | `Tự Do` |
| `tam duc` | `Tam Đức` | `Tam Dục` |
| `that dai` | `Thất Đại` | `Thật Dài` |
| `don giao` | `Đốn Giáo` | `Đổn Giáo` |

⇒ Tra cứu sẽ trả **DỊCH SAI** cho các mục khác nhau. Trong từ điển Phật học,
trả nhầm còn tệ hơn không trả.

### Phát hiện sâu hơn: `key_norm` của nhóm này là **dữ liệu hỏng**
`scripts/probe_t208b.py` thử 3 giả thuyết normalizer:

| Giả thuyết | Khớp |
|---|---|
| `normalize_text()` (bỏ dấu + `đ→d`) | 112.592 / 166.278 (67,7%) |
| **bỏ dấu nhưng GIỮ `đ/Đ`** | 131.817 / 166.278 (79,3%) |
| bỏ dấu + `đ→d` (trùng hệt `normalize_text`) | 112.592 (67,7%) |

Riêng 53.384 row nhóm T208, giả thuyết "bỏ dấu nhưng giữ `đ/Đ`" chỉ khớp
**36,3%**. Lý do: `key_norm` **tự mâu thuẫn trong cùng một chuỗi**:

```
key cu = 'Đuc lon. tu ton xung nhung nguoi đao đuc lon.'   ← Đ hoa rồi đ thường
key cu = '1.tu tanh khac : tam Đai bi lay vo si'          ← Đ giữ nguyên
```

⇒ Không có normalizer nào sinh ra được giá trị này. Đây là **dữ liệu hỏng**,
không phải "lệch quy ước". Sửa hàng loạt là sai về nguyên tắc.

---

## 2. Phương án đã build: khoá phụ, additive, có 2 lớp chặn

**Không sửa `key_norm`.** Thêm cột mới `lexicon.key_norm_alt` chỉ cho những row
mà tra cứu hiện tại **không** tìm được, và chỉ khi khoá phụ trỏ tới **đúng một
term** trong toàn bảng.

| Lớp chặn | Điều kiện | Số row bị loại |
|---|---|---|
| 1 | khoá phụ trỏ tới **1 term duy nhất** | 2.214 (mơ rồng) |
| 2 | khoá phụ **chưa bị** term nào chiếm | 0 (lớp 1 đã bao trọn) |

Ví dụ bị loại ở lớp 1 (an toàn hơn là trả sai):
```
'dai chung'  -> ['Đại Chúng', 'Đại Chứng']
'dai tu'     -> ['Đại Tu', 'Đại Từ', 'Đại Tự']
'dinh'       -> ['Dĩnh', 'Đinh', 'Đình']
'don giao'   -> ['Đốn Giáo', 'Đổn Giáo']
```

### Đo được
- **51.472 row** được thêm khoá phụ.
- Trong đó **19.661 row** có `term < 60` ký tự ⇒ đúng điều kiện `LENGTH(term) < 60`
  của `app.py:1250`, tức **là những row thực sự sẽ được tra cứu tìm thấy**.
- `key_norm` **nguyên vẹn 166.278 row** — hành vi tra cứu hiện tại không đổi.

---

## 3. Còn lại: CHƯA nối vào `app.py` — cần task riêng (T209)

`app.py` **đang có WIP của session khác** (`git status` = ` M app.py`) và line
đã trôi so với lúc khảo sát. Sửa trong commit này sẽ xung đột. Call site hiện tại:

| File:line | Truy vấn |
|---|---|
| `app.py:1250` | `SELECT term FROM lexicon WHERE key_norm = ? AND LENGTH(term) < 60 ORDER BY priority ASC LIMIT 1` |
| `app.py:2824` | `SELECT DISTINCT term FROM lexicon WHERE key_norm = ? AND LENGTH(term) < 100 ORDER BY priority ASC …` |

**Cách nối (đề xuất cho T209) — truy vấn 2 bước, giữ nguyên thứ tự ưu tiên:**

```python
row = conn.execute(q_key_norm, (key,)).fetchone()      # BƯỚC 1: y hệt hiện tại
if not row:
    row = conn.execute(q_key_norm_alt, (key,)).fetchone()   # BƯỚC 2: khoá phủ
```

Bước 1 giữ nguyên ⇒ không đổi hành vi với 112.592 row đang chạy tốt. Bước 2 chỉ
chạy khi bước 1 trượt, và theo cam kết của migration **không thể trả nhầm**.

Test đã chứng minh truy vấn 2 bước: mục đã tìm được vẫn trả về qua `key_norm`
(đúng đường cũ), mục hỏng trước đây giờ trả về qua `key_norm_alt`, và các cặp
mơ rồng (`Tứ Độ`/`Tự Do`, `Tam Đức`/`Tam Dục`) **không** bị trả nhầm.

---

## 4. Đã tạo

| File | Vai trò |
|------|---------|
| `scripts/t208_lexicon_altkey_migration.py` | `--stats/--dry-run/--apply/--verify/--revert` (additive) |
| `scripts/probe_t208.py` | đo va chạm khoá (bác bỏ đề xuất cũ) |
| `scripts/probe_t208b.py` | tìm normalizer cũ ⇒ kết luận dữ liệu hỏng |
| `scripts/probe_t208c.py` | đo lợi ích + rủi ro từng lớp chặn |
| `scripts/probe_t208d.py` | số an toàn thật (cả 2 lớp) |
| `tests/test_t208_lexicon_altkey.py` | **19/19 PASS** trên DB fixture |
| `package.json` | `test:t208` → nối vào `test:translation` |

## 5. Verify sau `--apply` (DB thật)
```
[OK] cột `key_norm_alt` tồn tại
[OK] số row có khoá phụ = 51472 (đúng kế hoạch)
[OK] trong đó term < 60 ký tự (điều kiện app.py:1250) = 19661
[OK] mọi khoá phụ trỏ tới ĐÚNG 1 term (không thể trả sai)   (0 vi phạm)
[OK] không khoá phụ nào trùng khoá hiện có của term KHÁC    (0 trường hợp)
[OK] key_norm còn nguyên (166278 row, không sửa dữ liệu)
[OK] PRAGMA integrity_check = 'ok'
=> PASS
```

## 6. Revert — thuận tiện, mất 0 dữ liệu
```bash
# code + docs
git revert --no-edit <sha_T208>

# DB (1 lệnh, additive nên không cần dữ liệu gốc)
python -X utf8 scripts/t208_lexicon_altkey_migration.py --revert

# hoặc khôi phục nguyên trạng DB (nếu cần)
# data/backups/lineage_t208_20261002_112520.db
```
Vì chỉ **thêm cột**, `--revert` = `DROP INDEX` + `DROP COLUMN` ⇒ **không mất
dòng dữ liệu nào**, `key_norm` không bao giờ bị chạm tới.

## 7. Sai lầm của chính tôi
Đề xuất T208 ban đầu (tính lại `key_norm`) **nguy hiểm** — tôi đã đưa ra khi
chỉ đo "số row lệch" mà **chưa đo va chạm khoá**. Bài học: trước khi ghi lại dữ
liệu sinh ra khoá tra cứu, **phải đo va chạm và kiểm tra có trả nhầm dịch
không** — đặc biệt với dữ liệu Phật học, nơi các mục gần nhau nhưng khác nghĩa.

## 8. Việc còn lại
- **L1 = 17, L2 = 15** (32 blocking) — nhãn sai, Admin tự cập nhật theo
  `docs/Mimo-Flash/T203-ttl-quarantine-list.md`. **ETL vẫn bị chặn.**
- **L5 = 25** nhóm `dila_id` trùng.
- **T209 (đề xuất):** nối truy vấn 2 bước vào `app.py:1250` + `app.py:2824` —
  làm khi `app.py` không còn WIP.
- Gộp 3 file TTL trùng người (`phong_huyet_dien_chieu`, gen 69/70/71).