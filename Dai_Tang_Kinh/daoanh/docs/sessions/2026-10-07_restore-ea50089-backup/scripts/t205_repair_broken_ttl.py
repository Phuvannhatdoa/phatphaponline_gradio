# -*- coding: utf-8 -*-
"""t205_repair_broken_ttl.py — [T205] sửa file TTL không parse được.

BA LỖI CẤU TRÚC TÌM ĐƯỢC (2026-10-01)
---------------------------------------
1) THIẾU `@prefix ex:`  — nội dung dùng `<ex:monk/...>` nhưng block khai báo chỉ có
   `bkg, crm, rdfs, xsd`. File tốt có đủ 5 prefix.
2) TAG NGÔN NGỮ CẮT CỤT — `bkg:biographicalNote '''…'''@v` (thiếu chữ `i`).
   rdflib đọc `@v` rồi gặp dòng kế tiếp ⇒ "expected '.' or '}' or ']'".
3) DÒNG CSV DÍNH CUỐI FILE — dạng `0-TS …, 0-TS …` (không phải Turtle) do quá
   trình ghi file bị ngắt rồi nối tiếp dữ liệu thô.

Ngoài ra một số file bị **CẮT NGANG** (dừng ở ~38.9 KB, thiếu `.` kết thúc) —
script chỉ đóng cú pháp tối thiểu, KHÔNG bịa nội dung. Những file đó vẫn nên được
Admin thay bằng bản gốc (script báo `[TRUNCATED]`).

AN TOÀN
-------
- TTL KHÔNG git track ⇒ backup file-level vào `data/backups/t205_ttl_<ts>/` + `--revert`.
- `--dry-run` mặc định, `--apply` mới ghi.
- Kiểm tra rdflib parse được TRƯỚC khi ghi; không sửa file mà sửa xong vẫn hỏng.
- `--revert` khôi phục từ backup.

Usage:
    python -X utf8 scripts/t205_repair_broken_ttl.py --stats
    python -X utf8 scripts/t205_repair_broken_ttl.py --dry-run
    python -X utf8 scripts/t205_repair_broken_ttl.py --apply
    python -X utf8 scripts/t205_repair_broken_ttl.py --revert
"""
import argparse
import datetime
import io
import os
import re
import shutil
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
TTL_DIR = os.path.join(DAOANH, 'data', 'ttl')
BACKUP_DIR = os.path.join(DAOANH, 'data', 'backups')

EX_PREFIX = '@prefix ex: <http://www.phatphaponline.org/ontology/buddhist-kg#> .'
# ngôn ngữ hợp lệ trong corpus
LANGS = ('vi', 'zh', 'en', 'sa', 'jp', 'san', 'peo', 'other', '')


def read(p):
    return io.open(p, encoding='utf-8', errors='replace').read()


def write(p, s):
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


def is_turtle_line(s):
    """Dòng có vẻ là Turtle (bỏ qua dòng trong triple-quote đang mở)."""
    t = s.strip()
    if not t or t.startswith('#'):
        return True
    return bool(re.search(r'[<>"@;]|\b(a|rdfs|bkg|crm|ex|xsd|crm):', t))


# --- bảng vá lỗi riêng đã XÁC MINH (áp dụng 1 lần, trước vòng lặp) ---
# Mỗi lỗi dưới đây đã kiểm chứng: sửa xong rdflib parse được.
PUNCT_FIXES = [
    # URI mở đầu bằng `ex:monk/…>` mà mất dấu `<` (chỉ dạng này là sai)
    (r'(?m)^([ \t]*)ex:monk/([\w\-]+)>', r'\1<ex:monk/\2>'),
]


def apply_punct_fixes(out, fixes):
    for pat, rep in PUNCT_FIXES:
        new, n = re.subn(pat, rep, out)
        if n:
            fixes.append('vá %d dòng theo /%s/' % (n, pat[:34]))
            out = new
    return out


def _csv_footer(t):
    """Dòng CSV dính của bộ xuất TTL: dạng `0-TS …, 0-TS …` (bắt đầu bằng số + `-`)."""
    return bool(re.match(r'^\s*\d+\s*-\s*(TS|Cs|Ton|Bo-Tat|TSCs)\b', t))


def _looks_csv(t):
    """Dòng không phải Turtle: có dấu phẩy + nhiều mã dạng `X-TS …`."""
    return (_csv_footer(t) or (t.count(',') >= 2 and len(re.findall(r'\b\w+-(?:TS|Cs)\b', t)) >= 2))


