#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cập nhật 4 task file (T454/T455/T456/T457) + ROLLBACK.md theo trạng thái thực tế.

Nguyên tắc:
- Sửa task file bằng blob (không `git add` cây thư mục) — AGENTS §17
- ROLLBACK.md: chèn dòng T454/T457 vào bảng "Commit gần đây" của bản HEAD
  (KHÔNG lấy worktree — worktree có WIP của session khác: T482/T470/T379)
"""
import os, re, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def head_text(path):
    return git(["show", "HEAD:" + path]).decode("utf-8")


def abspath(rel):
    return os.path.join(BASE, rel.replace("/", os.sep))


# ---------------------------------------------------------------- task files
T454 = DAO + "/tasks/T454-namevi-places-suffix-huy-cleanup.md"
T455 = DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md"
T456 = DAO + "/tasks/T456-home-search-autocomplete-dila-catalog.md"
T457 = DAO + "/tasks/T457-dila-biographies-nexus-import.md"

# --- T454: status -> done
t = head_text(T454)
t = t.replace("status: pending", "status: done", 1)
t = t.replace("updated: 2026-10-22", "updated: 2026-10-29", 1)
note_t454 = """
### Nhật ký 2026-10-29 — ĐÃ XỬ LÝ (Admin xác nhận DONE)
- **Đo lại**: `namevi_map_places` có **8 dòng** `name_vi` chứa hậu tố (2026-10-22) → **5 dòng** có mẫu `_ Huý`/`_ Ngoa` cần sửa (CSV: `docs/sessions/2026-10-28-t454/t454_namevi_suffixed_20261028_190704.csv`).
- **Cách sửa (Admin duyệt)**: bỏ hậu tố khỏi `name_vi`, **giữ hậu tố nguyên văn trong `note_vi`** (không mất thông tin). Không đụng `places_dila` (raw DILA).
- **Backup trước khi ghi**: `data/backups/lineage_t454_<ts>.db` (auto trong script).
- **Script**: `scripts/t454_cleanup_suffix.py` (`--stats` / `--apply` / `--revert`).
- **Verify sau apply** (`scripts/t454_verify_state.py`): dòng có hậu tố thật = **0**.
  - Lưu ý: `LIKE '%_ Huý%'` **không** escape `_` nên trả về 2 dòng giả ("Ải Ngoan Trại", "Ải Ngoan Sỡ") — phải dùng `LIKE '%\\_ Huý%' ESCAPE '\\'`.
- **ROLLBACK**: dòng 2026-10-28 trong `docs/ROLLBACK.md` (UPDATE ngược từ CSV giá trị gốc).
- **Bàn giao**: `docs/Handoff-2026-10-28-t454.md`.
"""
t = t.rstrip("\n") + "\n" + note_t454
T454_NEW = t.encode("utf-8")

# --- T455: status -> in_progress (đã phân loại, chờ Admin duyệt lô)
t = head_text(T455)
t = t.replace("status: pending", "status: in_progress", 1)
t = t.replace("updated: 2026-10-22", "updated: 2026-10-29", 1)
note_t455 = """
### Nhật ký 2026-10-29 — ĐÃ PHÂN LOẠI 794 DÒNG (chờ Admin duyệt lô, CHƯA ghi DB)
- **Phân loại tự động** (`scripts/classify_t455.py`, chỉ đọc CSV `docs/sessions/2026-10-22/T453/name_vi_mismatch_ALL.csv`):
  | Lô | Số dòng | Quy tắc | File CSV | Hành động |
  |----|---------|---------|----------|-----------|
  | **A** | **24** | `name_vi` ZQ sai rõ (tên Anh/Hán lệch chuẩn DILA) | `docs/sessions/2026-10-28-t455/name_vi_mismatch_A.csv` | **sửa** theo tên chuẩn |
  | **B** | **534** | alias/biệt hiệu cùng người (ZQ name_vi ≈ Cloud) | `docs/sessions/2026-10-28-t455/name_vi_mismatch_B.csv` | **giữ nguyên**, ghi alias |
  | **C** | **236** | khác quy ước chính tả / thiếu Hán | `docs/sessions/2026-10-28-t455/name_vi_mismatch_C.csv` | **sửa** đúng quy tắc |
  | | **794** | tổng | | |
- **Chưa ghi DB** (0 UPDATE). Script apply dự kiến: `scripts/t455_name_vi_fix.py` — chỉ chạy sau khi Admin duyệt từng lô.
- **Quy tắc bắt buộc**: tên Việt luôn `source_id=5` (ZQLOCAL) — **không** gán tên Việt cho nguồn DILA (source_id=1). Không sửa `people.name_zh`.
- **Câu hỏi còn chờ Admin**: Q3b (ưu tiên lô nào: theo `so_lan` hay nhóm sót Hán?), Q3c (duyệt bảng lịch sử additive `people_name_vi_history` không?), mẫu 20 dòng/lô để duyệt.
- **Bàn giao**: `docs/Handoff-2026-10-28-t455.md`.
"""
t = t.rstrip("\n") + "\n" + note_t455
T455_NEW = t.encode("utf-8")

# --- T456: chưa bắt đầu — ghi trạng thái chờ
t = head_text(T456)
t = t.replace("status: pending", "status: pending", 1)
t = t.replace("updated: 2026-10-22", "updated: 2026-10-29", 1)
note_t456 = """
### Trạng thái 2026-10-29 — CHƯA BẮT ĐẦU (blocked bởi T455)
- Thứ tự N4: **T454 ✅ → T457 ✅ → T455 (đang phân loại) → T456**.
- Phụ thuộc: `depends_on: [T453, T416, T450]`. T453 đã nạp đủ 5.747 bộ (chờ Admin xác nhận DONE); T416/T450 (autocomplete / FTS) đã có.
- Cần Admin duyệt phương án triển khai trước khi sửa `index.html` + route mới.
"""
t = t.rstrip("\n") + "\n" + note_t456
T456_NEW = t.encode("utf-8")

# --- T457: status -> done
t = head_text(T457)
t = t.replace("status: pending", "status: done", 1)
t = t.replace("updated: 2026-10-22", "updated: 2026-10-29", 1)
note_t457 = """
### Nhật ký 2026-10-29 — ĐÃ IMPORT (A2, additive), Admin xác nhận DONE
- **Quyết định A2**: JSONL lưu **đầy đủ** `person_ids` / `place_ids` (array) thay vì 1 id đầu tiên — đổi `scripts/t457_staging_v4.py` (dùng `re.findall` thay `pers[0]`).
- **Dry-run** (`--dry-run`): 21.740 nexus / **11 sách** / 7.066 có năm (32,5%) / `duplicate_composite_key=0`.
  - Tang_GSZ 5.446 · Song_GSZ 5.242 · Buxu_GSZ 3.971 · Xinxu_GSZ 2.955 · Liang_GSZ 1.819 · biQiuNi 373 · chuSanZangJiJi 473 · Ming_GSZ 587 · Jushi_Zhuan 523 · Mingsengzhuanchao 188 · OtherSources 163
