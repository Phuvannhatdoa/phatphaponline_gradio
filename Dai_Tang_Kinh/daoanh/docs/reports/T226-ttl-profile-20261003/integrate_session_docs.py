from pathlib import Path
r=Path('docs/reports/T226-ttl-profile-20261003')
p=Path('docs/tasktodo.md');s=p.read_text(encoding='utf-8-sig');entry=(r/'tasktodo-entry.txt').read_text(encoding='utf8')
if 'T226 — TTL học thuật v2' not in s:
 at=s.find('\n');p.write_bytes((s[:at]+'\n\n'+entry+'\n'+s[at:]).encode('utf8'))
p=Path('docs/ROLLBACK.md');s=p.read_text(encoding='utf-8-sig');entry=(r/'rollback-entry.txt').read_text(encoding='utf8')
if 'T226 — TTL profile/editor v2' not in s:p.write_bytes((s+'\n'+entry).encode('utf8'))
print('Tasktodo and rollback updated without replacing other session entries')
