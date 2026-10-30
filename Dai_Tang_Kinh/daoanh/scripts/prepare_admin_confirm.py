# -*- coding: utf-8 -*-
"""Áp dụng xác nhận DONE của Admin (2026-10-30) cho T453/T454/T457 + báo cáo T455.

- T453: task file đã `status: done` → chỉ cập nhật marker tasktodo ("chờ Admin xác nhận DONE" → DONE)
- T454/T457: thêm dòng "Admin xác nhận DONE (2026-10-30)" vào task file
- T455: task file status in_progress → ghi báo cáo phân tích + 3 phương án để Admin quyết
File dùng chung (tasktodo.md) dựng blob từ INDEX (AGENTS §17), không lấy worktree.
"""
import os, re, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

T453 = DAO + "/tasks/T453-dila-catalog-a-import-vi.md"
T454 = DAO + "/tasks/T454-namevi-places-suffix-huy-cleanup.md"
T455 = DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md"
T457 = DAO + "/tasks/T457-dila-biographies-nexus-import.md"
TODO = DAO + "/docs/tasktodo.md"


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


def index_text(path):
    out = git(["ls-files", "-s", "--", path]).decode().strip()
    sha = out.split()[1]
    return git(["cat-file", "blob", sha]).decode("utf-8")


out = {}

# ---------------- T453: chỉ cần marker tasktodo (task file đã done) ----------------
# ---------------- T454: thêm xác nhận Admin ----------------
t = head_text(T454)
note = """
### Admin xác nhận DONE (2026-10-30)
- Admin xác nhận DONE sau khi review báo cáo `docs/Handoff-2026-10-28-t454.md`.
- Verify cuối: `python -X utf8 scripts/t454_verify_state.py` → dòng còn hậu tố thật = **0**.
- Revert nếu cần: `python -X utf8 scripts/t454_cleanup_suffix.py --revert` | `git revert 01ee030f`.
"""
if "Admin xác nhận DONE (2026-10-30)" not in t:
    t = t.replace("updated: 2026-10-29", "updated: 2026-10-30", 1)
    t = t.rstrip("\n") + "\n" + note
    out[T454] = t.encode("utf-8")
    print("T454: them Admin xac nhan DONE")

# ---------------- T457: thêm xác nhận Admin ----------------
t = head_text(T457)
note = """
### Admin xác nhận DONE (2026-10-30)
- Admin xác nhận DONE sau khi review báo cáo `docs/Handoff-2026-10-28-t457.md` + manifest `docs/manifests/T457-manifest.json`.
- Số liệu apply: `dila_bio_nexus` 21.740 · `dila_bio_nexus_person` 36.049 · `dila_bio_nexus_place` 13.930 · 11 sách · 7.066 có năm.
- Revert nếu cần: `python -X utf8 scripts/t457_dila_bio_nexus_import.py --revert` | `git revert 2686da0a`.
"""
if "Admin xác nhận DONE (2026-10-30)" not in t:
    t = t.replace("updated: 2026-10-29", "updated: 2026-10-30", 1)
    t = t.rstrip("\n") + "\n" + note
    out[T457] = t.encode("utf-8")
    print("T457: them Admin xac nhan DONE")

# ---------------- T455: thêm báo cáo + 3 phương án ----------------
t = head_text(T455)
note = """
### Báo cáo phân tích 2026-10-30 (đã trình Admin — chờ quyết phương án)

Báo cáo đầy đủ: **`docs/reports/T455-analysis-794-mismatch.md`** (bằng chứng + số đo + 3 phương án).

**Tóm tắt:**
| Lô | Số | Bản chất | Có thể tự quyết? |
|---|---|---|---|
| A | 24 | ZQ hỏng rõ: để tên Anh / để nguyên chữ Hán hiến (`昰 竑 玘 霰 丏 讕` không có trong `hanviet_char_map`) → **17/24 còn sót Hán** | ✅ tra từ điển |
| B | 534 | **Không phải lỗi kỹ thuật** mà là khác *quy ước đọc cả từ*: ZQ đọc theo nghĩa chữ (`Long Thụ`, `Bàn Nhược`, `Vô Trứ`) vs Cloud đọc theo cách gọi quen thuộc VN (`Long Thọ`, `Bát Nhã`, `Vô Trước`). 478/534 sai ≤ 1 từ · 64/534 chỉ khác dấu gạch nối · **0/534** còn sót Hán | ⚠️ **không** — charmap không phân định được (269 ZQ vs 314 Cloud vs 113 hòa) |
| C | 236 | ZQ thiếu/sai 1 chữ, hay thiếu tiền tố tôn kính `釋` (Thích) → charmap (bảng chuẩn dự án) **nghiêng Cloud 188/236 (80 %)** | ✅ có bằng chứng máy |

**3 phương án để Admin chọn:**
- **(A) Khuyến nghị** — sửa **260 dòng** (lô A 24 + lô C 236), giữ 534 dòng lô B và ghi chú alias. Ít xâm lấn, có bằng chứng khách quan, không cần người duyệt 534 dòng. Lô B mở task riêng để làm dần theo `so_lan`.
- **(B)** — sửa cả **794** theo Cloud. Đồng bộ hết nhưng Cloud cũng có lỗi riêng (vd `實叉難陀` → "Thật" thay vì "Thực") và là bản dịch unreviewed.
- **(C)** — sửa lô A + C theo Cloud, lô B tra từ điển theo lô `so_lan` (ưu tiên ~50 người xuất hiện ≥ 20 lần). Chính xác nhất nhưng chậm, cần người duyệt.

**Quy tắc bất biến**: tên Việt luôn `source_id=5` (ZQLOCAL) — không gán tên Việt cho nguồn DILA (`source_id=1`); không sửa `people.name_zh`; additive (giữ giá trị cũ trong bảng lịch sử); backup + dòng `ROLLBACK.md`.

**Việc cần làm tiếp**: Admin chọn phương án → mới chạy `scripts/t455_name_vi_fix.py` (backup tự động → apply theo lô → verify → `ROLLBACK.md`).
"""
if "Báo cáo phân tích 2026-10-30" not in t:
    t = t.replace("updated: 2026-10-29", "updated: 2026-10-30", 1)
    t = t.rstrip("\n") + "\n" + note
    out[T455] = t.encode("utf-8")
    print("T455: them bao cao + 3 phuong an")

