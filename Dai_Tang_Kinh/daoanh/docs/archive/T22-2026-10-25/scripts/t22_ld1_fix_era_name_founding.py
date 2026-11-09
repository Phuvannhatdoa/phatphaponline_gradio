"""
T22-LD1 — Sửa 1.385 event `dila_era_name` có năm thành lập KHÔNG ĐƯỢC NGUỒN hỗ trợ.

VÌ SAO CẦN
==========
Layer D của T22 (`dila_era_name`, 1.471 row) suy ra năm từ **tên triều đại** trong
`places_dila.note`. Với 1.385 row (94,2%) **không lấy được năm** từ note, và trong đó
`label_zh` lại ghi dạng `… (NNNN年建)` ⇒ **mệnh lệnh "năm NNNN là năm xây" là bịa đặt**.

Bằng chứng (đo 2026-10-04, read-only):
  PL000000000352 year=727 | note:「隋時改名宏業寺，唐開元中改天王寺，金大定中改…」
      note CHỈ nói ĐỔI TÊN — không có tuyên bố xây. 727 = trung điểm (713-741).
  1.272 / 1.471 note KHÔNG có marker thành lập nào ⇒ sự kiện 'founding' vô căn cứ.

PHÂN TẦNG (tự suy ra lại từ `note` + `label_zh`, KHÔNG hardcode ID)
==================================================================
  A (58)  — note có năm Ả Rập cạnh marker            → GIỮ NGUYÊN
  B (28)  — note có triều đại + số Hán cạnh marker   → GIỮ NGUYÊN (chờ bảng era)
  C (1.385) — không lấy được năm → chia 2 kiểu sửa:
     mode='range' (684) — nhãn có KHOẢNG thật `(713-741年間)`;
                         `year` hiện tại **luôn nằm trong khoảng** (684/684, 0 ngoài)
                         ⇒ đổi `event_type='era_mention'`, `year=lo`, `year_end=hi`
                            (dùng cột `year_end` vốn 0%), `confidence='era_range'`
     mode='start' (701) — nhãn chỉ có `(N年建)`, N là **năm đầu đời**
                         ⇒ `year=NULL`, gỡ `(N年建)` khỏi nhãn,
                            `confidence='era_start_unverified'`

AN TOÀN
=======
* Chỉ chạm `source='dila_era_name'`.
* Mỗi `UPDATE` có guard `AND source=? AND event_type='founding'` ⇒ không lan sang nhóm khác.
* Đếm `rowcount` phải khớp số dự kiến, lệch ⇒ rollback từ backup.
* `--apply` backup DB trước + ghi log JSON (đủ giá trị cũ để `--revert`).
* `--revert` trả nguyên trạng từ log; lệch ⇒ khôi phục DB từ backup.

Usage
-----
  python -X utf8 scripts/t22_ld1_fix_era_name_founding.py --stats
  python -X utf8 scripts/t22_ld1_fix_era_name_founding.py --dry-run
  python -X utf8 scripts/t22_ld1_fix_era_name_founding.py --apply
  python -X utf8 scripts/t22_ld1_fix_era_name_founding.py --revert
"""

import argparse
import collections
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "..", "data", "lineage.db")
BACKUP_DIR = os.path.join(HERE, "..", "data", "backups")
LOG_PATH = os.path.join(HERE, "..", "data", "t22_ld1_fix_log.json")
REVIEW_PATH = os.path.join(HERE, "..", "data", "t22_phase2_review.json")

SOURCE = "dila_era_name"
SOURCE2 = "dila_founding_phase2"

# --- Phase B: dấu hiệu năm nằm trong context TÁI TẠO / "không rõ năm xây" ---
RENOVATION = re.compile(
    "重建|重修|重興|重創|重立|修葺|重修|募捐|改建|修葺|再造|再興"
)
FOUNDING_UNKNOWN = re.compile("始建年代不可考|始建年代不詳|年代不可考|不詳")
# --- năm trong ngoặc tròn bản rộng (dạng DILA hay dùng) ---
PAREN_YEAR = re.compile("[（(]\\s*(\\d{3,4})\\s*[)）]")

