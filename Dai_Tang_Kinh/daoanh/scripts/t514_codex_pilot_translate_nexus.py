# -*- coding: utf-8 -*-
"""
T514 việc 5 — PILOT: dịch 50 nexus đầu tiên của sách 'Mingsengzhuanchao' bằng
Codex CLI (đã login sẵn bằng tài khoản ChatGPT Plus của Admin trên máy này —
xem báo cáo T514), cho qua validator (việc 4, đọc translation_rules WHERE
status='active' thật từ DB), ghi staging JSONL. DỪNG CỨNG ở 50 nexus — không
bao giờ tự chạy quá --limit, mặc định 50 và không cho truyền lớn hơn
PILOT_HARD_CAP.

CHỈ ĐỌC DB (SELECT dila_bio_nexus, translation_rules). KHÔNG UPDATE/INSERT/
DELETE bảng nào. KHÔNG ghi dila_bio_nexus_vi.

Output: data/dila_import/biographies.2024-01/vn_translate_codex/<book>/batch_<ts>.jsonl
mỗi dòng: {nexus_id, book, text_zh, text_vi, model, timestamp, validation}
(bản KHÔNG qua được validator vẫn được ghi, nhưng validation.passed=False,
để tab UI hiển thị đúng trạng thái "chưa qua quy tắc" — KHÔNG ẩn số liệu).

Đo số liệu THẬT (không suy diễn): tổng thời gian, số bản đạt rule/tổng số
bản sinh, tốc độ giây/nexus — in ra cuối lần chạy và lưu vào
_pilot_report.json cùng thư mục output.

Usage:
    python scripts/t514_codex_pilot_translate_nexus.py --book Mingsengzhuanchao --limit 50
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
DAOANH_DIR = os.path.join(BASE, '..')
DB_PATH = os.path.join(DAOANH_DIR, 'data', 'lineage.db')
OUT_ROOT = os.path.join(DAOANH_DIR, 'data', 'dila_import', 'biographies.2024-01', 'vn_translate_codex')

PILOT_HARD_CAP = 50   # Admin: "pilot 50 nexus dừng chờ tôi xem" — khoá cứng, không vượt.
CODEX_MODEL = None    # None = dùng model mặc định đã cấu hình cho account Codex.

CODEX_EXE = shutil.which('codex') or 'codex'   # Windows: shutil.which tra ve .cmd/.exe dung PATHEXT,
                                                 # subprocess tran 'codex' thuong (khong shell) se WinError 2.

CJK_RE = re.compile(r'[一-鿿㐀-䶿豈-﫿]')
# CHỈ dùng dấu MACRON và CARON (hoàn toàn không tồn tại trong tiếng Việt) để
# nhận diện pinyin — dấu sắc/huyền (á à...) KHÔNG đưa vào vì đó là dấu thanh
# tiếng Việt hợp lệ (bug đã phát hiện khi pilot thật: "Cầu-na-bạt-đà" hợp lệ
# bị báo nhầm là pinyin do dùng chung regex với dấu sắc).
PINYIN_TONE_RE = re.compile(r'[āēīōūǖĀĒĪŌŪǕǎěǐǒǔǚǍĚǐǑǔǚ]')


def iter_nexus_rows(book, limit):
    """Streaming qua cursor, mode=ro thật ở mức SQLite URI. KHÔNG fetchall()."""
    uri = f'file:{os.path.abspath(DB_PATH)}?mode=ro'
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    try:
        cur = conn.execute(
            "SELECT nexus_id, text_zh, seq FROM dila_bio_nexus WHERE book = ? ORDER BY seq LIMIT ?",
            (book, limit)
        )
        for row in cur:
            yield row
    finally:
        conn.close()


def read_active_rules():
    """SELECT thật từ translation_rules — KHÔNG hard-code số lượng/nội dung."""
    conn = sqlite3.connect(f'file:{os.path.abspath(DB_PATH)}?mode=ro', uri=True, timeout=10)
    try:
        rows = conn.execute(
            "SELECT rule_code, rule_type, description, rule_text FROM translation_rules "
            "WHERE status='active' ORDER BY priority, rule_code"
        ).fetchall()
        return [{'rule_code': r[0], 'rule_type': r[1], 'description': r[2], 'rule_text': r[3]} for r in rows]
    finally:
        conn.close()


def validate(text_zh, text_vi, active_rules):
    """Giống hệt logic trong app.py (_t514_validate_translation) — bản độc
    lập cho pilot script để KHÔNG phải import toàn bộ app.py (tránh side
    effect khởi tạo Flask app / mở server khi chạy script dòng lệnh)."""
    checks = []
    text_vi = (text_vi or '').strip()
    text_zh = (text_zh or '').strip()

    def add(code, ok, note):
        checks.append({'rule_code': code, 'passed': ok, 'note': note})

    has_empty = len(text_vi) == 0
    add('_EMPTY_CHECK', not has_empty, 'Bản dịch trống' if has_empty else 'Có nội dung')
    has_cjk = bool(CJK_RE.search(text_vi))
    add('_NO_CJK_LEFTOVER', not has_cjk, 'Còn sót chữ Hán' if has_cjk else 'Không còn chữ Hán')
    has_pinyin = bool(PINYIN_TONE_RE.search(text_vi))
    add('NO_PINYIN', not has_pinyin, 'Phát hiện dấu pinyin' if has_pinyin else 'Không phát hiện pinyin')
    has_bracket = ('[' in text_vi) or (']' in text_vi)
    add('NO_ADDITION', not has_bracket, 'Có [] — khả năng thêm chú thích' if has_bracket else 'Không có []')
    len_ok = True
    if text_zh and not has_empty:
        ratio = len(text_vi) / max(len(text_zh), 1)
        len_ok = 0.4 <= ratio <= 6.0
    add('_LENGTH_RATIO', len_ok, 'Tỉ lệ độ dài bất thường' if not len_ok else 'Tỉ lệ độ dài hợp lý')

    machine_checkable = {'_EMPTY_CHECK', '_NO_CJK_LEFTOVER', 'NO_PINYIN', 'NO_ADDITION', '_LENGTH_RATIO'}
    n_not_checkable = sum(1 for r in active_rules if r['rule_code'] not in machine_checkable)
    return {
        'passed': all(c['passed'] for c in checks),
        'n_rules_active': len(active_rules),
        'n_checked_machine': len(checks),
        'n_not_machine_checkable': n_not_checkable,
        'checks': checks,
    }


PROMPT_TMPL = (
    'Dich doan Han van tieu su Phat giao sau sang tieng Viet hoc thuat, dung '
    'phien am Han-Viet chuan cho ten rieng/dia danh, giu nguyen nien hieu/nam '
    'thang/so lieu. CHI tra loi DUY NHAT ban dich tieng Viet, khong giai thich, '
    'khong lap lai nguyen van Han, khong dung markdown.\n\nHan van:\n{zh}'
)


def call_codex(text_zh, timeout_sec=90):
    """Gọi codex exec non-interactive, dùng -o <file> để lấy ĐÚNG câu trả lời
    cuối (last message), không phải parse transcript có banner. Trả về
    (text_vi hoặc None, error hoặc None)."""
    prompt = PROMPT_TMPL.format(zh=text_zh or '')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
        out_file = tf.name
    try:
        # Truyền prompt qua stdin (dấu '-'), KHÔNG qua argv: trên Windows,
        # subprocess dựng command-line qua list2cmdline rồi CreateProcess đọc
        # bằng codepage hệ thống (vd cp1252), làm hỏng ký tự CJK trong argv
        # (quan sát thực tế: Codex nhận prompt rỗng/hỏng, hỏi lại "gửi đoạn
        # Hán văn cần dịch"). stdin với encoding='utf-8' tường minh không bị
        # lỗi này.
        cmd = [
            CODEX_EXE, 'exec',
            '--sandbox', 'read-only',
            '-o', out_file,
            '-',
        ]
        if CODEX_MODEL:
            cmd[2:2] = ['-m', CODEX_MODEL]
        proc = subprocess.run(
            cmd, cwd=DAOANH_DIR, capture_output=True, timeout=timeout_sec,
            input=prompt.encode('utf-8'),
        )
        if proc.returncode != 0:
            stderr_txt = (proc.stderr or b'').decode('utf-8', errors='replace')
            return None, f'codex_exit_{proc.returncode}: {stderr_txt[-300:]}'
        if not os.path.isfile(out_file):
            return None, 'no_output_file'
        with open(out_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        if not text:
            return None, 'empty_output'
        return text, None
    except subprocess.TimeoutExpired:
        return None, 'timeout'
    except Exception as e:
        return None, f'exception: {e}'
    finally:
        try:
            os.unlink(out_file)
        except OSError:
            pass


def run(book, limit, verbose=True):
    limit = min(limit, PILOT_HARD_CAP)
    active_rules = read_active_rules()
    os.makedirs(os.path.join(OUT_ROOT, book), exist_ok=True)
    ts_tag = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = os.path.join(OUT_ROOT, book, f'batch_{ts_tag}.jsonl')

    rows = list(iter_nexus_rows(book, limit))
    if verbose:
        print(f"Pilot Codex T514 việc 5 · sách='{book}' · {len(rows)} nexus "
              f"(giới hạn cứng {PILOT_HARD_CAP}) · rule active={len(active_rules)}")

    n_generated = 0
    n_passed = 0
    n_error = 0
    t_start = time.time()
    per_nexus_sec = []

    with open(out_path, 'a', encoding='utf-8') as fout:
        for nexus_id, text_zh, seq in rows:
            t0 = time.time()
            text_vi, err = call_codex(text_zh)
            dt = time.time() - t0
            per_nexus_sec.append(dt)
            if err:
                n_error += 1
                if verbose:
                    print(f"  x [{nexus_id}] lỗi Codex: {err[:150]} ({dt:.1f}s)")
                continue
            n_generated += 1
            validation = validate(text_zh, text_vi, active_rules)
            if validation['passed']:
                n_passed += 1
            record = {
                'nexus_id': nexus_id, 'book': book, 'text_zh': text_zh, 'text_vi': text_vi,
                'model': 'codex-cli', 'timestamp': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'validation': validation,
            }
            fout.write(json.dumps(record, ensure_ascii=False) + '\n')
            fout.flush()
            if verbose:
                mark = 'PASS' if validation['passed'] else 'FAIL'
                print(f"  [{n_generated}/{len(rows)}] {nexus_id} -> {mark} ({dt:.1f}s)")

    elapsed = time.time() - t_start
    report = {
        'book': book,
        'n_requested': len(rows),
        'n_generated': n_generated,
        'n_error': n_error,
        'n_passed_validator': n_passed,
        'pass_rate_of_generated': round(n_passed / n_generated, 4) if n_generated else None,
        'elapsed_sec_total': round(elapsed, 1),
        'avg_sec_per_nexus': round(sum(per_nexus_sec) / len(per_nexus_sec), 2) if per_nexus_sec else None,
        'nexus_per_minute': round(len(rows) / (elapsed / 60.0), 2) if elapsed > 0 else None,
        'out_path': out_path,
        'ts': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
    report_path = os.path.join(OUT_ROOT, book, '_pilot_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    if verbose:
        print('\n=== PILOT XONG (ĐÃ DỪNG, KHÔNG CHẠY LÔ LỚN) ===')
        for k, v in report.items():
            print(f'  {k}: {v}')
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', required=True)
    ap.add_argument('--limit', type=int, default=50)
    args = ap.parse_args()
    if args.limit > PILOT_HARD_CAP:
        print(f"DỪNG: --limit={args.limit} vượt giới hạn cứng pilot "
              f"({PILOT_HARD_CAP}). Admin chỉ duyệt pilot 50 nexus.")
        sys.exit(1)
    run(args.book, args.limit)


if __name__ == '__main__':
    main()
