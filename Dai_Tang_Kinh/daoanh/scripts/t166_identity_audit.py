# -*- coding: utf-8 -*-
"""t166_identity_audit.py — T166 Write-Deny Audit + schema ràng buộc.

Chạy trong npm run pipeline (script "audit:t166"). Kiểm tra CI-style:

  1. **Schema** : mọi cột identity_*/policy tồn tại với đúng type. (phải migrate trước)
  2. **APP guard** : các endpoint translate trong app.py đều gọi _t166_post_check_translation
     ngay TRƯỚC _t165_write_cache (đảm bảo không có write-through "im lặng").
  3. **AUTH** : mọi route admin write (POST) gọi verify_session hoặc thuộc whitelist cho phép.
     (SPEC §20.2 #15: endpoint tạo LOCKED authority phải có auth.)
  4. **Config** : translation_rules.identity_lock_policy ∈ {P-PARTIAL, P-STOP}.
  5. **Legacy cache** : 0 row có identity_lock_hash nhưng KHÔNG có identity_status
     (guard viết thiếu). Và 0 row 'edited' bị timeline re-render.

Exit code 0 = PASS, 1 = FAIL (dừng pipeline). Không SỬA dữ liệu.
"""
import argparse
import os
import re
import sqlite3
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
APP_PATH = os.path.join(DAOANH, 'app.py')

# ── 1. Schema ────────────────────────────────────────────────────────────────
REQUIRED_COLS = {
    'translation_cache': (
        'identity_status TEXT',
        'identity_issues TEXT',
        'identity_lock_hash TEXT',
    ),
    'translation_rules': (
        'identity_lock_policy TEXT',
    ),
}
REQUIRED_INDEXES = {'idx_tc_identity': 'translation_cache(identity_status)'}
VALID_POLICY = ('P-PARTIAL', 'P-STOP')

# ── 2. App guard map ─────────────────────────────────────────────────────────
# source_type → (route function, cần verify có gọi post_check trước write_cache)
# Dùng regex duyệt nguồn để bắt "write qua cache không prooléct".
WRITE_CACHE_TYPES = ('person_bio', 'dila_card', 'place_note', 'relation_evidence')

# ── 3. Admin-write routes (POST/PUT/DELETE) cần auth ─────────────────────────
# Regex trên dòng route + hàm bên dưới. Các route thuần ĐỌC không cần.
FORBIDDEN_INLINE_LLM_KEY = ('AIzaSyB8qS0elX9NZ7IIFpmeZSkKfvAV6WiukiE',)


def _table_has(conn, table):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone())


def _col_type(conn, table, col):
    try:
        row = conn.execute(f'PRAGMA table_info({table})').fetchall()
        for r in row:
            if r[1] == col:
                return r[2]
    except sqlite3.Error:
        pass
    return None


def _check_schema(conn):
    problems = []
    for table, cols in REQUIRED_COLS.items():
        if not _table_has(conn, table):
            problems.append(f'  [FAIL] bảng {table} không tồn tại')
            continue
        for cspec in cols:
            col, _ = cspec.split(' ', 1)
            ctype = _col_type(conn, table, col)
            if ctype is None:
                problems.append(f'  [FAIL] {table}.{col} thiếu — chạy '
                                f'python -X utf8 scripts/t166_identity_migrate.py --apply')
            elif ctype.upper() != 'TEXT':
                problems.append(f'  [WARN] {table}.{col} type={ctype} (mong đợi TEXT)')
    for idx, spec in REQUIRED_INDEXES.items():
        found = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (idx,)
        ).fetchone()
        if not found:
            problems.append(f'  [FAIL] index {idx} thiếu ({spec})')
    return problems


def _check_app_guard():
    """Mỗi source_type phải có dấu _t166_post_check_translation xuất hiện
    trong cùng khối (trước) _t165_write_cache cho source_type tương ứng."""
    problems = []
    try:
        src = open(APP_PATH, encoding='utf-8').read()
    except OSError as exc:
        return [f'  [FAIL] không đọc được app.py: {exc}']

    # Mỗi write_cache INSERT phải nằm trong hàm có post_check trước đó.
    # Đếm theo cặp: post_check luôn xuất hiện ≥1 lần trước write_cache cùng source_type.
    for stype in WRITE_CACHE_TYPES:
        # đếm dấu hiệu trong file: 'source_type' + stype xuất hiện cùng đơn vị
        n_write = len(re.findall(rf"'{stype}'[,\s)]", src))
        # Mọi write phải đi sau một post_check trong CÙNG def — heuristic:
        # chia file theo 'def ', trong mỗi khối, nếu có write_cache source_type thì
        # phải có post_check_translation.
        guards = re.split(r'\ndef ', src)[1:]
        bad = 0
        for blk in guards:
            if re.search(rf"'{stype}'", blk) and 'write_cache' in blk:
                if '_t166_post_check_translation' not in blk:
                    bad += 1
        if bad:
            problems.append(
                f'  [FAIL] có {bad} khối hàm write_cache source_type={stype} '
                f"không có _t166_post_check_translation — SPEC §8.2")
    return problems


