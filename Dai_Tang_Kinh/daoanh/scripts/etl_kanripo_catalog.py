"""
ETL: Kanripo GitHub → kanripo_catalog
Fetch Buddhist text repos (KR6*) from https://github.com/orgs/kanripo
and upsert into kanripo_catalog with category + cbeta_ref metadata.

Kanripo (Kanseki Repository 漢籍リポジトリ) holds all Chinese classical texts.
Buddhist texts live in the KR6 series (子部 — Masters/Philosophy).
KR1-KR5 are Confucian/Taoist classics — excluded here.

Run:  python scripts/etl_kanripo_catalog.py [--dry-run] [--limit N]
"""

import argparse
import re
import sqlite3
import time
import json
import urllib.request
import urllib.error
from datetime import date

DB_PATH = "data/lineage.db"
GITHUB_ORG_API = "https://api.github.com/orgs/kanripo/repos"
GITHUB_SEARCH_API = "https://api.github.com/search/repositories"

# KR6 subcategory mapping (Buddhist section of Kanripo)
# Source: Kanseki Repository documentation / kanseki.org
KR6_SUBCAT = {
    "KR6a": ("Āgama", "Hán dịch A-hàm"),
    "KR6b": ("Luật tạng", "Vinaya"),
    "KR6c": ("Luận tạng", "Abhidharma"),
    "KR6d": ("Trung Quán", "Madhyamaka"),
    "KR6e": ("Mật tông", "Esoteric/Tantra"),
    "KR6f": ("Thiền tông", "Chan/Zen"),
    "KR6g": ("Tịnh Độ", "Pure Land"),
    "KR6h": ("Thiên Thai", "Tiantai"),
    "KR6i": ("Hoa Nghiêm", "Huayan misc"),
    "KR6j": ("Mật tông", "Tantra misc"),
    "KR6k": ("Trung Hoa bản địa", "Chinese indigenous"),
    "KR6l": ("Phụ lục", "Supplements"),
    "KR6m": ("Đại thừa", "Mahayana misc"),
    "KR6n": ("Bổn sinh / Nhân duyên", "Jataka/Avadana"),
    "KR6q": ("Hỏi đáp", "Catechisms"),
    "KR6s": ("Thư mục / Chú sớ", "Bibliography"),
    "KR6t": ("Dịch sử", "Translation history"),
}

# Curated CBETA T-number cross-references — CONFIRMED only.
# Do NOT add entries without verifying against actual Kanripo repo content.
# Kanripo KR6 subcategory prefixes do NOT map 1:1 to CBETA canon divisions.
# KR6a = Āgama (confirmed). Other KR6x subcategories need verification.
KNOWN_CBETA_REFS = {
    # Āgamas — confirmed via Kanripo repo descriptions
    "KR6a0001": "T1",     # 長阿含經 Dīrghāgama
    "KR6a0002": "T26",    # 中阿含經 Madhyamāgama
    "KR6a0003": "T99",    # 雜阿含經 Saṃyuktāgama
    "KR6a0004": "T125",   # 增壹阿含經 Ekottarikāgama
    # Bibliography seed (existing row)
    "KR6s0102": "L143n1608",  # 大藏聖教法寶標目
    # NOTE: KR6b/KR6c/KR6d cross-refs removed — actual titles from GitHub
    # do not match assumed mappings. Need manual verification per repo.
}


def get_kr6_cat(text_id):
    for prefix, (cat, subcat) in sorted(KR6_SUBCAT.items(), key=lambda x: -len(x[0])):
        if text_id.startswith(prefix):
            return cat, subcat
    return "Phật giáo", "KR6 misc"


def parse_title_zh(description):
    """
    Kanripo repo description format: "title-dynasty-" or plain title.
    Extract title_zh (Chinese title before first '-').
    """
    if not description:
        return ''
    # Pattern: "漢字title-朝代-" → take part before first '-'
    m = re.match(r'^([^\-\|]+)', description.strip())
    if m:
        return m.group(1).strip()
    return description[:80].strip()


def parse_dynasty(description):
    """Extract dynasty from 'title-dynasty-' format."""
    if not description:
        return ''
    parts = description.split('-')
    if len(parts) >= 2:
        return parts[1].strip()
    return ''


