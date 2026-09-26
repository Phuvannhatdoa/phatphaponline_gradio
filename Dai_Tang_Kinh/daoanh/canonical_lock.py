# ──────────────────────────────────────────────────────────────────────
# Canonical Lock Module (T166)
# SSOT identity guard for Vietnamese Buddhist person names
# ────────────────────────────────────────────────────────────────────

import re
import hashlib
import sqlite3
import unicodedata
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple


# ---------------------------------------------------------------------------
# Dataclass for canonical lock entries
# ---------------------------------------------------------------------------

@dataclass
class CanonicalLockEntry:
    source_form: str
    normalized_form: str
    entity_type: str
    canonical_id: str
    canonical_value: str
    authority_source: str
    authority_level: float
    status: str
    claims: List[Any]


# ---------------------------------------------------------------------------
# Policy class for canonical lock rules
# ---------------------------------------------------------------------------

class Policy:
    """Policy rules for canonical lock validation."""
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 20
    ALLOWED_COMMON_WORDS = {'thích', 'trà', 'uống', 'tôi', 'bạn', 'người', 'thầy', 'cô', 'chú', 'bác'}
    INVENTION_SEVERITY = 'HARD'
    MOJIBAKE_SEVERITY = 'HARD'


# Policy unknown (SPEC §4) — cấu hình được, mặc định P-PARTIAL
POLICY_PARTIAL = 'P-PARTIAL'   # vẫn call LLM, chỉ gắn cờ
POLICY_STOP = 'P-STOP'         # KHÔNG call LLM → REVIEW_REQUIRED

# Giá trị cột `translation_rules.identity_lock_policy` (Phase 3 migration)
VALID_POLICIES = (POLICY_PARTIAL, POLICY_STOP)


# ---------------------------------------------------------------------------
# Title words to strip from VI names (honorific/buddhist titles as PREFIXES only)
# Compound titles like "Hòa Thượng", "Thiền Sư" are part of names, not stripped
# ---------------------------------------------------------------------------

_TITLE_WORDS = (
    'thích', 'thích ca', 'ca', 'ngài', 'trưởng lão', 'bhikkhu', 'bhikkhuni',
    'samanera', 'samaneri', 'đại sư', 'pháp', 'giác', 'huệ', 'trí', 'tuệ',
    'triết', 'đạo', 'nghệ', 'nghiệm', 'ứng', 'chứng', 'thần', 'thánh', 'hiền',
)

_PUNCT_RE = re.compile(r'[\s\W]+', re.UNICODE)
_HAN_RE = re.compile(r'[\u4e00-\u9fff]+')


# ---------------------------------------------------------------------------
# normalize_vi: strip honorific titles, NFC, casefold, strip punctuation
# ---------------------------------------------------------------------------

def normalize_vi(s: str) -> str:
    """Normalize VI for compare: strip honorific titles, NFC, casefold, strip punct."""
    if not s:
        return ''
    s = s.strip()
    # Repeatedly strip titles from start until no more matches
    # This handles "Thích Ca Đơn Hà" -> strip "Thích" -> "Ca Đơn Hà" -> strip "Ca" -> "Đơn Hà"
    changed = True
    while changed:
        changed = False
        for title in _TITLE_WORDS:
            pattern = rf'^{re.escape(title)}\s+'
            if re.match(pattern, s, re.IGNORECASE):
                s = re.sub(pattern, '', s, flags=re.IGNORECASE)
                changed = True
                break  # restart from first title
    # NFC normalize + casefold
    s = unicodedata.normalize('NFC', s).casefold()
    # Strip punctuation/space
    s = _PUNCT_RE.sub('', s)
    return s


# ---------------------------------------------------------------------------
# extract_maximal_han_runs: extract maximal Han runs ≥2 chars from text
# ---------------------------------------------------------------------------

def extract_maximal_han_runs(text: str) -> list[str]:
    """Extract maximal Han runs ≥2 chars from text.
    Không n-gram chồng lấp, chỉ chuỗi Hán liên tục dài nhất.
    Cap ~40 runs/prompt (SPEC §3.2).
    """
    if not text:
        return []
    runs = _HAN_RE.findall(text)
    # Filter ≥2 chars, unique, keep order of first appearance
    seen = set()
    maximal = []
    for run in runs:
        if len(run) >= 2 and run not in seen:
            seen.add(run)
            maximal.append(run)
    return maximal[:40]


# ---------------------------------------------------------------------------
# is_valid_vi: validate if text is proper Vietnamese
# ---------------------------------------------------------------------------

def is_valid_vi(text: str) -> bool:
    """Check if text is valid Vietnamese (contains VI chars after stripping titles)."""
    if not text:
        return False
    # Strip "Thích" title
    s = re.sub(r'(?:^|[，。；，\.!?])\s*([Tt]hích)\s+', '', text, flags=re.IGNORECASE)
    if not s.strip():
        return False
    # After stripping title, should have content
    normalized = normalize_vi(s)
    return len(normalized) > 0 and not normalized.isascii()


# ---------------------------------------------------------------------------
# _check_canonical_invention: detect invented person-like VI names
# ---------------------------------------------------------------------------

def _check_canonical_invention(output: str, lock: list[CanonicalLockEntry],
                                allowed_by_entity: dict) -> list[dict]:
    """CANONICAL_INVENTION (SPEC §6) — tên người hóa-dạng-VI trong output
    KHÔNG thuộc allowed_vi_set của bất kỳ entity nào trong lock.
    Dùng chung _extract_personlike_vi (case-sensitive + vị trí title + allowlist).
    """
    issues: list[dict] = []
    rendered = _extract_personlike_vi(output)
    if not rendered:
        return issues

    # Gom toàn bộ biến thể VI hợp lệ (mọi entity trong lock)
    all_allowed: set[str] = set()
    for vi_set in (allowed_by_entity or {}).values():
        for a in vi_set:
            if a:
                all_allowed.add(a)
    for e in (lock or []):
        if e.canonical_value:
            all_allowed.add(normalize_vi(e.canonical_value))
        for c in (e.claims or []):
            v = c.get('canonical_value') if isinstance(c, dict) else None
            if v:
                all_allowed.add(normalize_vi(v))
    # Title suffix ("Đại sư", "Hòa Thượng") là từ chức vị, không phải tên
    for t in ('đạisư', 'hòathượng', 'thiềnsư', 'trưởnglão', 'ngài', 'thích'):
        all_allowed.add(t)

    # Severity: chỉ HARD khi lock có ít nhất 1 entry LOCKED (authority thật).
    # Nếu lock chỉ có CANDIDATE/UNKNOWN → WARN: theo SPEC §3.1
    # "name_vi_auto / auto_transliterate / local_translate (conf 0.5–0.7)
    #  → CANDIDATE (không LOCK, **không HARD_FAIL khi LLM khác** — vào hàng
    #  đợi admin_namevi_queue để human duyệt)" và §6.3 hàng 4
    # "flag CANONICAL_INVENTION **cảnh báo** → draft only".
    has_locked = any(e.status == 'LOCKED' for e in (lock or []))
    severity = 'HARD' if has_locked else 'WARN'

    for name in rendered:
        if _phrase_matches_any_allowed(name, all_allowed):
            continue
        norm = normalize_vi(name)
        if not norm:
            continue
        issues.append({
            'code': 'CANONICAL_INVENTION',
            'severity': severity,
            'detected': name,
            'message': f'Tên người tự sáng tạo không có trong authority: {name}',
        })
    return issues


