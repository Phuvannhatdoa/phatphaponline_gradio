# -*- coding: utf-8 -*-
"""Dung commit cô lập cho 1 task (T465 | T467 | T469) tu HEAD hien tai.

Nguyen tac:
- Noi dung commit = HEAD blob + CHI cac doan cua task (lay tu worktree bang neo cu the).
- Ghi blob bang git hash-object -w --no-filters; index tam GIT_INDEX_FILE (trong scoped-tasks/).
- Kiem: danh sach file dung; moi dong '+' cua commit deu co trong worktree (khong bịa noi dung).
- CAS thu cong tren .git/refs/heads/<branch>; that bai thi dung lai toi da 3 lan.
Usage: python -X utf8 build_scoped_commit.py <T465|T467|T469> [--dry]
"""
import os
import re
import subprocess
import sys

REPO = r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app"
BRANCH = "truyen-dang-the-pho-clean"
D = "Dai_Tang_Kinh/daoanh/"
APP = D + "app.py"
IDXH = D + "index.html"
NVM = D + "admin/namevimap.html"
OUT = os.path.join(REPO, "Dai_Tang_Kinh", "daoanh", "docs", "sessions", "2026-10-26", "scoped-tasks")
IDX = os.path.join(OUT, "tmp_index")
REF = os.path.join(REPO, ".git", "refs", "heads", BRANCH)
ENV = dict(os.environ, GIT_INDEX_FILE=IDX)


