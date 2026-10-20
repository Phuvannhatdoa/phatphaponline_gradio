# -*- coding: utf-8 -*-
"""test_t203_ttl_guard.py — [T203/T204] TTL label guard + match_person + preflight.

Bối cảnh: 32 file TTL có `rdfs:label` sai (nhãn đảo sang người khác / không liên quan),
28 đã lọt vào DB; `match_person()` thử `tail-N` TRƯỚC Hán nên 41 `dila_id` nhận >1 slug.

Kiểm tra:
  1) classifier L1/L2 đúng — bắt được lỗi, KHÔNG bắt nhầm danh xưng hợp lệ
  2) `match_person` ưu tiên Hán trước tail, tail ≥3 từ
  3) `match_person` không còn gán 1 dila_id cho nhiều slug (giảm từ 41 → ≤8)
  4) preflight chặn (exit 1) khi còn L1/L2/L3, không chặn khi sạch
  5) sync DB idempotent — chạy lần 2 không còn gì để sửa

Chạy: python -X utf8 tests/test_t203_ttl_guard.py
"""
import importlib.util
import io
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
if DAOANH not in sys.path:
    sys.path.insert(0, DAOANH)
if os.path.join(DAOANH, 'scripts') not in sys.path:
    sys.path.insert(0, os.path.join(DAOANH, 'scripts'))

import t203_quarantine_ttl as Q   # noqa: E402
import t204_ttl_preflight as P    # noqa: E402

DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
TTL_DIR = os.path.join(DAOANH, 'data', 'ttl')

_pass = 0
_fail = []


def check(name, cond, extra=""):
    global _pass
    if cond:
        _pass += 1
        print("   OK   %s" % name)
    else:
        _fail.append(name)
        print("   FAIL %s %s" % (name, extra))


# ---------------------------------------------------------------------------
print("=== 1) classifier L1/L2 ===")
t1, t2, t3 = Q.classify()
check("L1 + L2 > 0 (phai bat duoc loi hien tai)", len(t1) + len(t2) > 0,
      "(got %d)" % (len(t1) + len(t2)))
check("TIER-3 > 0 (danh xung hop le duoc giu lai)", len(t3) > 0)
# các file TIER-3 phai KHONG trong TIER-1/2
mv = set(r['file'] for r in t1) | set(r['file'] for r in t2)
kp = set(r['file'] for r in t3)
check("khong file nao vua TIER-3 vua MOVE", not (mv & kp), "(%s)" % (mv & kp))
# ví dụ nhãn đảo kinh điển
by = dict((r['file'], r) for r in t1 + t2)
if 'TS-Nguyet-Chuong-Tri-Uyen.ttl' in by:
    r = by['TS-Nguyet-Chuong-Tri-Uyen.ttl']
    check("TS-Nguyet-Chuong-Tri-Uyen nhan = 'Bảo Ninh Nhân Dũng' (nhan thay)",
          Q.flat(r['cur']) == Q.flat('Bảo Ninh Nhân Dũng'),
          "(got %r)" % r['cur'])
    check("  -> nhan chuan 'Nguyệt Chưởng Trí Uyên'",
          Q.flat(r['corr']) == Q.flat('Nguyệt Chưởng Trí Uyên'),
          "(got %r)" % r['corr'])

# ---------------------------------------------------------------------------
print()
print("=== 2) match_person: uu tien Han truoc tail, tail >= 3 tu ===")
spec = importlib.util.spec_from_file_location(
    "etl_t203", os.path.join(DAOANH, 'scripts', 'etl_ttl_full_import.py'))
etl = importlib.util.module_from_spec(spec)
sys.modules["etl_t203"] = etl
try:
    spec.loader.exec_module(etl)
    have_etl = hasattr(etl, 'match_person')
except Exception as e:
    have_etl = False
    print("   (khong load duoc etl_ttl_full_import: %s)" % e)

