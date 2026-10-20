#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T394 - GIAI DOAN 2 finalize (read-only source, in-place enrich of 6 audit JSON).

Tang them vao 6 deliverable cua docs/reports/zenodo-10004109-survey-20261016/
analysis/phase2/ - KHONG sua DB/TTL/legacy, KHONG import production.

Them:
  1. edge-diff.json            -> data.csv_edge_to_tei_lb_crosswalk
  2. uncertainty-inventory.json-> data.linkgrp_cert_low_detail (+ summary)
  3. rights-matrix.json        -> matrix[].unresolved / unresolved_reason
  4. person-id-audit.json      -> records[].dila_live (+ summary)
  5. relation-direction-audit.json -> data.dila_live_direction_crosscheck
  6. generation-inventory.json -> data.ptda_conversion_policy_statement

Chay:
  python -X utf8 scripts/t394_phase2_finalize.py --dry-run
  python -X utf8 scripts/t394_phase2_finalize.py --apply
  python -X utf8 scripts/t394_phase2_finalize.py --restore
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCAN = os.path.join(REPO, "docs", "reports", "zenodo-10004109-survey-20261016")
PH2 = os.path.join(SCAN, "analysis", "phase2")
DLIVE = os.path.join(PH2, "dila_live")
SRC = os.path.join(SCAN, "extracted", "vancutsem_laurent")

FILES = [
    "edge-diff.json",
    "relation-direction-audit.json",
    "generation-inventory.json",
    "uncertainty-inventory.json",
    "rights-matrix.json",
    "person-id-audit.json",
]

TEI_FILES = [
    "03-zutangji-haidongxinkaiyinbanji_SNA.xml",
    "03-zutangji-zutangjixu_SNA.xml",
    "03-zutangji_supp_SNA_caotang.xml",
    "03-zutangji_supp_SNA_xinghua.xml",
]

CSV_EDGES = "05-ZTJ_edges_ZTJmain.csv"

# 4 file TEI khai bao CC BY-NC-SA 4.0 trong khi record/README = CC BY 4.0
TEI_MIXED = set(TEI_FILES)


COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def strip_comments(text):
    """Bo XML comment - vi du tai dong 1457 chua 3 <linkGrp> minh hoa (neu khong bo se dem sai)."""
    return COMMENT_RE.sub("", text)


def read_tei(fn):
    with open(os.path.join(SRC, fn), encoding="utf-8") as fh:
        return strip_comments(fh.read())


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


# ---------------------------------------------------------------- crosswalk
def build_lb_index():
    """locator ed=B -> {file, line, ztj_locator}."""
    index = {}
    ed_b_total = 0
    for fn in TEI_FILES:
        path = os.path.join(SRC, fn)
        with open(path, encoding="utf-8") as fh:
            lines = strip_comments(fh.read()).splitlines(keepends=True)
        last_ztj = None
        for i, line in enumerate(lines, start=1):
            for m in re.finditer(r"<lb\b[^>]*>", line):
                tag = m.group(0)
                ed = re.search(r'ed="([^"]*)"', tag)
                n = re.search(r'n="([^"]*)"', tag)
                if not n:
                    continue
                if ed and ed.group(1) == "B":
                    ed_b_total += 1
                    index.setdefault(n.group(1), []).append(
                        {"file": fn, "line": i, "lb": tag.strip(), "ztj": None}
                    )
                elif ed and ed.group(1).startswith("K.1503"):
                    last_ztj = n.group(1)
                    # gan nguoc cho locator B ngay truoc (neu chua co ztj)
                    prev = index.get(_prev_b(lines, i))
                    if prev and prev[-1]["ztj"] is None:
                        prev[-1]["ztj"] = last_ztj
    return index, ed_b_total


def _prev_b(lines, upto):
    for j in range(upto - 1, -1, -1):
        m = re.search(r'<lb\b[^>]*ed="B"[^>]*n="([^"]+)"', lines[j])
        if m:
            return m.group(1)
    return None


