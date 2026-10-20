#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""T230 (P1 - roadmap T226) — Kiểm kê catalog nguồn và pháp lý, CHỈ ĐỌC.

Mục tiêu
--------
Đối chiếu danh mục nguồn đã công bố với 3 bảng registry trong DB
(`data_sources`, `source_authority`, `dataset_sources`) để biết chính xác:
  - nguồn nào có mặt ở đâu, nguồn nào thiếu;
  - nguồn nào đã có bằng chứng quyền (license_url / repository_url /
    license_verified) và nguồn nào im lặng;
  - có bao nhiêu con số "danh mục" đang mâu thuẫn nhau.

Script KHÔNG ghi DB, KHÔNG gọi ETL, KHÔNG mở public export.
Mặc định chỉ in báo cáo ra màn hình; `--out` mới ghi file báo cáo.

Cách dùng
---------
    python -X utf8 scripts/t230_source_catalog_audit.py
    python -X utf8 scripts/t230_source_catalog_audit.py --out docs/reports/T230
    python -X utf8 scripts/t230_source_catalog_audit.py --json     # máy đọc

Revert: script này không có side-effect ngoài thư mục báo cáo, xoá thư mục
báo cáo là revert trọn vẹn.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "lineage.db")
DOC_TRUSTED = os.path.join(BASE_DIR, "docs", "trusted-sources.md")
DOC_REGISTRY = os.path.join(BASE_DIR, "docs", "SOURCE_REGISTRY.md")

# Con số danh mục từng được tuyên bố. Chưa cái nào là SSOT — mục đích của
# script là đo lại và in ra mâu thuẫn thay vì giả định.
DECLARED_COUNTS = {
    "docs/trusted-sources.md (tieu de)": 20,
    "docs/TGS-integration-masterplan.md (Admin nhan)": 25,
}

# Bảng alias: tiêu đề mục trong trusted-sources.md -> mã nguồn canonical.
# Mục nào không resolve được sẽ bị ghi là `unresolved` (bằng chứng gap).
ALIASES = {
    "CBETA": ["CBETA"],
    "BDRC": ["BDRC"],
    "DDBC / DILA": ["DILA"],
    "Tipitaka.org / VRI": ["VRI"],
    "BGIS": ["BGIS"],
    "IDP": ["IDP"],
    "SAT": ["SAT"],
    "PTS": ["PTS"],
    "GRETIL": ["GRETIL"],
    "DSBC": ["DSBC"],
    "OCBS": ["OCBS"],
    "BuddhaNexus": ["BUDDHANEXUS"],
    "Kanripo": ["Kanripo"],
    "84000": ["84000"],
    "THL": ["THL"],
    "Treasury of Lives": ["TREASURY"],
    "Wikidata": ["Wikidata"],
    "CHGIS": ["TGAZ"],
    "FoJin": ["FoJin"],
    "SuttaCentral": ["SuttaCentral"],
    "ZENLINEAGE": ["ZENLINEAGE"],
    "ZQ": ["ZQLOCAL"],
    "Marcus": ["MARCUS"],
}

RE_SECTION = re.compile(r"^###\s+([\d.]+)\.?\s+(.+?)\s*$")
RE_TABLE_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|(.+)\|\s*$")
RE_TOKEN = re.compile(r"[A-Za-z0-9]+")


def normalize_dashes(text):
    """Gộp mọi kiểu gạch nối về '-' để tách tiêu đề ổn định."""
    return re.sub(r"[\u2010-\u2015\u2212]", "-", text or "")


def doc_token(title):
    """Rút mã nguồn từ tiêu đề mục: '4.5. BGIS - ...' -> 'BGIS'."""
    head = normalize_dashes(title).split("-")[0].strip()
    head = re.sub(r"\(.*?\)", "", head).strip()
    if head in ALIASES:
        return head
    m = re.match(r"^([A-Za-z][A-Za-z0-9.]{1,9})\b", head)
    if m:
        return m.group(1)
    return head


def norm(code):
    """Chuẩn hoá mã để so khớp, không đoán bỏ dấu học thuật."""
    return re.sub(r"[^A-Z0-9]", "", (code or "").upper())