MARKER = re.compile("[始創建]建|建國|创建|建於|建于")
YEAR_ARABIC = re.compile(r"\d{3,4}\s*年|[（(]\s*\d{3,4}\s*[)）]|[公西]元(?:前)?\s*\d{3,4}")
ERA_CN_NUM = re.compile("[一-鿿]{2,6}?[十百千万零一二两三四五六七八九]{1,4}\\s*年")
FAKE_YEAR_LABEL = re.compile(r"\s*[（(]\s*\d{1,4}\s*年建\s*[)）]")
RANGE_LABEL = re.compile(r"[（(]\s*(-?\d{1,4})\s*[-–—－~至]\s*(-?\d{1,4})\s*年間\s*[)）]")
START_ONLY_LABEL = re.compile(r"[（(]\s*(\d{1,4})\s*年建\s*[)）]")

WINDOW = 40


def classify(note):
    """A = có năm Ả Rập; B = era+số Hán; C = không lấy được năm."""
    if not note:
        return "C", "", None
    m = MARKER.search(note)
    if not m:
        return "C", "", None
    win = note[m.start(): m.start() + WINDOW]
    ma = YEAR_ARABIC.search(win)
    if ma:
        return "A", win, ma.group(0)
    if ERA_CN_NUM.search(win):
        return "B", win, None
    return "C", win, None


def fetch_rows(conn):
    cur = conn.cursor()
    cur.execute(
        "SELECT pte.id, pte.dila_id, pte.year, pte.year_end, pte.label_zh, "
        "       pte.confidence, pd.note "
        "FROM place_timeline_events pte "
        "LEFT JOIN places_dila pd ON pd.id = pte.dila_id "
        "WHERE pte.source = ?",
        (SOURCE,),
    )
    out = []
    for rid, dila_id, year, year_end, label_zh, conf, note in cur.fetchall():
        case, win, _ = classify(note or "")
        lab = label_zh or ""
        rg = RANGE_LABEL.search(lab)
        st = START_ONLY_LABEL.search(lab)
        if case == "C" and rg:
            mode = "range"
        elif case == "C" and st:
            mode = "start"
        else:
            mode = None
        out.append({
            "id": rid, "dila_id": dila_id, "year": year, "year_end": year_end,
            "label_zh": label_zh, "confidence": conf, "case": case, "mode": mode,
            "range_lo": int(rg.group(1)) if rg else None,
            "range_hi": int(rg.group(2)) if rg else None,
            "window": " ".join(win.split())[:60],
        })
    return out


def plan_targets(rows):
    return [r for r in rows if r["mode"] in ("range", "start")]


def cmd_stats(conn):
    rows = fetch_rows(conn)
    tot = len(rows)
    c = collections.Counter(r["case"] for r in rows)
    md = collections.Counter(r["mode"] for r in rows)
    print("=== T22-LD1 stats: source='%s' — %d row ===" % (SOURCE, tot))
    for k in ("A", "B", "C"):
        print("   %s  %5d  (%5.1f%%)" % (k, c[k], 100.0 * c[k] / tot if tot else 0))
    print()
    print("   mode='range' (nhãn có KHOẢNG năm thật) : %4d  -> year=lo, year_end=hi"
          % md["range"])
    print("   mode='start' (nhãn chỉ có năm đầu đời) : %4d  -> year NULL + gỡ '(N年建)'"
          % md["start"])
    print("   giữ nguyên (A+B)                         : %4d" % (c["A"] + c["B"]))
    print("   TỔNG sẽ sửa                              : %4d" % (md["range"] + md["start"]))
    inside = sum(1 for r in rows if r["mode"] == "range"
                 and r["range_lo"] <= r["year"] <= r["range_hi"])
    print()
    print("   kiểm tra: year hiện tại nằm trong khoảng ở mode='range': %d/%d"
          % (inside, md["range"]))
    print()
    print("   8 mẫu mode='range':")
    for r in [x for x in rows if x["mode"] == "range"][:8]:
        print("     %-14s year=%-6s -> %s..%s  %s"
              % (r["dila_id"], r["year"], r["range_lo"], r["range_hi"],
                 (r["label_zh"] or "")[:38]))
    print()
    print("   8 mẫu mode='start':")
    for r in [x for x in rows if x["mode"] == "start"][:8]:
        print("     %-14s year=%-6s -> NULL  %s"
              % (r["dila_id"], r["year"], (r["label_zh"] or "")[:42]))