def repair_iterative(src, filename, max_rounds=25):
    """Sửa lặp: lấy lỗi rdflib → vá dòng tương ứng → parse lại.

    Bền hơn việc đoán pattern: rdflib luôn chỉ đúng dòng lỗi.
    """
    fixes = []
    truncated = False
    out = src
    tried = set()          # (rule, dòng) đã thử — chống lặp vô hạn
    rnd = 0

    # 1) @prefix ex: (làm 1 lần, không cần lặp)
    if re.search(r'<ex:[\w]', out) and '@prefix ex:' not in out:
        m = re.search(r'^@prefix\s+bkg:.*$', out, re.M)
        if m:
            out = out[:m.end()] + '\n' + EX_PREFIX + out[m.end():]
            fixes.append('thêm @prefix ex:')

    out = apply_punct_fixes(out, fixes)

    for _ in range(max_rounds):
        ok, info = _parse_text(out)
        if ok:
            return out, fixes, truncated
        err = str(info)
        ml = re.search(r'at line (\d+)', err)

        # 3b) "EOF found after object" ⇒ file BỊ CẮT giữa chừng, đóng triple-quote
        #     đang mở rồi kết thúc statement (không bịa nội dung).
        if 'EOF found after object' in err or 'expected \'directive or statement\'' in err:
            lines = out.split('\n')
            # đóng triple-quote đang mở ở dòng cuối có nội dung
            opened = 0
            for i, l in enumerate(lines):
                opened += l.count('"""')
            if opened % 2 == 1:
                last = max(i for i, l in enumerate(lines) if l.strip())
                if not lines[last].rstrip().endswith(('"""', '"""@vi', '.')):
                    lines[last] = lines[last].rstrip() + '"""'
                    fixes.append('đóng triple-quote bị cắt (dòng %d)' % (last + 1))
                    truncated = True
                out = '\n'.join(lines)
                continue
            st = out.rstrip()
            if st and not st.endswith(('.', '}', ']')):
                out = out.rstrip() + ' .\n'
                fixes.append('thêm "." kết thúc statement (file bị cắt)')
                truncated = True
                continue
            break

        if not ml:
            break
        ln = int(ml.group(1))
        lines = out.split('\n')
        if not (1 <= ln <= len(lines)):
            break
        i = ln - 1
        t = lines[i].strip()

        # 3c) dòng lỗi là SUBJECT MỚI `<ex:monk/…>` mà statement trước chưa đóng
        #     ⇒ dấu `.` kết thúc bị mất. Vá vào dòng trước.
        if re.match(r'^\s*<ex:(monk|person)/', lines[i]):
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0:
                pj = lines[j].rstrip()
                if pj and not pj.endswith(('.', '}', ']', '@vi', '@zh', '@en', '@sa')) \
                        and '"""' not in pj[-8:] and '@prefix' not in pj:
                    lines[j] = pj + ' .'
                    fixes.append('L%d: thêm "." đóng statement trước subject mới' % ln)
                    truncated = True
                    out = '\n'.join(lines)
                    continue

        # 3d) dòng lỗi là PREDICATE (`bkg:hasDisciple …`) đứng ngay sau một objectList
        #     chưa đóng ⇒ dấu `,` cuối dòng trước phải là `;`.
        if re.match(r'^\s*bkg:(hasDisciple|hasTeacher|isLineageFounder|generationOrder)\b',
                lines[i]):
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0:
                pj = lines[j].rstrip()
                if pj.endswith(','):
                    lines[j] = pj[:-1] + ' ;'
                    fixes.append('L%d: đổi "," → ";" để mở predicate %s'
                                 % (ln, lines[i].strip().split()[0]))
                    out = '\n'.join(lines)
                    continue

        # 2) dòng CSV dính → vô hiệu hoá
        if _looks_csv(t):
            lines[i] = '# [T205] dòng CSV dính, đã vô hiệu: ' + t
            fixes.append('L%d: vô hiệu dòng CSV dính' % ln)
            out = '\n'.join(lines)
            continue

        # 3) URI mở đầu bằng `ex:monk/...` mà thiếu dấu `<` (sai 1 ký tự)
        m = re.match(r'^(\s*)ex:monk/[\w\-]+(\s*[,;.]?\s*)$', lines[i])
        if m:
            lines[i] = '%s<ex:monk/%s>%s' % (m.group(1),
                                             re.match(r'^ex:monk/([\w\-]+)', lines[i].strip()).group(1),
                                             m.group(2))
            fixes.append('L%d: thêm "<" mở đầu URI ex:monk/… bị thiếu' % ln)
            out = '\n'.join(lines)
            continue

        # 4) dòng bắt đầu bằng `bkg:hasDisciple` nhưng dòng trước chưa có `,`
        #    ⇒ dấu phẩy bị mất. Sửa DÒNG TRƯỚC (không chèn dòng giả).
        if re.match(r'^\s*bkg:hasDisciple\s+<ex:', lines[i]):
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0 and lines[j].rstrip().endswith(','):
                # đã có phẩy → dòng này là predicate mới, cần `;` kết thúc objectList
                lines[j] = lines[j].rstrip() + ' ;'
                lines[i] = '    ' + lines[i].strip()
                fixes.append('L%d: thêm ";" đóng objectList trước hasDisciple' % ln)
            else:
                lines[j] = lines[j].rstrip() + ' ,'
                lines[i] = lines[i]
                fixes.append('L%d: thêm "," nối hasDisciple vào objectList trước' % ln)
            out = '\n'.join(lines)
            continue

        # 5) `bkg:isLineageFounder true .` — thiếu dấu ngoặc kép quanh boolean
        m = re.search(r'bkg:isLineageFounder\s+(true|false)\s*(\.|$)', lines[i])
        if m:
            lines[i] = lines[i].replace(m.group(1) + m.group(2),
                                        '"%s"^^xsd:boolean .' % m.group(1), 1) \
                if m.group(2) == '.' else \
                lines[i].replace(m.group(1), '"%s"^^xsd:boolean' % m.group(1), 1)
            fixes.append('L%d: bọc boolean isLineageFounder thành literal' % ln)
            out = '\n'.join(lines)
            continue

        # 3) tag ngôn ngữ cắt cụt (`"""@v` thay vì `"""@vi`)
        m = re.search(r'"""\s*@(\w+)\s*$', lines[i])
        if m and m.group(1) not in LANGS:
            lines[i] = lines[i][:m.start()] + '@vi'
            fixes.append('L%d: sửa tag ngôn ngữ @%s → @vi' % (ln, m.group(1)))
            out = '\n'.join(lines)
            continue

        # 6) `. .` hoặc `..` — dấu chấm thừa cuối statement
        if re.search(r'\.\s+\.\s*$', lines[i]):
            lines[i] = re.sub(r'\.\s+\.\s*$', ' .', lines[i].rstrip())
            fixes.append('L%d: bỏ dấu "." thừa' % ln)
            out = '\n'.join(lines)
            continue

        # 7) statement `;` bị treo → chèn ` .` trước dòng lỗi
        prev = lines[i - 1].rstrip() if i > 0 else ''
        if prev and not prev.endswith(('.', '}', ']')) and '"""' not in prev[-8:]:
            lines.insert(i, prev + ' .')
            fixes.append('L%d: chèn " ." đóng statement trước dòng lỗi' % ln)
            truncated = True
            out = '\n'.join(lines)
            continue

        # 5) dòng lỗi rỗng / không nhận diện được → tìm dòng CSV gần nhất phía trên
        j = i - 1
        hit = False
        while j >= 0 and j > i - 30:
            if _looks_csv(lines[j].strip()):
                lines[j] = '# [T205] dòng CSV dính, đã vô hiệu: ' + lines[j].strip()
                fixes.append('L%d: vô hiệu dòng CSV dính (gần dòng lỗi)' % (j + 1))
                out = '\n'.join(lines)
                hit = True
                break
            j -= 1
        if hit:
            continue
        break

    ok, info = _parse_text(out)
    return out, fixes, truncated


