---
task: T379 (rebuild-gen-tables follow-up)
title: "Thiết kế: cho phép ID nội bộ (TTL_LOCAL / vn_person_authority slug) làm đầu cạnh trong lineage_edge_consensus"
status: design_only — CHƯA THỰC HIỆN
worktree: wt/t379-rebuild-gen-tables (HEAD 693aba62 lúc viết doc)
author: daoanh-debugger (agent), theo yêu cầu trực tiếp Admin qua chat 2026-11-07
scope: CHỈ thiết kế — KHÔNG ghi DB, KHÔNG đổi schema, KHÔNG commit code ở bước này.
next_step: Admin duyệt phương án (đặc biệt mục 1 và 2) rồi mới giao daoanh-debugger implement trong worktree này.
---

# Thiết kế: namespace (ns) cho `lineage_edge_consensus`

## 0. Lưu ý quan trọng — đối chiếu số liệu trước khi đọc tiếp

Prompt giao việc nêu **"399 cạnh cũ dùng slug VN bị chặn ở tầng thiết kế"**. Đo trực
tiếp trên `data/lineage.db` hiện tại (2026-11-07) cho thấy con số 399 đã **có ý
nghĩa khác** trong lịch sử, và số cạnh **đang thực sự bị chặn hôm nay nhỏ hơn**:

| Mốc | Ý nghĩa | Nguồn |
|---|---|---|
| **399** (T381 Decision 5, 2026-10-15) | Cạnh TTL **đã crosswalk được cả 2 đầu sang DILA id** (qua `vn_person_authority.dila_id`) nhưng chưa có dòng trong `lineage_edge_consensus` → đã **INSERT xong** 393/399 (6 bị bỏ do self-loop/reversed-duplicate). Đây là `consensus_status='ttl_only'`, `migration_marker='T381_TTL_ONLY_INSERT_20261015'`, **vẫn dùng DILA id**, không phải slug. | `scripts/t381_insert_ttl_only_edges.py`, đo lại: `SELECT COUNT(*) FROM lineage_edge_consensus WHERE consensus_status='ttl_only'` → **393** hôm nay. |
| **231** (đo lại hôm nay, 2026-11-07) | Cạnh trong `dharma_lineage_ttl_vn` (784 dòng) **không crosswalk được sang DILA** cho ít nhất 1 đầu — đây mới là nhóm **thật sự bị chặn** vì bảng chỉ nhận DILA id: `mismatch_teacher`=101, `mismatch_student`=128, `empty_teacher_slug`=2 (2 dòng này không có thầy — khai tổ gốc, không phải lỗi thiết kế ns, xem §7). | Chạy lại `classify_ttl_edges()` trong `scripts/t381_etl_ttl_into_consensus.py` trên `data/lineage.db` hiện tại. |

**Kết luận:** thiết kế dưới đây giải quyết nhóm **231 cạnh thật sự bị chặn** (không
phải 399). Số 399 trong prompt nhiều khả năng là tham chiếu nhầm sang báo cáo T381
cũ (đã DONE, dùng DILA id, không liên quan ns). Đề nghị Admin xác nhận lại nguồn số
399 nếu có một phép đo khác ngoài 2 phép đo trên — doc này **không tự suy diễn**
thêm, chỉ báo cáo đúng số đo được.

---

## 1. Quy ước định danh (ns + key)

### Hiện trạng

```sql
CREATE TABLE lineage_edge_consensus (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id           TEXT NOT NULL,   -- luôn 'A######' (DILA) hôm nay, 23.411/23.411 dòng
    disciple_id          TEXT NOT NULL,   -- luôn 'A######' (DILA) hôm nay
    relation_type        TEXT NOT NULL DEFAULT 'dharma_transmission',
    ...
    UNIQUE(teacher_id, disciple_id, relation_type)
);
```

Đo thực tế: **23.411/23.411 dòng** có `teacher_id` và `disciple_id` bắt đầu bằng
`'A'` (DILA) — 100%, xác nhận giả định "chỉ nhận DILA id" trong prompt là đúng.

### Hai phương án

**Phương án A — thêm cột `teacher_ns` / `disciple_ns`, giữ `teacher_id`/`disciple_id` là key thô (slug hoặc DILA code), KHÔNG đổi ý nghĩa cột cũ.**

```sql
ALTER TABLE lineage_edge_consensus ADD COLUMN teacher_ns TEXT NOT NULL DEFAULT 'DILA';
ALTER TABLE lineage_edge_consensus ADD COLUMN disciple_ns TEXT NOT NULL DEFAULT 'DILA';
```