# ---------------------------------------------------------------------------
# _check_canonical_mismatch: CANONICAL_IDENTITY_MISMATCH (SPEC §6)
# ---------------------------------------------------------------------------

# Entity type nào HARD_FAIL khi mismatch; BUDDHIST_TERM 1-char chỉ WARN
_HARD_MISMATCH_TYPES = frozenset({'PERSON', 'PLACE', 'DHARMA_NAME', 'TEMPLE',
                                  'DYNASTY', 'ERA', 'LINEAGE'})

# Bảng chữ cái Việt — dựng character-class TỰ ĐỘNG theo case thật.
#
# ⚠️ KHÔNG dùng range thô:
#   - `À-Ỹ` (U+00C0–U+1EF9) chứa CẢ chữ thường (đ=U+0111, ă=U+0103) → nuốt
#     hết lowercase ("Hòa Thượng An Lẫm đến đây" bị parse thành tên dài).
#   - Liệt kê tay thì THIẾU chữ có dấu (à á ả ã ạ ầ ế ử …).
# ⇒ Sinh class từ 2 khối Unicode tiếng Việt + lọc `.isupper()`/`.islower()`.
_VN_BASE = 'AĂÂBCDĐEÊGHIKLMNOÔƠPQRSTUƯVXY'


def _build_vn_class(upper: bool) -> str:
    """Character-class chữ cái Việt (đủ dấu) theo case yêu cầu.
    ⚠️ Phải cover TỚI U+01FF vì Ơ = U+01A0, Ư = U+01AF (nằm ngoài
    Latin Extended-A U+017F) — thiếu chúng thì "Đơn" chỉ match "Đơ".
    ⚠️ Phải BẮT ĐẦU từ U+0041 để có chữ ASCII n/a/y/... — bắt đầu ở U+00C0
    thì "Đơn" chỉ match "Đơ" (thiếu 'n').
    """
    chars: list[str] = []
    for lo, hi in ((0x0041, 0x024F),   # ASCII + Latin-1 + Ext-A + Ext-B (Ơ Ư)
                   (0x1EA0, 0x1EF8)):  # Latin Extended Additional (dấu VI)
        for cp in range(lo, hi + 1):
            ch = chr(cp)
            if ch.isalpha() and ch.isupper() == upper:
                chars.append(ch)
    for ch in _VN_BASE:
        if (ch.isupper() == upper) and ch not in chars:
            chars.append(ch)
    return ''.join(re.escape(c) for c in chars)


_VN_UP = _build_vn_class(True)
_VN_LO = _build_vn_class(False)


# Honorific VI — CASE-SENSITIVE (title-case) để "tôi thích trà" không khớp
# ("thích" viết thường ≠ "Thích" danh xưng). SPEC §20.2 #12.
#
# ⚠️ Vị trí: KHÔNG bắt buộc đầu câu — trong văn dịch "Thích X" thường đứng
# sau giới từ ("là Thích X", "do Thích X"). Bộ lọc thật sự là:
#   (1) honorific đúng case  +  (2) tên phía sau viết HOA (proper noun)
#   +  (3) tên đó không phải từ thường.
_TITLE_PREFIX_RE = re.compile(
    r'\b(Thích Ca|Thích|ngài|Ngài|Hòa Thượng|Thiền Sư|Đại sư|Trưởng lão)'
    r'\s+'
    r'((?:[' + _VN_UP + r'][' + _VN_LO + r']*)'
    r'(?:\s+[' + _VN_UP + r'][' + _VN_LO + r']*)*)'
)
# Honorific mơ hồ — sau nó có thể là từ thường ("tôi thích ăn", "thích trà")
# ⇒ cần lọc từ thường. Còn "Đại sư / Thiền Sư / Hòa Thượng / Trưởng lão"
# gần như LUÔN đi kèm tên riêng ("Đại sư Pháp Vân") ⇒ không lọc.
_AMBIGUOUS_TITLES = frozenset({'Thích', 'Thích Ca', 'ngài', 'Ngài'})
# Từ thường có thể đứng sau title trong câu đời thường (SPEC §20.2 #12)
_COMMON_AFTER_TITLE = frozenset({
    'trà', 'uống', 'ăn', 'làm', 'nói', 'xem', 'nghe', 'đi', 'lại', 'thế',
    'vậy', 'rất', 'nhiều', 'ít', 'thật', 'rồi', 'chưa', 'được', 'phải',
    'tôi', 'bạn', 'chúng', 'tăng', 'pháp', 'mà', 'và', 'hoặc', 'nhưng',
    'học', 'tu', 'giảng', 'dạy', 'thọ', 'sống', 'chết', 'làm', 'hiện',
})
# Từ chức vị đứng TRONG tên (bỏ khi so subsequence) — không phải tên riêng
_TITLE_TOKENS = frozenset({
    'hòa', 'thượng', 'thiền', 'sư', 'đại', 'trưởng', 'lão', 'ngài',
    'thích', 'ca', 'tôn', 'đại', 'đạo',
})


def _extract_personlike_vi(output: str) -> list[str]:
    """Trích các cụm tên-người-hóa-dạng-VI trong output.
    Case-sensitive honorific + proper-noun viết HOA + loại từ thường.
    Trả về list[str] (giữ nguyên honorific trong cụm, vd "Hòa Thượng An Lẫm").
    """
    found: list[str] = []
    for m in _TITLE_PREFIX_RE.finditer(output or ''):
        title = m.group(1) or ''
        name = (m.group(2) or '').strip()
        if not name:
            continue
        # (3) Chỉ lọc từ thường cho honorific mơ hồ ("Thích ăn", "thích trà")
        if title in _AMBIGUOUS_TITLES:
            words = name.split()
            if words[0].lower() in _COMMON_AFTER_TITLE:
                continue
            if len(words) == 1 and words[0].lower() in _COMMON_AFTER_TITLE:
                continue
        found.append(name)
    return found


