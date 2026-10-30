# -*- coding: utf-8 -*-
"""Cập nhật sau apply T455 phương án A: ROLLBACK row + task file + tasktodo (blob từ INDEX)."""
import os, re, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RB = DAO + "/docs/ROLLBACK.md"
T455 = DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md"
TODO = DAO + "/docs/tasktodo.md"


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def head_text(p):
    return git(["show", "HEAD:" + p]).decode("utf-8")


def index_text(p):
    out = git(["ls-files", "-s", "--", p]).decode().strip()
    return git(["cat-file", "blob", out.split()[1]]).decode("utf-8")


out = {}

# ---------------- ROLLBACK row (dựng từ HEAD blob) ----------------
rb = head_text(RB)
lines = rb.split("\n")
idx = None
for i, l in enumerate(lines[:40]):
    if l.startswith("| Date | Task | Backup | Revert |"):
        idx = i + 1
        break
assert idx is not None, "khong thay header bang ROLLBACK"
row = (
    "| 2026-10-30 | **T455 phương án A — chuẩn hoá `people.name_vi` (258 dòng sửa: lô A 22 + lô C 236) + bảng lịch sử mới "
    "`people_name_vi_history` (794 dòng: 258 updated / 534 kept_alias / 1 unchanged / 1 skipped_kept); lô B 534 dòng **không** đổi** "
    "| `data/backups/lineage_t455_20261030_144710.db` (sqlite copy 1.824.460.800 B, tạo TRƯỚC `--apply`) "
    "| `python -X utf8 scripts/t455_apply_planA.py --revert` — khôi phục `people.name_vi` = `name_vi_old` cho 258 dòng `action='updated'` "
    "rồi DELETE 794 dòng `people_name_vi_history` có `batch_id='T455-planA-20261030'`. Additive: **không** mất dữ liệu cũ "
    "(`name_zh` không đổi, `source_id` không đổi). Hoặc khôi phục nguyên trạng từ backup ở cột trên. "
    "Báo cáo: `docs/reports/T455-apply-planA-report.md`. |"
)
lines[idx:idx] = [row]
out[RB] = "\n".join(lines).encode("utf-8")
print("ROLLBACK: chen dong T455 (vi tri sau header bang)")

# ---------------- task file T455 ----------------
t = head_text(T455)
t = t.replace("updated: 2026-10-30", "updated: 2026-10-30", 1)
note = """
### APPLY phương án A — 2026-10-30 (Admin đã chọn phương án A)

**Đã ghi DB** (batch `T455-planA-20261030`), backup `data/backups/lineage_t455_20261030_144710.db`:

| Hạng mục | Kết quả |
|---|---|
| Bảng lịch sử mới `people_name_vi_history` | **794 dòng** (additive) — 258 `updated` / 534 `kept_alias` / 1 `unchanged` / 1 `skipped_kept` |
| `people.name_vi` được UPDATE | **258 dòng** (lô A 22 + lô C 236) |
| Lô B (534 dòng) | **không đổi** — chỉ ghi chú alias trong bảng lịch sử |
| `people.name_vi` còn sót chữ Hán | 422 → **405** (−17) |
| `people.name_zh` / `people.source_id` | **không đổi** |

- **2 dòng đặc biệt**: `A000142` sửa tay (`頙` không có trong bảng đọc → "Chân Tĩnh Thiên Trác") · `A001428` bỏ qua (DB đã là "Di Lặc Bồ Tát" tốt hơn Cloud "Di Lặc").
- **Quy tắc giữ nguyên**: tên Việt `source_id=5` (ZQLOCAL), không gán tên Việt cho DILA; không sửa `name_zh`; additive (giá trị cũ ở `name_vi_old`).
- **Script**: `scripts/t455_apply_planA.py` (`--dry-run` / `--apply` / `--revert`) · verify: `scripts/t455_verify_apply.py`.
- **Báo cáo**: `docs/reports/T455-apply-planA-report.md` · đề xuất: `docs/sessions/2026-10-30-t455-apply/t455_proposal_planA.csv`.
- **Revert**: `python -X utf8 scripts/t455_apply_planA.py --revert` | dòng `ROLLBACK.md` 2026-10-30.
- **Pipeline sau apply**: `npm run pipeline` **exit 0** ✅

**Còn lại (chưa làm)**:
1. **405 tên còn sót chữ Hán** — nhóm "532 tên sót Hán" trong task này, **không** nằm trong danh sách 794 (không có bản Cloud để đối chiếu) → cần task riêng.
2. **534 alias lô B** — đã ghi trong bảng lịch sử; mở task riêng để tra từ điển theo `so_lan` (không chặn T456).
3. **T456** — autocomplete ô Search HOME.
"""
if "APPLY phương án A — 2026-10-30" not in t:
    t = t.rstrip("\n") + "\n" + note
    out[T455] = t.encode("utf-8")
    print("task T455: them nhat ky APPLY")

# ---------------- tasktodo ----------------
todo = index_text(TODO)
old = "**Còn chờ Admin: chọn phương án A/B/C**"
new = ("**✅ ĐÃ APPLY phương án A (Admin chọn 2026-10-30, batch `T455-planA-20261030`)** — 258 dòng sửa "
       "(lô A 22 + lô C 236), 534 lô B giữ nguyên + ghi chú alias, bảng lịch sử mới `people_name_vi_history` 794 dòng; "
       "`name_vi` còn sót Hán 422 → 405; `name_zh`/`source_id` không đổi; pipeline exit 0. "
       "Báo cáo: `docs/reports/T455-apply-planA-report.md`. "
       "**Còn lại:** 405 tên sót Hán (task riêng) + 534 alias lô B (task riêng) + T456.")
if old in todo:
    todo = todo.replace(old, new, 1)
    print("tasktodo: T455 -> DA APPLY")
else:
    print("!! tasktodo: khong khop cum T455")
out[TODO] = todo.encode("utf-8")

STAGE = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-30-t455-apply", "blobs")
os.makedirs(STAGE, exist_ok=True)
for path, content in out.items():
    with open(os.path.join(STAGE, path.replace("/", "__")), "wb") as f:
        f.write(content)
    print("staged %-70s %d bytes" % (path, len(content)))
print("\nOK")