- `teacher_ns`/`disciple_ns` ∈ {`'DILA'`, `'TTL_LOCAL'`} (đúng 2 nguồn đang có theo
  `entity_source_ids.source`; không mở rộng thêm nguồn nào khác ở bước này).
- `teacher_id` khi `ns='DILA'` = DILA code (`A######`, khớp `people.id`).
- `teacher_id` khi `ns='TTL_LOCAL'` = slug (khớp `vn_person_authority.id`, ví dụ
  `minh_hai_phap_bao`).
- 23.411 dòng hiện có: `teacher_ns`/`disciple_ns` nhận **default `'DILA'`** qua
  `ALTER TABLE ... DEFAULT`, không cần UPDATE — tự động đúng vì 100% dòng cũ là DILA.

**Ưu điểm:**
- Additive thuần: không sửa giá trị cột cũ, không cần backfill UPDATE (rủi ro ghi
  sai = 0 vì SQLite `ADD COLUMN ... DEFAULT` áp cho mọi dòng hiện có tại thời điểm
  ALTER, không cần UPDATE riêng).
- Mọi câu SELECT cũ (`SELECT teacher_id, disciple_id FROM ...`, `WHERE teacher_id=?`)
  **vẫn đúng y nguyên** vì không đổi kiểu dữ liệu/giá trị cột đó — chỉ các chỗ cần
  phân biệt nguồn mới phải sửa thêm `ns`.
- `teacher_id`/`disciple_id` tiếp tục là chuỗi "tự nhiên" (DILA code hoặc slug), dễ
  đọc log/debug, khớp trực tiếp với `people.id` hoặc `vn_person_authority.id` không
  cần strip prefix.

**Nhược điểm:**
- Hai bảng khác nhau có thể trùng giá trị string ở `teacher_id` một cách tình cờ
  (ví dụ DILA code viết thường trùng 1 slug) — rủi ro lý thuyết, chưa gặp thực tế vì
  DILA code luôn dạng `A\d{6}` còn slug luôn chữ thường + `_`, nhưng vẫn nên validate
  ở tầng ETL (xem §4) để không dựa vào "may mắn không trùng định dạng".
- Code đọc bảng mà **quên** thêm điều kiện `ns` khi join sang bảng khác (ví dụ join
  `people.id = teacher_id` mà không check `teacher_ns='DILA'`) sẽ join nhầm nếu
  tương lai có slug trùng định dạng DILA — hôm nay an toàn vì định dạng khác hẳn,
  nhưng là nợ kỹ thuật cần ghi rõ trong code mới (xem §3).

**Phương án B — gộp ns vào chính `teacher_id`/`disciple_id` (ví dụ `'TTL_LOCAL:minh_hai_phap_bao'` vs `'A000005'`).**

**Ưu điểm:**
- Không cần thêm cột, không đổi `UNIQUE` constraint.
- Không có rủi ro string trùng định dạng giữa 2 namespace (prefix tách biệt tuyệt đối).

**Nhược điểm (quyết định loại phương án này):**
- **Phá mọi câu SQL cũ** dùng `teacher_id`/`disciple_id` để join trực tiếp với
  `people.id` (DILA) — 100% chỗ gọi hiện tại (app.py, `etl_gen_compute.py`,
  `etl_t187_primary_teacher.py`, …) đều giả định giá trị là DILA code thô, phải sửa
  **tất cả** để strip prefix trước khi join → vi phạm "fix nhỏ nhất", rủi ro
  regression cao hơn nhiều so với phương án A.
- `_t158_neighbors_consensus` trả `id` thẳng ra API JSON cho frontend
  (`places.html`) dùng làm `dila_id` trong URL (`/daoanh/api/monk/<dila_id>/...`) —
  gộp prefix vào id sẽ lộ ra URL/UI, phải thêm bước strip ở mọi lớp (API, frontend)
  thay vì chỉ ở lớp đọc DB.
- Đảo ngược được (migration-wise) khó hơn: phương án A chỉ cần `DROP COLUMN`
  (AGENTS.md §14, additive-revert), phương án B phải sửa lại giá trị string của
  toàn bộ dòng mới thêm.

### Khuyến nghị: **Phương án A**

Lý do tóm tắt: additive thật (không sửa dữ liệu cũ), không phá bất kỳ câu SQL nào
hiện có (chỉ *thêm* điều kiện ở nơi cần phân biệt nguồn), revert bằng `DROP COLUMN`
theo đúng quy tắc AGENTS.md §14. Rủi ro duy nhất (string trùng định dạng) được chặn
bằng validate ở ETL insert, không cần đổi thiết kế.

