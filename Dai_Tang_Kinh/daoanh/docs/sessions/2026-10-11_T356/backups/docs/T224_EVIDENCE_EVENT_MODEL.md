---
task: tasks/T224-geo-spatial-timeline-founding-phase2.md
report: G2-3 EVIDENCE_EVENT_MODEL
title: "Evidence/Event Model — hiện trạng place_timeline_events và khoảng trống"
status: ready-for-admin-review
created: 2026-10-04
measured_at: 2026-10-04
db: data/lineage.db (read-only)
---

# T224 · G2-3 — Evidence / Event Model

**Mục đích:** mô tả đúng **event đang có** và **evidence thật sự đi kèm**, để quyết
định có cần bảng `place_timeline_evidence` (DERIVED) như plan G3 dự tính hay không.

> **Kết luận trước:** dữ liệu hiện tại **chưa đủ cơ sở** để dựng bảng evidence. Lý do
> cụ thể ở §3–§5.

---

## 1. Schema hiện tại

`place_timeline_events` — **3.688 rows**, 11 cột:

| Cột | Kiểu | Fill rate | Ghi chú |
|---|---|---:|---|
| `id` | INTEGER | — | PK |
| `dila_id` | TEXT | 100% | ⚠️ **không có FK** tới `places_dila.id` |
| `event_type` | TEXT | 100% | 2 giá trị: `founding` 3.647 · `dissolved` 41 |
| `year` | INTEGER | 100% | |
| `year_end` | INTEGER | **0%** | 🔴 **cột chưa từng dùng** |
| `label_zh` | TEXT | 99,97% | |
| `label_vi` | TEXT | **1,0%** (36/3.688) | 🔴 gần như trống |
| `source` | TEXT | 100% | 8 nguồn |
| `source_ref` | TEXT | 100% | ⚠️ xem §3 |
| `confidence` | TEXT | 100% | 🔴 xem §4 |
| `created_at` | TEXT | — | |

**Index:** `idx_pte_dila(dila_id)` · `idx_pte_source(source)`
**FK:** ❌ **không có** — `dila_id` chỉ *tình cờ* khớp 3.688/3.688 với `places_dila.id`.
Query sai cột sẽ lỗi `no such column` (đã gặp ở T201: `places_dila` có PK `id`,
**không** có cột `dila_id`).

---

## 2. Phân bố nguồn × loại event

| `source` | `founding` | `dissolved` | Tổng | Loại evidence |
|---|---:|---:|---:|---|
| `dila_era_name` | 1.471 | 0 | 1.471 | suy luận |
| `dila_dynasty` | 851 | 0 | 851 | suy luận |
| `dila_note` | 719 | 0 | 719 | suy luận |
| `dila_note_regex` | 276 | 0 | 276 | suy luận |
| `dila_founding_phase2` | 55 | 0 | 55 | suy luận |
| `dila_fosizhi` | 15 | 0 | 15 | ngoài |
| `wikidata_p571` | 146 | 0 | 146 | **ngoài + QID** |
| `wikidata` | 114 | **41** | 155 | **ngoài + QID** |

⇒ **3.327 / 3.688 = 90,2%** event là **suy luận từ text**, không phải dữ liệu gốc.

---

## 3. 🔴 `source_ref` — 90% **không phải** con trỏ evidence

| Dạng | Số | Đánh giá |
|---|---:|---|
| QID thật (`Q\d+`) | **301** | ✅ dùng được |
| URL (`http…`) | **0** | ⚠️ không URL nào |
| Tự tham chiếu (`source_ref = source`) | **55** | 🔴 **vô nghĩa** |
| **Breadcrumb nội bộ** (`PL…·note·regex`) | **3.332** | 🔴 không phải evidence |

Mẫu breadcrumb: `PL000000000184·note·regex`

⇒ `source_ref` **không trỏ ra ngoài**. Nó chỉ ghi "row này đến từ regex trên note của
place X". Muốn kiểm chứng phải **quay lại `raw_xml`/`note`** — tức evidence **không
tự chứa, không đóng**, và không có phiên bản đóng băng.

⚠️ 3.332 breadcrumb có nghĩa là **đổi `note` là mất đường truy vết** của event đã có.

---

## 4. 🔴 `confidence` — 1 cột, 2 hệ, 16 giá trị

| Hệ | Giá trị | Số |
|---|---|---:|
| **Nhãn ngữ nghĩa** | `dynasty_range` | 844 |
| | `era_name_exact` | 764 |
| | `regex_note` | 714 |
| | `era_name_midpoint` | 707 |
| | `verified` | 122 |
| **Điểm số** | `0.85` | 194 |
| | `0.88` | 117 |
| | `0.75` | 69 |
| | `0.9` | 55 |
| | `0.90` | 27 |
| | `0.7` | 26 |
| | `0.72` | 25 |
| | `0.8` | 11 |
| | `0.5` | 7 |
| | `0.616` | 5 |
| | `0.595` | 1 |

