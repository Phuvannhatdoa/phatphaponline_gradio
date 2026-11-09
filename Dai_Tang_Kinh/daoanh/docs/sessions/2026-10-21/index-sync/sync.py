# -*- coding: utf-8 -*-
"""Dong bo .git/index ve HEAD cho 1 file (Admin da duyet 2026-10-21).

Chay: python -X utf8 docs/sessions/2026-10-21/index-sync/sync.py   (cwd = daoanh)
Khong dung git reset/checkout/stash/commit/push; khong sua worktree.
Chi thay the byte cua .git/index bang index tam (read-tree HEAD).
"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
REL = "Dai_Tang_Kinh/daoanh/.opencode/opencode.json"   # path tinh tu repo root
EXPECT = "M\t" + REL
TMP_INDEX = os.path.join(HERE, "tmp3.index")
BAK = os.path.join(HERE, "index.before-fix3.bak")
PRE = os.path.join(HERE, "pre-fix3.txt")
REPORT = os.path.join(HERE, "REPORT-3.md")


def run(args, cwd, env=None):
    r = subprocess.run(args, cwd=cwd, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (r.returncode,
            r.stdout.decode("utf-8", "replace"),
            r.stderr.decode("utf-8", "replace"))


def read_bytes(p):
    with open(p, "rb") as f:
        return f.read()


def write_index_bytes(git_index, data):
    with open(git_index, "r+b") as f:
        f.write(data)
        f.truncate(len(data))
        f.flush()
        os.fsync(f.fileno())


def die(msg, code=1):
    print("DUNG: " + msg, flush=True)
    sys.exit(code)


def main():
    rc, top, err = run(["git", "rev-parse", "--show-toplevel"], DAOANH)
    if rc != 0:
        die("khong tim thay repo root: " + err)
    ROOT = top.strip()

    # ---- Buoc 1: baseline ----
    rc, head, _ = run(["git", "rev-parse", "HEAD"], ROOT)
    HEAD = head.strip()
    _, staged, _ = run(["git", "diff", "--cached", "--name-status"], ROOT)
    _, st, _ = run(["git", "status", "--short"], ROOT)
    _, gp, _ = run(["git", "rev-parse", "--git-path", "index"], ROOT)
    GIT_INDEX = os.path.abspath(os.path.join(ROOT, gp.strip()))

    pre_text = (
        "HEAD: %s\n"
        "GIT_INDEX: %s\n"
        "\n== git diff --cached --name-status ==\n%s"
        "\n== git status --short ==\n%s"
    ) % (HEAD, GIT_INDEX, staged, st)
    with open(PRE, "w", encoding="utf-8", newline="\n") as f:
        f.write(pre_text)
    if not os.path.isfile(PRE) or os.path.getsize(PRE) == 0:
        die("khong ghi duoc pre-fix3.txt")
    print("pre-fix3: HEAD=%s staged=%r" % (HEAD, staged), flush=True)

    # ---- Buoc 2: kiem danh sach staged ----
    staged_lines = [l.rstrip("\r") for l in staged.splitlines() if l.strip()]
    if staged_lines != [EXPECT]:
        print("DUNG: staged khac dung 1 dong ky vong. Nguyen van:", flush=True)
        print(repr(staged), flush=True)
        sys.exit(3)

    # ---- Buoc 3: kiem HEAD va worktree ----
    rc, _, e = run(["git", "cat-file", "-e", "HEAD:" + REL], ROOT)
    if rc != 0:
        die("HEAD khong co file: " + e)
    rc, d, e = run(["git", "diff", "HEAD", "--", REL], ROOT)
    if rc != 0 or d.strip() != "":
        die("worktree khac HEAD (rc=%d): %r %s" % (rc, d, e))
    if not os.path.isfile(os.path.join(ROOT, REL)):
        die("file khong ton tai tren dia: " + REL)

    # ---- Buoc 4: index tam tu HEAD ----
    if os.path.exists(TMP_INDEX):
        os.remove(TMP_INDEX)
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = os.path.abspath(TMP_INDEX)
    rc, o, e = run(["git", "read-tree", "HEAD"], ROOT, env)
    if rc != 0 or not os.path.isfile(TMP_INDEX):
        die("read-tree that bai: %s %s" % (o, e))
    print("tmp3.index tao xong: %d bytes" % os.path.getsize(TMP_INDEX), flush=True)

    # ---- Buoc 5: sao luu .git/index goc ----
    src = read_bytes(GIT_INDEX)
    with open(BAK, "wb") as f:
        f.write(src)
    if os.path.getsize(BAK) != len(src):
        die("sao luu sai size")
    print("backup: %s (%d bytes)" % (BAK, len(src)), flush=True)

    # ---- Buoc 6: ghi byte vao .git/index ----
    tmp = read_bytes(TMP_INDEX)
    try:
        write_index_bytes(GIT_INDEX, tmp)
    except OSError as ex:
        try:
            write_index_bytes(GIT_INDEX, src)
            restored = "da khoi phuc tu backup"
        except OSError as ex2:
            restored = "KHOI PHUC THAT BAI: %r" % ex2
        die("loi quyen/ghi .git/index: %r; %s" % (ex, restored), 4)

    # ---- Buoc 7: xac minh ----
    problems = []
    rc, staged_after, e = run(["git", "diff", "--cached", "--name-status"], ROOT)
    if rc != 0 or staged_after.strip() != "":
        problems.append("staged-after khong rong: %r %s" % (staged_after, e))
    rc, head2, _ = run(["git", "rev-parse", "HEAD"], ROOT)
    if head2.strip() != HEAD:
        problems.append("HEAD doi: %s -> %s" % (HEAD, head2.strip()))
    rc, d2, e = run(["git", "diff", "HEAD", "--", REL], ROOT)
    if rc != 0 or d2.strip() != "":
        problems.append("diff HEAD -- REL khong rong: %r" % d2)
    file_ok = os.path.isfile(os.path.join(ROOT, REL))
    if not file_ok:
        problems.append("file mat tren dia")
    _, st_after, _ = run(["git", "status", "--short"], ROOT)

    if problems:
        try:
            write_index_bytes(GIT_INDEX, src)
            restored = "da khoi phuc .git/index tu backup"
        except OSError as ex:
            restored = "KHOI PHUC THAT BAI: %r" % ex
        die("xac minh that bai: %s; %s" % ("; ".join(problems), restored), 5)

    # ---- Buoc 8: don dep va bao cao ----
    os.remove(TMP_INDEX)
    report = (
        "# REPORT-3 — dong bo index ve HEAD (2026-10-21)\n\n"
        "- HEAD (khong doi): `%s`\n"
        "- Staged truoc: `%s`\n"
        "- Staged sau: rong (`git diff --cached --name-status`)\n"
        "- File: `%s` — ton tai tren dia: %s; `git diff HEAD -- <file>` rong\n"
        "- Backup index goc: `index-sync/index.before-fix3.bak` (%d bytes)\n"
        "- Baseline: `index-sync/pre-fix3.txt`\n"
        "- Rollback: copy `index.before-fix3.bak` de ghi de `.git/index` "
        "(chi thay index, khong dong vao worktree/HEAD)\n\n"
        "## git status --short sau fix\n```\n%s```\n"
    ) % (HEAD, EXPECT.replace("\t", " "), REL, file_ok, len(src), st_after)
    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write(report)

    print("OK. staged-after rong; HEAD=%s; file con tren dia=%s" % (HEAD, file_ok), flush=True)
    print("backup: " + BAK, flush=True)


if __name__ == "__main__":
    main()
