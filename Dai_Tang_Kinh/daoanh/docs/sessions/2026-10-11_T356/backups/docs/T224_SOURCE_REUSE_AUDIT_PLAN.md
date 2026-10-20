---
task: tasks/T224-geo-spatial-timeline-founding-phase2.md
report: G2-1 SOURCE_REUSE_AUDIT
title: "Source Reuse Audit — phân loại 59.167 DILA places (A1/A2/C/B/D/E)"
status: ready-for-admin-review
created: 2026-10-04
measured_at: 2026-10-04
db: data/lineage.db (read-only, file:...?mode=ro)
record: data/t224_g0_measurements.json
---

# T224 · G2-1 — Source Reuse Audit

**Đọc kèm:** `docs/Mimo-Flash/T224-geo-spatial-timeline-founding-phase2.md` (plan, tự chứa)
**Số đo gốc:** `data/t224_g0_measurements.json` — sinh bằng 1 script authoritative, tổng khớp tuyệt đối.

> ⚠️ **0 write DB.** Toàn bộ số dưới đây đọc qua `file:...?mode=ro`. Không có `INSERT`/
> `UPDATE`/`CREATE`. Cột nào cũng đối chiếu bằng **control** (xem §6).

---

## 1. Baseline (G0)

| Đối tượng | Số | Ghi chú |
|---|---:|---|
| `places_dila` | **59.167** | ✅ **mẫu số** của audit · PK `id` **unique** (59167 = distinct) |
| `places` | 59.161 | **không** dùng làm mẫu số — khác 6 dòng |
| `places_dila.raw_xml` khác rỗng | 59.167 (100%) | ⚠️ không dùng làm tiêu chí — xem §3 |
| `places_dila.note` khác rỗng | 17.085 | 15.919 giá trị khác nhau |
| `place_timeline_events` | 3.688 rows / **3.534** distinct `dila_id` | không có FK |
| `geo_cross_ref` | 190 rows | |

---

## 2. Phân bồ A1/A2/C/B/D/E (đo thật)

Thứ tự ưu tiên **`A1 > A2 > C > B > D > E`** — mỗi place vào **nhóm đầu tiên** khớp.

| Nhóm | Tiêu chí | Place | % |
|---|---|---:|---:|
| **A1** | event nguồn `wikidata` / `wikidata_p571` — bằng chứng ngoài | **249** | 0,421% |
| **A2** | event suy luận từ era / dynasty / note | **3.285** | 5,552% |
| **C** | có `geo_cross_ref`, chưa có event | **85** | 0,144% |
| **B** | có mốc thành lập (regex), chưa có event | **226** | 0,382% |
| **D** | có `note` mô tả, **chưa** có mốc thành lập → **cần NLP** | **13.336** | 22,540% |
| **E** | không có gì ⇒ **giới hạn nguồn** | **41.986** | 70,962% |
| | **TỔNG** | **59.167** | ✅ khớp `places_dila` |

### Vì sao phải có precedence

**22 place** khớp cả tiêu chí C lẫn tiêu chí B. Không ép thứ tự ⇒ tổng vỡ.
Ưu tiên **C trước B** vì cross-ref là mapping có chủ đích, còn regex B chỉ là chữi từ khoá.

### Vì sao tách A1 / A2

93% event là **suy luận**, không phải dữ liệu gốc:

| `source` | Event | Loại |
|---|---:|---|
| `dila_era_name` | 1.471 | suy luận (tên đời) |
| `dila_dynasty` | 851 | suy luận (triều đại) |
| `dila_note` | 719 | suy luận (mô tả) |
| `dila_note_regex` | 276 | suy luận (regex note) |
| `dila_founding_phase2` | 55 | suy luận (regex note) |
| `dila_fosizhi` | 15 | ngoài (Fosi Zhi) |
| `wikidata` + `wikidata_p571` | 155 | **ngoài, kèm QID** |

⚠️ Gộp A1+A2 thành "3.534 place đã có ngày thành lập" sẽ **sai 13 lần** về mức chắc chắn.

---

## 3. Vì sao nhóm B cũ (plan T181) là sai — bằng chứng

Plan cũ định nghĩa B = *"Có TEI/XML marked-up evidence trong `raw_xml`/`note`"*.

1. **`raw_xml` khác rỗng 59.167/59.167 = 100%** ⇒ "có mã XML" là tautology, khớp mọi dòng.
   Theo nghĩa đen, B = 59.167 và D = E = **0**.
2. **TEI không có markup ngày thành lập.** `foundingDate` = **0**, `founded` = **0**
   (pattern ASCII ⇒ tin cậy tuyệt đối).
