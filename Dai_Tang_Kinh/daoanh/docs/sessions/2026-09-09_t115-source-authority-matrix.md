# Session — T115 Source Authority Matrix & Referee Rules (DONE)

**Ngày:** 2026-09-09 · **Trạng thái:** DONE · **Commit:** `27e4b22`

## Bối cảnh
Lee Tổng phê chuẩn đề xuất nắn đặc tả T112 trong phiên thảo luận (8 điểm lệch G1–G8):
giữ tinh thần "Referee Principle — không đếm phiếu" nhưng đúng thực trạng hệ thống.

## Sản phẩm (docs-only — 0 code, 0 ETL, 0 DB-ALTER)
1. **MỚI `docs/SOURCE_AUTHORITY_MATRIX.md`**:
   - §1 Referee Principle: decision bằng `authority_score` → `precedence_order` (0-based).
   - §2 Authority Levels = **nhãn theo khoảng score**: L1-Primary ≥80 (DILA 100 · CBETA 80) ·
     L2-Scholarly 45–75 (SAT 75 · Kanripo 70 · MARCUS 60 · CHGIS 58 · TGAZ 55 · ZQLOCAL 50 ·
     SuttaCentral 50 · 84000 45) · L3-Reference <45 (BDRC 40 · FoJin 40 · Wikidata 25).
   - §3 Conflict Logic: score khác → winner đề xuất; score bằng → precedence nhỏ thắng đề xuất;
     tie / cùng level cao → **Conflict Pool admin (lineage_conflicts_v2, T109)**; KHÔNG tự áp
     (giữ điều lệnh "không tự quyết conflict"); `implemented=0` không dùng cho đề xuất.
   - §4 bảng 13 nguồn thật (đối chiếu read-only data/lineage.db).
   - §5 chuẩn tên: GRETIL chưa có · Wikidata ≠ Wikipedia · ZQLOCAL = DILA local · GIS = BLOCK.
   - §6 Scope: docs-only; đổi score cần Lee duyệt + ROLLBACK.
2. **`docs/SOURCE_REGISTRY.md` §6** — bảng đối chiếu 13 dòng score + **sửa lệch số liệu**:
   4 `implemented=1` · 9 `implemented=0` · "5 active" = 5 historical-ingested (kể Wikidata, dù `implemented=0`).
3. **`tasks/T115-source-authority-matrix-referee.md`** (status done) + tasktodo/roadmap/SCHEMA_DESIGN
   (T02→**T112+T115**, T114→Done, T115→Done) + ROLLBACK row `27e4b22`.

## Xác minh
- Số liệu score/precedence lấy trực tiếp từ `source_authority` (data/lineage.db, read-only) — 13/13 khớp.
- Không tồn tại placeholder ngoài `27e4b22` (fill ở commit session-note).
- Dashboard: regen `scripts/build_progress_data.py` → T115 hiện trên board.

## Rollback
- Revert docs: `git revert --no-edit 27e4b22` (0 DB → không cần revert DB).

## Việc kế tiếp (outside task này)
- T112 chờ Lee duyệt §5 activation; T113 phần A chờ :5000. Nếu chốt "tự áp winner" → task code
  riêng (mirror T111, ghi `en_audit_log` `editor='system:proposal'`).