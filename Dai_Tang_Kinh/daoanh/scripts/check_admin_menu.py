import sys
from pathlib import Path

REQUIRED = [
    ('admin/index.html', 'agent_team.html'),
    ('admin/index.html', 'DILA Team Agent Dashboard'),
    ('admin/index.html', 'sync_log.html'),
]

def main():
    base = Path(__file__).resolve().parent.parent
    missing = []
    for rel, needle in REQUIRED:
        p = base / rel
        if not p.exists() or needle not in p.read_text(encoding='utf-8', errors='replace'):
            missing.append(f'{rel}: missing "{needle}"')
    if missing:
        print('[FAIL] admin menu missing:')
        for m in missing:
            print('  - ' + m)
        return 1
    print('[OK] admin menu has DILA Team Agent Dashboard')
    return 0

if __name__ == '__main__':
    sys.exit(main())
