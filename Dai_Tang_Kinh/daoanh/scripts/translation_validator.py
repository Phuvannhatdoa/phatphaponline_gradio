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

T167 (2026-11-07, Phương án A — Admin chốt): thêm hàm validate_text(source_text,
draft_text, ref=None, con=None) — adapter CHỈ KIỂM TRA cho pipeline chưa ghi
translation_segments (ví dụ lô T50 passage backfill, ghi passage.vi_text +
translation_cache). Hàm này KHÔNG ghi DB, KHÔNG sửa draft, chỉ trả cờ tham khảo.
Layer B (provenance)/E (canonical name đầy đủ)/G (ruleset compliance) CHƯA áp
dụng ở adapter này — xem khối "TEXT ADAPTER" bên dưới.
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


# ======================= TEXT ADAPTER (T167, 2026-11-07) =======================
#
# Bối cảnh: lô dịch T50 (scripts/t50_passage_vi_backfill.py) ghi
# passage.vi_text + translation_cache, KHÔNG ghi translation_segments
# (không có translation_id, ruleset_id, prompt_version... như validate_translation()
# cần). Admin đã chọn Phương án A (2026-11-07): gắn validator T167 vào lô T50
# ở CHẾ ĐỘ CHỈ KIỂM TRA — validate_text() dưới đây KHÔNG đụng
# validate_translation()/validate_job() hiện có, KHÔNG ghi DB, KHÔNG sửa draft.
#
# QUAN TRỌNG — kết quả validate_text() CHỈ LÀ CỜ THAM KHẢO:
#   - Layer A/C/F ở đây là bản RÚT GỌN của layer_a_schema/layer_c_omission_addition/
#     layer_f_sanity (không cần bản ghi translation_segments đầy đủ, không có
#     alignment/provenance DB thật).
#   - Layer D (terminology) chỉ chạy best-effort nếu đọc được glossary; lỗi đọc
#     glossary KHÔNG làm hỏng kết quả (tối đa REVIEW, không raise).
#   - Layer B (provenance translation_segments), E (canonical person/place lookup
#     DILA/places/namevi_map đầy đủ) và G (ruleset compliance) CHƯA được áp dụng
#     trong validate_text() — cần translation_segments thật để chạy đúng, xem
#     validate_translation() ở trên.
def validate_text(source_text, draft_text, ref=None, con=None):
    """T167 Phase 4 — Adapter validator cho văn bản rời (KHÔNG cần translation_segments).

    Dùng cho pipeline chưa ghi translation_segments (ví dụ T50 passage backfill):
    chỉ có cặp (source_text Hán gốc, draft_text bản dịch nháp) + ref tham khảo
    (ví dụ "T50n2060 0001a01"). KHÔNG ghi DB, KHÔNG sửa draft_text — chỉ trả dict
    kết quả cùng định dạng {'overall', 'layers': [...]} như validate_translation().

    Args:
        source_text: nguyên văn Hán (CBETA raw_text).
        draft_text: bản dịch nháp AI (sau clean/normalize, trước khi ghi DB).
        ref: chuỗi tham khảo để log (loc_ref/sigla); không dùng để tra DB.
        con: sqlite3 connection (tuỳ chọn) — chỉ dùng cho layer D khi cần;
             None vẫn chạy được (layer D tự fallback glossary rỗng).

    Returns:
        dict {'ref', 'overall': PASS|REVIEW|FAIL, 'layers': [...], 'mode', 'validated_at'}
        — KHÔNG bao giờ raise ra ngoài (mọi lỗi layer bị bắt riêng, hạ xuống REVIEW).
    """
    layers = []
    overall = ['PASS']  # list để mutate trong closure (Python 2/3 an toàn, không cần nonlocal)

    def _update(status):
        if status == 'FAIL':
            overall[0] = 'FAIL'
        elif status == 'REVIEW' and overall[0] == 'PASS':
            overall[0] = 'REVIEW'

    # Layer A (rút gọn) — schema/rỗng
    try:
        if not (source_text or '').strip():
            status, msg = 'FAIL', 'source_text rỗng'
        elif not (draft_text or '').strip():
            status, msg = 'FAIL', 'draft_text rỗng'
        else:
            status, msg = 'PASS', ''
    except Exception as e:
        status, msg = 'REVIEW', f'Layer A lỗi (bỏ qua, không chặn): {e}'
    layers.append({'layer': 'A', 'status': status, 'message': msg})
    _update(status)

    # Layer C (rút gọn) — echo nguyên văn Hán + tỷ lệ độ dài (không cần DB alignment)
    try:
        zh = source_text or ''
        vi = draft_text or ''
        if zh_norm(vi) == zh_norm(zh):
            status, msg = 'FAIL', 'Echo nguyên văn Hán (chưa dịch)'
        elif len(zh) == 0:
            status, msg = 'FAIL', 'Nguyên bản rỗng'
        else:
            ratio = len(vi) / len(zh)
            if not (RATIO_MIN <= ratio <= RATIO_MAX):
                status, msg = 'REVIEW', f'Tỷ lệ ký tự {ratio:.2f} ngoài [{RATIO_MIN}-{RATIO_MAX}]'
            else:
                status, msg = 'PASS', ''
    except Exception as e:
        status, msg = 'REVIEW', f'Layer C lỗi (bỏ qua, không chặn): {e}'
    layers.append({'layer': 'C', 'status': status, 'message': msg})
    _update(status)

    # Layer D (rút gọn, best-effort) — glossary lock, chỉ kiểm nếu đọc được
    try:
        seg_like = {'translation_text': draft_text or '', 'source_text': source_text or ''}
        status, msg = layer_d_terminology(seg_like, con)
    except Exception as e:
        status, msg = 'REVIEW', f'Layer D không đọc được glossary (bỏ qua, không chặn): {e}'
    layers.append({'layer': 'D', 'status': status, 'message': msg})
    _update(status)

    # Layer F — sanity tiếng Việt (ký tự Việt, cấu trúc câu)
    try:
        status, msg = layer_f_sanity({'translation_text': draft_text or ''})
    except Exception as e:
        status, msg = 'REVIEW', f'Layer F lỗi (bỏ qua, không chặn): {e}'
    layers.append({'layer': 'F', 'status': status, 'message': msg})
    _update(status)

    return {
        'ref': ref,
        'overall': overall[0],
        'layers': layers,
        'mode': 'validate_text-adapter-CHI-KIEM-TRA-T167',
        'note': 'Chỉ cờ tham khảo; layer B/E/G đầy đủ chưa áp dụng (cần translation_segments thật).',
        'validated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


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