def _phrase_matches_any_allowed(phrase: str, allowed: set[str]) -> bool:
    """True nếu BẤT KỲ subsequence liên tiếp của `phrase` (sau khi bỏ từ
    chức vị) khớp một giá trị trong `allowed`.
    Xử lý "Hòa Thượng An Lẫm" vs canonical "An Lẫm" (tên chức vị đứng trong tên).
    """
    if not phrase:
        return False
    # Bỏ từ chức vị, giữ lại các từ còn lại
    core = [w for w in phrase.split() if w.lower() not in _TITLE_TOKENS]
    if not core:
        core = phrase.split()
    n = len(core)
    for i in range(n):
        for j in range(i + 1, n + 1):
            sub = ' '.join(core[i:j])
            norm = normalize_vi(sub)
            if norm and norm in allowed:
                return True
    # So cả cụm (trường hợp không có từ chức vị nào bị lọc)
    if normalize_vi(phrase) in allowed:
        return True
    return False


def _allowed_vi_by_source_form(lock: list[CanonicalLockEntry]) -> dict[str, set[str]]:
    """Gom MỌI biến thể VI đã biết theo `source_form` (bỏ entity_type).
    Fix false HARD_FAIL khi cùng 1 Hán có nhiều entity class:
    `少林寺` → term "chùa Thiếu Lâm" (LOCKED) + place "Thiếu Lâm Tự".
    SPEC §3.4: allowed_vi_set = mọi biến thể VI đã biết của entity đó.
    """
    out: dict[str, set[str]] = {}
    for e in lock:
        if not e.source_form:
            continue
        bucket = out.setdefault(e.source_form, set())
        if e.canonical_value:
            bucket.add(normalize_vi(e.canonical_value))
        for c in (e.claims or []):
            v = c.get('canonical_value') if isinstance(c, dict) else None
            if v:
                bucket.add(normalize_vi(v))
    return out


def _check_canonical_mismatch(output: str, lock: list[CanonicalLockEntry]) -> list[dict]:
    """CANONICAL_IDENTITY_MISMATCH (SPEC §6).

    ⚠️ Trigger đúng (sửa mâu thuẫn §6 vs §6.3):
      §6 ghi "match_by_maximal_han_run(output, entry.source_form)" nhưng §6.3
      lại đòi output THUẦN TIẾNG VIỆT ("Thích Đơn Hà Mật") → HARD_FAIL.
      Output dịch không chứa Hán ⇒ trigger theo Han-run trong output VÔ DỤNG.
      ⇒ Trigger đúng: Hán CÓ trong **source** (lock build từ source ⇒ chắc chắn),
        và output có render tên (person-like VI) — thì tên đó PHẢI là biến thể
        hợp lệ của entry. Không render gì ⇒ không có gì để so ⇒ không flag
        (tránh false fail khi dịch đoạn văn bỏ qua tên).
    """
    issues: list[dict] = []
    if not output or not lock:
        return issues

    rendered = _extract_personlike_vi(output)
    allowed_by_sf = _allowed_vi_by_source_form(lock)
    out_norm = normalize_vi(output)

    for e in lock:
        if e.status != 'LOCKED' or not e.source_form or not e.canonical_value:
            continue
        variants = allowed_by_sf.get(e.source_form) or set()
        # Đã chứa 1 biến thể hợp lệ (kể cả alias của entity khác cùng Hán) → PASS
        if any(v and v in out_norm for v in variants):
            continue

        term_len1 = (e.entity_type == 'BUDDHIST_TERM' and len(e.source_form) < 2)

        if not rendered:
            # Output KHÔNG render tên nào. Không chứng minh được tên sai, nhưng
            # cũng không xác nhận được tên đúng ⇒ WARN (không HARD) để admin
            # duyệt, thay vì im lặng coi là pass/trusted.
            # (R4: unknown an toàn hơn invented "trông như đúng")
            if term_len1:
                continue
            issues.append({
                'code': 'LOCKED_NAME_NOT_RENDERED',
                'severity': 'WARN',
                'detected': e.source_form,
                'canonical_id': e.canonical_id,
                'entity_type': e.entity_type,
                'expected': e.canonical_value,
                'message': (f'{e.source_form} → canonical "{e.canonical_value}" '
                            f'({e.canonical_id}) không xuất hiện trong output'),
            })
            continue

        # Output CÓ render tên nhưng KHÔNG phải biến thể hợp lệ → LLM đã bịa
        # / đổi tên ⇒ HARD (trừ term 1-char chỉ WARN — SPEC §20.2 #11)
        hard = (e.entity_type in _HARD_MISMATCH_TYPES) or \
               (e.entity_type == 'BUDDHIST_TERM' and not term_len1)
        issues.append({
            'code': 'CANONICAL_IDENTITY_MISMATCH',
            'severity': 'HARD' if hard else 'WARN',
            'detected': e.source_form,
            'canonical_id': e.canonical_id,
            'entity_type': e.entity_type,
            'expected': e.canonical_value,
            'rendered': rendered,
            'message': (f'{e.source_form} → canonical bắt buộc "{e.canonical_value}" '
                        f'({e.canonical_id}) không xuất hiện trong output'),
        })
    return issues

def build_canonical_lock_candidate_person(source_text: str) -> CanonicalLockEntry:
    """Build a candidate person entry from source text."""
    # Extract name after "Thích"
    pattern = r'(?:^|[，。；，\.!?])\s*([Tt]hích)\s+([A-Za-zÀ-ÿ\u00c0-\u024f][A-Za-zÀ-ÿ\u00c9\u00cb-\u024f\'-]*)'
    name = ''
    for m in re.finditer(pattern, source_text, re.IGNORECASE):
        name = m.group(2).strip()
        if name:
            break
    # Compute normalized forms
    normalized_form = normalize_vi(source_text)
    # Derive canonical_value as the full name after "Thích"
    canonical_value = name if name else source_text
    # Entity type default to PERSON
    entity_type = 'PERSON'
    canonical_id = hashlib.sha256(normalized_form.encode('utf-8')).hexdigest()[:8]
    authority_source = 'name_vi_map.name_vi_final'
    authority_level = 0.7
    status = 'CANDIDATE'
    claims = []
    return CanonicalLockEntry(
        source_form=source_text,
        normalized_form=normalized_form,
        entity_type=entity_type,
        canonical_id=canonical_id,
        canonical_value=canonical_value,
        authority_source=authority_source,
        authority_level=authority_level,
        status=status,
        claims=claims,
    )


# ---------------------------------------------------------------------------
# build_canonical_lock_conflict: build conflict entries
# ---------------------------------------------------------------------------

def build_canonical_lock_conflict(entries: list[CanonicalLockEntry]) -> CanonicalLockEntry:
    """Build a conflict entry from existing entries."""
    # Find entries with same normalized_form but different canonical_value
    groups: dict[str, list[CanonicalLockEntry]] = {}
    for e in entries:
        groups.setdefault(e.normalized_form, []).append(e)
    conflicts = [g for g in groups.values() if len(g) > 1]
    if not conflicts:
        # Return first entry as-is if no conflict
        return entries[0] if entries else CanonicalLockEntry(
            source_form='', normalized_form='', entity_type='',
            canonical_id='', canonical_value='',
            authority_source='', authority_level=0.0, status='',
            claims=[]
        )
    # Return the first conflicting group's first entry as representative
    return conflicts[0][0]


