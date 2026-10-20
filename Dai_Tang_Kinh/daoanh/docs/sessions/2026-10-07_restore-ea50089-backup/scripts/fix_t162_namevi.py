# -*- coding: utf-8 -*-
"""
fix_t162_namevi.py — T162: Reseed name_vi sau T149 (people + name_vi_map).

VẤN ĐỀ
------
T149 đã sửa name_zh sai (28,275 rows bị đổi giữa t78 backup 8/31 và live DB),
nhưng people.name_vi (28,121 rows) và name_vi_map (18,807 rows) VẪN giữ
phiên âm của name_zh CŨ sai. Script này:
  - A (affected)    = people mà name_zh hiện tại != name_zh trong t78 backup.
  - C (candidates)  = A ∩ (name_vi hiện tại == name_vi t78) ∩ KHÔNG protected.
  - P (protected)   = người/có name_vi_map.source='daoanh_dict' hoặc approved_by
                      (bàn tay người — KHÔNG chạm, chỉ báo cáo).
  - Ambiguous       = A ∩ (name_vi hiện tại != name_vi t78) → đã bị đổi một
                      cách không rõ ràng (có thể đúng như A000001, có thể rác
                      như A000006) → KHÔNG tự quyết, report để Admin review.

ENGINE PHIÊN ÂM
----------------
Tái dùng ĐÚNG logic seed (seed_persons_namevi.ensure_vietnamese) mà KHÔNG import
app.py (vì app.py có thể đang bị agent khác sửa dở):
  1. CUSTOM_HANVIET dict literal    → parse an toàn bằng ast từ app.py
  2. CUSTOM_HANVIET["奘"]="Trạng"    → line cố định sau dict literal
  3. custom_hanviet_override (DB)   → phủ override admin (ưu tiên cao nhất)
  4. hanviet_fallback (DB)          → fallback 8650 ký tự
Xử lý chuỗi y hệt ensure_vietnamese: space giữa 2 ký tự CJK liên tiếp,
title-case từng word (không chạm word bắt đầu bằng CJK).

MODE
----
  --stats     in số liệu A / C / P / ambiguous / map-stale, không đổi gì.
  --dry-run   in mẫu 20 stale + A000001 + protected + ambiguous (không đổi gì).
  --apply     sao lưu full (nếu chưa có pre-apply backup) → UPDATE people.name_vi
              + name_vi_map trong 1 transaction → ghi manifest JSON → verify.
  --verify    in lại counts + các case mẫu sau apply, so với manifest.
  --revert    restore lineage.db từ pre-apply backup (data/backups/lineage_t162_<ts>.db).

AN TOÀN / REVERT
----------------
- Apply 100% trong 1 transaction; có pre-apply full backup + manifest:
  data/backups/lineage_t162_<ts>.db  (bản gốc)
  data/backups/t162_manifest.json     (id -> {old_vi,new_vi,old_map,new_map})
- --revert: sao chép backup đè lên lineage.db (cách chuẩn như T149/T157).
"""
import argparse
import ast
import datetime
import json
import os
import re
import sqlite3
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
LIVE_DB = os.path.join(DATA, "lineage.db")
T78_DB = os.path.join(DATA, "lineage_backup_t78.db")
BACKUP_DIR = os.path.join(DATA, "backups")
APP_PY = os.path.join(BASE, "app.py")
LATEST_TAG = os.path.join(BACKUP_DIR, "t162_latest.txt")
MANIFEST = os.path.join(BACKUP_DIR, "t162_manifest.json")

