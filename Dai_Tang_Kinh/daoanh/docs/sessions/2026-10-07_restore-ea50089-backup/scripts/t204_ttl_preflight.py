# -*- coding: utf-8 -*-
"""t204_ttl_preflight.py — [T203/T204] CỔNG CHẶN TTL trước khi ETL nạp vào DB.

MỤC ĐÍCH
--------
Khi Admin cập nhật file TTL, các lỗi sau phải bị **phát hiện TRƯỚC** khi nạp, không
để tới lúc DB đã bẩn:

  L1  Nhãn đảo   — `rdfs:label` của file trùng tên MỘT NGƯỜI KHÁC mà file khai báo
                  (thầy/trò) ⇒ nhãn bị đảo sang người khác.
  L2  Nhãn lệch  — `rdfs:label` không liên quan tới nhãn chuẩn trong corpus.
  L3  File hỏng  — rdflib KHÔNG parse được ⇒ ETL hiện **bỏ qua im lặng** ⇒ vị đó
                  chưa từng vào DB mà không ai biết.
  L4  Mojibake   — chứa `Ð` (U+00D0) thay cho `Đ` (U+0110) ⇒ làm nhiễu so khớp tên.
  L5  Đụng ID    — >1 slug (không phải `alias_*`) cùng `dila_id` trong DB.

Exit code: 0 = sạch · 1 = có LỌC (L1/L2/L3 — **chặn import**) · 2 = có CẢNH BÁO
(L4/L5 — không chặn nhưng báo).

Dùng như module (`preflight()`) hoặc CLI.

Usage:
    python -X utf8 scripts/t204_ttl_preflight.py --report
    python -X utf8 scripts/t204_ttl_preflight.py --strict   # L4/L5 cũng FAIL
"""
import argparse
import os
import sys
import unicodedata
from collections import defaultdict

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
TTL_DIR = os.path.join(DAOANH, 'data', 'ttl')
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')

EXIT_CLEAN, EXIT_BLOCK, EXIT_WARN = 0, 1, 2


