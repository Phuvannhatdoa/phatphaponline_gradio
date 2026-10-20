"""
TTL Person Formal Name Extractor — Phase 4
Scan all TTL files, extract formal Vietnamese names, attempt DILA crosswalk.

Usage:
    python scripts/ttl_person_name_extractor.py --dry-run
    python scripts/ttl_person_name_extractor.py --apply   (only after dry-run review)

Outputs (dry-run):
    docs/TTL_PERSON_NAME_IMPORT_DRY_RUN.csv
    docs/TTL_PERSON_NAME_REVIEW_QUEUE.csv

Outputs (apply):
    docs/TTL_PERSON_NAME_IMPORT_RESULT.csv
    Inserts rows into person_display_names table.
"""

import argparse
import csv
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import rdflib
from rdflib import URIRef
from rdflib.namespace import RDFS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
TTL_BASE = BASE_DIR / "data" / "ttl"
DB_PATH = BASE_DIR / "data" / "lineage.db"
DOCS_DIR = BASE_DIR / "docs"

# ---------------------------------------------------------------------------
# RDF constants
# Root TTL files use angle-bracket URIs (stored literally, e.g. "bkg:Monk").
# Subdir TTL files use proper prefix notation (expanded by rdflib, e.g.
# "http://www.phatphaponline.org/ontology/buddhist-kg#Monk").
# We handle both by checking both forms.
# ---------------------------------------------------------------------------
BKG_NS = rdflib.Namespace("http://www.phatphaponline.org/ontology/buddhist-kg#")
CRM_NS = rdflib.Namespace("http://www.cidoc-crm.org/cidoc-crm/")

# Root-file literals (unresolved)
MONK_TYPE_RAW   = URIRef("bkg:Monk")
CRM_P1_RAW      = URIRef("crm:P1_is_identified_by")
BKG_APP_TYPE_RAW = URIRef("bkg:hasAppellationType")
BKG_CHINESE_RAW = URIRef("bkg:ChineseName")
BKG_BIO_RAW     = URIRef("bkg:biographicalNote")

# Subdir-file proper URIs (rdflib-expanded)
MONK_TYPE_FULL  = BKG_NS.Monk
CRM_P1_FULL     = CRM_NS.P1_is_identified_by
BKG_APP_TYPE_FULL = BKG_NS.hasAppellationType
BKG_BIO_FULL    = BKG_NS.biographicalNote

# Regex to pull leading Chinese characters from the biographical note
# (used ONLY for crosswalk matching, never for display)
_ZH_PREFIX = re.compile(r"^([一-鿿㐀-䶿]+)")


def _find_monk_subjects(g: rdflib.Graph) -> list:
    """Find bkg:Monk subjects — handles both root-file literals and subdir expanded URIs."""
    subjects = set()
    for monk_type in (MONK_TYPE_RAW, MONK_TYPE_FULL):
        subjects.update(g.subjects(rdflib.RDF.type, monk_type))
    return list(subjects)


def _get_labels(g: rdflib.Graph, subj) -> list[tuple[str, str | None]]:
    """Return list of (label_text, lang) for a subject."""
    return [(str(o), getattr(o, "language", None)) for o in g.objects(subj, RDFS.label)]


def _get_appellations(g: rdflib.Graph, subj) -> list[tuple[str | None, str | None]]:
    """Return list of (label, appellation_type) from crm:P1_is_identified_by nodes."""
    results = []
    for p1_pred in (CRM_P1_RAW, CRM_P1_FULL):
        for app_node in g.objects(subj, p1_pred):
            alabel = g.value(app_node, RDFS.label)
            # appellation type can be a URI or a string literal
            for atype_pred in (BKG_APP_TYPE_RAW, BKG_APP_TYPE_FULL):
                atype = g.value(app_node, atype_pred)
                if atype is not None:
                    results.append((str(alabel) if alabel else None, str(atype)))
                    break
            else:
                if alabel:
                    results.append((str(alabel), None))
    return results


