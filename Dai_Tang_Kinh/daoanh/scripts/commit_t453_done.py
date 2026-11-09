# -*- coding: utf-8 -*-
"""Thêm ghi chú Admin xác nhận DONE (2026-10-30) vào task file T453 + commit."""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
TMP = os.path.join(os.environ.get("TEMP", r"C:\Users\Nam Thien\AppData\Local\Temp"), "opencode", "daoanh-stage")
os.makedirs(TMP, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

T453 = DAO + "/tasks/T453-dila-catalog-a-import-vi.md"


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def main():
    head = git(["show", "HEAD:" + T453]).decode("utf-8")
    note = ("- [2026-10-30] **Admin xác nhận DONE** — đã nạp đủ 5.747 bộ / 5.589 lượt người / 765 nơi dịch; "
            "marker `docs/tasktodo.md` đã đổi từ \"chờ Admin xác nhận DONE\" sang DONE. "
            "Bàn giao: `docs/Handoff-2026-10-22-T453-dila-catalog.md`.")
    if "[2026-10-30] **Admin xác nhận DONE**" in head:
        print("đã có ghi chú, không cần commit")
        return
    t = head.replace("updated: 2026-10-22", "updated: 2026-10-30", 1)
    t = t.rstrip("\n") + "\n" + note + "\n"
    content = t.encode("utf-8")

    parent = git(["rev-parse", "HEAD"]).decode().strip()
    tmp = os.path.join(TMP, "idx.index")
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    blob = git(["hash-object", "-w", "--stdin"], inp=content).decode().strip()
    git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, T453)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode().replace("\r", "").strip()
    print("STAGED:", staged)
    assert staged.endswith(T453), "staged sai"
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m",
               "docs(T453): ghi chu Admin xac nhan DONE 2026-10-30 (da nap du 5747 bo) + docs"]).decode().strip()
    os.remove(tmp)

    cur = open(BRANCH_REF, encoding="utf-8").read().strip()
    if cur != parent:
        raise RuntimeError("CAS fail")
    with open(BRANCH_REF, "w", encoding="utf-8", newline="\n") as f:
        f.write(new + "\n")

    tmp2 = os.path.join(TMP, "sync.index")
    git(["read-tree", new], {"GIT_INDEX_FILE": tmp2})
    data = open(tmp2, "rb").read()
    with open(REAL_INDEX, "r+b") as f:
        f.write(data); f.truncate(len(data))
    os.remove(tmp2)

    # đồng bộ worktree
    with open(os.path.join(BASE, T453.replace("/", os.sep)), "wb") as f:
        f.write(content)

    print("COMMIT", new)
    print(git(["log", "--oneline", "-3"]).decode())


if __name__ == "__main__":
    main()
