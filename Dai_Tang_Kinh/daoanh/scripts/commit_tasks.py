#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit 4 task riêng biệt (T454/T457/T455/T456) theo AGENTS §17.

Mỗi task = 1 commit → `git revert <sha>` độc lập cho từng task.
Không dùng `git add` cây thư mục (nuốt WIP session khác).
Blob + tmp index + commit-tree + CAS ghi ref trực tiếp.
"""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
WORK = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-28-commit")
STAGE = os.path.join(WORK, "blobs")   # blob chuẩn bị sẵn


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def staged_blob(path):
    """Nội dung blob đã chuẩn bị: ưu tiên file trong STAGE, fallback HEAD/worktree."""
    staged = os.path.join(STAGE, path.replace("/", "__"))
    if os.path.exists(staged):
        with open(staged, "rb") as f:
            return f.read()
    wt = os.path.join(BASE, path.replace("/", os.sep))
    if os.path.exists(wt):
        with open(wt, "rb") as f:
            return f.read()
    raise RuntimeError("không tìm thấy nội dung cho " + path)


def make_commit(parent, entries, msg):
    tmp = os.path.join(WORK, "tmp_%s.index" % str(time.time()).replace(".", ""))
    if os.path.exists(tmp):
        os.remove(tmp)
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    for path, content in entries:
        blob = git(["hash-object", "-w", "--stdin"], inp=content).decode().strip()
        git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode()
    got_lines = [x for x in staged.replace("\r", "").strip().split("\n") if x]
    got = sorted(x.split("\t", 1)[1] for x in got_lines)
    expect = sorted(p for p, _ in entries)
    if got != expect:
        raise RuntimeError("staged mismatch\n got=%s\n expect=%s" % (got, expect))
    for x in got_lines:
        if x.startswith("D\t"):
            raise RuntimeError("phat hien file bi XOA trong staged: " + x)
    print("STAGED (%d):" % len(got))
    for g in got_lines:
        print("   ", g)
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m", msg]).decode().strip()
    os.remove(tmp)
    return new


def cas_ref(parent, new):
    cur = open(BRANCH_REF, encoding="utf-8").read().strip()
    if cur != parent:
        raise RuntimeError("CAS fail: ref=%s expected=%s" % (cur, parent))
    with open(BRANCH_REF, "w", encoding="utf-8", newline="\n") as f:
        f.write(new + "\n")


def sync_real_index(new):
    tmp2 = os.path.join(WORK, "sync.index")
    if os.path.exists(tmp2):
        os.remove(tmp2)
    git(["read-tree", new], {"GIT_INDEX_FILE": tmp2})
    with open(tmp2, "rb") as f:
        data = f.read()
    with open(REAL_INDEX, "r+b") as f:
        f.write(data)
        f.truncate(len(data))
    os.remove(tmp2)
    return len(data)


def commit(parent, entries, msg, label):
    new = make_commit(parent, entries, msg)
    cas_ref(parent, new)
    n = sync_real_index(new)
    print("\n[%s] COMMIT %s (index sync %d bytes)\n" % (label, new, n))
    return new


def main():
    os.makedirs(STAGE, exist_ok=True)
    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("START PARENT", parent)

    # ================= COMMIT 1 — T454 =================
    e = [
        (DAO + "/tasks/T454-namevi-places-suffix-huy-cleanup.md", staged_blob(DAO + "/tasks/T454-namevi-places-suffix-huy-cleanup.md")),
        (DAO + "/scripts/t454_cleanup_suffix.py", staged_blob(DAO + "/scripts/t454_cleanup_suffix.py")),
        (DAO + "/scripts/t454_verify_state.py", staged_blob(DAO + "/scripts/t454_verify_state.py")),
        (DAO + "/docs/Handoff-2026-10-28-t454.md", staged_blob(DAO + "/docs/Handoff-2026-10-28-t454.md")),
    ]
    for rel in ["apply.py", "apply_simple.py", "measure.py", "t454_namevi_suffixed_20261028_190704.csv"]:
        p = DAO + "/docs/sessions/2026-10-28-t454/" + rel
        e.append((p, staged_blob(p)))
    parent = commit(parent, e,
        "feat(T454): lam sach hau to '_ Huy'/'_ Ngoa' trong namevi_map_places.name_vi (5 dong, chuyen sang note_vi) + verify 0 dong + script + handoff",
        "T454")

    # ================= COMMIT 2 — T457 =================
    e = [
        (DAO + "/tasks/T457-dila-biographies-nexus-import.md", staged_blob(DAO + "/tasks/T457-dila-biographies-nexus-import.md")),
        (DAO + "/docs/Handoff-2026-10-28-t457.md", staged_blob(DAO + "/docs/Handoff-2026-10-28-t457.md")),
        (DAO + "/docs/manifests/T457-manifest.json", staged_blob(DAO + "/docs/manifests/T457-manifest.json")),
    ]
    for rel in ["t457_dila_bio_nexus_import.py", "t457_staging_v4.py", "t457_verify.py"]:
        p = DAO + "/scripts/" + rel
        e.append((p, staged_blob(p)))
    for rel in ["dryrun_stats.py", "dryrun_stats.txt", "staging_output.txt", "staging_v4_output.txt"]:
        p = DAO + "/docs/sessions/2026-10-28-t457/" + rel
        e.append((p, staged_blob(p)))
    parent = commit(parent, e,
        "feat(T457): import DILA bio nexus A2 (21.740 nexus / 11 sach / 7.066 co nam; 36.049 person + 13.930 place link; 3 bang additive) + script + manifest + handoff",
        "T457")

    # ================= COMMIT 3 — T455 classify =================
    e = [
        (DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md", staged_blob(DAO + "/tasks/T455-person-name-vi-standardize-from-dila-catalog.md")),
        (DAO + "/docs/Handoff-2026-10-28-t455.md", staged_blob(DAO + "/docs/Handoff-2026-10-28-t455.md")),
        (DAO + "/scripts/classify_t455.py", staged_blob(DAO + "/scripts/classify_t455.py")),
        (DAO + "/scripts/t455_check_state.py", staged_blob(DAO + "/scripts/t455_check_state.py")),
    ]
    for rel in ["plan.md", "classify_out.txt", "name_vi_mismatch_A.csv", "name_vi_mismatch_B.csv", "name_vi_mismatch_C.csv"]:
        p = DAO + "/docs/sessions/2026-10-28-t455/" + rel
        e.append((p, staged_blob(p)))
    parent = commit(parent, e,
        "feat(T455): phan loai 794 dong name_vi lech thanh 3 lo A=24/B=534/C=236 (chua ghi DB, cho Admin duyet tung lo) + script + handoff",
        "T455")

    # ================= COMMIT 4 — T456 status + ROLLBACK =================
    e = [
        (DAO + "/tasks/T456-home-search-autocomplete-dila-catalog.md", staged_blob(DAO + "/tasks/T456-home-search-autocomplete-dila-catalog.md")),
        (DAO + "/docs/ROLLBACK.md", staged_blob(DAO + "/docs/ROLLBACK.md")),
    ]
    parent = commit(parent, e,
        "docs(T456): ghi trang thai cho autocomplete HOME (blocked boi T455) + rollback row T454/T457 trong ROLLBACK.md",
        "T456+ROLLBACK")

    print("=== FINAL ===")
    print("HEAD:", git(["rev-parse", "HEAD"]).decode().strip())
    print(git(["log", "--oneline", "-6"]).decode())


if __name__ == "__main__":
    main()