def edges_crosswalk():
    path = os.path.join(SRC, CSV_EDGES)
    with open(path, encoding="utf-8-sig") as fh:
        raw = fh.read().splitlines()
    header = raw[0].split(",")
    rows = []
    for line in raw[1:]:
        if not line.strip():
            continue
        parts = line.split(",", len(header) - 1)
        rows.append(dict(zip(header, parts)))

    index, ed_b_total = build_lb_index()
    loc_re = re.compile(r"#([0-9a-z]+)\b")
    per_edge = []
    used = set()
    for r in rows:
        ref = r.get("e@ref", "")
        locs = loc_re.findall(ref)
        matches = []
        for loc in locs:
            used.add(loc)
            hits = index.get(loc, [])
            matches.append(
                {
                    "locator": loc,
                    "matched": bool(hits),
                    "tei": [
                        {"file": h["file"], "line": h["line"], "ztj": h["ztj"]}
                        for h in hits
                    ],
                }
            )
        per_edge.append(
            {
                "source": r.get("Source"),
                "target": r.get("Target"),
                "type": r.get("Type"),
                "uuid": r.get("Id"),
                "e_ref": ref,
                "locators": matches,
            }
        )
    missing = sorted(
        {m["locator"] for e in per_edge for m in e["locators"] if not m["matched"]}
    )
    unused = sorted(set(index.keys()) - used)
    return {
        "definition": (
            "Map tung locator trong e@ref cua 256 CSV edge sang <lb ed=\"B\"> trong 4 TEI. "
            "Khong dung de chon dinh dang chuan; chi la doi soat locator."
        ),
        "csv_edge_count": len(per_edge),
        "distinct_locators": len(used),
        "matched_locators": len([l for l in used if l in index]),
        "missing_locators": missing,
        "missing_count": len(missing),
        "tei_lb_ed_B_total": ed_b_total,
        "tei_lb_ed_B_used_by_edges": len([l for l in used if l in index]),
        "tei_lb_ed_B_unused": unused,
        "tei_lb_ed_B_unused_count": len(unused),
        "unused_note": (
            "lb ed=B khong xuat hien trong e@ref cua edge table; co the phuc vu noi dung khac, "
            "khong ket luan la thieu canh."
        ),
        "edges": per_edge,
    }


# ---------------------------------------------------------------- uncertainty
def linkgrp_low_detail():
    """41 linkGrp cert=low: dem <link> ben trong + pham vi."""
    fn = TEI_FILES[0]
    text = read_tei(fn)
    groups = []
    for m in re.finditer(r"<linkGrp\b[^>]*>.*?</linkGrp>", text, re.S):
        blob = m.group(0)
        cm = re.search(r'cert="([^"]+)"', blob)
        if not (cm and cm.group(1) == "low"):
            continue
        line = text[: m.start()].count("\n") + 1
        links = re.findall(r"<link\b[^>]*>", blob)
        targets = []
        for lk in links:
            tm = re.search(r'target="([^"]+)"', lk)
            if tm:
                targets += [t.lstrip("#") for t in tm.group(1).split()]
        ptrs = [
            p.lstrip("#")
            for p in re.findall(r'<ptr\b[^>]*target="([^"]+)"', blob)
        ]
        groups.append(
            {
                "file": fn,
                "line": line,
                "link_count": len(links),
                "targets": sorted(set(targets)),
                "ptr_targets": sorted(set(ptrs)),
            }
        )
    targets_flat = [t for g in groups for t in g["targets"]]
    ptr_flat = [t for g in groups for t in g["ptr_targets"]]
    return {
        "definition": (
            "41 linkGrp cert=\"low\" chi nam trong file haidongxinkaiyinbanji. "
            "Dem <link> ben trong tung nhom; so nhom KHONG bang so canh."
        ),
        "comment_stripped": True,
        "group_count": len(groups),
        "total_link_elements": sum(g["link_count"] for g in groups),
        "distinct_link_targets": len(set(targets_flat)),
        "distinct_ptr_targets": len(set(ptr_flat)),
        "max_links_per_group": max((g["link_count"] for g in groups), default=0),
        "scope": "extracted/vancutsem_laurent/" + fn,
        "signal_only": (
            "cert=low la tin hieu do tin cay cua nguon, KHONG loai canh, "
            "KHONG xac nhan huong thay/de tu."
        ),
        "groups": groups,
    }


