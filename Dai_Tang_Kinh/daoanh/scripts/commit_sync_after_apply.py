#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit script sync + cập nhật Handoff với kết quả apply T455 phương án A."""
import os, re, subprocess, sys, time

BASE = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
DAO = "Dai_Tang_Kinh/daoanh"
os.chdir(BASE)
BRANCH_REF = os.path.join(BASE, ".git", "refs", "heads", "truyen-dang-the-pho-clean")
REAL_INDEX = os.path.join(BASE, ".git", "index")
TMP = os.path.join(os.environ.get("TEMP", r"C:\Users\Nam Thien\AppData\Local\Temp"), "opencode", "daoanh-stage")
os.makedirs(TMP, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HO = DAO + "/docs/Handoff-2026-10-29-n4-t454-t457-batch.md"


def git(args, env=None, inp=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(["git"] + args, capture_output=True, env=e, input=inp)
    if r.returncode != 0:
        raise RuntimeError("git %s rc=%s err=%s" % (args, r.returncode, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def read(rel):
    with open(os.path.join(BASE, rel.replace("/", os.sep)), "rb") as f:
        return f.read()


def main():
    # cập nhật Handoff: thêm kết quả apply T455 phương án A
    t = git(["show", "HEAD:" + HO]).decode("utf-8")
    rep = [
        ("| **HEAD** | `828ae63f1172c6c7d73a901517a6144995ebc952` |",
         "| **HEAD** | `f241ebd432143ae565b4e75b100c69ec03effaef` |"),
        ("| **Commit mới** | **13** (xem §6) |",
         "| **Commit mới** | **17** (xem §6) |"),
        ("| **DB đã ghi** | T454 (5 dòng UPDATE) · T457 (3 bảng additive) — **T455 chưa ghi** |",
         "| **DB đã ghi** | T454 (5 dòng UPDATE) · T457 (3 bảng additive) · **T455 phương án A (258 dòng UPDATE + bảng lịch sử 794 dòng)** |"),
        ("| 1 | **T455 — apply 3 lô** | Đã phân loại xong, chờ duyệt | Q3b: ưu tiên lô nào (theo `so_lan` hay nhóm sót Hán)? Q3c: duyệt bảng lịch sử additive `people_name_vi_history` không? Mẫu 20 dòng/lô OK chứ? |",
         "| 1 | **T455 — ✅ ĐÃ APPLY phương án A** (Admin chọn 2026-10-30) | 258 dòng sửa + 534 alias ghi chú + bảng lịch sử 794 dòng | ~~Q3b/Q3c~~ → Admin đã chọn **A** |"),
    ]
    for old, new in rep:
        if old not in t:
            print("!! khong khop:", old[:60].replace("\n", " "))
        else:
            t = t.replace(old, new, 1)

    note = """
---

## Phụ lục — T455 phương án A đã APPLY (2026-10-30)

Admin chọn **phương án A** (sửa 260 dòng có bằng chứng rõ, giữ 534 lô B ghi chú alias). Đã apply + verify + commit.

| Hạng mục | Trước | Sau |
|---|---|---|
| Bảng lịch sử `people_name_vi_history` | không tồn tại | **794 dòng** (additive) — 258 `updated` / 534 `kept_alias` / 1 `unchanged` / 1 `skipped_kept` |
| `people.name_vi` được UPDATE | — | **258 dòng** (lô A 22 + lô C 236) |
| Lô B 534 dòng | — | **không đổi** (chỉ ghi chú alias) |
| `people.name_vi` còn sót Hán | 422 | **405** (−17) |
| `people.name_zh` / `source_id` | — | **không đổi** |

- **Backup**: `data/backups/lineage_t455_20261030_144710.db` · **batch**: `T455-planA-20261030`
- **2 dòng đặc biệt**: `A000142` sửa tay (`Chân Tĩnh Thiên Trác` — `頙` không có trong bảng đọc) · `A001428` bỏ qua (DB đã là "Di Lặc Bồ Tát" tốt hơn Cloud "Di Lặc"; UPDATE có điều kiện nên tự bỏ qua)
- **Revert**: `python -X utf8 scripts/t455_apply_planA.py --revert` | dòng `ROLLBACK.md` 2026-10-30
- **Báo cáo**: `docs/reports/T455-apply-planA-report.md` · đề xuất: `docs/sessions/2026-10-30-t455-apply/t455_proposal_planA.csv`
- **Pipeline sau apply**: `npm run pipeline` **exit 0** ✅ · `dup:ids` **PASS** ✅

**Còn lại**: 405 tên sót Hán (nhóm "532 tên sót Hán" — không có bản Cloud để đối chiếu → task riêng) · 534 alias lô B (task riêng, không chặn T456) · **T456** autocomplete HOME.
"""
    if "Phụ lục — T455 phương án A đã APPLY" not in t:
        t = t.rstrip("\n") + "\n" + note

    entries = [
        (HO, t.encode("utf-8")),
        (DAO + "/scripts/sync_after_t455_apply.py", read(DAO + "/scripts/sync_after_t455_apply.py")),
        (DAO + "/scripts/commit_t455_apply.py", read(DAO + "/scripts/commit_t455_apply.py")),
        (DAO + "/scripts/commit_sync_after_apply.py", read(DAO + "/scripts/commit_sync_after_apply.py")),
    ]

    parent = git(["rev-parse", "HEAD"]).decode().strip()
    print("PARENT", parent)
    tmp = os.path.join(TMP, "idx.index")
    env = {"GIT_INDEX_FILE": tmp}
    git(["read-tree", parent], env)
    for path, content in entries:
        blob = git(["hash-object", "-w", "--stdin"], inp=content).decode().strip()
        git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path)], env)
    staged = git(["diff", "--cached", "--name-status"], env).decode().replace("\r", "").strip()
    print("STAGED:\n" + staged)
    got = sorted(x.split("\t", 1)[1] for x in staged.splitlines() if x)
    ent = dict(entries)
    for g in got:
        assert g in ent, "staged ngoai danh sach: " + g
    for path, content in entries:
        if path not in got:
            assert git(["rev-parse", "HEAD:" + path]).decode().strip() == \
                   git(["hash-object", "--stdin"], inp=content).decode().strip(), \
                   "chua staged nhung khac HEAD: " + path
    tree = git(["write-tree"], env).decode().strip()
    new = git(["commit-tree", tree, "-p", parent, "-m",
               "docs: handoff phu luc T455 phuong an A da apply (258 dong sua, 794 dong lich su, pipeline xanh) + script sync + docs"]).decode().strip()
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

    print("COMMIT", new)
    print(git(["log", "--oneline", "-3"]).decode())


if __name__ == "__main__":
    main()
