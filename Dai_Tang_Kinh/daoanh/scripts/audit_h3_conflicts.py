# -*- coding: utf-8 -*-
"""
T263 (P1) — Audit H3 CONFLICTS: đếm & phân loại các dòng H3 "pass nới" có
`r != year` (năm suy ra từ note KHÁC năm đã lưu). READ-ONLY — không sửa DB.

VÌ SAO CẦN
==========
H3 đang PASS (0 FAIL) sau T251+T252, nhưng một phần dòng pass theo nhánh
W1a-legacy: `era_year_in_text(note)` tìm được biểu thức `<era><số Hán>年`
nằm trong khoảng của NIÊN HIỆU nào đó và trả về CE year `r` — KHÔNG bắt buộc
`r == year`. Nếu `r != year` thì bằng chứng không chứng minh được đúng năm lưu.
Đây là "gap im lặng": gate xanh nhưng 285 dòng chưa được chứng minh đủ.

Script này — giống mọi gate T234 — là QUERY chạy lại được. Nó liệt kê chính
xác các dòng đó, gắn 1 nhóm gợi ý (A/B/C) để con người rà, xuất TSV + report.
KHÔNG tự sửa dữ liệu. Exit 0 (WARN); `--strict` dành cho Phase 3 (chưa dùng).

PHÂN LOẠI GỢI Ý (máy phân loại để người rà, KHÔNG phải phán quyết)
=================================================================
  B — year nằm TRONG khoảng [y0,y1] của chính era mà text nêu (era trải nhiều
      năm, note chứng minh được thập niên/triều đại chứ không phải đúng năm).
      => KHÔNG phải bug buộc sửa; Part 2 sẽ gắn năm_support='era-range'.
  C — year nằm trong khoảng của MỘT ERA KHÁC (khác tên với era text nêu).
      => note nhắc sự kiện/niên hiệu khác (conflation nhiều sự kiện 1 note).
      => cần rà, tách evidence hoặc đánh dấu REVIEW (UI T259/T260 pattern).
  A — year KHÔNG nằm trong MỌI khoảng niên hiệu đã biết.
      => năm lưu rõ ràng mâu thuẫn bằng chứng; ứng viên sửa year (khuôn W4)
         HOẶC phải có nguồn riêng.

Usage
-----
  python -X utf8 scripts/audit_h3_conflicts.py
  python -X utf8 scripts/audit_h3_conflicts.py --out docs/evidence   (mặc định)
  python -X utf8 scripts/audit_h3_conflicts.py --strict   # Phase 3: FAIL nếu còn
Exit: 0 = report xong (WARN) · 1 = (--strict) còn conflict
"""

import argparse
import io
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_data_honesty import (  # noqa: E402
    DB_PATH, NUMCH, cn2int, load_era_map, era_year_in_text,
)
from audit_data_honesty import RANGE_RE  # noqa: E402  (khoang nam trong label)

HERE = os.path.dirname(os.path.abspath(__file__))
DATE = "2026-10-08"


def first_era_match(text, era_map):
    """Replicate vong scan cua era_year_in_text de bat lai (era_named, n, ce, span).

    Tra ve (zh, n, ce, (y0,y1)) voi ce nam trong khoang dau tien hop le;
    (zh, n, None, None) neu co bieu thuc nhung ngoai MỌI khoang;
    None neu khong co bieu thuc nao.
    """
    for zh, spans in era_map.items():
        i = text.find(zh)
        while i >= 0:
            m = re.match("((?:元|[" + NUMCH + "]{1,4}))\\s*年",
                         text[i + len(zh): i + len(zh) + 7])
            if m:
                tok = m.group(1)
                n = 1 if tok == "元" else cn2int(tok)
                if n:
                    for y0, y1 in spans:
                        ce = y0 + n - 1
                        if y0 <= ce <= (y1 if y1 is not None else ce):
                            return zh, n, ce, (y0, y1)
                    return zh, n, None, None
                return None
            i = text.find(zh, i + 1)
    return None