# ---------------------------------------------------------------- rights
def rights_flags():
    """Danh dau unresolved cho 4 file TEI co khai bao ghep."""
    rows = {}
    for fn in TEI_MIXED:
        rows["extracted/vancutsem_laurent/" + fn] = {
            "unresolved": True,
            "unresolved_reason": (
                "File-specific notice CC BY-NC-SA 4.0 xung dot voi record/README CC BY 4.0; "
                "chua co van ban giai thich tu nguon. Khong ket luan phap ly."
            ),
        }
    return rows


# ---------------------------------------------------------------- DILA live
def load_dila_live():
    path = os.path.join(DLIVE, "dila-live-lookup-20261016-final.json")
    if not os.path.exists(path):
        return None
    return load_json(path)


def dila_summary(live):
    recs = live["records"]
    ok = [r for r in recs if r.get("fields")]
    return {
        "schema": live.get("schema"),
        "source_file": "analysis/phase2/dila_live/dila-live-lookup-20261016-final.json",
        "requested": len(recs),
        "accessible": len(ok),
        "inaccessible": len(recs) - len(ok),
        "note": (
            "Tra cuu truc tiep authority.dila.edu.tw (first-hand). "
            "HTTP200 + ID khop KHONG dong nghia xac nhan identity/lineage. "
            "Khong gop nhan vat."
        ),
    }


def attach_dila(records, live):
    byid = {r["authority_id_requested"]: r for r in live["records"]}
    for rec in records:
        sid = rec.get("source_id")
        lr = byid.get(sid)
        if not lr:
            rec["dila_live"] = {
                "status": "not_attempted",
                "authority_id_requested": sid,
            }
            continue
        f = lr.get("fields", {})
        rec["dila_live"] = {
            "status": "accessible" if f else "inaccessible",
            "authority_id_requested": sid,
            "url": lr.get("url"),
            "fetched_at_utc": lr.get("fetched_at_utc"),
            "sha256_html": lr.get("sha256_html"),
            "response_bytes": lr.get("response_bytes"),
            "dynasty": f.get("wiki_Dynasty"),
            "gender": f.get("wiki_Gender"),
            "is_monk": f.get("wiki_is_monk"),
            "is_historical": f.get("wiki_Historical"),
            "relationship": lr.get("teacher_disciple"),
            "same_as": lr.get("wiki_sameas"),
            "occurs_in": lr.get("wiki_OccurredIn"),
            "note": f.get("wiki_Note"),
            "identity_policy": "khong gop; chi ghi bang chung first-hand",
        }


def relation_dila_crosscheck(live, person_ids):
    byid = {r["authority_id_requested"]: r for r in live["records"]}
    out = []
    for pid in person_ids:
        lr = byid.get(pid)
        if not lr:
            continue
        out.append(
            {
                "person_id": pid,
                "dila_relationship_raw": lr.get("teacher_disciple"),
                "dila_direction_basis": (
                    "DILA ghi [老師]/[弟子] theo nguon (v.d. 禪典·禪宗法系譜), "
                    "KHONG theo quy uoc '嗣' cua ZTJ; giu rieng provenance."
                ),
            }
        )
    return {
        "definition": (
            "Doi chieu huong quan he: huong do nguon ghi (DILA) vs huong tu suy tu ZTJ. "
            "Thieu bang chung -> giu undirected/unknown."
        ),
        "records": out,
    }


# ---------------------------------------------------------------- generation
def generation_policy():
    return {
        "statement": (
            "Gia tri generation trong CSV/XLSX duoc giu NGUYEN BAN. "
            "Khong quy doi sang he so doi PTDA, khong cong/tru offset, "
            "khong suy so doi tu ten hay vi tri."
        ),
        "ptda_conversion": "none",
        "raw_preserved": True,
    }