### UNIQUE constraint mới

Constraint cũ `UNIQUE(teacher_id, disciple_id, relation_type)` **phải đổi** vì nếu
không, một cạnh DILA `A000005 -> A003958` và một cạnh TTL_LOCAL tình cờ có slug
trùng ký tự `A000005 -> A003958` (không xảy ra hôm nay do định dạng khác, nhưng
không được dựa vào giả định đó ở tầng constraint) sẽ bị SQLite coi là trùng khóa.

SQLite không hỗ trợ `ALTER TABLE ... ADD CONSTRAINT` hay `DROP CONSTRAINT` — phải
tạo lại UNIQUE bằng **index UNIQUE riêng** (không cần rebuild table):

```sql
-- Composite UNIQUE index thay cho UNIQUE constraint cũ (bảng giữ nguyên, không rebuild)
CREATE UNIQUE INDEX IF NOT EXISTS uq_lec_ns_key
    ON lineage_edge_consensus(teacher_ns, teacher_id, disciple_ns, disciple_id, relation_type);
```

Lưu ý: UNIQUE constraint **gốc** (`sqlite_autoindex_lineage_edge_consensus_1` trên
`(teacher_id, disciple_id, relation_type)`) vẫn tồn tại song song (không DROP được
dễ dàng trên PRIMARY KEY autoindex của SQLite mà không rebuild bảng) — **đây là
điểm cần Admin lưu ý**: hai edge cùng `(teacher_id, disciple_id, relation_type)`
nhưng khác `ns` (ví dụ DILA `A000005->A003958` và TTL_LOCAL slug trùng ký tự, dù
chưa xảy ra) **vẫn bị chặn bởi constraint cũ** cho tới khi rebuild bảng (DROP+CREATE
+ copy data, không additive). Vì xác suất trùng ký tự giữa 2 định dạng khác nhau
bằng 0 trong thực tế hiện tại, đề xuất **giữ nguyên constraint cũ, không rebuild
bảng** ở bước này — chỉ thêm index UNIQUE mới cho ns, và ghi rõ hạn chế này để Admin
quyết nếu muốn rebuild bảng (ngoài phạm vi "additive" nên cần duyệt riêng).

---

## 2. Migration additive (DDL dự kiến — CHƯA CHẠY)

```sql
-- Bước 1: thêm 2 cột ns, default 'DILA' (áp cho toàn bộ 23.411 dòng hiện có)
ALTER TABLE lineage_edge_consensus ADD COLUMN teacher_ns TEXT NOT NULL DEFAULT 'DILA';
ALTER TABLE lineage_edge_consensus ADD COLUMN disciple_ns TEXT NOT NULL DEFAULT 'DILA';

-- Bước 2: index UNIQUE mới bao gồm ns (xem §1 vì sao không DROP constraint cũ)
CREATE UNIQUE INDEX IF NOT EXISTS uq_lec_ns_key
    ON lineage_edge_consensus(teacher_ns, teacher_id, disciple_ns, disciple_id, relation_type);

-- Bước 3 (khuyến nghị, không bắt buộc): index phục vụ lookup theo ns riêng
-- (giúp query "chỉ lấy cạnh TTL_LOCAL để review" nhanh hơn full scan)
CREATE INDEX IF NOT EXISTS idx_lec_teacher_ns ON lineage_edge_consensus(teacher_ns, teacher_id);
CREATE INDEX IF NOT EXISTS idx_lec_disciple_ns ON lineage_edge_consensus(disciple_ns, disciple_id);
```

**KHÔNG có bước UPDATE** — toàn bộ 23.411 dòng cũ nhận giá trị đúng (`'DILA'`) ngay
từ `DEFAULT`, không cần (và không nên) chạy `UPDATE ... SET teacher_ns='DILA'` vì
rủi ro ghi nhầm > 0 trong khi `ADD COLUMN DEFAULT` rủi ro ghi nhầm = 0 (SQLite tự
làm, không qua code của ta).

### Kiểm tra số dòng trước/sau (bắt buộc chạy, --dry-run trước)

```sql
-- TRƯỚC migration
SELECT COUNT(*) FROM lineage_edge_consensus;                              -- kỳ vọng 23411
SELECT COUNT(*) FROM lineage_edge_consensus WHERE teacher_id LIKE 'A%';   -- kỳ vọng 23411

-- SAU migration (ALTER TABLE xong, chưa insert gì mới)
SELECT COUNT(*) FROM lineage_edge_consensus;                              -- PHẢI vẫn = 23411
SELECT COUNT(*) FROM lineage_edge_consensus WHERE teacher_ns='DILA' AND disciple_ns='DILA';  -- PHẢI = 23411
SELECT COUNT(*) FROM lineage_edge_consensus WHERE teacher_ns!='DILA' OR disciple_ns!='DILA'; -- PHẢI = 0
```

