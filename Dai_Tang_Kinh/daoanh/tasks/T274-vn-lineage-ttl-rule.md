---
id: T274
title: "Quy tắc riêng cho dòng Việt Nam: TTL đủ để gán NỐI PHÁP khi Marcus không có bản ghi tương ứng"
module: Lineage / Generation
priority: high
status: in_progress
created: 2026-10-10
owner: claude-code
parent: T270
done_when: >
  (1) Có nhánh gán nhãn mới 'noi_phap_ttl_only' trong scripts/t270_label_edges.py, chỉ áp dụng khi:
      Marcus KHÔNG có cạnh (teacher_id, disciple_id) tương ứng, TTL có dharma_flag=True cho
      cặp tên (ttl_confirmed=True), và cặp không mơ hồ (không trùng tên đồng danh phía DILA,
      không khớp >1 ứng viên TTL theo hậu tố) — tức là đã qua được mọi kiểm tra mơ hồ hiện có
      trước khi tới bước gán nhãn NỐI PHÁP/THAM HỌC.
  (2) Quy tắc cũ (cần cả TTL và Marcus) giữ nguyên áp dụng cho cạnh có Marcus — không đổi hành vi
      của nhãn 'noi_phap' hiện tại.
  (3) Chạy dry-run (không ghi DB) xuất docs/evidence/2026-10-10_T274_vn_dry_run.tsv với thống kê
      số cạnh mỗi nhóm nhãn + ước lượng số cạnh thuộc dòng Việt Nam.
  (4) Kiểm tay 10 mẫu noi_phap_ttl_only đối chiếu TTL, ghi đúng/sai.
  (5) Cập nhật tasktodo.md + dashboard (build_t263_status.py đọc checklist vào "plan4" +
      dashboard_process.html hiển thị plan4).
  (6) Admin xác nhận DONE — KHÔNG tự đánh DONE, KHÔNG ghi nhãn mới vào DB khi chưa có xác nhận.
revert: >
  Chưa ghi DB — không cần rollback DB. Thay đổi code có bản sao tại
  docs/sessions/2026-10-10/t270_label_edges.py.bak-before-T274 (và bản sao build_t263_status.py,
  dashboard_process.html nếu có sửa) — phục hồi bằng cách copy lại từ các bản .bak này.
  File dry-run là dẫn xuất, xóa để quay lại.
outcome: >
  2026-10-10: Bước 1-2 xong (code + dry-run, không ghi DB). Kết quả trên DB hiện tại:
  46.004 cạnh DILA; noi_phap (TTL+Marcus)=30; noi_phap_ttl_only (nhãn mới T274)=0;
  tham_hoc=24.212; mo_ho=21.755 (trong đó 8.201 Marcus thiếu bản ghi nhưng bị chặn ở
  bước mơ hồ trước khi tới nhãn mới); không ghép được=7. Nguyên nhân 0 kết quả: bộ lọc
  đồng danh/hậu tố (T270, giữ nguyên không đổi) rất nghiêm — gần 47% cạnh DILA rơi vào
  mo_ho vì tên pháp hiệu ngắn trùng nhiều ID DILA trong corpus lớn. Bước 3 (kiểm 10 mẫu)
  KHÔNG thực hiện được vì không có mẫu noi_phap_ttl_only nào để kiểm. Quy tắc đã cài đúng
  theo phê chuẩn Admin nhưng chưa có hiệu lực thực tế trên dữ liệu hiện tại.
  **PHÁT HIỆN 2026-10-11 (quan trọng):** Base pool DILA (46.004 cạnh `source_code='DILA' AND
  raw_relation_type='dila:teacher_of'`) **KHÔNG CHỨA** cạnh truyền thừa Việt Nam. Các cạnh
  Việt Nam nằm ở source TTL (`hasTeacher`/`hasDisciple`, ~1.300 cạnh), KHÔNG nằm trong base pool
  DILA. Quy tắc T274 được thiết kế để lọc trên base pool DILA (cạnh đã có DILA, thiếu Marcus)
  — nhưng cạnh Việt Nam KHÔNG CÓ trong base pool đó. Cần thiết kế lại: (a) mở rộng base pool
  để bao gồm cạnh TTL, hoặc (b) tách task riêng xử lý cạnh TTL → noi_phap_ttl_only.
  → Chưa ghi DB, chưa đánh DONE — chờ Admin quyết định hướng tiếp theo.

