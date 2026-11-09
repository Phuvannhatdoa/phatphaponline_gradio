# -*- coding: utf-8 -*-
"""Đổi số T463 -> T468 (bên footprint nhỏ hơn) và tạo file T445 "giữ số" dạng con trỏ.
Chỉ đụng: tasks/T463-*.md (đổi tên + sửa) và tasks/T445-*.md (tạo mới dạng con trỏ).
"""
import os
import sys

REPO_DAOANH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TASKS = os.path.join(REPO_DAOANH, "tasks")
OLD = os.path.join(TASKS, "T463-placevn-wizard-ui-b0-b9.md")
NEW = os.path.join(TASKS, "T468-placevn-wizard-ui-b0-b9.md")
KEEP = os.path.join(TASKS, "T445-placevn-wizard-ui-b0-b9.md")
DATE = "2026-10-26"

if not os.path.isfile(OLD):
    sys.exit("ABORT: thiếu " + OLD)
if os.path.exists(NEW):
    sys.exit("ABORT: đã tồn tại " + NEW)
if os.path.exists(KEEP):
    sys.exit("ABORT: đã tồn tại " + KEEP + " (không ghi đè)")

raw = open(OLD, "rb").read()
text = raw.decode("utf-8")
assert text.startswith("---\r\n"), "BOM/format lạ"
nl = "\r\n"

# 1) Frontmatter
old_head = "id: T463" + nl + "former_ids: [T445]" + nl
assert text.count(old_head) == 1, "frontmatter không khớp"
text = text.replace(old_head, "id: T468" + nl + "former_ids: [T463, T445]" + nl + "updated: " + DATE + nl, 1)

# 2) Tự tham chiếu trong body: T463 -> T468 (đã kiểm: 4 chỗ, sau khi thêm former_ids không còn T463 ở frontmatter)
n_self = text.count("T463")
assert n_self == 4, "số tự tham chiếu T463 = %d (kỳ vọng 4)" % n_self
text = text.replace("T463", "T468")

# 3) Ghi: os.rename rồi ghi nội dung mới (giữ CRLF)
os.rename(OLD, NEW)
with open(NEW, "wb") as f:
    f.write(text.encode("utf-8"))

# 4) File giữ số T445: con trỏ (không còn bản nội dung trùng)
keep_text = (
    "---" + nl
    + "id: T445" + nl
    + 'title: "Wizard UI cho T444 Gemini Places Translation (B0-B9) — đã gộp vào T468"' + nl
    + "status: deferred" + nl
    + "depends_on: [T444]" + nl
    + "merged_into: T468" + nl
    + "updated: " + DATE + nl
    + "---" + nl + nl
    + "# T445 — con trỏ gộp" + nl + nl
    + "Gộp với T468 (trùng nội dung) — " + DATE + "." + nl + nl
    + "Task sống: `tasks/T468-placevn-wizard-ui-b0-b9.md` (former_ids: T463, T445)." + nl
    + "Bản T445 trước gộp: `git show e4fbc5ba:Dai_Tang_Kinh/daoanh/tasks/T445-placevn-wizard-ui-b0-b9.md` (UTF-16)." + nl
    + "Bản nháp đã gỡ trước đó: `docs/sessions/2026-10-26/T445-duplicate-removed/`." + nl
)
with open(KEEP, "wb") as f:
    f.write(keep_text.encode("utf-8"))

print("OK rename+edit:", os.path.basename(NEW), "bytes", os.path.getsize(NEW))
print("OK pointer:", os.path.basename(KEEP), "bytes", os.path.getsize(KEEP))