def extract_one_ttl(ttl_path: Path) -> dict:
    """Parse a single TTL file; return structured extraction dict."""
    result = {
        "ttl_file": str(ttl_path.relative_to(BASE_DIR)).replace("\\", "/"),
        "ttl_filename_stem": ttl_path.stem,
        "rdf_subject": None,
        "formal_name_vi": None,
        "formal_name_zh": None,
        "bio_zh_hint": None,  # from bio text, for crosswalk only
        "parse_error": None,
    }
    try:
        g = rdflib.Graph()
        g.parse(str(ttl_path), format="turtle")
    except Exception as exc:
        result["parse_error"] = str(exc)[:200]
        return result

    # Find the main bkg:Monk subject
    monk_subjects = _find_monk_subjects(g)
    if not monk_subjects:
        result["parse_error"] = "no bkg:Monk subject found"
        return result

    # Pick the subject whose URI slug matches the filename (most reliable)
    stem_slug = ttl_path.stem.lower().replace("-", "_")
    chosen = None
    for s in monk_subjects:
        s_str = str(s)
        slug = s_str.split("/")[-1].lower()
        if slug == stem_slug or s_str.endswith(stem_slug):
            chosen = s
            break
    if chosen is None:
        chosen = monk_subjects[0]  # fallback to first

    result["rdf_subject"] = str(chosen)

    # Formal Vietnamese name — rdfs:label with @vi or no lang
    # Also pick up @zh label for Chinese name
    for label_text, lang in _get_labels(g, chosen):
        if lang == "vi" or (lang is None and not result["formal_name_vi"]):
            vi_text = label_text.replace("_", " ").strip()
            if vi_text and not result["formal_name_vi"]:
                result["formal_name_vi"] = vi_text
        elif lang == "zh" and not result["formal_name_zh"]:
            result["formal_name_zh"] = label_text.strip()

    # Chinese name — via bkg:ChineseName or @zh appellation label
    for alabel, atype in _get_appellations(g, chosen):
        if not alabel:
            continue
        if atype and ("ChineseName" in atype or "chinese" in atype.lower()):
            if not result["formal_name_zh"]:
                result["formal_name_zh"] = alabel.strip()
        elif alabel and _ZH_PREFIX.match(alabel) and not result["formal_name_zh"]:
            # unlabelled appellation but text looks Chinese
            pass  # don't guess without type

    # Bio text hint for crosswalk (leading Chinese chars only)
    bio = None
    for bio_pred in (BKG_BIO_RAW, BKG_BIO_FULL):
        bio = g.value(chosen, bio_pred)
        if bio:
            break
    if bio and not result["formal_name_zh"]:
        m = _ZH_PREFIX.match(str(bio).strip())
        if m and len(m.group(1)) >= 2:
            result["bio_zh_hint"] = m.group(1)

    return result


def load_ttl_mapping(conn: sqlite3.Connection) -> dict:
    """Return {ttl_filename_stem: (dila_id, status)} from ttl_mapping."""
    c = conn.cursor()
    c.execute("SELECT ttl_filename, dila_id, status FROM ttl_mapping")
    mapping = {}
    for row in c.fetchall():
        stem, dila_id, status = row
        mapping[stem] = (dila_id or "", status or "")
    return mapping


def load_people_zh_index(conn: sqlite3.Connection) -> dict:
    """Return {name_zh: [dila_id, ...]} from people table for Chinese crosswalk."""
    c = conn.cursor()
    c.execute("SELECT id, name_zh FROM people WHERE name_zh IS NOT NULL AND name_zh != ''")
    index: dict[str, list[str]] = {}
    for dila_id, name_zh in c.fetchall():
        name_zh = name_zh.strip()
        index.setdefault(name_zh, []).append(dila_id)
    return index


