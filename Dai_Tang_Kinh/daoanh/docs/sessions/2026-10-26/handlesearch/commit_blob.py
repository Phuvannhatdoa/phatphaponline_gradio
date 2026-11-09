"""Commit 1 file theo cách BLOB, qua index tạm (GIT_INDEX_FILE) — không đụng WIP khác.

Usage: python commit_blob.py <path-relative-to-repo-root> <source-file-abs> <msgfile>
- parent = HEAD lúc commit; read-tree parent vào index tạm;
- hash-object -w <source> + update-index --cacheinfo 100644 → chỉ file này khác parent;
- write-tree → commit-tree -p parent → CAS thủ công trên ref (không os.replace / update-ref).
"""
import os
import subprocess
import sys

REPO = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DIR = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(DIR, "wt_tmp_index")


sys.stdout.reconfigure(encoding="utf-8")


def git(*args, env=None):
    r = subprocess.run(["git", *args], cwd=REPO, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout


def tmp_env():
    return dict(os.environ, GIT_INDEX_FILE=TMP)


def blob_at(rev, path):
    return git("rev-parse", "%s:%s" % (rev, path)).strip()


def main():
    path, src, msgfile = sys.argv[1], sys.argv[2], sys.argv[3]
    parent = git("rev-parse", "HEAD").strip()
    old_blob_parent = blob_at(parent, path)
    env = tmp_env()
    if os.path.exists(TMP):
        os.remove(TMP)
    git("read-tree", parent, env=env)
    blob = git("hash-object", "-w", "--", src).strip()
    git("update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path), env=env)
    staged = git("diff", "--cached", "--name-status", env=env)
    print("STAGED:\n" + staged)
    if staged.strip() != "M\t" + path:
        raise SystemExit("ABORT: staged không đúng 1 file M: %r" % staged)
    print("DIFF:\n" + git("diff", "--cached", env=env))
    tree = git("write-tree", env=env).strip()
    new = git("commit-tree", tree, "-p", parent, "-F", msgfile).strip()

    ref = git("symbolic-ref", "HEAD").strip()
    refpath = os.path.join(REPO, git("rev-parse", "--git-path", ref).strip())
    cur = git("rev-parse", "HEAD").strip()
    if cur != parent:
        raise SystemExit("ABORT CAS: HEAD đã đổi %s != parent %s" % (cur, parent))
    open(refpath, "w", encoding="utf-8").write(new + "\n")  # CAS đã kiểm tay ở trên
    os.remove(TMP)
    print("PARENT", parent)
    print("NEW", new)
    print("ref", ref, "blob_parent", old_blob_parent, "blob_new", blob)
    print("HEAD now", git("rev-parse", "HEAD").strip())


if __name__ == "__main__":
    main()