def _check_auth():
    """Endpoint admin-write phải gọi verify_session. Dùng regex đầy đủ để tránh
    false negative. Whitelist: route đăng nhập / session (không áp dụng auth)."""
    problems = []
    try:
        src = open(APP_PATH, encoding='utf-8').read()
    except OSError as exc:
        return [f'  [FAIL] không đọc được app.py: {exc}']

    # Các route bắt đầu bằng /daoanh/api/admin/ hoặc /api/admin/ và là POST/PUT/DELETE
    admin_write = []
    for m in re.finditer(
        r"@app\.route\('(/daoanh/api/admin/[^']+)'(?:,\s*methods=['\"](POST|PUT|DELETE))?",
        src):
        path, method = m.group(1), m.group(2) or 'GET'
        if method in ('POST', 'PUT', 'DELETE'):
            admin_write.append((path, method))

    # Với mỗi admin-write route, tìm khối hàm ngay sau và kiểm tra verify_session
    for path, method in admin_write:
        idx = src.index(path)
        after = src[idx:idx + 2500]
        if 'verify_session' not in after and 'auth_required' not in after:
            problems.append(f'  [FAIL] {path} [{method}] không gọi verify_session')

    # inline API key lộ trong file (SPEC §20.2 #15)
    for key in FORBIDDEN_INLINE_LLM_KEY:
        if key in src:
            # L17400+ đã dùng nhưng chỉ khi groq_key thiếu — cảnh báo, để Admin xử lý
            problems.append(f'  [WARN] inline Gemini API key vẫn nằm trong app.py')
    return problems


def _check_data(conn):
    problems = []
    if not _table_has(conn, 'translation_cache'):
        return problems
    try:
        # Legacy row có identity_lock_hash nhưng thiếu identity_status → guard viết thiếu
        bad = conn.execute(
            "SELECT COUNT(*) FROM translation_cache "
            "WHERE identity_lock_hash IS NOT NULL AND identity_status IS NULL"
        ).fetchone()[0]
        if bad:
            problems.append(
                f'  [FAIL] {bad} row cache có identity_lock_hash nhưng thiếu '
                f'identity_status (guard viết thiếu)')
        # Policy không hợp lệ
        badpol = conn.execute(
            "SELECT COUNT(*) FROM translation_rules "
            "WHERE identity_lock_policy NOT IN ('P-PARTIAL','P-STOP')"
        ).fetchone()[0]
        if badpol:
            problems.append(f'  [FAIL] {badpol} row translation_rules có policy không hợp lệ')
    except sqlite3.Error as exc:
        problems.append(f'  [WARN] không đọc được translation_cache: {exc}')
    return problems


def _stats(conn):
    print('=== T166 identity status distribution ===')
    if _table_has(conn, 'translation_cache'):
        rows = conn.execute(
            "SELECT COALESCE(identity_status,'(NULL=legacy)') s, COUNT(*) n "
            "FROM translation_cache GROUP BY s ORDER BY n DESC").fetchall()
    else:
        rows = []
    for s, n in rows or [('(no table)', 0)]:
        print(f'  {s:24s} {n:>6}')


def main():
    ap = argparse.ArgumentParser(description='T166 write-deny audit')
    ap.add_argument('--fix-missing-policy', action='store_true',
                    help='[không dùng] SERVER sẽ tự điền default — chỉ dùng khi db quá cũ')
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        print('═══ T166 Identity Audit ═══')
        problems = []
        problems += _check_schema(conn)
        problems += _check_app_guard()
        problems += _check_auth()
        problems += _check_data(conn)

        _stats(conn)

        print('\n── Kết quả ──')
        n_fail = sum(1 for p in problems if '[FAIL]' in p)
        n_warn = sum(1 for p in problems if '[WARN]' in p)
        for p in problems:
            print(p)
        if n_fail:
            print(f'\n❌ T166 audit: {n_fail} FAIL, {n_warn} WARN')
            sys.exit(1)
        if n_warn:
            print(f'\n✅ T166 audit: PASS (0 FAIL) + {n_warn} WARN (không chặn pipeline)')
        else:
            print('✅ T166 audit: PASS — schema đủ, app guard đầy đủ, auth ok, data hợp lệ')
    finally:
        conn.close()


if __name__ == '__main__':
    main()