def _flat(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = (s.replace("Ð", "D").replace("đ", "d").replace("Đ", "D")
          .replace("_", " "))
    s = "".join(c if c.isalnum() or c.isspace() else " " for c in s.lower())
    return " ".join(s.split())


def _key(fn):
    """Slug chuẩn để tra index.

    ⚠ PHẢI giữ dấu `_`: index được dựng từ `<ex:monk/nguyet_chuong_tri_uyen>` (có `_`),
    còn tên file là `TS-Nguyet-Chuong-Tri-Uyen` (có `-`). Nếu flatten hai bên theo
    kiểu khác nhau sẽ không khớp ⇒ âm thầm bỏ sót mọi lỗi.
    """
    import re
    stem = fn[:-4] if fn.lower().endswith('.ttl') else fn
    return re.sub(r"^(TS|Cs|Bo-Tat)-", "", stem, flags=re.I).replace('-', '_').lower()


def _read(p):
    import io
    return io.open(p, encoding='utf-8', errors='replace').read()


def _own_label(src):
    import re
    for m in re.finditer(r'rdfs:label\s+"([^"]+)"@vi', src):
        tail = src[max(0, m.start() - 200):m.start()].rsplit("<", 1)[-1]
        if tail.startswith("ex:monk/") or tail.startswith("ex:person/"):
            continue
        return m.group(1)
    return None


def check_labels(ttl_dir=TTL_DIR):
    """L1 + L2 — so `rdfs:label` của file với nhãn chuẩn trong corpus.

    ⚠ DÙNG CHUNG classifier với `t203_quarantine_ttl.classify()` (nguồn sự thật
    duy nhất) để L1/L2 ở đây và danh sách quarantine của T203 **không lệch nhau**.
    Nếu tự viết lại logic so khớp, rất dễ lệch (tiền tố hợp lệ `Cư Sĩ …`,
    `Am Chủ …` sẽ bị gắn cờ nhầm là lỗi).
    """
    try:
        import t203_quarantine_ttl as _q
    except ImportError:
        return []
    # [T222] Pass ttl_dir through so classify() only checks files in managed scope.
    t1, t2, _t3 = _q.classify(ttl_dir=ttl_dir)
    out = []
    for r, code in ([(x, 'L1') for x in t1] + [(x, 'L2') for x in t2]):
        out.append({'code': code, 'file': r['file'], 'current': r['cur'],
                    'expected': r['corr'], 'evidence': r['evidence'],
                    'msg': r['why']})
    return out


def check_empty(ttl_dir=TTL_DIR):
    """L6 — file TTL RỖNG (0 byte) hoặc không có triple nào.

    Bắt buộc: TTL KHÔNG git track ⇒ file bị xoá rỗng là MẤT DỮ LIỆU THẬT mà
    `git status`/`git revert` không thấy. Đã xảy ra 1 lần (2026-10-02):
    `TS-Dai-Xa-Nhu-Truong.ttl` còn 0 byte, chỉ khôi phục được nhờ backup file-level
    của T205. Nên phải CHẶN ETL trước khi nạp.
    """
    bad = []
    for fn in sorted(f for f in os.listdir(ttl_dir) if f.endswith('.ttl')):
        if fn == '0-template.ttl':
            continue
        p = os.path.join(ttl_dir, fn)
        size = os.path.getsize(p)
        if size == 0:
            bad.append({'code': 'L6', 'file': fn, 'size': 0,
                        'msg': 'file RỖNG (0 byte) — mất dữ liệu, TTL không git track'})
            continue
        # file chỉ toàn comment/dòng trắng => không có triple nào
        try:
            import rdflib
            g = rdflib.Graph()
            g.parse(p, format='turtle')
            if len(g) == 0:
                bad.append({'code': 'L6', 'file': fn, 'size': size,
                            'msg': 'file parse được nhưng KHÔNG có triple nào'})
        except Exception:
            pass          # đã L3 bắt
    return bad


def check_subject_collision(ttl_dir=TTL_DIR):
    """L7 — cùng một subject URI `ex:monk/X` xuất hiện ở NHIỀU file.

    Ghi đè lẫn nhau nên chỉ file cuối được nạp, các file kia **mất im lặng**.
    Ví dụ thật (2026-10-02): `TS-Tuyet-Giau-Chon-Phac.ttl` (gen 69),
    `TS-Dai-Xa-Nhu-Truong.ttl` (gen 70), `TS-Minh-Hoang-Tu-Dung.ttl` (gen 71)
    đều dùng subject `ex:monk/phong_huyet_dien_chieu` ⇒ DB chỉ có 1 row,
    2 file kia không bao giờ được nạp.
    """
    import re as _re
    own = _re.compile(
        r'^\s*<ex:(?:monk|person)/([\w\-]+)>\s+a\s+<bkg:Monk>', _re.M)
    where = {}
    for fn in sorted(f for f in os.listdir(ttl_dir) if f.endswith('.ttl')):
        if fn == '0-template.ttl':
            continue
        src = _read(os.path.join(ttl_dir, fn))
        # CHỈ lấy khai báo ĐẦU TIÊN = subject chính của file.
        # Một file có thể khai báo thêm nhiều monk khác (ví dụ khối CSV thứ hai
        # do T205 gặp) — đó KHÔNG phải chủ đề của file, tính vào sẽ báo sai.
        m = own.search(src)
        if m:
            where.setdefault(m.group(1), []).append(fn)
    bad = []
    for slug, files in sorted(where.items()):
        if len(files) > 1:
            bad.append({'code': 'L7', 'slug': slug, 'count': len(files),
                        'files': ', '.join(files),
                        'msg': 'subject ex:monk/%s xuất hiện ở %d file — ghi đè lẫn nhau, chỉ file cuối được nạp'
                               % (slug, len(files))})
    return bad


def check_parse(ttl_dir=TTL_DIR):
    """L3 — file rdflib không parse được."""
    try:
        import rdflib
    except Exception:
        return None
    bad = []
    for fn in sorted(f for f in os.listdir(ttl_dir) if f.endswith('.ttl')):
        if fn == '0-template.ttl':
            continue
        try:
            g = rdflib.Graph()
            g.parse(os.path.join(ttl_dir, fn), format='turtle')
        except Exception as e:
            bad.append({'code': 'L3', 'file': fn,
                        'msg': 'rdflib không parse được: %s' % str(e)[:80]})
    return bad


def check_mojibake(ttl_dir=TTL_DIR):
    """L4 — chứa Ð (U+00D0) thay Đ (U+0110)."""
    bad = []
    for fn in sorted(f for f in os.listdir(ttl_dir) if f.endswith('.ttl')):
        try:
            src = _read(os.path.join(ttl_dir, fn))
        except Exception:
            continue
        n = src.count('Ð')
        if n:
            bad.append({'code': 'L4', 'file': fn, 'count': n,
                        'msg': '%d ký tự Ð (U+00D0) thay cho Đ (U+0110)' % n})
    return bad


def check_dila_collision(db_path=DB_PATH):
    """L5 — >1 slug non-alias cùng dila_id trong DB."""
    import sqlite3
    if not os.path.exists(db_path):
        return []
    try:
        con = sqlite3.connect('file:' + db_path.replace('\\', '/') + '?mode=ro',
                              uri=True)
    except Exception:
        return []
    try:
        rows = con.execute(
            "SELECT dila_id, COUNT(*), GROUP_CONCAT(id) "
            "FROM vn_person_authority "
            "WHERE dila_id IS NOT NULL AND dila_id <> '' AND id NOT LIKE 'alias_%' "
            "GROUP BY dila_id HAVING COUNT(*) > 1").fetchall()
    except sqlite3.Error:
        return []
    finally:
        con.close()
    return [{'code': 'L5', 'dila_id': r[0], 'count': r[1], 'ids': r[2],
             'msg': '%d slug non-alias cùng dila_id' % r[1]} for r in rows]


def preflight(ttl_dir=TTL_DIR, db_path=DB_PATH, strict=False):
    """Trả (blocking, warnings, all_findings)."""
    blocking = check_labels(ttl_dir)
    parsed = check_parse(ttl_dir)
    if parsed:
        blocking = blocking + parsed
    # L6 file rỗng + L7 subject trùng giữa các file — CẢ HAI đều gây MẤT DỮ LIỆU
    # nên chặn (blocking), không phải cảnh báo.
    empty = check_empty(ttl_dir)
    if empty:
        blocking = blocking + empty
    collide = check_subject_collision(ttl_dir)
    if collide:
        blocking = blocking + collide
    warnings = check_mojibake(ttl_dir) + check_dila_collision(db_path)
    if strict:
        return (blocking + warnings, [], blocking + warnings)
    return (blocking, warnings, blocking + warnings)


def _print(findings, title):
    if not findings:
        print('  [%s] OK — 0' % title)
        return
    print('  [%s] %d' % (title, len(findings)))
    for f in findings[:60]:
        if f['code'] == 'L5':
            print('      L5 dila_id=%s n=%d ids=%s'
                  % (f['dila_id'], f['count'], (f['ids'] or '')[:70]))
        elif f['code'] == 'L4':
            print('      L4 %-34s %s' % (f['file'], f['msg']))
        elif f['code'] == 'L6':
            print('      L6 %-34s %s' % (f['file'], f['msg']))
        elif f['code'] == 'L7':
            print('      L7 ex:monk/%-24s %s' % (f['slug'], f['files']))
        else:
            print('      %s %-34s %s' % (f['code'], f['file'], f['msg']))
            if 'current' in f:
                print('           hiện tại: %r' % f['current'])
                print('           chuẩn   : %r  (x%d nguồn)'
                      % (f['expected'], f['evidence']))
    if len(findings) > 60:
        print('      … còn %d' % (len(findings) - 60))


def main():
    p = argparse.ArgumentParser(description='TTL preflight — chặn lỗi trước khi ETL nạp')
    p.add_argument('--report', action='store_true', help='in báo cáo đầy đủ')
    p.add_argument('--strict', action='store_true',
                   help='coi L4/L5 cũng là lỗi chặn (exit 1)')
    p.add_argument('--quiet', action='store_true')
    p.add_argument('--ttl-dir', default=TTL_DIR)
    p.add_argument('--db-path', default=DB_PATH)
    args = p.parse_args()

    blocking, warnings, _ = preflight(args.ttl_dir, args.db_path, args.strict)
    if not args.quiet:
        print('=' * 78)
        print('TTL PREFLIGHT — %s' % args.ttl_dir)
        print('=' * 78)
        print('[CHẶN IMPORT]')
        _print(blocking, 'L1/L2/L3')
        print('[CẢNH BÁO]')
        _print(warnings, 'L4/L5')
        print('=' * 78)
        print('  L1 nhãn đảo · L2 nhãn lệch · L3 file hỏng (rdflib)')
        print('  L4 mojibake Ð/Đ · L5 dila_id đụng')
        print('=' * 78)
    if blocking:
        return EXIT_BLOCK
    if warnings:
        return EXIT_WARN
    return EXIT_CLEAN


if __name__ == '__main__':
    sys.exit(main())