def crosswalk(
    extraction: dict,
    ttl_map: dict,
    zh_index: dict,
) -> tuple[str, str, str, str, str]:
    """
    Return (dila_id, verification_status, matching_method, evidence, review_reason).
    """
    stem = extraction["ttl_filename_stem"]
    formal_zh = extraction.get("formal_name_zh") or ""
    bio_zh    = extraction.get("bio_zh_hint") or ""

    # --- VERIFIED_DIRECT: ttl_mapping with status 'verified' ---
    if stem in ttl_map:
        dila_id, status = ttl_map[stem]
        if status == "verified" and dila_id:
            return dila_id, "verified_direct", "ttl_mapping_filename", f"ttl_mapping row stem={stem}", ""
        else:
            return dila_id, "review_required", "ttl_mapping_filename", f"ttl_mapping status={status}", f"ttl_mapping status: {status}"

    # --- VERIFIED_CROSSWALK: exact Chinese name match against people.name_zh ---
    zh_candidates = []
    # Try formal_name_zh first
    if formal_zh and formal_zh in zh_index:
        zh_candidates = zh_index[formal_zh]
        evidence_zh = formal_zh
    elif bio_zh and bio_zh in zh_index:
        zh_candidates = zh_index[bio_zh]
        evidence_zh = bio_zh + " (bio hint)"
    else:
        evidence_zh = formal_zh or bio_zh or ""

    if len(zh_candidates) == 1:
        return zh_candidates[0], "verified_crosswalk", "chinese_name_exact", f"zh={evidence_zh} → {zh_candidates[0]}", ""
    elif len(zh_candidates) > 1:
        return "", "review_required", "chinese_name_multiple", f"zh={evidence_zh} matches {zh_candidates}", f"Multiple DILA candidates: {zh_candidates}"

    # --- REJECTED: no match ---
    reason = f"No match: formal_zh={formal_zh!r}, bio_zh={bio_zh!r}"
    return "", "rejected", "none", "", reason


def run_extraction(conn: sqlite3.Connection) -> list[dict]:
    """Scan all TTL files and return list of enriched records."""
    ttl_map = load_ttl_mapping(conn)
    zh_index = load_people_zh_index(conn)

    # Dedup: if same stem appears in both root and subdir, keep only the subdir
    # (subdir files tend to have better-structured TTL with @zh labels).
    all_files = sorted(TTL_BASE.rglob("*.ttl"))
    seen_stems: dict[str, Path] = {}
    for fp in all_files:
        stem = fp.stem
        existing = seen_stems.get(stem)
        if existing is None:
            seen_stems[stem] = fp
        elif fp.parent != TTL_BASE:
            # fp is in a subdir → prefer it over root
            seen_stems[stem] = fp
        # else keep existing (root wins over a second root copy)
    ttl_files = sorted(seen_stems.values())
    print(f"  Scanning {len(ttl_files)} TTL files ({len(all_files) - len(ttl_files)} dupes skipped) …")

    records = []
    for ttl_path in ttl_files:
        ext = extract_one_ttl(ttl_path)
        dila_id, vstatus, method, evidence, review_reason = crosswalk(ext, ttl_map, zh_index)

        records.append({
            "ttl_file": ext["ttl_file"],
            "rdf_subject": ext["rdf_subject"] or "",
            "formal_name_vi": ext["formal_name_vi"] or "",
            "formal_name_zh": ext["formal_name_zh"] or ext["bio_zh_hint"] or "",
            "dila_id_candidate": dila_id,
            "canonical_person_id": dila_id,
            "matching_method": method,
            "verification_status": vstatus,
            "evidence": evidence,
            "parse_error": ext["parse_error"] or "",
            "proposed_action": "apply" if vstatus in ("verified_direct", "verified_crosswalk") else "skip",
            "duplicate_group": "",
            "rejection_or_review_reason": review_reason or ext["parse_error"] or "",
        })

    # Detect duplicate groups (same DILA ID, multiple TTL)
    from collections import Counter
    dila_counts = Counter(r["dila_id_candidate"] for r in records if r["dila_id_candidate"])
    for r in records:
        dida = r["dila_id_candidate"]
        if dida and dila_counts[dida] > 1:
            r["duplicate_group"] = f"dila={dida} count={dila_counts[dida]}"
            if r["verification_status"] in ("verified_direct", "verified_crosswalk"):
                r["verification_status"] = "review_required"
                r["rejection_or_review_reason"] = f"Duplicate: {dila_counts[dida]} TTL files map to same DILA ID {dida}"
                r["proposed_action"] = "skip"

    return records