def git(args, env=None, stdin=None):
    r = subprocess.run(["git"] + args, cwd=REPO, env=env or os.environ,
                       input=stdin, capture_output=True)
    if r.returncode != 0:
        raise SystemExit("git %s failed: %s" % (args, r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8")


def head_text(path):
    t = git(["cat-file", "blob", "HEAD:" + path])
    assert "\r" not in t, "HEAD blob co CR: " + path
    return t


def wt_text(path):
    with open(os.path.join(REPO, path), encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def one(text, old, new):
    n = text.count(old)
    assert n == 1, "anchor count=%d: %r" % (n, old[:80])
    return text.replace(old, new)


def wline(text, prefix):
    lines = [ln for ln in text.split("\n") if ln.startswith(prefix)]
    assert len(lines) == 1, "wline %r count=%d" % (prefix, len(lines))
    return lines[0]


def extract_handle_search(text):
    s = text.index("function handleSearch(e) {")
    e = text.index("\n}\n", s) + 3
    return text[s:e]


# ---------- builders (nhan: HEAD -> noi dung commit) ----------

def b465_app(h, w):
    # Khong sua docstring: doan docstring trong worktree tron noi dung T466, khong tach sach duoc.
    h = one(h,
            '        base_from = """\n            FROM places_dila pd\n'
            '            LEFT JOIN namevi_map_places m ON m.dila_id = pd.id\n        """',
            '        base_from = """\n            FROM places_dila pd\n'
            '            LEFT JOIN namevi_map_places m ON m.dila_id = pd.id\n'
            '            LEFT JOIN codex_place_name c ON c.dila_id = pd.id\n        """')
    h = one(h,
            '                   m.needs_review AS needs_review\n            {base_from}',
            '                   m.needs_review AS needs_review,\n'
            '                   c.name_vi AS claude_name_vi\n            {base_from}')
    h = one(h,
            "                'claude_name_vi': None,   # Giai đoạn 2 — chưa có bảng ai_place_name\n",
            "                'claude_name_vi': r['claude_name_vi'],  # T465 — JOIN codex_place_name.dila_id (T443 applied 2026-10-23)\n")
    return h


def b465_nvm(h, w):
    h = one(h,
            '            Cột Claude/Gemini đang trống (giai đoạn 2, chưa triển khai).\n',
            '            Cột Claude lấy từ bảng <code>codex_place_name</code>, JOIN qua <code>dila_id</code> (T465 —\n'
            '            thay cho <code>codex_district_name</code> dùng sai namespace ID ở T440).\n'
            '            Cột Gemini đang trống (giai đoạn 2, chưa triển khai).\n')
    h = one(h,
            '<th title="Giai đoạn 2 — chưa triển khai">Claude</th>',
            '<th title="Nguồn: codex_place_name.name_vi (JOIN qua dila_id, T465)">Claude</th>')
    h = one(h,
            "                        ${_placeSourceBadge(item.source_badge)}\n                    </td>\n"
            "                    <td style=\"color:var(--text-faint);font-size:12px\">—</td>\n",
            "                        ${_placeSourceBadge(item.source_badge)}\n                    </td>\n"
            "                    <td style=\"font-size:12px;color:${item.claude_name_vi ? 'var(--success)' : 'var(--text-faint)'}\">${_esc(item.claude_name_vi || '—')}</td>\n")
    return h


def b467_index(h, w):
    hs_w = extract_handle_search(w)
    hs_w2 = re.sub(r'^  closeSuggest\(\); // T469: Enter[^\n]*\n', '', hs_w, flags=re.M)
    assert hs_w2 != hs_w, "khong bo duoc dong closeSuggest T469 trong handleSearch"
    hs_h = extract_handle_search(h)
    h = one(h, hs_h, hs_w2)
    block = w[w.index("/* T467: renderer khớp"):w.index("/* ── T453: hiển thị kinh lục DILA")]
    assert "T469" not in block
    h = one(h, "/* ── T453: hiển thị kinh lục DILA", block + "/* ── T453: hiển thị kinh lục DILA")
    return h


def b469_index(h, w):
    css = w[w.index("/* T469: dropdown"):w.index("/* ── Search result panel")]
    h = one(h, "/* ── Search result panel", css + "/* ── Search result panel")
    hero_w = w[w.index('    <div class="search-form">'):w.index('    <div class="search-tags">')]
    hero_h = h[h.index('    <form class="search-wrap" onsubmit="handleSearch(event)">'):h.index('    <div class="search-tags">')]
    h = one(h, hero_h, hero_w)
    h = one(h, "function handleSearch(e) {\n  e.preventDefault();\n",
            "function handleSearch(e) {\n  e.preventDefault();\n"
            + wline(w, "  closeSuggest(); // T469: Enter") + "\n")
    js = w[w.index("/* ── T469: autocomplete"):w.index("/* T467: renderer khớp")]
    h = one(h, "/* T467: renderer khớp đúng shape", js + "/* T467: renderer khớp đúng shape")
    h = one(h, "function setSearch(val) {\n",
            "function setSearch(val) {\n" + wline(w, "  closeSuggest(); // T469: tag") + "\n")
    return h


def b469_app(h, w):
    block = w[w.index("# ── T469: lazy in-memory"):w.index("@app.route('/daoanh/api/public/dila_works')")]
    return one(h, "@app.route('/daoanh/api/public/dila_works')",
               block + "@app.route('/daoanh/api/public/dila_works')")


TASKS = {
    "T465": ("fix", "T465 Tab Place cot Claude doc codex_place_name JOIN dila_id",
             [(APP, b465_app), (NVM, b465_nvm)]),
    "T467": ("fix", "T467 autocomplete trang chu doc dung field monks/works (BUG-052)",
             [(IDXH, b467_index)]),
    "T469": ("feat", "T469 autocomplete trang chu nhom Nhan vat / Kinh sach + endpoint /daoanh/api/search/suggest",
             [(APP, b469_app), (IDXH, b469_index)]),
}


def main():
    tid = sys.argv[1]
    dry = "--dry" in sys.argv
    kind, desc, files = TASKS[tid]
    expected = sorted(p for p, _ in files)
    for attempt in range(3):
        parent = git(["rev-parse", "HEAD"]).strip()
        if os.path.exists(IDX):
            os.remove(IDX)
        git(["read-tree", "HEAD"], env=ENV)
        for path, builder in files:
            new = builder(head_text(path), wt_text(path))
            sha = git(["hash-object", "-w", "--no-filters", "--stdin"],
                      stdin=new.encode("utf-8")).strip()
            git(["update-index", "--add", "--cacheinfo", "100644,%s,%s" % (sha, path)], env=ENV)
        status = git(["diff", "--cached", "--name-status"], env=ENV)
        names = sorted(ln.split("\t", 1)[1] for ln in status.strip().splitlines() if ln.strip())
        assert names == expected, "file set sai: %r vs %r" % (names, expected)
        # moi dong '+' phai ton tai nguyen van trong worktree (khong bia noi dung)
        for path, _ in files:
            # so khop sau khi bo dau phay cuoi (cot SQL cuoi cung khong co dau phay)
            wt_lines = set(ln.rstrip("\r").rstrip(",") for ln in wt_text(path).split("\n"))
            diff = git(["diff", "--cached", "-U0", "--", path], env=ENV)
            added = [ln[1:] for ln in diff.split("\n") if ln.startswith("+") and not ln.startswith("+++")]
            # ngoai le co chu y: cau ghi chu HTML viet cho trang thai T465 (Gemini van trong khi chua co T466)
            allowed_new = {"            Cột Gemini đang trống (giai đoạn 2, chưa triển khai)."}
            missing = [ln for ln in added if ln.rstrip(",") not in wt_lines and ln not in allowed_new]
            print("[%s] %s: +%d dong, khong co trong worktree = %d" % (tid, path, len(added), len(missing)))
            for m in missing[:5]:
                print("   MISSING:", m[:120])
            assert not missing, "co dong '+' khong nam trong worktree"
        stat = git(["diff", "--cached", "--numstat"], env=ENV)
        print("[%s] numstat:\n%s" % (tid, stat.strip()))
        if dry:
            print("[%s] DRY RUN: khong commit. parent=%s" % (tid, parent))
            return
        tree = git(["write-tree"], env=ENV).strip()
        msg = "%s: %s" % (kind, desc)
        new_commit = git(["commit-tree", tree, "-p", parent, "-m", msg]).strip()
        cur = open(REF, encoding="utf-8").read().strip()
        if cur != parent:
            print("[%s] CAS fail: ref=%s != parent=%s (attempt %d) -> rebuild" % (tid, cur, parent, attempt + 1))
            continue
        with open(REF, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_commit + "\n")
        now = git(["rev-parse", "HEAD"]).strip()
        assert now == new_commit, "HEAD=%s != new=%s" % (now, new_commit)
        print("[%s] COMMITTED parent=%s new=%s" % (tid, parent, new_commit))
        print("[%s] msg: %s" % (tid, msg))
        return
    raise SystemExit("[%s] that bai sau 3 lan CAS" % tid)


if __name__ == "__main__":
    main()