# ---------------------------------------------------------------------------
# build_canonical_lock_glossary_term: build glossary term entry
# ---------------------------------------------------------------------------

def build_canonical_lock_glossary_term(term: str, definition: str) -> CanonicalLockEntry:
    """Build a glossary term entry."""
    normalized = normalize_vi(term)
    canonical_id = hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:8]
    return CanonicalLockEntry(
        source_form=term,
        normalized_form=normalized,
        entity_type='GLOSSARY',
        canonical_id=canonical_id,
        canonical_value=term,
        authority_source='glossary',
        authority_level=1.0,
        status='LOCKED',
        claims=[],
    )


# ---------------------------------------------------------------------------
# build_canonical_lock_locked_person: build locked person entry
# ---------------------------------------------------------------------------

def build_canonical_lock_locked_person(canonical_value: str, authority_level: float = 1.0) -> CanonicalLockEntry:
    """Build a locked person entry."""
    normalized = normalize_vi(canonical_value)
    canonical_id = hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:8]
    return CanonicalLockEntry(
        source_form=canonical_value,
        normalized_form=normalized,
        entity_type='PERSON',
        canonical_id=canonical_id,
        canonical_value=canonical_value,
        authority_source='name_vi_map.name_vi_final',
        authority_level=authority_level,
        status='LOCKED',
        claims=[],
    )


# ---------------------------------------------------------------------------
# build_canonical_lock_locked_place: build locked place entry
# ---------------------------------------------------------------------------

def build_canonical_lock_locked_place(canonical_value: str) -> CanonicalLockEntry:
    """Build a locked place entry."""
    normalized = normalize_vi(canonical_value)
    canonical_id = hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:8]
    return CanonicalLockEntry(
        source_form=canonical_value,
        normalized_form=normalized,
        entity_type='PLACE',
        canonical_id=canonical_id,
        canonical_value=canonical_value,
        authority_source='place_vi_map',
        authority_level=1.0,
        status='LOCKED',
        claims=[],
    )


# ---------------------------------------------------------------------------
# build_canonical_lock_mojibake_rejected: detect and reject mojibake
# ---------------------------------------------------------------------------

def build_canonical_lock_mojibake_rejected(text: str) -> bool:
    """Detect if text contains mojibake (double-encoded UTF-8)."""
    # Simple heuristic: if text contains replacement char or invalid sequences
    if '\ufffd' in text:  # Unicode replacement character
        return True
    # Check for double-encoded patterns (e.g., %C3%A9 instead of é)
    try:
        text.encode('utf-8').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return True
    return False


# ---------------------------------------------------------------------------
# build_lock_prompt_section: build the prompt lock section for T165
# ---------------------------------------------------------------------------

def build_lock_prompt_section(lock: list[CanonicalLockEntry]) -> str:
    """Build prompt lock section (SPEC T166 §5).
    Wording = CONSTRAINT, không phải "suggestion/hint/example".
    """
    if not lock:
        return ''
    locked = [e for e in lock if e.status == 'LOCKED']
    candidates = [e for e in lock if e.status == 'CANDIDATE']
    conflicts = [e for e in lock if e.status == 'CONFLICT']
    unknowns = [e for e in lock if e.status == 'UNKNOWN_REVIEW']

    L: list[str] = []
    L.append('=== LOCKED CANONICAL CONTEXT (BẮT BUỘC, KHÔNG ĐỔI) ===')
    if locked:
        for e in sorted(locked, key=lambda x: (x.entity_type, x.canonical_value)):
            L.append(f'{e.source_form} → {e.canonical_value}  '
                     f'[{e.entity_type} {e.canonical_id}]  authority={e.authority_source}')
    else:
        L.append('(không có mục nào)')
    L.append('')

    L.append('=== CANDIDATE (đề xuất máy, CHỈ ĐỀ XUẤT — không bắt buộc) ===')
    if candidates:
        for e in sorted(candidates, key=lambda x: (x.entity_type, x.canonical_value)):
            L.append(f'{e.source_form} → {e.canonical_value}  '
                     f'[{e.entity_type} {e.canonical_id}]  '
                     f'({e.authority_source}, level={e.authority_level})')
    else:
        L.append('(không có mục nào)')
    L.append('')

    L.append('=== CONFLICT (NGUỒN XUNG ĐỘT — KHÔNG tự chọn, giữ nguyên Hán) ===')
    if conflicts:
        for e in sorted(conflicts, key=lambda x: x.source_form):
            vals = ' | '.join(sorted({
                (c.get('canonical_value') or '') for c in (e.claims or [])
                if isinstance(c, dict) and c.get('canonical_value')
            }))
            L.append(f'{e.source_form}  [{e.entity_type} {e.canonical_id}]  '
                     f'claims: {vals or e.canonical_value}')
    else:
        L.append('(không có mục nào)')
    L.append('')

    L.append('=== UNKNOWN / REVIEW (GIỮ HÁN, KHÔNG SÁNG TÁC) ===')
    if unknowns:
        for e in sorted(unknowns, key=lambda x: x.source_form):
            L.append(e.source_form)
        L.append('→ Giữ nguyên Hán cho các tên ở mục này. KHÔNG tự đặt tên Việt.')
    else:
        L.append('(không có mục nào)')
    return '\n'.join(L)


# ---------------------------------------------------------------------------
# t166_lock_fingerprint: generate fingerprint for constitution_hash
# ---------------------------------------------------------------------------

def t166_lock_fingerprint(lock: list[CanonicalLockEntry]) -> str:
    """Generate fingerprint for constitution_hash.
    Only LOCKED entries contribute (sorted).
    Returns sha256[:16] or '' if no LOCKED.
    """
    locked = [e for e in lock if e.status == 'LOCKED']
    if not locked:
        return ''
    parts = []
    for e in sorted(locked, key=lambda x: x.normalized_form):
        parts.append(f"{e.normalized_form}:{e.canonical_value}:{e.entity_type}:{e.authority_source}")
    blob = '|'.join(parts).encode('utf-8')
    return hashlib.sha256(blob).hexdigest()[:16]


# ---------------------------------------------------------------------------
# pre_assert: pre-assertion check before adding to lock
# ---------------------------------------------------------------------------

