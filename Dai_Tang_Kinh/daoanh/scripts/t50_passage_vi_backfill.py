"""
t50_passage_vi_backfill.py — T50c: Backfill passage.vi_text (bản dịch nháp AI) + cache + report
================================================================================================
Mục tiêu:
  - Dịch nháp (draft) Hán văn CBETA cho các passage liên kết với THỰC THỂ PLACE
    qua Groq (giống pipeline T73/T74) → ghi vào `passage.vi_text` + `translation_draft=1`.
  - Đồng thời lưu vào `translation_cache` (source_type='passage', entity_id=passage_id,
    source_hash=sha256(raw_text), status='auto') để user load sau REUSE cache,
    không gọi LLM lần nữa (đúng mẫu api_place_translate).
  - Hỗ trợ báo lỗi: report endpoint (đã add ở app.py) tăng report_count trong translation_cache.

Usage:
    python scripts/t50_passage_vi_backfill.py --dry-run
    python scripts/t50_passage_vi_backfill.py --limit 20
    python scripts/t50_passage_vi_backfill.py --sigla T50n2060 --limit 50
    python scripts/t50_passage_vi_backfill.py --verify
    python scripts/t50_passage_vi_backfill.py --revert            # gỡ toàn bộ (rollback)
    python scripts/t50_passage_vi_backfill.py --revert --sigla T50n2060

Key tự động đọc theo thứ tự: env GROQ_KEY → data/llm_config.json.groq_key → GROQ_KEY trong app.py.
Rollback nhanh: backup DB đã có ở data/lineage_backup_t50_20260902.db.
"""
import sqlite3
import sys
import os
import io
import re
import time
import json
import hashlib
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── Đường dẫn ─────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
DAOANH = os.path.dirname(HERE)
# T50 test-robustness (2026-11-03): cho phép override đường dẫn DB qua env
# `T50_DB_PATH` để test khởi động có thể chạy trên fixture DB tạm khi worktree
# chưa có `data/lineage.db` thật (data/ không được git track). Mặc định KHÔNG
# đổi: không set env → vẫn dùng data/lineage.db như cũ.
DB_PATH = os.environ.get('T50_DB_PATH') or os.path.join(DAOANH, 'data', 'lineage.db')
LLM_CONFIG_PATH = os.path.join(DAOANH, 'data', 'llm_config.json')
APP_PY = os.path.join(DAOANH, 'app.py')
SCRIPTS_DIR = HERE
_T50_STATUS_FILE = os.path.join(DAOANH, 'data', 't50_job_status.json')

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def _t50_self_reconcile_on_failure(exit_reason, extra=None):
    """T50 Windows startup fix (2026-11-03): khi worker này tự chết bất thường
    (KeyboardInterrupt/Exception), tự ghi t50_job_status.json về running=False
    NGAY (không chờ admin mở lại dashboard để app.py poll /job-status mới phát
    hiện pid chết). Chỉ đụng file khi pid trong status khớp pid của chính
    mình — tránh đè trạng thái của job khác đang chạy song song (race).
    Chỉ dùng cho nhánh lỗi; khi hoàn tất bình thường KHÔNG gọi hàm này, để
    app.py (/api/admin/t50/job-status) tự lo việc chuyển sang sigla kế tiếp
    trong hàng đợi như thiết kế cũ."""
    try:
        if not os.path.exists(_T50_STATUS_FILE):
            return
        with open(_T50_STATUS_FILE, 'r', encoding='utf-8') as f:
            st = json.load(f)
        if int(st.get('pid') or -1) != os.getpid():
            return
        st['running'] = False
        st['exit_reason'] = exit_reason
        st['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        if extra:
            st.update(extra)
        with open(_T50_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

try:
    from hanviet_normalization import normalize_text as hanviet_normalize
except Exception:
    hanviet_normalize = lambda t: t

try:
    from style_constitution import select_rules as _t165_select_rules_0
    _SSOT_OK = True
except Exception:
    _SSOT_OK = False
    _t165_select_rules_0 = None

GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
DEFAULT_MODEL = 'qwen/qwen3.8-27b'

# ── Cấu hình key / model ───────────────────────────────────────────────────
def _llm_config_read():
    try:
        with open(LLM_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _read_app_const():
    """Best-effort đọc GROQ_KEY / GROQ_MODEL từ app.py (không import app — tránh khởi động Flask)."""
    try:
        with open(APP_PY, 'r', encoding='utf-8') as f:
            src = f.read()
        key = re.search(r'^GROQ_KEY\s*=\s*"([^"]+)"', src, re.M)
        model = re.search(r'^GROQ_MODEL\s*=\s*"([^"]+)"', src, re.M)
        return (key.group(1) if key else ''), (model.group(1) if model else DEFAULT_MODEL)
    except Exception:
        return '', DEFAULT_MODEL


def resolve_groq_key():
    cfg = _llm_config_read()
    if os.environ.get('GROQ_KEY'):
        return os.environ['GROQ_KEY']
    if cfg.get('groq_key'):
        return cfg['groq_key']
    hardcoded, _ = _read_app_const()
    return hardcoded


def resolve_groq_model():
    cfg = _llm_config_read()
    if os.environ.get('GROQ_MODEL'):
        return os.environ['GROQ_MODEL']
    if cfg.get('groq_model'):
        return cfg['groq_model']
    _, model = _read_app_const()
    return model or DEFAULT_MODEL


# ── Prompt + gọi LLM ───────────────────────────────────────────────────────
def _style_lock_blocks(conn, source_text=None):
    """T123 — Style Constitution lock. T165: delegate SSOT style_lock → rules lọc theo
    match_scope + glossary filter theo source_text (nếu có). Trả
    (rule_block, glossary_block, exemplar_block). Không nạp toàn bộ lexicon (Zero-RAM)."""
    try:
        from style_constitution import style_lock as _ss_lock
        lk = _ss_lock(conn, source_text=source_text)
        rule_block = '\n'.join(
            f"- {r['rule_text']}" for r in lk['rules'])
        glossary_block = '\n'.join(
            f"  - {g['term_zh']} → {g['term_vi']}" for g in lk['glossary'])
        parts = []
        for i, e in enumerate(lk['exemplar'], 1):
            parts.append(
                f"--- MẪU {i} (theo {e['source_label']}) ---\n"
                f"Hán: {e['zh']}\nViệt: {e['vi']}"
            )
        exemplar_block = '\n\n'.join(parts)
        return rule_block, glossary_block, exemplar_block
    except Exception:
        pass
    # legacy fallback (SSOT không sẵn)
    rule_block, glossary_block, exemplar_block = '', '', ''
    try:
        rows = conn.execute(
            "SELECT rule_text FROM translation_rules WHERE is_active=1 ORDER BY priority ASC"
        ).fetchall()
        rule_block = '\n'.join(f"- {r['rule_text']}" for r in rows)
    except Exception:
        rule_block = ''
    try:
        gl = conn.execute(
            "SELECT term_zh, term_vi FROM translation_glossary WHERE is_locked=1 ORDER BY id LIMIT 120"
        ).fetchall()
        glossary_block = '\n'.join(f"  - {g['term_zh']} → {g['term_vi']}" for g in gl)
    except Exception:
        glossary_block = ''
    try:
        ex = conn.execute(
            "SELECT zh, vi, source_label FROM translation_exemplar "
            "WHERE is_active=1 ORDER BY length_zh LIMIT 3"
        ).fetchall()
        parts = []
        for i, e in enumerate(ex, 1):
            parts.append(
                f"--- MẪU {i} (theo {e['source_label']}) ---\n"
                f"Hán: {e['zh']}\nViệt: {e['vi']}"
            )
        exemplar_block = '\n\n'.join(parts)
    except Exception:
        exemplar_block = ''
    return rule_block, glossary_block, exemplar_block


def build_prompt(raw_text, ref, conn=None):
    """Prompt dịch đoạn Hán CBETA → Việt, giữ tên riêng dạng Hán-Việt.
    T123 — nhúng Style Constitution (active rules + glossary lock + exemplar danh tác).
    T165 — rules/glossary filter theo raw_text (source_text)."""
    rule_block, glossary_block, exemplar_block = _style_lock_blocks(conn, source_text=raw_text)
    return f"""[PERSONA — BAN DỊCH PTDA]
Bạn là thành viên Ban Dịch PTDA — dịch giả Hán-Việt chuyên ngành Phật học, kế thừa tinh thần
các dịch giả và từ điển Phật học danh tiếng. Dịch đoạn Hán văn CBETA sau sang tiếng Việt.

=== QUY TẮC DỊCH BẮT BUỘC (Style Constitution) ===
{rule_block or '- Dịch trung thành, trang trọng, tôn kính người xuất gia bằng "ngài" (KHÔNG dùng "chàng").'}

=== GLOSSARY LOCK (thuật ngữ bắt buộc, ưu tiên cao nhất) ===
{glossary_block or '  (không có)'}

=== FEW-SHOT MẪU PHONG CÁCH (học theo tiền bối danh tác) ===
{exemplar_block or '  (không có)'}

[HÁN GỐC - CBETA]
{raw_text}

QUY ƯỚC TÊN RIÊNG:
- Mọi tên người, tên chùa, tên địa danh phải dùng dạng Hán-Việt.
- Không dùng dạng tiếng Anh, Pinyin, hoặc phiên âm hiện đại.
- Ví dụ: 少林寺 → Thiếu Lâm Tự, 會稽 → Cối Kê.
- Người xuất gia phải xưng hô "ngài/Hòa Thượng/Thiền Sư", NGHIÊM CẤM "chàng/anh/cậu/ông".

YÊU CẦU DỊCH THUẬT:
- Dịch đoạn Hán trên sang tiếng Việt hiện đại, mạch lạc, dễ hiểu.
- Giữ đủ thông tin lai lịch nhân vật, bối cảnh địa danh, sự kiện tu học / hoằng pháp chính.
- Văn phong tường thuật, nối câu mạch lạc (không chẻ thành câu vụn).
- Không liệt kê từng câu nguyên văn; chỉ cần 1 đoạn tiếng Việt hoàn chỉnh.
- Độ dài: 1-2 câu Hán → 1-2 câu Việt; 3-5 câu Hán → 3-4 câu Việt; 5-10 câu Hán → 5-7 câu Việt.

Số hiệu mã: {ref}
""".strip()


def clean_llm_output(text):
    if not text:
        return text
    cleaned = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line == 'ETA':
            continue
        if re.match(r'^\(CBETA[\s\(\)]*$', line):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)


def call_groq(prompt, key, model, max_attempts=8):
    """Gọi Groq với retry + backoff trên 429 (rate limit free tier) và 5xx/network.
    Trả về text hoặc None (chỉ None khi đã cạn số lần thử)."""
    import urllib.request
    import urllib.error
    payload = json.dumps({
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.1,
        'max_tokens': 2048,
    }).encode('utf-8')
    for attempt in range(1, max_attempts + 1):
        try:
            req = urllib.request.Request(
                GROQ_URL, data=payload,
                headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
                         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            if data.get('choices'):
                return (data['choices'][0]['message']['content'] or '').strip()
            err = str(data.get('error', 'Unknown'))[:200]
            print(f'    ✗ attempt{attempt} Groq api_error: {err}')
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry = 30.0
                try:
                    ra = e.headers.get('Retry-After')
                    if ra:
                        retry = float(ra)
                except Exception:
                    pass
                if attempt < max_attempts:
                    print(f'    ⏳ attempt{attempt} rate_limit → retry sau {retry:.0f}s', end='', flush=True)
                    time.sleep(retry)
                    continue
                print(f'    ✗ attempt{attempt} Groq HTTP 429 (hết lần retry)')
            elif e.code in (401, 403):
                print(f'    ✗ attempt{attempt} Groq HTTP {e.code} — key/UA bị từ chối. Abort.')
                return None
            else:
                retry = 15.0
                if attempt < max_attempts:
                    print(f'    ⏳ attempt{attempt} HTTP {e.code} → retry sau {retry:.0f}s', end='', flush=True)
                    time.sleep(retry)
                    continue
                print(f'    ✗ attempt{attempt} Groq HTTP {e.code}')
        except Exception as e:
            retry = 10.0
            if attempt < max_attempts:
                print(f'    ⏳ attempt{attempt} network error → retry: {e}', end='', flush=True)
                time.sleep(retry)
                continue
            print(f'    ✗ attempt{attempt} Groq error: {e}')
    return None


# ── T167 validator adapter (2026-11-07, Admin Phương án A) ─────────────────
# Gắn validator T167 (scripts/translation_validator.py::validate_text) vào lô
# T50 ở CHẾ ĐỘ CHỈ KIỂM TRA: chạy SAU khi có draft từ Groq (sau call_groq, sau
# clean/normalize, TRƯỚC khi ghi passage.vi_text), ghi kết quả ra file JSON
# RIÊNG (data/t50_validation_report.jsonl, append 1 dòng/passage). Tuyệt đối
# KHÔNG đổi passage.vi_text / translation_draft / translation_cache hiện có —
# chỉ là lớp quan sát thêm. Lỗi validator (import thiếu, exception bất kỳ) chỉ
# in log cảnh báo, KHÔNG chặn lô dịch. Tắt bằng cờ --no-validate (mặc định BẬT).
#
# GHI CHÚ: kết quả validate_text() chỉ là CỜ THAM KHẢO — layer B/E/G đầy đủ
# (provenance translation_segments, canonical person/place DILA, ruleset
# compliance) CHƯA được áp dụng ở adapter này. Xem docstring translation_validator.py.
VALIDATION_REPORT_PATH = os.path.join(DAOANH, 'data', 't50_validation_report.jsonl')


def t167_validate_and_log(passage_id, raw_text, draft_text, ref, conn, enabled=True):
    """Gọi validate_text() (T167) và append 1 dòng JSON vào VALIDATION_REPORT_PATH.
    KHÔNG ghi vào lineage.db. KHÔNG sửa draft_text. KHÔNG raise ra ngoài — mọi lỗi
    (kể cả import translation_validator thất bại) chỉ in cảnh báo rồi return."""
    if not enabled:
        return
    try:
        from translation_validator import validate_text as _t167_validate_text
        result = _t167_validate_text(raw_text, draft_text, ref=ref, con=conn)
        result['passage_id'] = passage_id
        with open(VALIDATION_REPORT_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    except Exception as _e:
        print(f'    ⚠ validator T167 lỗi (bỏ qua, KHÔNG chặn lô dịch): {_e}')


def source_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:24]


def rules_version(conn):
    """T165: delegate SSOT select_rules(conn)['rules_version_global'] (rất khớp _t73_rules_version —
    SHA256 toàn bộ rule_text active theo priority). FOLLBACK giống cũ nếu SSOT lỗi."""
    try:
        if _t165_select_rules_0 is not None:
            return _t165_select_rules_0(conn, None)['rules_version_global']
    except Exception:
        pass
    try:
        rows = conn.execute(
            "SELECT rule_text FROM translation_rules WHERE is_active=1 ORDER BY priority ASC"
        ).fetchall()
        combined = '\n---\n'.join(r['rule_text'] or '' for r in rows)
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
    except Exception:
        return ''


# ── Schema additive + query ────────────────────────────────────────────────
def ensure_schema(conn):
    cols = [r[1] for r in conn.execute("PRAGMA table_info(passage)").fetchall()]
    if 'translation_draft' not in cols:
        conn.execute("ALTER TABLE passage ADD COLUMN translation_draft INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print('  + Added passage.translation_draft')


def select_pending(conn, sigla=None, limit=None, offset=0):
    """Distinct passage_id liên kết PLACE, chưa có vi_text (resumable)."""
    sub = (
        "SELECT DISTINCT pe.passage_id FROM passage_entity pe "
        "JOIN entity e ON pe.entity_id = e.entity_id "
        "WHERE e.entity_type='PLACE'"
    )
    sql = (
        "SELECT p.passage_id, p.text_id, p.loc_ref, p.raw_text "
        "FROM passage p WHERE p.passage_id IN (" + sub + ") "
        "  AND (p.vi_text IS NULL OR p.vi_text='') "
        "  AND p.raw_text IS NOT NULL AND p.raw_text != ''"
    )
    params = []
    if sigla:
        sql += " AND p.text_id = ?"
        params.append(sigla)
    if limit:
        sql += " ORDER BY p.passage_id LIMIT ? OFFSET ?"
        params += [limit, offset]
    else:
        sql += " ORDER BY p.passage_id"
    return conn.execute(sql, params).fetchall()


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description='T50c: backfill passage.vi_text (draft AI) + cache')
    ap.add_argument('--dry-run', action='store_true', help='chỉ đếm, không dịch')
    ap.add_argument('--limit', type=int, default=0, help='giới hạn số passage (0 = tất cả)')
    ap.add_argument('--offset', type=int, default=0, help='bắt đầu từ offset')
    ap.add_argument('--sigla', default='', help='lọc theo text_id (vd T50n2060)')
    ap.add_argument('--api-key', default='', help='Groq key (nếu muốn ghi đè)')
    ap.add_argument('--sleep', type=float, default=0.2, help='giây ngủ giữa mỗi gọi Groq')
    ap.add_argument('--verify', action='store_true', help='thống kê trạng thái hiện tại')
    ap.add_argument('--revert', action='store_true', help='rollback: xoá vi_text + cache đã đổ')
    ap.add_argument('--no-validate', action='store_true',
                     help='T167: tắt validator (mặc định BẬT) — chỉ ghi cờ tham khảo vào '
                          'data/t50_validation_report.jsonl, KHÔNG đổi passage.vi_text/cache')
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    if args.verify:
        ensure_schema(conn)
        total_all = conn.execute("SELECT COUNT(*) FROM passage").fetchone()[0]
        linked = conn.execute(
            "SELECT COUNT(DISTINCT p.passage_id) FROM passage p WHERE p.passage_id IN ("
            "SELECT DISTINCT pe.passage_id FROM passage_entity pe "
            "JOIN entity e ON pe.entity_id=e.entity_id WHERE e.entity_type='PLACE')"
        ).fetchone()[0]
        done = conn.execute(
            "SELECT COUNT(*) FROM passage WHERE vi_text IS NOT NULL AND vi_text!=''").fetchone()[0]
        draft = conn.execute(
            "SELECT COUNT(*) FROM passage WHERE translation_draft=1").fetchone()[0]
        cache = conn.execute(
            "SELECT COUNT(*) FROM translation_cache WHERE source_type='passage'").fetchone()[0]
        reported = conn.execute(
            "SELECT COUNT(*) FROM translation_cache WHERE source_type='passage' AND status='reported'").fetchone()[0]
        print('== VERIFY T50 ==')
        print(f'  passage tổng:                {total_all}')
        print(f'  passage liên kết PLACE:      {linked}')
        print(f'  đã có vi_text:               {done}')
        print(f'  translation_draft=1:         {draft}')
        print(f'  translation_cache passage:   {cache} (reported={reported})')
        conn.close()
        return

    if args.revert:
        ensure_schema(conn)
        if args.sigla:
            where = " AND p.text_id=?"
            params = [args.sigla]
        else:
            where = ""
            params = []
        linked_sub = (
            "SELECT DISTINCT pe.passage_id FROM passage_entity pe "
            "JOIN entity e ON pe.entity_id=e.entity_id WHERE e.entity_type='PLACE'")
        rows = conn.execute(
            "SELECT p.passage_id, p.raw_text FROM passage p WHERE p.passage_id IN (" + linked_sub + ")"
            " AND (p.translation_draft=1) " + where, params).fetchall()
        updated = 0
        for r in rows:
            conn.execute("UPDATE passage SET vi_text=NULL, translation_draft=0 WHERE passage_id=?",
                         (r['passage_id'],))
            updated += 1
        conn.commit()
        # Xoá cache tương ứng (source_hash theo raw_text)
        del_rows = conn.execute("SELECT source_hash FROM translation_cache WHERE source_type='passage'").fetchall()
        if not args.sigla:
            conn.execute("DELETE FROM translation_cache WHERE source_type='passage'")
            conn.commit()
            print(f'  Đã xoá {len(del_rows)} dòng translation_cache source_type=passage')
        else:
            # lọc theo passage raw_text hash? đơn giản: xoá cache có entity_id thuộc sigla
            for r in rows:
                h = source_hash(r['raw_text'] or '')
                conn.execute("DELETE FROM translation_cache WHERE source_type='passage' AND source_hash=?",
                             (h,))
            conn.commit()
            print('  Đã xoá cache passage cho sigla đã chọn')
        print(f'  REVERT OK: {updated} passage đã reset (vi_text=NULL, translation_draft=0)')
        conn.close()
        return

    # ---- Dry-run / translate ----
    ensure_schema(conn)
    key = args.api_key or resolve_groq_key()
    model = resolve_groq_model()
    if not key:
        print('✗ Không tìm thấy GROQ key (env/llm_config.json/app.py). Dùng --api-key. Abort.')
        conn.close()
        return 1

    limit = args.limit or 0
    rows = select_pending(conn, args.sigla or None, limit or -1, args.offset)
    print(f'== T50 backfill (+cache) ==')
    print(f'  model={model}  sigla={args.sigla or "(tất cả)"}  pending(window)={len(rows)}')
    if not rows:
        print('  Không còn passage chờ dịch.')
        conn.close()
        return 0

    if args.dry_run:
        print('  [DRY RUN — không dịch]')
        for r in rows[:5]:
            print(f'    {r["passage_id"]} {r["text_id"]} {r["loc_ref"]} · {len(r["raw_text"])} chữ: {r["raw_text"][:40]}…')
        conn.close()
        return 0

    # Dịch
    rv = rules_version(conn)
    ok = fail = 0
    for r in rows:
        raw = (r['raw_text'] or '').strip()
        ref = f"{r['text_id']}"
        if r['loc_ref']:
            ref = f"{r['text_id']} {r['loc_ref']}"
        prompt = build_prompt(raw, ref, conn)
        text = call_groq(prompt, key, model)
        if text:
            text = clean_llm_output(text)
            text = (hanviet_normalize(text) or text).strip()
            if text:
                t167_validate_and_log(r['passage_id'], raw, text, ref, conn,
                                       enabled=not args.no_validate)
                conn.execute(
                    "UPDATE passage SET vi_text=?, translation_draft=1 WHERE passage_id=?",
                    (text, r['passage_id']))
                now = time.strftime('%Y-%m-%dT%H:%M:%S')
                try:
                    from style_constitution import write_cache as _ss_write_cache
                    _ss_write_cache(
                        conn, source_hash(raw), 'passage', str(r['passage_id']), raw, text,
                        model, rv, status='auto')
                except Exception:
                    conn.execute(
                        """INSERT OR REPLACE INTO translation_cache
                           (source_hash, source_type, entity_id, source_text, translated_text,
                            model_id, rules_version, status, report_count, created_at, updated_at)
                           VALUES (?,?,?,?,?,?,?,'auto',0,?,?)""",
                        (source_hash(raw), 'passage', str(r['passage_id']), raw, text,
                         model, rv, now, now))
                conn.commit()
                ok += 1
                print(f'  ✓ {r["passage_id"]} [{ref}] → {text[:60]}…')
            else:
                fail += 1
        else:
            fail += 1
            print(f'  ✗ {r["passage_id"]} [{ref}] — dịch thất bại (bỏ qua, sẽ thử lại lần sau)')
        time.sleep(args.sleep)

    print(f'\n  OK={ok}  FAIL={fail}  (resume-safe: passage đã dịch được bỏ qua lần sau)')
    conn.close()
    return 0 if fail == 0 else 2


if __name__ == '__main__':
    # T50 Windows startup fix (2026-11-03): bắt KeyboardInterrupt/Exception ở
    # cấp top-level để (1) thoát với mã lỗi rõ ràng thay vì traceback dở dang
    # + KeyboardInterrupt không rõ nguyên nhân (xem data/t50_job.log cũ), và
    # (2) tự cập nhật t50_job_status.json running=False ngay khi chết bất
    # thường, không chờ admin mở lại dashboard. Không đổi logic dịch/schema.
    try:
        _rc = main()
    except KeyboardInterrupt:
        print('\n✗ Job bị ngắt (KeyboardInterrupt) — có thể do Ctrl+C hoặc '
              'tiến trình cha bị dừng. Đã dừng sạch, không ghi dở dang.',
              file=sys.stderr)
        _t50_self_reconcile_on_failure('keyboard_interrupt')
        sys.exit(130)
    except Exception as _e:
        import traceback as _tb
        _tb.print_exc()
        print(f'\n✗ Job dừng vì lỗi ngoài dự kiến: {_e}', file=sys.stderr)
        _t50_self_reconcile_on_failure('exception', {'error': str(_e)[:300]})
        sys.exit(1)
    else:
        sys.exit(_rc)