3. **`ns0:note` là boilerplate nguồn, không phải evidence:** mẫu 4.000 dòng chỉ **794**
   giá trị khác nhau; `中研院歷史地名` chiếm ~78%; mẫu đầu đều là `廣大之陸上人文地理區域`.
4. **Văn bản mô tả thật nằm ở cột `note`** (15.919 giá trị khác nhau) — đó là **prose**
   ⇒ việc của **nhóm D**, không phải B.

**Định nghĩa lại (đã đo):** B = `note` **hoặc** `raw_xml` chứa một trong
`始建於` · `創建` · `建於` · `建國`.

| Mốc | Số place (độc lập, chưa loại trùng) |
|---|---:|
| `始建於` | 215 |
| `建於` | 482 |
| `創建` | 242 |
| `建國` | 30 |
| **B sau dedupe + loại trùng A/C** | **226** |

Trong 226 place của B, **6** có marker chỉ nằm ở `raw_xml` (`note` rỗng) ⇒ regex bắt buộc
quét **cả hai** cột.

---

## 4. Nhóm D — ước lượng khối lượng NLP

| Chỉ số | Giá trị |
|---|---:|
| Số place | **13.336** |
| Tổng ký tự `note` | **733.814** |
| Ước lượng token (~1,6 ký tự/token) | **~458.633** |
| Số batch ~8.000 token | **57** |
| Độ dài: median / p90 / max | 42 / 123 / **1.740** |

**Đánh giá:** 458k token là **rất nhỏ** — một lần chạy LLM rẻ để xử lý hết, **không** cần
batch 57 lần nếu chấp nhận 1 prompt lớn. Nhóm median chỉ 42 ký tự ⇒ output ngắn.

⚠️ **Không tự động hoá.** Đề xuất: regex mở rộng trước (rẻ, kiểm chứng được), chỉ đưa
phần còn lại cho LLM. `p90 = 123` ký tự ⇒ note dài không nhiều.

---

## 5. Nhóm E — đây là **giới hạn nguồn**, không phải việc chưa làm

Admin đã chốt **hướng (a)**. Cơ sở:

| Trong 41.986 place của E | Số | % của E |
|---|---:|---:|
| **vẫn có `name_zh`** (tên Hán) | 41.982 | 99,99% |
| **vẫn có `name`** (tên la-tinh) | 41.980 | 99,99% |
| **vẫn có `raw_xml`** (khung TEI) | 41.986 | 100,00% |
| **vẫn có `note_category`** | 41.986 | 100,00% |
| **vẫn có `district`** | 41.950 | 99,91% |
| **vẫn có lat/lon** | 41.928 | **99,86%** |
| có `listbibl` (danh mục kinh) | 1.201 | 2,86% |

⇒ **E không phải "chưa enrich"**: E **đã** có tên, **đã** có toạ độ, **đã** có phân loại
nơi chốn. Những gì E **không** có chỉ là **nội dung mô tả** (`note` rỗng) và **mốc thời
gian** — cả hai đều là thứ **nguồn DILA không cung cấp** cho các place này.

Đây là **giới hạn của nguồn dữ liệu**, không phải backlog kỹ thuật ⇒ **không mở G3**.

---

## 6. Bẫy kỹ thuật — **bắt buộc** control trước khi tin số

**Pattern CJK truyền qua PowerShell heredoc bị mangle thành `?` ⇒ `LIKE '%始建於%'`
trả 0 giả.** Phiên review 2026-10-04 đã dính lỗi này, suýt kết luận nhầm "B rỗng".

Control bắt buộc trước mọi lần đo CJK:

| Pattern | Giá trị đúng |
|---|---:|
| `建` | 4.646 |
| `帝` | 798 |
| `唐宋` | 36 |

**Cả 3 bằng 0 ⇒ pattern đã chết, đừng tin kết quả.** Mọi script phải dùng `\uXXXX`
trong Python hoặc để file UTF-8.

---

## 7. Đề xuất (trình Admin trước G3)

1. **Nhận** phân bồ A1/A2/C/B/D/E như G2-1 này.
2. **226 place nhóm B** → chuyển cho **T22** làm worklist (gấp **4×** 55 row T22 đã có).
   Không làm trùng — T22 là chủ sở hữu, còn `in_progress`.
3. **13.336 place nhóm D** → ưu tiên **mở rộng regex** trước; LLM chỉ cho phần còn lại.
   Không cam kết số lượng trước khi đo regex mới.
4. **G3 không mở.** Không cần bảng DERIVED cho tới khi có ≥1 nguồn evidence mới.
5. Sửa `confidence` **trước khi** sinh row mới — xem G2-3.

---

## 8. Revert

Docs-only: `git revert --no-edit de114937 66b5ca2` (xoá 3 file `docs/T224_*.md`).
`data/t224_g0_measurements.json` additive — xoá file là đủ. **0 DB.**