#!/usr/bin/env python3
"""
T177 D6 — Fix 2 rules đang giữ rule_text='_keep_' (toggle-sentinel lưu nhầm xuống thật).
====================================================================================
Admin phê chuẩn 2026-09-26:
  (1) NO_PINYIN      → RESTORE rule_text + description từ seed gốc `scripts/t73_translation_system.py`
                      (rule duy nhất cấm pinyin; không có rule thay thế).
  (2) HANVIET_NAMES  → DEACTIVATE (is_active=0) vì trùng vai trò CANONICAL_NAMES + HANVIET_PLACES
                      (đã hoạt động). Hết xuất hiện trong prompt + khỏi khuyến nghị lỗi.

Sau khi đổi: invalidate cache hợp lệ (invalidate_cache_for_rule) để constitution_hash của
đúng các row liên quan được tính lại — tránh miss toàn bộ cache (T165 §3).

CLI:
  python -X utf8 scripts/t177_d6_rules_fix.py --stats|--dry-run|--apply|--revert

  --stats   in trạng thái hiện tại (không đổi gì)
  --dry-run preview UPDATE (không commit)
  --apply   thực hiện (backup tự động thành data/backups/lineage_t177_d6_fix_<ts>.db)
  --revert  khôi phục trạng thái cũ (NO_PINYIN lại '_keep_', HANVIET_NAMES lại is_active=1)
            — KHÔNG vô hiệu hoá thay đổi cache (cache invalidated thì vẫn invalidated như
            admin đã bấm; muốn lấy lại bản dịch cũ → restore backup trước khi apply)
"""
import sqlite3, sys, shutil, argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))  # để import style_constitution được (SSOT cùng cấp daoanh)
DB = ROOT / 'data' / 'lineage.db'
BACKUP_DIR = ROOT / 'data' / 'backups'

# Khớp seed gốc scripts/t73_translation_system.py (line 18-40)
NO_PINYIN_TXT = (
    "NGHIÊM CẤM dùng phiên âm pinyin Trung Quốc trong bản dịch. "
    "Ví dụ: KHÔNG viết 'Zhijixiang', 'Bianjing', 'fashi', 'chanshi', 'dashi'. "
    "Tất cả tên riêng và danh hiệu phải chuyển sang âm Hán-Việt tương ứng."
)
NO_PINYIN_DESC = "Cấm tuyệt đối dùng pinyin"
HANVIET_NAMES_DESC = "Tên người → âm Hán-Việt (DEACTIVATED 2026-09-26 — trùng CANONICAL_NAMES/HANVIET_PLACES)"


def conn():
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    return c


def _has_col(c, table, col):
    return any(r[1] == col for r in c.execute(f"PRAGMA table_info({table})"))


def current(c):
    out = {}
    rows = c.execute(
        "SELECT rule_code, rule_type, description, rule_text, is_active, status, updated_at "
        "FROM translation_rules WHERE rule_code IN ('NO_PINYIN','HANVIET_NAMES') ORDER BY rule_code"
    ).fetchall()
    for r in rows:
        out[r['rule_code']] = dict(r)
    return out


def stats(c):
    st = c.execute(
        "SELECT status, is_active, COUNT(*) n FROM translation_rules GROUP BY status, is_active"
    ).fetchall()
    active = c.execute(
        "SELECT COUNT(*) FROM translation_rules WHERE status='active' AND is_active=1"
    ).fetchone()[0]
    keep = c.execute(
        "SELECT COUNT(*) FROM translation_rules WHERE status='active' AND is_active=1 AND rule_text='_keep_'"
    ).fetchone()[0]
    cache_total = c.execute("SELECT COUNT(*) FROM translation_cache").fetchone()[0]
    cache_inv = c.execute(
        "SELECT COUNT(*) FROM translation_cache WHERE status='invalidated'"
    ).fetchone()[0]
    hash_rows = c.execute(
        "SELECT COUNT(*) FROM translation_cache WHERE constitution_hash IS NOT NULL"
    ).fetchone()[0] if _has_col(c, 'translation_cache', 'constitution_hash') else 0
    return {
        'active_total': active,
        'active_keep': keep,
        'cache_total': cache_total,
        'cache_invalidated': cache_inv,
        'cache_semantic': hash_rows,
    }


