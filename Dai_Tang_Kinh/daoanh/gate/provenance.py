#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T78 — ProvenanceGate
====================
Bảo đảm mọi Evidence ingest vào TGS đều có provenance bắt buộc. Nếu thiếu
trường bắt buộc => REJECT. KHÔNG tạo Canonical Fact từ Evidence thiếu provenance.

Trường bắt buộc (theo §8):
  source_id, source_uri, source_version, commit_sha hoặc release_version,
  retrieved_at, content_hash, license_status, transformation, evidence_type

Version pinning: KHÔNG dùng "latest" làm provenance duy nhất.
"""
from datetime import datetime
from typing import Dict, List, Optional


class ProvenanceGate:
    """Kiểm tra provenance bắt buộc trước khi cho phép ingest."""

    REQUIRED = [
        'source_id', 'source_uri', 'source_version', 'retrieved_at',
        'content_hash', 'license_status', 'transformation', 'evidence_type',
    ]
    # Cần một trong hai (commit_sha HOẶC release_version)
    _VERSION_SHA = {'commit_sha', 'release_version'}
    _BAD_LATEST = {'latest', 'main', 'master', 'head'}

    def __init__(self, require_version_pin: bool = False):
        # require_version_pin: policy per-source; nếu True => bắt buộc commit/release cụ thể
        self.require_version_pin = require_version_pin

    def check(self, provenance: dict) -> Dict:
        """Kiểm tra. Trả về {passed, reason, missing, needs_manual_pin}."""
        now = datetime.now().isoformat(timespec='seconds')
        prov = provenance or {}
        missing = [k for k in self.REQUIRED if not prov.get(k)]

        # Bắt buộc version pin: phải có commit_sha HOẶC release_version (không phải latest)
        pin_status = 'none'
        has_sha = bool(prov.get('commit_sha'))
        has_release = bool(prov.get('release_version'))
        if has_sha:
            pin_status = 'git_pin'
        elif has_release:
            pin_status = 'release_pin'
            if str(prov.get('release_version')).strip().lower() in self._BAD_LATEST:
                pin_status = 'bad_latest'
        elif self.require_version_pin:
            missing.append('commit_sha/release_version')

        if missing:
            return {
                'passed': False,
                'reason': f"thiếu provenance bắt buộc: {', '.join(sorted(set(missing)))}",
                'missing': sorted(set(missing)),
                'pin_status': pin_status,
                'checked_at': now,
            }

        if pin_status == 'bad_latest':
            return {
                'passed': False,
                'reason': "'latest' không được dùng làm provenance duy nhất — cần commit_sha/release cụ thể",
                'missing': ['commit_sha/release_version'],
                'pin_status': pin_status,
                'checked_at': now,
            }

        return {
            'passed': True,
            'reason': 'provenance đầy đủ',
            'missing': [],
            'pin_status': pin_status,
            'checked_at': now,
        }

    def source_version_policy(self, policy: str) -> 'ProvenanceGate':
        """Cấu hình theo version_policy của source."""
        self.require_version_pin = policy == 'git_pin' or policy == 'release_pin'
        return self