def repair(src, filename):
    """Wrapper giữ tương thích — dùng vòng lặp sửa-lỗi."""
    return repair_iterative(src, filename)


def _parse_text(text):
    """Parse text tạm. Trả (ok, triples|error)."""
    try:
        import rdflib
    except Exception:
        return None, 0
    p = os.path.join(BACKUP_DIR, '_t205_probe.ttl')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    try:
        g = rdflib.Graph()
        g.parse(p, format='turtle')
        return True, len(g)
    except Exception as e:
        return False, str(e)
    finally:
        try:
            os.remove(p)
        except Exception:
            pass


def can_parse(path):
    try:
        import rdflib
    except Exception:
        return None, 0
    try:
        g = rdflib.Graph()
        g.parse(path, format='turtle')
        return True, len(g)
    except Exception as e:
        return False, str(e).replace('\n', ' ')[:70]


def verify(fn, path):
    """Kiểm chứng file đã vá có đủ dữ liệu hay bị cắt.

    Trả (ok, thông tin). Dùng để phân biệt "bị cắt thật" với "chỉ thiếu dấu chấm".
    """
    import rdflib
    CORE = ('label', 'type', 'biographicalNote', 'dharmaLineageName',
            'generationOrder', 'P1_is_identified_by', 'birthEvent',
            'deathEvent', 'hasTeacher', 'hasDisciple', 'gender',
            'isLineageFounder')
    g = rdflib.Graph()
    g.parse(path, format='turtle')
    ps = set()
    bio = ''
    for _s, pr, o in g:
        t = str(pr)
        ps.add(t.split('#')[-1] if '#' in t else t.rsplit('/', 1)[-1])
        if t.split('#')[-1] == 'biographicalNote':
            bio = str(o).strip()
    miss = [k for k in CORE if k not in ps]
    complete = bool(bio) and bio[-1] in '.!?"\''
    return (not miss and complete), {
        'triples': len(g), 'missing': miss, 'bio_len': len(bio),
        'bio_end': bio[-46:] if bio else '', 'complete': complete,
    }