Script migration nên theo đúng khuôn mẫu `scripts/t158_consensus_migration.py` /
`scripts/t425_add_columns_and_views.py` đã có trong repo (cùng pattern
`--dry-run` mặc định, `--apply` mới ghi DB, backup tự động, `PRAGMA quick_check`
sau commit) — không viết lại pattern mới.

### Rebuild badge/consensus_status?

**Không cần.** `teacher_ns`/`disciple_ns` không tham gia công thức
`agreeing_source_count`/`consensus_status`/`source_badge` (công thức đó dựa trên
`dila_asserted/marcus_asserted/ttl_asserted/lineage_asserted`, không liên quan ns).
Thêm cột ns không làm sai badge của 23.411 dòng cũ.

---

## 3. Nơi đọc `lineage_edge_consensus` — có cần sửa không

Grep `lineage_edge_consensus` trong code sống (loại trừ `docs/sessions/**` là bản
backup lịch sử, không phải code đang chạy):

| File:dòng | Việc gì | Cần sửa vì ns mới? |
|---|---|---|
| `app.py:6491,6504` (`_t158_neighbors_consensus`) | `SELECT c.teacher_id AS id, ... FROM lineage_edge_consensus c WHERE c.disciple_id=?` / `WHERE c.teacher_id=?` | **Không bắt buộc để chạy được** (cột cũ không đổi ý nghĩa) nhưng **nên thêm `ns` vào SELECT** để response trả `source_type`/`ns` cho frontend badge (xem §4). Không sửa thì cạnh TTL_LOCAL vẫn trả về đúng nhưng frontend không biết để hiện badge khác màu. |
| `app.py:7268,7302,7303,7349,7350` (`_t86_person_info`, `_t86_origin_place` gọi trong `api_monk_lineage_tree`) | Resolve `nid` (có thể là slug TTL_LOCAL) → tên hiển thị | **PHẢI sửa.** `_t86_person_info` (app.py:6395-6441) đã có cơ chế fallback `ttl_persons` (T186) với `source_type='ttl_local'` — nhưng bảng `ttl_persons` **không tồn tại** trong `data/lineage.db` thật (xác nhận bằng try/except `sqlite3.OperationalError 'no such table'` ở app.py:6408-6416 và 7260-7265). Cần đổi fallback từ `ttl_persons` sang `vn_person_authority` (bảng đang có 1.512 dòng, đủ field `name_vi/name_zh/dharma_title/bio`). Đây là **điểm sửa chính của resolver**, không phải lỗi mới do ns — là lỗ hổng đã có từ T186, ns mới khiến nó lộ ra vì giờ mới có cạnh thật trỏ tới slug. |
| `app.py:7253-7267` (center node exists check) | `SELECT 1 FROM people WHERE id=?` rồi fallback `ttl_persons` | **PHẢI sửa tương tự** — đổi fallback sang `vn_person_authority WHERE id=?` để route `/daoanh/api/monk/<slug>/lineage-tree` nhận được slug làm center. |
| `app.py:7710,7722,7734` (BFS ngược lên tìm root — hàm khác, dòng ~7710) | `SELECT teacher_id FROM lineage_edge_consensus WHERE disciple_id=?` (trace to root) | Không bắt buộc sửa ngay — nếu BFS đi tới node TTL_LOCAL, vòng lặp vẫn chạy đúng (dict key là string, không quan tâm định dạng); chỉ cần `_t86_person_info` ở noi gọi hiển thị kết quả đã resolve đúng tên là đủ. |
| `scripts/etl_gen_compute.py:309` (`build_children`) | `SELECT teacher_id, disciple_id FROM lineage_edge_consensus` → dict BFS tính đời (gen) | **Nên sửa** (không bắt buộc để không crash). Dòng 289 cùng file có heuristic `not pid.startswith('A')` để lọc id non-DILA khi ghi `person_gen_computed` — đây là cách cũ "đoán theo hình dạng string". Khi có `ns` tường minh, nên đổi sang check `ns != 'DILA'` thay vì `startswith('A')` để không phụ thuộc hình dạng string (rebuild-gen-tables đang là trọng tâm của worktree này — nên làm cùng lúc, không tách task riêng). |
| `scripts/etl_t187_primary_teacher.py:150` | `SELECT ... FROM lineage_edge_consensus` để tính thầy chính (`lineage_primary_teacher`) | Không bắt buộc — bảng `lineage_primary_teacher` join bằng `(teacher_id, disciple_id)` thô, TTL_LOCAL edge không có dòng `is_primary` tương ứng thì `COALESCE(lpt.is_primary,0)` trả 0 (mặc định), không crash. Nên thêm sau nếu Admin muốn TTL_LOCAL edges cũng có is_primary. |
| `scripts/t158_consensus_migration.py` | Tạo bảng (migration gốc, đã chạy xong từ T158) | Không sửa — migration lịch sử, không chạy lại. |
| `scripts/t381_etl_ttl_into_consensus.py`, `scripts/t381_insert_ttl_only_edges.py` | ETL cũ (T381, đã DONE) — crosswalk slug→DILA rồi mới insert/update bằng DILA id | Không sửa — các script này **cố tình** chỉ nhận cạnh đã crosswalk được sang DILA (xem §0). Vẫn giữ nguyên làm đường ETL cho nhóm 553 cạnh matched; ns là đường ETL **mới, bổ sung** cho nhóm 231 cạnh không matched, không thay thế 2 script này. |
| `scripts/etl_ttl_full_import.py:402-570`, `scripts/etl_ttl_persons.py:266-340` | ETL cũ hơn (T186), update `ttl_asserted`/insert TTL-only edges, legacy | Không sửa trong phạm vi task này — 2 script legacy, không rõ còn được chạy định kỳ hay không (cần Admin xác nhận trước khi đụng). Ghi nhận: `etl_ttl_persons.py` dòng 22 có comment `DELETE FROM lineage_edge_consensus WHERE source_marker='TTL_VN_ONLY'` nhưng cột `source_marker` **không có trong schema thật** — comment đã lạc hậu, không phải bug của thiết kế ns mới. |
| `scripts/t425_add_columns_and_views.py:186-201` | So sánh overlay (từ `lineage_edge_assertions`) vs `lineage_edge_consensus`, chỉ đọc, phục vụ QA | Không sửa — script chẩn đoán, không chạy production. |
| `scripts/_t410_probe_ids.py` | Probe đọc, debug script | Không sửa. |
| `tests/test_t158_consensus.py:16` | Test tồn tại bảng + cấu trúc | **Nên thêm test mới** (không sửa test cũ) cho `teacher_ns`/`disciple_ns` default + UNIQUE index mới, theo đúng tinh thần "test case yêu cầu + edge case" ở AGENTS. |
| `admin/*.html`, `api_*.py`, `src_python/**` | — | **Không có kết quả grep nào** khớp `lineage_edge_consensus` hoặc trực tiếp `teacher_id`/`disciple_id` của bảng này (`api_ttl_*.py` dùng `marcus_networks`, bảng khác). Không cần sửa. |