def write_dry_run_csv(records: list[dict], run_id: str):
    """Write TTL_PERSON_NAME_IMPORT_DRY_RUN.csv and REVIEW_QUEUE.csv."""
    DOCS_DIR.mkdir(exist_ok=True)

    dry_run_cols = [
        "ttl_file", "rdf_subject", "formal_name_vi", "formal_name_zh",
        "dila_id_candidate", "canonical_person_id", "matching_method",
        "verification_status", "evidence", "proposed_action",
        "duplicate_group", "rejection_or_review_reason",
    ]
    dry_path = DOCS_DIR / "TTL_PERSON_NAME_IMPORT_DRY_RUN.csv"
    with open(dry_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=dry_run_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)
    print(f"  Dry-run CSV: {dry_path}")

    review_cols = [
        "ttl_file", "rdf_subject", "formal_name_vi", "formal_name_zh",
        "dila_id_candidate", "matching_method", "rejection_or_review_reason",
    ]
    review_path = DOCS_DIR / "TTL_PERSON_NAME_REVIEW_QUEUE.csv"
    review_rows = [r for r in records if r["verification_status"] in ("review_required", "rejected")]
    with open(review_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=review_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(review_rows)
    print(f"  Review queue: {review_path} ({len(review_rows)} rows)")

    # Summary
    from collections import Counter
    counts = Counter(r["verification_status"] for r in records)
    total = len(records)
    print(f"\n  === DRY-RUN SUMMARY (run_id={run_id}) ===")
    print(f"  Total TTL files scanned : {total}")
    print(f"  verified_direct         : {counts['verified_direct']}")
    print(f"  verified_crosswalk      : {counts['verified_crosswalk']}")
    print(f"  review_required         : {counts['review_required']}")
    print(f"  rejected                : {counts['rejected']}")
    print(f"  parse_error             : {sum(1 for r in records if r['parse_error'])}")
    return counts


def ensure_schema(conn: sqlite3.Connection):
    """Create person_display_names table if not exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS person_display_names (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id             TEXT    NOT NULL,
            dila_person_id        TEXT,
            locale                TEXT    NOT NULL DEFAULT 'vi',
            display_name_vi       TEXT    NOT NULL,
            display_name_zh       TEXT,
            authority_name_vi     TEXT,
            authority_name_zh     TEXT,
            appellation_vi        TEXT,
            appellation_zh        TEXT,
            style_type            TEXT    DEFAULT 'formal',
            is_preferred          INTEGER DEFAULT 1,
            verification_status   TEXT    NOT NULL,
            source_type           TEXT    DEFAULT 'ttl',
            source_file           TEXT    NOT NULL,
            source_subject_uri    TEXT,
            source_predicate      TEXT    DEFAULT 'rdfs:label',
            source_ref            TEXT,
            mapping_method        TEXT,
            mapping_evidence      TEXT,
            import_run_id         TEXT,
            created_at            TEXT    DEFAULT CURRENT_TIMESTAMP,
            updated_at            TEXT    DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (person_id, locale, source_file)
        )
    """)
    conn.commit()


def load_authority_names(conn: sqlite3.Connection, dila_ids: list[str]) -> dict:
    """Return {dila_id: (name_vi, name_zh)} from people table."""
    if not dila_ids:
        return {}
    c = conn.cursor()
    placeholders = ",".join("?" * len(dila_ids))
    c.execute(f"SELECT id, name_vi, name_zh FROM people WHERE id IN ({placeholders})", dila_ids)
    return {row[0]: (row[1] or "", row[2] or "") for row in c.fetchall()}


