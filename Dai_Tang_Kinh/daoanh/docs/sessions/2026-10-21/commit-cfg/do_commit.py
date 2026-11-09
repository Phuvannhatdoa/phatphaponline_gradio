"""One-off: commit only Dai_Tang_Kinh/daoanh/.opencode/opencode.json via temp index.

Does NOT touch the real .git/index, does NOT push, does NOT use update-ref.
"""
import os
import subprocess
import sys

REPO_ROOT = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
BRANCH = "truyen-dang-the-pho-clean"
TARGET = "Dai_Tang_Kinh/daoanh/.opencode/opencode.json"
MSG = "chore: cho phep git update-index (cacheinfo theo AGENTS 17) + docs"
OUT_DIR = os.path.join(REPO_ROOT, "Dai_Tang_Kinh", "daoanh", "docs", "sessions",
                       "2026-10-21", "commit-cfg")
TMP_INDEX = os.path.abspath(os.path.join(OUT_DIR, "tmp.index"))
REF_PATH = os.path.join(REPO_ROOT, ".git", "refs", "heads", BRANCH)


def run(args, env, check=True):
    p = subprocess.run(args, cwd=REPO_ROOT, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise SystemExit(f"ABORT: {' '.join(args)} -> rc={p.returncode}\n"
                         f"stdout: {p.stdout}\nstderr: {p.stderr}")
    return p.stdout.strip()


def main():
    base_env = os.environ.copy()
    base_env.pop("GIT_INDEX_FILE", None)

    parent = run(["git", "rev-parse", "HEAD"], base_env)
    branch = run(["git", "branch", "--show-current"], base_env)
    if branch != BRANCH:
        raise SystemExit(f"ABORT: branch={branch!r}, expected {BRANCH!r}")

    os.makedirs(OUT_DIR, exist_ok=True)
    if os.path.exists(TMP_INDEX):
        os.remove(TMP_INDEX)

    env = base_env.copy()
    env["GIT_INDEX_FILE"] = TMP_INDEX
    try:
        run(["git", "read-tree", parent], env)
        run(["git", "add", "--", TARGET], env)
        staged = run(["git", "diff", "--cached", "--name-status"], env)
        expected = f"M\t{TARGET}"
        if staged != expected:
            raise SystemExit(f"ABORT: staged diff mismatch:\n{staged!r}\n"
                             f"expected {expected!r}")
        tree = run(["git", "write-tree"], env)
        new = run(["git", "commit-tree", tree, "-p", parent, "-m", MSG], base_env)

        # CAS thu cong
        with open(REF_PATH, "r", encoding="utf-8") as f:
            cur = f.read().strip()
        if cur != parent:
            raise SystemExit(f"ABORT: ref moved. current={cur} parent={parent}")
        with open(REF_PATH, "w", encoding="utf-8") as f:
            f.write(new + "\n")

        print("PARENT:", parent)
        print("NEW:", new)
        print("TREE:", tree)
        print("DIFF --cached (verified):", staged)
    finally:
        for p in (TMP_INDEX, TMP_INDEX + ".lock"):
            if os.path.exists(p):
                os.remove(p)

    print("--- git show --stat --oneline NEW (no temp index) ---")
    print(run(["git", "show", "--stat", "--oneline", new], base_env))


if __name__ == "__main__":
    sys.exit(main())