**Tổng kết phạm vi sửa khi implement (ngoài phạm vi doc này, chỉ để Admin thấy
trước kích thước việc):** 2 chỗ PHẢI sửa (resolver `_t86_person_info` +
center-exists check trong `app.py`, ~4 điểm nối liền nhau, cùng 1 hàm/route), 1 chỗ
NÊN sửa cùng lúc (`etl_gen_compute.py`, vì cùng worktree rebuild-gen-tables), còn
lại không bắt buộc.

**Liên quan nhưng NGOÀI PHẠM VI task này:** `lineage_edge_assertions` (bảng khác,
cột `subject_person_id`/`object_person_id`) cũng chỉ nhận DILA id, được 4 VIEW T425
(`v_tree_dila/marcus/ttl/overlay`) đọc. Nếu sau này Admin muốn cạnh TTL_LOCAL cũng
hiện trong tab "Cây TTL" (`?trees=ttl`), sẽ cần thiết kế ns tương tự cho bảng đó —
**không nằm trong doc này**, ghi nhận làm follow-up riêng.

---

## 4. Quy tắc cho cạnh TTL_LOCAL

- **Trạng thái mặc định khi insert:** `is_default_visible=0` (giống `ttl_only` của
  T381) — **không** tự động hiện trong cây mặc định cho tới khi Admin duyệt.
- **consensus_status riêng:** đề xuất giá trị mới `'ttl_local_candidate'` (khác
  `'ttl_only'` của T381 vì T381 `ttl_only` đã có DILA id hợp lệ ở cả 2 đầu, còn
  nhóm này có đầu là slug chưa xác minh — cần phân biệt rõ để không trộn 2 quy
  trình review khác nhau).