def apply_import(records: list[dict], conn: sqlite3.Connection, run_id: str, dry_run: bool):
    """Insert verified records into person_display_names."""
    ensure_schema(conn)

    to_apply = [r for r in records if r["verification_status"] in ("verified_direct", "verified_crosswalk")]
    if not to_apply:
        print("  No verified records to apply.")
        return []

    dila_ids = list({r["dila_id_candidate"] for r in to_apply if r["dila_id_candidate"]})
    auth_names = load_authority_names(conn, dila_ids)

    applied = []
    for r in to_apply:
        pid = r["dila_id_candidate"]
        auth_vi, auth_zh = auth_names.get(pid, ("", ""))

        # Derive appellation (prefix before the dharma name)
        # e.g., "Bách Trượng Hoài Hải" → try to split off last 2 syllables as dharma name
        # We do not guess — leave null unless we can verify from data
        appellation_vi = None
        appellation_zh = None

        row = {
            "person_id"           : pid,
            "dila_person_id"      : pid,
            "locale"              : "vi",
            "display_name_vi"     : r["formal_name_vi"],
            "display_name_zh"     : r["formal_name_zh"] or None,
            "authority_name_vi"   : auth_vi or None,
            "authority_name_zh"   : auth_zh or None,
            "appellation_vi"      : appellation_vi,
            "appellation_zh"      : appellation_zh,
            "style_type"          : "formal",
            "is_preferred"        : 1,
            "verification_status" : r["verification_status"],
            "source_type"         : "ttl",
            "source_file"         : r["ttl_file"],
            "source_subject_uri"  : r["rdf_subject"],
            "source_predicate"    : "rdfs:label",
            "source_ref"          : None,
            "mapping_method"      : r["matching_method"],
            "mapping_evidence"    : r["evidence"],
            "import_run_id"       : run_id,
        }

        if dry_run:
            applied.append(row)
            continue

        conn.execute("""
            INSERT OR IGNORE INTO person_display_names
            (person_id, dila_person_id, locale, display_name_vi, display_name_zh,
             authority_name_vi, authority_name_zh, appellation_vi, appellation_zh,
             style_type, is_preferred, verification_status, source_type, source_file,
             source_subject_uri, source_predicate, source_ref, mapping_method,
             mapping_evidence, import_run_id)
            VALUES
            (:person_id, :dila_person_id, :locale, :display_name_vi, :display_name_zh,
             :authority_name_vi, :authority_name_zh, :appellation_vi, :appellation_zh,
             :style_type, :is_preferred, :verification_status, :source_type, :source_file,
             :source_subject_uri, :source_predicate, :source_ref, :mapping_method,
             :mapping_evidence, :import_run_id)
        """, row)
        applied.append(row)

    if not dry_run:
        conn.commit()

    return applied


def write_result_csv(applied: list[dict]):
    out = DOCS_DIR / "TTL_PERSON_NAME_IMPORT_RESULT.csv"
    cols = [
        "person_id", "dila_person_id", "display_name_vi", "display_name_zh",
        "authority_name_vi", "verification_status", "mapping_method",
        "mapping_evidence", "source_file", "import_run_id",
    ]
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(applied)
    print(f"  Result CSV: {out} ({len(applied)} rows applied)")


def main():
    parser = argparse.ArgumentParser(description="TTL Person Name Extractor")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Extract and report only, do NOT write to DB (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Write verified records to person_display_names table")
    args = parser.parse_args()

    do_apply = args.apply
    run_id = datetime.utcnow().strftime("run_%Y%m%d_%H%M%S")

    print(f"TTL Person Name Extractor — {run_id}")
    print(f"Mode: {'APPLY' if do_apply else 'DRY-RUN'}")
    print(f"TTL base: {TTL_BASE}")
    print(f"DB: {DB_PATH}")
    print()

    if not DB_PATH.exists():
        sys.exit(f"ERROR: DB not found: {DB_PATH}")
    if not TTL_BASE.exists():
        sys.exit(f"ERROR: TTL dir not found: {TTL_BASE}")

    conn = sqlite3.connect(str(DB_PATH))
    ensure_schema(conn)

    records = run_extraction(conn)
    counts = write_dry_run_csv(records, run_id)

    if do_apply:
        guard_ok = (
            counts.get("verified_direct", 0) + counts.get("verified_crosswalk", 0) > 0
        )
        if not guard_ok:
            print("\nGuard: 0 verified records — nothing to apply.")
        else:
            print(f"\nApplying {counts.get('verified_direct',0) + counts.get('verified_crosswalk',0)} records…")
            applied = apply_import(records, conn, run_id, dry_run=False)
            write_result_csv(applied)
            print(f"  Done. {len(applied)} rows written to person_display_names.")
    else:
        # Dry-run: show what would be applied
        applied = apply_import(records, conn, run_id, dry_run=True)
        if applied:
            write_result_csv(applied)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