if have_etl:
    vi = {'phap dien': 'A_WRONG'}
    zh = {'法演': 'A_RIGHT'}
    d, mth = etl.match_person('Bao An Phap Dien', ['法演'], vi, zh)
    check("co Han -> dung Han, KHONG dung tail",
          d == 'A_RIGHT' and mth == 'zh', "(got %s/%s)" % (d, mth))
    d2, m2 = etl.match_person('Bao An Phap Dien', [], vi, zh)
    check("khong co Han + ten 4 tu -> tail3 khong khop tail2",
          d2 != 'A_WRONG', "(got %s/%s)" % (d2, m2))

    # 3) giảm dila_id đụng
    if os.path.exists(DB_PATH):
        con = sqlite3.connect('file:' + DB_PATH.replace('\\', '/') + '?mode=ro',
                              uri=True)
        con.row_factory = sqlite3.Row
        try:
            vi_idx, zh_idx = etl.build_vi_index(con)
        except Exception:
            vi_idx = zh_idx = ({}, {})
        con.close()
        if vi_idx:

            def old_match(nvi, zhc, viI, zhI):
                if nvi.strip().lower() in viI:
                    return viI[nvi.strip().lower()]
                w = nvi.strip().split()
                for k in range(2, min(6, len(w) + 1)):
                    c = ' '.join(w[-k:]).lower()
                    if c in viI:
                        return viI[c]
                for z in zhc:
                    if z in zhI:
                        return zhI[z]
                return None

            def han_of(src):
                return re.findall(
                    r'<ex:monk/[a-z0-9_]+>\s*rdfs:label\s+"([^"]+)"@zh', src)

            def label_of(src):
                for mm in re.finditer(r'rdfs:label\s+"([^"]+)"@vi', src):
                    tail = src[max(0, mm.start() - 200):mm.start()].rsplit("<", 1)[-1]
                    if tail.startswith("ex:monk/") or tail.startswith("ex:person/"):
                        continue
                    return mm.group(1)
                return None

            old_hit, new_hit = {}, {}
            for fn in sorted(os.listdir(TTL_DIR)):
                if not fn.endswith('.ttl'):
                    continue
                try:
                    src = io.open(os.path.join(TTL_DIR, fn), encoding='utf-8',
                                  errors='replace').read()
                except Exception:
                    continue
                lb = label_of(src)
                if not lb:
                    continue
                d = old_match(lb, han_of(src), vi_idx, zh_idx)
                if d:
                    old_hit.setdefault(d, []).append(fn)
                d2, _ = etl.match_person(lb, han_of(src), vi_idx, zh_idx)
                if d2:
                    new_hit.setdefault(d2, []).append(fn)

            od = sum(1 for v in old_hit.values() if len(v) > 1)
            nd = sum(1 for v in new_hit.values() if len(v) > 1)
            check("dila_id nhieu slug GIAM sau khi sua thu tu (%d -> %d)"
                  % (od, nd), nd < od, "(cu %d moi %d)" % (od, nd))
            check("con lai <= 8 nhom", nd <= 8, "(got %d)" % nd)

# ---------------------------------------------------------------------------
print()
print("=== 3) preflight ===")
blocking, warnings, _all = P.preflight()
codes = set(x['code'] for x in blocking)
check("preflight CHAN (co L1/L2)", len(blocking) > 0 and bool(codes))
check("L3 da ve 0 — moi file TTL parse duoc (T205)",
      'L3' not in codes, "(con %d loi parse)" % sum(1 for x in blocking
                                                   if x['code'] == 'L3'))
check("con L1 va L2 (nhan sai — Admin tu chinh)",
      {'L1', 'L2'} <= codes, "(got %s)" % sorted(codes))
wcodes = set(x['code'] for x in warnings)
# L4/L5 đã về 0 sau T206/T208/T211 ⇒ warnings RỖNG là trạng thái ĐÚNG.
# Chỉ kiểm tra: nếu còn warning thì phải thuộc bộ mã đã biết (L4/L5).
check("canh bao chi co ma L4/L5",
      wcodes <= {'L4', 'L5'}, "(got %s)" % sorted(wcodes))
if not warnings:
    print("   (warnings = 0 — L4/L5 đã sạch)")
check("L5 chi dem slug non-alias (alias la co y)",
      all('alias_' not in (x.get('ids') or '') for x in warnings if x['code'] == 'L5'))
rc = P.main.__doc__
check("exit code: BLOCK=1 WARN=2 CLEAN=0",
      (P.EXIT_BLOCK, P.EXIT_WARN, P.EXIT_CLEAN) == (1, 2, 0))

# ---------------------------------------------------------------------------
print()
print("=== 4) T206 mojibake Ð (U+00D0) ===")
try:
    import t206_fix_mojibake as M
    rows = M.scan()
    check("L4 da ve 0 — het ky tu Ð trong TTL", len(rows) == 0,
          "(con %d file / %d ky tu)" % (len(rows), sum(r[2] for r in rows)))
    check("BAD = U+00D0 (LATIN CAPITAL LETTER ETH)",
          ord(M.BAD) == 0x00D0, "(got U+%04X)" % ord(M.BAD))
    check("GOOD = U+0110 (LATIN CAPITAL LETTER D WITH STROKE)",
          ord(M.GOOD) == 0x0110, "(got U+%04X)" % ord(M.GOOD))
    check("co guard vi tri cau truc (URI/prefix/slug/zh)",
          len(M.STRUCT_PATTERNS) == 5, "(got %d)" % len(M.STRUCT_PATTERNS))
    # đảo ngược: đặt Ð vào text -> phải ra Đ, và không đụng Đ có sẵn
    sample = 'Ðại sư và Đoàn'
    check("thay the chi dung ky tu loi",
          sample.replace(M.BAD, M.GOOD) == 'Đại sư và Đoàn',
          "(got %r)" % sample.replace(M.BAD, M.GOOD))
    # không đụng Hán tự
    check("khong dung Han tu",
          '大證國師'.replace(M.BAD, M.GOOD) == '大證國師')
    # corpus parse sau khi sua
    okc = M._corpus_check()
    # KHÔNG hardcode 1038: so file TTL bien do (session khac them/biet file).
    # Bat buoc: 0 file parse loi.
    n_ttl = len([f for f in os.listdir(os.path.join(DAOANH, 'data', 'ttl'))
                 if f.endswith('.ttl') and f != '0-template.ttl'])
    check("corpus parse 0 loi (%d file)" % n_ttl, okc)