def class_row(year, found, era_map):
    """Tra ve (group, ghi_chu)."""
    zh, n, ce, span = found
    spans_zh = era_map[zh]
    if any(y0 <= year <= (y1 if y1 is not None else year) for y0, y1 in spans_zh):
        amb = " (ten trung, %d khoang)" % len(spans_zh) if len(spans_zh) > 1 else ""
        return "B", ("year %d nam TRONG khoang cua %s%s" % (year, zh, amb))
    any_ok = False
    for spans in era_map.values():
        if any(y0 <= year <= (y1 if y1 is not None else year) for y0, y1 in spans):
            any_ok = True
            break
    if any_ok:
        return "C", ("year %d thuoc ERA KHAC (khong phai %s) — note nhu nhieu su kien"
                     % (year, zh))
    return "A", ("year %d nam NGOAI moi khoang niem hieu da biet (era nhanh: %s)"
                 % (year, zh))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "docs", "evidence"))
    ap.add_argument("--strict", action="store_true",
                    help="Phase 3: exit 1 khi con conflict (mặc định exit 0 = WARN)")
    a = ap.parse_args()

    conn = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(DB_PATH).replace("\\", "/"),
                           uri=True)
    era_map = load_era_map(conn)

    rows = conn.execute(
        "SELECT p.dila_id, p.year, p.source_ref, p.label_zh, pd.note "
        "FROM place_timeline_events p "
        "LEFT JOIN places_dila pd ON pd.id = p.dila_id "
        "WHERE p.year IS NOT NULL").fetchall()

    conflicts, w1a_total, exact_passes = [], 0, 0
    mismatch_r = 0
    for did, year, sref, label, note in rows:
        note = note or ""
        label = label or ""
        if str(year) in note or str(year) in note.replace("（", "(").replace("）", ")"):
            continue                        # year hien ro trong note — khong xung dot
        r = era_year_in_text(note, era_map, year)
        if r is not None and r >= 0:
            w1a_total += 1
            if r != year:
                found = first_era_match(note, era_map)
                if found is None:           # phong thu: r>=0 nhung khong bat lai duoc era
                    grp, note_desc = "A", "khong xac dinh duoc era (r=%d)" % r
                    zh_out, n_out, span_out = None, None, None
                else:
                    grp, note_desc = class_row(year, found, era_map)
                    zh_out, n_out, span_out = found[0], found[1], found[3]
                conflicts.append((did, year, r, zh_out, n_out, span_out,
                                  grp, note_desc))
            else:
                exact_passes += 1

    # ---- T265: doi chieu voi bang quyet dinh timeline_year_support (chi doc)
    from collections import Counter, defaultdict
    has_support_tbl = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='timeline_year_support'"
    ).fetchone() is not None

    # gop theo cap (dila_id, year) nhu match_events() trong t265_year_support.py,
    # vi mot cap co the ung voi nhieu id (nhieu nguon) nhung CUNG mot quyet dinh.
    pair_group = {}
    for did, year, r, zh, n, span, grp, desc in conflicts:
        pair_group.setdefault((did, year), grp)

    pair_decided_status = {}
    if has_support_tbl:
        for (did, year) in pair_group:
            ids = [i[0] for i in conn.execute(
                "SELECT id FROM place_timeline_events WHERE dila_id = ? AND year = ?",
                (did, year)).fetchall()]
            statuses = set()
            for eid in ids:
                row = conn.execute(
                    "SELECT status FROM timeline_year_support WHERE event_id = ?",
                    (eid,)).fetchone()
                if row:
                    statuses.add(row[0])
            if statuses:
                pair_decided_status[(did, year)] = statuses

    conn.close()

    # ---- in ket qua
    print("=" * 70)
    print("T263 H3 CONFLICTS — read-only phan loai 'pass noi' (r != year)")
    print("=" * 70)
    print("  W1a-legacy pass (note suy ra era-year trong khoang): %d" % w1a_total)
    print("    trong do r == year  (bang chung dung nam):          %d" % exact_passes)
    print("    trong do r != year  (CONFLICT — nam chua du chung):  %d" % len(conflicts))
    print("-" * 70)
    grp_count = Counter(g[6] for g in conflicts)
    for g in ("B", "C", "A"):
        print("  Nhom %s: %d" % (g, grp_count.get(g, 0)))
    print("-" * 70)
    if not has_support_tbl:
        print("  QUYET DINH (timeline_year_support): chua co bang quyet dinh")
        total_undecided = len(pair_group)
    else:
        print("  QUYET DINH (timeline_year_support) — tinh theo cap (dila_id, year):")
        total_undecided = 0
        for g in ("B", "C", "A"):
            pairs_g = [p for p, gg in pair_group.items() if gg == g]
            decided_status = Counter()
            undecided = 0
            for p in pairs_g:
                st = pair_decided_status.get(p)
                if not st:
                    undecided += 1
                else:
                    for s in st:
                        decided_status[s] += 1
            decided_total = len(pairs_g) - undecided
            detail = ", ".join("%s=%d" % (s, c) for s, c in sorted(decided_status.items()))
            print("    Nhom %s: %d/%d cap da co quyet dinh%s · chua co quyet dinh: %d"
                  % (g, decided_total, len(pairs_g),
                     (" (%s)" % detail) if detail else "", undecided))
            total_undecided += undecided
        print("-" * 70)
    print("  Y NGHIA: B = year nam trong khoang era text neu (ok, ghi ro support);")
    print("           C = year thuoc era khac (nghi conflation); A = year ngoai moi khoang")
    print("           (ung vien suy xet sua year theo khuon W4). MOI nhom deu can nguoi ra.")
    print("-" * 70)

    # ---- xuat file
    out_dir = os.path.abspath(a.out)
    os.makedirs(out_dir, exist_ok=True)
    tsv = os.path.join(out_dir, "%s_T263_h3_conflicts.tsv" % DATE)
    tsv_sum = os.path.join(out_dir, "%s_T263_h3_conflicts_summary.tsv" % DATE)
    with io.open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("dila_id\tyear\tr_derived\tera_name\tn\tera_span\tgroup\tghi_chu\n")
        for did, year, r, zh, n, span, grp, desc in sorted(conflicts):
            f.write("%s\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n"
                    % (did, year, r, zh, n,
                       ("%s-%s" % span) if span else "-", grp, desc))
    with io.open(tsv_sum, "w", encoding="utf-8", newline="\n") as f:
        f.write("group\tcount\tmo_ta\n")
        f.write("B\t%d\tyear trong khoang cua chinh era text neu (era trai nhieu nam)\n"
                % grp_count.get("B", 0))
        f.write("C\t%d\tyear thuoc era khac — nghi conflation nhieu su kien trong note\n"
                % grp_count.get("C", 0))
        f.write("A\t%d\tyear ngoai moi khoang niem hieu da biet — ung vien ra/sua year\n"
                % grp_count.get("A", 0))
    print("  TSV : %s" % tsv)
    print("  SUM : %s" % tsv_sum)
    print("-" * 70)
    print("  Vi du moi nhom (toi da 5 dong):")
    shown = {}
    for did, year, r, zh, n, span, grp, desc in sorted(conflicts):
        if shown.setdefault(grp, 0) >= 5:
            continue
        shown[grp] += 1
        print("   [%s] %s year=%d r=%d era=%s span=%s :: %s"
              % (grp, did, year, r, zh, span, desc))
    total = len(conflicts)
    if total:
        print("-" * 70)
        print("  CANH BAO: %d dong H3 pass 'noi' — track con so nay; phai giam dan ve 0." % total)
        if a.strict:
            if total_undecided > 0:
                print("[STRICT] con %d cap chua co quyet dinh — pipeline bi chan (Phase 3)." % total_undecided)
                return 1
            else:
                print("[STRICT-PASS] %d cap da co quyet dinh — pipeline xanh." % total)
        else:
            print("[WARN] khong chan pipeline (chay --strict o Phase 3).")
    else:
        print("SACH: khong con dong pass noi r != year — co the chuyen WARN -> STRICT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())