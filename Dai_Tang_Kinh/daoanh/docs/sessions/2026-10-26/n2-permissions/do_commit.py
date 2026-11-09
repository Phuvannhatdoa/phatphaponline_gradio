"""Commit 3 file đích danh bằng index tạm (không đụng .git/index thật).

Quy trình: parent = HEAD mới nhất -> read-tree parent vào index tạm -> add đích danh ->
kiểm name-status phải đúng EXPECTED -> write-tree -> commit-tree -> CAS thủ công trên
file ref (đọc lại, so với parent; ghi tại chỗ, không update-ref, không os.replace).
Tối đa 3 lần thử nếu ref bị đổi giữa chừng.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF_NAME = "truyen-dang-the-pho-clean"
TMP_INDEX = os.path.join(HERE, "wt_tmp_index")
FILES = [
    "Dai_Tang_Kinh/daoanh/.opencode/agents/daoanh-qa.md",
    "Dai_Tang_Kinh/daoanh/.opencode/agents/tich-hop.md",
    "Dai_Tang_Kinh/daoanh/scripts/verify_design_compliance.py",
]
EXPECTED = {("M", f) for f in FILES}
MSG = "fix: khoi phuc quyen agent (qa sqlite deny, tich-hop edit docs-only) + test compliance exit 1 + docs"


def repo_root():
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE,
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()


REPO = repo_root()


def git(args, index=None):
    env = os.environ.copy()
    if index:
        env["GIT_INDEX_FILE"] = index
    r = subprocess.run(["git"] + args, cwd=REPO, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%d: %s" % (" ".join(args), r.returncode, r.stderr.strip()))
    return r.stdout


def ref_path():
    gitdir = git(["rev-parse", "--git-dir"]).strip()
    return os.path.join(REPO, gitdir, "refs", "heads", REF_NAME)


def read_ref():
    p = ref_path()
    if not os.path.isfile(p):
        raise RuntimeError("không thấy file ref (có thể packed-refs): " + p)
    with open(p, encoding="utf-8") as f:
        return f.read().strip()


def cleanup():
    for name in (TMP_INDEX, TMP_INDEX + ".lock"):
        if os.path.exists(name):
            os.remove(name)


def build(parent):
    cleanup()
    git(["read-tree", parent], index=TMP_INDEX)
    git(["add", "--"] + FILES, index=TMP_INDEX)
    lines = [l for l in git(["diff", "--cached", "--name-status"], index=TMP_INDEX).splitlines() if l.strip()]
    got = set()
    for line in lines:
        st, path = line.split("\t", 1)
        got.add((st.strip(), path.strip()))
    if got != EXPECTED:
        raise RuntimeError("staged KHÔNG đúng mong đợi: %s" % lines)
    return git(["write-tree"], index=TMP_INDEX).strip(), lines


def main():
    for attempt in range(1, 4):
        parent = git(["rev-parse", "HEAD"]).strip()
        ref_val = read_ref()
        if ref_val != parent:
            print("[attempt %d] ref=%s != HEAD=%s -> thử lại" % (attempt, ref_val, parent))
            continue
        tree, staged = build(parent)
        new = git(["commit-tree", tree, "-p", parent, "-m", MSG], index=TMP_INDEX).strip()
        # CAS thủ công: đọc lại ref ngay trước khi ghi
        if read_ref() != parent:
            print("[attempt %d] ref đổi giữa chừng -> dựng lại từ HEAD mới" % attempt)
            continue
        with open(ref_path(), "w", encoding="utf-8", newline="\n") as f:
            f.write(new + "\n")
        cleanup()
        print("PARENT=" + parent)
        print("NEW=" + new)
        print("STAGED:")
        for l in staged:
            print("  " + l)
        return 0
    cleanup()
    print("BLOCKED: ref đổi liên tục sau 3 lần thử; không commit.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
