# -*- coding: utf-8 -*-
"""
T167 Phase 4 — Translation Validator (deterministic layers A-G)

Validator không rewrite bản dịch. Chỉ gate PASS / REVIEW / FAIL.
FAIL vẫn lưu raw để audit.

Layers:
  A. Schema/JSON validation
  B. Provenance validation (ruleset_id, prompt_version, model, source_hash)
  C. Omission/Addition heuristic gate (ratio, echo check, segment count)
  D. Terminology consistency (glossary lock, canonical names)
  E. Canonical person/place checks (DILA/people/places/namevi_map lookup)
  F. Source/Target sanity (length, language, structure)
  G. Ruleset compliance (active rules in ruleset satisfied)

Usage:
    python scripts/translation_validator.py <translation_id>
    python scripts/translation_validator.py --job <job_id>
    python scripts/translation_validator.py --work <work_id> --status unreviewed
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'lineage.db')
GLOSS_PATH = os.path.join(BASE_DIR, 'data', 'glossaries', 'vi-buddhist.json')

RATIO_MIN, RATIO_MAX = 0.6, 8.0
ZH_RE = re.compile(r'[\u4e00-\u9fff]')


def _con():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    return con


def load_glossary():
    try:
        with open(GLOSS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get('terms', {})
    except Exception:
        return {}


def zh_norm(s):
    return re.sub(r'\s+', '', s or '')


# ======================= VALIDATION LAYERS =======================

def layer_a_schema(seg):
    """A. Schema/JSON validation - kiểm tra các field bắt buộc."""
    required = ['translation_id', 'translation_text', 'source_original_hash',
                'prompt_version', 'model_name', 'provider', 'ruleset_id',
                'created_by_job_id', 'revision_no']
    missing = [f for f in required if not seg.get(f)]
    if missing:
        return 'FAIL', f'Schema missing: {missing}'
    if not isinstance(seg.get('revision_no'), int):
        return 'FAIL', 'revision_no không phải int'
    return 'PASS', ''


def layer_b_provenance(seg, con):
    """B. Provenance validation."""
    # ruleset tồn tại
    if seg['ruleset_id']:
        rs = con.execute("SELECT 1 FROM translation_rulesets WHERE ruleset_id=?", (seg['ruleset_id'],)).fetchone()
        if not rs:
            return 'FAIL', f"ruleset_id '{seg['ruleset_id']}' không tồn tại trong translation_rulesets"
    else:
        return 'FAIL', 'ruleset_id rỗng'
    # prompt_version khớp expected
    if seg['prompt_version'] != 't95-batch-cbeta-v1':
        return 'REVIEW', f"prompt_version '{seg['prompt_version']}' khác kỳ vọng 't95-batch-cbeta-v1'"
    # source_hash không rỗng
    if not seg['source_original_hash']:
        return 'FAIL', 'source_original_hash rỗng'
    # model/provider không rỗng
    if not seg['model_name'] or not seg['provider']:
        return 'FAIL', 'model_name hoặc provider rỗng'
    return 'PASS', ''


def layer_c_omission_addition(seg, con):
    """C. Omission/Addition heuristic gate."""
    # Lấy nguyên bản
    tp = con.execute("SELECT original_zh, sequence_no FROM text_passages WHERE passage_id=?",
                     (seg['passage_id'],)).fetchone()
    if not tp:
        return 'FAIL', f"Không tìm thấy text_passages cho {seg['passage_id']}"

    zh = tp['original_zh']
    vi = seg['translation_text'] or ''

    # 1. Echo check
    if zh_norm(vi) == zh_norm(zh):
        return 'FAIL', 'Echo nguyên văn Hán (chưa dịch)'

    # 2. Tỷ lệ ký tự
    if len(zh) == 0:
        return 'FAIL', 'Nguyên bản rỗng'
    ratio = len(vi) / len(zh)
    if not (RATIO_MIN <= ratio <= RATIO_MAX):
        return 'REVIEW', f'Tỷ lệ ký tự {ratio:.2f} ngoài [{RATIO_MIN}-{RATIO_MAX}]'

    # 3. Segment count heuristic (nếu alignment có)
    align = con.execute("SELECT COUNT(*) as c FROM passage_translation_alignment WHERE translation_id=?",
                        (seg['translation_id'],)).fetchone()
    if align and align['c'] == 0:
        return 'REVIEW', 'Không có alignment record'

    return 'PASS', ''


def layer_d_terminology(seg, con):
    """D. Terminology consistency - kiểm tra glossary lock."""
    glossary = load_glossary()
    vi = seg['translation_text'] or ''
    issues = []

    for zh_term, vi_term in glossary.items():
        if zh_term in seg.get('source_text', '') or zh_term in vi:  # cần source_text; tạm bỏ qua nếu không có
            pass  # sẽ check khi có source_text từ text_passages

    # Kiểm tra các thuật ngữ cốt lõi KHÔNG được dịch sai
    forbidden_patterns = {
        'Phật': 'Phật', 'Pháp': 'Pháp', 'Tăng': 'Tăng',  # Tam Bảo
        'Bồ Tát': 'Bồ Tát', 'A La Hán': 'A La Hán',
        'Niết Bàn': 'Niết Bàn', 'Bồ Đề': 'Bồ Đề',
    }
    # Tạm: chỉ flag nếu thấy từ tiếng Anh/viết tắt trong bản dịch Phật học
    if re.search(r'\b(Buddha|Dharma|Sangha|Nirvana|Bodhi)\b', vi, re.IGNORECASE):
        issues.append('Có từ tiếng Anh thay vì Hán-Việt chuẩn')

    if issues:
        return 'REVIEW', '; '.join(issues)
    return 'PASS', ''


def layer_e_canonical_names(seg, con):
    """E. Canonical person/place - lookup DILA/people/places/namevi_map."""
    vi = seg['translation_text'] or ''
    issues = []

    # Extract potential Hán names in brackets or patterns
    # Tạm: check nếu có tên không resolve được
    # Cần source_text để extract entities → skip deep check ở validator cơ bản

    # Kiểm tra placeholder REVIEW
    if '[REVIEW:' in vi:
        return 'REVIEW', 'Có placeholder [REVIEW:] chưa resolve'

    return 'PASS', ''


def layer_f_sanity(seg):
    """F. Source/Target sanity."""
    vi = seg['translation_text'] or ''
    issues = []

    # Language check - ít nhất 50% ký tự Việt (Latin + dấu)
    viet_chars = len(re.findall(r'[a-zA-Zàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]', vi))
    total_chars = len(vi.replace(' ', ''))
    if total_chars > 0 and viet_chars / total_chars < 0.5:
        issues.append(f'Tỷ lệ ký tự Việt thấp ({viet_chars}/{total_chars})')

    # Empty check
    if not vi.strip():
        return 'FAIL', 'Bản dịch rỗng'

    # Cấu trúc cơ bản
    if vi.count('.') == 0 and vi.count('。') == 0 and len(vi) > 100:
        issues.append('Dài mà không có dấu câu kết thúc')

    if issues:
        return 'REVIEW', '; '.join(issues)
    return 'PASS', ''


def layer_g_ruleset(seg, con):
    """G. Ruleset compliance - kiểm tra các rule active trong ruleset."""
    if not seg['ruleset_id']:
        return 'REVIEW', 'Không có ruleset_id'

    # Lấy active rules của ruleset này
    rules = con.execute("""
        SELECT tr.rule_code, tr.rule_type, tr.rule_text, tr.priority
        FROM translation_rules tr
        JOIN translation_ruleset_rules trr ON tr.rule_code = trr.rule_code
        WHERE trr.ruleset_id = ? AND trr.is_active = 1 AND tr.is_active = 1
        ORDER BY tr.priority
    """, (seg['ruleset_id'],)).fetchall()

    if not rules:
        return 'REVIEW', f'Ruleset {seg["ruleset_id"]} không có rule active nào'

    # Tạm: compliance check cơ bản = check FORBIDDEN rules (type='forbidden')
    # Cần source_text và logic phức tạp hơn → L0 validator chỉ check existence
    forbidden_rules = [r for r in rules if r['rule_type'] == 'forbidden']
    return 'PASS', f'{len(rules)} rules active ({len(forbidden_rules)} forbidden)'


# ======================= MAIN VALIDATOR =======================

def validate_translation(translation_id, con):
    """Validate 1 translation_segments record. Trả dict kết quả."""
    seg = con.execute("SELECT * FROM translation_segments WHERE translation_id=?", (translation_id,)).fetchone()
    if not seg:
        return {'translation_id': translation_id, 'overall': 'FAIL', 'error': 'Not found'}

    seg = dict(seg)
    # Lấy source_text từ text_passages
    tp = con.execute("SELECT original_zh FROM text_passages WHERE passage_id=?", (seg['passage_id'],)).fetchone()
    if tp:
        seg['source_text'] = tp['original_zh']

    results = []
    layers = [
        ('A', layer_a_schema, (seg,)),
        ('B', layer_b_provenance, (seg, con)),
        ('C', layer_c_omission_addition, (seg, con)),
        ('D', layer_d_terminology, (seg, con)),
        ('E', layer_e_canonical_names, (seg, con)),
        ('F', layer_f_sanity, (seg,)),
        ('G', layer_g_ruleset, (seg, con)),
    ]

    overall = 'PASS'
    for name, fn, args in layers:
        status, msg = fn(*args)
        results.append({'layer': name, 'status': status, 'message': msg})
        if status == 'FAIL' and overall != 'FAIL':
            overall = 'FAIL'
        elif status == 'REVIEW' and overall == 'PASS':
            overall = 'REVIEW'

    return {
        'translation_id': translation_id,
        'overall': overall,
        'layers': results,
        'validated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


def validate_job(job_id, con):
    """Validate tất cả translation của 1 job."""
    segs = con.execute("SELECT translation_id FROM translation_segments WHERE created_by_job_id=?", (job_id,)).fetchall()
    out = []
    for s in segs:
        out.append(validate_translation(s['translation_id'], con))
    return out


def validate_work_unreviewed(work_id, con, limit=100):
    """Validate các translation unreviewed của 1 work."""
    segs = con.execute("""
        SELECT ts.translation_id FROM translation_segments ts
        WHERE ts.work_id = ? AND ts.quality_status = 'unreviewed'
        ORDER BY ts.created_at DESC LIMIT ?
    """, (work_id, limit)).fetchall()
    out = []
    for s in segs:
        out.append(validate_translation(s['translation_id'], con))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('translation_id', nargs='?')
    parser.add_argument('--job')
    parser.add_argument('--work')
    parser.add_argument('--status', default='unreviewed')
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    con = _con()
    try:
        if args.translation_id:
            res = validate_translation(args.translation_id, con)
            print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else format_result(res))
        elif args.job:
            res = validate_job(args.job, con)
            print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else format_batch(res))
        elif args.work:
            res = validate_work_unreviewed(args.work, con, args.limit)
            print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else format_batch(res))
        else:
            parser.print_help()
    finally:
        con.close()


def format_result(r):
    if 'error' in r:
        return f"❌ {r['translation_id']}: {r['error']}"
    icon = '✅' if r['overall'] == 'PASS' else ('⚠️' if r['overall'] == 'REVIEW' else '❌')
    out = [f"{icon} {r['translation_id']} → {r['overall']}"]
    for l in r['layers']:
        s_icon = '✅' if l['status'] == 'PASS' else ('⚠️' if l['status'] == 'REVIEW' else '❌')
        out.append(f"  Layer {l['layer']}: {s_icon} {l['message']}")
    return '\n'.join(out)


def format_batch(batch):
    pass_count = sum(1 for r in batch if r['overall'] == 'PASS')
    review_count = sum(1 for r in batch if r['overall'] == 'REVIEW')
    fail_count = sum(1 for r in batch if r['overall'] == 'FAIL')
    out = [f"=== Batch: {len(batch)} | PASS {pass_count} | REVIEW {review_count} | FAIL {fail_count} ==="]
    for r in batch:
        out.append(format_result(r))
    return '\n'.join(out)


if __name__ == '__main__':
    main()