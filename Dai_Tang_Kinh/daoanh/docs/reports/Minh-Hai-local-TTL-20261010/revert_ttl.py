import argparse, hashlib, json
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--apply',action='store_true')
parser.add_argument('--dry-run',action='store_true')
args=parser.parse_args()
base=Path(__file__).resolve().parent
root=base.parents[2]
manifest=json.loads((base/'manifest.json').read_text(encoding='utf8'))
target=(root/manifest['target']).resolve()
expected=(root/'data/ttl/TS-Minh-Hai-Phap-Bao.ttl').resolve()
backup=(root/manifest['backup_file']).resolve()
assert target==expected and backup.is_relative_to((root/'data/backups').resolve()), 'Path guard failed'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(backup)==manifest['before_sha256'], 'Backup hash mismatch'
current=sha(target)
if current==manifest['before_sha256']:
    print('Already original; no write.')
elif current!=manifest['after_sha256']:
    raise SystemExit('Target has newer edits; refuse overwrite. Re-read before reverting.')
elif not args.apply:
    print('Dry run: restore only '+str(target)+' from '+str(backup))
else:
    target.write_bytes(backup.read_bytes())
    assert sha(target)==manifest['before_sha256'], 'Restored hash mismatch'
    manifest['status']='reverted'
    (base/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\
',encoding='utf8')
    print('Restored original TTL; DB not touched.')
