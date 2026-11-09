import os
import subprocess
import sys

REPO = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
BRANCH = "truyen-dang-the-pho-clean"
TMP_INDEX = os.path.join(REPO, "Dai_Tang_Kinh", "daoanh", "docs", "sessions",
                         "2026-10-26", "bugs-done", "wt_tmp_index")
MSG = "docs: dong bug BUG-048/049/050/051 (Admin xac nhan DONE) + docs"

# Chi commit file nay. Task files T435-T438 KHONG nam trong commit nay (xem report).
PATHS = ["Dai_Tang_Kinh/daoanh/docs/bugs.md"]
EXPECTED_NAMES = ["M\tDai_Tang_Kinh/daoanh/docs/bugs.md"]

REF_PATH = os.path.join(REPO, ".git", "refs", "heads", BRANCH)


def git(args, use_tmp_index=False):
    env = os.environ.copy()
    if use_tmp_index:
        env["GIT_INDEX_FILE"] = TMP_INDEX
    r = subprocess.run(["git"] + args, cwd=REPO, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r


def must(args, use_tmp_index=False):
    r = git(args, use_tmp_index)
    if r.returncode != 0:
        cleanup()
        sys.exit("FAIL git %s rc=%d err=%s" % (" ".join(args), r.returncode, r.stderr.strip()))
    return r.stdout.strip()


def cleanup():
    if os.path.exists(TMP_INDEX):
        os.remove(TMP_INDEX)


def main():
    if not os.path.isfile(REF_PATH):
        sys.exit("FAIL: loose ref not found (co the packed-refs): " + REF_PATH)

    for attempt in range(1, 4):
        parent = must(["rev-parse", "HEAD"])
        print("attempt", attempt, "PARENT", parent)

        cleanup()
        must(["read-tree", parent], use_tmp_index=True)
        for p in PATHS:
            must(["add", "--", p], use_tmp_index=True)

        names = must(["diff", "--cached", "--name-status"], use_tmp_index=True).splitlines()
        if names != EXPECTED_NAMES:
            cleanup()
            sys.exit("FAIL staged list unexpected: %r (expected %r)" % (names, EXPECTED_NAMES))
        print("staged OK:", names)

        tree = must(["write-tree"], use_tmp_index=True)
        new = must(["commit-tree", tree, "-p", parent, "-m", MSG])
        print("NEW", new)

        with open(REF_PATH, "r", encoding="utf-8") as f:
            cur = f.read().strip()
        if cur != parent:
            print("RACE: ref=%s parent=%s -> retry" % (cur, parent))
            continue

        with open(REF_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(new + "\n")
        cleanup()
        print("CAS OK, ref updated to", new)
        return
    cleanup()
    sys.exit("FAIL: race 3 lan, dung. Khong ghi ref.")


if __name__ == "__main__":
    main()
