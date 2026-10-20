# -*- coding: utf-8 -*-
"""T356: fixture tạm chứng minh partition/read-only; không mở DB production."""
import csv
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import t356_t224_readonly_audit as audit

STAMP = "2026-10-11T00:00:00+07:00"


def fixture(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE places(id TEXT PRIMARY KEY);
        CREATE TABLE places_dila(id TEXT PRIMARY KEY,name_zh TEXT,note TEXT,raw_xml TEXT,geo_lat REAL,geo_long REAL);
        CREATE TABLE place_timeline_events(id INTEGER PRIMARY KEY,dila_id TEXT,event_type TEXT,year INTEGER,
            year_end INTEGER,source TEXT,source_ref TEXT,confidence TEXT,label_vi TEXT);
        CREATE TABLE geo_cross_ref(dila_id TEXT);
    """)
    rows = [
        ("P1", "One", "marker", "", 1., 2.),
        ("P2", "Two", "", "", None, None),
        ("P3", "Three", "\u5efa\u65bc site", "", 3., 4.),
        ("P4", "Four", "\u5275\u5efa site", "", None, None),
        ("P5", "Five", "geographic prose", "", None, None),
        ("P6", "Six", "\t \n\r", "", None, None),
        ("P7", "Dissolved", "", "", None, None),
        ("P8", "RawOnly", "", '<other:note xmlns:other="http://www.tei-c.org/ns/1.0">\u59cb\u5efa\u65bc</other:note>', None, None),
        ("P9", "NewSource", "\u5efa\u570b", "", None, None),
    ]
    conn.executemany("INSERT INTO places_dila VALUES (?,?,?,?,?,?)", rows)
    conn.executemany("INSERT INTO places VALUES (?)", [(row[0],) for row in rows])
    conn.executemany("INSERT INTO geo_cross_ref VALUES (?)", [("P1",), ("P3",), ("P3",)])
    events = [
        (1,"P1","founding",100,None,"wikidata_p571","Q1","0.9","vi"),
        (2,"P1","era_mention",None,120,"dila_note","PL001·note·regex","era_range",""),
        (3,"P2","founding",200,None,"dila_founding_phase2","dila_founding_phase2","verified",""),
        (4,"P7","dissolved",1860,None,"wikidata","https://example.org/evidence","0.90",""),
        (5,"P9","era_mention",None,None,"other_source","Q1junk","NaN",""),
    ]
    conn.executemany("INSERT INTO place_timeline_events VALUES (?,?,?,?,?,?,?,?,?)", events)
    conn.commit()
    conn.close()


class TestT356(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "fixture.db"
        fixture(self.db)

    def run_report(self, name="output"):
        output = Path(self.temp.name) / name
        report = audit.run_audit(self.db, output, STAMP, command=["test-fixture"])
        with (output / "membership.csv").open(encoding="utf-8", newline="") as stream:
            members = {row["dila_id"]: row for row in csv.DictReader(stream)}
        return output, report, members

    def test_partition_unique_and_precedence_with_duplicate_xref(self):
        _, report, members = self.run_report()
        self.assertEqual(report["bucket_counts"], {"A1":2,"A2":2,"C":1,"B":2,"D":1,"E":1})
        self.assertEqual(report["membership_count"], 9)
        self.assertEqual(len(members), 9)
        self.assertEqual(members["P1"]["bucket"], "A1")
        self.assertEqual(members["P3"]["bucket"], "C")
        self.assertEqual(report["overlaps"]["no_event_xref_and_marker"], 1)

    def test_dissolved_and_era_mentions_are_not_founding_coverage(self):
        _, report, members = self.run_report()
        self.assertEqual(members["P7"]["bucket"], "A1")
        self.assertEqual(members["P7"]["has_dissolved_event"], "1")
        self.assertEqual(members["P7"]["has_founding_event"], "0")
        self.assertEqual(members["P9"]["has_any_event"], "1")
        self.assertEqual(members["P9"]["has_founding_event"], "0")
        self.assertEqual(report["flags"]["has_founding_event"], 2)
        self.assertEqual(report["overlaps"]["A1_without_founding"], 1)

    def test_raw_only_any_namespace_marker_and_no_raw_text_output(self):
        _, _, members = self.run_report()
        self.assertEqual(members["P8"]["bucket"], "B")
        self.assertEqual(members["P8"]["marker_raw_xml"], "1")
        self.assertEqual(members["P8"]["marker_note"], "0")
        self.assertNotIn("raw_xml", members["P8"])
        self.assertEqual(members["P6"]["bucket"], "E")

    def test_source_counts_independent_wikidata_p571_and_baseline_not_excluded(self):
        _, report, _ = self.run_report()
        sources = {row["source"]: row["event_count"] for row in report["sources_by_event_type"]}
        self.assertEqual(sources["wikidata"], 1)
        self.assertEqual(sources["wikidata_p571"], 1)
        self.assertEqual(report["source_event_total"], 5)
        self.assertEqual(report["baseline_55"]["current_count"], 1)
        self.assertEqual(report["baseline_55"]["historical_count"], 55)
        self.assertFalse(report["baseline_55"]["excluded_from_totals"])
        self.assertEqual(report["baseline_55"]["self_reference"], 1)

    def test_locator_and_confidence_classification(self):
        self.assertEqual(audit.source_ref_kind("Q1","x"), "qid")
        self.assertEqual(audit.source_ref_kind("Q1\u00b7P571","x"), "qid_property")
        self.assertEqual(audit.source_ref_kind("Q1\u00b7P571junk","x"), "internal")
        self.assertEqual(audit.source_ref_kind("Q1junk","x"), "internal")
        self.assertEqual(audit.source_ref_kind("Q0","x"), "internal")
        self.assertEqual(audit.source_ref_kind("https://example.org/a","x"), "url")
        self.assertEqual(audit.source_ref_kind("x","x"), "self_ref")
        self.assertEqual(audit.source_ref_kind(None,"x"), "missing")
        self.assertEqual(audit.confidence_kind("0.90"), "numeric")
        self.assertEqual(audit.confidence_kind(0), "numeric")
        self.assertEqual(audit.confidence_score(0), 0)
        self.assertEqual(audit.confidence_kind("verified"), "label")
        self.assertEqual(audit.confidence_kind("1.1"), "invalid_numeric")
        self.assertEqual(audit.confidence_kind("NaN"), "invalid_numeric")
        self.assertEqual(audit.confidence_kind(None), "missing")
        self.assertIsNone(audit.confidence_score("verified"))

    def test_readonly_rejects_writes_and_database_bytes_unchanged(self):
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        conn = audit.open_readonly(self.db)
        try:
            self.assertEqual(conn.execute("PRAGMA query_only").fetchone()[0], 1)
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE places_dila SET note='changed'")
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("CREATE TABLE forbidden(x)")
            with self.assertRaises(audit.AuditError):
                audit.select(conn, "DELETE FROM places_dila")
        finally:
            conn.close()
        self.run_report()
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(), before)

    def test_dry_run_creates_no_output_and_read_transaction_proof(self):
        output = Path(self.temp.name) / "must-not-exist"
        report = audit.run_audit(self.db, output, STAMP, dry_run=True)
        self.assertFalse(output.exists())
        self.assertEqual(report["read_only_proof"]["total_changes"], 0)
        self.assertEqual(report["read_only_proof"]["query_only"], 1)
        self.assertTrue(report["read_only_proof"]["single_read_transaction"])

    def test_manifest_hashes_and_historical_current_labels(self):
        output, report, _ = self.run_report()
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        for item in manifest["files"]:
            self.assertEqual(hashlib.sha256((output/item["path"]).read_bytes()).hexdigest(), item["sha256"])
        self.assertEqual(report["label"], "current_read_transaction")
        self.assertEqual(report["historical_reference"]["label"], "historical_reference_only")
        self.assertEqual(report["timestamp"], STAMP)
        self.assertEqual(report["database_counts"]["places_dila"], 9)
        self.assertEqual(report["historical_reference"]["total_places_dila"], 59167)

    def test_existing_output_never_overwritten_and_out_dir_required(self):
        output, _, _ = self.run_report()
        before = (output/"summary.json").read_bytes()
        with self.assertRaises(audit.AuditError):
            audit.run_audit(self.db, output, STAMP)
        self.assertEqual((output/"summary.json").read_bytes(), before)
        with self.assertRaises(audit.AuditError):
            audit.run_audit(self.db, timestamp=STAMP)

    def test_missing_schema_fails_without_migration(self):
        bad = Path(self.temp.name) / "bad.db"
        conn = sqlite3.connect(bad)
        conn.execute("CREATE TABLE places_dila(id TEXT PRIMARY KEY)")
        conn.close()
        before = bad.read_bytes()
        with self.assertRaises(audit.AuditError):
            audit.run_audit(bad, timestamp=STAMP, dry_run=True)
        self.assertEqual(bad.read_bytes(), before)

    def test_cli_help_and_fixture_dry_run(self):
        script = ROOT/"scripts/t356_t224_readonly_audit.py"
        help_run = subprocess.run([sys.executable,"-B","-X","utf8",str(script),"--help"],capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(help_run.returncode,0,help_run.stderr)
        run = subprocess.run([sys.executable,"-B","-X","utf8",str(script),"--db-path",str(self.db),"--timestamp",STAMP,"--dry-run"],
                             capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)["database_counts"]["places_dila"],9)

    def test_truncated_fields_are_not_misclassified_as_valid_prefixes(self):
        conn = sqlite3.connect(self.db)
        conn.execute("UPDATE place_timeline_events SET source_ref=?,confidence=? WHERE id=1",
                     ("Q1"+" "*2050+"junk", "0.9"+" "*70+"junk"))
        conn.commit()
        conn.close()
        output, report, members = self.run_report()
        self.assertIn("truncated",members["P1"]["source_ref_kind"])
        self.assertIn("truncated",members["P1"]["legacy_confidence_kind"])
        with (output/"events_audit.csv").open(encoding="utf-8",newline="") as stream:
            event = next(csv.DictReader(stream))
        self.assertEqual(event["source_ref_truncated"],"1")
        self.assertEqual(event["confidence_truncated"],"1")
        self.assertEqual(event["confidence_score"],"")
        self.assertEqual(report["event_source_ref_kinds"]["truncated"],1)

    def test_long_raw_xml_remains_in_sqlite_not_report(self):
        conn = sqlite3.connect(self.db)
        conn.execute("UPDATE places_dila SET raw_xml=? WHERE id='P8'", ("x"*1000000+"\u5efa\u65bc",))
        conn.commit()
        conn.close()
        output, _, members = self.run_report()
        self.assertEqual(members["P8"]["marker_raw_xml"],"1")
        self.assertGreater(int(members["P8"]["raw_xml_chars"]),1000000)
        self.assertLess((output/"membership.csv").stat().st_size,20000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
