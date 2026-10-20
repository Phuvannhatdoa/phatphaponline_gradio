# T424 — Dry-run report (verify, 2026-10-20)

## Trạng thái phát hiện khi bắt đầu

T424 **đã được Admin duyệt và APPLY xong trước đó cùng ngày 2026-10-20** (session
`docs/sessions/2026-10-19/T424/`, commit `e5c2cc1`), KHÔNG phải task còn pending như
frontmatter của `tasks/T424-load-ttl-edges-into-assertions.md` hiển thị (file task
đó không nằm trong git — `git log` rỗng — nên nội dung outcome cũ "chưa làm" bị bỏ
quên, không được cập nhật sau khi apply; `docs/tasktodo.md` thì ĐÃ được cập nhật
đúng ở commit `e5c2cc1`, đánh dấu T424 "✅ ĐÃ GHI DB 2026-10-20").

Vì vậy, thay vì chạy dry-run lần đầu + chờ duyệt + apply, agent đã:
1. Kiểm tra DB hiện tại (`lineage_edge_assertions WHERE source_code='TTL'`).
2. Chạy lại `scripts/t424_load_ttl_edges.py --dry-run` (không ghi DB) để **đối chiếu**
   số liệu dry-run mới nhất với số liệu đã apply, xác nhận không có sai lệch /
   không cần apply lại.

## Bước 1 — Kiểm tra dependency T423

`tasks/T423-register-ttl-source-and-mapping.md`: status `in_progress`, outcome ghi
rõ đã APPLY 2026-10-20: `data_sources(TTL_LOCAL, id=15)`, `entity_hub` +204
(`ptda:<slug>`, id 267007–267210), `entity_source_ids(source='TTL_LOCAL')` +1.054
(794 accepted / 260 candidate), UNIQUE partial index `uq_esi_source_srcid_accepted`.
→ Dùng thẳng mapping này (không cần fallback `dharma_lineage_ttl_vn`).

## Bước 2–4 — Dry-run (chạy lại để verify)

```
cd Dai_Tang_Kinh/daoanh
python scripts/t424_load_ttl_edges.py --dry-run
```

Kết quả (giống hệt lần dry-run gốc ngày 2026-10-19, trước khi apply):

| Chỉ số | Giá trị |
|---|---|
| Cạnh distinct theo slug (từ `data/ttl/TS-*.ttl`) | 1.143 |
| Self-loop theo slug (trước khi sụp canonical) | 4 |
| Cạnh 2 đầu đã map (`insertable_both_mapped`) | 1.076 |
| Cạnh sau khi dedupe theo canonical_id | 1.062 |
| Self-loop canonical sau sụp N:1 (bị loại, KHÔNG nạp) | 2 |
| — `nam_vien_hue_ngung` → A004981 | |
| — `thai_tu_dao_nhat` → A038615 | |
| Cả 2 đầu `accepted` | 614 |
| Cả 2 đầu `candidate` hoặc hỗn hợp | 448 (195 candidate/accepted + 188 accepted/candidate + 79 candidate/candidate) |
| Đảo chiều (canonical), KHÔNG tự sửa | 2 cặp: `A000472 ⇄ ptda:tinh_tu_van`; `A003868 ⇄ A010427` |
| Slug chưa map → cạnh bị bỏ | 66 slug / 67 cạnh |

## Đối chiếu với DB hiện tại (đã apply)

```sql
SELECT source_code, COUNT(*) FROM lineage_edge_assertions GROUP BY source_code;
-- DILA 23014 | MARCUS 11169 | TTL 1062

SELECT mapping_verified, COUNT(*) FROM lineage_edge_assertions
WHERE source_code='TTL' GROUP BY mapping_verified;
-- 0 → 448 | 1 → 614

SELECT trust_level, COUNT(*) FROM lineage_edge_assertions WHERE source_code='TTL' GROUP BY trust_level;
-- L2 → 1062

SELECT COUNT(*) FROM lineage_edge_assertions
WHERE source_code='TTL' AND subject_person_id = object_person_id;
-- 0  (2 self-loop canonical đã bị loại đúng như dry-run, không bị nạp nhầm)
```

**Kết luận:** số liệu dry-run mới khớp 100% với số liệu đã ghi DB (1.062 cạnh,
614/448 split theo `mapping_verified`, `trust_level='L2'` toàn bộ, 0 self-loop
trong DB). Không có sai lệch, không cần apply lại. `INSERT OR IGNORE` của script
là idempotent (khóa theo `edge_key = 'TTL|<teacher>|<disciple>'`) nên chạy lại
dry-run không tạo thay đổi và apply lại (nếu có) cũng sẽ không tạo dòng trùng.

## Việc KHÔNG tự sửa (theo done_when của task, giữ nguyên để Admin quyết)

- 2 self-loop canonical: đã bị loại khỏi tập nạp (không vào DB) — đúng quy tắc,
  không tự gộp/sửa identity.
- 2 cặp đảo chiều canonical (`A000472 ⇄ ptda:tinh_tu_van`, `A003868 ⇄ A010427`):
  cả 2 chiều đều đã nạp vào `lineage_edge_assertions` (nguồn TTL ghi theo đúng
  triple gốc trong 2 file TTL khác nhau) — không tự chọn chiều đúng.
- 66 slug chưa có hồ sơ định danh (TTL chưa map): cạnh liên quan bị bỏ, danh sách
  tại `docs/sessions/2026-10-19/T424/t424_unmapped_slugs.tsv`.

## File bằng chứng

- Báo cáo dry-run gốc (trước apply): `docs/sessions/2026-10-19/T424/t424_report.txt`
- TSV cạnh/self-loop/đảo chiều/unmapped: `docs/sessions/2026-10-19/T424/t424_edges.tsv`,
  `t424_selfloops.tsv`, `t424_reverse_pairs.tsv`, `t424_unmapped_slugs.tsv`
- Session apply log: `docs/sessions/2026-10-19_T424-nap-canh-ttl.md`
- Backup trước khi apply: `data/backups/T424_20261020_073511/lineage.db`
  (quick_check=ok)
- Rollback: `docs/ROLLBACK.md`, hoặc
  `python -X utf8 scripts/t424_load_ttl_edges.py --revert --backup data/backups/T424_20261020_073511/lineage.db`
  hoặc `DELETE FROM lineage_edge_assertions WHERE source_code='TTL'`

## Việc còn thiếu (bookkeeping, không phải DB)

`tasks/T424-load-ttl-edges-into-assertions.md` là file chưa từng được git add/commit
(`git log` rỗng cho file này) — frontmatter `status: pending` / outcome "chưa làm"
và checklist 4 dòng `[ ]` đang SAI so với thực tế (đã apply xong, chỉ còn thiếu
bước daoanh-qa + Admin xác nhận DONE). Đề xuất Admin cho phép cập nhật file task
này để khớp với `docs/tasktodo.md` (đã đúng) — KHÔNG tự sửa vì đây là file
tracking/trạng thái, không phải data/DB.

## Kết quả cần Admin duyệt

Không có — task đã ở trạng thái "đã ghi DB, chờ daoanh-qa + Admin DONE" từ trước.
Dry-run verify lần này chỉ xác nhận lại tính nhất quán, không phát hiện sai lệch
cần quyết định mới. Đề xuất bước kế tiếp: gọi `daoanh-qa` kiểm T424 (và T423), sau
đó Admin xác nhận DONE, rồi tiếp T425.