🔴 **Vấn đề gốc:** cột `confidence` đang lưu **hai thứ khác nhau** — *phương pháp suy
luận* (`era_name_exact`) lẫn *độ tin cậy* (`0.85`). Không tách được bằng SQL
(`WHERE confidence > 0.8` sẽ **bỏ sót** 2.337 row nhãn, và `WHERE confidence = 'verified'`
lọc sai nghĩa).

Ngoài ra `0.9` và `0.90` **cùng giá trị, khác chuỗi** — 2 nhóm tách phát sinh từ 2 script.

**Hệ quả cho plan cũ:** ràng buộc *"mọi row NLP = `confidence='candidate'`"* (đã bỏ khỏi
T224) sẽ **làm hỏng** 3.327 row hiện có và trộn thêm hệ thứ ba.

**Đề xuất (additive, chưa làm):**
- Cột mới `evidence_method` ← chuyển 5 giá trị nhãn sang.
- Cột mới `confidence_score REAL` ← chuyển 11 giá trị số sang (`0.90` → `0.9` khi migrate).
- `confidence` cũ giữ nguyên, đánh dấu deprecated.
- **Không** `ALTER`/`UPDATE` bảng gốc (T82 freeze).

---

## 5. 🔴 Lỗi chất lượng ở T22 — ghi nhận, **không** sửa ở đây

**55/55 row** `source='dila_founding_phase2'`:

| Trường | Giá trị | Vấn đề |
|---|---|---|
| `label_vi` | **rỗng 55/55** | T22 khai `label_vi` trong schema ⇒ vi phạm schema của chính nó |
| `label_zh` | tên chữ Hán của place | không phải nhãn sự kiện |
| `source_ref` | `= dila_founding_phase2` (tự tham chiếu) | vô nghĩa |

`label_vi` chỉ **1,0%** trong toàn bảng — phần lớn nằm đúng ở 55 row này.

**Ai sửa:** **T22** (`in_progress`, chủ sở hữu `places_dila.note` pipeline).
**T224 không đụng** — chỉ ghi nhận để tránh làm trùng.

---

## 6. Vì sao **chưa** dựng bảng `place_timeline_evidence`

Plan G3 dự tính bảng DERIVED `place_timeline_evidence`. Dữ liệu hiện tại **chưa đủ cơ sở**:

| Điều kiện cho bảng evidence | Hiện trạng |
|---|---|
| Mỗi event có con trỏ evidence bên ngoài | ❌ 90,2% là breadcrumb nội bộ |
| Độ tin cậy tách được khỏi phương pháp | ❌ 1 cột, 16 giá trị, 2 hệ |
| Khoá ngoại về place | ❌ không FK |
| Lịch sử bằng chứng đóng băng | ❌ không có |
| `label_vi` | ❌ 1,0% |

**Đề xuất: hoãn.** Xây bảng evidence bây giờ sẽ chỉ **sao chép** 90% breadcrumb — tức
một bảng evidence **không có evidence**.

### Điều kiện mở lại (tất cả phải đạt)

1. `evidence_method` + `confidence_score` tách cột (additive).
2. `source_ref` phân loại được: `qid` | `url` | `internal` | `self_ref`.
3. Có **≥1 nguồn ngoài mới** thật (CHGIS/TGAZ/BDRC — cần license, xem G2-2 §3).
4. Thêm FK hoặc guard khi ETL ghi.
5. **HITL** có `reviewed_by` + `reviewed_at`.

---

## 7. Việc nên làm ngay (rẻ, không cần G3)

| # | Việc | Chi phí | Rủi ro |
|---|---|---|---|
| 1 | Phân loại `source_ref` thành 4 loại — **chỉ đọc + báo cáo** | rẻ | 0 |
| 2 | Báo cáo `confidence`: 5 nhãn + 11 số, tách 2 cột ở **bảng view/CSV** | rẻ | 0 (không ALTER) |
| 3 | Báo cáo 3.688 event theo `dila_id` × nguồn, tìm event trùng năm | rẻ | 0 |
| 4 | Gửi T22: 55 row `label_vi` rỗng | 0 | 0 |

**Không** tạo bảng, **không** `ALTER`, **không** `UPDATE` cho tới khi Admin duyệt mục §6.

## 8. Revert

Docs-only: `git revert --no-edit <sha>`. **0 DB.**