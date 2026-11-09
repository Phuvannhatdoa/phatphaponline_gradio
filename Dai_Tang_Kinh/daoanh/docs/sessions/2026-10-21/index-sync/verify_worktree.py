"""Doi chieu status-before.txt voi su ton tai file tren dia (worktree) hien tai.
Quy tac:
- Y == 'D' (xoa trong worktree truoc do): file phai KHONG ton tai.
- Con lai (M, A, ??, X=D nhung Y=' ', ...): file phai TON TAI.
Ghi ket qua vao verify-worktree.txt. Chay tu repo root (visjs-app)."""
import os

BASE = "Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-21/index-sync/"
ROOT = "."

lines = open(BASE + "status-before.txt", encoding="utf-8").read().splitlines()
rows = []
for ln in lines:
    if len(ln) < 4:
        continue
    x, y, path = ln[0], ln[1], ln[3:]
    if path.endswith("/"):
        # thu muc untracked (vd docs/): kiem tra thu muc ton tai
        exists = os.path.isdir(os.path.join(ROOT, path.rstrip("/")))
        expect = True
    else:
        exists = os.path.exists(os.path.join(ROOT, path))
        expect = (y != "D")
    rows.append((x, y, path, expect, exists))

bad = [r for r in rows if r[3] != r[4]]
out = []
out.append("total_status_before_lines=%d" % len(rows))
out.append("mismatch_count=%d" % len(bad))
for r in bad:
    out.append("MISMATCH x=%r y=%r expect_exists=%s exists=%s path=%s" % (r[0], r[1], r[3], r[4], r[2]))

nine = [
    "Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-21/T263-damaged/2026-10-08_T263_h3_conflicts.tsv",
    "Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-21/T263-damaged/2026-10-08_T263_h3_conflicts_summary.tsv",
    "Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-21/permission/opencode.json.before",
    "Dai_Tang_Kinh/daoanh/tasks/T449-audit-h3-evidence-guard.md",
    "Dai_Tang_Kinh/daoanh/.opencode/opencode.json",
    "Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md",
    "Dai_Tang_Kinh/daoanh/docs/tasktodo.md",
    "Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-20_BUG-pl-id-404.md",
    "Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-20_BUG-placevn-baseurl.md",
]
for p in nine:
    out.append("NINE exists=%s %s" % (os.path.exists(os.path.join(ROOT, p)), p))

open(BASE + "verify-worktree.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