def cmd_dry_run(conn):
    rows = fetch_rows(conn)
    tg = plan_targets(rows)
    print("=== DRY-RUN: %d row ===" % len(tg))
    print()
    print("-- mode='range' (8 mẫu) --")
    for r in [x for x in tg if x["mode"] == "range"][:8]:
        print("   %-14s %-30s -> year=%s year_end=%s  conf='era_range'"
              % (r["dila_id"], (r["label_zh"] or "")[:30], r["range_lo"], r["range_hi"]))
    print()
    print("-- mode='start' (8 mẫu) --")
    for r in [x for x in tg if x["mode"] == "start"][:8]:
        nl = FAKE_YEAR_LABEL.sub("", r["label_zh"] or "").rstrip()
        print("   %-14s %-30s -> year=NULL  label=%r  conf='era_start_unverified'"
              % (r["dila_id"], (r["label_zh"] or "")[:30], nl[:30]))
    print()
    print("KHÔNG ghi DB. Dùng --apply để chạy thật (có backup).")


def fetch_rows_phase2(conn):
    """55 row `dila_founding_phase2`: label_vi rỗng + source_ref tự tham chiếu."""
    cur = conn.cursor()
    cur.execute(
        "SELECT e.id, e.dila_id, e.year, e.label_zh, e.source_ref, e.confidence, "
        "       p.note, m.name_vi, m.name_zh, m.needs_review "
        "FROM place_timeline_events e "
        "LEFT JOIN places_dila p ON p.id = e.dila_id "
        "LEFT JOIN namevi_map_places m ON m.dila_id = e.dila_id "
        "WHERE e.source = ?",
        (SOURCE2,),
    )
    out = []
    for rid, dila_id, year, label_zh, sref, conf, note, vi, vizh, rev in cur.fetchall():
        note = note or ""
        flag = None
        ctx = ""
        if FOUNDING_UNKNOWN.search(note):
            flag = "founding_unknown"
        else:
            m = PAREN_YEAR.search(note)
            if m:
                i = m.start()
                win = note[max(0, i - 34): i + 18]
                if RENOVATION.search(win):
                    flag = "renovation_context"
                    ctx = " ".join(win.split())[:70]
        out.append({
            "id": rid, "dila_id": dila_id, "year": year, "label_zh": label_zh,
            "source_ref": sref, "confidence": conf,
            "label_vi": vi, "mp_name_zh": vizh, "needs_review": rev,
            "flag": flag, "flag_ctx": ctx,
            "year_in_paren": bool(PAREN_YEAR.search(note)),
        })
    return out


def cmd_stats2(conn):
    rows = fetch_rows_phase2(conn)
    print()
    print("=== PHASE B: source='%s' — %d row ===" % (SOURCE2, len(rows)))
    print("   label_vi rong            : %d" % sum(1 for r in rows if not r["label_vi"]))
    print("   co ten Viet (namevi_map) : %d" % sum(1 for r in rows if r["label_vi"]))
    print("   needs_review=1           : %d" % sum(1 for r in rows if r["needs_review"]))
    print("   năm nằm trong ngoặc      : %d" % sum(1 for r in rows if r["year_in_paren"]))
    print()
    fl = collections.Counter(r["flag"] for r in rows if r["flag"])
    print("   CẦN REVIEW (KHÔNG tự sửa year):")
    for k, v in fl.items():
        print("      %-22s %d" % (k, v))
    print()
    print("   6 mẫu cần review:")
    for r in [x for x in rows if x["flag"]][:6]:
        print("      %-14s y=%-5s %-18s %s" % (r["dila_id"], r["year"], r["flag"],
                                               r["flag_ctx"][:52]))


def cmd_apply2(conn):
    """Ghi: label_vi + source_ref. KHÔNG đụng year/event_type."""
    rows = fetch_rows_phase2(conn)
    tg = [r for r in rows if r["label_vi"]]
    print()
    print("=== PHASE B APPLY: %d row (label_vi + source_ref) ===" % len(tg))
    cur = conn.cursor()
    ch = 0
    for r in tg:
        new_ref = "note_paren_year" if r["year_in_paren"] else "note_year"
        cur.execute(
            "UPDATE place_timeline_events SET label_vi=?, source_ref=? "
            "WHERE id=? AND source=? AND (label_vi IS NULL OR label_vi='')",
            (r["label_vi"], new_ref, r["id"], SOURCE2),
        )
        ch += cur.rowcount
    conn.commit()
    print("Đã sửa: %d / %d" % (ch, len(tg)))
    # xuất danh sách review (KHÔNG tự đổi year)
    rv = [r for r in rows if r["flag"]]
    with open(REVIEW_PATH, "w", encoding="utf-8") as f:
        json.dump([{"dila_id": r["dila_id"], "year": r["year"],
                    "label_zh": r["label_zh"], "flag": r["flag"],
                    "context": r["flag_ctx"]} for r in rv],
                  f, ensure_ascii=False, indent=1)
    print("Danh sách review (chưa đổi year): %d row -> %s" % (len(rv), REVIEW_PATH))
    return ch


