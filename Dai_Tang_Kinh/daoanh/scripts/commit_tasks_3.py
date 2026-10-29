#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit 5 (ROLLBACK backup path chính xác) + Commit 6 (tasktodo markers T454-T457).

AGENTS §17: file dùng chung (ROLLBACK.md, tasktodo.md) dựng blob từ **index**,
KHÔNG lấy worktree (để không nuốt WIP của session khác: T500/T486/T485/T482/T470...).
"""
import os, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
WORK = os.path.join(BASE, DAO, "docs", "sessions", "2026-10-28-commit")
STAGE = os.path.join(WORK, "blobs")


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def index_blob(path):
    """Đọc blob của file trong INDEX (không phải worktree) — AGENTS §17."""
    out = git(["ls-files", "-s", "--", path]).decode().strip()
    if not out:
        raise RuntimeError("file khong co trong index: " + path)
    sha = out.split()[1]
    return git(["cat-file", "blob", sha])


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
            raise RuntimeError("file bi XOA: " + x)
    print("STAGED:", got_lines)
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
    sync_real_index(new)
    print("[%s] COMMIT %s\n" % (label, new))
    return new


def main():
    # ---- xoá file rác UTF-16 ở root docs/ (do tôi tạo nhầm khi probe) ----
    junk = os.path.join(BASE, "docs", "tasktodo.md")
    if os.path.exists(junk):
        with open(junk, "rb") as f:
            head = f.read(4)
        if head.startswith(b"\xff\xfe"):
            os.remove(junk)
            print("removed junk UTF-16 root docs/tasktodo.md")

    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("START PARENT", parent)

    # ================= COMMIT 5 — ROLLBACK backup path chính xác =================
    RB = DAO + "/docs/ROLLBACK.md"
    staged = os.path.join(STAGE, RB.replace("/", "__"))
    with open(staged, "rb") as f:
        rb = f.read()
    parent = commit(parent, [(RB, rb)],
        "docs: chinh xac backup path T454 trong ROLLBACK.md (lineage_t454_20261028_201150.db + 5 dila_id)",
        "ROLLBACK-fix")

    # ================= COMMIT 6 — tasktodo markers T454..T457 =================
    TODO = DAO + "/docs/tasktodo.md"
    todo = index_blob(TODO).decode("utf-8")
    nl = "\r\n" if "\r\n" in todo else "\n"
    blocks = []
    blocks.append(
        "<!-- T454:START -->" + nl +
        "> **[2026-10-29 · T454 — làm sạch hậu tố \"_ Huý\"/\"_ Ngoa\" trong `namevi_map_places.name_vi`] ✅ DONE.** 5 dòng đã sửa "
        "(hậu tố chuyển sang `note_vi`, không mất thông tin; không đụng `places_dila`). Backup `data/backups/lineage_t454_20261028_201150.db`. "
        "Verify: `python -X utf8 scripts/t454_verify_state.py` → dòng còn hậu tố thật = **0** (phải dùng `LIKE '%\\_ Huý%' ESCAPE '\\'`; `LIKE '%_ Huý%'` cho 2 false-positive). "
        "Commit `01ee030f`. Revert: `python -X utf8 scripts/t454_cleanup_suffix.py --revert` | `git revert 01ee030f`. Task: `tasks/T454-namevi-places-suffix-huy-cleanup.md`." + nl +
        "<!-- T454:END -->")
    blocks.append(
        "<!-- T455:START -->" + nl +
        "> **[2026-10-29 · T455 — chuẩn hoá tên người Việt (794 lệch + 532 sót Hán)] 🔄 IN_PROGRESS — đã phân loại, chờ Admin duyệt lô (CHƯA ghi DB).** "
        "Phân loại tự động 794 dòng (`scripts/classify_t455.py`): **Lô A = 24** (ZQ sai rõ → sửa) · **Lô B = 534** (alias cùng người → giữ, ghi alias) · "
        "**Lô C = 236** (khác quy ước chính tả → sửa). CSV: `docs/sessions/2026-10-28-t455/name_vi_mismatch_{A,B,C}.csv`. "
        "Quy tắc bắt buộc: tên Việt luôn `source_id=5` (ZQLOCAL), **không** gán tên Việt cho nguồn DILA (`source_id=1`); không sửa `people.name_zh`. "
        "Còn chờ Admin: Q3b (thứ tự lô), Q3c (duyệt bảng lịch sử additive `people_name_vi_history`), mẫu 20 dòng/lô. "
        "Commit `a5d2ec25`. Task: `tasks/T455-person-name-vi-standardize-from-dila-catalog.md`." + nl +
        "<!-- T455:END -->")
    blocks.append(
        "<!-- T456:START -->" + nl +
        "> **[2026-10-29 · T456 — autocomplete ô Search HOME (gợi ý kinh lục DILA / người / địa danh)] ⏳ PENDING — blocked bởi T455.** "
        "Thứ tự N4: T454 ✅ → T457 ✅ → T455 (đang phân loại) → T456. Phụ thuộc `depends_on: [T453, T416, T450]` — T453 đã nạp đủ 5.747 bộ (chờ Admin xác nhận DONE), "
        "T416/T450 (autocomplete + FTS) đã có. Cần Admin duyệt phương án triển khai trước khi sửa `index.html` + route mới. "
        "Commit `38ffb5f4`. Task: `tasks/T456-home-search-autocomplete-dila-catalog.md`." + nl +
        "<!-- T456:END -->")
    blocks.append(
        "<!-- T457:START -->" + nl +
        "> **[2026-10-29 · T457 — import DILA bio nexus (A2: array đầy đủ person+place)] ✅ DONE.** "
        "Dry-run: 21.740 nexus / 11 sách / 7.066 có năm (32,5%). Apply 3 bảng additive (`nexus_events` cũ 10.458 dòng **không** đụng): "
        "`dila_bio_nexus` = 21.740 dòng · `dila_bio_nexus_person` = 36.049 link · `dila_bio_nexus_place` = 13.930 link; index `idx_bn_book`/`idx_bn_person`/`idx_bn_year`/`idx_bn_place`. "
        "Backup `data/backups/lineage_t457_20261029_094901.db`. Manifest SHA-256: `docs/manifests/T457-manifest.json`. "
        "Commit `2686da0a`. Revert: `python -X utf8 scripts/t457_dila_bio_nexus_import.py --revert` (DROP 3 bảng + 4 index) | `git revert 2686da0a`. "
        "Task: `tasks/T457-dila-biographies-nexus-import.md`." + nl +
        "<!-- T457:END -->")

    anchor = "<!-- T461:END -->"
    assert anchor in todo, "khong tim thay anchor T461:END trong index tasktodo"
    todo_new = todo.replace(anchor, anchor + nl + nl + (nl + nl).join(blocks), 1)
    parent = commit(parent, [(TODO, todo_new.encode("utf-8"))],
        "docs(tasktodo): them marker T454/T455/T456/T457 (4 task N4 da/đang lam) + docs",
        "tasktodo")

    print("=== FINAL ===")
    print("HEAD:", git(["rev-parse", "HEAD"]).decode().strip())
    print(git(["log", "--oneline", "-7"]).decode())


if __name__ == "__main__":
    main()