- **Apply** (3 bảng additive, KHÔNG đụng `nexus_events` cũ 10.458 dòng):
  - `dila_bio_nexus` = **21.740 dòng**
  - `dila_bio_nexus_person` = **36.049 link**
  - `dila_bio_nexus_place` = **13.930 link**
  - index: `idx_bn_book`, `idx_bn_person`, `idx_bn_year`, `idx_bn_place`
- **Backup trước apply**: `data/backups/lineage_t457_20261029_094901.db`.
- **Script**: `scripts/t457_dila_bio_nexus_import.py` (`--stats` / `--dry-run` / `--apply` / `--revert`), verify: `scripts/t457_verify.py`.
- **ROLLBACK**: dòng 2026-10-29 trong `docs/ROLLBACK.md` — `DROP TABLE` 3 bảng + 4 index (additive, 0 mất dữ liệu cũ).
- **Manifest**: `docs/manifests/T457-manifest.json` (SHA-256 11 file nguồn).
- **Bàn giao**: `docs/Handoff-2026-10-28-t457.md`.
"""
t = t.rstrip("\n") + "\n" + note_t457
T457_NEW = t.encode("utf-8")

# ---------------------------------------------------------------- ROLLBACK
# Chèn 2 dòng T454/T457 vào bảng "Commit gần đây" của bản HEAD (bản worktree có
# WIP session khác: T482/T470/T379 — không lấy).
RB = DAO + "/docs/ROLLBACK.md"
rb = head_text(RB)
lines = rb.split("\n")
# tìm dòng header bảng rồi chèn ngay sau
idx = None
for i, l in enumerate(lines[:30]):
    if l.startswith("| Date | Task | Backup | Revert |"):
        idx = i + 1
        break
assert idx is not None, "không tìm thấy header bảng ROLLBACK"

row_t454 = (
    "| 2026-10-28 | **T454 — làm sạch hậu tố `_ Huý`/`_ Ngoa` trong `namevi_map_places.name_vi`** (5 dòng; hậu tố chuyển sang `note_vi`) "
    "| `data/backups/lineage_t454_20261028_*.db` (sqlite copy, tạo TRƯỚC `--apply`) "
    "| `python -X utf8 scripts/t454_cleanup_suffix.py --revert` (UPDATE `name_vi` về giá trị gốc theo CSV `docs/sessions/2026-10-28-t454/t454_namevi_suffixed_20261028_190704.csv`). Verify: `python -X utf8 scripts/t454_verify_state.py` — dòng còn hậu tố thật = **0** (dùng `LIKE '%\\_ Huý%' ESCAPE '\\'`, KHÔNG dùng `LIKE '%_ Huý%'` vì `_` là wildcard → 2 false-positive). Additive: không mất `note_vi`, không đụng `places_dila`. |"
)
row_t457 = (
    "| 2026-10-29 | **T457 — import DILA bio nexus (A2, array person+place)** — 3 bảng additive `dila_bio_nexus` (21.740) + `dila_bio_nexus_person` (36.049) + `dila_bio_nexus_place` (13.930), 11 sách, 7.066 có năm "
    "| `data/backups/lineage_t457_20261029_094901.db` (sqlite copy, tạo TRƯỚC `--apply`) "
    "| `python -X utf8 scripts/t457_dila_bio_nexus_import.py --revert` — DROP TABLE `dila_bio_nexus`, `dila_bio_nexus_person`, `dila_bio_nexus_place` + DROP INDEX `idx_bn_book`, `idx_bn_person`, `idx_bn_year`, `idx_bn_place`. Additive: **KHÔNG** đụng `nexus_events` cũ (10.458 dòng giữ nguyên). Verify: `python -X utf8 scripts/t457_verify.py`. |"
)
lines[idx:idx] = [row_t454, row_t457]
RB_NEW = "\n".join(lines).encode("utf-8")

# ---------------------------------------------------------------- output
out = {
    T454: T454_NEW,
    T455: T455_NEW,
    T456: T456_NEW,
    T457: T457_NEW,
    RB: RB_NEW,
}
manifest = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-28-commit")
os.makedirs(manifest, exist_ok=True)
for path, content in out.items():
    name = path.replace("/", "__")
    with open(os.path.join(manifest, name), "wb") as f:
        f.write(content)
    print("prepared %-70s %d bytes" % (path, len(content)))
print("\nOK — %d file blob staged trong %s" % (len(out), manifest))