# ---------------------------------------------------------------------------
# Parsing CUSTOM_HANVIET từ app.py (an toàn: không import module, đọc file thô)
# ---------------------------------------------------------------------------
def extract_custom_hanviet(app_py=APP_PY, other_line="CUSTOM_HANVIET[\"奘\"] = \"Trạng\""):
    """Đọc app.py, tách literal dict của CUSTOM_HANVIET bằng ast.parse trên
    đúng dòng khai báo. Trả về dict (kèm line đặc biệt 奘=Trạng)."""
    with open(app_py, "r", encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"\bCUSTOM_HANVIET\s*=\s*\{", src)
    if not m:
        raise RuntimeError("Không tìm thấy CUSTOM_HANVIET = { trong app.py")
    start = m.end() - 1  # vị trí '{'
    # đếm ngoặc để lấy đúng literal dict
    depth = 0
    i = start
    in_str = None
    while i < len(src):
        ch = src[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in "'\"":
            in_str = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    literal = src[start:i + 1]
    custom = ast.literal_eval(literal)
    # line cố định sau literal (奘 = Trạng) — parse an toàn
    mm = re.search(r'CUSTOM_HANVIET\s*\[\s*(["\'])(.+?)\1\s*\]\s*=\s*(["\'])(.+?)\3',
                   src[m.end():])
    if mm:
        custom[mm.group(2)] = mm.group(4)
    return custom


def load_hv_tables(conn):
    """custom_hanviet_override (ưu tiên cao nhất) + hanviet_fallback."""
    override = {}
    fallback = {}
    try:
        for r in conn.execute("SELECT char, hanviet FROM custom_hanviet_override"):
            override[r[0]] = r[1]
    except Exception:
        pass
    try:
        for r in conn.execute("SELECT ch, hv FROM hanviet_fallback"):
            fallback[r[0]] = r[1]
    except Exception:
        pass
    return override, fallback


def build_hanviet_dict(conn):
    """Ghép: fallback (gốc) → CUSTOM_HANVIET (phủ) → override admin (phủ nữa)."""
    override, fallback = load_hv_tables(conn)
    custom = extract_custom_hanviet()
    hv = dict(fallback)
    hv.update(custom)
    hv.update(override)
    return hv


def ensure_vietnamese(name_zh, hv):
    """Bản clone của seed_persons_namevi.ensure_vietnamese (tái dùng engine)."""
    if not name_zh:
        return ""
    out = []
    for c in name_zh:
        if "\u4e00" <= c <= "\u9fff":
            v = hv.get(c)
            out.append(v if v else c)
        else:
            out.append(c)
    spaced = []
    for i, tok in enumerate(out):
        if i > 0 and ("\u4e00" <= name_zh[i - 1] <= "\u9fff") and ("\u4e00" <= name_zh[i] <= "\u9fff"):
            spaced.append(" ")
        spaced.append(tok)
    result = "".join(spaced)
    titled = []
    for w in result.split(" "):
        if w and ("\u4e00" <= w[0] <= "\u9fff"):
            titled.append(w)
        elif w:
            titled.append(w[0].upper() + w[1:] if len(w) > 1 else w.upper())
        else:
            titled.append(w)
    return " ".join(titled)


def _ok_hanviet_name(name_vi, non_hanviet_words):
    """Clone _ok_hanviet_name (app.py:16657) — dùng cho verify NAME LOCK."""
    if not name_vi or len(name_vi.strip()) < 2:
        return False
    words = {w.lower() for w in name_vi.split()}
    return not words.intersection(non_hanviet_words)


def load_non_hanviet_words():
    """Đọc _NON_HANVIET_NAME_WORDS từ app.py (đặt trước hàm verify)."""
    with open(APP_PY, "r", encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"_NON_HANVIET_NAME_WORDS\s*=\s*\{([^}]*)\}", src)
    if not m:
        return set()
    return {t.strip() for t in m.group(1).split(",") if t.strip()}


# ---------------------------------------------------------------------------
# Tính tập dữ liệu
# ---------------------------------------------------------------------------
def build_sets(t78=T78_DB, live=LIVE_DB):
    """Trả về (affected, candidates, protected_ids, ambiguous, map_stale_ids)."""
    conn_t = sqlite3.connect("file:{}?mode=ro".format(t78), uri=True)
    conn_t.row_factory = sqlite3.Row
    conn_l = sqlite3.connect(live)
    conn_l.row_factory = sqlite3.Row

    t78_rows = {r["id"]: (r["name_zh"], r["name_vi"]) for r in conn_t.execute(
        "SELECT id, name_zh, name_vi FROM people").fetchall()}

    live_rows = {r["id"]: (r["name_zh"], r["name_vi"]) for r in conn_l.execute(
        "SELECT id, name_zh, name_vi FROM people").fetchall()}

    protected_ids = set()
    for r in conn_l.execute(
        "SELECT DISTINCT dila_id FROM name_vi_map WHERE dila_id IS NOT NULL "
        "AND (source = 'daoanh_dict' OR approved_by IS NOT NULL OR approved_by != '')"
    ):
        if r[0]:
            protected_ids.add(r[0])

    affected = {}
    ambiguous = {}
    for pid, (lz, lv) in live_rows.items():
        if pid not in t78_rows:
            continue
        tz, tv = t78_rows[pid]
        if lz != tz:                      # name_zh đã bị T149 đổi
            affected[pid] = (lz, lv, tz, tv)
            if lv != tv:                  # name_vi đã bị đổi bởi ai đó
                ambiguous[pid] = (lz, lv, tz, tv)

    candidates = {}
    for pid, (lz, lv, tz, tv) in affected.items():
        if pid in protected_ids:
            continue
        if lv == tv:                      # name_vi vẫn stale với name_zh cũ
            candidates[pid] = (lz, lv, tz, tv)

    # name_vi_map stale: row có dila_id trong affected, source auto/suggest,
    # hoặc name_vi bằng với old people.name_vi, hoặc name_zh == old people.name_zh
    map_stale_ids = []
    for r in conn_l.execute(
        "SELECT id, dila_id, name_zh, name_vi, name_vi_auto, source "
        "FROM name_vi_map WHERE dila_id IS NOT NULL"
    ):
        pid = r["dila_id"]
        if pid not in affected:
            continue
        old_zh, old_vi = t78_rows.get(pid, ("", ""))
        if pid in protected_ids:
            continue
        if r["source"] in ("daoanh_dict",):
            continue
        if r["name_zh"] == old_zh or (r["name_vi"] == old_vi) or (r["name_vi_auto"] == old_vi):
            map_stale_ids.append((pid, r["id"], old_vi, r["name_vi"], r["source"]))

    conn_t.close()
    conn_l.close()
    return affected, candidates, protected_ids, ambiguous, map_stale_ids


# ---------------------------------------------------------------------------
# Các mode
# ---------------------------------------------------------------------------
def cmd_stats(candidates, protected_ids, ambiguous, map_stale_ids, affected):
    print("=" * 66)
    print("T162 STATS")
    print("=" * 66)
    print("A  affected (name_zh đổi giữa t78 vs live) : {:>5}".format(len(affected)))
    print("P  protected (daoanh_dict / approved_by)    : {:>5}".format(len(protected_ids)))
    print("C  candidates (stale name_vi, sẽ sửa)       : {:>5}".format(len(candidates)))
    print("X  ambiguous (name_vi đã đổi, KHÔNG chạm)   : {:>5}".format(len(ambiguous)))
    print("M  name_vi_map stale (auto, sẽ sync)        : {:>5}".format(len(map_stale_ids)))
    print("P∩A  trong affected is                       : {:>5}".format(
        len(protected_ids.intersection(affected))))

    conn = sqlite3.connect(LIVE_DB)
    hv = build_hanviet_dict(conn)
    conn.close()
    # thống kê: bao nhiêu candidate có new_vi != old_vi (thay đổi thực)
    would_change = 0
    cjk_left = 0
    ok_hanviet = 0
    non_hv_words = load_non_hanviet_words()
    for pid, (lz, lv, tz, tv) in candidates.items():
        nv = ensure_vietnamese(lz, hv)
        if nv != lv:
            would_change += 1
        if re.search(r'[\u4e00-\u9fff\u3400-\u4dbf]', nv):
            cjk_left += 1
        if _ok_hanviet_name(nv, non_hv_words):
            ok_hanviet += 1
    print("C_effective (new_vi sẽ khác old_vi)          : {:>5}".format(would_change))
    print("  trong đó new_vi còn ký tự CJK hiếm          : {:>5}".format(cjk_left))
    print("  new_vi đạt NAME LOCK filter _ok_hanviet    : {:>5}/{}".format(
        ok_hanviet, len(candidates)))


def cmd_dry_run(candidates, protected_ids, ambiguous, map_stale_ids, affected):
    conn = sqlite3.connect(LIVE_DB)
    hv = build_hanviet_dict(conn)
    conn.close()
    print("=" * 66)
    print("T162 DRY-RUN (không thay đổi gì)")
    print("=" * 66)
    print("\n--- Case no-op chuẩn: A000001 (KHÔNG trong candidates) ---")
    for pid in ("A000001", "A000002", "A000006"):
        if pid in affected:
            lz, lv, tz, tv = affected[pid]
            print("  {:<8} zh: {:<10} vi(stale): {:<24} -> new_vi: {}".format(
                pid, lz, lv, ensure_vietnamese(lz, hv)))
        else:
            print("  {:<8} không bị ảnh hưởng".format(pid))

    print("\n--- Protected (KHÔNG chạm, báo cáo) {} ---".format(len(protected_ids)))
    conn = sqlite3.connect(LIVE_DB)
    rows = conn.execute(
        "SELECT p.id, p.name_zh, p.name_vi, m.source, m.name_vi, m.approved_by "
        "FROM people p LEFT JOIN name_vi_map m ON m.dila_id = p.id "
        "WHERE p.id IN ({}) LIMIT 8".format(",".join("?" * min(8, len(protected_ids)))),
        list(protected_ids)[:8]).fetchall()
    for r in rows:
        print("  {:<8} zh={:<10} vi={:<24} map_src={:<12} map_vi={:<24} appr={}".format(
            r[0], r[1], r[2], r[3], r[4], r[5]))
    conn.close()

    print("\n--- Ambiguous (không tự quyết, chờ Admin) {} ---".format(len(ambiguous)))
    for i, (pid, (lz, lv, tz, tv)) in enumerate(ambiguous.items()):
        if i >= 8:
            break
        print("  {:<8} zh:{:<10} vi:{:<24} (cũ t78: zh={:<10} vi={})".format(
            pid, lz, lv, tz, tv))

    print("\n--- Mẫu 20 candidates stale ---")
    for i, (pid, (lz, lv, tz, tv)) in enumerate(candidates.items()):
        if i >= 20:
            break
        new_vi = ensure_vietnamese(lz, hv)
        flag = "CHANGE" if new_vi != lv else "same"
        print("  {:<8} zh:{:<12} old_vi:{:<24} new_vi:{:<24} [{}]".format(
            pid, lz, lv, new_vi, flag))


def cmd_apply(candidates, protected_ids, ambiguous, map_stale_ids, affected):
    # 1) backup pre-apply nếu chưa có
    if os.path.exists(LATEST_TAG):
        ts = open(LATEST_TAG, "r").read().strip()
        backup = os.path.join(BACKUP_DIR, "lineage_t162_{}.db".format(ts))
        if not os.path.exists(backup):
            backup = None
    else:
        backup = None
    if not backup:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(BACKUP_DIR, "lineage_t162_{}.db".format(ts))
        print("Backup pre-apply ->", backup)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with sqlite3.connect(LIVE_DB) as a:
            b = sqlite3.connect(backup)
            with b:
                a.backup(b)
            b.close()
        open(LATEST_TAG, "w").write(ts)
    else:
        ts = os.path.basename(backup).replace("lineage_t162_", "").replace(".db", "")
        print("Tái dùng backup pre-apply:", backup)

    conn = sqlite3.connect(LIVE_DB)
    hv = build_hanviet_dict(conn)
    conn.execute("BEGIN")
    manifest = {}
    changed = 0
    unchanged = 0
    try:
        cur = conn.cursor()
        for pid, (lz, lv, tz, tv) in candidates.items():
            new_vi = ensure_vietnamese(lz, hv)
            if new_vi == lv:
                unchanged += 1
                continue
            cur.execute("UPDATE people SET name_vi = ? WHERE id = ?",
                        (new_vi, pid))
            changed += 1
            manifest[pid] = {"old_vi": lv, "new_vi": new_vi}
        # name_vi_map sync (chỉ row stale auto/suggest)
        map_changed = 0
        map_deleted = 0
        for pid, mid, old_vi, cur_map_vi, src in map_stale_ids:
            new_vi = ensure_vietnamese(affected[pid][0], hv)
            new_zh = affected[pid][0]
            if pid in manifest:
                new_vi = manifest[pid]["new_vi"]
            # conflict-safe: nếu cặp (new_vi, new_zh) đã tồn tại ở row KHÁC
            # thì row stale này thành duplicate → DELETE (giữ lookup không trùng).
            other = conn.execute(
                "SELECT id FROM name_vi_map "
                "WHERE name_vi = ? AND name_zh = ? AND id != ? LIMIT 1",
                (new_vi, new_zh, mid)).fetchone()
            if other:
                cur.execute("DELETE FROM name_vi_map WHERE id = ?", (mid,))
                map_deleted += 1
                if pid in manifest:
                    manifest[pid]["old_map_vi"] = cur_map_vi
                    manifest[pid]["new_map_vi"] = "DUPLICATE_DELETED"
                continue
            if cur_map_vi == new_vi and new_zh:
                # chỉ cập nhật name_zh (không cần đổi vi)
                cur.execute("UPDATE name_vi_map SET name_zh = ? WHERE id = ?",
                            (new_zh, mid))
            else:
                cur.execute(
                    "UPDATE name_vi_map SET name_zh = ?, name_vi = ?, name_vi_auto = ? WHERE id = ?",
                    (new_zh, new_vi, new_vi, mid))
            map_changed += 1
            if pid in manifest:
                manifest[pid]["old_map_vi"] = cur_map_vi
                manifest[pid]["new_map_vi"] = new_vi
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        print("ERROR, rollback:", e)
        sys.exit(1)
    conn.close()

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump({"backup": os.path.basename(backup),
                   "ts": ts,
                   "people_changed": changed,
                   "map_changed": map_changed,
                   "map_deleted": map_deleted,
                   "entries": manifest}, f, ensure_ascii=False, indent=1)
    print("=" * 66)
    print("APPLY DONE")
    print("  people.name_vi  changed   :", changed)
    print("  people.name_vi  unchanged :", unchanged)
    print("  name_vi_map     updated   :", map_changed)
    print("  name_vi_map     deleted   :", map_deleted)
    print("  backup                     :", backup)
    print("  manifest                   :", MANIFEST)
    print("REVERT: python scripts/fix_t162_namevi.py --revert")


def cmd_verify(candidates, protected_ids, ambiguous, map_stale_ids, affected):
    conn = sqlite3.connect(LIVE_DB)
    hv = build_hanviet_dict(conn)
    non_hv = load_non_hanviet_words()
    manifest = {}
    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST, encoding="utf-8")).get("entries", {})

    print("=" * 66)
    print("T162 VERIFY")
    print("=" * 66)
    nv = load_non_hanviet_words()
    # tái tính sets
    aff2, cand2, prot2, amb2, map2 = build_sets()
    # ambiguous thật (đổi BỞI NGƯỜI KHÁC trước T162) = ambiguous hiện tại
    # TRỪ rows mà T162 đã sửa (nằm trong manifest).
    pre_changed = {pid for pid in amb2 if pid not in manifest}
    print("A={} C={} P={} X(pre-T162, khác manifest)={} M={}".format(
        len(aff2), len(cand2), len(prot2), len(pre_changed), len(map2)))

    # (1) mọi candidate phải có new_vi == people.name_vi hiện tại
    mismatch = 0
    for pid, (lz, lv, tz, tv) in cand2.items():
        expect = ensure_vietnamese(lz, hv)
        if expect != lv:
            mismatch += 1
            print("  !MISMATCH {:<8} expect={:<24} got={}".format(pid, expect, lv))
    print("candidates còn pending (mismatch):", mismatch)

    # (2) ca canonical
    rows = conn.execute(
        "SELECT id, name_zh, name_vi FROM people WHERE id IN ('A000001','A000002')"
    ).fetchall()
    for r in rows:
        print("  {} zh={} vi={} (ok_hanviet: {})".format(
            r[0], r[1], r[2], _ok_hanviet_name(r[2], nv)))

    # (3) NAME LOCK filter: trong các row đã đổi, bao nhiêu đạt _ok_hanviet
    total = 0
    bad = 0
    for pid, entry in manifest.items():
        new_vi = entry.get("new_vi", "")
        total += 1
        if not _ok_hanviet_name(new_vi, nv):
            bad += 1
            if bad <= 10:
                print("  !filter-fail {:<8} new_vi={}".format(pid, new_vi))
    print("verify filter _ok_hanviet: {}/{} đạt".format(total - bad, total))

    # (4) không còn row nào name_zh CJK lẫn trong name_vi (safety)
    leftover_cjk = conn.execute(
        "SELECT COUNT(*) FROM people WHERE name_vi GLOB '*[一-鿿]*'"
    ).fetchone()[0]
    print("people.name_vi vẫn chứa CJK (dự kiến = row chưa có HV):", leftover_cjk)
    conn.close()
    print("VERIFY DONE")


