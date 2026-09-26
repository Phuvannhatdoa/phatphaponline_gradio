---
id: T115
title: "Source Authority Matrix & Referee Rules"
module: Data Governance / Source Registry
priority: medium
status: done
depends_on: [T112, T108, T78, T68]
created: 2026-09-09
updated: 2026-09-09
done_when: >
  Tài liệu luật trọng tài `docs/SOURCE_AUTHORITY_MATRIX.md` tồn tại: nhãn Level theo
  khoảng authority_score (Primary ≥80 · Scholarly 45–75 · Reference <45) + Luật Trọng Tài
  (không đếm phiếu, dùng score + precedence_order 0-based; tie → Conflict Pool admin T109;
  KHÔNG tự áp winner) + bảng ánh xạ 13 nguồn thật + chuẩn tên (GRETIL chưa có /
  Wikidata ≠ Wikipedia / ZQLOCAL = DILA local). SOURCE_REGISTRY.md có §6 đối chiếu số liệu
  (sửa lệch 4 implemented=1 · 9 implemented=0 · 5 historical-ingested). docs-only, 0 ETL/0 DB.
---

# T115 — Source Authority Matrix & Referee Rules

## Mục tiêu
Chốt **thứ bậc tin cậy nguồn** + **Luật Trọng Tài (Referee Principle)** cho conflict resolution:
hệ thống không đếm phiếu, dùng `authority_score` → `precedence_order` (0-based). Bảng
`source_authority` ĐÃ tồn tại và có sẵn 13 dòng score (T68/T78) — task này chỉ **tài liệu hoá
+ đối chiếu + chuẩn hoá tên**, không sửa DB.

## Khác biệt so với đặc tả T112 cũ (đã nắn theo thực trạng — G1–G8)
1. File **mới** `SOURCE_AUTHORITY_MATRIX.md` (không ghi đè `SOURCE_REGISTRY.md` — đã có §1–§5).
2. Level = **nhãn khoảng-score trực quan**, LUẬT = score+precedence trực tiếp (hết tự mâu thuẫn Level vs Score).
3. **KHÔNG tự áp winner** — giữ điều lệnh "không tự quyết conflict, chỉ trình Admin" (T100/T109);
   đề xuất ghi `en_audit_log` với `editor='system:proposal'` khi hiện thực code sau này.
4. Chuẩn tên: **GRETIL chưa có** · **Wikidata ≠ Wikipedia** · ZQLOCAL = DILA local.
5. Số liệu đúng DB: 4 `implemented=1` · 9 `implemented=0` · 5 historical-ingested (kể Wikidata).

## Nội dung (đã bàn giao)
- `docs/SOURCE_AUTHORITY_MATRIX.md` — §1 Objective · §2 Level (L1≥80/L2 45–75/L3<45) ·
  §3 Conflict Logic (score → precedence → tie → pool admin, `implemented=0` không dùng đề xuất) ·
  §4 bảng 13 nguồn thật · §5 chuẩn tên · §6 Scope (docs-only).
- `docs/SOURCE_REGISTRY.md` §6 — đối chiếu 13 dòng score + sửa số liệu lệch.
- SCHEMA_DESIGN.md (Phụ lục A) + tasktodo.md + roadmap.md cập nhật T115 ✅.

## Acceptance
- ✅ `docs/SOURCE_AUTHORITY_MATRIX.md` tồn tại, 0 placeholder hash, số liệu khớp DB read-only.
- ✅ `SOURCE_REGISTRY.md` §6 đối chiếu; không phá §1–§5.
- ✅ Dashboard (`data/progress_data.json`) hiển thị T115 (regen `scripts/build_progress_data.py`).
- ✅ Revert tiện: ROLLBACK row `27e4b22`; git revert 1 lệnh. 0 DB nên không có revert DB.

## Tiến độ (2026-09-09)
- ✅ DONE (commit `27e4b22`, session `docs/sessions/2026-09-09_t115-source-authority-matrix.md`).