def gh_get(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "ptda-kanripo-etl/1.0"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403 and attempt < retries - 1:
                print(f"  Rate limited (403), sleeping 60s...")
                time.sleep(60)
            else:
                raise
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                raise
    return None


def fetch_kr6_repos(limit=None):
    """
    Fetch KR6* repos from kanripo org using GitHub Search API.
    Search API finds KR6 directly without paging through all 1500+ org repos.
    Rate limit: 10 requests/min unauthenticated — sleep between pages.
    """
    repos = []
    page = 1
    per_page = 100
    while True:
        url = (f"{GITHUB_SEARCH_API}?q=KR6+in:name+org:kanripo"
               f"&per_page={per_page}&page={page}&sort=updated")
        print(f"  Search page {page}...", end=' ', flush=True)
        try:
            result = gh_get(url)
        except Exception as e:
            print(f"ERROR: {e}")
            break
        if not result or 'items' not in result:
            print("(no items)")
            break
        items = result['items']
        kr6 = [r for r in items if re.match(r'^KR6', r['name'])]
        repos.extend(kr6)
        total_count = result.get('total_count', 0)
        print(f"{len(items)} hits, {len(kr6)} KR6 | total_count={total_count}")
        if len(items) < per_page:
            break
        page += 1
        time.sleep(7)  # search API: 10 req/min → 6s minimum; use 7s to be safe
        if limit and len(repos) >= limit:
            repos = repos[:limit]
            break
    return repos


def upsert_repos(conn, repos, dry_run=False):
    today = str(date.today())
    inserted = updated = skipped = 0

    for repo in repos:
        text_id = repo['name']
        description = repo.get('description') or ''
        github_repo = repo.get('html_url') or f"https://github.com/kanripo/{text_id}"

        title_zh = parse_title_zh(description)
        dynasty = parse_dynasty(description)
        cat, subcat = get_kr6_cat(text_id)
        cbeta_ref = KNOWN_CBETA_REFS.get(text_id, '')

        if dry_run:
            print(f"  [DRY] {text_id}: '{title_zh}' | {cat} | dynasty={dynasty} | cbeta={cbeta_ref}")
            continue

        existing = conn.execute(
            "SELECT id, title_zh, cbeta_ref FROM kanripo_catalog WHERE text_id=?", (text_id,)
        ).fetchone()

        if existing:
            # Prefer existing curated title/cbeta over API data
            new_title = title_zh if title_zh and not existing[1] else existing[1]
            new_cbeta = cbeta_ref if cbeta_ref else (existing[2] or '')
            conn.execute("""
                UPDATE kanripo_catalog
                SET title_zh=?, category=?, subcategory=?, cbeta_ref=?,
                    github_repo=?, catalog_created=?
                WHERE text_id=?
            """, (new_title, cat, subcat, new_cbeta, github_repo, today, text_id))
            updated += 1
        else:
            conn.execute("""
                INSERT INTO kanripo_catalog
                    (text_id, title_zh, title_en, category, subcategory, cbeta_ref,
                     language, license, github_repo, catalog_created, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (text_id, title_zh, '', cat, subcat, cbeta_ref,
                  'zh', 'CC BY-SA 4.0', github_repo, today,
                  f"dynasty:{dynasty}" if dynasty else ''))
            inserted += 1

    if not dry_run:
        conn.commit()
    return inserted, updated, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    print("=== Kanripo ETL Phase B — KR6 Buddhist texts ===")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'WRITE'}")

    print("\n[1] Fetching KR6 Buddhist repos from GitHub API...")
    try:
        repos = fetch_kr6_repos(limit=args.limit)
        print(f"  KR6 repos found: {len(repos)}")
    except Exception as e:
        print(f"  ERROR fetching from GitHub: {e}")
        repos = []

    conn = sqlite3.connect(DB_PATH)

    if not repos:
        print("\n[FALLBACK] Seeding known cbeta_refs into existing rows...")
        for text_id, cbeta_ref in KNOWN_CBETA_REFS.items():
            row = conn.execute(
                "SELECT id FROM kanripo_catalog WHERE text_id=?", (text_id,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE kanripo_catalog SET cbeta_ref=? WHERE text_id=?",
                    (cbeta_ref, text_id)
                )
                print(f"  Updated {text_id} → cbeta_ref={cbeta_ref}")
        conn.commit()
        conn.close()
        return

    print(f"\n[2] Upserting {len(repos)} repos...")
    inserted, updated, skipped = upsert_repos(conn, repos, dry_run=args.dry_run)

    if not args.dry_run:
        total = conn.execute("SELECT COUNT(*) FROM kanripo_catalog").fetchone()[0]
        crossrefs = conn.execute(
            "SELECT COUNT(*) FROM kanripo_catalog WHERE cbeta_ref != '' AND cbeta_ref IS NOT NULL"
        ).fetchone()[0]
        print(f"\n[3] Results:")
        print(f"  Inserted: {inserted}")
        print(f"  Updated:  {updated}")
        print(f"  Total in kanripo_catalog: {total}")
        print(f"  Rows with cbeta_ref: {crossrefs}")

        print("\n[4] Sample rows:")
        for row in conn.execute(
            "SELECT text_id, title_zh, category, cbeta_ref FROM kanripo_catalog "
            "WHERE cbeta_ref != '' ORDER BY text_id LIMIT 10"
        ).fetchall():
            print(f"  {row}")

    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    main()
