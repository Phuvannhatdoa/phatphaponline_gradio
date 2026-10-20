# SOURCE AUTHORITY MATRIX — Ma trận Thẩm quyền Dữ liệu & Luật Trọng Tài (T115)

> **Ngày:** 2026-09-09 · **Task:** `tasks/T115-source-authority-matrix-referee.md`
> **Bảng nghiệp vụ tham chiếu:** `source_authority` (data/lineage.db — T68/T78) · **View:** `v_assertions`
> (JOIN `source_authority` → `authority_score`/`precedence_order`)
> **Trạng thái:** ✅ DONE — là tài liệu **luật** (docs-only), KHÔNG kèm code tự áp (xem §3).

---

## 1. MỤC TIÊU (OBJECTIVE)

Thiết lập **hệ phân cấp độ tin cậy nguồn** để xử lý tranh chấp dữ liệu (nhân vật/địa danh/khái niệm):

> **Luật Trọng Tài (Referee Principle):** khi hai nguồn mâu thuẫn (vd DILA vs Marcus), hệ thống
> **KHÔNG đếm phiếu** (theo số lượng nguồn) mà dùng **độ tin cậy** — `authority_score` (cao = đáng tin
> hơn) rồi tới `precedence_order` (nhỏ = ưu tiên hơn, **0-based**).

Tham chiếu đã có trong code từ T68: `app.py:_name_vi_evidence` — gom ứng viên tên Việt, **bỏ phiếu trọng
số theo authority_score** (không đếm phiếu). `v_assertions` JOIN `source_authority` trả
`authority_score`/`precedence_order` cho mọi claim.

## 2. CẤP ĐỘ NGUỒN (AUTHORITY LEVELS) — nhãn theo khoảng score

> ⚠️ Level là **nhãn trực quan** theo khoảng `authority_score`. **Luật quyết = score + precedence trực
> tiếp** (§3), KHÔNG tra bảng Level. Dải score thật trong DB: **100 → 25**.

| Level | Khoảng score | Màu | Ý nghĩa |
|---|---|---|---|
| **L1 — Primary** | **≥ 80** | Xanh lá | Chứng cứ trực tiếp: văn bản kinh chính (CBETA), kho học thuật chính thống (DILA) |
| **L2 — Scholarly** | **45 – 75** | Vàng | Nghiên cứu/diễn giải: Marcus (Bingenheimer), GRETIL *(chưa có — §5)*, Kanripo, data GIS học thuật, nội bộ admin-duyệt (ZQLOCAL)… |
| **L3 — Community/Reference** | **< 45** | Đỏ | Tham khảo: BDRC/FoJin (chưa activate), Wikidata — chỉ dùng khi không có nguồn L1/L2, luôn đánh dấu "cần kiểm chứng" |

## 3. LOGIC XỬ LÝ TRANH CHẤP (CONFLICT LOGIC)

Đối với 1 entity + 1 property, hai nguồn khác nhau đưa giá trị khác nhau:

1. **Score khác nhau** → source có `authority_score` cao hơn = **đề xuất ưu tiên (winner)** cho tầng hiển thị trọng tài.
2. **Score bằng nhau** → source có `precedence_order` nhỏ hơn (**0-based**) thắng **đề xuất**.
3. **Không phân thắng bại được** (tie score + tie order, hoặc hai nguồn cùng Level cao ngang nhau) → **KHÔNG tự quyết**: đẩy vào **Conflict Pool** (`lineage_conflicts_v2`, luồng Admin T109) + ghi `en_audit_log`.
4. **Bất kỳ đề xuất nào** đều ở mức "gợi ý cho UI/Admin" — **KHÔNG tự áp đặt dữ liệu**; giữ nghiêm điều lệnh **"KHÔNG tự quyết conflict (chỉ trình Admin)"** (T100/T109). Khi hiện thực hóa đề xuất tự động → ghi `editor='system:proposal'` vào `en_audit_log` (cần xác nhận schema trước khi code).
5. **Nguồn `implemented=0`** (chưa kích hoạt, theo T70/T112 §5) vẫn có score nhưng **không được dùng** cho đề xuất tới khi Admin kích hoạt.