# ---------------------------------------------------------------- main
def run(apply_changes):
    backups = {}
    live = load_dila_live()
    if live is None:
        print("!! thieu dila-live-lookup-20261016-final.json", file=sys.stderr)
        return 2

    # --- backups
    for fn in FILES:
        p = os.path.join(PH2, fn)
        if not os.path.exists(p):
            print("!! thieu", p, file=sys.stderr)
            return 2
        backups[fn] = sha256_file(p)

    if apply_changes:
        for fn in FILES:
            p = os.path.join(PH2, fn)
            bak = p + ".pre-t394.bak"
            if not os.path.exists(bak):
                shutil.copy2(p, bak)

    # --- 1. edge-diff
    p = os.path.join(PH2, "edge-diff.json")
    ed = load_json(p)
    cw = edges_crosswalk()
    ed["data"]["csv_edge_to_tei_lb_crosswalk"] = cw
    if apply_changes:
        dump_json(p, ed)
    print("edge-diff: locators=%d matched=%d missing=%d unused=%d"
          % (cw["distinct_locators"], cw["matched_locators"],
             cw["missing_count"], cw["tei_lb_ed_B_unused_count"]))

    # --- 2. uncertainty
    p = os.path.join(PH2, "uncertainty-inventory.json")
    un = load_json(p)
    detail = linkgrp_low_detail()
    un["data"]["linkgrp_cert_low_detail"] = detail
    if apply_changes:
        dump_json(p, un)
    print("uncertainty: groups=%d links=%d distinct_targets=%d max=%d"
          % (detail["group_count"], detail["total_link_elements"],
             detail["distinct_link_targets"], detail["max_links_per_group"]))

    # --- 3. rights
    p = os.path.join(PH2, "rights-matrix.json")
    rt = load_json(p)
    flags = rights_flags()
    n_unres = 0
    for row in rt["data"]["matrix"]:
        f = flags.get(row["file"])
        if f:
            row["unresolved"] = True
            row["unresolved_reason"] = f["unresolved_reason"]
            n_unres += 1
        else:
            row["unresolved"] = False
            row["unresolved_reason"] = None
    rt["data"]["unresolved_count"] = n_unres
    rt["data"]["unresolved_policy"] = (
        "unresolved=True nghia la KHONG du can cu de ket luan phap ly; "
        "khong tu dong cap hay chon mot license."
    )
    if apply_changes:
        dump_json(p, rt)
    print("rights: unresolved=%d / %d" % (n_unres, len(rt["data"]["matrix"])))

    # --- 4. person-id-audit
    p = os.path.join(PH2, "person-id-audit.json")
    pa = load_json(p)
    attach_dila(pa["data"]["records"], live)
    pa["data"]["dila_live_lookup_summary"] = dila_summary(live)
    if apply_changes:
        dump_json(p, pa)
    print("person-id-audit: attached dila_live to %d records"
          % len(pa["data"]["records"]))

    # --- 5. relation-direction-audit
    p = os.path.join(PH2, "relation-direction-audit.json")
    rd = load_json(p)
    rd["data"]["dila_live_direction_crosscheck"] = relation_dila_crosscheck(
        live, pa["data"]["person_ids"]
    )
    if apply_changes:
        dump_json(p, rd)
    print("relation-direction: crosscheck %d ids"
          % len(rd["data"]["dila_live_direction_crosscheck"]["records"]))

    # --- 6. generation-inventory
    p = os.path.join(PH2, "generation-inventory.json")
    gi = load_json(p)
    gi["data"]["ptda_conversion_policy"] = generation_policy()
    if apply_changes:
        dump_json(p, gi)
    print("generation: policy attached")

    print("MODE:", "APPLY" if apply_changes else "DRY-RUN")
    return 0


def restore():
    n = 0
    for fn in FILES:
        p = os.path.join(PH2, fn)
        bak = p + ".pre-t394.bak"
        if os.path.exists(bak):
            shutil.copy2(bak, p)
            n += 1
    print("restored", n, "files")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--restore", action="store_true")
    a = ap.parse_args()
    if a.restore:
        restore()
    else:
        sys.exit(run(a.apply))
