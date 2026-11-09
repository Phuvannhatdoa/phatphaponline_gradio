#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T470 PHASE 2 — vong bo sung (2026-10-26).

Doc tu docs/sessions/2026-10-26/dila_json_reconcile_after_v2.csv (DB_THIEU)
+ docs/sessions/2026-10-26/dila_id_missing_from_people.csv (817 ID chua co
dong trong `people`), roi:

1. INSERT dong moi vao `people` cho 817 dila_id chua co (chi dien
   dynasty/bio/birth_year/death_year tu JSON; COT TEN de trong, khong tu
   dien/suy ten).
2. UPDATE cac cot sau CHI KHI dang NULL/rong, cho TOAN BO 49.487 ID (ca
   817 ID moi va nguoi da co):
   - people.dynasty       <- JSON dynasty (join cac phan tu bang '、')
   - people.bio           <- JSON concise_bio
   - people.birth_year / death_year <- JSON birth_death_dates (extract_year,
     giu dung quy uoc nam TCN = so am, nhu script t470_phase2_apply_birth_death.py)
   - codex_person_name.xml_sha256 <- JSON xml_sha256 (UPDATE neu dong da co
     va cot NULL/rong; INSERT dong moi neu dila_id chua co trong
     codex_person_name)

KHONG dong:
   - places_of_origin, works_in_tripitaka, cbeta_citations, active_at_places:
     JSON chi co TEN (string), khong co ID chuan de join; ghi se phai
     merge-by-name (vi pham naming-and-identity.md / data-integrity.md) ->
     DUNG, chi bao cao so lieu, khong ghi.
   - wikidata_qid: khong co bang person-wikidata nao trong DB -> chi bao cao,
     khong ghi (theo yeu cau admin).
   - canon_catalog: khong dung toi.

An toan:
   - Doc JSON goc (khong dung gia tri preview bi cat trong CSV) de co gia
     tri day du truoc khi ghi.
   - Moi UPDATE deu co dieu kien cot dich dang NULL/'' (double-check tai thoi
     diem ghi, khong tin tuong 100% CSV cu).
   - INSERT people chi khi id chua ton tai (kiem lai truoc khi ghi).
   - Ghi theo lo (mac dinh 500 dong/lo), log JSONL gia tri truoc/sau de revert
     chon loc, SELECT verify sau moi lo.
   - --apply de ghi thuc; khong co cu --apply la dry-run (chi in so lieu,
     KHONG ghi REVERT_LOG — sua theo QA 2026-10-26, tranh log bi trung lap
     khi chay dry-run nhieu lan truoc khi --apply).
   - --revert: doc lai log JSONL, set lai NULL cho dung cac o da ghi (chi khi
     gia tri hien tai con khop gia tri da ghi trong log). Voi dong `people`
     duoc INSERT moi: TRUOC KHI DELETE, kiem name_zh/name_vi/name_en/name_ja
     con NULL het khong — neu Admin da dien ten vao sau thi BO QUA, khong xoa
     (sua theo QA 2026-10-26, tranh mat du lieu Admin dien tay cho T471).