def apply_changes():
    c = conn()
    pre = current(c)
    assert pre['NO_PINYIN']['status'] == 'active', "NO_PINYIN không active?"
    changed = 0
    # NO_PINYIN restore text + desc
    cur = c.execute(
        "UPDATE translation_rules SET rule_text=?, description=?, updated_at=? WHERE rule_code='NO_PINYIN'",
        (NO_PINYIN_TXT, NO_PINYIN_DESC, datetime.now().isoformat()))
    changed += cur.rowcount
    # HANVIET_NAMES deactivate
    cur = c.execute(
        "UPDATE translation_rules SET is_active=0, description=?, updated_at=? WHERE rule_code='HANVIET_NAMES'",
        (HANVIET_NAMES_DESC, datetime.now().isoformat()))
    changed += cur.rowcount
    c.commit()

    # invalidate cache liên quan 2 rule (bỏ quyền truy cập row emitted từng rule)
    inv = 0
    if _has_col(c, 'translation_cache', 'selected_rule_codes'):
        from style_constitution import invalidate_cache_for_rule
        inv += invalidate_cache_for_rule(c, 'NO_PINYIN')
        inv += invalidate_cache_for_rule(c, 'HANVIET_NAMES')
    c.close()
    return changed, inv


def revert_changes():
    c = conn()
    cur = c.execute(
        "UPDATE translation_rules SET rule_text='_keep_', description='', updated_at=? WHERE rule_code='NO_PINYIN'",
        (datetime.now().isoformat(),))
    n1 = cur.rowcount
    cur = c.execute(
        "UPDATE translation_rules SET is_active=1, description='', updated_at=? WHERE rule_code='HANVIET_NAMES'",
        (datetime.now().isoformat(),))
    n2 = cur.rowcount
    c.commit()
    c.close()
    return n1 + n2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['stats', 'dry-run', 'apply', 'revert'])
    args = ap.parse_args()

    c = conn()
    st = stats(c)
    cur = current(c)
    c.close()

    print(f"[T177-D6] DB: {DB}")
    print(f"[T177-D6] active rules (status=active AND is_active=1): {st['active_total']}  | trong đó rule_text='_keep_': {st['active_keep']}")
    print(f"[T177-D6] cache: total={st['cache_total']} invalidated={st['cache_invalidated']} semantic={st['cache_semantic']}")
    for code, d in cur.items():
        print(f"[T177-D6] {code}: status={d['status']} is_active={d['is_active']} "
              f"desc={d['description']!r} text={(d['rule_text'] or '')[:50]!r}")

    if args.mode == 'stats':
        print("\n[OK] --stats done. Không thay đổi gì.")
        return 0

    if args.mode == 'dry-run':
        print("\n[DRY-RUN] sẽ thực hiện:")
        print("  UPDATE NO_PINYIN     → rule_text restored (seed T73) + description='Cấm tuyệt đối dùng pinyin'")
        print("  UPDATE HANVIET_NAMES → is_active=0 + description note DEACTIVATED")
        print("  invalidate_cache_for_rule('NO_PINYIN') + ('HANVIET_NAMES')")
        print("  backup tự động: data/backups/lineage_t177_d6_fix_<ts>.db")
        print("\n[DRY-RUN] kết thúc — không commit, không backup.")
        return 0

    if args.mode == 'apply':
        BACKUP_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        bkp = BACKUP_DIR / f"lineage_t177_d6_fix_{ts}.db"
        shutil.copy2(str(DB), str(bkp))
        print(f"[BACKUP] {bkp} ({bkp.stat().st_size / 1024 / 1024:.1f} MB)")
        changed, inv = apply_changes()
        print(f"[APPLY] updated {changed} rule row; invalidated {inv} cache row")
        print("[OK] --apply xong. ROLLBACK row khuyến nghị: docs/ROLLBACK.md (T177 D6).")
        return 0

    if args.mode == 'revert':
        n = revert_changes()
        print(f"[REVERT] đã phục hồi {n} row về trạng thái trước apply "
              "(NO_PINYIN='_keep_', HANVIET_NAMES is_active=1, desc rỗng)")
        print("[NOTE] cache đã invalidated vẫn giữ invalidated — muốn lấy bản dịch cũ → restore backup pre-apply.")
        return 0


if __name__ == '__main__':
    sys.exit(main())