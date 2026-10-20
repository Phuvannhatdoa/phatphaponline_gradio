import json

waiver = {
  "issuer": "Admin",
  "run_id": "VNPA-20261012-fixed001",
  "db_path": r"E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\lineage_test.db",
  "input_hash": "aa518a31caa9f073d1a499545f3b5fd814f2e0f167ef47f8c7ea47c1a3142ca8",
  "script_hash": "68ab190c79e2bf329c77b3e74f2d209a775e958593db7978ae56774dcc145f2b",
  "findings_hash": "682b55cbfe8b8f7a45a59aa5dc6c68bf11471a15b191c388529c885bea5199db",
  "expires_at": "2026-10-19T23:59:59Z"
}

with open('waiver_final.json', 'w') as f:
    json.dump(waiver, f, ensure_ascii=False, indent=2)

# Verify
with open('waiver_final.json', 'r') as f:
    w = json.load(f)
print('db_path:', repr(w['db_path']))

from pathlib import Path
db = str(Path('data/lineage_test.db').resolve(strict=True))
print('match:', w['db_path'] == str(Path('data/lineage_test.db').resolve(strict=True)))