def cmd_revert2(conn):
    with open(LOG_PATH, encoding="utf-8") as f:
        log = json.load(f)
    ph = log.get("phase2") or {}
    ids = ph.get("ids") or []
    print("=== REVERT phase B: %d row ===" % len(ids))
    cur = conn.cursor()
    done = 0
    for rid in ids:
        cur.execute(
            "UPDATE place_timeline_events SET label_vi=?, source_ref=? "
            "WHERE id=? AND source=?",
            (ph.get("label_vi_old", ""), ph.get("source_ref_old", SOURCE2),
             rid, SOURCE2),
        )
        done += cur.rowcount
    conn.commit()
    print("Đã khôi phục: %d / %d" % (done, len(ids)))


def cmd_apply(conn, db_path):
    rows = fetch_rows(conn)
    tg = plan_targets(rows)
    if not tg:
        print("Không có row nào cần sửa.")
        return
    print("=== APPLY: %d row (%d range + %d start) ==="
          % (len(tg), sum(1 for r in tg if r["mode"] == "range"),
             sum(1 for r in tg if r["mode"] == "start")))
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(BACKUP_DIR, "lineage_t22ld1_%s.db" % stamp)
    shutil.copy2(db_path, backup)
    print("Backup: %s" % backup)

    cur = conn.cursor()
    changed = 0
    for r in tg:
        if r["mode"] == "range":
            cur.execute(
                "UPDATE place_timeline_events SET event_type='era_mention', "
                "  year=?, year_end=?, confidence='era_range' "
                "WHERE id=? AND source=? AND event_type='founding'",
                (r["range_lo"], r["range_hi"], r["id"], SOURCE),
            )
        else:
            nl = FAKE_YEAR_LABEL.sub("", r["label_zh"] or "").rstrip()
            cur.execute(
                "UPDATE place_timeline_events SET event_type='era_mention', "
                "  year=NULL, year_end=NULL, label_zh=?, "
                "  confidence='era_start_unverified' "
                "WHERE id=? AND source=? AND event_type='founding'",
                (nl, r["id"], SOURCE),
            )
        changed += cur.rowcount
    conn.commit()
    print("Đã sửa: %d / %d" % (changed, len(tg)))
    if changed != len(tg):
        print("⚠ rowcount lệch — rollback")
        conn.close()
        shutil.copy2(backup, db_path)
        print("Đã khôi phục DB từ backup.")
        return
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "run_at": datetime.now().isoformat(), "backup": backup, "changed": changed,
            "rows": [{"id": r["id"], "dila_id": r["dila_id"], "year": r["year"],
                      "year_end": r["year_end"], "label_zh": r["label_zh"],
                      "confidence": r["confidence"], "mode": r["mode"]} for r in tg],
            "phase2": [],
        }, f, ensure_ascii=False, indent=1)
    print("Log: %s" % LOG_PATH)
    conn.close()
    # ---- Phase B: label_vi + source_ref cho 55 row, KHÔNG đụng year ----
    conn2 = sqlite3.connect(db_path)
    changed2 = cmd_apply2(conn2)
    ids2 = [r["id"] for r in fetch_rows_phase2(conn2) if r["label_vi"]]
    conn2.close()
    with open(LOG_PATH, encoding="utf-8") as f:
        log = json.load(f)
    log["phase2"] = {"changed": changed2, "ids": ids2,
                     "label_vi_old": "", "source_ref_old": SOURCE2}
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print("Log đã ghi kèm phase2 (%d id)." % len(ids2))

    v = sqlite3.connect(db_path)
    q = v.cursor()
    g = lambda s: q.execute(s, (SOURCE,)).fetchone()[0]
    print()
    print("VERIFY (source='%s'):" % SOURCE)
    print("   era_mention           : %d" % g(
        "SELECT COUNT(*) FROM place_timeline_events WHERE source=? AND event_type='era_mention'"))
    print("   era_range (có year_end): %d" % g(
        "SELECT COUNT(*) FROM place_timeline_events WHERE source=? AND confidence='era_range'"))
    print("   era_start_unverified  : %d" % g(
        "SELECT COUNT(*) FROM place_timeline_events WHERE source=? AND confidence='era_start_unverified'"))
    print("   founding còn lại      : %d" % g(
        "SELECT COUNT(*) FROM place_timeline_events WHERE source=? AND event_type='founding'"))
    print("   founding year IS NULL : %d  (phải = 0)" % g(
        "SELECT COUNT(*) FROM place_timeline_events WHERE source=? AND event_type='founding' AND year IS NULL"))
    print("   nhãn còn '(N年建)'     : %d  (phải = 0)" % g(
        "SELECT COUNT(*) FROM place_timeline_events WHERE source=? AND label_zh LIKE '%年建%'"))
    v.close()


