# -*- coding: utf-8 -*-
"""
T74b — PILOT giai doan Gemini free (T266): dich thu bio nguoi (DILA, tieng Han)
sang tieng Viet bang Gemini free tier, gop 5 tieu su / 1 yeu cau, de Admin danh
gia chat luong truoc khi quyet dinh chuyen sang API tra phi (xem tasks/T266-*.md,
tasks/T74b-*.md).

QUAN TRONG — day la PILOT, khong phai batch chinh thuc:
- Chi SELECT tu data/lineage.db voi mode=ro (read-only o muc OS lan SQLite URI).
- KHONG ghi vao people.bio_vi hay person_bio_vi_draft hay bang nao khac cua DB.
- Ket qua nhap ghi vao file JSONL draft (mac dinh
  docs/evidence/<ngay>_T74b_pilot_gemini.jsonl), moi dong:
  {dila_id, name_zh, name_vi, dynasty, bio_han_truncated, bio_vi_draft,
   cjk_flag, model, char_in, char_out, ts}
- Chon 200 dong theo seed co dinh (random.Random(SEED).sample) tren danh sach
  id da sort -> lap lai duoc giua cac lan chay.
- Gemini API key doc tu GEMINI_API_KEY trong .env (khong in ra log/report).
- Goi tuan tu (khong song song), retry co han + backoff khi gap 429.
- Gop 5 tieu su / 1 yeu cau (BATCH_SIZE=5), moi tieu su danh so va co ma dinh
  danh [[ID:dila_id]] trong prompt. Phan hoi cua model duoc parse theo cung
  marker; ma nao thieu hoac khong khop trong phan hoi se duoc dua vao hang doi
  thu lai (retry_queue trong state file), KHONG gan nham tieu su cho ma khac.
- Co the tiep tuc (resume) neu bi ngat: dong da co trong file JSONL (theo
  dila_id) se duoc skip khi chay lai; trang thai luu trong
  docs/evidence/T74b_pilot_state.json (--state-file de doi duong dan). Viec
  tim "da xong" quet TAT CA file docs/evidence/*_T74b_pilot_gemini.jsonl (khong
  chi file cua ngay hom nay), vi ten file nhap doi theo ngay chay (T266 muc 1).
  Dong CU (truoc T266, thieu cjk_flag) -> se dich lai 1 lan (khong sua/xoa file
  cu) (T266 muc 2).
- Phan hoi Gemini duoc kiem tra candidates[0].finishReason. Neu khac 'STOP'
  (vd 'MAX_TOKENS' khi bi cat vi cham maxOutputTokens, hoac 'SAFETY'/
  'RECITATION'/'OTHER', hoac truong hop khong co candidates nao ca -- bi
  Gemini chan hoan toan, vd blockReason) thi ca batch do bi coi la LOI TAM:
  KHONG ghi draft cho bat ky ma nao trong batch, dua het vao retry_queue.
  TAT CA cac loai loi nay (nhan dien qua tien to 'finish_reason_', gia tri
  'max_tokens', hoac tien to 'no_candidates') deu dung CHUNG mot gioi han
  thu lai rieng, dem bang truong 'max_tokens_attempts' trong retry_queue
  (KHAC voi truong 'attempts' chung dung cho loi mang/HTTP, de 1 loi mang
  truoc do khong lam dila_id bi 'gave_up' ngay vi finishReason) (T266-fix4).
  Moi dila_id chi duoc thu lai toi da MAX_TOKENS_RETRY_LIMIT lan (hien tai =
  2) theo dem 'max_tokens_attempts'; qua so lan do se duoc ghi vao state la
  'gave_up' (kem reason = chuoi loi thuc te) va KHONG bao gio dua lai vao
  hang doi nua (tranh lap vo han) (T266-fix3, tong quat hoa o T266-fix4).
- Gioi han cung: toi da --max-requests YEU CAU HTTP THUC SU (ke ca retry do
  429/5xx/loi mang/not_json) trong MOT LAN CHAY (mac dinh 20, khong the vuot
  qua 20 du co truyen so lon hon -- xem MAX_REQUESTS_HARD_CAP). Dem theo tung
  request HTTP, khong theo so batch.
- API key gui qua header 'x-goog-api-key', KHONG nhung vao query string cua
  URL (tranh lo key vao log/state/error). Moi chuoi loi luu ra file (vd
  retry_queue.last_error) deu duoc che key truoc khi ghi.
- Neu gap loi 429 co quotaId theo ngay (GenerateRequestsPerDayPerProjectPerModel)
  -> dung sach ngay lap tuc, luu trang thai, in thong bao tieng Viet ro rang.
- Dung lai neu gap loi lap lai lien tuc (mac dinh 5 loi lien tiep).
- (T266-fix5 muc C) Khi 1 batch (5 tieu su) bi loi nhom finishReason/
  blockReason (MAX_TOKENS/SAFETY/RECITATION/OTHER/no_candidates), lan CHAY
  SAU (khi ma do da co max_tokens_attempts >= 1 trong retry_queue) se tach
  rieng CHI nhung ma do thanh batch 1-tieu-su de thu lai tung ma mot (xem
  build_batches_with_split). Ma moi/chua loi van gop 5/batch nhu cu (khong
  tach mac dinh).
- (T266-fix5 muc D) Ham aggregate_evidence() / co `--aggregate` tren CLI:
  doc TOAN BO file docs/evidence/*_T74b_pilot_gemini.jsonl, loai trung theo
  dila_id (giu dong CO cjk_flag uu tien hon dong khong co; cung nhom giu
  dong moi hon theo ts), in so lieu tong hop. KHONG ghi DB, KHONG ghi file.

Usage:
    python scripts/t74b_pilot_gemini_translate.py --dry-run
        # xem cac batch 5 tieu su se goi, khong goi API

    python scripts/t74b_pilot_gemini_translate.py --max-requests 20
        # chay toi da 20 yeu cau (= toi da 100 tieu su) trong lan nay (mac dinh)

    python scripts/t74b_pilot_gemini_translate.py --out <path.jsonl> --state-file <path.json>
        # chi dinh file nhap / file trang thai khac

    python scripts/t74b_pilot_gemini_translate.py --self-test
        # chay bo kiem thu noi bo bang phan hoi gia lap (mock), KHONG goi API thuc
"""
import json
import os
import random
import re
import sqlite3
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(BASE, '..')
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'lineage.db')
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

SEED = 20261008          # seed co dinh -> chon lai cung 200 dong moi lan chay
PILOT_SIZE = 200          # gioi han cung cua pilot nay, KHONG vuot
BATCH_SIZE = 5            # gop 5 tieu su / 1 yeu cau (T266 muc 2)
MAX_RETRIES = 3
MAX_CONSEC_ERRORS = 5
MAX_ID_RETRY_ATTEMPTS = 3   # 1 dila_id bi thieu/khong khop qua nhieu lan -> bao cao, khong tu dong bo qua vinh vien
MAX_TOKENS_RETRY_LIMIT = 2  # T266-fix3/fix4: 1 dila_id bi loi nhom finishReason/blockReason
                             # (MAX_TOKENS, SAFETY, RECITATION, OTHER, no_candidates) qua
                             # MAX_TOKENS_RETRY_LIMIT lan (dem rieng qua max_tokens_attempts)
                             # -> 'gave_up', khong dua lai vao hang doi.
SLEEP_OK = 6.5            # ~9 RPM -- 2.2s (lan dau) van bi 429 lien tiep sau 10 request thanh
                          # cong, free tier gemini-3.8-flash co ve thap hon gia dinh ban dau.
SLEEP_AFTER_429 = 20.0
MODEL = 'gemini-3.8-flash'   # app.py dung 'gemini-3.6-flash' (chet, HTTP 404 "no longer
                              # available, dung models/gemini-3.8-flash") -- da test truc tiep
                              # (2026-10-08) xac nhan 3.8-flash tra 200, 3.6/2.5/2.0/1.5 deu 404.
GEMINI_URL_TMPL = (
    'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
)   # KHONG nhung key vao query string nua -- key gui qua header x-goog-api-key (T266 loi 3)
BIO_TRUNCATE_FOR_DRAFT = 300   # chi luu bio Han da cat ngan trong file nhap, khong luu full

MAX_REQUESTS_HARD_CAP = 20     # T266 muc 5: gioi han cung, khong duoc vuot du CLI truyen gi
DEFAULT_MAX_REQUESTS = 20

# Nhan dien chu Han (CJK Unified Ideographs + mo rong thuong gap) de cam co,
# KHONG dung de loai bo ban dich.
CJK_RE = re.compile(r'[一-鿿㐀-䶿豈-﫿]')

# Marker bao quanh ma dinh danh trong prompt va trong phan hoi mong doi.
ID_MARKER_RE = re.compile(r'\[\[ID:([^\]]+)\]\]')

try:
    import requests
except Exception:
    requests = None


# Che moi chuoi dang 'key=...' (truong hop con lai tu URL/response cua Google
# vo tinh echo lai) truoc khi luu vao state/log (T266 loi 3).
SECRET_KEY_QS_RE = re.compile(r'(key=)[^&\s"\'\\]+', re.IGNORECASE)


def mask_secrets(text, key=None):
    """Che gia tri key thuc (neu biet) va moi pattern 'key=...' trong chuoi,
    dung truoc khi ghi bat ky chuoi loi nao ra file/log."""
    if not text:
        return text
    masked = text
    if key:
        masked = masked.replace(key, '***')
    masked = SECRET_KEY_QS_RE.sub(r'\1***', masked)
    return masked


class RequestCounter:
    """Dem SO YEU CAU HTTP THUC SU da goi trong 1 lan chay (ke ca retry do
    429/5xx/loi mang/not_json), de gioi han cung --max-requests ap dung dung
    nghia 'yeu cau HTTP', khong phai 'batch' (T266 loi 4)."""
    def __init__(self, limit):
        self.limit = limit
        self.count = 0

    def can_request(self):
        return self.count < self.limit

    def consume(self):
        self.count += 1


def load_env(path):
    """doc .env don gian (KEY=VALUE), khong phu thuoc python-dotenv de giam bien so."""
    env = {}
    if not os.path.isfile(path):
        return env
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def resolve_gemini_key():
    key = os.environ.get('GEMINI_API_KEY')
    if key:
        return key
    env = load_env(ENV_PATH)
    return env.get('GEMINI_API_KEY', '')


PROMPT_HEADER = (
    'Dich cac doan tieu su Phat hoc sau sang tieng Viet hoc thuat.\n'
    'Dung phien am Han-Viet chuan cho ten rieng. Giu nguyen nam thang, so lieu, '
    'ky hieu tong phai. Van phong trang trong, suc tich.\n\n'
    'QUY TAC TRA LOI BAT BUOC:\n'
    '- Co dung {n} tieu su duoi day, moi tieu su bat dau bang mot dong rieng ghi ma '
    'dinh danh (dinh dang giu nguyen y nhu trong de bai, xem vi du ngay duoi), giu '
    'nguyen ma nay, khong dich, khong doi ky tu nao trong ma.\n'
    '- Tra loi lai DUNG {n} dong ma dinh danh theo dung thu tu va dung dinh dang nhu '
    'de bai da cho, moi dong ma theo sau boi ban dich tuong ung voi tieu su do.\n'
    '- Khong gop, khong bo sot, khong them tieu su nao khac ngoai {n} ma da cho.\n'
    '- Chi tra ve ban dich cho moi muc, khong them loi ban, khong dung Han tu, '
    'khong dung JSON hay the markdown.\n\n'
)


def build_batch_prompt(items):
    """items: list of (dila_id, name_zh, dynasty, bio) -> prompt gop BATCH_SIZE tieu su."""
    parts = [PROMPT_HEADER.format(n=len(items))]
    for dila_id, name_zh, dynasty, bio in items:
        parts.append(f'[[ID:{dila_id}]]\n')
        parts.append(f'Nhan vat: {name_zh or ""} ({dynasty or ""})\n')
        parts.append(f'{bio or ""}\n\n')
    return ''.join(parts)


def parse_batch_response(text, expected_ids):
    """
    Tach phan hoi theo marker [[ID:xxx]] -> dict {dila_id: ban_dich}.
    Chi tra ve cac ma THUC SU co trong expected_ids va co noi dung khong rong;
    khong bao gio gan noi dung cua mot ma cho ma khac (tranh gan nham).
    """
    result = {}
    if not text:
        return result
    expected_set = set(expected_ids)
    matches = list(ID_MARKER_RE.finditer(text))
    for idx, m in enumerate(matches):
        found_id = m.group(1).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if found_id not in expected_set:
            # Ma la nhung khong thuoc batch nay (model bi lech) -> bo qua, khong gan nham.
            continue
        if not content:
            continue
        if found_id in result:
            # Trung ma trong phan hoi -> giu ban dau tien, khong de gan de len (tranh nham lan).
            continue
        result[found_id] = content
    return result


