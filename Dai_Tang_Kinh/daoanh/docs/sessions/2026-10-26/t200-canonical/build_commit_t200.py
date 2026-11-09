# -*- coding: utf-8 -*-
"""Commit T200 bằng blob + index tạm (không đụng worktree ROLLBACK.md có WIP phiên khác).
CAS ref thủ công; retry tối đa 3 lần nếu HEAD đổi."""
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

REPO = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAOANH = os.path.join(REPO, "Dai_Tang_Kinh", "daoanh")
SESS = os.path.join(DAOANH, "docs", "sessions", "2026-10-26", "t200-canonical")
TMP_IDX = os.path.join(SESS, "tmp.index")
REAL_IDX = os.path.join(REPO, ".git", "index")
REL_SCRIPT = "Dai_Tang_Kinh/daoanh/scripts/t200_canonical_name_row.py"
REL_RB = "Dai_Tang_Kinh/daoanh/docs/ROLLBACK.md"
SCRIPT_PATH = os.path.join(DAOANH, "scripts", "t200_canonical_name_row.py")
MSG = ("fix: them dong canonical A001984 vao vn_person_authority "
       "(additive, giu dong alias) + script t200 + rollback row + docs")

BLOCK = """
## T200 — dòng canonical A001984 (2026-10-28)

| Migration | Lệnh revert | Backup | Ngày |
|---|---|---|---|
| T200 canonical row A001984 | `python -X utf8 scripts/t200_canonical_name_row.py --revert` (DELETE đúng 1 dòng `id='canonical_A001984'` AND `dila_id='A001984'`; KHÔNG đụng dòng `alias_A001984`) | `Dai_Tang_Kinh/daoanh/data/backups/lineage_t200_20261028_115712.db` | 2026-10-28 |

- Lệnh apply: `python -X utf8 scripts/t200_canonical_name_row.py --apply` (INSERT 1 dòng vào `vn_person_authority`: id `canonical_A001984`, name_vi `Quy Sơn Linh Hựu` (= `people.name_vi`), name_zh `靈祐`, dila_id `A001984`, status `auto_ttl`, ttl_filename `TS-Quy-Son-Linh-Huu` (lấy từ dòng alias), entity_type `monk`).
- Ghi chú: additive, +1 dòng (1511 → 1512), dữ liệu cũ không mất; dòng `alias_A001984` giữ nguyên. Admin đã duyệt riêng cho A001984 (gỡ cổng `test:t200`). Không sửa bảng `people`.
""".lstrip("\n")


def run(args, env=None, check=True):
    r = subprocess.run(args, cwd=REPO, env=env, capture_output=True)
    if check and r.returncode != 0:
        raise RuntimeError("%s\n%s" % (" ".join(args), r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8", "replace").strip()


def tmp_env():
    e = dict(os.environ)
    e["GIT_INDEX_FILE"] = TMP_IDX
    return e


def build(parent):
    rb_old = subprocess.run(["git", "cat-file", "blob", "%s:%s" % (parent, REL_RB)],
                            cwd=REPO, capture_output=True, check=True).stdout
    if not rb_old.endswith(b"\n"):
        rb_old += b"\n"
    rb_new = rb_old + b"\n" + BLOCK.encode("utf-8")
    new_path = os.path.join(SESS, "ROLLBACK.new.md")
    with open(new_path, "wb") as f:
        f.write(rb_new)
    rb_blob = run(["git", "hash-object", "-w", new_path])
    sc_blob = run(["git", "hash-object", "-w", SCRIPT_PATH])
    if os.path.exists(TMP_IDX):
        os.remove(TMP_IDX)
    env = tmp_env()
    run(["git", "read-tree", parent], env=env)
    run(["git", "update-index", "--add", "--cacheinfo", "100644,%s,%s" % (sc_blob, REL_SCRIPT)], env=env)
    run(["git", "update-index", "--cacheinfo", "100644,%s,%s" % (rb_blob, REL_RB)], env=env)
    names = run(["git", "diff", "--cached", "--name-status"], env=env)
    return rb_blob, sc_blob, names, env


def main():
    print("== PRE: HEAD / ref / real index ==")
    print("HEAD0 =", run(["git", "rev-parse", "HEAD"]))
    print("REF   =", run(["git", "symbolic-ref", "HEAD"]))
    print("real index diff --cached (must be empty):",
          repr(run(["git", "diff", "--cached", "--name-status"])))

    new = None
    for attempt in range(1, 4):
        parent = run(["git", "rev-parse", "HEAD"])
        rb_blob, sc_blob, names, env = build(parent)
        print("\n== attempt %d parent=%s ==" % (attempt, parent))
        print("tmp index diff --cached:\n" + names)
        expect = "M\t%s\nA\t%s" % (REL_RB, REL_SCRIPT)
        if names.replace("\r", "") != expect:
            raise SystemExit("ABORT: name-status không đúng 2 file mong đợi")
        tree = run(["git", "write-tree"], env=env)
        cand = run(["git", "commit-tree", tree, "-p", parent, "-m", MSG])
        ref = run(["git", "symbolic-ref", "HEAD"])
        refpath = os.path.join(REPO, ".git", *ref.split("/"))
        cur = run(["git", "rev-parse", "HEAD"])
        if cur != parent:
            print("HEAD đã đổi (%s != %s) → dựng lại" % (cur, parent))
            continue
        # CAS thủ công: kiểm file ref trước khi ghi
        if os.path.exists(refpath):
            with open(refpath, "rb") as f:
                on_disk = f.read().decode().strip()
            if on_disk != parent:
                print("CAS fail: ref on disk=%s != parent → dựng lại" % on_disk)
                continue
        with open(refpath, "wb") as f:
            f.write((cand + "\n").encode())
        new = cand
        print("CAS OK → NEW =", new)
        break
    if new is None:
        raise SystemExit("ABORT: không commit được sau 3 lần")

    print("\n== VERIFY ==")
    print("HEAD now =", run(["git", "rev-parse", "HEAD"]))
    print(run(["git", "show", "--stat", "--format=%H%n%P%n%s", new]))

    # Đồng bộ index thật về HEAD mới — chỉ khi index thật trước đó sạch (đã kiểm ở PRE)
    real_vs_new = run(["git", "diff", "--cached", "--name-status"], check=True)
    print("\nreal index vs NEW HEAD (dự kiến: D script, M ROLLBACK):")
    print(real_vs_new)
    exp_real = "M\t%s\nD\t%s" % (REL_RB, REL_SCRIPT)
    if real_vs_new.replace("\r", "") != exp_real:
        raise SystemExit("STOP: index thật có staged lạ — KHÔNG đồng bộ; báo Admin")
    shutil.copy2(REAL_IDX, os.path.join(SESS, "index.bak"))
    with open(TMP_IDX, "rb") as f:
        data = f.read()
    with open(REAL_IDX, "r+b") as f:
        f.write(data)
        f.truncate()
    print("real index synced; index.bak =", os.path.join(SESS, "index.bak"))
    print("git diff --cached after sync (must be empty):",
          repr(run(["git", "diff", "--cached", "--name-status"])))
    os.remove(TMP_IDX)
    print("PARENT =", run(["git", "log", "--format=%P", "-1", new]))
    print("NEW    =", new)


if __name__ == "__main__":
    main()