**PHÁT HIỆN 2026-10-11 (session Phase 2 analysis):** Kiểm toàn bộ task dependencies:
- Base pool DILA (46.004 cạnh `source_code='DILA' AND raw_relation_type='dila:teacher_of'`)
  **KHÔNG CHỨA** bất kỳ cạnh nào từ dòng Việt Nam.
- Cạnh Việt Nam nằm HOÀN TOÀN ở source TTL (hasTeacher/hasDisciple, ~1.300 cạnh),
  không có trong base pool DILA đang được T270 xử lý.
- T274 quy tắc được thiết kế để lọc cạnh trong base pool DILA, nhưng dữ liệu Việt Nam
  không ở đó → quy tắc không có hiệu lực thực tế.
- **CÁCH GIẢI QUYẾT TÙNG CHỌN:**
  (A) Mở rộng base pool để bao gồm cạnh TTL, sau đó T274 có ý nghĩa.
  (B) Tách task riêng để xử lý TTL edges → noi_phap_ttl_only (không dùng T274).
  (C) Dùng TTL trực tiếp làm source dành cho Việt Nam, bỏ qua T274 logic.
- **Status 2026-10-11:** Chờ Admin quyết định hướng A/B/C + resources (session mới)
---

# T274 — Quy tắc riêng dòng Việt Nam cho nối pháp (TTL-only khi Marcus thiếu)

> **Ghi chú 2026-10-15 (gộp file, điều phối Decision 6):** Trước đây có 2 file cùng id T274
> (`T274-vn-lineage-ttl-rule.md` — giai đoạn thiết kế quy tắc gốc; `T274-ttl-rule-design.md` —
> giai đoạn triển khai Option B). Đã gộp nội dung `T274-ttl-rule-design.md` vào mục
> "## 6. Design Phase — Option B (Unified DILA + TTL)" dưới đây và xoá file đó để hết trùng
> `dup:ids`. Nội dung chính (thiết kế quy tắc gốc, done_when, outcome ở trên) giữ nguyên.

## 1. Bối cảnh / Lý do

T270 đã chốt quy tắc: cạnh là NỐI PHÁP khi **cả TTL và Marcus cùng xác nhận**. Quy tắc này đúng
cho các dòng có bản ghi Marcus, nhưng Marcus **thiếu phần lớn dòng truyền thừa Việt Nam** —
nhiều cặp thầy-trò Việt Nam có TTL ghi rõ "pháp tự"/"đắc pháp" nhưng Marcus không có cạnh tương
ứng (không phải vì không nối pháp, mà vì Marcus chưa từng ghi nhận dòng này).

**Admin đã phê chuẩn (2026-10-10):** với dòng thầy-trò mà Marcus không có bản ghi, TTL là nguồn
đủ để gán NỐI PHÁP tự động khi ghi rõ "pháp tự"/"đắc pháp"/tương đương (tức dharma_flag=True
trong data/ttl_dharma_index.json), **miễn là cặp không mơ hồ** (tên không trùng nhiều người DILA
theo cả hai hướng kiểm tra đồng danh/hậu tố đã có trong t270_label_edges.py). Nếu có mâu thuẫn
hoặc tên trùng nhiều người DILA → đưa vào danh sách Admin xem (không tự gán).

Quy tắc cũ (cần cả TTL và Marcus) **giữ nguyên không đổi** cho dòng có bản ghi Marcus.

## 2. Điều kiện DONE

