# -*- coding: utf-8 -*-
"""Probe nhánh CONTRACT của cổng hai tầng (chỉ đọc DB, KHÔNG ghi data/design_compliance.json).
Monkeypatch 1 metric trỏ bảng không tồn tại → kỳ vọng: contract_fail có id, exit 1 ngay cả không --strict.
Chạy: python -B -X utf8 docs/sessions/2026-10-26/gate2-tiers/contract_probe.py
"""
import os
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
SCRIPT = os.path.join(DAOANH, 'scripts', 'verify_design_compliance.py')

spec = importlib.util.spec_from_file_location('vdc', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 1) metric lỗi cấu trúc: bảng không tồn tại
m.METRICS[0] = dict(m.METRICS[0], passed_sql='SELECT COUNT(*) FROM __no_such_table_t_gate__')
p = m.compute(strict=False)
print('[PROBE] contract_fail_metrics =', p['summary']['contract_fail_metrics'])
print('[PROBE] coverage_fail_metrics =', p['summary']['coverage_fail_metrics'])
print('[PROBE] metric0 status =', p['metrics'][0]['status'], '| gate_class =', p['metrics'][0]['gate_class'])
print('[PROBE] contract_error =', p['metrics'][0]['contract_error'])

# 2) chạy main() với --json và OUT_PATH tạm (không đụng data/design_compliance.json)
m.OUT_PATH = os.path.join(HERE, 'probe_should_not_exist.json')
sys.argv = ['verify_design_compliance.py', '--json']
try:
    m.main()
    print('[PROBE] main() returned normally (exit 0)')
except SystemExit as e:
    print('[PROBE] main() SystemExit code =', e.code)
print('[PROBE] probe file written? ', os.path.exists(m.OUT_PATH))
