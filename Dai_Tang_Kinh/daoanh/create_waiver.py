import sys
sys.path.insert(0, 'scripts')
import t357_vnpa_safe_etl as t357
import json

# Compute input_hash
inputs = t357.inputs_manifest('data/ttl/old')
input_hash = t357.digest(inputs)

# Compute script_hash
scripts = t357.scripts_manifest()
script_hash = t357.digest(scripts)

# Findings hash (from earlier)
findings_hash = "682b55cbfe8b8f7a45a59aa5dc6c68bf11471a15b191c388529c885bea5199db"

print("input_hash:", input_hash)
print("script_hash:", script_hash)
print("findings_hash:", findings_hash)

# Create waiver
waiver = {
    "issuer": "Admin",
    "run_id": "VNPA-20261012-auto",
    "db_path": "E:\\\\Backup 2025\\\\QuaiTieuTu\\\\Anan Son\\\\phatphaponline_gradio\\\\truyenthua\\\\visjs-app\\\\Dai_Tang_Kinh\\\\daoanh\\\\data\\\\lineage_test.db",
    "input_hash": input_hash,
    "script_hash": script_hash,
    "findings_hash": findings_hash,
    "expires_at": "2026-10-19T23:59:59Z"
}

with open('waiver_complete.json', 'w') as f:
    json.dump(waiver, f, ensure_ascii=False, indent=2)

print("\nWaiver written to waiver_complete.json")