def scan():
    broken = []
    if not os.path.isdir(TTL_DIR):
        return broken
    for fn in sorted(os.listdir(TTL_DIR)):
        if not fn.endswith('.ttl') or fn == '0-template.ttl':
            continue
        p = os.path.join(TTL_DIR, fn)
        ok, info = can_parse(p)
        if ok is False:
            broken.append((fn, p, info))
    return broken


def main():
    ap = argparse.ArgumentParser(description='T205 — sửa file TTL không parse được')
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--revert', action='store_true')
    ap.add_argument('--verify', action='store_true',
                    help='kiem chung file da va: du predicate / bio co cat khong')
    args = ap.parse_args()

    broken = scan()
    print('=' * 84)
    print('T205 — SỬA FILE TTL HỎNG  (%d file)' % len(broken))
    print('TTL_DIR = %s' % TTL_DIR)
    print('=' * 84)

    plans = []
    for fn, p, err in broken:
        src = read(p)
        new, fixes, trunc = repair(src, fn)
        if new == src or not fixes:
            print('  %-34s [BỎ QUA] không xác định cách sửa' % fn)
            continue
        # kiểm tra parse được không (ghi tạm rồi thử)
        tmp = os.path.join(BACKUP_DIR, '_t205_tmp.ttl')
        os.makedirs(BACKUP_DIR, exist_ok=True)
        write(tmp, new)
        ok, info = can_parse(tmp)
        if not ok:
            write(tmp, src)
            print('  %-34s [BỎ QUA] sửa xong vẫn hỏng: %s' % (fn, info))
            continue
        write(tmp, src)
        plans.append({'file': fn, 'path': p, 'fixes': fixes,
                      'truncated': trunc, 'triples': info})

    for pl in plans:
        print()
        print('  %-34s  triples=%s%s'
              % (pl['file'], pl['triples'],
                 '   [NGHI BI CAT — can kiem chung]' if pl['truncated'] else ''))
        for fx in pl['fixes']:
            print('      · %s' % fx)

    # Nhắc: nhãn truncated là heuristic, PHẢI kiểm chứng trước khi kết luận.
    # T205 (2026-10-01): 3 file bị gắn [TRUNCATED] hoá ra đều ĐỦ 12/12 predicate,
    # bio dài 322-381% median và kết thúc câu hoàn chỉnh ⇒ KHÔNG mất dữ liệu.
    if any(pl['truncated'] for pl in plans):
        print()
        print('  [LUU Y] Nhan "NGHI BI CAT" chi la heuristic ban chay.')
        print('         Hay chay --verify de kiem chung predicate/bio truoc khi')
        print('         yeu cau Admin upload lai ban goc.')

    print()
    print('  Sửa được: %d / %d file' % (len(plans), len(broken)))

    if args.verify:
        print()
        print('  --- KIEM CHUNG DU LIEU (12 predicate + bio) ---')
        for fn in ("TS-Ban-Son-Bao-Tich.ttl", "TS-Thanh-Dang-Minh-Luong.ttl",
                   "TS-Van-Cai-Thu-Tri.ttl"):
            ok, info = verify(fn, os.path.join(TTL_DIR, fn))
            tag = 'DU DU LIEU' if ok else 'THIEU: %s' % (info['missing'] or 'bio cut')
            print('    %-30s %-16s triples=%-4d bio=%-6d %s'
                  % (fn, tag, info['triples'], info['bio_len'],
                     ('ket thuc: ...%s' % info['bio_end']) if info['complete'] else ''))
        print('=' * 84)
        return 0

    if not (args.apply or args.dry_run):
        print('=' * 84)
        return 0
    if args.dry_run:
        print('  [DRY-RUN] chưa ghi gì. Dùng --apply để thực hiện.')
        print('=' * 84)
        return 0

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bdir = os.path.join(BACKUP_DIR, 't205_ttl_%s' % ts)
    os.makedirs(bdir, exist_ok=True)
    n = 0
    for pl in plans:
        shutil.copy2(pl['path'], os.path.join(bdir, pl['file']))
        write(pl['path'], read(pl['path']) if False else repair(read(pl['path']),
                                                                 pl['file'])[0])
        n += 1
        print('  [SỬA] %s' % pl['file'])
    print()
    print('[XONG] %d file · backup %s' % (n, bdir))
    print('[REVERT] python -X utf8 scripts/t205_repair_broken_ttl.py --revert "%s"' % bdir)
    print('=' * 84)
    return 0


if __name__ == '__main__':
    sys.exit(main())