def read_doc_expanded(path):
    """Đọc bảng 'Nguồn mở rộng đã duyệt' (ngoài danh mục gốc)."""
    out = []
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    inside = False
    for raw in lines:
        if re.match(r"^###\s+Ngu\u1ed3n m\u1edf r\u1ed9ng", raw):
            inside = True
            continue
        if inside and raw.startswith("##"):
            break
        if not inside:
            continue
        if not raw.strip().startswith("|"):
            continue
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= set("-: "):
            continue
        if cells[0].lower() in ("ngu\u1ed3n", "source"):
            continue
        title = re.sub(r"\(.*?\)", "", cells[0]).strip()
        out.append(make_row(
            "MR", cells[0].strip(), doc_token(title), [],
            {"group": cells[1] if len(cells) > 1 else None,
             "status": cells[2] if len(cells) > 2 else None,
             "report": cells[3] if len(cells) > 3 else None,
             "note": cells[4] if len(cells) > 4 else None}))
    return out


def make_row(number, title, token, body, extra=None):
    """Chuẩn hoá một dòng catalog về cùng một khuôn."""
    text = "\n".join(body)
    lic = re.search(r"^- \*\*License:\*\*\s*(.+)$", text, re.M)
    repo = re.search(r"^- \*\*(?:GitHub|Repo|Repository):\*\*\s*(.+)$", text, re.M)
    prio = re.search(r"^- \*\*(?:Ưu tiên|Ứu tiên|Ưu tiên):\*\*\s*(.+)$", text, re.M)
    return {
        "number": number,
        "title": title,
        "token": token,
        "codes": ALIASES.get(token, [token]),
        "resolved": token in ALIASES,
        "license_text": lic.group(1).strip() if lic else None,
        "repo_text": repo.group(1).strip() if repo else None,
        "priority_text": prio.group(1).strip() if prio else None,
        "expanded": extra,
    }


def read_doc_sections(path):
    """Đọc các mục nguồn đánh số trong trusted-sources.md."""
    out = []
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    cur = None
    for raw in lines:
        m = RE_SECTION.match(raw)
        if m:
            if cur:
                out.append(cur)
            cur = {"number": m.group(1), "title": m.group(2),
                   "token": doc_token(m.group(2)), "body": []}
            continue
        if cur is not None:
            if raw.startswith("## ") or raw.startswith("---"):
                out.append(cur)
                cur = None
            else:
                cur["body"].append(raw)
    if cur:
        out.append(cur)

    rows = []
    for s in out:
        rows.append(make_row(s["number"], s["title"], s["token"], s["body"]))
    rows.extend(read_doc_expanded(path))
    return rows


def read_doc_registry(path):
    """Đọc bảng khai báo trong SOURCE_REGISTRY.md (nguồn/authority/legal/mode).

    Chỉ đọc bảng đầu tiên (header `# | Source | Authority | ...`) để không
    nuốt nhầm các bảng khác cùng nằm trong file.
    """
    out = []
    if not os.path.isfile(path):
        return out
    inside = False
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not inside:
                if re.match(r"^\|\s*#\s*\|\s*Source\s*\|", line, re.I):
                    inside = True
                continue
            if not line.startswith("|"):
                break
            m = RE_TABLE_ROW.match(line)
            if not m:
                continue
            cells = [c.strip() for c in m.group(3).split("|")]
            out.append({
                "n": int(m.group(1)),
                "source": m.group(2).strip(),
                "authority": cells[0] if cells else None,
                "legal": cells[1] if len(cells) > 1 else None,
                "data_status": cells[2] if len(cells) > 2 else None,
                "mode": cells[3] if len(cells) > 3 else None,
                "note": cells[4] if len(cells) > 4 else None,
            })
    return out


def read_db():
    """Mở DB read-only. Không bao giờ ghi trong script kiểm kê này."""
    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError("khong thay DB: %s" % DB_PATH)
    con = sqlite3.connect("file:%s?mode=ro" % DB_PATH.replace("\\", "/"),
                          uri=True)
    con.row_factory = sqlite3.Row
    try:
        data_sources = [dict(r) for r in con.execute(
            "SELECT * FROM data_sources").fetchall()]
        authority = [dict(r) for r in con.execute(
            "SELECT * FROM source_authority").fetchall()]
        dataset_sources = [dict(r) for r in con.execute(
            "SELECT * FROM dataset_sources").fetchall()]
    finally:
        con.close()
    return data_sources, authority, dataset_sources