def cmd_revert():
    if not os.path.exists(LATEST_TAG):
        print("Không tìm thấy t162_latest.txt — không có pre-apply backup.")
        sys.exit(2)
    ts = open(LATEST_TAG, "r").read().strip()
    backup = os.path.join(BACKUP_DIR, "lineage_t162_{}.db".format(ts))
    if not os.path.exists(backup):
        print("Thiếu backup:", backup)
        sys.exit(2)
    print("Revert lineage.db <-", backup)
    with sqlite3.connect(backup) as a:
        b = sqlite3.connect(LIVE_DB)
        with b:
            a.backup(b)
        b.close()
    print("REVERT DONE — dữ liệu đã về trạng thái trước apply T162.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--t78", default=T78_DB, help="path to pre-T149 backup db")
    ap.add_argument("--live", default=LIVE_DB, help="path to live db")
    args = ap.parse_args()

    affected, candidates, protected_ids, ambiguous, map_stale_ids = build_sets(
        t78=args.t78, live=args.live)

    if args.stats:
        cmd_stats(candidates, protected_ids, ambiguous, map_stale_ids, affected)
    elif args.dry_run:
        cmd_dry_run(candidates, protected_ids, ambiguous, map_stale_ids, affected)
    elif args.apply:
        cmd_apply(candidates, protected_ids, ambiguous, map_stale_ids, affected)
    elif args.verify:
        cmd_verify(candidates, protected_ids, ambiguous, map_stale_ids, affected)
    elif args.revert:
        cmd_revert()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()