- **Không tính vào đếm đời tự động** (`person_gen_computed`) cho tới khi
  `vn_person_authority.status` của **cả 2 đầu** slug liên quan đạt `'verified'`
  (không phải `'auto_ttl'`/`'alias_vi_suffix'`/`'alias_zh_match'`/`'pending'`) HOẶC
  Admin duyệt thủ công qua cột `human_override` (cột đã có sẵn trong bảng, dùng
  đúng mục đích gốc, không thêm cột mới). `etl_gen_compute.py` cần thêm điều kiện
  lọc `consensus_status != 'ttl_local_candidate' OR human_override='approved'` khi
  build BFS children map.
- **Hiển thị nhãn nguồn trên cây:** tái dùng field `source_type` đã có sẵn trong
  response của `_t86_person_info` (giá trị `'ttl_local'`) — chỉ cần sửa fallback
  trỏ đúng `vn_person_authority` (xem §3) là badge "Danh tăng VN – TTL local" (đã
  có concept trong comment code T186) **tự động hoạt động**, không cần thêm UI mới.
  Màu/nhãn riêng cho cạnh (không phải node): đề xuất tái dùng style "TTL" hiện có
  (`COLOR_TTL = '#dc2626'`, app.py dòng ~7200) cho cạnh `ttl_local_candidate`, thêm
  `dashed=True` để phân biệt trực quan với cạnh `ttl_only` (T381, đã có DILA, nét
  liền) — việc này thuộc lớp renderer, không phải DB, ghi nhận cho bước implement.

---

## 5. Rủi ro và kiểm chứng

**Không mất dữ liệu — cách chứng minh:**
1. Trước ALTER: `SELECT COUNT(*), (SELECT COUNT(*) FROM lineage_edge_consensus WHERE teacher_id LIKE 'A%' AND disciple_id LIKE 'A%') FROM lineage_edge_consensus;` → ghi lại 2 số.
2. Sau ALTER (chưa insert gì mới): chạy lại đúng 2 câu trên — **phải khớp 100%** số
   trước. Thêm: `SELECT COUNT(*) FROM lineage_edge_consensus WHERE teacher_ns IS NULL OR disciple_ns IS NULL;` → phải = 0 (NOT NULL DEFAULT đảm bảo).
3. Sau khi insert batch cạnh TTL_LOCAL mới: `COUNT(*)` tổng phải = (số trước) +
   (số dòng insert thật, đếm bằng `cursor.rowcount` hoặc so `before/after` trong
   transaction) — không hơn không kém. Idempotent: chạy lại script insert lần 2
   phải cho `to_insert=0` (dùng UNIQUE index mới `uq_lec_ns_key` để check tồn tại
   trước khi insert, đúng pattern `t381_insert_ttl_only_edges.py`).

**Regression trên route đọc bảng:**
- `GET /daoanh/api/monk/<dila_id>/lineage-tree` (route chính, app.py:7230) — test
  với 1 DILA id cũ (không đổi hành vi) + 1 DILA id có cạnh mới trỏ tới TTL_LOCAL ở
  độ sâu 1 (`up=1` hoặc `down=1`) để xác nhận node TTL_LOCAL hiện đúng tên (sau khi
  sửa resolver §3) hoặc ít nhất không crash (trước khi sửa resolver, kỳ vọng hiện
  `id` thô làm tên, không 500).
- `GET /daoanh/api/monk/<slug>/lineage-tree` (center = slug TTL_LOCAL trực tiếp) —
  case mới hoàn toàn, test riêng: phải trả 200 + tên đúng từ `vn_person_authority`,
  không 404 "person not found" (hiện tại sẽ 404 vì `ttl_persons` không tồn tại —
  đây chính là bug cần test fail trước/pass sau khi sửa §3).
- Mọi route/script KHÁC đọc `lineage_edge_consensus` (liệt kê ở §3) chạy lại
  `npm run pipeline` (lint/test/e2e theo AGENTS.md §11) sau migration — không được
  có regression ở tab/route không liên quan (ví dụ trang person profile DILA
  thường, trang Nexus places).
- `scripts/t425_add_columns_and_views.py` so sánh overlay (chạy ở mode so sánh,
  không `--apply`) — chạy lại sau migration để xác nhận số liệu overlay vs
  consensus không lệch bất thường do cột mới (dự kiến không lệch vì view đó đọc từ
  `lineage_edge_assertions`, không đọc `teacher_ns`/`disciple_ns`).

---

## 6. Backup và rollback