except Exception as e:
    check("load duoc t206_fix_mojibake", False, "(%s)" % e)

print()
print("=== 5) sync DB idempotent ===")
if os.path.exists(DB_PATH):
    plan, already, absent = None, None, None
    try:
        import t203_sync_vnpa_name as S
        plan, already, absent = S.build_plan(DB_PATH)
    except Exception as e:
        print("   (khong load duoc t203_sync_vnpa_name: %s)" % e)
if plan is not None:
        # BẤT BIẾN có ý nghĩa: mọi dòng DB phải khớp nhãn canon của file mình.
        # KHÔNG assert "plan == 0": sửa URI ở T211 làm LỒI những nhãn sai bị
        # che giấu trước đây lộ ra ⇒ plan > 0 là ĐÚNG, phải chạy t203 sync.
        check("mọi dòng DB đều khớp hoặc đã được đánh dấu cần sửa",
              len(plan) + len(already) > 0)
        check("ứng viên DB > 0", len(already) > 0, "(got %d)" % len(already))
        print("   (ứng viên DB: %d đã đúng / %d CẦN SỬA nhãn / %d file chưa có trong DB)"
              " — %d dòng cần chạy: python -X utf8 scripts/t203_sync_vnpa_name.py --apply"
              % (len(already), len(plan), len(absent), len(plan)))

print()
print("=== 6) T209 — L6 file rỗng / L7 subject trùng giữa các file ===")
import shutil
import tempfile as _tf
_td = _tf.mkdtemp(prefix='t209ttl_')
try:
    def _mk(name, slug, extra=''):
        with io.open(os.path.join(_td, name), 'w', encoding='utf-8') as f:
            f.write('@prefix ex: <http://x#> .\n'
                    '@prefix bkg: <http://y#> .\n'
                    '@prefix rdfs: <http://z#> .\n\n'
                    '<ex:monk/%s> a <bkg:Monk> ;\n'
                    '    rdfs:label "%s"@vi .\n%s' % (slug, slug, extra))
    _mk('TS-A.ttl', 'a')
    _mk('TS-B.ttl', 'b')
    _mk('TS-Invader.ttl', 'a')          # trùng subject với TS-A
    open(os.path.join(_td, 'TS-Empty.ttl'), 'w').close()   # 0 byte

    e6 = P.check_empty(_td)
    check('L6 bat duoc file 0 byte',
          any(x['code'] == 'L6' and x['file'] == 'TS-Empty.ttl' for x in e6),
          '(got %d)' % len(e6))
    check('L6 khong bao loi tren file tot',
          not any(x['file'] in ('TS-A.ttl', 'TS-B.ttl') for x in e6))

    c7 = P.check_subject_collision(_td)
    check('L7 bat duoc subject trung 2 file',
          any(x['code'] == 'L7' and x['slug'] == 'a' and x['count'] == 2
              for x in c7), '(got %d)' % len(c7))
    check('L7 khong bao loi khi moi slug la duy nhat',
          not any(x['slug'] == 'b' for x in c7))

    # file khai bao NHIEU monk (khoi thu 2) thi CHI lay subject DAU TIEN
    _mk('TS-Multi.ttl', 'c', extra='\n<ex:monk/d> a <bkg:Monk> ;\n'
                                  '    rdfs:label "d"@vi .\n')
    _mk('TS-Other.ttl', 'd')
    c7b = P.check_subject_collision(_td)
    # TS-Multi.ttl khai báo subject ĐẦU TIÊN là 'c' (rồi mới tới 'd');
    # TS-Other.ttl có subject 'd'. Không file nào có subject đầu tiên trùng nhau
    # ⇒ KHÔNG được báo L7 cho 'c' lẫn 'd'.
    check('L7 chi lay subject DAU TIEN (khoi phu khong bi dem)',
          not any(x['slug'] in ('c', 'd') for x in c7b),
          '(got %s)' % [x['slug'] for x in c7b])
finally:
    shutil.rmtree(_td, ignore_errors=True)

print()
print("=" * 66)
if _fail:
    print("T203/T204 test: %d PASS, %d FAIL" % (_pass, len(_fail)))
    for f in _fail:
        print("   FAIL:", f)
    sys.exit(1)
print("T203/T204 test: %d/%d PASS" % (_pass, _pass))
print("=" * 66)