class ApiResult:
    def __init__(self, text=None, error=None, rate_limited=False, daily_quota_exceeded=False,
                 quota_id=None, attempts_used=1, finish_reason=None):
        self.text = text
        self.error = error
        self.rate_limited = rate_limited
        self.daily_quota_exceeded = daily_quota_exceeded
        self.quota_id = quota_id
        # So yeu cau HTTP THUC SU da tieu ton de tao ra ket qua nay (ke ca
        # retry). Mock (self-test) khong goi HTTP thuc nen de mac dinh = 1,
        # tuong duong 1 "luot goi" trong thong ke (T266 loi 4).
        self.attempts_used = attempts_used
        # candidates[0].finishReason cua Gemini (T266-fix3). None khi khong
        # xac dinh duoc (vd mock cu, hoac loi truoc khi co response). run_pilot
        # ghi lai gia tri nay vao JSONL ('STOP' neu thieu) de kiem sau.
        self.finish_reason = finish_reason


def _is_finish_reason_class_error(error):
    """T266-fix4: nhan dien loi thuoc nhom finishReason/blockReason (vd
    'max_tokens', 'finish_reason_safety', 'finish_reason_recitation',
    'finish_reason_other', hoac 'no_candidates...' khi Gemini chan ca cau
    tra loi). Cac loi nay chiu CUNG mot gioi han thu lai rieng
    (MAX_TOKENS_RETRY_LIMIT, dem qua 'max_tokens_attempts'), KHAC voi loi
    mang/HTTP thong thuong (http_error, rate_limit_429, not_json, ...) --
    truoc T266-fix4 chi 'max_tokens' duoc xu ly rieng, cac gia tri khac
    (SAFETY/RECITATION/OTHER/khong co candidates) roi vao nhanh loi chung
    KHONG co gioi han, co the lap vo han."""
    if not error:
        return False
    return (error == 'max_tokens'
            or error.startswith('finish_reason_')
            or error.startswith('no_candidates'))


def _extract_full_text(data):
    """Noi TOAN BO cac parts cua candidate dau tien, khong chi parts[0] (T266 muc 1)."""
    cands = data.get('candidates')
    if not cands:
        return None
    content = cands[0].get('content') or {}
    parts = content.get('parts') or []
    texts = [p.get('text', '') for p in parts if isinstance(p, dict) and p.get('text')]
    if not texts:
        return None
    return ''.join(texts).strip()


def _extract_finish_reason(data):
    """Doc candidates[0].finishReason (T266-fix3). Tra ve None neu khong co
    candidates hoac khong co truong nay (khong suy dien)."""
    cands = data.get('candidates')
    if not cands:
        return None
    return cands[0].get('finishReason')


def _detect_daily_quota(resp_text):
    """
    Phat hien 429 do het han muc THEO NGAY (quotaId co 'PerDay'), phan biet voi
    429 tam thoi (vi du rate limit theo phut) de biet luc nao can dung sach
    hoan toan thay vi chi backoff roi thu lai.
    """
    if not resp_text:
        return False, None
    m = re.search(r'"quotaId"\s*:\s*"([^"]+)"', resp_text)
    if m and 'PerDay' in m.group(1):
        return True, m.group(1)
    if 'GenerateRequestsPerDayPerProjectPerModel' in resp_text:
        return True, 'GenerateRequestsPerDayPerProjectPerModel'
    return False, None


def call_gemini(key, model, prompt, counter):
    """counter: RequestCounter dung chung cho CA lan chay (khong rieng cho batch
    nay), de gioi han --max-requests dem dung so yeu cau HTTP THUC SU, ke ca
    retry (T266 loi 4). Key gui qua header x-goog-api-key, khong qua query
    string (T266 loi 3)."""
    if not requests:
        return ApiResult(error='requests_not_available', attempts_used=0)
    url = GEMINI_URL_TMPL.format(model=model)
    headers = {'x-goog-api-key': key, 'Content-Type': 'application/json'}
    body = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 4096, 'temperature': 0.1},
    }
    last_err = 'unknown'
    attempts_used = 0
    for attempt in range(MAX_RETRIES + 1):
        if not counter.can_request():
            last_err = 'request_budget_exhausted'
            break
        counter.consume()
        attempts_used += 1
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=90)
        except Exception as e:
            last_err = mask_secrets(f'http_error: {e}', key)
            if attempt < MAX_RETRIES and counter.can_request():
                time.sleep(2 * (2 ** attempt))
            continue
        if resp.status_code == 429:
            is_daily, quota_id = _detect_daily_quota(resp.text)
            if is_daily:
                return ApiResult(error='rate_limit_429_daily', rate_limited=True,
                                  daily_quota_exceeded=True, quota_id=quota_id,
                                  attempts_used=attempts_used)
            last_err = 'rate_limit_429'
            if attempt < MAX_RETRIES and counter.can_request():
                time.sleep(SLEEP_AFTER_429 * (attempt + 1))
            continue
        if resp.status_code != 200:
            last_err = mask_secrets(f'HTTP {resp.status_code}: {resp.text[:200]}', key)
            if attempt < MAX_RETRIES and counter.can_request():
                time.sleep(2 * (2 ** attempt))
            continue
        try:
            data = resp.json()
        except Exception:
            last_err = 'not_json'
            continue
        text = _extract_full_text(data)
        finish_reason = _extract_finish_reason(data)
        if finish_reason and finish_reason != 'STOP':
            # Bi cat ngang (vd MAX_TOKENS) -> KHONG dung ket qua nay du co text
            # hay khong (ban dich co the bi cat giua cau). Khong retry lai ngay
            # trong cung HTTP call (prompt dai nhu cu se lai bi cat) -- de
            # run_pilot dua vao retry_queue/gave_up qua cac lan chay khac nhau
            # (T266-fix3).
            kind = 'max_tokens' if finish_reason == 'MAX_TOKENS' else f'finish_reason_{finish_reason.lower()}'
            return ApiResult(error=kind, attempts_used=attempts_used, finish_reason=finish_reason)
        if text:
            return ApiResult(text=text, attempts_used=attempts_used, finish_reason=finish_reason or 'STOP')
        last_err = mask_secrets(f'no_candidates: {str(data)[:200]}', key)
        break
    rate_limited = last_err in ('rate_limit_429',)
    return ApiResult(error=mask_secrets(last_err, key), rate_limited=rate_limited,
                      attempts_used=attempts_used)


SELECT_SQL = """
SELECT id, name_zh, name_vi, dynasty, bio
FROM people
WHERE bio IS NOT NULL
  AND LENGTH(bio) > 80
  AND bio NOT GLOB '*http*'
  AND source_origin = 'DILA'
  AND (bio_vi IS NULL OR bio_vi = '')
ORDER BY id
"""


def select_pilot_rows(con, n=PILOT_SIZE):
    rows = con.execute(SELECT_SQL).fetchall()
    ids_sorted = [r[0] for r in rows]
    by_id = {r[0]: r for r in rows}
    rnd = random.Random(SEED)
    chosen_ids = sorted(rnd.sample(ids_sorted, min(n, len(ids_sorted))))
    return [by_id[i] for i in chosen_ids]


# Dau cau ket thuc cau hop le cho mot ban dich tieng Viet. GIU LAI hang so nay
# chi de tham khao/doc, KHONG con dung de quyet dinh "chua xong" nua (T266-fix2,
# daoanh-qa phat hien): tieu su DILA thuong ket thuc hop le bang nhieu ky tu
# khac ngoai danh sach nay (vd （…）, 。, 」, 》, …, chu so), nen dung heuristic
# nay cho CA dong moi se bien dong moi thanh "chua xong" va bi dich lai mai,
# ton han muc Gemini mien phi.
_SENTENCE_END_CHARS = ('.', '!', '?', ')', '"', '”', '»', ':', ';')


def _is_legacy_incomplete(obj):
    """
    CHI coi la CHUA xong (can dich lai) khi dong THIEU truong cjk_flag hoan
    toan -- tuc la dong CU tu truoc T266, luc script con chua ghi truong nay.
    Day la hanh vi duy nhat con lai (T266-fix2 muc 1+2): dong cu thieu
    cjk_flag van duoc dua vao hang doi dich lai MOT LAN (de bo sung cjk_flag),
    KHONG kiem tra dau cau ket cau nua.

    Dong da CO truong cjk_flag (du gia tri True hay False) duoc coi la DA
    XONG, BAT KE ky tu cuoi cua ban dich -- ap dung cho ca dong cu da duoc
    dich lai lan 1 (co cjk_flag) va dong moi tu dau. Day chinh la co che chong
    lap vo han: 1 dila_id da co ban nhap moi (co cjk_flag) se khong bao gio bi
    dua lai vao hang doi chi vi ky tu cuoi "khong hop heuristic" (T266-fix2
    muc 3) -- vi dieu kien duy nhat de coi "chua xong" la THIEU han truong
    cjk_flag, ma mot khi da dich lai lan 1 thi truong nay luon duoc ghi.

    KHONG sua/xoa file cu, chi dung de loc khi doc lai (T266 loi 2, lua chon
    "danh dau logic khi doc" thay vi sua/xoa file cu -- it rui ro nhat vi
    khong dong vao du lieu da ghi).
    """
    return 'cjk_flag' not in obj


def load_done_ids(path):
    """Doc 1 file JSONL, tra ve set dila_id duoc coi la DA XONG (bo qua dong
    cu khong day du theo _is_legacy_incomplete)."""
    done = set()
    if not os.path.isfile(path):
        return done
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            dila_id = obj.get('dila_id')
            if not dila_id:
                continue
            if _is_legacy_incomplete(obj):
                continue
            done.add(dila_id)
    return done


EVIDENCE_GLOB_SUFFIX = '_T74b_pilot_gemini.jsonl'