# ---------------- tasktodo: T453/T454/T457 marker (dung blob tu INDEX) ----------------
todo = index_text(TODO)
nl = "\r\n" if "\r\n" in todo else "\n"

reps = [
    # T453: đã xác nhận DONE
    (r"(<!-- T453:START -->\n)(> \*\*\[2026-10-22 · T453[^\n]*?)(chờ Admin xác nhận DONE)",
     r"\1\2**✅ DONE (Admin xác nhận 2026-10-30)** — đã nạp đủ 5.747 bộ / 5.589 lượt người / 765 nơi dịch; task file `status: done`"),
]
# làm thủ công cho an toàn (regex phức tạp)
old_t453 = "chờ Admin xác nhận DONE.** Đã nạp **đủ 5.747 bộ / 5.589 lượt người / 765 nơi dịch**"
new_t453 = "**✅ DONE (Admin xác nhận 2026-10-30).** Đã nạp **đủ 5.747 bộ / 5.589 lượt người / 765 nơi dịch**"
if old_t453 in todo:
    todo = todo.replace(old_t453, new_t453, 1)
    print("tasktodo: T453 -> DONE")
else:
    print("!! tasktodo: khong tim thay cum T453")

# T454 marker
old = "**ĐÃ XỬ LÝ (Admin xác nhận DONE)"
if "T454 — làm sạch hậu tố" in todo:
    todo = todo.replace(
        "T454 — làm sạch hậu tố \"_ Huý\"/\"_ Ngoa\" trong `namevi_map_places.name_vi`] ✅ DONE.",
        "T454 — làm sạch hậu tố \"_ Huý\"/\"_ Ngoa\" trong `namevi_map_places.name_vi`] ✅ **DONE (Admin xác nhận 2026-10-30)**.",
        1)
    print("tasktodo: T454 -> DONE")

# T457 marker
if "T457 — import DILA bio nexus (A2: array đầy đủ person+place)] ✅ DONE." in todo:
    todo = todo.replace(
        "T457 — import DILA bio nexus (A2: array đầy đủ person+place)] ✅ DONE.",
        "T457 — import DILA bio nexus (A2: array đầy đủ person+place)] ✅ **DONE (Admin xác nhận 2026-10-30)**.",
        1)
    print("tasktodo: T457 -> DONE")

# T455 marker: thêm link báo cáo
old455 = "**Còn chờ Admin: Q3b (thứ tự lô), Q3c (duyệt bảng lịch sử additive `people_name_vi_history`), mẫu 20 dòng/lô."
new455 = ("**Còn chờ Admin: chọn phương án A/B/C (xem báo cáo `docs/reports/T455-analysis-794-mismatch.md`: "
          "A = sửa 260 dòng có bằng chứng, B = sửa cả 794 theo Cloud, C = sửa 260 + tra từ điển lô B theo `so_lan`); "
          "Q3c (duyệt bảng lịch sử additive `people_name_vi_history`).")
if old455 in todo:
    todo = todo.replace(old455, new455, 1)
    print("tasktodo: T455 -> them link bao cao + 3 phuong an")
else:
    print("!! tasktodo: khong tim thay cum T455")

out[TODO] = todo.encode("utf-8")

# ---------------- ghi blob ra staging ----------------
STAGE = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-30-t455-analysis", "blobs")
os.makedirs(STAGE, exist_ok=True)
for path, content in out.items():
    with open(os.path.join(STAGE, path.replace("/", "__")), "wb") as f:
        f.write(content)
    print("staged %-72s %d bytes" % (path, len(content)))
print("\nOK — %d blob trong %s" % (len(out), STAGE))
