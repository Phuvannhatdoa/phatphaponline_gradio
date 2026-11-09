"""
T22-LD3 — Rà tay 3 nhóm còn treo, sinh danh sách review (read-only, KHÔNG ghi DB).

  N1. 86 row `dila_era_name` event_type='founding' còn lại
      → năm trong note có phải năm XÂY, hay năm TU SỬA / đổi tên?
  N2. 5 row `dila_founding_phase2` (đã ghi ra data/t22_phase2_review.json)
  N3. 23 row `dila_founding_phase2` có label_zh ≠ places_dila.name_zh
      → tên nào đúng? Có phải 2 place khác nhau không?

Output: `data/t22_ld3_review.json` (máy phân loại theo luật) + bảng console để
người đọc phán quyết tay. Script KHÔNG tự sửa — mọi quyết định do Admin.

Usage
-----
  python -X utf8 scripts/t22_ld3_review_remaining.py
"""

import json
import os
import re
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "..", "data", "lineage.db")
OUT = os.path.join(HERE, "..", "data", "t22_ld3_review.json")

# --- từ khoá TU SỬA / ĐỔI TÊN (dùng escape để không lệ từ khi truyền shell) ---
RENOVATION = re.compile(
    "重建|重修|重興|重創|重立|修葺|募捐|改建|再造|再興|修葺|擴建|增修|復建|恢復"
)
RENAME = re.compile("改名|更名|改稱|稱為|改號|遷都|遷都|改置|升鎮|置為")
UNKNOWN = re.compile("始建年代不可考|始建年代不詳|年代不可考|不詳|無考")
# --- năm Ả Rập, có hoặc không kèm 年 ---
PAREN_YEAR = re.compile("[\uff08(]\\s*(\\d{3,4})\\s*[\uff09)]")
ARAB_YEAR = re.compile("(\\d{3,4})\\s*\u5e74")


def context(note, year, before=34, after=18):
    """Trả về đoạn note bao quanh năm `year` (ưu tiên dạng ngoặc tròn)."""
    for rx in (PAREN_YEAR, ARAB_YEAR):
        for m in rx.finditer(note):
            if m.group(1) == str(year):
                return " ".join(note[max(0, m.start() - before): m.end() + after].split())
    i = note.find(str(year))
    if i >= 0:
        return " ".join(note[max(0, i - before): i + len(str(year)) + after].split())
    return ""


def review_era_name(conn):
    rows = conn.execute(
        "SELECT e.id, e.dila_id, e.year, e.label_zh, e.confidence, p.note "
        "FROM place_timeline_events e JOIN places_dila p ON p.id = e.dila_id "
        "WHERE e.source = 'dila_era_name' AND e.event_type = 'founding'"
    ).fetchall()
    out = []
    for rid, did, year, lab, conf, note in rows:
        note = note or ""
        ctx = context(note, year)
        flags = []
        if RENOVATION.search(ctx):
            flags.append("renovation_in_ctx")
        if RENAME.search(ctx):
            flags.append("rename_in_ctx")
        if UNKNOWN.search(note):
            flags.append("founding_unknown")
        # năm có nằm trong ngoặc ngay sau marker thành lập?
        near = bool(PAREN_YEAR.search(note)) or bool(ARAB_YEAR.search(note))
        verdict = "can_xay" if (not flags and near) else ("nghi_van" if flags else "khong_ro")
        out.append({
            "id": rid, "dila_id": did, "year": year, "label_zh": lab,
            "confidence": conf, "flags": flags, "verdict": verdict,
            "context": ctx[:110],
        })
    return out


def review_phase2_5():
    p = os.path.join(HERE, "..", "data", "t22_phase2_review.json")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def review_name_mismatch(conn):
    rows = conn.execute(
        "SELECT e.dila_id, e.label_zh, e.year, p.name_zh, m.name_zh AS map_zh, "
        "       m.name_vi, m.needs_review "
        "FROM place_timeline_events e "
        "JOIN places_dila p ON p.id = e.dila_id "
        "LEFT JOIN namevi_map_places m ON m.dila_id = e.dila_id "
        "WHERE e.source = 'dila_founding_phase2' AND e.label_zh <> p.name_zh"
    ).fetchall()
    out = []
    for did, ev, year, pd, mp, vi, rev in rows:
        out.append({
            "dila_id": did, "event_label_zh": ev, "places_dila_name_zh": pd,
            "map_name_zh": mp, "name_vi": vi, "needs_review": rev, "year": year,
            # bản đồ khớp: 'event' = namevi_map ủng hộ event; 'places_dila' = ngược lại
            "side": ("event" if mp == ev else ("places_dila" if mp == pd else "khong_xac_dinh")),
        })
    return out


def main():
    conn = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)

    n1 = review_era_name(conn)
    print("=== N1. 86 row era_name con lai ===")
    import collections
    v = collections.Counter(x["verdict"] for x in n1)
    print("   can_xay %d | nghi_van %d | khong_ro %d"
          % (v["can_xay"], v["nghi_van"], v["khong_ro"]))
    print()
    for tag in ("nghi_van", "khong_ro"):
        sub = [x for x in n1 if x["verdict"] == tag]
        print("   --- %s (%d) ---" % (tag, len(sub)))
        for x in sub[:14]:
            print("     %-14s y=%-6s %-34s" % (x["dila_id"], x["year"], x["context"][:60]))
        print()

    n2 = review_phase2_5()
    print("=== N2. 5 row phase2 nghi van ===")
    for x in n2:
        print("   %-14s y=%-6s %-18s %s" % (x["dila_id"], x["year"], x["flag"],
                                            (x.get("context") or "")[:56]))
    print()

    n3 = review_name_mismatch(conn)
    print("=== N3. %d row lech label_zh vs places_dila.name_zh ===" % len(n3))
    sc = collections.Counter(x["side"] for x in n3)
    print("   namevi_map ủng hộ phía: %s" % dict(sc))
    for x in n3[:14]:
        print("   %-14s ev=%-11r pd=%-11r map=%-11r vi=%r"
              % (x["dila_id"], x["event_label_zh"], x["places_dila_name_zh"],
                 x["map_name_zh"], x["name_vi"]))
    print()

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"n1_era_name": n1, "n2_phase2_5": n2, "n3_name_mismatch": n3},
                  f, ensure_ascii=False, indent=1)
    print("Đã ghi: %s" % OUT)
    conn.close()


if __name__ == "__main__":
    main()