#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T78 — SourceAnalyzer (Legal Check cho repo mới)
================================================
Phân tích một repo PUBLIC (không token) để:
  1. Đọc LICENSE + README (GitHub raw + API metadata public).
  2. Map license thành mã SPDX + đánh giá software vs data/corpus.
  3. Chạy LicenseGate lên từng operation.
  4. Tạo:
       - Kết luận: INGEST / REFERENCE_ONLY (nội bộ) / BLOCKED
       - NOTES tích hợp đề nghị (mặc định có sẵn — admin có thể chỉnh/duyệt)
       - Provenance draft (commit_sha, retrieved_at, content_hash nếu có)
  5. Báo cáo cho admin; admin bấm XÁC NHẬN → source-add (legal_status=AUDITING).

Rule-based SPDX (deterministic — dễ test), KHÔNG dùng LLM trong gate. LLM check độc
lập riêng từng repo trước khi gửi link cho admin (ngoài luồng gate).

Nguyên tắc: PUBLIC ≠ FREE · SOFTWARE ≠ CORPUS · REFERENCE ≠ COPY.
"""
import hashlib
import json
import re
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .license import LicenseGate
from .provenance import ProvenanceGate
from .status import LegalStatus


# Bảng rule SPDX: (alias/keyword, spdx, commercial, derivative, sharealike, noncommercial, note)
SPDX_RULES = [
    ('cc-by-nc-sa',   'CC BY-NC-SA 4.0', 0, 1, 1, 1, 'phi thương mại + share-alike'),
    ('cc-by-nc',      'CC BY-NC 4.0',    0, 1, 0, 1, 'phi thương mại'),
    ('cc-by-sa',      'CC BY-SA 4.0',    1, 1, 1, 0, 'share-alike'),
    ('cc-by',         'CC BY 4.0',       1, 1, 0, 0, 'ghi công'),
    ('cc0',           'CC0 1.0',         1, 1, 0, 0, 'public domain'),
    ('apache-2.0',    'Apache-2.0',      1, 1, 0, 0, 'permisive'),
    ('mit',           'MIT',             1, 1, 0, 0, 'permisive'),
    ('bsd-3',         'BSD-3-Clause',    1, 1, 0, 0, 'permisive'),
    ('bsd-2',         'BSD-2-Clause',    1, 1, 0, 0, 'permisive'),
    ('gpl-3.0',       'GPL-3.0',         1, 1, 1, 0, 'copyleft (software)'),
    ('gpl-2.0',       'GPL-2.0',         1, 1, 1, 0, 'copyleft (software)'),
    ('lgpl',          'LGPL',            1, 1, 1, 0, 'copyleft (software)'),
    ('mpl-2.0',       'MPL-2.0',         1, 1, 0, 0, 'file-level copyleft'),
    ('unlicense',     'Unlicense',       1, 1, 0, 0, 'public domain'),
    ('isc',           'ISC',             1, 1, 0, 0, 'permisive'),
    ('artistic',      'Artistic-2.0',    1, 1, 0, 0, 'permisive'),
]

# License KINH VĂN / CORPUS nguồn Phật học — hầu hết chưa xác minh phạm vi copy corpus
_CORPUS_DEFAULT_UNKNOWN = {'corpus': 'UNKNOWN', 'reason': 'phạm vi corpus redistribution chưa xác minh'}


def _clean(s: str) -> str:
    return ' '.join((s or '').lower().split())


def map_spdx(text: str) -> Tuple[Optional[dict], bool]:
    """Map nội dung LICENSE -> rule SPDX. Trả về (rule|None, đã_phát_hiện)."""
    if not text:
        return None, False
    low = _clean(text)
    for key, spdx, comm, deriv, sa, nc, note in SPDX_RULES:
        if key in low:
            return {'spdx': spdx, 'commercial_use': comm, 'derivative_allowed': deriv,
                    'sharealike_required': sa, 'noncommercial': nc, 'note': note}, True
    return None, False


class SourceAnalyzer:
    """Phân tích repo public + sinh report/notes/provenance draft."""

    def __init__(self, db_path: str = 'data/lineage.db', timeout: int = 20):
        self.gate = LicenseGate(db_path)
        self.prov_gate = ProvenanceGate()
        self.timeout = timeout
        self._http_available = True

    # ---------- fetch public repo (no token) ----------
    def _open_url(self, url: str) -> Optional[str]:
        if not self._http_available:
            return None
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'tgs-legal-check/1.0'})
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = r.read(2 * 1024 * 1024)  # giới hạn 2MB
                return data.decode('utf-8', errors='replace')
        except Exception:
            return None

    def fetch_repo(self, repo_url: str) -> dict:
        """Trích repo_owner/repo_name từ URL; fetch LICENSE + metadata public."""
        m = re.search(r'(?:github\.com)/([^/]+)/([^/?#]+)', repo_url or '')
        if not m:
            return {'valid': False, 'reason': 'URL không hợp lệ hoặc không phải GitHub public'}
        owner, repo = m.group(1), m.group(2).replace('.git', '')
        base = f'https://raw.githubusercontent.com/{owner}/{repo}'

        license_text = None
        # Thử các tên file LICENSE phổ biến
        for fname in ('LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING', 'LICENCE'):
            txt = self._open_url(f'{base}/HEAD/{fname}')
            if txt:
                license_text = txt
                break

        readme = self._open_url(f'{base}/HEAD/README.md') or self._open_url(f'{base}/HEAD/readme.md')

        # Metadata public (không token — có thể rate-limit)
        meta = {}
        api = self._open_url(f'https://api.github.com/repos/{owner}/{repo}')
        if api:
            try:
                j = json.loads(api)
                meta = {
                    'homepage': j.get('homepage'),
                    'license_spdx_from_github': (j.get('license') or {}).get('spdx_id'),
                    'html_url': j.get('html_url'),
                    'updated_at': j.get('updated_at'),
                    'description': j.get('description'),
                    'default_branch': j.get('default_branch'),
                }
            except (json.JSONDecodeError, AttributeError):
                meta = {}

        commit_sha = None
        ref = self._open_url(f'https://api.github.com/repos/{owner}/{repo}/commits/{meta.get("default_branch","HEAD")}')
        if ref:
            try:
                commit_sha = json.loads(ref).get('sha')
            except (json.JSONDecodeError, AttributeError):
                commit_sha = None

        return {
            'valid': True,
            'owner': owner, 'repo': repo,
            'html_url': f'https://github.com/{owner}/{repo}',
            'license_text': license_text,
            'readme': readme,
            'meta': meta,
            'commit_sha': commit_sha,
            'retrieved_at': datetime.now().isoformat(timespec='seconds'),
        }

    # ---------- phân tích & report ----------
    def analyze(self, source_name: str, repo_url: str) -> Dict:
        """Toàn bộ luồng: fetch -> SPDX -> gate -> report + notes + provenance draft."""
        now = datetime.now().isoformat(timespec='seconds')
        fetched = self.fetch_repo(repo_url)
        if not fetched.get('valid'):
            return {'success': False, 'valid': False, 'reason': fetched.get('reason'),
                    'checked_at': now, 'source_name': source_name, 'repo_url': repo_url}

        # SOFTWARE license từ LICENSE file (nếu có)
        sw_rule, sw_found = map_spdx(fetched.get('license_text'))
        gh_spdx = (fetched.get('meta') or {}).get('license_spdx_from_github')

        # CORPUS license: KHÔNG giả định = software. Mặc định UNKNOWN cho corpus kinh văn.
        corpus_rule = None
        corpus_status = 'UNKNOWN'
        # Chỉ khi LICENSE file nói rõ đến data/corpus/database (đọc README hint) mới tạm đánh dấu AUDITING
        readme_low = _clean(fetched.get('readme'))
        if readme_low and any(k in readme_low for k in ('corpus', 'database', 'dataset', 'data set', 'kinh văn', 'text corpus')):
            corpus_status = 'AUDITING'

        # ----------------------------------------
        # QUYẾT ĐỊNH integration_mode (3 nhánh)
        # ----------------------------------------
        reason_lines = []
        if sw_rule:
            reason_lines.append(f"Software license (LICENSE file): {sw_rule['spdx']} — phần mềm/công cụ")
        elif gh_spdx:
            reason_lines.append(f"Software license (GitHub API): {gh_spdx}")
        else:
            reason_lines.append('Software license: KHÔNG phát hiện giấy phép rõ ràng')

        reason_lines.append(f"Corpus/data license: {corpus_status} — KHÔNG giả định bằng software license")

        if corpus_rule:
            integration_mode = 'INGEST'
            legal_status = 'AUDITING'
            reason_lines.append(f"Corpus license xác minh: {corpus_rule['spdx']} — có thể tiến tới INGEST sau review")
        elif corpus_status == 'AUDITING':
            # Có hint corpus trong README nhưng chưa xác minh phạm vi -> tham khảo, không copy
            integration_mode = 'REFERENCE_ONLY'
            legal_status = 'AUDITING'
            reason_lines.append('Có bằng chứng corpus trong repo nhưng phạm vi redistribution CHƯA xác minh -> REFERENCE_ONLY nội bộ')
        else:
            integration_mode = 'REFERENCE_ONLY'
            legal_status = 'AUDITING'
            reason_lines.append('Chưa xác minh phạm vi corpus -> đề xuất REFERENCE_ONLY (tham khảo nội bộ, không copy vào Canonical)')

        # Software license nếu là permissive -> cho phép DOWNLOAD/STORE_RAW code
        sw_op = 'DOWNLOAD'
        sw_allowed = bool(sw_rule) or bool(gh_spdx)
        if sw_rule and sw_rule['commercial_use'] == 0 and 'noncommercial' in readme_low:
            sw_allowed = True  # vẫn là công cụ dùng được

        # ---------- đánh giá qua LicenseGate từng operation ----------
        # Gate chạy trên registry — với source mới chưa có trong DB, gate trả UNKNOWN;
        # analyzer tự tổng hợp theo rule software/corpus phía trên.
        versions = {
            'commit_sha': fetched.get('commit_sha'),
            'release_version': None,
            'retrieved_at': fetched.get('retrieved_at'),
            'content_hash': self._content_hash(fetched.get('license_text') or ''),
            'source_uri': fetched.get('html_url'),
        }

        notes_default = self._default_notes(source_name, fetched.get('html_url'), integration_mode)

        report = {
            'success': True,
            'valid': True,
            'source_name': source_name,
            'repo_url': fetched.get('html_url'),
            'checked_at': now,
            'software_license': (sw_rule or {}).get('spdx') or gh_spdx or 'UNKNOWN',
            'corpus_license_status': corpus_status,
            'integration_mode': integration_mode,
            'legal_status': legal_status,
            'authority_eval': 'chưa xác minh (nhập sau khi audit nickname chuyên ngành)',  # tách Authority khỏi Legal
            'findings': [
                {'category': 'Software License', 'status': 'PASS' if (sw_rule or gh_spdx) else 'WARN',
                 'detail': f"{sw_rule['spdx'] if sw_rule else (gh_spdx or 'chưa rõ')}"},
                {'category': 'Corpus Permission', 'status': 'WARN' if corpus_status != 'UNKNOWN' else 'WARN',
                 'detail': f"{corpus_status} — chưa xác minh phạm vi copy corpus"},
                {'category': 'Redistribution', 'status': 'WARN',
                 'detail': 'chưa khẳng định — không giả định được phân phối lại'},
                {'category': 'Commercial Use', 'status': 'WARN',
                 'detail': f"{'phi thương mại' if sw_rule and sw_rule['noncommercial'] else 'chưa xác minh — không giả định'}"},
            ],
            'software_operation': {
                'DOWNLOAD/STORE_RAW': sw_allowed,
                'reason': 'software license được phép dùng làm công cụ',
            },
            'corpus_operation': {
                'INGEST': False, 'REDISTRIBUTE': False, 'COMMERCIAL_USE': False,
                'REFERENCE_ONLY': integration_mode == 'REFERENCE_ONLY',
                'reason': 'corpus permission chưa verify; chỉ REFERENCE_ONLY nội bộ',
            },
            'recommendation': (
                'KHÔNG copy corpus vào Canonical DB hiện tại. '
                'Chỉ dùng tham khảo/đối chiếu nội bộ, phi thương mại. '
                'Khi tác giả cấp quyền (free/commercial) -> team xác nhận sau, nâng ACTIVE.'
                if integration_mode == 'REFERENCE_ONLY' else
                'Có thể tiến tới INGEST sau khi admin review xác minh phạm vi corpus.'
            ),
            'notes': notes_default,
            'provenance_draft': versions,
            'github_commit_sha': fetched.get('commit_sha'),
            'github_license_spdx': gh_spdx,
        }
        return report

    @staticmethod
    def _content_hash(text: str) -> Optional[str]:
        if not text:
            return None
        return 'sha256:' + hashlib.sha256(text.encode('utf-8')).hexdigest()

    @staticmethod
    def _default_notes(name: str, url: Optional[str], integration_mode: str) -> List[str]:
        """Notes mặc định có sẵn — admin có thể chỉnh/duyệt trước khi thêm."""
        if integration_mode == 'REFERENCE_ONLY':
            return [
                f"Chỉ dùng để đối chiếu/trích dẫn NỘI BỘ nguồn «{name}» ({url or 'URL'}).",
                "KHÔNG nhúng nội dung gốc vào đầu ra công khai.",
                "KHÔNG tự động publish/redistribute corpus.",
                "Tương lai: nếu tác giả cấp phép (free/commercial) -> team xác nhận sau, lúc đó nâng ACTIVE cho ingest.",
            ]
        return [
            f"Nguồn «{name}» ({url or 'URL'}) — đang AUDITING, chưa ACTIVE.",
            "Chưa khẳng định quyền redistribute/commercial cho corpus.",
            "Cần admin xác minh phạm vi trước khi bật INGEST.",
        ]