Xem `done_when` trong frontmatter. Tóm tắt: code chỉ sửa file (không ghi DB) → dry-run → kiểm 10
mẫu tay → báo Admin → chỉ ghi DB/đổi trạng thái DONE sau khi Admin xác nhận rõ ràng.

## 3. Các bước

- [x] **Bước 1 — Cập nhật quy tắc trong code**: thêm nhánh `noi_phap_ttl_only` vào
      `scripts/t270_label_edges.py` (không ghi DB). Backup trước vào
      `docs/sessions/2026-10-10/t270_label_edges.py.bak-before-T274`. `py_compile` sau khi sửa.
- [x] **Bước 2 — Chạy thử (đọc DB mode=ro)**: xuất
      `docs/evidence/2026-10-10_T274_vn_dry_run.tsv` — danh sách cạnh `noi_phap_ttl_only`, danh
      sách cạnh còn mơ hồ (`mo_ho`), và thống kê số cạnh mỗi nhóm + ước lượng số cạnh dòng Việt
      Nam. KHÔNG ghi DB.
- [ ] **Bước 3 — Kiểm 10 mẫu**: KHÔNG thực hiện được — `noi_phap_ttl_only` cho ra 0 cạnh trên
      DB hiện tại (xem outcome), nên không có mẫu nào để chọn/kiểm. Để mở, chờ Admin quyết định
      có cần rà soát sâu hơn danh sách `mo_ho` (8.201 cạnh Marcus thiếu bản ghi) hay không.
- [x] **Bước 4 — Dừng lại chờ Admin**: đã báo số liệu (không có mẫu để báo vì 0 kết quả). Không
      ghi nhãn vào DB, không đánh DONE. **Chờ Admin duyệt trước khi ghi nhãn vào DB.**
- [x] **Bước 5 — Tài liệu và dashboard**: cập nhật `docs/tasktodo.md` (block T274 giữa marker
      START/END, giữ lịch sử); sửa `scripts/build_t263_status.py` đọc checklist T274 vào khóa
      `plan4`, chạy lại; sửa `dashboard/dashboard_process.html` thêm danh sách `plan4` (backup
      trước, `node --check` sau khi sửa).

## 4. Ràng buộc

- Không ghi DB, không git, không xóa file dự án, không gọi API, không khởi server.
- Không đổi status của task khác. Không tự đánh DONE task này.
- Mọi file code sửa phải có bản sao trong `docs/sessions/2026-10-10/` trước khi sửa.

## 5. Liên quan

- T270 (`tasks/T270-nois-phap-ttl-marcus-consensus.md`) — quy tắc gốc TTL+Marcus.
- `data/ttl_dharma_index.json`, `data/dharma_edges.json` — dữ liệu dẫn xuất liên quan.
- T275 (`tasks/T275-ttl-anchor-generation.md`) — bị block bởi T274 (xem mục 6).

## 6. Design Phase — Option B (Unified DILA + TTL)

> Nội dung mục này gộp từ `tasks/T274-ttl-rule-design.md` (đã xoá, điều phối Decision 6,
> 2026-10-15) — giai đoạn triển khai tiếp theo sau khi phát hiện (mục "outcome" ở frontmatter,
> ghi 2026-10-11) rằng base pool DILA không chứa cạnh truyền thừa Việt Nam.

**Quyết Định Architecture.** Admin phê chuẩn: **Option B — Mở rộng DILA base pool để tích hợp
1.300 cạnh TTL dòng Việt** (thay vì tách task riêng hoặc dùng TTL độc lập — hai lựa chọn B/C nêu
ở outcome mục 5 trên).

**Case Demo — Lâm Tế Liễu Quán:**
- Liễu Quán = đệ tử Minh Hoàng Tử Dung (Lâm Tế Trung Quốc, từ DILA).
- Liễu Quán = khai tông hệ thống Liễu Quán tại Việt Nam (từ TTL).
- Kết quả mong đợi: Minh Hoàng → Liễu Quán → [Đệ tử Việt, USA] (thống nhất, không tách làm hai cây).