def rights_gaps(row):
    """Trường bằng chứng quyền còn thiếu của một row data_sources."""
    missing = []
    if not row.get("license_verified"):
        missing.append("license_verified")
    if not row.get("license_url"):
        missing.append("license_url")
    if not row.get("repository_url"):
        missing.append("repository_url")
    if not row.get("source_version"):
        missing.append("source_version")
    if not row.get("adapter_version"):
        missing.append("adapter_version")
    if not row.get("base_url"):
        missing.append("base_url")
    return missing


def build_report():
    data_sources, authority, dataset_sources = read_db()
    sections = read_doc_sections(DOC_TRUSTED)
    declared_registry = read_doc_registry(DOC_REGISTRY)

    by_code = {}
    for r in data_sources:
        by_code[norm(r.get("source_code"))] = r
    names = {}
    for r in data_sources:
        names[norm(r.get("source_name"))] = r

    auth_codes = {norm(a.get("source_code")): a for a in authority}
    ds_names = {norm(d.get("name")): d for d in dataset_sources}

    matrix = []
    for s in sections:
        matched, missing = None, []
        for code in s["codes"]:
            key = norm(code)
            if key in by_code:
                matched = by_code[key]
                break
            if key in names:
                matched = names[key]
                break
        entry = {
            "doc_number": s["number"],
            "doc_title": s["title"],
            "token": s["token"],
            "alias_resolved": s["resolved"],
            "codes": s["codes"],
            "doc_license_text": s["license_text"],
            "doc_repo_text": s["repo_text"],
            "in_data_sources": bool(matched),
            "source_id": matched.get("source_id") if matched else None,
            "source_code": matched.get("source_code") if matched else None,
            "legal_status": matched.get("legal_status") if matched else None,
            "integration_mode": matched.get("integration_mode") if matched else None,
            "license_verified": matched.get("license_verified") if matched else None,
            "license_url": matched.get("license_url") if matched else None,
            "repository_url": matched.get("repository_url") if matched else None,
            "in_source_authority": bool(matched) and norm(
                matched.get("source_code")) in auth_codes,
            "authority_score": (auth_codes.get(norm(matched["source_code"]), {})
                                .get("authority_score") if matched else None),
            "in_dataset_sources": bool(matched) and norm(
                matched.get("source_code")) in ds_names,
            "rights_missing": rights_gaps(matched) if matched else None,
            "unresolved_alias": not s["resolved"],
        }
        matrix.append(entry)
        if not matched:
            missing.append(s["token"])

    doc_codes = {norm(c) for e in matrix for c in e["codes"]}
    db_only = []
    for r in data_sources:
        key = norm(r.get("source_code"))
        if key not in doc_codes:
            db_only.append({
                "source_code": r.get("source_code"),
                "source_name": r.get("source_name"),
                "legal_status": r.get("legal_status"),
                "integration_mode": r.get("integration_mode"),
                "rights_missing": rights_gaps(r),
            })

    registry_only = []
    for d in declared_registry:
        key = norm(d["source"])
        if key not in doc_codes and key not in {norm(r.get("source_code"))
                                                for r in data_sources}:
            registry_only.append(d)

    rights = [{
        "source_code": r.get("source_code"),
        "legal_status": r.get("legal_status"),
        "integration_mode": r.get("integration_mode"),
        "license_verified": r.get("license_verified"),
        "license_url": r.get("license_url"),
        "repository_url": r.get("repository_url"),
        "software_license": r.get("software_license"),
        "data_license": r.get("data_license"),
        "corpus_license": r.get("corpus_license"),
        "image_license": r.get("image_license"),
        "redistribution_allowed": r.get("redistribution_allowed"),
        "rights_missing": rights_gaps(r),
    } for r in data_sources]

    verified = [r for r in data_sources if r.get("license_verified")]
    with_url = [r for r in data_sources if r.get("license_url")]
    with_repo = [r for r in data_sources if r.get("repository_url")]

    token_hits = {}
    for e in matrix:
        if not e["in_data_sources"]:
            token_hits[e["token"]] = token_hits.get(e["token"], 0) + 1
    dup_tokens = sorted(t for t, n in token_hits.items() if n > 1)

    return {
        "task": "T230",
        "phase": "P1 (roadmap T226) — catalog nguồn và pháp lý",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "read-only (khong ghi DB, khong ETL, khong export)",
        "db_path": os.path.relpath(DB_PATH, BASE_DIR).replace("\\", "/"),
        "counts": {
            "data_sources": len(data_sources),
            "source_authority": len(authority),
            "dataset_sources": len(dataset_sources),
            "doc_sections_numbered": len(sections),
            "doc_registry_rows": len(declared_registry),
            "declared_counts": DECLARED_COUNTS,
            "doc_only_missing_in_db": sorted(token_hits),
            "doc_duplicate_tokens": dup_tokens,
            "db_only_not_in_doc": [d["source_code"] for d in db_only],
            "registry_only": [d["source"] for d in registry_only],
        },
        "rights_summary": {
            "license_verified": len(verified),
            "license_url_present": len(with_url),
            "repository_url_present": len(with_repo),
            "total": len(data_sources),
        },
        "matrix": matrix,
        "db_only": db_only,
        "registry_only": registry_only,
        "rights": rights,
        "artifacts": {
            "note": "Chua co bang artifact cap release/commit/SHA; "
                    "chi co cot source_version dang text tu do.",
            "source_version_values": {
                (r.get("source_code") or "?"): r.get("source_version")
                for r in data_sources},
        },
    }


