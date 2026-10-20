import json
import hashlib

findings = [
  {'code': 'L4', 'file': 'TS-Chuong-Hiep-Chanh-Tri.ttl', 'count': 2, 'msg': '2 ký tự Ð (U+00D0) thay cho Đ (U+0110)'},
  {'code': 'L4', 'file': 'TS-Phap-Kiem-Minh-Giac.ttl', 'count': 13, 'msg': '13 ký tự Ð (U+00D0) thay cho Đ (U+0110)'},
  {'code': 'L4', 'file': 'TS-Thiet-Dang-Bao-Quang.ttl', 'count': 6, 'msg': '6 ký tự Ð (U+00D0) thay cho Đ (U+0110)'},
  {'code': 'L4', 'file': 'TS-Thiet-Dinh-An-Triem.ttl', 'count': 9, 'msg': '9 ký tự Ð (U+00D0) thay cho Đ (U+0110)'},
  {'code': 'L4', 'file': 'TS-Toan-Y-Pho-Hue.ttl', 'count': 10, 'msg': '10 ký tự Ð (U+00D0) thay cho Đ (U+0110)'}
]
canonical_json = json.dumps(findings, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
with open('canonical_findings.json', 'w', encoding='utf-8') as f:
    f.write(canonical_json)
findings_hash = hashlib.sha256(canonical_json.encode('utf8')).hexdigest()
with open('findings_hash.txt', 'w') as f:
    f.write(findings_hash)
print('Findings hash:', findings_hash)