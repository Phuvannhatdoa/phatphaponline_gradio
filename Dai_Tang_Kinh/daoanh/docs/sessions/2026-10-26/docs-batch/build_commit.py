import os, subprocess, shutil, sys

ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
BATCH = os.path.join(ROOT, DAO, "docs", "sessions", "2026-10-26", "docs-batch")
os.chdir(ROOT)
BRANCH_REF = os.path.join(ROOT, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(ROOT, ".git", "index")

T435 = DAO + "/tasks/T435-bug048-claude-column-no-count.md"
TODO = DAO + "/docs/tasktodo.md"
MSG = "docs: T435 xac nhan DONE (BUG-048) + T453 chot ban ghi moi + docs"
REPORT_LINE = ("**Admin xác nhận DONE (2026-10-26).** Báo cáo: docs/T435_BUG048_FINAL_REPORT.md (BUG-048). "
               "Trạng thái DONE đã ghi trong docs/bugs.md (commit b1832c7f).")
T453_NOTE = ("> **Admin chốt 2026-10-26: lấy bản ghi mới nhất làm chuẩn** (nguồn: `tasks/T453-dila-catalog-a-import-vi.md` "
             "— nhật ký 2026-10-25 16:00, Admin Notes 2026-10-25 18:33; mtime file 2026-10-26 13:50). "
             "Trạng thái T453 theo đó: (A)+(B) đã xong, 26 tạng đã nạp (5.747 bộ), chờ Admin xác nhận DONE.")


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def head_blob(path):
    return git(["show", "HEAD:" + path])


def build_t435(raw):
    txt = raw.decode("utf-8")
    assert "Admin xác nhận DONE (2026-10-26)" not in txt, "T435 already marked"
    nl = "\r\n" if "\r\n" in txt else "\n"
    body = txt if txt.endswith("\n") else txt + "\n"
    return (body + nl + REPORT_LINE + nl).encode("utf-8")


def build_todo(raw):
    txt = raw.decode("utf-8")
    assert "Admin chốt 2026-10-26" not in txt, "tasktodo already has note"
    assert txt.count("<!-- T453:END -->") == 1
    assert "<!-- T453:START -->" in txt
    new = txt.replace("\n<!-- T453:END -->", "\n" + T453_NOTE + "\n<!-- T453:END -->", 1)
    assert new != txt
    return new.encode("utf-8")


def attempt(n):
    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("ATTEMPT", n, "PARENT", parent)
    b435 = build_t435(head_blob(T435))
    btodo = build_todo(head_blob(TODO))
    blob435 = git(["hash-object", "-w", "--stdin"], inp=b435).decode().strip()
    blobtodo = git(["hash-object", "-w", "--stdin"], inp=btodo).decode().strip()
    print("BLOB T435", blob435)
    print("BLOB TODO", blobtodo)

    tmp = os.path.join(BATCH, "tmp.index")
    if os.path.exists(tmp):
        os.remove(tmp)
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob435, T435)], env)
    git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blobtodo, TODO)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode()
    print("STAGED:\n" + staged)
    got = sorted(staged.replace("\r", "").strip().split("\n"))
    expect = sorted(["M\t" + T435, "M\t" + TODO])
    if got != expect:
        raise RuntimeError("staged mismatch")
    numstat = git(["diff", "--cached", "--numstat"], env).decode()
    print("NUMSTAT:\n" + numstat)
    for line in numstat.strip().split("\n"):
        add, dele, _ = line.split("\t")
        allowed = {"tasktodo.md": "1", "T435-bug048-claude-column-no-count.md": "2"}
        name = line.split("\t")[2].split("/")[-1]
        assert dele == "0" and add == allowed[name], "unexpected change: " + line
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m", MSG]).decode().strip()
    print("NEW", new)
    return parent, new, tmp


def main():
    for n in range(1, 4):
        parent, new, tmp = attempt(n)
        cur = open(BRANCH_REF, encoding="utf-8").read().strip()
        print("CAS current ref", cur, "expected", parent)
        if cur == parent:
            with open(BRANCH_REF, "w", encoding="utf-8", newline="\n") as f:
                f.write(new + "\n")
            print("REF WRITTEN")
            break
        print("HEAD moved, retry")
        os.remove(tmp)
    else:
        print("ABORT: CAS failed 3 times")
        sys.exit(2)

    # sync real index to new HEAD (temp index from new commit, then in-place bytes write)
    tmp2 = os.path.join(BATCH, "sync.index")
    if os.path.exists(tmp2):
        os.remove(tmp2)
    git(["read-tree", new], {"GIT_INDEX_FILE": tmp2})
    with open(tmp2, "rb") as f:
        data = f.read()
    with open(REAL_INDEX, "r+b") as f:
        f.write(data)
        f.truncate(len(data))
    os.remove(tmp2)
    if os.path.exists(tmp):
        os.remove(tmp)
    print("REAL INDEX SYNCED", len(data))


if __name__ == "__main__":
    main()
