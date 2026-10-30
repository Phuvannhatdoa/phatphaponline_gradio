# -*- coding: utf-8 -*-
"""Chốt T455 DONE + tạo task T501/T502 + cập nhật tasktodo (blob từ INDEX)."""
import os, re, subprocess, sys

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

T455 = DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md"
T501 = DAO + "/tasks/T501-person-name-vi-han-residue-405.md"
T502 = DAO + "/tasks/T502-person-name-vi-alias-lotB-534.md"
TODO = DAO + "/docs/tasktodo.md"
UNDONE = DAO + "/docs/reports/UNDONE-2026-10-30.md"


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


def read(rel):
    with open(os.path.join(BASE, rel.replace("/", os.sep)), "rb") as f:
        return f.read()


out = {}

# ---------------- T455 -> done ----------------
t = head_text(T455)
t = t.replace("status: in_progress", "status: done", 1)
t = t.replace("updated: 2026-10-30", "updated: 2026-10-30", 1)
note = """
### Admin xác nhận DONE (2026-10-30) — task đóng, phần còn lại tách task riêng
- Admin xác nhận DONE sau khi review `docs/reports/T455-apply-planA-report.md` (phương án A).
- **Đã hoàn thành**: phân loại 794 dòng thành 3 lô · apply 258 dòng (lô A 22 + lô C 236) · 534 alias lô B ghi chú trong bảng lịch sử · bảng lịch sử `people_name_vi_history` 794 dòng · backup + dòng `ROLLBACK.md` · `npm run pipeline` exit 0 · `dup:ids` PASS.
- **Phần còn lại tách thành task riêng** (không chặn task khác):
  - **`T501`** — 405 tên còn sót chữ Hán (nhóm "532 tên sót Hán" — không có bản Cloud để đối chiếu) → `tasks/T501-person-name-vi-han-residue-405.md`
  - **`T502`** — 534 alias lô B cần tra từ điển theo `so_lan` → `tasks/T502-person-name-vi-alias-lotB-534.md`
- **Sổ việc còn treo**: `docs/reports/UNDONE-2026-10-30.md`.
- **Tiếp theo**: `T456` — autocomplete ô Search HOME.
"""
if "Admin xác nhận DONE (2026-10-30) — task đóng" not in t:
    t = t.rstrip("\n") + "\n" + note
    out[T455] = t.encode("utf-8")
    print("T455 -> done")

# ---------------- tasktodo ----------------
todo = index_text(TODO)
nl = "\r\n" if "\r\n" in todo else "\n"

old = "**✅ ĐÃ APPLY phương án A (Admin chọn 2026-10-30, batch `T455-planA-20261030`)**"
new = "**✅ DONE (Admin xác nhận 2026-10-30)**"
if old in todo:
    todo = todo.replace(old, new, 1)
    print("tasktodo: T455 -> DONE")

# thêm marker T501/T502
blocks = []
blocks.append(
    "<!-- T501:START -->" + nl +
    "> **[2026-10-30 · T501 — 405 tên người còn sót chữ Hán trong `people.name_vi`] ⏳ PENDING — chờ Admin chọn nguồn âm.** "
    "Tách từ T455 (phương án A chỉ xử lý 260 dòng có bằng chứng đối chiếu). Đo: 422 → 405 dòng còn Hán sau apply; "
    "**0** dòng thuộc batch T455 (không sót lại) — nhóm này **không có bản dịch Cloud** để so (Cloud chỉ phủ 26 tạng `authority_catalog`). "
    "Hướng: (a) sinh bản dịch Cloud mới · (b) `hanviet_char_map` + tra tay chữ hiến (`昰 竑 玘 霰 丏 哌 鸖 晙 屾 僼 蜞 頔 璹 橖 涑`) · "
    "(c) hiển thị song song Hán + Việt. Task: `tasks/T501-person-name-vi-han-residue-405.md`." + nl +
    "<!-- T501:END -->")
blocks.append(
    "<!-- T502:START -->" + nl +
    "> **[2026-10-30 · T502 — 534 alias lô B: tra từ điển 534 tên người theo `so_lan`] ⏳ PENDING — chờ Admin duyệt cách chia lô.** "
    "Tách từ T455. 534/794 dòng **không phải lỗi kỹ thuật** mà là khác *quy ước đọc cả từ*: ZQ đọc theo nghĩa chữ (`Long Thụ`, `Bàn Nhược`, `Vô Trứ`) "
    "vs Cloud theo cách gọi VN (`Long Thọ`, `Bát Nhã`, `Vô Trước`). Đo: 478/534 sai ≤ 1 từ · 64/534 chỉ khác gạch nối · 0/534 còn Hán. "
    "`hanviet_char_map` **không phân định được** (269 ZQ / 314 Cloud / 113 hòa) ⇒ cần người duyệt. Đã ghi chú alias trong "
    "`people_name_vi_history` (`action='kept_alias'`) nên không mất thông tin. Task: `tasks/T502-person-name-vi-alias-lotB-534.md`." + nl +
    "<!-- T502:END -->")

anchor = "<!-- T461:END -->"
assert anchor in todo, "khong thay anchor T461:END"
# chèn ngay sau block T455 để giữ nhóm
m = re.search(r"<!-- T455:START -->.*?<!-- T455:END -->", todo, re.DOTALL)
assert m, "khong thay block T455"
todo = todo[:m.end()] + nl + nl + (nl + nl).join(blocks) + todo[m.end():]
print("tasktodo: them marker T501/T502")
out[TODO] = todo.encode("utf-8")

# ---------------- task file mới ----------------
out[T501] = read(T501)
out[T502] = read(T502)
out[UNDONE] = read(UNDONE)

STAGE = os.path.join(BASE, "opencode-stage-t501")
os.makedirs(STAGE, exist_ok=True)
for path, content in out.items():
    with open(os.path.join(STAGE, path.replace("/", "__")), "wb") as f:
        f.write(content)
    print("staged %-72s %d bytes" % (path, len(content)))
print("\nOK — staging NGOAI repo (%s) để không FAIL dup:ids" % STAGE)