def pre_assert(lock: list[CanonicalLockEntry], output: str = '',
               allowed_by_entity: Optional[dict] = None,
               policy: str = POLICY_PARTIAL) -> Tuple[str, list[dict]]:
    """Pre-assertion TRƯỚC khi gọi LLM (SPEC §5 bước 3).

    Trả về ('pass'|'review_required'|'failed', issues[]).

    Policy P-PARTIAL (mặc định): unknown/CONFLICT vẫn CHO gọi LLM, chỉ gắn cờ.
    Policy P-STOP (Admin flag)   : KHÔNG gọi LLM → REVIEW_REQUIRED.

    ⚠️ `UNCONTROLLED_PROPER_NAME` = token khớp authority nhưng CHƯA gán status
       (bug phân loại) → STOP Ở CẢ 2 policy (§4.1).
    """
    if allowed_by_entity is None:
        allowed_by_entity = _build_allowed_by_entity(lock)

    issues: list[dict] = []

    # §4.1 UNCONTROLLED_PROPER_NAME — có canonical_value nhưng status rỗng/lạ
    for e in (lock or []):
        if e.canonical_value and e.status not in (
                'LOCKED', 'CANDIDATE', 'CONFLICT', 'UNKNOWN_REVIEW'):
            issues.append({
                'code': 'UNCONTROLLED_PROPER_NAME',
                'severity': 'HARD',
                'detected': e.source_form,
                'message': (f'{e.source_form} khớp authority nhưng chưa phân loại '
                            f'(status={e.status!r}) — lỗi build lock'),
            })
    if issues:
        return 'failed', issues

    # Mojibake trong chính source/entry
    if build_canonical_lock_mojibake_rejected(output or ''):
        issues.append({'code': 'MOJIBAKE', 'severity': 'HARD',
                       'message': 'Phát hiện mojibake trong đầu vào'})
        return 'failed', issues

    # CONFLICT / UNKNOWN_REVIEW → gắn cờ (không chặn ở P-PARTIAL)
    n_conflict = sum(1 for e in (lock or []) if e.status == 'CONFLICT')
    n_unknown = sum(1 for e in (lock or []) if e.status == 'UNKNOWN_REVIEW')
    if n_conflict:
        issues.append({'code': 'CONFLICT', 'severity': 'WARN',
                       'message': f'{n_conflict} nguồn xung đột — không tự chọn, giữ Hán'})
    if n_unknown:
        issues.append({'code': 'UNKNOWN_REVIEW', 'severity': 'WARN',
                       'message': (f'{n_unknown} maximal Hán run chưa có authority '
                                   f'— giữ nguyên Hán, không sáng tác tên VI')})
    if issues and policy == POLICY_STOP:
        return 'failed', issues
    return ('review_required' if issues else 'pass'), issues


# ---------------------------------------------------------------------------
# post_assert: post-assertion check after adding to lock
# ---------------------------------------------------------------------------

def post_assert(lock: list[CanonicalLockEntry], output: str,
                 allowed_by_entity: Optional[dict] = None) -> Tuple[str, list[dict]]:
    """Post-assertion: check if output should be accepted or rejected.
    Trả về (identity_status, identity_issues[]) — SPEC §6:
      HARD (CANONICAL_IDENTITY_MISMATCH / CANONICAL_INVENTION / MOJIBAKE) → 'failed'
      WARN (TERM_LEN1_MISMATCH)                                          → 'review_required'
      không có issue                                                      → 'pass'
    """
    if allowed_by_entity is None:
        allowed_by_entity = _build_allowed_by_entity(lock)

    # 1. LOCKED mismatch (CANONICAL_IDENTITY_MISMATCH) — SPEC §6
    issues = _check_canonical_mismatch(output, lock)

    # 2. Invented person-like VI (CANONICAL_INVENTION) — SPEC §6
    issues += _check_canonical_invention(output, lock, allowed_by_entity)

    # 3. Mang cờ UNKNOWN_REVIEW / CONFLICT từ lock sang response (SPEC §4.1
    #    "P-PARTIAL: vẫn dịch + giữ Hán + flag"; §3.3 conflict → HITL).
    #    ⇒ identity_status='review_required' ⇒ cache KHÔNG trusted, serve DRAFT.
    n_unknown = sum(1 for e in (lock or []) if e.status == 'UNKNOWN_REVIEW')
    n_conflict = sum(1 for e in (lock or []) if e.status == 'CONFLICT')
    if n_unknown:
        issues.append({
            'code': 'UNKNOWN_REVIEW', 'severity': 'WARN',
            'message': (f'{n_unknown} maximal Hán run chưa có authority — '
                        f'giữ nguyên Hán, không sáng tác tên Việt'),
        })
    if n_conflict:
        issues.append({
            'code': 'CONFLICT', 'severity': 'WARN',
            'message': f'{n_conflict} nguồn xung đột — không tự chọn, route HITL',
        })

    # 4. Mojibake
    if build_canonical_lock_mojibake_rejected(output):
        issues.append({'code': 'MOJIBAKE', 'severity': 'HARD',
                       'message': 'Phát hiện mojibake trong output'})

    if not issues:
        return 'pass', []
    if any(i['severity'] == 'HARD' for i in issues):
        return 'failed', issues
    return 'review_required', issues


# ---------------------------------------------------------------------------
# t165_constitution_hash: generate constitution_hash for T165
# ---------------------------------------------------------------------------

def t165_constitution_hash(lock: list[CanonicalLockEntry]) -> str:
    """Generate constitution_hash for T165 from lock entries.
    Only LOCKED entries contribute, sorted by normalized_form.
    Returns sha256[:16] or '' if no LOCKED.
    """
    locked = [e for e in lock if e.status == 'LOCKED']
    if not locked:
        return ''
    parts = []
    for e in sorted(locked, key=lambda x: x.normalized_form):
        parts.append(f"{e.normalized_form}:{e.canonical_value}")
    blob = '|'.join(parts).encode('utf-8')
    return hashlib.sha256(blob).hexdigest()[:16]


# ---------------------------------------------------------------------------
# SOURCE_PRIORITY — SSOT duy nhất, dùng chung với _glossary_resolver
# (SPEC T166 §3.1 — sau review §20.2 #1/#2/#3/#4/#9/#16)
#
# Mức 1.0  = LOCKED  (chỉ khi có FLAG hợp lệ + is_valid_vi)
# Mức 0.95 = LOCKED  (vn_person_authority verified)
# Mức 0.9  = LOCKED  (namevi_map_places reviewed — chỉ 2 row thật)
# Mức 0.7  = CANDIDATE (auto confidence — KHÔNG bao giờ LOCK, bất kể entity)
# ---------------------------------------------------------------------------

SOURCE_LEVELS = {
    'canonical_decision.admin_approved': 1.0,
    'person_display_names.verified': 1.0,
    'person_name_correction.applied': 1.0,
    'translation_glossary.is_locked': 1.0,
    'name_vi_map.final+approved': 1.0,
    'name_vi_map.final': 0.9,
    'vn_person_authority.verified': 0.95,
    'namevi_map_places.reviewed': 0.9,
    # Auto / machine-chấm → CANDIDATE (SPEC §3.1 nguyên tắc lock)
    'name_vi_map.auto': 0.7,
    'namevi_map_places.auto': 0.7,
    'vn_person_authority.auto': 0.7,
    'canonical_decision.auto_transliterate': 0.7,
    'people.name_vi': 0.7,
}

LOCK_THRESHOLD = 1.0          # >= → LOCKED (fallback khi không có flag)
CANDIDATE_THRESHOLD = 0.0     # < LOCK_THRESHOLD nhưng có VI → CANDIDATE

