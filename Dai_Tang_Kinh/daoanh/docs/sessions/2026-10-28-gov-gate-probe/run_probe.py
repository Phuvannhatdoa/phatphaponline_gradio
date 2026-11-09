# -*- coding: utf-8 -*-
"""Probe: gate test:gov vẫn bắt được vi phạm license (không đụng data/lineage.db)."""
import os
import shutil
import sqlite3
import subprocess
import sys

# Daoanh root: file nằm ở docs/sessions/2026-10-28-gov-gate-probe/run_probe.py
DAOANH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
DB = os.path.join(DAOANH, 'data', 'lineage.db')
PROBE_DB = os.path.join(DAOANH, 'docs', 'sessions', '2026-10-28-gov-gate-probe', 'probe.db')

os.makedirs(os.path.dirname(PROBE_DB), exist_ok=True)
if not os.path.isfile(DB):
    raise FileNotFoundError('DB không tồn tại: ' + DB)
if os.path.exists(PROBE_DB):
    os.unlink(PROBE_DB)
shutil.copy2(DB, PROBE_DB)

def run_pytest(extra_args):
    return subprocess.run([sys.executable, '-X', 'utf8', '-m', 'pytest'] + extra_args,
                          cwd=DAOANH, capture_output=True, text=True)

# 1. Baseline: DB gốc (copy) → test phải PASS (18/18)
r1 = run_pytest(['tests/test_b25_authority_contract.py', '-q'])
print('=== BASELINE ===')
print('exit:', r1.returncode)
print(r1.stdout[-300:])

# 2. Vi phạm: Wikidata verified=1 + data_commercial=1 → FAIL
c = sqlite3.connect(PROBE_DB)
c.execute("UPDATE data_sources SET license_verified=1, data_commercial=1 WHERE source_code='Wikidata'")
c.commit()
c.close()
r2 = run_pytest(['tests/test_b25_authority_contract.py::test_e_all_sources_license_unverified', '-q'])
print('=== PROBE Wikidata verified=1 + commercial=1 ===')
print('exit:', r2.returncode, '(kỳ vọng != 0)')
print(r2.stdout[-500:])

# 3. Vi phạm: thêm nguồn verified ngoài danh sách (ZQLOCAL) → FAIL
c = sqlite3.connect(PROBE_DB)
c.execute("UPDATE data_sources SET license_verified=1 WHERE source_code='ZQLOCAL'")
c.commit()
c.close()
r3 = run_pytest(['tests/test_b25_authority_contract.py::test_e_all_sources_license_unverified', '-q'])
print('=== PROBE ZQLOCAL verified=1 (ngoài VERIFIED_SOURCES) ===')
print('exit:', r3.returncode, '(kỳ vọng != 0)')
print(r3.stdout[-500:])

# 4. Vi phạm: source verified nhưng backfill data_license → FAIL
c = sqlite3.connect(PROBE_DB)
c.execute("UPDATE data_sources SET license_verified=1, data_license='CC-BY' WHERE source_code='ZQLOCAL'")
c.commit()
c.close()
r4 = run_pytest(['tests/test_b25_authority_contract.py::test_e_all_sources_license_unverified', '-q'])
print('=== PROBE ZQLOCAL verified=1 + data_license backfill ===')
print('exit:', r4.returncode, '(kỳ vọng != 0)')
print(r4.stdout[-500:])

# 5. Vi phạm: nguồn verified không phi thương mại (CBETA data_commercial=1) → FAIL
c = sqlite3.connect(PROBE_DB)
c.execute("UPDATE data_sources SET data_commercial=1 WHERE source_code='CBETA'")
c.commit()
c.close()
r5 = run_pytest(['tests/test_b25_authority_contract.py::test_e_all_sources_license_unverified', '-q'])
print('=== PROBE CBETA data_commercial=1 ===')
print('exit:', r5.returncode, '(kỳ vọng != 0)')
print(r5.stdout[-500:])

os.unlink(PROBE_DB)
print('=== probe.db đã xóa, data/lineage.db không bị thay đổi ===')