1. **Trước `--apply`:** backup file-level bằng `shutil.copy2` (đúng pattern đã
   dùng ở `t158_consensus_migration.py`/`t381_insert_ttl_only_edges.py`), lưu
   `docs/sessions/<YYYY-MM-DD>/lineage.db.backup_t379_ns_<timestamp>`. Không dùng
   SQLite Online Backup API riêng vì toàn bộ migration chạy trong transaction DDL
   đơn giản (ALTER + CREATE INDEX), file-copy backup là đủ và nhất quán với các
   script hiện có trong repo.
2. **Trong transaction:** `BEGIN` → 2x `ALTER TABLE ADD COLUMN` → 2x
   `CREATE INDEX` → kiểm tra số dòng (§5) → `COMMIT`. Nếu bất kỳ bước nào lỗi:
   `ROLLBACK`, giữ file backup, báo Admin, không tự retry.
3. **Sau commit:** `PRAGMA quick_check` — phải `ok`, nếu không: dừng, phục hồi từ
   backup bước 1, báo Admin (đúng flow `t381_insert_ttl_only_edges.py` đã làm).
4. **Rollback (additive — theo AGENTS.md §14 mục 6):**
   ```sql
   DROP INDEX IF EXISTS idx_lec_disciple_ns;
   DROP INDEX IF EXISTS idx_lec_teacher_ns;
   DROP INDEX IF EXISTS uq_lec_ns_key;
   ALTER TABLE lineage_edge_consensus DROP COLUMN disciple_ns;
   ALTER TABLE lineage_edge_consensus DROP COLUMN teacher_ns;
   ```
   SQLite hỗ trợ `DROP COLUMN` từ bản ≥3.35 (cần xác nhận version SQLite đang dùng
   trước khi implement — nếu bản cũ hơn, rollback phải dùng
   `shutil.copy2(backup, db_path)` thay thế, ghi rõ trong script `--revert`).
   Mất 0 dữ liệu vì chỉ xóa cột/index thêm mới, không đụng 23.411 dòng gốc.
5. **Nếu đã insert cạnh TTL_LOCAL mới trước khi rollback:** DROP COLUMN sẽ xóa
   luôn các dòng đó nếu chúng **chỉ** tồn tại nhờ có ns (tức là hàng mới thêm có
   `teacher_ns='TTL_LOCAL'` — xóa cột không xóa dòng, nhưng dòng đó sẽ còn
   `teacher_id`=slug mà không còn cách phân biệt với DILA nữa). Vì vậy: nếu cần
   rollback sau khi đã có dữ liệu TTL_LOCAL thật, ưu tiên **restore từ file backup
   toàn bộ** (bước 1) thay vì DROP COLUMN, để không để lại slug "lạc" trong bảng
   DILA-only logic. Ghi rõ 2 lựa chọn rollback này trong script `--revert`, để
   script tự chọn theo: còn dòng `ns='TTL_LOCAL'` nào không → có thì bắt buộc
   restore file, không có thì DROP COLUMN là đủ.

---

## 7. 399 (231 đo thực tế) cạnh VN — breakdown

Xem lại khung số liệu ở §0. Breakdown thêm (đo bằng `classify_ttl_edges()` trên
`data/lineage.db` hiện tại, 2026-11-07):

| Nhóm | Số cạnh | Ghi chú |
|---|---|---|
| Matched cả 2 đầu sang DILA (đã qua T381, không thuộc phạm vi ns) | 553 | 393 đã insert `ttl_only`, 149 pre-existing update `ttl_asserted`, ~9-12 còn pending do dedup/dữ liệu đổi — không phải việc của doc này |
| **mismatch_teacher** — slug thầy không có `dila_id` | 101 | Cả 2 đầu *có thể* đều là TTL_LOCAL (nếu trò cũng không có dila_id) hoặc teacher=TTL_LOCAL / disciple=DILA (nếu trò có dila_id nhưng không được dùng vì teacher fail trước) |
| **mismatch_student** — slug thầy ĐÃ có `dila_id`, slug trò không có | 128 | teacher=DILA, disciple=TTL_LOCAL (dạng cạnh "pha trộn" — teacher_ns='DILA', disciple_ns='TTL_LOCAL') |
| **empty_teacher_slug** — không có thầy (khai tổ gốc) | 2 | KHÔNG phải vấn đề ns — đây là dòng TTL ghi nhận người không có thầy (ví dụ Thích Ca Mâu Ni). Không nên insert thành cạnh teacher→disciple (không có teacher) — đề xuất bỏ qua, không thuộc thiết kế này. |
| **Tổng cạnh "bị chặn ở tầng thiết kế" thật sự cần ns để thêm** | **229** (101+128, loại 2 dòng empty) | Đây là số cần dùng thay cho "399" trong báo cáo tiếp theo. |