## 4. BẢNG ÁNH XẠ 13 NGUỒN (thực trạng `source_authority`, data/lineage.db)

| source_code | authority_score | precedence_order (0-based) | implemented | Level | Legal (T78 §2) | Note |
|---|:---:|:---:|:---:|---:|---|---|
| **DILA** | 100 | 1 | 1 | **L1** | AUDITING | Nguồn chính thức địa danh Phật giáo |
| **CBETA** | 80 | 2 | 1 | **L1** | AUDITING | Tham chiếu kinh văn (Hán tạng) |
| **SAT** | 75 | 3 | 0 | L2 | UNKNOWN | Daizōkyō DB — chưa implement |
| **Kanripo** | 70 | 9 | 0 | L2 | UNKNOWN | Hán-Tạng critical editions — chưa implement (DEFER §5) |
| **MARCUS** | 60 | 4 | 1 | L2 | AUDITING | Glossary/Nets (Bingenheimer) — **diễn giải**, CC0 |
| **CHGIS** | 58 | 5 | 0 | L2 | UNKNOWN | Harvard GIS — chưa implement |
| **TGAZ** | 55 | 10 | 0 | L2 (GIS) | UNKNOWN | Harvard Gazetteer — chưa implement |
| **ZQLOCAL** | 50 | 0 | 1 | L2 (nội bộ) | AUDITING | Bản Việt nội bộ, tên do admin duyệt |
| **SuttaCentral** | 50 | 11 | 0 | L2 | UNKNOWN | Pali Canon — chưa implement (DEFER §5) |
| **84000** | 45 | 12 | 0 | L2 | UNKNOWN | Tạng Tây Tạng Toh — chưa implement (DEFER §5) |
| **BDRC** | 40 | 6 | 0 | L3 | UNKNOWN | Kho số hóa Tây Tạng — chưa implement (BLOCK §5) |
| **FoJin** | 40 | 7 | 0 | L3 | UNKNOWN | 佛典 — chưa implement (BLOCK §5) |
| **Wikidata** | 25 | 8 | 0 | **L3** | CC0 (cần verify) | **REFERENCE_ONLY** (§5 T112) — chỉ tham khảo ngoài |

> Ghi chú: **DILA=1 · CBETA=2 … 84000=12** là `precedence_order` **0-based** (ZQLOCAL=0 đứng đầu vì nội bộ).
> 4 nguồn `implemented=1` (DILA/CBETA/MARCUS/ZQLOCAL) · 9 nguồn `implemented=0` (cả Wikidata — dù có dữ liệu
> historical, "5 nguồn historical-ingested" kể Wikidata). Xem đối chiếu đầy đủ: `SOURCE_REGISTRY.md` §6.

## 5. CHUẨN TÊN NGUỒN (tránh nhầm)

- **GRETIL** (Göttingen) **CHƯA thuộc** danh sách 13 nguồn repo — muốn dùng phải đi qua T78 `source-add`
  (Legal Check, `integration_mode`, audit), không tự thêm vào matrix.
- **Wikipedia ≠ Wikidata**: hệ thống dùng **Wikidata** (CC0 — cần xác minh, role REFERENCE_ONLY theo §5 T112).
  Không nhập Wikipedia làm nguồn chứng cứ.
- **ZQLOCAL = bản Việt nội bộ** (tên do Admin duyệt, corpus từ DILA local) — giữ score riêng 50, không gộp
  với DILA 100.
- Level 2 đặc biệt: dữ liệu **GIS học thuật** (CHGIS/TGAZ) gắn nhãn L2-GIS nhưng **BLOCK** (redistribution
  chưa rõ, §5 T112) — nhãn Level KHÔNG đồng nghĩa "được ingest".

## 6. PHẠM VI (SCOPE)

- **docs-only trong task này:** 0 ETL, 0 ALTER/DROP, 0 code mới. Score/precedence trong DB **giữ nguyên**.
- Mọi thay đổi score/phân cấp sau này: **Lee Tổng phải duyệt** trước, kèm ROLLBACK row.
- Tự động phân thắng bại (áp winner) là **code mới** — nếu chốt, lập task riêng mirror T111 (gating + log
  `editor='system:proposal'`), KHÔNG làm trong task docs này.