# SPEC §3.1 "Nguyên tắc lock": LOCKED chỉ khi có FLAG hợp lệ —
# `verified / reviewed / applied / final+approved / admin_approved`.
# `authority_level` chỉ là RANK, KHÔNG phải điều kiện LOCK.
# (Nếu dùng level>=1.0 để LOCK thì vn_person_authority.verified=0.95
#  sẽ rơi xuống CANDIDATE → sai fixture A009460 §6.3/§14.)
_LOCK_FLAGS = frozenset({
    'canonical_decision.admin_approved',
    'person_display_names.verified',
    'vn_person_authority.verified',
    'person_name_correction.applied',
    'translation_glossary.is_locked',
    'name_vi_map.final+approved',
    'namevi_map_places.reviewed',
})


def is_lock_flagged(authority_source: str, authority_level: float) -> bool:
    """Quyết định LOCKED: ưu tiên FLAG, fallback level (config đổi được)."""
    if authority_source in _LOCK_FLAGS:
        return True
    return authority_level >= LOCK_THRESHOLD

# Thứ tự ưu tiên nguồn (cao → thấo). Cùng hằng này phải được _glossary_resolver đọc.
SOURCE_PRIORITY = (
    'canonical_decision',
    'person_display_names',
    'vn_person_authority',
    'person_name_correction',
    'translation_glossary',
    'name_vi_map',
    'namevi_map_places',
    'people',
)

_ENTITY_TYPE_BY_SOURCE = {
    'canonical_decision': 'PLACE',
    'person_display_names': 'PERSON',
    'vn_person_authority': 'PERSON',
    'person_name_correction': 'PERSON',
    'translation_glossary': 'BUDDHIST_TERM',
    'name_vi_map': 'PERSON',
    'namevi_map_places': 'PLACE',
    'people': 'PERSON',
}

_MAX_HAN_RUNS = 40           # SPEC §3.2 cap ~40 run/prompt


def _in_clause(n: int) -> str:
    """Sinh placeholder '?,?,?' cho SQL IN (n) — chống SQL injection."""
    return ','.join('?' * n)


def _query_all_sources(conn, han_runs: list[str]) -> list[tuple]:
    """Single batch query, UNION ALL 8 nguồn theo SOURCE_PRIORITY.
    Zero-RAM: chỉ truy vấn theo IN (han_runs), không load bảng lớn.
    Returns list of (source_form, canonical_value, canonical_id, entity_type,
                    authority_source, authority_level, source_table).
    """
    if not han_runs:
        return []
    n = len(han_runs)
    ph = _in_clause(n)
    params = list(han_runs)
    rows: list[tuple] = []

    def _safe(sql: str, args: list) -> list[tuple]:
        """Chạy query, nuốt lỗi schema (bảng/cột chưa tồn tại) → trả [].
        Zero-RAM + an toàn: thiếu bảng = nguồn chết, KHÔNG làm hỏng cả build.
        """
        try:
            cur = conn.execute(sql, args)
            return cur.fetchall()
        except sqlite3.Error:
            return []

    # #1 canonical_decision — join places_dila/people lấy name_zh làm source_form
    #     (entity_ref là ID PL…, không phải Hán — không join = nguồn chết)
    for r in _safe(
        f"""SELECT COALESCE(pd.name_zh, pj.name_zh, cd.entity_ref) AS sf,
                   cd.canonical_name_vi, cd.entity_ref,
                   cd.authority_rank, cd.confidence
            FROM canonical_decision cd
            LEFT JOIN places_dila pd ON pd.dila_id = cd.entity_ref
            LEFT JOIN people pj     ON pj.id = cd.entity_ref
            WHERE COALESCE(pd.name_zh, pj.name_zh) IN ({ph})
               OR cd.entity_ref IN ({ph})""",
        params + han_runs,
    ):
        sf, cvi, ref, rank, conf = r
        lvl = SOURCE_LEVELS.get(f'canonical_decision.{rank}', 0.7)
        if is_valid_vi(cvi or ''):
            rows.append((sf, cvi, ref or '', 'PLACE',
                         f'canonical_decision.{rank}', lvl, 'canonical_decision'))

    # #2 person_display_names — verification_status LIKE 'verified%' AND is_preferred=1
    for sf, cvi, pid in _safe(
        f"""SELECT COALESCE(display_name_zh, authority_name_zh) AS sf,
                   COALESCE(authority_name_vi, display_name_vi) AS cvi,
                   COALESCE(dila_person_id, person_id)
            FROM person_display_names
            WHERE verification_status LIKE 'verified%' AND is_preferred = 1
              AND COALESCE(display_name_zh, authority_name_zh) IN ({ph})""",
        list(han_runs),
    ):
        if is_valid_vi(cvi or ''):
            rows.append((sf, cvi, pid or '', 'PERSON',
                         'person_display_names.verified',
                         SOURCE_LEVELS['person_display_names.verified'],
                         'person_display_names'))

    # #3 vn_person_authority — status='verified'
    for sf, cvi, did in _safe(
        f"""SELECT name_zh, name_vi, dila_id FROM vn_person_authority
            WHERE status = 'verified' AND name_zh IN ({ph})""",
        list(han_runs),
    ):
        if is_valid_vi(cvi or ''):
            rows.append((sf, cvi, did or '', 'PERSON',
                         'vn_person_authority.verified',
                         SOURCE_LEVELS['vn_person_authority.verified'],
                         'vn_person_authority'))

    # #4 person_name_correction — status='applied'  (KHÔNG phải 'approved')
    for sf, cvi, pid in _safe(
        f"""SELECT name_zh, current_vi, person_id FROM person_name_correction
            WHERE status = 'applied' AND name_zh IN ({ph})""",
        list(han_runs),
    ):
        if is_valid_vi(cvi or ''):
            rows.append((sf, cvi, pid or '', 'PERSON',
                         'person_name_correction.applied',
                         SOURCE_LEVELS['person_name_correction.applied'],
                         'person_name_correction'))

    # #5 translation_glossary — is_locked=1 (term 1-char → CANDIDATE, không LOCK)
    for sf, cvi in _safe(
        f"""SELECT term_zh, term_vi FROM translation_glossary
            WHERE is_locked = 1 AND term_zh IN ({ph})""",
        list(han_runs),
    ):
        if is_valid_vi(cvi or ''):
            # SPEC §20.2 #11: term 1-char → severity WARN ở post_assert
            # (giữ flag is_locked để vẫn LOCK; severity tách riêng)
            rows.append((sf, cvi, '', 'BUDDHIST_TERM',
                         'translation_glossary.is_locked',
                         SOURCE_LEVELS['translation_glossary.is_locked'],
                         'translation_glossary'))

    # #6 name_vi_map — name_vi_final IS NOT NULL (authority) · approved_by = boost
    for sf, cvi, did, appr in _safe(
        f"""SELECT name_zh, name_vi_final, dila_id, approved_by FROM name_vi_map
            WHERE name_vi_final IS NOT NULL AND name_zh IN ({ph})""",
        list(han_runs),
    ):
        if is_valid_vi(cvi or ''):
            key = 'name_vi_map.final+approved' if appr else 'name_vi_map.final'
            rows.append((sf, cvi, did or '', 'PERSON', key,
                         SOURCE_LEVELS[key], 'name_vi_map'))

    # #6b name_vi_map — auto (name_vi_auto) → CANDIDATE, KHÔNG bao giờ LOCK
    for sf, cav in _safe(
        f"""SELECT name_zh, name_vi_auto FROM name_vi_map
            WHERE name_vi_auto IS NOT NULL AND name_vi_final IS NULL
              AND name_zh IN ({ph})""",
        list(han_runs),
    ):
        if is_valid_vi(cav or ''):
            rows.append((sf, cav, '', 'PERSON',
                         'name_vi_map.auto',
                         SOURCE_LEVELS['name_vi_map.auto'], 'name_vi_map'))

    # #7 namevi_map_places — vn_name_status='reviewed' (chỉ 2 row thật)
    for sf, cvi, did, conf in _safe(
        f"""SELECT name_zh, name_vi, dila_id, confidence FROM namevi_map_places
            WHERE vn_name_status = 'reviewed' AND name_zh IN ({ph})""",
        list(han_runs),
    ):
        if is_valid_vi(cvi or ''):
            rows.append((sf, cvi, did or '', 'PLACE',
                         'namevi_map_places.reviewed',
                         SOURCE_LEVELS['namevi_map_places.reviewed'],
                         'namevi_map_places'))

    # #8 people.name_vi — CHỈ provenance approved (default: KHÔNG lock)
    for sf, cvi, pid, origin in _safe(
        f"""SELECT name_zh, name_vi, id, source_origin FROM people
            WHERE name_vi IS NOT NULL AND name_zh IN ({ph})""",
        list(han_runs),
    ):
        if is_valid_vi(cvi or '') and (origin and 'approved' in str(origin).lower()):
            rows.append((sf, cvi, pid or '', 'PERSON',
                         'people.name_vi', SOURCE_LEVELS['people.name_vi'], 'people'))

    return rows


