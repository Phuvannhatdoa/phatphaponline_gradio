"""
t50_backfill_ref_translations.py — T50c: Batch backfill CBETA ref translations
================================================================================
Batch translate refs where han_text IS NOT NULL AND vi_summary_clean IS NULL.
Uses Gemini pipeline from app.py.

Usage:
    python scripts/t50_backfill_ref_translations.py              # translate all pending
    python scripts/t50_backfill_ref_translations.py --limit 10   # translate 10
    python scripts/t50_backfill_ref_translations.py --dry-run    # preview only
"""
import sqlite3, sys, argparse, io, time, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DB_PATH = 'data/lineage.db'


def hanviet_normalize(text, glossary=None):
    """Basic Han-Viet normalization — correct common Pinyin errors."""
    if not text:
        return text
    # Common corrections
    corrections = {
        'Tang': 'Tăng', 'Phat': 'Phật', 'Linh': 'Linh',
        'Thien': 'Thiên', 'Chung': 'Chung', 'Son': 'Sơn',
    }
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)
    return text


def make_translation_prompt(han_text):
    """Create prompt for Gemini translation."""
    return f"""Dịch câu Hán văn Phật giáo sau sang tiếng Việt.
Yêu cầu:
- Dùng Hán-Việt cho thuật ngữ Phật giáo
- Giữ nguyên tên riêng (người, nơi)
- Ngắn gọn, dễ hiểu

Hán văn:
{han_text}

Tiếng Việt:"""


def call_gemini(prompt, api_key=None):
    """Call Gemini API for translation. Returns translated text or None."""
    try:
        import urllib.request, json
        key = api_key or ''
        if not key:
            return None
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}'
        data = json.dumps({'contents': [{'parts': [{'text': prompt}]}]}).encode()
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
    except Exception as e:
        print(f"  Gemini error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='T50c: Batch backfill CBETA translations')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=100, help='Max refs to translate')
    parser.add_argument('--api-key', default='', help='Gemini API key')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    # Find pending translations
    pending = conn.execute("""
        SELECT ref_code, han_text, vi_summary_clean
        FROM cbeta_ref_passages
        WHERE han_text IS NOT NULL AND han_text != ''
          AND (vi_summary_clean IS NULL OR vi_summary_clean = '')
        LIMIT ?
    """, (args.limit,)).fetchall()

    total_pending = conn.execute("""
        SELECT COUNT(*) FROM cbeta_ref_passages
        WHERE han_text IS NOT NULL AND han_text != ''
          AND (vi_summary_clean IS NULL OR vi_summary_clean = '')
    """).fetchone()[0]

    total_done = conn.execute("""
        SELECT COUNT(*) FROM cbeta_ref_passages
        WHERE vi_summary_clean IS NOT NULL AND vi_summary_clean != ''
    """).fetchone()[0]

    print(f"Translation backfill status:")
    print(f"  Already translated: {total_done}")
    print(f"  Pending: {total_pending}")
    print(f"  Would translate: {len(pending)}")

    if pending:
        print(f"\nPending refs:")
        for ref, han, _ in pending[:5]:
            print(f"  {ref}: {han[:60]}...")

    if args.dry_run or not pending:
        print(f"\n[{'DRY RUN' if args.dry_run else 'Nothing to do'}]")
        conn.close()
        return

    if not args.api_key:
        print("\n⚠ No --api-key provided. Cannot translate.")
        print("  Set GEMINI_API_KEY env var or pass --api-key=...")
        conn.close()
        return

    # Translate each ref
    translated = 0
    for ref, han, _ in pending:
        print(f"\nTranslating {ref}: {han[:50]}...")
        prompt = make_translation_prompt(han)
        result = call_gemini(prompt, args.api_key)
        if result:
            clean = hanviet_normalize(result.strip())
            conn.execute("""
                UPDATE cbeta_ref_passages SET vi_summary_clean = ?
                WHERE ref_code = ?
            """, (clean, ref))
            conn.commit()
            translated += 1
            print(f"  ✓ {clean[:60]}")
        else:
            print(f"  ✗ Translation failed")
        time.sleep(4)  # Rate limit

    print(f"\n✅ Translated {translated}/{len(pending)} refs")

    # Final stats
    total_done_after = conn.execute("""
        SELECT COUNT(*) FROM cbeta_ref_passages
        WHERE vi_summary_clean IS NOT NULL AND vi_summary_clean != ''
    """).fetchone()[0]
    print(f"   Total translated: {total_done} → {total_done_after}")

    conn.close()


if __name__ == '__main__':
    main()