def gather_done_ids_all_evidence(out_path, verbose=False):
    """
    Quet TAT CA file *_T74b_pilot_gemini.jsonl trong thu muc cua out_path (vi
    ten file nhap doi theo ngay chay -> khong the chi doc file cua hom nay,
    T266 loi 1), hop voi out_path chinh no (de van dung voi --out tuy chinh
    khong theo dung pattern ten, vd trong self-test). Dong cu khong day du bi
    loai theo load_done_ids/_is_legacy_incomplete (T266 loi 2).
    """
    folder = os.path.dirname(os.path.abspath(out_path)) or '.'
    pattern = os.path.join(folder, f'*{EVIDENCE_GLOB_SUFFIX}')
    try:
        import glob as _glob
        glob_matches = _glob.glob(pattern)
    except Exception:
        glob_matches = []
    # Chuan hoa duong dan truoc khi dua vao set, vi glob tra duong dan tuyet
    # doi con out_path co the la duong dan khac dang (tuong doi, '..', hoa/
    # thuong khac) -- neu khong chuan hoa, CUNG MOT FILE se bi doc 2 LAN va
    # dem gap doi so dong (ca "da xong" va "legacy_skipped").
    files = {os.path.normcase(os.path.abspath(p)) for p in glob_matches}
    files.add(os.path.normcase(os.path.abspath(out_path)))
    # map lai ve duong dan thuc (abspath cua out_path/glob) de mo file dung.
    real_paths = {os.path.normcase(os.path.abspath(p)): os.path.abspath(p) for p in glob_matches}
    real_paths[os.path.normcase(os.path.abspath(out_path))] = os.path.abspath(out_path)
    files = {real_paths[k] for k in files}

    done = set()
    n_legacy_skipped = 0
    for fp in sorted(files):
        if not os.path.isfile(fp):
            continue
        with open(fp, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                dila_id = obj.get('dila_id')
                if not dila_id:
                    continue
                if _is_legacy_incomplete(obj):
                    n_legacy_skipped += 1
                    continue
                done.add(dila_id)
    if verbose and n_legacy_skipped:
        print(f'  (Resume) {n_legacy_skipped} dong CU (truoc T266, thieu cjk_flag) -> '
              f'se dich lai 1 lan (khong sua/xoa file cu).')
    return done, n_legacy_skipped


DEFAULT_STATE_PATH = os.path.join(PROJECT_ROOT, 'docs', 'evidence', 'T74b_pilot_state.json')


def load_state(path):
    if not os.path.isfile(path):
        return {
            'seed': SEED, 'model': MODEL, 'retry_queue': {}, 'gave_up': {}, 'quota_exhausted': None,
            'stats_total': {'n_success': 0, 'n_error': 0, 'n_429': 0, 'n_cjk_flagged': 0,
                             'n_requests': 0},
            'last_run_ts': None,
        }
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return {
                'seed': SEED, 'model': MODEL, 'retry_queue': {}, 'gave_up': {}, 'quota_exhausted': None,
                'stats_total': {'n_success': 0, 'n_error': 0, 'n_429': 0, 'n_cjk_flagged': 0,
                                 'n_requests': 0},
                'last_run_ts': None,
            }


def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def build_batches_with_split(pending_ids, retry_queue):
    """T266-fix5 muc C: gop 5/batch theo mac dinh, nhung 1 dila_id da TUNG bi
    loi nhom finishReason/blockReason (max_tokens_attempts >= 1 trong
    retry_queue, nghia la lan truoc no nam trong 1 batch bi tran token) thi
    LAN NAY duoc tach rieng thanh batch 1 tieu su, de thu lai tung ma mot
    (khong bi ca 1 batch lon lam hong ca nhung ma dich duoc).
    CHI tach khi batch da LOI (co max_tokens_attempts >= 1); ma con lai (moi/
    chua loi) van gop theo BATCH_SIZE nhu cu (khong tach mac dinh)."""
    retry_queue = retry_queue or {}
    singles_needed = [pid for pid in pending_ids
                       if (retry_queue.get(pid) or {}).get('max_tokens_attempts', 0) >= 1]
    singles_set = set(singles_needed)
    grouped_pending = [pid for pid in pending_ids if pid not in singles_set]
    return list(chunk(grouped_pending, BATCH_SIZE)) + [[pid] for pid in singles_needed]


def aggregate_evidence(evidence_dir, verbose=True):
    """T266-fix5 muc D: doc TOAN BO file *_T74b_pilot_gemini.jsonl trong
    evidence_dir, loai trung theo dila_id (giu dong CO truong cjk_flag uu
    tien hon dong KHONG co; trong cung nhom co/khong co cjk_flag, giu dong co
    'ts' MOI HON). KHONG ghi gi vao DB hay file nao -- chi tra ve so lieu +
    dict ket qua trong RAM de admin/script khac tu quyet dinh dung lam gi."""
    import glob as _glob
    pattern = os.path.join(evidence_dir, f'*{EVIDENCE_GLOB_SUFFIX}')
    files = sorted(_glob.glob(pattern))
    best = {}
    n_lines = 0
    n_dup_skipped = 0
    n_bad_json = 0
    for fp in files:
        with open(fp, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    n_bad_json += 1
                    continue
                n_lines += 1
                did = obj.get('dila_id')
                if not did:
                    continue
                prev = best.get(did)
                if prev is None:
                    best[did] = obj
                    continue
                n_dup_skipped += 1
                prev_has_cjk = 'cjk_flag' in prev
                cur_has_cjk = 'cjk_flag' in obj
                if cur_has_cjk and not prev_has_cjk:
                    best[did] = obj
                elif cur_has_cjk == prev_has_cjk:
                    # cung nhom co/khong co cjk_flag -> giu ban MOI HON theo ts
                    # (chuoi rong coi la cu nhat, so sanh chuoi ISO ts hop le).
                    if (obj.get('ts') or '') >= (prev.get('ts') or ''):
                        best[did] = obj
                # else: cur khong co cjk_flag nhung prev co -> giu prev, khong lam gi.
    n_unique = len(best)
    n_cjk_flagged = sum(1 for o in best.values() if o.get('cjk_flag'))
    result = {
        'files': files, 'n_files': len(files), 'n_lines': n_lines,
        'n_bad_json': n_bad_json, 'n_unique': n_unique,
        'n_dup_skipped': n_dup_skipped, 'n_cjk_flagged': n_cjk_flagged,
        'unique': best,
    }
    if verbose:
        print('=== TONG HOP EVIDENCE T74b (T266-fix5 muc D, KHONG ghi DB) ===')
        print(f'  So file *{EVIDENCE_GLOB_SUFFIX} quet duoc: {result["n_files"]}')
        for fp in files:
            print(f'    - {os.path.basename(fp)}')
        print(f'  Tong so dong doc duoc: {n_lines} (loi json: {n_bad_json})')
        print(f'  So dila_id DUY NHAT sau loai trung: {n_unique}')
        print(f'  So dong trung bi loai (giu 1, bo cac dong con lai): {n_dup_skipped}')
        print(f'  Trong ban giu lai, co chu Han sau dich (cjk_flag=True): {n_cjk_flagged}')
    return result


def compute_dry_run(con, out_path, state_path, limit, verbose=False):
    """T266-fix4 muc 3: dung chung cho --dry-run va self-test. KHONG goi API,
    KHONG ghi gi -- chi doc DB (select_pilot_rows), doc evidence JSONL da co
    (gather_done_ids_all_evidence) va doc state (load_state) de tru luon cac
    ma da 'gave_up' ra khoi danh sach can dich (truoc fix4, dry-run khong doc
    state nen van dem ca ma da gave_up vao so 'can dich', gay nham lan)."""
    pilot_rows = select_pilot_rows(con, limit)
    done_ids, n_legacy_skipped = gather_done_ids_all_evidence(out_path, verbose=verbose)
    state = load_state(state_path)
    gave_up = state.get('gave_up') or {}
    retry_queue = state.get('retry_queue') or {}
    pending_ids = [r[0] for r in pilot_rows if r[0] not in done_ids and r[0] not in gave_up]
    batches = build_batches_with_split(pending_ids, retry_queue)
    return {
        'pilot_rows': pilot_rows,
        'done_ids': done_ids,
        'n_legacy_skipped': n_legacy_skipped,
        'gave_up': gave_up,
        'retry_queue': retry_queue,
        'pending_ids': pending_ids,
        'batches': batches,
    }


def run_pilot(con, out_path, state_path, max_requests, call_fn, limit=PILOT_SIZE, verbose=True,
              sleep_fn=time.sleep):
    """
    Logic chinh, tach rieng call_fn (goi API thuc hoac mock) de co the don vi
    test ma khong goi API thuc (T266 - kiem thu khong ton han muc).
    Tra ve dict thong ke cua lan chay nay.
    """
    pilot_rows = select_pilot_rows(con, limit)
    by_id = {r[0]: r for r in pilot_rows}
    if verbose:
        print(f'Pilot T74b (Gemini free tier) · seed={SEED} · chon {len(pilot_rows)}/{limit} dong '
              f'(trong tong eligible) · model={MODEL} · batch={BATCH_SIZE}')

    done_ids, _n_legacy_skipped = gather_done_ids_all_evidence(out_path, verbose=verbose)
    state = load_state(state_path)
    retry_queue = state.get('retry_queue') or {}
    gave_up = state.setdefault('gave_up', {})

    # Neu lan truoc da bi het han muc theo ngay cung ngay hom nay -> dung ngay, khong goi them.
    qexh = state.get('quota_exhausted')
    today_str = datetime.now().strftime('%Y-%m-%d')
    if qexh and qexh.get('date') == today_str:
        if verbose:
            print('DUNG: da ghi nhan het han muc Gemini THEO NGAY hom nay '
                  f'({qexh.get("quota_id")}). Khong goi them, doi sang hom sau.')
        return {'n_success': 0, 'n_error': 0, 'n_429': 0, 'n_requests': 0,
                'n_cjk_flagged': 0, 'stopped_reason': 'daily_quota_already_exhausted_today'}

    if done_ids and verbose:
        print(f'Resume: {len(done_ids)} dong da co trong {out_path}, se skip.')
    if retry_queue and verbose:
        print(f'Resume: {len(retry_queue)} ma dang trong hang doi thu lai (retry_queue).')

    # Danh sach can dich = (pilot rows chua co draft) hop (id trong retry_queue con duoi nguong).
    # Id da 'gave_up' (vuot MAX_TOKENS_RETRY_LIMIT lan finishReason != STOP) KHONG
    # duoc dua lai vao hang doi nua (T266-fix3), tranh goi API vo ich.
    pending_ids = [r[0] for r in pilot_rows if r[0] not in done_ids and r[0] not in gave_up]
    # dam bao id trong retry_queue nhung khong con trong pilot_rows (vd doi seed) thi bo qua.
    pending_ids = [pid for pid in pending_ids if pid in by_id]
    if gave_up and verbose:
        print(f'Resume: {len(gave_up)} ma da "gave_up" (vuot {MAX_TOKENS_RETRY_LIMIT} lan '
              'finishReason != STOP), khong thu lai nua.')

    # T266-fix5 muc C: ma da tung bi loi finishReason/blockReason trong 1
    # batch (max_tokens_attempts >= 1) duoc tach rieng thanh batch 1 tieu su
    # o lan chay nay, de thu lai tung ma mot thay vi ca batch lon. Ma moi/
    # chua loi van gop 5/batch nhu cu (khong tach mac dinh).
    batches = build_batches_with_split(pending_ids, retry_queue)
    max_requests = min(max_requests, MAX_REQUESTS_HARD_CAP)
    # KHONG cat batches theo so luong batch nua: 1 batch co the ton NHIEU hon
    # 1 yeu cau HTTP thuc su do retry (429/5xx/loi mang/not_json). Gioi han
    # thuc su ap dung qua RequestCounter (dem tung request HTTP) ben duoi
    # (T266 loi 4). Danh sach batches chi can mot chan tren hop ly de khong
    # lap vo ich khi het pending_ids.
    counter = RequestCounter(max_requests)

    n_success = n_error = n_429 = n_cjk = n_requests = 0
    consec_errors = 0
    total_char_in = total_char_out = 0
    stopped_reason = None
    t_start = time.time()

    with open(out_path, 'a', encoding='utf-8') as fout:
        for batch_ids in batches:
            if not counter.can_request():
                stopped_reason = 'max_requests_reached'
                if verbose:
                    print(f'DUNG: da dat gioi han {max_requests} yeu cau HTTP (ke ca retry) '
                          'trong lan chay nay. Chay lai de tiep tuc (resume).')
                break

            items = [(pid, by_id[pid][1], by_id[pid][3], by_id[pid][4]) for pid in batch_ids]
            prompt = build_batch_prompt(items)
            res = call_fn(prompt, counter)
            used = res.attempts_used if res.attempts_used is not None else 1
            n_requests += used

            if res.error == 'request_budget_exhausted':
                stopped_reason = 'max_requests_reached'
                if verbose:
                    print(f'DUNG: da dat gioi han {max_requests} yeu cau HTTP (ke ca retry) '
                          'trong lan chay nay. Chay lai de tiep tuc (resume).')
                break

            if res.daily_quota_exceeded:
                n_429 += 1
                state['quota_exhausted'] = {
                    'date': today_str, 'quota_id': res.quota_id,
                    'ts': datetime.now().isoformat(timespec='seconds'),
                }
                if verbose:
                    print('DUNG SACH: Gemini bao het HAN MUC THEO NGAY '
                          f'(quotaId={res.quota_id}). Phai doi khoang 20 gio roi chay lai. '
                          'Da luu trang thai, khong mat tien do.')
                stopped_reason = 'daily_quota_exceeded'
                break

            if res.rate_limited:
                n_429 += 1

            if res.error and _is_finish_reason_class_error(res.error):
                # T266-fix3/fix4: finishReason != STOP (MAX_TOKENS, SAFETY,
                # RECITATION, OTHER) hoac khong co candidates (blockReason) ->
                # KHONG ghi draft cho bat ky ma nao trong batch. Dem RIENG
                # bang 'max_tokens_attempts' (khac 'attempts' chung cho loi
                # mang), de 1 loi mang truoc do khong lam gave_up som. Moi ma
                # chi duoc thu lai toi da MAX_TOKENS_RETRY_LIMIT lan theo dem
                # nay; qua nguong -> 'gave_up' (khong dua lai vao retry_queue).
                n_error += 1
                consec_errors += 1
                err_masked = mask_secrets(res.error[:200])
                if verbose:
                    print(f'  x batch {batch_ids}: finishReason/blockReason loi '
                          f'({err_masked}) -> khong ghi draft, dua vao retry_queue.')
                for pid in batch_ids:
                    entry = retry_queue.get(pid, {'attempts': 0, 'max_tokens_attempts': 0})
                    entry.setdefault('attempts', 0)
                    entry['attempts'] += 1
                    entry['max_tokens_attempts'] = entry.get('max_tokens_attempts', 0) + 1
                    entry['last_error'] = err_masked
                    entry['last_ts'] = datetime.now().isoformat(timespec='seconds')
                    if entry['max_tokens_attempts'] >= MAX_TOKENS_RETRY_LIMIT:
                        gave_up[pid] = {
                            'reason': err_masked, 'attempts': entry['max_tokens_attempts'],
                            'last_ts': entry['last_ts'],
                        }
                        retry_queue.pop(pid, None)
                        if verbose:
                            print(f'  ! [{pid}] da thu lai {entry["max_tokens_attempts"]} lan vi '
                                  f'finishReason/blockReason ({err_masked}) -> gave_up, khong '
                                  'dua lai vao hang doi.')
                    else:
                        retry_queue[pid] = entry
                if consec_errors >= MAX_CONSEC_ERRORS:
                    if verbose:
                        print(f'DUNG: {MAX_CONSEC_ERRORS} loi lien tiep, dung pilot de tranh '
                              'lang phi quota.')
                    stopped_reason = 'max_consec_errors'
                    break
                sleep_fn(SLEEP_OK)
                continue

            if res.error:
                n_error += 1
                consec_errors += 1
                if verbose:
                    print(f'  x batch {batch_ids}: loi {mask_secrets(res.error[:120])}')
                for pid in batch_ids:
                    entry = retry_queue.get(pid, {'attempts': 0})
                    entry['attempts'] = entry.get('attempts', 0) + 1
                    # res.error da duoc mask_secrets() trong call_gemini, che lan nua
                    # cho chac (phong truong hop call_fn khac khong tu che) (T266 loi 3).
                    entry['last_error'] = mask_secrets(res.error[:200])
                    entry['last_ts'] = datetime.now().isoformat(timespec='seconds')
                    retry_queue[pid] = entry
                if consec_errors >= MAX_CONSEC_ERRORS:
                    if verbose:
                        print(f'DUNG: {MAX_CONSEC_ERRORS} loi lien tiep, dung pilot de tranh '
                              'lang phi quota.')
                    stopped_reason = 'max_consec_errors'
                    break
                sleep_fn(SLEEP_OK)
                continue

            consec_errors = 0
            batch_finish_reason = res.finish_reason or 'STOP'
            parsed = parse_batch_response(res.text, batch_ids)
            missing_ids = [pid for pid in batch_ids if pid not in parsed]

            for pid in missing_ids:
                entry = retry_queue.get(pid, {'attempts': 0})
                entry['attempts'] = entry.get('attempts', 0) + 1
                entry['last_error'] = 'missing_or_unmatched_id_in_response'
                entry['last_ts'] = datetime.now().isoformat(timespec='seconds')
                retry_queue[pid] = entry
                if verbose:
                    note = ''
                    if entry['attempts'] >= MAX_ID_RETRY_ATTEMPTS:
                        note = f' (da thu {entry["attempts"]} lan, can xem lai bang tay)'
                    print(f'  ! [{pid}] thieu/khong khop ma trong phan hoi -> hang doi thu lai{note}')

            for pid in batch_ids:
                if pid not in parsed:
                    continue
                bio_vi_draft = parsed[pid]
                row = by_id[pid]
                _, name_zh, name_vi, dynasty, bio = row
                cjk_flag = bool(CJK_RE.search(bio_vi_draft))
                if cjk_flag:
                    n_cjk += 1
                char_in = len(bio or '')
                char_out = len(bio_vi_draft or '')
                total_char_in += char_in
                total_char_out += char_out
                record = {
                    'dila_id': pid,
                    'name_zh': name_zh,
                    'name_vi': name_vi,
                    'dynasty': dynasty,
                    'bio_han_truncated': (bio or '')[:BIO_TRUNCATE_FOR_DRAFT],
                    'bio_vi_draft': bio_vi_draft,
                    'cjk_flag': cjk_flag,
                    'finish_reason': batch_finish_reason,
                    'model': MODEL,
                    'char_in': char_in,
                    'char_out': char_out,
                    'ts': datetime.now().isoformat(timespec='seconds'),
                }
                fout.write(json.dumps(record, ensure_ascii=False) + '\n')
                fout.flush()
                n_success += 1
                retry_queue.pop(pid, None)
                if verbose and (n_success <= 5 or n_success % 25 == 0):
                    flag_note = ' [CO CHU HAN]' if cjk_flag else ''
                    print(f'  ok [{n_success}] {pid} {name_vi} -> {bio_vi_draft[:70]}{flag_note}')

            sleep_fn(SLEEP_OK)

    elapsed = time.time() - t_start
    totals = state.setdefault('stats_total', {'n_success': 0, 'n_error': 0, 'n_429': 0,
                                                'n_cjk_flagged': 0, 'n_requests': 0})
    totals['n_success'] += n_success
    totals['n_error'] += n_error
    totals['n_429'] += n_429
    totals['n_cjk_flagged'] += n_cjk
    totals['n_requests'] += n_requests
    state['retry_queue'] = retry_queue
    state['last_run_ts'] = datetime.now().isoformat(timespec='seconds')
    state['seed'] = SEED
    state['model'] = MODEL
    save_state(state_path, state)

    if verbose:
        print('\n=== LAN CHAY NAY XONG ===')
        print(f'  File nhap: {out_path}')
        print(f'  File trang thai: {state_path}')
        print(f'  So yeu cau HTTP da goi: {n_requests} (gioi han {max_requests})')
        print(f'  Thanh cong: {n_success} · Loi: {n_error} · So lan 429: {n_429} · '
              f'Co chu Han sau dich: {n_cjk}')
        print(f'  Hang doi thu lai con lai: {len(retry_queue)} · Da "gave_up" (vuot '
              f'{MAX_TOKENS_RETRY_LIMIT} lan max_tokens): {len(gave_up)}')
        print(f'  Thoi gian: {elapsed/60:.1f} phut')
        print(f'  Ky tu dau vao (xap xi): {total_char_in:,} · dau ra: {total_char_out:,}')
        if stopped_reason:
            print(f'  Ly do dung: {stopped_reason}')

    return {
        'n_success': n_success, 'n_error': n_error, 'n_429': n_429, 'n_requests': n_requests,
        'n_cjk_flagged': n_cjk, 'stopped_reason': stopped_reason,
    }


# ---------------------------------------------------------------------------
# Self-test (mock) — T266: kiem thu KHONG goi API thuc, dung phan hoi gia lap.
# ---------------------------------------------------------------------------

def _consume_mock_budget(counter):
    """Mock khong goi HTTP thuc nhung VAN phai tieu 1 don vi tu counter dung
    chung, de --max-requests gioi han dung trong ca self-test (giong nhu
    call_gemini thuc se counter.consume() cho moi lan goi HTTP) (T266 loi 4)."""
    if counter is not None:
        counter.consume()


def _build_good_text(ids):
    """Dung chung cho cac mock tra loi 'dich thanh cong' -- tach rieng khoi
    _mock_good_response de tai su dung trong mock khac (vd T266-fix5 Test 20)
    ma KHONG goi _consume_mock_budget 2 lan."""
    parts_text = []
    for i in ids:
        parts_text.append(f'[[ID:{i}]]\nBan dich gia lap cho {i}.\n\n')
    return ''.join(parts_text)


def _mock_good_response(prompt, counter=None):
    """Mock tra loi dung dinh dang cho moi ma tim thay trong prompt."""
    _consume_mock_budget(counter)
    ids = ID_MARKER_RE.findall(prompt)
    return ApiResult(text=_build_good_text(ids))


def _mock_missing_one_response(prompt, counter=None):
    """Mock bo sot ma cuoi cung trong batch (test phat hien thieu ma)."""
    _consume_mock_budget(counter)
    ids = ID_MARKER_RE.findall(prompt)
    parts_text = []
    for i in ids[:-1]:
        parts_text.append(f'[[ID:{i}]]\nBan dich gia lap cho {i}.\n\n')
    return ApiResult(text=''.join(parts_text))


def _mock_cjk_response(prompt, counter=None):
    """Mock tra ve ban dich con lan chu Han (test co chu Han)."""
    _consume_mock_budget(counter)
    ids = ID_MARKER_RE.findall(prompt)
    parts_text = []
    for i in ids:
        parts_text.append(f'[[ID:{i}]]\nBan dich co lan chu 漢 con sot.\n\n')
    return ApiResult(text=''.join(parts_text))


def _mock_reversed_order_response(prompt, counter=None):
    """Mock tra ve cac ma theo thu tu DAO NGUOC so voi prompt -- test ghep
    dung noi dung theo ma, khong theo vi tri/thu tu (T266 muc nhe)."""
    _consume_mock_budget(counter)
    ids = ID_MARKER_RE.findall(prompt)
    parts_text = []
    for i in reversed(ids):
        parts_text.append(f'[[ID:{i}]]\nBan dich gia lap cho {i}.\n\n')
    return ApiResult(text=''.join(parts_text))


def _mock_max_tokens_response(prompt, counter=None):
    """Mock gia lap finishReason != STOP (vd MAX_TOKENS): tra ve loi 'max_tokens'
    (giong ket qua call_gemini se tra ve khi bi cat ngang), KHONG co text dung
    duoc -- dung de test run_pilot khong ghi draft + gioi han thu lai (T266-fix3)."""
    _consume_mock_budget(counter)
    return ApiResult(error='max_tokens', finish_reason='MAX_TOKENS')


def _mock_safety_response(prompt, counter=None):
    """T266-fix4 Test 17: mock gia lap finishReason='SAFETY' -- phai duoc xu
    ly bang CUNG gioi han thu lai nhu max_tokens (qua _is_finish_reason_class_error),
    KHONG roi vao nhanh loi chung khong gioi han."""
    _consume_mock_budget(counter)
    return ApiResult(error='finish_reason_safety', finish_reason='SAFETY')


def _make_mock_network_then_max_tokens():
    """T266-fix4 Test 18: lan goi DAU TIEN tra loi mang chung (khong lien quan
    finishReason), lan goi THU HAI (va cac lan sau) tra MAX_TOKENS -- dung de
    kiem tra 2 bo dem 'attempts' (chung) va 'max_tokens_attempts' (rieng)
    khong bi lam chung, tranh gave_up som chi vi co 1 loi mang truoc do."""
    state = {'calls': 0}

    def _mock(prompt, counter=None):
        _consume_mock_budget(counter)
        state['calls'] += 1
        if state['calls'] == 1:
            return ApiResult(error='http_error: ket noi tam thoi loi')
        return ApiResult(error='max_tokens', finish_reason='MAX_TOKENS')
    return _mock


def _make_mock_batch_maxtokens_then_singles_good():
    """T266-fix5 Test 20: batch nhieu hon 1 ma (vd 5) -> tra loi max_tokens
    (mo phong tran token khi gop 5 tieu su); nhung khi batch chi con 1 ma
    (tuc da bi build_batches_with_split tach rieng o lan chay sau) -> tra loi
    thanh cong binh thuong. Dung de kiem tra: lan 1 (batch 5) that bai ->
    khong ghi draft nao; lan 2 (5 batch don, sau khi max_tokens_attempts>=1)
    -> tung ma duoc goi rieng va thanh cong duoc ghi draft."""
    def _mock(prompt, counter=None):
        _consume_mock_budget(counter)
        ids = ID_MARKER_RE.findall(prompt)
        if len(ids) > 1:
            return ApiResult(error='max_tokens', finish_reason='MAX_TOKENS')
        return ApiResult(text=_build_good_text(ids))
    return _mock


def _make_mock_batch1_good_batch2_daily_quota():
    """T266-fix5 Test 22: lan goi DAU (batch 1, 5 ma) thanh cong; lan goi THU
    HAI (batch 2, 5 ma khac) het han muc theo ngay ngay lap tuc. Dung de mo
    phong 1 ngay chay bi dung giua duong (da dich xong 1 phan) vi het quota
    ngay, roi hom sau tiep tuc dich phan con lai (khong dich lai phan da
    xong)."""
    state = {'calls': 0}

    def _mock(prompt, counter=None):
        _consume_mock_budget(counter)
        state['calls'] += 1
        if state['calls'] == 1:
            ids = ID_MARKER_RE.findall(prompt)
            return ApiResult(text=_build_good_text(ids))
        return ApiResult(error='rate_limit_429_daily', rate_limited=True,
                          daily_quota_exceeded=True,
                          quota_id='GenerateRequestsPerDayPerProjectPerModel')
    return _mock


def _mock_daily_quota_response(prompt, counter=None):
    """Mock het han muc THEO NGAY ngay lap tuc (khong can goi HTTP thuc)."""
    _consume_mock_budget(counter)
    return ApiResult(error='rate_limit_429_daily', rate_limited=True,
                      daily_quota_exceeded=True, quota_id='GenerateRequestsPerDayPerProjectPerModel')


def _mock_fail_if_called(prompt, counter=None):
    """Dung de khang dinh KHONG duoc goi them lan nao (vd sau khi het han muc
    theo ngay, cung ngay khong duoc goi tiep) -- T266 'luong 429 theo ngay'."""
    raise AssertionError('call_fn khong duoc goi (da het han muc theo ngay hom nay)')


def _mock_split_parts_response(prompt):
    """
    Mock API thuc: tra ve nhieu 'parts' rieng le trong candidates[0].content.parts
    (mo phong truong hop Gemini cat response thanh nhieu parts) -- test noi parts.
    Ham nay khong di qua call_gemini (vi call_fn trong run_pilot nhan prompt->ApiResult
    truc tiep), nen test _extract_full_text duoc goi rieng o duoi.
    """
    raise NotImplementedError


class _FakeDB:
    """DB gia lap trong RAM dung chung schema voi select_pilot_rows, de self-test
    khong dong vao data/lineage.db thuc."""
    def __init__(self, n):
        self.rows = [
            (f'PL{1000+i:06d}', f'名{i}', f'Ten{i}', 'Duong', f'Day la tieu su chu Han so {i}. ' * 5)
            for i in range(n)
        ]

    def execute(self, sql):
        class _Cur:
            def __init__(self, rows):
                self._rows = rows

            def fetchall(self):
                return self._rows
        return _Cur(self.rows)


def _self_test():
    import tempfile
    results = []

    def check(name, cond, detail=''):
        results.append((name, bool(cond), detail))

    # --- Test 1: noi toan bo parts (khong chi parts[0]) ---
    data = {'candidates': [{'content': {'parts': [
        {'text': 'Phan dau. '}, {'text': 'Phan hai. '}, {'text': 'Phan ba.'}]}}]}
    full = _extract_full_text(data)
    check('noi_toan_bo_parts', full == 'Phan dau. Phan hai. Phan ba.', full)

    # --- Test 2: gop 5 tieu su / batch + parse dung du 5 ma, dung noi dung
    #     cho DUNG ma (khong chi "co mat", kiem tra thuc chat noi dung khop ma) ---
    items = [(f'PL{i:06d}', f'名{i}', 'Duong', f'bio {i}') for i in range(5)]
    prompt = build_batch_prompt(items)
    check('prompt_co_du_5_marker', len(ID_MARKER_RE.findall(prompt)) == 5,
          ID_MARKER_RE.findall(prompt))
    mock_res = _mock_good_response(prompt)
    parsed = parse_batch_response(mock_res.text, [it[0] for it in items])
    check('parse_du_5_ma', len(parsed) == 5, list(parsed.keys()))
    # kiem tra THUC SU: noi dung cua moi ma phai chua chinh ma do (mock nhung
    # co y nghia -- truoc day test nay co "or True" lam no luon PASS du sai).
    check('parse_dung_noi_dung',
          all(key in parsed[key] for key in parsed),
          {k: v for k, v in parsed.items()})

    # --- Test 3: thieu 1 ma -> khong gan nham, con lai 4, noi dung 4 ma con
    #     lai van dung cua chinh ma do (khong bi lech/gan nham do mat 1 vi tri) ---
    mock_missing = _mock_missing_one_response(prompt)
    parsed_missing = parse_batch_response(mock_missing.text, [it[0] for it in items])
    missing_ids = [it[0] for it in items if it[0] not in parsed_missing]
    check('phat_hien_thieu_1_ma', len(parsed_missing) == 4 and len(missing_ids) == 1, missing_ids)
    check('khong_gan_nham_cho_ma_khac',
          all(key in parsed_missing[key] for key in parsed_missing),
          {k: v for k, v in parsed_missing.items()})

    # --- Test 3b: ma tra ve theo thu tu DAO NGUOC so voi de bai -- van phai
    #     ghep dung noi dung theo MA, khong theo VI TRI/THU TU xuat hien ---
    mock_rev = _mock_reversed_order_response(prompt)
    parsed_rev = parse_batch_response(mock_rev.text, [it[0] for it in items])
    check('ma_dao_thu_tu_van_ghep_dung',
          len(parsed_rev) == 5 and all(key in parsed_rev[key] for key in parsed_rev),
          {k: v for k, v in parsed_rev.items()})

    # --- Test 3c: phan hoi co MA LA (khong nam trong batch nay) + 5 ma dung
    #     -> ma la bi bo qua, 5 ma dung khong bi anh huong ---
    text_with_stray = f'[[ID:PL999999]]\nNoi dung cua ma la, khong thuoc batch nay.\n\n' + mock_res.text
    parsed_stray = parse_batch_response(text_with_stray, [it[0] for it in items])
    check('bo_qua_ma_la_khong_thuoc_batch',
          'PL999999' not in parsed_stray and len(parsed_stray) == 5
          and all(key in parsed_stray[key] for key in parsed_stray),
          list(parsed_stray.keys()))

    # --- Test 3d: ma TRUNG trong phan hoi -> giu noi dung cua LAN DAU, khong
    #     de ban sau (co the la noi dung khac/sai) de len ban dau ---
    dup_id = items[0][0]
    text_with_dup = (f'[[ID:{dup_id}]]\nBan dau tien (phai giu lai).\n\n'
                      f'[[ID:{dup_id}]]\nBan thu hai (phai BI BO QUA).\n\n')
    parsed_dup = parse_batch_response(text_with_dup, [dup_id])
    check('ma_trung_giu_ban_dau',
          parsed_dup.get(dup_id) == 'Ban dau tien (phai giu lai).', parsed_dup.get(dup_id))

    # --- Test 4: co chu Han -> flag nhung khong loai bo ban dich ---
    mock_cjk = _mock_cjk_response(prompt)
    parsed_cjk = parse_batch_response(mock_cjk.text, [it[0] for it in items])
    any_cjk_flagged = any(CJK_RE.search(v) for v in parsed_cjk.values())
    check('danh_dau_cjk', any_cjk_flagged and len(parsed_cjk) == 5, '')
    check('khong_loai_bo_ban_dich_co_han',
          all(len(v.strip()) > 0 for v in parsed_cjk.values()), '')

    # --- Test 5: chay full run_pilot voi mock DB + mock call_fn, roi resume ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, 'test_pilot.jsonl')
        state_path = os.path.join(tmpdir, 'test_state.json')
        fake_con = _FakeDB(12)  # 12 dong -> 3 batch (5,5,2) voi BATCH_SIZE=5

        stats1 = run_pilot(fake_con, out_path, state_path, max_requests=2,
                            call_fn=_mock_good_response, limit=12, verbose=False,
                            sleep_fn=lambda s: None)
        check('run1_gioi_han_2_yeu_cau', stats1['n_requests'] == 2, stats1)
        check('run1_thanh_cong_10_dong', stats1['n_success'] == 10, stats1)

        done_after_run1 = load_done_ids(out_path)
        check('run1_ghi_dung_10_dong_vao_jsonl', len(done_after_run1) == 10, len(done_after_run1))

        # Resume: chay tiep, phai BO QUA 10 dong da xong, chi lam batch con lai (2 dong = 1 batch)
        stats2 = run_pilot(fake_con, out_path, state_path, max_requests=5,
                            call_fn=_mock_good_response, limit=12, verbose=False,
                            sleep_fn=lambda s: None)
        check('run2_resume_chi_con_1_batch', stats2['n_requests'] == 1, stats2)
        check('run2_them_2_dong', stats2['n_success'] == 2, stats2)

        done_after_run2 = load_done_ids(out_path)
        check('tong_12_dong_sau_resume', len(done_after_run2) == 12, len(done_after_run2))

        state_final = load_state(state_path)
        check('state_khong_con_retry_queue', len(state_final.get('retry_queue') or {}) == 0,
              state_final.get('retry_queue'))
        check('state_tong_thanh_cong_12',
              state_final.get('stats_total', {}).get('n_success') == 12,
              state_final.get('stats_total'))

    # --- Test 6: gioi han cung max-requests khong vuot 20 du truyen so lon hon ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, 'test_pilot2.jsonl')
        state_path = os.path.join(tmpdir, 'test_state2.json')
        fake_con2 = _FakeDB(200)
        stats3 = run_pilot(fake_con2, out_path, state_path, max_requests=999,
                            call_fn=_mock_good_response, limit=200, verbose=False,
                            sleep_fn=lambda s: None)
        check('gioi_han_cung_khong_vuot_20', stats3['n_requests'] <= MAX_REQUESTS_HARD_CAP,
              stats3['n_requests'])

    # --- Test 7: phat hien quota theo ngay tu noi dung loi 429 ---
    is_daily, qid = _detect_daily_quota(
        '{"error":{"code":429,"message":"x","status":"RESOURCE_EXHAUSTED",'
        '"details":[{"quotaId":"GenerateRequestsPerDayPerProjectPerModel"}]}}')
    check('phat_hien_quota_theo_ngay', is_daily and qid == 'GenerateRequestsPerDayPerProjectPerModel', qid)

    is_daily_minute, _ = _detect_daily_quota(
        '{"error":{"code":429,"message":"x","details":[{"quotaId":"GenerateRequestsPerMinute"}]}}')
    check('khong_nham_quota_theo_phut_la_theo_ngay', is_daily_minute is False, is_daily_minute)

    # --- Test 8: T266 loi 1 -- ten file nhap doi theo ngay, nhung resume phai
    #     quet TAT CA file *_T74b_pilot_gemini.jsonl trong thu muc, khong chi
    #     file cua "hom nay" (mo phong 2 ngay chay voi 2 file khac ten) ---
    with tempfile.TemporaryDirectory() as tmpdir:
        day1_path = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        day2_path = os.path.join(tmpdir, '2026-10-10_T74b_pilot_gemini.jsonl')
        state_path = os.path.join(tmpdir, 'T74b_pilot_state.json')
        fake_con8 = _FakeDB(12)

        # "Ngay 1": ghi vao file cua ngay 1.
        stats_day1 = run_pilot(fake_con8, day1_path, state_path, max_requests=2,
                                call_fn=_mock_good_response, limit=12, verbose=False,
                                sleep_fn=lambda s: None)
        check('ngay1_ghi_10_dong', stats_day1['n_success'] == 10, stats_day1)

        # "Ngay 2": file nhap MOI (ten khac), nhung phai thay 10 dong cua ngay 1
        # la "da xong" qua gather_done_ids_all_evidence, chi con 1 batch (2 dong).
        done_ids_day2, _ = gather_done_ids_all_evidence(day2_path)
        check('ngay2_thay_du_10_dong_ngay1_qua_file_khac', len(done_ids_day2) == 10,
              len(done_ids_day2))

        stats_day2 = run_pilot(fake_con8, day2_path, state_path, max_requests=5,
                                call_fn=_mock_good_response, limit=12, verbose=False,
                                sleep_fn=lambda s: None)
        check('ngay2_khong_dich_lai_10_dong_ngay1', stats_day2['n_success'] == 2, stats_day2)
        check('ngay2_chi_goi_1_yeu_cau', stats_day2['n_requests'] == 1, stats_day2)

    # --- Test 9: T266 loi 2 + T266-fix2 -- dong CU thieu cjk_flag phai duoc
    #     coi la CHUA xong (de dich lai); dong da CO cjk_flag (du gia tri gi,
    #     du ket thuc the nao) phai duoc coi la DA XONG -- KHONG sua/xoa file
    #     cu. (A2 duoc CAP NHAT o T266-fix2: truoc day A2 "co cjk_flag nhung
    #     bi cat giua cau" bi coi la chua xong -- chinh day la bug ma
    #     daoanh-qa phat hien, vi tieu su DILA hop le cung thuong khong ket
    #     thuc bang dau cau ASCII trong _SENTENCE_END_CHARS. Sau fix, A2 phai
    #     duoc coi la DA XONG vi da co cjk_flag, bat ke ky tu cuoi.) ---
    with tempfile.TemporaryDirectory() as tmpdir:
        legacy_path = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        legacy_lines = [
            # (a) thieu truong cjk_flag hoan toan (dung format script truoc T266)
            {'dila_id': 'A1', 'bio_vi_draft': 'Ban dich day du, co dau cau.',
             'model': 'gemini-3.8-flash'},
            # (b) CO cjk_flag nhung "ket thuc khong co dau cau ASCII chuan" --
            # T266-fix2: KHONG con coi la chua xong, vi da co cjk_flag (tranh
            # dich lai vo han cho dong that ra DA xong nhung ket thuc bang
            # dau cau khac, vd 」/（…）/so).
            {'dila_id': 'A2', 'bio_vi_draft': 'Ban dich ket thuc khong co dau cau ASCII', 'cjk_flag': False},
            # (c) dong hop le, day du, co dau cau -> PHAI duoc coi la da xong
            {'dila_id': 'A3', 'bio_vi_draft': 'Ban dich hop le, day du.', 'cjk_flag': False},
        ]
        with open(legacy_path, 'w', encoding='utf-8') as f:
            for obj in legacy_lines:
                f.write(json.dumps(obj, ensure_ascii=False) + '\n')
        done_legacy, n_skipped = gather_done_ids_all_evidence(legacy_path)
        check('legacy_thieu_cjk_flag_coi_la_chua_xong', 'A1' not in done_legacy, done_legacy)
        check('co_cjk_flag_du_ket_thuc_sao_van_coi_da_xong', 'A2' in done_legacy, done_legacy)
        check('legacy_dong_hop_le_van_tinh_da_xong', 'A3' in done_legacy, done_legacy)
        check('legacy_dem_dung_so_dong_bi_bo_qua', n_skipped == 1, n_skipped)
        # File cu KHONG bi sua/xoa (vi chi doc, khong ghi lai).
        with open(legacy_path, 'r', encoding='utf-8') as f:
            lines_after = f.readlines()
        check('legacy_khong_sua_xoa_file_cu', len(lines_after) == 3, len(lines_after))

    # --- Test 9b: T266-fix2 -- 3 case cu the admin yeu cau kiem tra ---
    with tempfile.TemporaryDirectory() as tmpdir:
        path9b = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        lines_9b = [
            # (a) dong MOI: co cjk_flag va ket thuc bang dau cau CJK (」) hoac
            # dang (（…）) -- khong nam trong _SENTENCE_END_CHARS ASCII, nhung
            # la ket thuc hop le cua tieu su DILA -> PHAI coi la DA XONG.
            {'dila_id': 'B1', 'bio_vi_draft': 'Trich dan ket thuc bang 」', 'cjk_flag': True},
            {'dila_id': 'B2', 'bio_vi_draft': 'Mot cau co chu thich（…）', 'cjk_flag': False},
            # (b) dong CU thieu truong cjk_flag VA bi cat giua cau (khong dau
            # cau cuoi) -> PHAI coi la CHUA xong (dung ca 2 dieu kien, nhung
            # ly do duy nhat la THIEU cjk_flag).
            {'dila_id': 'B3', 'bio_vi_draft': 'Cau bi cat giua duong di ma khong',
             'model': 'gemini-3.8-flash'},
            # (c) dong CU thieu truong cjk_flag NHUNG da ket thuc dung dau cau
            # -> VAN phai coi la CHUA xong, vi ly do duy nhat la thieu
            # cjk_flag (khong con kiem tra dau cau cho truong hop nay nua).
            {'dila_id': 'B4', 'bio_vi_draft': 'Cau nay ket thuc dung dau cau.',
             'model': 'gemini-3.8-flash'},
        ]
        with open(path9b, 'w', encoding='utf-8') as f:
            for obj in lines_9b:
                f.write(json.dumps(obj, ensure_ascii=False) + '\n')
        done_9b, n_skipped_9b = gather_done_ids_all_evidence(path9b)
        check('a_dong_moi_cjk_flag_ket_thuc_bang_」_coi_da_xong', 'B1' in done_9b, done_9b)
        check('a_dong_moi_cjk_flag_ket_thuc_bang_（…）_coi_da_xong', 'B2' in done_9b, done_9b)
        check('b_dong_cu_thieu_cjk_flag_cat_giua_cau_coi_chua_xong', 'B3' not in done_9b, done_9b)
        check('c_dong_cu_thieu_cjk_flag_du_ket_thuc_dung_van_coi_chua_xong',
              'B4' not in done_9b, done_9b)
        check('b_c_dem_dung_2_dong_bi_bo_qua', n_skipped_9b == 2, n_skipped_9b)

    # --- Test 10: T266 loi 3 -- key gui qua header x-goog-api-key (khong qua
    #     query string cua URL), va moi chuoi loi luu ra deu duoc che key ---
    check('url_khong_con_query_string_key', '{key}' not in GEMINI_URL_TMPL and 'key=' not in
          GEMINI_URL_TMPL, GEMINI_URL_TMPL)
    masked = mask_secrets(
        'Loi goi toi https://x/y:generateContent?key=FAKEKEY_SECRET_123&other=1 that bai',
        key='FAKEKEY_SECRET_123')
    check('mask_secrets_che_key_trong_url', 'FAKEKEY_SECRET_123' not in masked, masked)
    check('mask_secrets_giu_lai_phan_khac', 'other=1' in masked, masked)

    class _FakeResp:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

        def json(self):
            raise ValueError('khong co json (mock loi)')

    class _FakeRequestsAlwaysBadStatus:
        calls = []

        @staticmethod
        def post(url, json=None, headers=None, timeout=None):
            _FakeRequestsAlwaysBadStatus.calls.append((url, headers))
            return _FakeResp(400, 'Bad request toi key=FAKEKEY_SECRET_123 trong noi dung loi')

    global requests
    _orig_requests = requests
    _orig_sleep = time.sleep
    time.sleep = lambda s: None   # call_gemini goi time.sleep() cung khi retry; khong cho ngu thuc trong self-test
    requests = _FakeRequestsAlwaysBadStatus
    try:
        counter10 = RequestCounter(1)
        res10 = call_gemini('FAKEKEY_SECRET_123', MODEL, 'prompt', counter10)
    finally:
        requests = _orig_requests
        time.sleep = _orig_sleep
    check('call_gemini_dung_header_x_goog_api_key',
          all(h and h.get('x-goog-api-key') == 'FAKEKEY_SECRET_123'
              for _, h in _FakeRequestsAlwaysBadStatus.calls),
          _FakeRequestsAlwaysBadStatus.calls)
    check('call_gemini_url_khong_chua_key', all('FAKEKEY_SECRET_123' not in u for u, _ in
          _FakeRequestsAlwaysBadStatus.calls), [u for u, _ in _FakeRequestsAlwaysBadStatus.calls])
    check('loi_tra_ve_khong_chua_key_that', 'FAKEKEY_SECRET_123' not in (res10.error or ''),
          res10.error)

    # --- Test 11: T266 loi 4 -- gioi han --max-requests dem THEO HTTP REQUEST
    #     THUC SU (ke ca retry do 429), KHONG theo batch. Gia lap server luon
    #     tra 429 (khong phai theo ngay) -> call_gemini se retry, nhung phai
    #     DUNG LAI dung luc counter het, khong vuot qua gioi han duoc giao ---
    class _FakeRequestsAlways429:
        calls = []

        @staticmethod
        def post(url, json=None, headers=None, timeout=None):
            _FakeRequestsAlways429.calls.append(1)
            return _FakeResp(429, '{"error":{"details":[{"quotaId":"GenerateRequestsPerMinute"}]}}')

    requests = _FakeRequestsAlways429
    time.sleep = lambda s: None
    try:
        counter11 = RequestCounter(2)   # chi cho phep 2 yeu cau HTTP thuc su
        res11 = call_gemini('FAKEKEY', MODEL, 'prompt', counter11)
    finally:
        requests = _orig_requests
        time.sleep = _orig_sleep
    check('retry_429_dung_dung_luc_het_counter',
          len(_FakeRequestsAlways429.calls) == 2, len(_FakeRequestsAlways429.calls))
    check('attempts_used_khop_so_lan_goi_thuc', res11.attempts_used == 2, res11.attempts_used)
    check('counter_khong_con_cho_sau_khi_het', counter11.can_request() is False, counter11.count)

    # --- Test 12: luong run_pilot khi gap 429 THEO NGAY -> dung sach, ghi
    #     quota_exhausted, KHONG goi them trong cung ngay (ke ca lan chay sau) ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path12 = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        state_path12 = os.path.join(tmpdir, 'T74b_pilot_state.json')
        fake_con12 = _FakeDB(10)

        stats12a = run_pilot(fake_con12, out_path12, state_path12, max_requests=20,
                              call_fn=_mock_daily_quota_response, limit=10, verbose=False,
                              sleep_fn=lambda s: None)
        check('gap_429_ngay_dung_sach_khong_thanh_cong', stats12a['n_success'] == 0, stats12a)
        check('gap_429_ngay_ghi_dung_ly_do_dung',
              stats12a.get('stopped_reason') == 'daily_quota_exceeded', stats12a)

        state_after12a = load_state(state_path12)
        check('gap_429_ngay_ghi_quota_exhausted_vao_state',
              bool(state_after12a.get('quota_exhausted')), state_after12a.get('quota_exhausted'))

        # Chay lai NGAY TRONG NGAY -> phai dung sach NGAY TU DAU, khong goi them
        # (dung mock se bao loi AssertionError neu bi goi, de chac chan 0 lan goi).
        stats12b = run_pilot(fake_con12, out_path12, state_path12, max_requests=20,
                              call_fn=_mock_fail_if_called, limit=10, verbose=False,
                              sleep_fn=lambda s: None)
        check('cung_ngay_khong_goi_them_sau_khi_het_han_muc',
              stats12b['n_requests'] == 0 and
              stats12b.get('stopped_reason') == 'daily_quota_already_exhausted_today',
              stats12b)

    # --- Test 13: T266-fix3 -- finishReason != STOP (max_tokens) khong duoc
    #     ghi draft; cac ma vao retry_queue voi ly do max_tokens; qua
    #     MAX_TOKENS_RETRY_LIMIT lan thi 'gave_up' va KHONG bi goi lai ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path13 = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        state_path13 = os.path.join(tmpdir, 'T74b_pilot_state.json')
        fake_con13 = _FakeDB(5)   # 5 dong -> 1 batch duy nhat (BATCH_SIZE=5)
        pid5 = [f'PL{1000 + i:06d}' for i in range(5)]

        # Lan 1: max_tokens -> khong ghi draft, attempts=1 cho ca 5 ma.
        stats13a = run_pilot(fake_con13, out_path13, state_path13, max_requests=1,
                              call_fn=_mock_max_tokens_response, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        check('max_tokens_khong_ghi_draft_lan1', stats13a['n_success'] == 0, stats13a)
        done13a = load_done_ids(out_path13)
        check('max_tokens_chua_co_dong_nao_trong_jsonl', len(done13a) == 0, done13a)
        state13a = load_state(state_path13)
        check('max_tokens_vao_retry_queue_attempts_1',
              all(state13a.get('retry_queue', {}).get(pid, {}).get('attempts') == 1
                  for pid in pid5),
              state13a.get('retry_queue'))
        check('max_tokens_chua_gave_up_lan1', len(state13a.get('gave_up') or {}) == 0,
              state13a.get('gave_up'))

        # Lan 2: van max_tokens -> attempts=2 = MAX_TOKENS_RETRY_LIMIT -> gave_up,
        # xoa khoi retry_queue. T266-fix5: vi ca 5 ma da co max_tokens_attempts=1
        # tu lan 1, lan nay build_batches_with_split tach rieng thanh 5 batch
        # 1-tieu-su (khong con gop chung 1 batch 5 nhu truoc fix5) -> can
        # max_requests=5 (truoc fix5 chi can 1) de ca 5 ma deu duoc thu lai.
        stats13b = run_pilot(fake_con13, out_path13, state_path13, max_requests=5,
                              call_fn=_mock_max_tokens_response, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        state13b = load_state(state_path13)
        check('max_tokens_sau_2_lan_gave_up_du_5_ma',
              all(pid in (state13b.get('gave_up') or {}) for pid in pid5),
              state13b.get('gave_up'))
        check('max_tokens_gave_up_khong_con_trong_retry_queue',
              len(state13b.get('retry_queue') or {}) == 0, state13b.get('retry_queue'))
        check('max_tokens_van_khong_ghi_draft_lan2', stats13b['n_success'] == 0, stats13b)

        # Lan 3: 5 ma da 'gave_up' -> KHONG duoc dua lai vao hang doi/goi API
        # (mock se raise AssertionError neu bi goi, dam bao chac chan 0 lan goi).
        stats13c = run_pilot(fake_con13, out_path13, state_path13, max_requests=1,
                              call_fn=_mock_fail_if_called, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        check('gave_up_khong_duoc_goi_lai', stats13c['n_requests'] == 0, stats13c)
        check('gave_up_khong_co_draft_nao_duoc_ghi', stats13c['n_success'] == 0, stats13c)

    # --- Test 14: finishReason STOP (hoac khong co) van ghi draft nhu cu, va
    #     moi dong moi co truong finish_reason de kiem sau ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path14 = os.path.join(tmpdir, 'test_stop.jsonl')
        state_path14 = os.path.join(tmpdir, 'test_stop_state.json')
        fake_con14 = _FakeDB(5)
        stats14 = run_pilot(fake_con14, out_path14, state_path14, max_requests=1,
                             call_fn=_mock_good_response, limit=5, verbose=False,
                             sleep_fn=lambda s: None)
        check('stop_van_ghi_draft_nhu_cu', stats14['n_success'] == 5, stats14)
        with open(out_path14, 'r', encoding='utf-8') as f:
            recs14 = [json.loads(ln) for ln in f if ln.strip()]
        check('stop_co_truong_finish_reason_trong_jsonl',
              all(r.get('finish_reason') == 'STOP' for r in recs14),
              [r.get('finish_reason') for r in recs14])

    # --- Test 15: call_gemini thuc su (qua requests gia lap tra HTTP 200) voi
    #     finishReason='MAX_TOKENS' -> tra ve loi 'max_tokens', KHONG tra text
    #     (du JSON co text bi cat), va KHONG retry vo ich trong cung 1 call ---
    class _FakeRespJson:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
            self.text = json.dumps(json_data)

        def json(self):
            return self._json

    class _FakeRequestsMaxTokens:
        calls = []

        @staticmethod
        def post(url, json=None, headers=None, timeout=None):
            _FakeRequestsMaxTokens.calls.append(1)
            body = {'candidates': [{
                'content': {'parts': [{'text': 'Ban dich bi cat ngang gi'}]},
                'finishReason': 'MAX_TOKENS',
            }]}
            return _FakeRespJson(200, body)

    _orig_requests = requests
    _orig_sleep = time.sleep
    time.sleep = lambda s: None
    requests = _FakeRequestsMaxTokens
    try:
        counter15 = RequestCounter(5)
        res15 = call_gemini('FAKEKEY', MODEL, 'prompt', counter15)
    finally:
        requests = _orig_requests
        time.sleep = _orig_sleep
    check('call_gemini_max_tokens_tra_loi_khong_text',
          res15.text is None and res15.error == 'max_tokens', (res15.text, res15.error))
    check('call_gemini_max_tokens_finish_reason_dung',
          res15.finish_reason == 'MAX_TOKENS', res15.finish_reason)
    check('call_gemini_max_tokens_khong_retry_vo_ich_trong_1_call',
          len(_FakeRequestsMaxTokens.calls) == 1, len(_FakeRequestsMaxTokens.calls))

    # --- Test 16: call_gemini thuc su voi finishReason='STOP' -> van tra ve
    #     text binh thuong nhu truoc T266-fix3 (khong regression) ---
    class _FakeRequestsStop:
        calls = []

        @staticmethod
        def post(url, json=None, headers=None, timeout=None):
            _FakeRequestsStop.calls.append(1)
            body = {'candidates': [{
                'content': {'parts': [{'text': 'Ban dich day du.'}]},
                'finishReason': 'STOP',
            }]}
            return _FakeRespJson(200, body)

    requests = _FakeRequestsStop
    time.sleep = lambda s: None
    try:
        counter16 = RequestCounter(5)
        res16 = call_gemini('FAKEKEY', MODEL, 'prompt', counter16)
    finally:
        requests = _orig_requests
        time.sleep = _orig_sleep
    check('call_gemini_stop_van_tra_text_binh_thuong',
          res16.text == 'Ban dich day du.' and res16.finish_reason == 'STOP',
          (res16.text, res16.finish_reason))

    # --- Test 17: T266-fix4 -- finishReason='SAFETY' phai chiu CUNG gioi han
    #     thu lai nhu max_tokens: khong ghi draft; sau 2 lan -> gave_up voi
    #     reason chua 'safety'; lan 3 KHONG goi them (dung _mock_fail_if_called). ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path17 = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        state_path17 = os.path.join(tmpdir, 'T74b_pilot_state.json')
        fake_con17 = _FakeDB(5)   # 5 dong -> 1 batch duy nhat (BATCH_SIZE=5)
        pid5_17 = [f'PL{1000 + i:06d}' for i in range(5)]

        stats17a = run_pilot(fake_con17, out_path17, state_path17, max_requests=1,
                              call_fn=_mock_safety_response, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        check('safety_khong_ghi_draft_lan1', stats17a['n_success'] == 0, stats17a)
        done17a = load_done_ids(out_path17)
        check('safety_chua_co_dong_nao_trong_jsonl', len(done17a) == 0, done17a)
        state17a = load_state(state_path17)
        check('safety_vao_retry_queue_max_tokens_attempts_1',
              all(state17a.get('retry_queue', {}).get(pid, {}).get('max_tokens_attempts') == 1
                  for pid in pid5_17),
              state17a.get('retry_queue'))
        check('safety_chua_gave_up_lan1', len(state17a.get('gave_up') or {}) == 0,
              state17a.get('gave_up'))

        # T266-fix5: lan nay ca 5 ma da co max_tokens_attempts=1 tu lan 1 ->
        # build_batches_with_split tach rieng thanh 5 batch 1-tieu-su, can
        # max_requests=5 (truoc fix5 chi can 1) de ca 5 ma deu duoc thu lai.
        stats17b = run_pilot(fake_con17, out_path17, state_path17, max_requests=5,
                              call_fn=_mock_safety_response, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        state17b = load_state(state_path17)
        check('safety_sau_2_lan_gave_up_du_5_ma',
              all(pid in (state17b.get('gave_up') or {}) for pid in pid5_17),
              state17b.get('gave_up'))
        check('safety_gave_up_reason_chua_tu_safety',
              all('safety' in (state17b.get('gave_up', {}).get(pid, {}).get('reason') or '')
                  for pid in pid5_17),
              state17b.get('gave_up'))
        check('safety_gave_up_khong_con_trong_retry_queue',
              len(state17b.get('retry_queue') or {}) == 0, state17b.get('retry_queue'))
        check('safety_van_khong_ghi_draft_lan2', stats17b['n_success'] == 0, stats17b)

        # Lan 3: 5 ma da 'gave_up' -> KHONG duoc goi lai (mock raise neu bi goi).
        stats17c = run_pilot(fake_con17, out_path17, state_path17, max_requests=1,
                              call_fn=_mock_fail_if_called, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        check('safety_gave_up_khong_duoc_goi_lai', stats17c['n_requests'] == 0, stats17c)
        check('safety_gave_up_khong_co_draft_nao_duoc_ghi', stats17c['n_success'] == 0, stats17c)

    # --- Test 18: T266-fix4 -- 1 loi mang truoc do (tang 'attempts' chung)
    #     roi MAX_TOKENS 1 lan (tang 'max_tokens_attempts' rieng) -> KHONG
    #     gave_up ngay, vi bo dem rieng moi = 1 (< MAX_TOKENS_RETRY_LIMIT=2) ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path18 = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        state_path18 = os.path.join(tmpdir, 'T74b_pilot_state.json')
        fake_con18 = _FakeDB(5)
        pid5_18 = [f'PL{1000 + i:06d}' for i in range(5)]
        mock18 = _make_mock_network_then_max_tokens()

        # Lan 1: loi mang chung -> 'attempts' = 1, 'max_tokens_attempts' van 0,
        # KHONG gave_up.
        stats18a = run_pilot(fake_con18, out_path18, state_path18, max_requests=1,
                              call_fn=mock18, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        state18a = load_state(state_path18)
        check('loi_mang_truoc_tang_attempts_chung_khong_tang_max_tokens_attempts',
              all(state18a.get('retry_queue', {}).get(pid, {}).get('attempts') == 1
                  and state18a.get('retry_queue', {}).get(pid, {}).get('max_tokens_attempts', 0) == 0
                  for pid in pid5_18),
              state18a.get('retry_queue'))

        # Lan 2: MAX_TOKENS 1 lan -> 'max_tokens_attempts' = 1 (rieng), KHONG
        # gave_up ngay (can 2 lan theo MAX_TOKENS_RETRY_LIMIT).
        stats18b = run_pilot(fake_con18, out_path18, state_path18, max_requests=1,
                              call_fn=mock18, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        state18b = load_state(state_path18)
        check('max_tokens_sau_loi_mang_truoc_do_khong_gave_up_ngay',
              len(state18b.get('gave_up') or {}) == 0, state18b.get('gave_up'))
        check('max_tokens_attempts_rieng_bang_1_sau_1_lan_max_tokens',
              all(state18b.get('retry_queue', {}).get(pid, {}).get('max_tokens_attempts') == 1
                  for pid in pid5_18),
              state18b.get('retry_queue'))
        check('attempts_chung_van_tiep_tuc_tang_doc_lap',
              all(state18b.get('retry_queue', {}).get(pid, {}).get('attempts') == 2
                  for pid in pid5_18),
              state18b.get('retry_queue'))

    # --- Test 19: T266-fix4 muc 3 -- dry-run (qua compute_dry_run) phai doc
    #     state, loai cac ma trong gave_up khoi so can dich. ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path19 = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        state_path19 = os.path.join(tmpdir, 'T74b_pilot_state.json')
        fake_con19 = _FakeDB(12)   # 12 dong, khong co dong nao da xong trong jsonl

        # Khong co gave_up -> can dich du 12.
        dr19a = compute_dry_run(fake_con19, out_path19, state_path19, limit=12, verbose=False)
        check('dry_run_khong_gave_up_can_dich_du_12', len(dr19a['pending_ids']) == 12,
              len(dr19a['pending_ids']))
        check('dry_run_khong_gave_up_in_0', len(dr19a['gave_up']) == 0, dr19a['gave_up'])

        # Ghi state co 3 ma 'gave_up' -> can dich phai giam dung 3.
        gave_up_ids = [f'PL{1000 + i:06d}' for i in range(3)]
        state19 = load_state(state_path19)
        for pid in gave_up_ids:
            state19['gave_up'][pid] = {'reason': 'max_tokens', 'attempts': 2, 'last_ts': 'x'}
        save_state(state_path19, state19)

        dr19b = compute_dry_run(fake_con19, out_path19, state_path19, limit=12, verbose=False)
        check('dry_run_loai_dung_3_ma_gave_up_khoi_can_dich',
              len(dr19b['pending_ids']) == 9, len(dr19b['pending_ids']))
        check('dry_run_khong_con_ma_gave_up_trong_pending',
              all(pid not in dr19b['pending_ids'] for pid in gave_up_ids), dr19b['pending_ids'])
        check('dry_run_in_dung_so_gave_up', len(dr19b['gave_up']) == 3, dr19b['gave_up'])
        # Dry-run KHONG ghi gi: file jsonl van chua ton tai (chua tung mo 'a').
        check('dry_run_khong_ghi_file_jsonl', not os.path.isfile(out_path19),
              os.path.isfile(out_path19))

    # --- Test 20: T266-fix5 muc C -- batch 5 bi MAX_TOKENS -> lan chay SAU
    #     (khi max_tokens_attempts >= 1) tach thanh 5 request don le, moi ma
    #     duoc xu ly rieng; ma nao thanh cong duoc ghi draft. ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path20 = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        state_path20 = os.path.join(tmpdir, 'T74b_pilot_state.json')
        fake_con20 = _FakeDB(5)   # 5 dong -> 1 batch duy nhat (BATCH_SIZE=5)
        pid5_20 = [f'PL{1000 + i:06d}' for i in range(5)]
        mock20 = _make_mock_batch_maxtokens_then_singles_good()

        # Lan 1: batch gop 5 ma -> MAX_TOKENS -> khong ghi draft nao, ca 5 ma
        # vao retry_queue voi max_tokens_attempts=1.
        stats20a = run_pilot(fake_con20, out_path20, state_path20, max_requests=1,
                              call_fn=mock20, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        check('t20_lan1_batch5_max_tokens_khong_ghi_draft', stats20a['n_success'] == 0,
              stats20a)
        check('t20_lan1_chi_1_yeu_cau_HTTP_cho_ca_batch', stats20a['n_requests'] == 1,
              stats20a)
        state20a = load_state(state_path20)
        check('t20_lan1_ca_5_ma_vao_retry_queue_max_tokens_attempts_1',
              all(state20a.get('retry_queue', {}).get(pid, {}).get('max_tokens_attempts') == 1
                  for pid in pid5_20),
              state20a.get('retry_queue'))

        # Lan 2: ca 5 ma da max_tokens_attempts=1 -> build_batches_with_split
        # tach rieng thanh 5 batch 1-tieu-su; mock tra thanh cong cho batch 1
        # ma -> ca 5 ma duoc goi RIENG (5 yeu cau HTTP) va deu thanh cong.
        stats20b = run_pilot(fake_con20, out_path20, state_path20, max_requests=5,
                              call_fn=mock20, limit=5, verbose=False,
                              sleep_fn=lambda s: None)
        check('t20_lan2_tach_thanh_5_yeu_cau_rieng', stats20b['n_requests'] == 5,
              stats20b)
        check('t20_lan2_ca_5_ma_thanh_cong_duoc_ghi_draft', stats20b['n_success'] == 5,
              stats20b)
        done20b = load_done_ids(out_path20)
        check('t20_lan2_du_5_dong_trong_jsonl', len(done20b) == 5, done20b)
        state20b = load_state(state_path20)
        check('t20_lan2_retry_queue_rong_sau_khi_thanh_cong',
              len(state20b.get('retry_queue') or {}) == 0, state20b.get('retry_queue'))

    # --- Test 20b: trong lan tach, 1 ma van tiep tuc that bai (van max_tokens
    #     o lan don) -> 4 ma kia thanh cong duoc ghi draft, rieng ma do tang
    #     max_tokens_attempts len 2 (>= MAX_TOKENS_RETRY_LIMIT) -> gave_up,
    #     KHONG lam anh huong ma khac. ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path20c = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        state_path20c = os.path.join(tmpdir, 'T74b_pilot_state.json')
        fake_con20c = _FakeDB(5)
        pid5_20c = [f'PL{1000 + i:06d}' for i in range(5)]
        bad_pid = pid5_20c[0]

        def _mock20c(prompt, counter=None):
            _consume_mock_budget(counter)
            ids = ID_MARKER_RE.findall(prompt)
            if len(ids) > 1:
                return ApiResult(error='max_tokens', finish_reason='MAX_TOKENS')
            if ids == [bad_pid]:
                return ApiResult(error='max_tokens', finish_reason='MAX_TOKENS')
            return ApiResult(text=_build_good_text(ids))

        run_pilot(fake_con20c, out_path20c, state_path20c, max_requests=1,
                  call_fn=_mock20c, limit=5, verbose=False, sleep_fn=lambda s: None)
        stats20c2 = run_pilot(fake_con20c, out_path20c, state_path20c, max_requests=5,
                               call_fn=_mock20c, limit=5, verbose=False,
                               sleep_fn=lambda s: None)
        check('t20b_4_ma_thanh_cong_1_ma_that_bai', stats20c2['n_success'] == 4, stats20c2)
        state20c2 = load_state(state_path20c)
        check('t20b_ma_loi_gave_up_sau_2_lan', bad_pid in (state20c2.get('gave_up') or {}),
              state20c2.get('gave_up'))
        check('t20b_4_ma_con_lai_khong_bi_gave_up',
              all(pid not in (state20c2.get('gave_up') or {}) for pid in pid5_20c if pid != bad_pid),
              state20c2.get('gave_up'))

    # --- Test 21: T266-fix5 muc D -- ham tong hop (aggregate_evidence) doc
    #     nhieu file *_T74b_pilot_gemini.jsonl, loai trung theo dila_id, giu
    #     dong CO cjk_flag uu tien hon dong KHONG co, va trong cung nhom giu
    #     ban MOI HON theo ts. KHONG ghi gi ca (chi doc). ---
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, '2026-10-08_T74b_pilot_gemini.jsonl')
        f2 = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        # X1: chi co trong f1, dong cu (khong cjk_flag) -> van duoc giu (ma
        # duy nhat, khong co ban nao khac de so sanh).
        # X2: co trong ca f1 (cu, khong cjk_flag, ts som) va f2 (moi, co
        # cjk_flag, ts muon) -> phai giu ban f2 (co cjk_flag).
        # X3: co trong ca f1 va f2, CA HAI deu co cjk_flag, nhung f2 ts muon
        # hon -> phai giu ban f2 (moi hon).
        with open(f1, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'dila_id': 'X1', 'bio_vi_draft': 'ban X1 cu',
                                 'ts': '2026-10-08T01:00:00'}, ensure_ascii=False) + '\n')
            f.write(json.dumps({'dila_id': 'X2', 'bio_vi_draft': 'ban X2 cu khong cjk',
                                 'ts': '2026-10-08T02:00:00'}, ensure_ascii=False) + '\n')
            f.write(json.dumps({'dila_id': 'X3', 'bio_vi_draft': 'ban X3 cu hon',
                                 'cjk_flag': False, 'ts': '2026-10-08T03:00:00'},
                                ensure_ascii=False) + '\n')
        with open(f2, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'dila_id': 'X2', 'bio_vi_draft': 'ban X2 moi co cjk',
                                 'cjk_flag': True, 'ts': '2026-10-09T01:00:00'},
                                ensure_ascii=False) + '\n')
            f.write(json.dumps({'dila_id': 'X3', 'bio_vi_draft': 'ban X3 moi hon',
                                 'cjk_flag': False, 'ts': '2026-10-09T02:00:00'},
                                ensure_ascii=False) + '\n')

        agg = aggregate_evidence(tmpdir, verbose=False)
        check('t21_tong_so_file_quet_duoc', agg['n_files'] == 2, agg['n_files'])
        check('t21_tong_so_dong_doc', agg['n_lines'] == 5, agg['n_lines'])
        check('t21_so_dila_id_duy_nhat_sau_loai_trung', agg['n_unique'] == 3, agg['n_unique'])
        check('t21_so_dong_trung_bi_loai', agg['n_dup_skipped'] == 2, agg['n_dup_skipped'])
        check('t21_X1_chi_co_1_ban_duoc_giu',
              agg['unique'].get('X1', {}).get('bio_vi_draft') == 'ban X1 cu',
              agg['unique'].get('X1'))
        check('t21_X2_giu_ban_co_cjk_flag_du_cu_hon_ts',
              agg['unique'].get('X2', {}).get('bio_vi_draft') == 'ban X2 moi co cjk',
              agg['unique'].get('X2'))
        check('t21_X3_giu_ban_moi_hon_ts_khi_cung_khong_co_cjk',
              agg['unique'].get('X3', {}).get('bio_vi_draft') == 'ban X3 moi hon',
              agg['unique'].get('X3'))
        check('t21_khong_ghi_file_nao_moi', sorted(os.listdir(tmpdir)) == sorted(
              [os.path.basename(f1), os.path.basename(f2)]), os.listdir(tmpdir))

    # --- Test 22: T266-fix5 muc E -- chay duoc hom sau: 1 lan chay dich xong
    #     1 phan roi het han muc THEO NGAY giua duong -> lan chay sau (mo
    #     phong "hom sau" bang cach doi lai ngay trong quota_exhausted cua
    #     state) phai tiep tuc dich PHAN CON LAI, KHONG dich lai phan da
    #     xong (resume dung tu retry_queue/state + file jsonl da co). ---
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path22 = os.path.join(tmpdir, '2026-10-09_T74b_pilot_gemini.jsonl')
        state_path22 = os.path.join(tmpdir, 'T74b_pilot_state.json')
        fake_con22 = _FakeDB(10)   # 10 dong -> 2 batch (5, 5)
        mock22 = _make_mock_batch1_good_batch2_daily_quota()

        stats22a = run_pilot(fake_con22, out_path22, state_path22, max_requests=20,
                              call_fn=mock22, limit=10, verbose=False,
                              sleep_fn=lambda s: None)
        check('t22_ngay1_dich_duoc_5_dong_truoc_khi_het_han_muc',
              stats22a['n_success'] == 5, stats22a)
        check('t22_ngay1_dung_vi_het_han_muc_ngay',
              stats22a.get('stopped_reason') == 'daily_quota_exceeded', stats22a)
        done_after22a = load_done_ids(out_path22)
        check('t22_ngay1_co_dung_5_dong_trong_jsonl', len(done_after22a) == 5,
              done_after22a)

        # Mo phong "hom sau": doi lai 'date' trong quota_exhausted thanh ngay
        # hom qua (khac ngay hien tai), dung AssertionError-mock de dam bao
        # khong bi chan boi 'quota_exhausted hom nay' nua.
        state22 = load_state(state_path22)
        state22['quota_exhausted']['date'] = '2000-01-01'
        save_state(state_path22, state22)

        stats22b = run_pilot(fake_con22, out_path22, state_path22, max_requests=20,
                              call_fn=_mock_good_response, limit=10, verbose=False,
                              sleep_fn=lambda s: None)
        check('t22_hom_sau_chi_dich_5_dong_con_lai_khong_dich_lai',
              stats22b['n_success'] == 5, stats22b)
        check('t22_hom_sau_chi_goi_1_yeu_cau_cho_1_batch_con_lai',
              stats22b['n_requests'] == 1, stats22b)
        done_after22b = load_done_ids(out_path22)
        check('t22_tong_du_10_dong_sau_2_ngay', len(done_after22b) == 10, done_after22b)

    n_pass = sum(1 for _, ok, _ in results if ok)
    n_total = len(results)
    print(f'=== SELF-TEST (mock, khong goi API thuc) — {n_pass}/{n_total} PASS ===')
    for name, ok, detail in results:
        mark = 'OK ' if ok else 'FAIL'
        line = f'  [{mark}] {name}'
        if not ok:
            line += f' -- {detail}'
        print(line)
    return n_pass == n_total, n_pass, n_total


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if '--self-test' in argv:
        ok, n_pass, n_total = _self_test()
        return 0 if ok else 1

    if '--aggregate' in argv:
        # T266-fix5 muc D: chi doc va in so lieu tong hop, KHONG ghi DB,
        # KHONG ghi file nao (chi doc cac file *_T74b_pilot_gemini.jsonl co
        # san trong docs/evidence/).
        evidence_dir = os.path.join(PROJECT_ROOT, 'docs', 'evidence')
        aggregate_evidence(evidence_dir, verbose=True)
        return 0

    dry_run = '--dry-run' in argv
    limit = PILOT_SIZE
    max_requests = DEFAULT_MAX_REQUESTS
    out_path = os.path.join(
        PROJECT_ROOT, 'docs', 'evidence',
        f'{datetime.now().strftime("%Y-%m-%d")}_T74b_pilot_gemini.jsonl')
    state_path = DEFAULT_STATE_PATH

    for i, a in enumerate(argv):
        if a == '--limit' and i + 1 < len(argv):
            limit = min(int(argv[i + 1]), PILOT_SIZE)
        elif a.startswith('--limit='):
            limit = min(int(a.split('=', 1)[1]), PILOT_SIZE)
        elif a == '--max-requests' and i + 1 < len(argv):
            max_requests = min(int(argv[i + 1]), MAX_REQUESTS_HARD_CAP)
        elif a.startswith('--max-requests='):
            max_requests = min(int(a.split('=', 1)[1]), MAX_REQUESTS_HARD_CAP)
        elif a == '--out' and i + 1 < len(argv):
            out_path = argv[i + 1]
        elif a.startswith('--out='):
            out_path = a.split('=', 1)[1]
        elif a == '--state-file' and i + 1 < len(argv):
            state_path = argv[i + 1]
        elif a.startswith('--state-file='):
            state_path = a.split('=', 1)[1]

    con = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
    con.execute('PRAGMA query_only = ON')

    if dry_run:
        dr = compute_dry_run(con, out_path, state_path, limit, verbose=True)
        pilot_rows = dr['pilot_rows']
        done_ids = dr['done_ids']
        gave_up = dr['gave_up']
        retry_queue = dr['retry_queue']
        pending_ids = dr['pending_ids']
        batches = dr['batches']
        print(f'Pilot T74b (Gemini free tier) · seed={SEED} · chon {len(pilot_rows)}/{limit} dong '
              f'· da xong {len(done_ids)} · con {len(pending_ids)} · {len(batches)} batch '
              f'(batch_size={BATCH_SIZE}) · model={MODEL}')
        print(f'  gave_up: {len(gave_up)} ma (bo qua)')
        print(f'  retry_queue: {len(retry_queue)} ma dang cho thu lai')
        print(f'--- DRY RUN: 2 batch dau (khong goi API), gioi han thuc te moi lan chay = '
              f'{min(max_requests, MAX_REQUESTS_HARD_CAP)} yeu cau ---')
        by_id = {r[0]: r for r in pilot_rows}
        for b in batches[:2]:
            print(f'  batch: {b}')
            for pid in b:
                _, name_zh, name_vi, dynasty, bio = by_id[pid]
                print(f'    [{pid}] {name_vi} ({name_zh}) · {dynasty} · bio_len={len(bio or "")}')
        con.close()
        return 0

    key = resolve_gemini_key()
    if not key:
        print('LOI: khong tim thay GEMINI_API_KEY trong env hoac .env.')
        con.close()
        return 1

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    def real_call_fn(prompt, counter):
        return call_gemini(key, MODEL, prompt, counter)

    run_pilot(con, out_path, state_path, max_requests, real_call_fn, limit=limit, verbose=True)
    con.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