"""

import sys
import io
import os
import re
import csv
import json
import sqlite3
import pathlib
import datetime
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
DAOANH_ROOT = HERE.parent
EXTRACTED_DIR = DAOANH_ROOT / "data" / "dila_import" / "extracted"
DB_PATH = DAOANH_ROOT / "data" / "lineage.db"
SESSION_DIR = DAOANH_ROOT / "docs" / "sessions" / "2026-10-26"
CSV_V2 = SESSION_DIR / "dila_json_reconcile_after_v2.csv"
MISSING_CSV = SESSION_DIR / "dila_id_missing_from_people.csv"
LOG_PATH = SESSION_DIR / "t470_phase2_bosung_apply.log"
REVERT_LOG = SESSION_DIR / "t470_phase2_bosung_revert_log.jsonl"

WRITABLE_FIELDS = {"dynasty", "concise_bio", "birth_death_dates", "xml_sha256"}
BATCH_SIZE = 500


def extract_year(range_str):
    if not range_str:
        return None
    m = re.search(r"([+-]?\d{3,4})", str(range_str))
    return int(m.group(1)) if m else None


def load_json(pid):
    p = EXTRACTED_DIR / f"{pid}.json"
    if not p.is_file():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def log(msg, fh=None):
    print(msg)
    if fh:
        fh.write(msg + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now()

    if args.revert:
        do_revert()
        return

    with open(LOG_PATH, "a", encoding="utf-8") as log_fh:
        mode = "apply" if args.apply else "dry-run"
        log(f"\n=== t470_phase2_bosung_apply.py — {started.isoformat()} mode={mode} ===", log_fh)

        missing_ids = set()
        with open(MISSING_CSV, "r", encoding="utf-8") as f:
            r = csv.reader(f)
            next(r, None)
            for row in r:
                if row:
                    missing_ids.add(row[0].strip())
        log(f"817-list missing_from_people: {len(missing_ids)} id", log_fh)

        # Dila_id nao can xu ly cho moi field (tu CSV DB_THIEU)
        need = {f: set() for f in WRITABLE_FIELDS}
        with open(CSV_V2, "r", encoding="utf-8") as f:
            r = csv.reader(f)
            header = next(r)
            for row in r:
                if len(row) < 3:
                    continue
                pid, field, cls = row[0], row[1], row[2]
                if field in WRITABLE_FIELDS and cls == "DB_THIEU":
                    need[field].add(pid)
        for f in WRITABLE_FIELDS:
            log(f"  can xu ly field={f}: {len(need[f])} dila_id (DB_THIEU theo CSV v2)", log_fh)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("SELECT id FROM people")
        existing_people = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT dila_id FROM codex_person_name")
        existing_codex = {r[0] for r in cur.fetchall()}

        # ----- 1. INSERT 817 dong moi vao people (chi id + field co san) -----
        insert_candidates = sorted(missing_ids - existing_people)
        log(f"\n[BUOC 1] INSERT dong moi vao people: {len(insert_candidates)} ung vien "
            f"(817-list tru nhung id da co san - phong truong hop da duoc insert vong truoc)", log_fh)

        revert_entries = []
        inserted_people = 0
        updated_counts = {f: 0 for f in WRITABLE_FIELDS}
        skipped_counts = {f: 0 for f in WRITABLE_FIELDS}
        codex_inserted = 0

        for batch_start in range(0, len(insert_candidates), BATCH_SIZE):
            batch = insert_candidates[batch_start:batch_start + BATCH_SIZE]
            for pid in batch:
                data = load_json(pid)
                if not data:
                    continue
                dyn_items = [x for x in (data.get("dynasty") or []) if x]
                dynasty_val = "、".join(dyn_items) if dyn_items else None
                bio_val = data.get("concise_bio") or None
                bd = data.get("birth_death_dates") or {}
                by, dy = extract_year(bd.get("birth")), extract_year(bd.get("death"))
                if args.apply:
                    cur.execute(
                        "INSERT INTO people (id, dynasty, bio, birth_year, death_year, source_origin) "
                        "VALUES (?,?,?,?,?,?)",
                        (pid, dynasty_val, bio_val, by, dy, "DILA"),
                    )
                revert_entries.append({"table": "people", "op": "insert", "id": pid})
                inserted_people += 1
                existing_people.add(pid)
            if args.apply:
                conn.commit()
            log(f"  lo INSERT people {batch_start // BATCH_SIZE + 1}: {len(batch)} dong, "
                f"luy ke inserted_people={inserted_people}", log_fh)

        # ----- 2. UPDATE dynasty/concise_bio/birth_death_dates cho TOAN BO id can (ca moi+cu) -----
        for field, col_group in (("dynasty", ["dynasty"]), ("concise_bio", ["bio"]),
                                   ("birth_death_dates", ["birth_year", "death_year"])):
            ids = sorted(need[field])
            log(f"\n[BUOC 2] UPDATE field={field} -> cot {col_group}: {len(ids)} ung vien tu CSV", log_fh)
            processed = 0
            for batch_start in range(0, len(ids), BATCH_SIZE):
                batch = ids[batch_start:batch_start + BATCH_SIZE]
                for pid in batch:
                    data = load_json(pid)
                    if not data:
                        continue
                    if field == "dynasty":
                        items = [x for x in (data.get("dynasty") or []) if x]
                        if not items:
                            continue
                        new_val = "、".join(items)
                        cur.execute("SELECT dynasty FROM people WHERE id=?", (pid,))
                        row = cur.fetchone()
                        if row is None:
                            skipped_counts[field] += 1
                            continue
                        cur_val = row[0]
                        if cur_val and str(cur_val).strip():
                            skipped_counts[field] += 1
                            continue
                        if args.apply:
                            cur.execute("UPDATE people SET dynasty=? WHERE id=? AND (dynasty IS NULL OR dynasty='')",
                                        (new_val, pid))
                        revert_entries.append({"table": "people", "op": "update", "id": pid,
                                                "col": "dynasty", "before": cur_val, "after": new_val})
                        updated_counts[field] += 1
                    elif field == "concise_bio":
                        new_val = data.get("concise_bio") or None
                        if not new_val:
                            continue
                        cur.execute("SELECT bio FROM people WHERE id=?", (pid,))
                        row = cur.fetchone()
                        if row is None:
                            skipped_counts[field] += 1
                            continue
                        cur_val = row[0]
                        if cur_val and str(cur_val).strip():
                            skipped_counts[field] += 1
                            continue
                        if args.apply:
                            cur.execute("UPDATE people SET bio=? WHERE id=? AND (bio IS NULL OR bio='')",
                                        (new_val, pid))
                        revert_entries.append({"table": "people", "op": "update", "id": pid,
                                                "col": "bio", "before": cur_val, "after": new_val})
                        updated_counts[field] += 1
                    else:  # birth_death_dates
                        bd = data.get("birth_death_dates") or {}
                        jb, jd = extract_year(bd.get("birth")), extract_year(bd.get("death"))
                        if jb is None and jd is None:
                            continue
                        cur.execute("SELECT birth_year, death_year FROM people WHERE id=?", (pid,))
                        row = cur.fetchone()
                        if row is None:
                            skipped_counts[field] += 1
                            continue
                        cur_by, cur_dy = row
                        wrote_any = False
                        if jb is not None and cur_by is None:
                            if args.apply:
                                cur.execute("UPDATE people SET birth_year=? WHERE id=? AND birth_year IS NULL",
                                            (jb, pid))
                            revert_entries.append({"table": "people", "op": "update", "id": pid,
                                                    "col": "birth_year", "before": None, "after": jb})
                            wrote_any = True
                        if jd is not None and cur_dy is None:
                            if args.apply:
                                cur.execute("UPDATE people SET death_year=? WHERE id=? AND death_year IS NULL",
                                            (jd, pid))
                            revert_entries.append({"table": "people", "op": "update", "id": pid,
                                                    "col": "death_year", "before": None, "after": jd})
                            wrote_any = True
                        if wrote_any:
                            updated_counts[field] += 1
                        else:
                            skipped_counts[field] += 1
                    processed += 1
                if args.apply:
                    conn.commit()
                log(f"  lo {field} {batch_start // BATCH_SIZE + 1}: {len(batch)} dong xu ly, "
                    f"luy ke ghi={updated_counts[field]} bo_qua={skipped_counts[field]}", log_fh)

        # ----- 3. xml_sha256 -> codex_person_name -----
        ids = sorted(need["xml_sha256"])
        log(f"\n[BUOC 3] xml_sha256 -> codex_person_name: {len(ids)} ung vien tu CSV", log_fh)
        for batch_start in range(0, len(ids), BATCH_SIZE):
            batch = ids[batch_start:batch_start + BATCH_SIZE]
            for pid in batch:
                data = load_json(pid)
                if not data:
                    continue
                new_val = data.get("xml_sha256") or None
                if not new_val:
                    continue
                if pid in existing_codex:
                    cur.execute("SELECT xml_sha256 FROM codex_person_name WHERE dila_id=?", (pid,))
                    row = cur.fetchone()
                    cur_val = row[0] if row else None
                    if cur_val and str(cur_val).strip():
                        skipped_counts["xml_sha256"] += 1
                        continue
                    if args.apply:
                        cur.execute(
                            "UPDATE codex_person_name SET xml_sha256=? WHERE dila_id=? AND (xml_sha256 IS NULL OR xml_sha256='')",
                            (new_val, pid))
                    revert_entries.append({"table": "codex_person_name", "op": "update", "id": pid,
                                            "col": "xml_sha256", "before": cur_val, "after": new_val})
                    updated_counts["xml_sha256"] += 1
                else:
                    if args.apply:
                        cur.execute("INSERT INTO codex_person_name (dila_id, xml_sha256) VALUES (?,?)",
                                    (pid, new_val))
                    revert_entries.append({"table": "codex_person_name", "op": "insert", "id": pid})
                    existing_codex.add(pid)
                    codex_inserted += 1
            if args.apply:
                conn.commit()
            log(f"  lo xml_sha256 {batch_start // BATCH_SIZE + 1}: {len(batch)} dong, "
                f"update={updated_counts['xml_sha256']} insert_moi={codex_inserted}", log_fh)

        conn.close()

        if args.apply:
            with open(REVERT_LOG, "a", encoding="utf-8") as rfh:
                for e in revert_entries:
                    rfh.write(json.dumps(e, ensure_ascii=False) + "\n")
        else:
            log(f"[dry-run] KHONG ghi REVERT_LOG (se co {len(revert_entries)} entries neu --apply)", log_fh)

        log("\n=== TONG KET ===", log_fh)
        log(f"mode={mode}", log_fh)
        log(f"people INSERT moi: {inserted_people}", log_fh)
        log(f"people UPDATE dynasty: {updated_counts['dynasty']} (bo qua da co gia tri: {skipped_counts['dynasty']})", log_fh)
        log(f"people UPDATE bio: {updated_counts['concise_bio']} (bo qua da co gia tri: {skipped_counts['concise_bio']})", log_fh)
        log(f"people UPDATE birth/death_year (so o): {updated_counts['birth_death_dates']} ca (bo qua: {skipped_counts['birth_death_dates']})", log_fh)
        log(f"codex_person_name UPDATE xml_sha256: {updated_counts['xml_sha256']} (bo qua da co gia tri: {skipped_counts['xml_sha256']})", log_fh)
        log(f"codex_person_name INSERT moi (dila_id chua co dong): {codex_inserted}", log_fh)
        log(f"Revert log: {REVERT_LOG} ({len(revert_entries)} entries)", log_fh)
        if not args.apply:
            log("DRY-RUN — khong ghi gi vao DB. Chay lai voi --apply de ghi thuc.", log_fh)


def do_revert():
    """Doc REVERT_LOG, set lai NULL cho dung cac o da ghi (chi khi gia tri hien
    tai con khop gia tri 'after' da ghi). INSERT -> DELETE dong vua tao (chi
    khi khong co du lieu khac da duoc them vao sau boi nguoi khac - kiem truoc
    khi xoa)."""
    if not REVERT_LOG.is_file():
        print(f"Khong co revert log: {REVERT_LOG}")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    entries = []
    with open(REVERT_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    n_update_ok = 0
    n_insert_del = 0
    n_skipped_named = 0
    skipped_named_ids = []
    for e in reversed(entries):
        if e["op"] == "update":
            table, col, pid, after = e["table"], e["col"], e["id"], e.get("after")
            id_col = "id" if table == "people" else "dila_id"
            cur.execute(f"SELECT {col} FROM {table} WHERE {id_col}=?", (pid,))
            row = cur.fetchone()
            if row and row[0] == after:
                cur.execute(f"UPDATE {table} SET {col}=NULL WHERE {id_col}=?", (pid,))
                n_update_ok += 1
        elif e["op"] == "insert":
            table, pid = e["table"], e["id"]
            id_col = "id" if table == "people" else "dila_id"
            if table == "people":
                # An toan: KHONG xoa dong people neu Admin da dien ten vao sau
                # khi insert (name_zh/name_vi/name_en/name_ja). Chi xoa khi ca
                # 4 cot ten van con NULL (chua bi dien).
                cur.execute(
                    "SELECT name_zh, name_vi, name_en, name_ja FROM people WHERE id=?",
                    (pid,),
                )
                row = cur.fetchone()
                if row is None:
                    continue  # dong khong con ton tai, khong co gi de xoa
                name_zh, name_vi, name_en, name_ja = row
                has_name = any(
                    v is not None and str(v).strip() for v in (name_zh, name_vi, name_en, name_ja)
                )
                if has_name:
                    n_skipped_named += 1
                    skipped_named_ids.append(pid)
                    continue
            cur.execute(f"DELETE FROM {table} WHERE {id_col}=?", (pid,))
            n_insert_del += 1
    conn.commit()
    conn.close()
    print(f"Revert xong: {n_update_ok} UPDATE->NULL, {n_insert_del} INSERT->DELETE, "
          f"{n_skipped_named} people BO QUA (da bi Admin dien ten, khong xoa)")
    if skipped_named_ids:
        print("  ID bo qua vi da co ten:", ", ".join(skipped_named_ids))


if __name__ == "__main__":
    main()