def render_markdown(rep):
    c = rep["counts"]
    rs = rep["rights_summary"]
    L = []
    A = L.append
    A("# T230 — Bao cao kiem ke catalog nguon va phap ly (P1)")
    A("")
    A("- **Che do:** `%s`" % rep["mode"])
    A("- **Sinh luc:** %s" % rep["generated_at"])
    A("- **DB:** `%s` (chi doc)" % rep["db_path"])
    A("")
    A("## 1. So lieu")
    A("")
    A("| Bang | So dong |")
    A("|---|---|")
    A("| `data_sources` | %d |" % c["data_sources"])
    A("| `source_authority` | %d |" % c["source_authority"])
    A("| `dataset_sources` | %d |" % c["dataset_sources"])
    A("| Mục nguồn đánh số trong `trusted-sources.md` | %d |" %
      c["doc_sections_numbered"])
    A("| Dòng khai báo trong `SOURCE_REGISTRY.md` | %d |" %
      c["doc_registry_rows"])
    A("")
    A("**Con số danh mục đang mâu thuẫn:** %s. Không cái nào là SSOT." %
      "; ".join("%s = %d" % (k, v) for k, v in c["declared_counts"].items()))
    A("")
    A("## 2. Bang chung quyen")
    A("")
    A("| Chi so | Gia tri |")
    A("|---|---|")
    A("| `license_verified = 1` | %d / %d |" %
      (rs["license_verified"], rs["total"]))
    A("| Co `license_url` | %d / %d |" %
      (rs["license_url_present"], rs["total"]))
    A("| Co `repository_url` | %d / %d |" %
      (rs["repository_url_present"], rs["total"]))
    A("")
    A("| source_code | legal_status | mode | license_verified | license_url | repository_url | thieu |")
    A("|---|---|---|---|---|---|---|")
    for r in rep["rights"]:
        A("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["source_code"], r["legal_status"], r["integration_mode"],
            r["license_verified"], r["license_url"] or "-",
            r["repository_url"] or "-",
            ", ".join(r["rights_missing"]) or "-"))
    A("")
    A("## 3. Gap nguon")
    A("")
    A("- Chỉ có trong doc, chưa có trong `data_sources`: %s" %
      (", ".join(c["doc_only_missing_in_db"]) or "không có"))
    if c.get("doc_duplicate_tokens"):
        A("- Token lặp trong doc (một nguồn nhiều mục): %s" %
          ", ".join(c["doc_duplicate_tokens"]))
    A("- Chỉ có trong DB, chưa có trong doc: %s" %
      (", ".join(c["db_only_not_in_doc"]) or "không có"))
    A("- Chỉ khai trong `SOURCE_REGISTRY.md`: %s" %
      (", ".join(c["registry_only"]) or "không có"))
    A("")
    A("| # | Tieu de | token | trong DB | source_authority | dataset_sources | alias |")
    A("|---|---|---|---|---|---|---|")
    for e in rep["matrix"]:
        A("| %s | %s | %s | %s | %s | %s | %s |" % (
            e["doc_number"], e["doc_title"], e["token"],
            "co" if e["in_data_sources"] else "KHONG",
            "co" if e["in_source_authority"] else "-",
            "co" if e["in_dataset_sources"] else "-",
            "resolved" if e["alias_resolved"] else "UNRESOLVED"))
    A("")
    A("## 4. Artifact")
    A("")
    A(rep["artifacts"]["note"])
    A("")
    for code, ver in rep["artifacts"]["source_version_values"].items():
        A("- %s: `%s`" % (code, ver))
    A("")
    A("## 5. Phai lam tiep (P1 chua xong)")
    A("")
    A("1. Admin chot danh muc chuan: doc 16 muc, DB 14, roadmap 25 — "
      "khong tu them dong.")
    A("2. `source_version` phai la release/commit/SHA cua artifact, khong "
      "phai nhanh hieu.")
    A("3. Moi source can `license_url` + `repository_url` + bang chung "
      "artifact-level; khong lay software_license lam data_license.")
    A("4. Nguon chua ro quyen giu `draft`/UNKNOWN, khong mo public export.")
    A("")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="T230 kiem ke catalog nguon (read-only)")
    ap.add_argument("--out", default="",
                    help="thu muc bao cao (mac dinh: chi in stdout)")
    ap.add_argument("--json", action="store_true",
                    help="in JSON ra stdout")
    args = ap.parse_args(argv)

    try:
        rep = build_report()
    except Exception as exc:  # noqa: BLE001 - bao loi thân thiện
        sys.stderr.write("LỖI kiểm kê catalog nguồn: %s\n" % exc)
        return 1

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0

    c = rep["counts"]
    rs = rep["rights_summary"]
    print("=" * 62)
    print("T230 — KIỂM KÊ CATALOG NGUỒN (read-only)")
    print("=" * 62)
    print("DB        : data_sources=%d  source_authority=%d  dataset_sources=%d"
          % (c["data_sources"], c["source_authority"], c["dataset_sources"]))
    print("Doc       : %d mục đánh số  ·  %d dòng trong SOURCE_REGISTRY.md"
          % (c["doc_sections_numbered"], c["doc_registry_rows"]))
    print("Mâu thuẫn  : %s" % "; ".join(
        "%s=%d" % (k, v) for k, v in c["declared_counts"].items()))
    print("Quyền      : license_verified=%d  license_url=%d  repository_url=%d"
          " (trên %d nguồn)"
          % (rs["license_verified"], rs["license_url_present"],
             rs["repository_url_present"], rs["total"]))
    print("Thiếu DB   : %s" % (", ".join(c["doc_only_missing_in_db"]) or "-"))
    print("Chỉ trong DB: %s" % (", ".join(c["db_only_not_in_doc"]) or "-"))
    print("-" * 62)
    for e in rep["matrix"]:
        print("  %-5s %-34s DB:%-3s quyen thieu:%s" % (
            e["doc_number"], e["doc_title"][:34],
            "co" if e["in_data_sources"] else "KHONG",
            ",".join(e["rights_missing"] or []) or "-"))
    print("=" * 62)

    if args.out:
        out = args.out if os.path.isabs(args.out) else os.path.join(
            BASE_DIR, args.out)
        os.makedirs(out, exist_ok=True)
        jf = os.path.join(out, "catalog-audit.json")
        mf = os.path.join(out, "README.md")
        with open(jf, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=2)
        with open(mf, "w", encoding="utf-8") as fh:
            fh.write(render_markdown(rep))
        print("Đã ghi %s" % os.path.relpath(jf, BASE_DIR))
        print("Đã ghi %s" % os.path.relpath(mf, BASE_DIR))
    return 0


if __name__ == "__main__":
    sys.exit(main())