"""Commit các thay đổi hiện tại thành NHIỀU commit theo nhóm, để mỗi nhóm revert riêng được.

Quy trình (AGENTS §14/§17): index tạm từ HEAD, ghi đúng các file của nhóm, write-tree,
commit-tree, cập nhật ref với kiểm tra CAS (parent phải vẫn là HEAD). Không dùng git add
cả thư mục. Sau cùng đồng bộ index thật cho đúng các đường dẫn đã commit.
"""
import os
import subprocess
import sys

REPO = "E:/Backup 2025/QuaiTieuTu/Anan Son/phatphaponline_gradio/truyenthua/visjs-app"
TOP = os.path.join(REPO, "Dai_Tang_Kinh")
BRANCH = "truyen-dang-the-pho-clean"
TRAILER = "Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"

def git(*a, env=None, check=True):
    r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, env=env)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {r.stderr.decode('utf-8','replace')}")
    return r.stdout.decode("utf-8", "replace").strip()

def files_changed():
    out = git("status", "--porcelain", "-z", "--untracked-files=all", check=False)
    res = []
    for entry in out.split("\0"):
        if len(entry) > 3:
            res.append(entry[3:])
    return res

def group_of(p):
    q = p.replace("\\", "/")
    if q.startswith("Dai_Tang_Kinh/dashboard/"):
        return "G1-dashboard"
    if "/admin/" in q and q.endswith((".html", ".js", ".css")) or q.endswith("admin/sync_log.html"):
        return "G2-admin-ui"
    if q.endswith(("places.html",)):
        return "G2-admin-ui"
    if q.endswith(("app.py", "local_gateway.py", "core.py", "routes_translate.py", "db_core.py")):
        return "G3-backend-fix"
    if "/scripts/" in q or "/tests/" in q:
        return "G4-scripts-tests"
    if "/tasks/" in q or "/docs/" in q or q.endswith(("CLAUDE.md", "tasktodo.md")) or "/.opencode/" in q:
        return "G5-tasks-docs"
    return "G6-other"

MSG = {
    "G1-dashboard": "dashboard: khôi phục thư mục dashboard/ (agent_team, serve.py) từ nhánh WIP + + docs",
    "G2-admin-ui": "admin-ui: khôi phục tab Catalog/Xác Minh Tác Giả, menu admin, sync_log, places tree-source + + docs",
    "G3-backend-fix": "backend: khôi phục route dịch lại T447 (pre-commit check, HASH_MISMATCH) và sửa cạnh DILA-only T506 + + docs",
    "G4-scripts-tests": "scripts+tests: khôi phục công cụ và test từ WIP 2026-11-01 + + docs",
    "G5-tasks-docs": "tasks+docs: khôi phục task/tài liệu từ WIP 2026-11-01 và cập nhật trạng thái + + docs",
    "G6-other": "chore: khôi phục các file còn lại từ WIP 2026-11-01 + + docs",
}

def commit_group(name, paths, parent):
    idx = os.path.join(REPO, ".git", f"groupcommit_{name}.idx")
    env = dict(os.environ, GIT_INDEX_FILE=idx)
    try:
        git("read-tree", parent, env=env)
        for p in paths:
            full = os.path.join(REPO, p)
            if os.path.exists(full):
                sha = git("hash-object", "-w", "--path", p, "--", p)
                git("update-index", "--add", "--cacheinfo", f"100644,{sha},{p}", env=env)
            else:
                git("update-index", "--force-remove", "--", p, env=env)
        tree = git("write-tree", env=env)
        msg = f"{MSG[name]}\n\n{TRAILER}"
        commit = git("commit-tree", tree, "-p", parent, "-m", msg)
        git("update-ref", f"refs/heads/{BRANCH}", commit, parent)
        return commit
    finally:
        if os.path.exists(idx):
            os.unlink(idx)

def sync_real_index(paths):
    for p in paths:
        full = os.path.join(REPO, p)
        if os.path.exists(full):
            sha = git("rev-parse", f"HEAD:{p}", check=False)
            if sha:
                git("update-index", "--cacheinfo", f"100644,{sha},{p}")

def main(dry):
    files = files_changed()
    groups = {}
    for p in files:
        if "/.codegraph/" in p.replace("\\", "/") or p.endswith(".codegraph/"):
            continue
        groups.setdefault(group_of(p), []).append(p)
    for g, ps in groups.items():
        print(g, len(ps))
    if dry:
        return 0
    order = ["G1-dashboard", "G2-admin-ui", "G3-backend-fix", "G4-scripts-tests", "G5-tasks-docs", "G6-other"]
    done = []
    for g in order:
        ps = groups.get(g)
        if not ps:
            continue
        parent = git("rev-parse", f"refs/heads/{BRANCH}")
        c = commit_group(g, ps, parent)
        done.append((g, c[:10], len(ps)))
        print("COMMIT", g, c[:10], len(ps))
    all_paths = [p for g in order for p in groups.get(g, [])]
    sync_real_index(all_paths)
    print("HEAD", git("rev-parse", "--short", "HEAD"))
    return 0

if __name__ == "__main__":
    sys.exit(main("--dry" in sys.argv))