### Bước 1 — Rule TTL dòng Việt Nam

Input: `daoanh/data/sources/ttl_vietnam_edges.txt` (hoặc tương đương) — 1.300 cạnh
`hasTeacher`/`hasDisciple` từ TTL.

Rule: "Sư tổ Việt Nam" = monk xuất hiện trong TTL từ Khuôn Phổ trở xuống; Khuôn Phổ = pivot
point (có trong cả DILA + TTL); descendant của Khuôn Phổ (TTL) = dòng Việt; merge với DILA tại
Khuôn Phổ. Deliverable: `docs/Mimo-Flash/T274-ttl-rule-design-SPEC.md`.

### Bước 2 — Local ID cho 211 monk Việt

Schema change (cần Admin duyệt riêng trước khi chạy — chưa duyệt tại thời điểm viết mục này):
`ALTER TABLE marcus_people ADD COLUMN local_id TEXT UNIQUE;`

Naming convention: `vn_<name_slug>` (diacritics-free, lowercase, underscore). Ví dụ: Vạn Hạnh →
`vn_van_hanh`; Liễu Quán → `vn_lieu_quan`.

Mapping: với mỗi monk Việt trong 211 — nếu có `dila_id` thì `local_id = dila_id`; nếu không thì
sinh `local_id` mới và gán `source_id = 5` (ZQLOCAL) nếu chưa có. Deliverable:
`scripts/create_local_ids_for_vietnamese_monks.py` (tạo 211 local_id, verify unique, xuất CSV
mapping dila_id → local_id, name).

### Bước 3 — Xử lý 48 discrepancies (DILA vs TTL)

48 monk xuất hiện ở cả DILA + TTL, phân loại:

| Case | Số lượng ước tính | Chiến lược |
|---|---|---|
| Việt (TTL phù hợp hơn) | ~20 | TTL ưu tiên — merge/giữ cạnh TTL |
| Quốc tế (DILA phù hợp hơn) | ~15 | DILA ưu tiên — giữ cạnh DILA |
| Mơ hồ (cần Admin quyết) | ~13 | Ghi log, hỏi Admin — không tự gán |

Heuristic: `nation == "Vietnam"` → nguồn TTL, confidence 0,95; `nation` quốc tế → nguồn DILA,
confidence 0,95; còn lại → ghi log mơ hồ, không tự quyết. Deliverable:
`scripts/resolve_t274_discrepancies.py` → `docs/evidence/T274_discrepancies_resolved.csv` (48
dòng) + `docs/evidence/T274_discrepancies_ambiguous.csv` (nếu có).

### Bước 4 — TTL edge dataset để merge

Output: `data/processed/ttl_edges_for_dila_merge.json` — mỗi cạnh có `teacher_id`/`student_id`
(local_id hoặc dila_id), `source: "ttl"`, `confidence`, `evidence`. Metadata: tổng 1.300 cạnh,
48 discrepancies đã resolve.

### Tiêu chí hoàn thành mục 6

- Schema: cột `local_id` tạo xong, 211 monk có local_id (sau khi Admin duyệt ALTER TABLE).
- Rule document `T274-ttl-rule-design-SPEC.md` ghi rõ pivot + merge logic.
- `ttl_edges_for_dila_merge.json` sẵn sàng cho T275.
- 48 discrepancies resolved hoặc ambiguous (danh sách hỏi Admin).
- Verify: script pass lint/no import errors; CSV/JSON hợp lệ; không duplicate local_id; đủ 1.300
  cạnh TTL trong dataset.

### Blocked by / Blocks

- Không bị block (Admin đã quyết Option B).
- Block T275 (TTL Generation Engine) — chờ mục 6 hoàn tất.

### Timeline ước tính

Bước 1-2: ~1 ngày. Bước 3-4: ~1 ngày. Tổng ~1-2 ngày (có thể làm song song).