def _stable_id(entity_type: str, source_form: str) -> str:
    """canonical_id ổn định: DILA/PL id nếu có, ngược lại hash8 từ (type, source_form)."""
    if entity_type and source_form:
        return hashlib.sha256(
            f'{entity_type}:{source_form}'.encode('utf-8')
        ).hexdigest()[:8]
    return ''


def _apply_lock_threshold(entries: list[CanonicalLockEntry]) -> list[CanonicalLockEntry]:
    """Gán status theo SOURCE_LEVELS + flag LOCK_THRESHOLD.
    - level >= LOCK_THRESHOLD  → LOCKED
    - level <  LOCK_THRESHOLD  → CANDIDATE
    - CONFLICT nếu cùng (source_form, entity_type) mà >1 canonical_value khác nhau
    """
    if not entries:
        return []

    # Gom theo (source_form, entity_type)
    groups: dict[tuple, list[CanonicalLockEntry]] = {}
    for e in entries:
        groups.setdefault((e.source_form, e.entity_type), []).append(e)

    result: list[CanonicalLockEntry] = []
    for (sf, et), grp in groups.items():
        vi_values = {g.canonical_value for g in grp if g.canonical_value}
        if len(vi_values) > 1:
            # CONFLICT — giữ TẤT CẢ claims, KHÔNG auto-pick (SPEC §3.3)
            grp.sort(key=lambda x: (-x.authority_level,
                                     SOURCE_PRIORITY.index(x.authority_source.split('.')[0])
                                     if x.authority_source.split('.')[0] in SOURCE_PRIORITY
                                     else 99))
            top = grp[0]
            claims = [
                {'source_form': g.source_form,
                 'canonical_value': g.canonical_value,
                 'canonical_id': g.canonical_id,
                 'authority_source': g.authority_source,
                 'authority_level': g.authority_level}
                for g in grp
            ]
            result.append(CanonicalLockEntry(
                source_form=sf, normalized_form=unicodedata.normalize('NFC', sf or '').replace(' ', ''),
                entity_type=et, canonical_id=top.canonical_id or _stable_id(et, sf),
                canonical_value=top.canonical_value,
                authority_source=top.authority_source,
                authority_level=top.authority_level,
                status='CONFLICT', claims=claims,
            ))
            continue

        # Không conflict → sort theo priority rồi level, chọn best
        def _key(g: CanonicalLockEntry):
            tbl = g.authority_source.split('.')[0]
            pri = SOURCE_PRIORITY.index(tbl) if tbl in SOURCE_PRIORITY else 99
            return (pri, -g.authority_level)

        grp.sort(key=_key)
        best = grp[0]
        status = 'LOCKED' if is_lock_flagged(best.authority_source,
                                             best.authority_level) else 'CANDIDATE'
        # claims = các biến thể VI khác (alias) của cùng entity (SPEC §3.4)
        claims = [
            {'canonical_value': g.canonical_value,
             'authority_source': g.authority_source,
             'authority_level': g.authority_level}
            for g in grp if g.canonical_value and g.canonical_value != best.canonical_value
        ]
        result.append(CanonicalLockEntry(
            source_form=sf,
            normalized_form=unicodedata.normalize('NFC', sf or '').replace(' ', ''),
            entity_type=et,
            canonical_id=best.canonical_id or _stable_id(et, sf),
            canonical_value=best.canonical_value,
            authority_source=best.authority_source,
            authority_level=best.authority_level,
            status=status,
            claims=claims,
        ))
    return result


def build_canonical_lock(conn, source_text: str) -> list[CanonicalLockEntry]:
    """Build canonical lock per-request từ authority thật (SPEC T166 §3).

    Zero-RAM: chỉ query theo IN (maximal Han run ≤40), không load bảng lớn.
    Returns list[CanonicalLockEntry] (LOCKED / CANDIDATE / CONFLICT).
    """
    if not source_text:
        return []
    han_runs = extract_maximal_han_runs(source_text)[:_MAX_HAN_RUNS]
    if not han_runs:
        return []
    rows = _query_all_sources(conn, han_runs)

    entries: list[CanonicalLockEntry] = []
    matched: set[str] = set()
    for sf, cvi, cid, et, auth, lvl, _tbl in rows:
        if not sf or not cvi:
            continue
        matched.add(sf)
        entries.append(CanonicalLockEntry(
            source_form=sf,
            normalized_form=unicodedata.normalize('NFC', sf).replace(' ', ''),
            entity_type=et,
            canonical_id=cid or _stable_id(et, sf),
            canonical_value=cvi,
            authority_source=auth,
            authority_level=lvl,
            status='CANDIDATE',
            claims=[],
        ))
    resolved = _apply_lock_threshold(entries)

    # §3.2 UNMATCHED_CJK — maximal Han run ≥2 KHÔNG khớp authority nào.
    # → UNKNOWN_REVIEW: P-PARTIAL vẫn dịch nhưng GIỮ HÁN, KHÔNG bịa tên VI.
    #   (không n-gram chồng lấp, đã cap ~40 ở extract_maximal_han_runs)
    for run in han_runs:
        if run in matched:
            continue
        # run có chứa 1 source_form đã match không? (run dài hơn tên trong nó)
        if any(run.startswith(m) or m in run for m in matched):
            continue
        resolved.append(CanonicalLockEntry(
            source_form=run,
            normalized_form=unicodedata.normalize('NFC', run).replace(' ', ''),
            entity_type='UNKNOWN',
            canonical_id=_stable_id('UNKNOWN', run),
            canonical_value='',          # KHÔNG đề xuất tên VI (SPEC §3.2)
            authority_source='(no authority match)',
            authority_level=0.0,
            status='UNKNOWN_REVIEW',
            claims=[],
        ))
    return resolved


