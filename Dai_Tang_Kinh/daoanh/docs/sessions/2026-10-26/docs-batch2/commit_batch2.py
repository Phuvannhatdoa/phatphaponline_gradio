# -*- coding: utf-8 -*-
"""Commit batch2: 11 file (T436-T438, T454-T457, bao cao bug 048-051).

Quy trinh (AGENTS §14/§17): index tam bang read-tree HEAD -> git add tuong minh
-> kiem name-status = dung 11 dong A -> write-tree -> commit-tree -> CAS thu cong
(doc ref, so sanh parent, ghi tai cho, khong os.replace, khong update-ref).
Khong push. Khong dong vao index that.
"""
import os
import subprocess
import sys

ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh/"
FILES = [
    DAO + "tasks/T454-namevi-places-suffix-huy-cleanup.md",
    DAO + "tasks/T455-person-name-vi-standardize-from-dila-catalog.md",
    DAO + "tasks/T456-home-search-autocomplete-dila-catalog.md",
    DAO + "tasks/T457-dila-biographies-nexus-import.md",
    DAO + "tasks/backup/T436-bug049-etl-pass-button-error.md",
    DAO + "tasks/backup/T437-bug050-namevimap-stuck-loading.md",
    DAO + "tasks/backup/T438-bug051-places-lineage-arrows-missing.md",
    DAO + "docs/T435_BUG048_FINAL_REPORT.md",
    DAO + "docs/BUG-049_ETL_PASS_BUTTON_FIX_REPORT.md",
    DAO + "docs/T436_T437_VERIFY_FIX_REPORT.md",
    DAO + "docs/BUG-051_PLACES_LINEAGE_ARROWS_REPORT.md",
]
MSG = ("docs: dua task T436-T438/T454-T457 + bao cao bug 048-051 vao git, "
       "them muc Mo ta + xac nhan DONE + docs")
REF = os.path.join(ROOT, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
TMPDIR = os.path.join(ROOT, DAO.replace("/", os.sep), "docs", "sessions",
                      "2026-10-26", "docs-batch2")
TMPIDX = os.path.join(TMPDIR, "index.tmp")


def git(args, env=None):
    r = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", env=env)
    if r.returncode != 0:
        raise SystemExit("GIT FAIL %s: %s" % (args, r.stderr.strip()))
    return r.stdout


def idx_env():
    e = os.environ.copy()
    e["GIT_INDEX_FILE"] = TMPIDX
    return e


def build_index(parent):
    if os.path.exists(TMPIDX):
        os.remove(TMPIDX)
    env = idx_env()
    git(["read-tree", parent], env)
    git(["add", "--"] + FILES, env)
    ns = git(["diff", "--cached", "--name-status"], env).splitlines()
    got = set()
    for line in ns:
        st, path = line.split("\t", 1)
        got.add((st, path))
    want = set(("A", f) for f in FILES)
    if got != want:
        raise SystemExit("LECH DANH SACH: thieu=%s thua=%s" %
                         (want - got, got - want))
    stat = git(["diff", "--cached", "--stat"], env)
    tree = git(["write-tree"], env).strip()
    return tree, stat


def main():
    os.makedirs(TMPDIR, exist_ok=True)
    for attempt in range(1, 4):
        parent = git(["rev-parse", "HEAD"]).strip()
        print("attempt %d PARENT=%s" % (attempt, parent))
        tree, stat = build_index(parent)
        print("--- diff --cached --stat ---")
        print(stat)
        new = git(["commit-tree", tree, "-p", parent, "-m", MSG]).strip()
        print("NEW=%s" % new)
        cur = open(REF, encoding="utf-8").read().strip()
        if cur != parent:
            print("CAS MISMATCH: ref=%s != parent; retry" % cur)
            continue
        with open(REF, "w", encoding="utf-8", newline="\n") as f:
            f.write(new + "\n")
        print("CAS OK: ref -> %s" % new)
        if os.path.exists(TMPIDX):
            os.remove(TMPIDX)
        print("PARENT=%s" % parent)
        print("NEW=%s" % new)
        return
    raise SystemExit("CAS that bai 3 lan; dung, bao cao")


if __name__ == "__main__":
    sys.exit(main())