def cmd_revert(conn, db_path):
    if not os.path.exists(LOG_PATH):
        print("Không có log sửa — không có gì để revert.")
        return
    with open(LOG_PATH, encoding="utf-8") as f:
        log = json.load(f)
    print("=== REVERT %d row ===" % log["changed"])
    cur = conn.cursor()
    done = 0
    for r in log["rows"]:
        cur.execute(
            "UPDATE place_timeline_events SET event_type='founding', year=?, "
            "  year_end=?, label_zh=?, confidence=? "
            "WHERE id=? AND source=? AND event_type='era_mention'",
            (r["year"], r["year_end"], r["label_zh"], r["confidence"], r["id"], SOURCE),
        )
        done += cur.rowcount
    conn.commit()
    print("Đã khôi phục: %d / %d" % (done, len(log["rows"])))
    if done != len(log["rows"]):
        print("⚠ lệch — khôi phục từ backup %s" % log["backup"])
        conn.close()
        shutil.copy2(log["backup"], db_path)
        print("Đã khôi phục DB từ backup.")
        return
    conn.close()
    print("Backup vẫn còn: %s" % log["backup"])
    # Phase B
    conn2 = sqlite3.connect(db_path)
    cmd_revert2(conn2)
    conn2.close()


def cmd_fix_labels(conn, db_path):
    """Gỡ `(N年建)` còn sót ở nhóm A/B (case C đã gỡ trong Phase A).

    Nhãn dạng `… ��大中 (847年建)` ghép **năm đầu đời** + mệnh lệnh "năm NNNN là năm
    xây" ⇒ mệnh lệnh sai. Không đụng `year`/`event_type` (nhóm A/B chưa được duyệt đổi).
    """
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, label_zh FROM place_timeline_events "
        "WHERE source=? AND event_type='founding' AND label_zh LIKE ?",
        (SOURCE, "%年建%"),
    ).fetchall()
    tg = [(rid, lab, FAKE_YEAR_LABEL.sub("", lab or "").rstrip())
          for rid, lab in rows if FAKE_YEAR_LABEL.search(lab or "")]
    print("=== FIX LABELS: %d / %d row con '(N年建)' ===" % (len(tg), len(rows)))
    if not tg:
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(BACKUP_DIR, "lineage_t22ld1_label_%s.db" % stamp)
    shutil.copy2(db_path, backup)
    print("Backup: %s" % backup)
    ch = 0
    for rid, old, new in tg:
        if new == old:
            continue
        cur.execute(
            "UPDATE place_timeline_events SET label_zh=? WHERE id=? AND source=? AND event_type='founding'",
            (new, rid, SOURCE),
        )
        ch += cur.rowcount
    conn.commit()
    with open(LOG_PATH, encoding="utf-8") as f:
        log = json.load(f) if os.path.exists(LOG_PATH) else {}
    log["fix_labels"] = {"backup": backup, "changed": ch,
                         "rows": [{"id": r, "label_zh": o} for r, o, _ in tg]}
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print("Đã gỡ: %d" % ch)
    for rid, old, new in tg[:8]:
        print("   %r -> %r" % (old[:34], new[:34]))
    conn.close()
    v = sqlite3.connect(db_path)
    left = v.execute("SELECT COUNT(*) FROM place_timeline_events WHERE source=? AND label_zh LIKE ?",
                     (SOURCE, "%年建%")).fetchone()[0]
    print("VERIFY còn '(N年建)' ở source='%s': %d (phải = 0)" % (SOURCE, left))
    v.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--fix-labels", action="store_true")
    a = ap.parse_args()
    if not any([a.stats, a.dry_run, a.apply, a.revert, a.fix_labels]):
        ap.print_help()
        sys.exit(1)
    db_path = os.path.abspath(DB_PATH)
    conn = sqlite3.connect(db_path)
    if a.stats:
        cmd_stats(conn)
        cmd_stats2(conn)
    elif a.dry_run:
        cmd_dry_run(conn)
    elif a.apply:
        cmd_apply(conn, db_path)
    elif a.revert:
        cmd_revert(conn, db_path)
    elif a.fix_labels:
        cmd_fix_labels(conn, db_path)
    conn.close()


if __name__ == "__main__":
    main()