"""T357 fixture/fault-injection tests. Không đọc DB/TTL production."""
import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import etl_ttl_person_authority as legacy
import t357_vnpa_safe_etl as safe

TTL = '''@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://fixture/monk/monk_alpha> a bkg:Monk; rdfs:label "Alpha"@vi;
 bkg:biographicalNote "Xuất gia 1089, trùng tu 1163";
 bkg:hasTeacher <https://fixture/monk/teacher>;
 bkg:associatedPlaces <https://fixture/place/p1>;
 bkg:authoredWorks <https://fixture/work/w1>;
 bkg:hasKeyLifeEvent <https://fixture/event/life> .
<https://fixture/monk/teacher> rdfs:label "Teacher"@vi .
<https://fixture/place/p1> rdfs:label "Place"@vi .
<https://fixture/work/w1> rdfs:label "Work"@vi .
<https://fixture/event/life> rdfs:label "Life"@vi; bkg:year 1120 .
'''
BETA = '''@prefix bkg: <http://www.phatphaponline.org/ontology/buddhist-kg#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
<https://fixture/monk/monk_beta> a bkg:Monk; rdfs:label "Beta"@vi;
 bkg:biographicalNote "Một đoạn lịch sử 1500–1600, không phải sinh tử" .
'''


class SafetyFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='t357-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'fixture.db'
        self.ttl = self.root / 'ttl'
        self.ttl.mkdir()
        (self.ttl / 'Alpha.ttl').write_text(TTL, encoding='utf-8')
        (self.ttl / 'Beta.ttl').write_text(BETA, encoding='utf-8')
        conn = sqlite3.connect(self.db)
        conn.executescript(legacy.SCHEMA)
        conn.execute('CREATE TABLE ttl_mapping(ttl_filename TEXT,dila_id TEXT)')
        conn.execute("INSERT INTO ttl_mapping VALUES ('Alpha','A-new')")
        conn.execute("INSERT INTO vn_person_authority(id,ttl_filename,name_vi,dila_id,status,birth_year,death_year) "
                     "VALUES ('monk_alpha','Alpha','Curated Alpha','A-old','confirmed',111,222)")
        conn.execute("INSERT INTO vn_person_authority(id,ttl_filename,name_vi,dila_id,status) "
                     "VALUES ('alias_keep','Alpha','Alias','A-alias','confirmed')")
        conn.execute("INSERT INTO vn_person_authority(id,ttl_filename,name_vi) VALUES ('outside','Outside','Outside')")
        conn.execute("INSERT INTO vn_person_relations VALUES (10,'monk_alpha','hasTeacher','stale','Stale','Alpha')")
        conn.execute("INSERT INTO vn_person_relations VALUES (20,'outside','hasTeacher','monk_alpha','Alpha',NULL)")
        conn.execute("INSERT INTO vn_person_events VALUES (40,'monk_alpha','KeyLifeEvent','life','Old',1000,'Alpha')")
        conn.commit()
        conn.close()
        safe.initialize_controls(self.db)
        self.reference = self.root / 'label-reference.json'
        self.reference.write_text(json.dumps({'definition_version': 'T357-label-reference-v1',
            'issuer': 'fixture-only', 'reviewed': True, 'source_locators': ['fixture labels Alpha/Beta'],
            'index': {'alpha': {'Alpha': 1}, 'beta': {'Beta': 1}}}), encoding='utf-8')
        self.index = 0

    def plan(self, **kwargs):
        self.index += 1
        out = self.root / ('plan-' + str(self.index))
        result = safe.make_plan(self.db, self.ttl, out, run_id='fixture-' + str(self.index), label_reference=self.reference, **kwargs)
        return out, result

    def auth(self, plan):
        return {'issuer': 'fixture-review-only', 'expires_at': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                'run_id': plan['run_id'], 'db_path': str(self.db.resolve()),
                'plan_hash': plan['plan_hash'], 'external_writers_quiesced': True, 'diff_hash': plan['diff_hash']}

    def dump(self):
        conn = sqlite3.connect(self.db)
        result = {table: conn.execute('SELECT * FROM "' + table + '" ORDER BY 1,2').fetchall()
                  for table in safe.TABLES + ('ttl_mapping', 'vnpa_etl_runs', 'vnpa_etl_changes', 'sqlite_sequence')}
        conn.close()
        return result

    def sql(self, statement):
        conn = sqlite3.connect(self.db)
        conn.execute(statement)
        conn.commit()
        conn.close()

    def test_plan_real_preflight_is_readonly_and_bounded_stage(self):
        before = self.dump()
        out, plan = self.plan()
        self.assertEqual(self.dump(), before)
        self.assertEqual(plan['findings'], [])
        self.assertTrue((out / 'stage.sqlite').exists())
        self.assertGreater(plan['counts']['accepted'], 0)
        self.assertEqual(plan['counts']['failed'], 0)
        conn = safe.connect(self.db)
        with self.assertRaises(sqlite3.OperationalError):
            conn.execute("DELETE FROM vn_person_authority")
        conn.close()

    def test_apply_single_commit_and_strict_counts_preserve_dates_ids_alias(self):
        out, plan = self.plan()
        trace = []
        result = safe.apply_plan(out, self.auth(plan), trace=trace.append)
        self.assertEqual(sum(s.strip().upper() == 'COMMIT' for s in trace), 1)
        self.assertEqual(sum(s.strip().upper() == 'BEGIN IMMEDIATE' for s in trace), 1)
        self.assertEqual(result['counts'], plan['counts'])
        rows = self.dump()['vn_person_authority']
        alpha = next(r for r in rows if r[0] == 'monk_alpha')
        beta = next(r for r in rows if r[0] == 'monk_beta')
        self.assertEqual((alpha[2], alpha[10], alpha[11], alpha[13], alpha[14]),
                         ('Curated Alpha', 111, 222, 'A-old', 'confirmed'))
        self.assertEqual((beta[10], beta[11]), (None, None))
        self.assertEqual(len([r for r in rows if r[0] == 'alias_keep']), 1)
        self.assertTrue(any(r[0] == 20 for r in self.dump()['vn_person_relations']))
        self.assertIn('biography-year-not-canonical', (out / 'date-candidates.jsonl').read_text(encoding='utf-8'))

    def test_faults_at_every_mutation_and_before_commit_restore_full_rowsets(self):
        locations = ('after_begin', 'after_deleted:vn_person_relations',
                     'after_inserted:vn_person_authority', 'after_updated:vn_person_authority',
                     'after_inserted:vn_person_places', 'after_inserted:vn_person_works',
                     'after_inserted:vn_person_relations', 'after_updated:vn_person_events', 'before_commit')
        for location in locations:
            with self.subTest(location=location):
                before = self.dump()
                out, plan = self.plan()
                reached = []
                def inject(point):
                    reached.append(point)
                    if point == location:
                        raise RuntimeError('fault:' + point)
                with self.assertRaises(RuntimeError):
                    safe.apply_plan(out, self.auth(plan), fault=inject)
                self.assertIn(location, reached)
                self.assertEqual(self.dump(), before)

    def test_parse_failure_before_rw(self):
        before = self.dump()
        (self.ttl / 'Alpha.ttl').write_text('not valid turtle @@@', encoding='utf-8')
        with self.assertRaises(safe.SafetyError):
            self.plan()
        self.assertEqual(self.dump(), before)

    def test_missing_preflight_failclosed(self):
        before = self.dump()
        original = safe.importlib.import_module
        def missing(name):
            if name == 't204_ttl_preflight':
                raise ImportError('fixture missing module')
            return original(name)
        with mock.patch.object(safe.importlib, 'import_module', side_effect=missing):
            with self.assertRaises(ImportError):
                self.plan()
        self.assertEqual(self.dump(), before)

    def test_missing_db_not_created_and_missing_controls_not_migrated(self):
        missing = self.root / 'missing.db'
        with self.assertRaises(FileNotFoundError):
            safe.make_plan(missing, self.ttl, self.root / 'no-create', label_reference=self.reference)
        self.assertFalse(missing.exists())
        self.sql('DROP TABLE vnpa_etl_changes')
        before = safe.file_hash(self.db)
        with self.assertRaises(safe.SafetyError):
            self.plan()
        self.assertEqual(safe.file_hash(self.db), before)

    def test_skip_preflight_cli_failclosed(self):
        before = self.dump()
        with contextlib.redirect_stderr(io.StringIO()):
            status = legacy.main(['--db', str(self.db), '--skip-preflight'])
        self.assertEqual(status, 1)
        self.assertEqual(self.dump(), before)

    def test_waiver_exact_binding_expiry_and_nonwaivable_parse(self):
        warning = {'code': 'L2', 'file': 'Alpha.ttl', 'msg': 'fixture'}
        def findings(directory, conn, reference):
            return [warning], []
        with self.assertRaises(safe.SafetyError):
            self.plan(preflight=findings)
        run_id = 'waiver-fixture'
        inputs = safe.inputs_manifest(self.ttl)
        waiver = {'issuer': 'fixture-review', 'run_id': run_id, 'db_path': str(self.db.resolve()),
                  'input_hash': safe.digest(inputs), 'script_hash': safe.digest(safe.scripts_manifest()),
                  'findings_hash': safe.digest([warning]),
                  'expires_at': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}
        good = safe.make_plan(self.db, self.ttl, self.root / 'waived', run_id, waiver, findings, label_reference=self.reference)
        self.assertEqual(good['findings'], [warning])
        waiver['expires_at'] = '2000-01-01T00:00:00+00:00'
        with self.assertRaises(safe.SafetyError):
            safe.make_plan(self.db, self.ttl, self.root / 'expired', run_id, waiver, findings)
        with self.assertRaises(safe.SafetyError):
            self.plan(preflight=lambda *_: ([{'code': 'L3'}], []), waiver=waiver)

    def test_logical_db_input_mapping_and_schema_drift_fail_before_mutation(self):
        mutations = ("UPDATE vn_person_authority SET name_vi='Drift' WHERE id='outside'",
                     "UPDATE ttl_mapping SET dila_id='Drift' WHERE ttl_filename='Alpha'",
                     'CREATE TABLE extra_schema(x TEXT)')
        for statement in mutations:
            with self.subTest(statement=statement):
                out, plan = self.plan()
                self.sql(statement)
                before = self.dump()
                with self.assertRaises(safe.SafetyError):
                    safe.apply_plan(out, self.auth(plan))
                self.assertEqual(self.dump(), before)
        out, plan = self.plan()
        (self.ttl / 'Beta.ttl').write_text(BETA + '\n# drift\n', encoding='utf-8')
        before = self.dump()
        with self.assertRaises(safe.SafetyError):
            safe.apply_plan(out, self.auth(plan))
        self.assertEqual(self.dump(), before)

    def test_invalid_auth_and_writer_lock(self):
        out, plan = self.plan()
        before = self.dump()
        ack = self.auth(plan)
        ack['external_writers_quiesced'] = False
        with self.assertRaises(safe.SafetyError):
            safe.apply_plan(out, ack)
        lock = Path(str(self.db) + '.t357-writer.lock')
        lock.write_text('another-writer', encoding='utf-8')
        with self.assertRaises(safe.SafetyError):
            safe.apply_plan(out, self.auth(plan))
        self.assertTrue(lock.exists())
        self.assertEqual(self.dump(), before)

    def test_sql_exception_ignored_insert_and_protected_trigger_rollback(self):
        triggers = (
            "CREATE TRIGGER fixture_ignore BEFORE INSERT ON vn_person_authority WHEN NEW.id='monk_beta' BEGIN SELECT RAISE(IGNORE); END",
            "CREATE TRIGGER fixture_protected AFTER UPDATE ON vn_person_authority WHEN NEW.id='monk_alpha' BEGIN UPDATE vn_person_authority SET name_vi='Bad' WHERE id='alias_keep'; END",
        )
        for index, trigger in enumerate(triggers):
            with self.subTest(trigger=trigger):
                self.sql(trigger)
                out, plan = self.plan()
                before = self.dump()
                with self.assertRaises(safe.SafetyError):
                    safe.apply_plan(out, self.auth(plan))
                self.assertEqual(self.dump(), before)
                self.sql('DROP TRIGGER ' + ('fixture_ignore' if index == 0 else 'fixture_protected'))

    def test_expected_managed_rowset_detects_trigger_insert(self):
        self.sql("CREATE TRIGGER fixture_extra AFTER INSERT ON vn_person_authority WHEN NEW.id='monk_beta' "
                 "BEGIN INSERT INTO vn_person_authority(id,ttl_filename,name_vi) VALUES('unplanned','Alpha','Extra'); END")
        out, plan = self.plan()
        before = self.dump()
        with self.assertRaises(safe.SafetyError):
            safe.apply_plan(out, self.auth(plan))
        self.assertEqual(self.dump(), before)

    def test_duplicate_staged_business_key_fails_before_write(self):
        with open(self.ttl / 'Alpha.ttl', 'a', encoding='utf-8') as stream:
            stream.write('<https://fixture/monk/monk_alpha> <http://www.phatphaponline.org/ontology/buddhist-kg#hasTeacher> <https://other/teacher> .')
        before = self.dump()
        with self.assertRaises(safe.SafetyError):
            self.plan()
        self.assertEqual(self.dump(), before)

    def test_after_commit_report_failure_reconciles_ledger_and_no_repeat_mutation(self):
        out, plan = self.plan()
        def fail(point):
            if point == 'after_commit':
                raise OSError('report unavailable')
        with self.assertRaises(OSError):
            safe.apply_plan(out, self.auth(plan), fault=fail)
        before = self.dump()
        result = safe.apply_plan(out, self.auth(plan))
        self.assertTrue(result['replayed'])
        self.assertEqual(result['counts']['inserted'], 0)
        self.assertEqual(self.dump(), before)

    def test_new_run_same_inputs_has_zero_semantic_diff(self):
        out, plan = self.plan()
        safe.apply_plan(out, self.auth(plan))
        before = {k: v for k, v in self.dump().items() if k in safe.TABLES}
        other, plan2 = self.plan()
        self.assertEqual(plan2['counts']['inserted'] + plan2['counts']['updated'] + plan2['counts']['deleted'], 0)
        safe.apply_plan(other, self.auth(plan2))
        self.assertEqual({k: v for k, v in self.dump().items() if k in safe.TABLES}, before)

    def test_run_id_collision_and_stage_tamper_failclosed(self):
        out, plan = self.plan()
        safe.apply_plan(out, self.auth(plan))
        other = self.root / 'collision'
        collision = safe.make_plan(self.db, self.ttl, other, run_id=plan['run_id'], label_reference=self.reference)
        before = self.dump()
        with self.assertRaises(safe.SafetyError):
            safe.apply_plan(other, self.auth(collision))
        with open(out / 'date-candidates.jsonl', 'a', encoding='utf-8') as stream:
            stream.write('{}\n')
        with self.assertRaises(safe.SafetyError):
            safe.apply_plan(out, self.auth(plan))
        self.assertEqual(self.dump(), before)

    def test_scoped_rollback_preserves_unrelated_later_write(self):
        original = self.dump()
        out, plan = self.plan()
        safe.apply_plan(out, self.auth(plan))
        self.sql("UPDATE vn_person_authority SET name_vi='Later outside' WHERE id='outside'")
        result = safe.rollback_run(self.db, plan['run_id'], self.auth(plan))
        self.assertGreater(result['restored'], 0)
        after = self.dump()
        original['vn_person_authority'] = [tuple('Later outside' if i == 2 and row[0] == 'outside' else value
                                                for i, value in enumerate(row)) for row in original['vn_person_authority']]
        for table in safe.TABLES:
            self.assertEqual(after[table], original[table])

    def test_rollback_drift_and_fault_are_atomic(self):
        out, plan = self.plan()
        safe.apply_plan(out, self.auth(plan))
        before = self.dump()
        def fail(_):
            raise RuntimeError('inverse fault')
        with self.assertRaises(RuntimeError):
            safe.rollback_run(self.db, plan['run_id'], self.auth(plan), fault=fail)
        self.assertEqual(self.dump(), before)
        self.sql("UPDATE vn_person_authority SET name_vi='Later curated' WHERE id='monk_beta'")
        before = self.dump()
        with self.assertRaises(safe.SafetyError):
            safe.rollback_run(self.db, plan['run_id'], self.auth(plan))
        self.assertEqual(self.dump(), before)


    def test_frozen_reference_failclosed_and_never_calls_corpus_index(self):
        import t203_quarantine_ttl as q
        with mock.patch.object(q, 'authoritative_index', side_effect=AssertionError('outside-scope corpus scan')):
            out, plan = self.plan()
            safe.apply_plan(out, self.auth(plan))
        with self.assertRaises(safe.SafetyError):
            safe.make_plan(self.db, self.ttl, self.root / 'no-reference')


    def test_inverse_ledger_tamper_stops_rollback(self):
        out, plan = self.plan()
        safe.apply_plan(out, self.auth(plan))
        self.sql("UPDATE vnpa_etl_changes SET before_json='{}' WHERE seq=1")
        before = self.dump()
        with self.assertRaisesRegex(safe.SafetyError, 'ledger hash'):
            safe.rollback_run(self.db, plan['run_id'], self.auth(plan))
        self.assertEqual(self.dump(), before)

    def test_control_ignored_rowcount_cannot_claim_commit(self):
        self.sql("CREATE TRIGGER fixture_control BEFORE INSERT ON vnpa_etl_runs BEGIN SELECT RAISE(IGNORE); END")
        out, plan = self.plan()
        before = self.dump()
        with self.assertRaisesRegex(safe.SafetyError, 'Control affected rowcount'):
            safe.apply_plan(out, self.auth(plan))
        self.assertEqual(self.dump(), before)

    def test_cli_reports_committed_artifact_failure_distinctly(self):
        out, plan = self.plan()
        ack_file = self.root / 'authorization.json'
        ack_file.write_text(json.dumps(self.auth(plan)), encoding='utf-8')
        original = safe.apply_plan
        def broken_report(directory, ack):
            def fail(point):
                if point == 'after_commit':
                    raise OSError('artifact failure fixture')
            return original(directory, ack, fault=fail)
        output = io.StringIO()
        with mock.patch.object(safe, 'apply_plan', side_effect=broken_report), contextlib.redirect_stdout(output):
            status = safe.cli(['--mode', 'apply', '--db', str(self.db), '--out-dir', str(out),
                               '--authorization', str(ack_file)])
        self.assertEqual(status, 2)
        result = json.loads(output.getvalue())
        self.assertEqual(result['state'], 'committed_artifact_failed')
        self.assertEqual(result['counts']['failed'], 0)


    def test_rollback_trigger_outside_scope_fails_closed_and_rolls_back(self):
        out, plan = self.plan()
        safe.apply_plan(out, self.auth(plan))
        self.sql("CREATE TRIGGER rollback_corrupt AFTER UPDATE ON vn_person_authority WHEN NEW.id='monk_alpha' "
                 "BEGIN UPDATE vn_person_authority SET name_vi='ROLLBACK_CORRUPTED' WHERE id='outside'; END")
        before = self.dump()
        with self.assertRaises(safe.RollbackBlocked) as caught:
            safe.rollback_run(self.db, plan['run_id'], self.auth(plan))
        self.assertEqual(caught.exception.state, 'rollback_blocked')
        self.assertRegex(str(caught.exception), 'protected/outside|not authorized')
        self.assertEqual(self.dump(), before)

    def test_final_control_trigger_cannot_write_business_rows_on_apply(self):
        self.sql("CREATE TRIGGER late_apply AFTER UPDATE ON vnpa_etl_runs "
                 "BEGIN UPDATE vn_person_authority SET name_vi='LATE_TRIGGER_CORRUPTED' WHERE id='outside'; END")
        out, plan = self.plan()
        before = self.dump()
        trace = []
        with self.assertRaisesRegex(safe.SafetyError, 'unsupported trigger|not authorized'):
            safe.apply_plan(out, self.auth(plan), trace=trace.append)
        self.assertEqual(self.dump(), before)
        self.assertNotIn('COMMIT', [s.strip().upper() for s in trace])

    def test_final_control_trigger_cannot_write_business_rows_on_rollback(self):
        out, plan = self.plan()
        safe.apply_plan(out, self.auth(plan))
        self.sql("CREATE TRIGGER late_rollback AFTER UPDATE ON vnpa_etl_runs "
                 "BEGIN UPDATE vn_person_authority SET name_vi='LATE_TRIGGER_CORRUPTED' WHERE id='outside'; END")
        before = self.dump()
        with self.assertRaises(safe.RollbackBlocked) as caught:
            safe.rollback_run(self.db, plan['run_id'], self.auth(plan))
        self.assertEqual(caught.exception.state, 'rollback_blocked')
        self.assertEqual(self.dump(), before)

    def test_invalid_generation_and_self_teacher_disciple_rejected_before_rw(self):
        cases = ((-1, None), (0, None), (201, None), (1, 'hasTeacher'),
                 (1, 'hasDisciple'), (-1, 'hasTeacher'))
        original_connect = safe.connect
        for generation, relation in cases:
            with self.subTest(generation=generation, relation=relation):
                extra = '<https://fixture/monk/monk_beta> bkg:generationOrder %s' % generation
                extra += ('; bkg:%s <https://fixture/monk/monk_beta>' % relation) if relation else ''
                (self.ttl / 'Beta.ttl').write_text(BETA + extra + ' .\n', encoding='utf-8')
                before = self.dump()
                modes = []
                def tracked(path, mode='ro'):
                    modes.append(mode)
                    return original_connect(path, mode)
                with mock.patch.object(safe, 'connect', side_effect=tracked):
                    with self.assertRaises(safe.SafetyError):
                        self.plan()
                self.assertNotIn('rw', modes)
                self.assertEqual(self.dump(), before)

    def test_years_never_digits_concatenation_or_biography_min_max(self):
        self.assertIsNone(legacy.extract_year('1500–1600'))
        self.assertIsNone(legacy.extract_year('around 1500'))
        self.assertIsNone(legacy.extract_year('1500-99-99'))
        self.assertEqual(legacy.extract_year('1500-01-02'), 1500)
        self.assertEqual(legacy.extract_year('-100'), -100)


if __name__ == '__main__':
    unittest.main(verbosity=2)