def _build_allowed_by_entity(lock: list[CanonicalLockEntry]) -> dict:
    """Build allowed_by_entity dict from lock entries for invention detection."""
    allowed: dict[str, set[str]] = {}
    for e in lock:
        if e.canonical_value and e.canonical_id:
            full_norm = normalize_vi(e.canonical_value)
            allowed.setdefault(e.canonical_id, set()).add(full_norm)
    return allowed


# ---------------------------------------------------------------------------
# translate_with_guard: wrapper dùng chung cho CẢ 3 đường dịch
# (SPEC §17 Coverage: app.py interactive · cbeta worker batch · admin/app.py mirror)
# ---------------------------------------------------------------------------

def translate_with_guard(conn, source_text: str, call_llm_fn,
                         policy: str = POLICY_PARTIAL) -> dict:
    """Bọc 1 lần gọi LLM bằng CanonicalLock hard-guard (pre + post assert).

    Args:
        conn:          sqlite3 connection (read-only dùng cho lookup authority)
        source_text:   text Hán gốc (chứa maximal Han run)
        call_llm_fn:   callable(prompt: str) -> str  — nhận prompt ĐÃ ghép lock section
        policy:        POLICY_PARTIAL (mặc định) | POLICY_STOP

    Returns dict:
        ok               : bool  — False khi bị chặn trước khi gọi LLM (P-STOP)
        output           : str   — text LLM trả về ('' nếu bị chặn)
        error_code       : str   — 'REVIEW_REQUIRED' khi bị chặn
        identity_status  : 'pass'|'review_required'|'failed'
        identity_issues  : list[dict]
        identity_lock_hash : str  — fingerprint (đưa vào constitution_hash)
        lock             : list[CanonicalLockEntry]  (debug/log)
    """
    if policy not in VALID_POLICIES:
        policy = POLICY_PARTIAL

    # 1) Build lock (Zero-RAM: SQL batch theo maximal Han run ≤40)
    lock = build_canonical_lock(conn, source_text)
    lock_hash = t166_lock_fingerprint(lock)

    # 2) Pre-assert + inject prompt section
    pre_status, pre_issues = pre_assert(lock, source_text, policy=policy)
    if pre_status == 'failed':
        return {
            'ok': False,
            'output': '',
            'error_code': 'REVIEW_REQUIRED',
            'identity_status': 'failed',
            'identity_issues': pre_issues,
            'identity_lock_hash': lock_hash,
            'lock': lock,
        }

    lock_section = build_lock_prompt_section(lock)
    prompt = f'{lock_section}\n\n{source_text}' if lock_section else source_text

    # 3) Call LLM (P-PARTIAL vẫn gọi; P-STOP đã return ở bước 2)
    try:
        output = call_llm_fn(prompt)
    except Exception as exc:                       # noqa: BLE001
        # Không để job batch chết vì lỗi LLM (SPEC §17 coverage ②)
        return {
            'ok': False,
            'output': '',
            'error_code': 'LLM_ERROR',
            'identity_status': 'failed',
            'identity_issues': [{'code': 'LLM_ERROR', 'severity': 'WARN',
                                 'message': f'{type(exc).__name__}: {exc}'}],
            'identity_lock_hash': lock_hash,
            'lock': lock,
        }
    output = output or ''

    # 4) Post-assert
    allowed = _build_allowed_by_entity(lock)
    identity_status, identity_issues = post_assert(lock, output, allowed)

    return {
        'ok': True,
        'output': output,
        'identity_status': identity_status,
        'identity_issues': identity_issues,
        'identity_lock_hash': lock_hash,
        'lock': lock,
    }


def post_check_translation(conn, source_text: str, output: str,
                           policy: str = POLICY_PARTIAL) -> dict:
    """Post-check 1 bản dịch ĐÃ sinh bởi prompt Style Constitution (T166 §6.3).

    Dùng cho integration với app.py: build_style_prompt đã nhúng identity block
    vào prompt (qua style_lock.t166_identity_lock), nên luồng này CHỈ cần
    post_assert trên output — không dựng prompt lại.

    Vẫn pre_assert nhẹ để bắt trường hợp P-STOP mà prompt chưa kịp chặn
    (VD source chỉ toàn UNKNOWN, model vẫn bịa tên — SPEC §6.4 #9).

    Args:
        conn:        sqlite3 connection (read-only lookup authority)
        source_text: text Hán gốc (chứa maximal Han run)
        output:      bản dịch LLM trả về
        policy:      POLICY_PARTIAL | POLICY_STOP

    Returns dict (giống translate_with_guard, không có 'lock'):
        ok                : bool  — False khi output bị chặn (pre hoặc post)
        output            : str
        error_code        : 'REVIEW_REQUIRED' khi bị chặn, None nếu ok
        identity_status   : 'pass'|'review_required'|'failed'
        identity_issues   : list[dict]
        identity_lock_hash: str
    """
    lock = build_canonical_lock(conn, source_text)
    lock_hash = t166_lock_fingerprint(lock)

    # Pre-assert còn sót (P-STOP nặng → chặn dù LLM đã chạy, tránh ghi non-lock)
    pre_status, pre_issues = pre_assert(lock, source_text, policy=policy)
    if pre_status == 'failed':
        return {
            'ok': False,
            'output': '',
            'error_code': 'REVIEW_REQUIRED',
            'identity_status': 'failed',
            'identity_issues': pre_issues,
            'identity_lock_hash': lock_hash,
        }

    allowed = _build_allowed_by_entity(lock)
    identity_status, identity_issues = post_assert(lock, output or '', allowed)
    blocked = identity_status == 'failed'

    return {
        'ok': not blocked,
        'output': output if not blocked else '',
        'error_code': 'REVIEW_REQUIRED' if blocked else None,
        'identity_status': identity_status,
        'identity_issues': identity_issues,
        'identity_lock_hash': lock_hash,
    }