**Có cả 2 đầu TTL_LOCAL (cả 2 slug đều không có dila_id) hay chỉ 1 đầu:** chưa đo
tách riêng được trong lần này — câu lệnh đo cụ thể (so khớp từng slug với
`vn_person_authority.id` để phân "known candidate, no dila_id" vs "slug hoàn toàn
chưa có trong `entity_source_ids`/`vn_person_authority`") đã bị **chặn bởi hook
bảo vệ cây chính** (`PreToolUse` hook báo "CHẶN: lệnh ghi/git nhắm vào cây chính")
khi chạy từ `daoanh/` (main tree) dù chỉ là `SELECT` read-only — hook này chặn theo
cwd, không phân biệt đọc/ghi. **Việc đo cần chạy lại trong chính worktree này**
(`wt/t379-rebuild-gen-tables`, có bản sao `data/lineage.db` riêng nếu đã sync, hoặc
Admin cho phép đọc main tree) ở bước audit kế tiếp, trước khi implement — ghi làm
**TODO bắt buộc** của bước build, không đoán số ở đây.

**Số có thể thêm ngay vs cần duyệt candidate:** theo quy tắc ở §4
(`is_default_visible=0`, `consensus_status='ttl_local_candidate'` cho MỌI dòng mới
— không có nhóm "thêm ngay thành visible"), nên về mặt **ghi vào DB thì cả 229
cạnh đều "thêm được ngay"** (không cần slug đạt `dila_id` hay `status='verified'`
trước — đó chính là mục đích của thiết kế ns: không cần quy đổi slug sang DILA
nữa). Nhưng về mặt **hiển thị/đếm đời** thì **0 cạnh** được tính tự động cho tới
khi Admin duyệt từng slug liên quan (đưa `vn_person_authority.status` lên
`'verified'` hoặc set `human_override`) — đúng tinh thần "candidate, không đưa vào
đếm đời tự động cho tới khi Admin duyệt" mà prompt yêu cầu.

---

## Tóm tắt 10 dòng cho Admin

1. Việc này **chỉ là thiết kế** — chưa chạy, chưa commit, chưa đổi DB.
2. Số liệu đo lại: cạnh VN thật sự bị chặn hôm nay là **229** (loại 2 dòng không có
   thầy), không phải 399 — 399 là một việc khác đã DONE (T381, dùng DILA id).
3. Đề xuất: thêm 2 cột `teacher_ns`/`disciple_ns` (`DEFAULT 'DILA'`), KHÔNG đổi
   cột `teacher_id`/`disciple_id` cũ — additive 100%, không UPDATE dòng cũ.
4. Thêm 1 UNIQUE index mới gồm `ns` để tránh trùng khóa giữa 2 namespace (constraint
   PRIMARY KEY cũ vẫn còn, hạn chế lý thuyết đã ghi rõ trong doc, rủi ro thực tế = 0).
5. 2 chỗ **phải sửa code** để chạy đúng: resolver tên hiển thị (`_t86_person_info`)
   và check "person tồn tại" trong route lineage-tree — cả 2 đang có fallback trỏ
   nhầm vào bảng `ttl_persons` không tồn tại (lỗi cũ từ T186, lộ ra khi có ns mới).
6. 1 chỗ nên sửa cùng lúc: `scripts/etl_gen_compute.py` (tính đời) — đổi heuristic
   `startswith('A')` sang check `ns` tường minh, đúng trọng tâm worktree
   `rebuild-gen-tables`.
7. Cạnh TTL_LOCAL mới: mặc định **không hiện** trong cây, **không tính đời tự
   động** cho tới khi Admin duyệt từng slug (`vn_person_authority.status='verified'`
   hoặc `human_override`).
8. Rollback: `DROP COLUMN` (additive) nếu chưa có dữ liệu mới; nếu đã có cạnh
   TTL_LOCAL thật thì ưu tiên restore file backup toàn bộ (ghi rõ lý do trong §6).
9. **Cần Admin duyệt:** (a) chọn Phương án A (ns là cột riêng) so với B (gộp vào
   id) — khuyến nghị A; (b) chấp nhận giữ UNIQUE constraint cũ song song (không
   rebuild bảng) hay yêu cầu rebuild để dọn sạch; (c) tên trạng thái mới
   `'ttl_local_candidate'` có ổn không.
10. Có 1 phần chưa đo được (tách "slug có candidate row nhưng chưa có dila_id" vs
    "slug hoàn toàn chưa từng import") do hook bảo vệ cây chính chặn query read-only
    chạy từ `daoanh/` — cần đo lại trong worktree này ở bước audit kế tiếp trước khi
    implement.
