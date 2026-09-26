#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T78 — LicenseGate
=================
Kiểm tra quyền sử dụng cho một source theo operation, dựa trên `data_sources`
(Source Registry). Trả về đối tượng đầy đủ (không phải boolean):

    checkSourcePermission(source_id, operation)
    -> { allowed, status, reason, license, source_id, checked_at }

Operations: READ_METADATA / DOWNLOAD / STORE_RAW / TRANSFORM / DERIVE /
            INGEST / REDISTRIBUTE / COMMERCIAL_USE

Nguyên tắc:
  - Tách SOFTWARE LICENSE ≠ DATA/CORPUS LICENSE (MIT repo ≠ corpus APPROVED).
  - UNKNOWN/BLOCKED/FROZEN => KHÔNG INGEST.
  - REFERENCE_ONLY => chỉ citation, không copy corpus vào Canonical.
  - AUTHORITY ≠ LEGAL: không dùng authority_score để approve legal.
"""
import json
import sqlite3
from datetime import datetime
from typing import Dict, Optional

from .status import LegalStatus, default_allows


class LicenseGate:
    """Cổng kiểm tra quyền pháp lý. Data-driven từ data_sources."""

    OPERATIONS = ['READ_METADATA', 'DOWNLOAD', 'STORE_RAW', 'TRANSFORM',
                  'DERIVE', 'INGEST', 'REDISTRIBUTE', 'COMMERCIAL_USE']

    # Operation cần quyền DATA (không chỉ software)
    _DATA_OPERATIONS = {'INGEST', 'REDISTRIBUTE', 'COMMERCIAL_USE', 'DERIVE', 'TRANSFORM'}

    def __init__(self, db_path: str = 'data/lineage.db'):
        self.db_path = db_path

    def _get_source(self, source_id) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            cols = [d[1] for d in conn.execute('PRAGMA table_info(data_sources)')]
            row = conn.execute('SELECT * FROM data_sources WHERE source_id = ?', (source_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def _license_summary(self, row: dict, cols: list) -> dict:
        def g(name, fallback=None):
            return row.get(name) if name in cols else fallback
        return {
            'software': g('software_license') or g('license_note'),
            'data': g('data_license'),
            'corpus': g('corpus_license'),
            'spdx': g('license_spdx'),
        }

    def checkSourcePermission(self, source_id, operation: str) -> Dict:
        """Kiểm tra quyền. Trả về đối tượng đầy đủ."""
        row = self._get_source(source_id)
        now = datetime.now().isoformat(timespec='seconds')
        if row is None:
            return {
                'allowed': False, 'status': 'UNKNOWN',
                'reason': 'source_id không tồn tại trong Source Registry',
                'license': {}, 'source_id': source_id, 'checked_at': now,
            }

        cols = list(row.keys())
        status = (row.get('legal_status') or 'UNKNOWN').upper()
        data_status = (row.get('data_license_status') or 'UNKNOWN').upper()
        ls = LegalStatus(source_id=source_id, source_code=row.get('source_code'),
                         legal_status=status, data_license_status=data_status,
                         integration_mode=row.get('integration_mode'), source=row)

        lic = self._license_summary(row, cols)
        need_data = operation in self._DATA_OPERATIONS
        effective_status = data_status if need_data else status

        reason_lines = []

        # 1) Trạng thái pháp lý chung
        if status in {'BLOCKED', 'UNKNOWN', 'FROZEN'}:
            freeze = f" ({row.get('freeze_reason')})" if row.get('freeze_reason') else ''
            return {
                'allowed': False, 'status': status,
                'reason': f"legal_status={status}{freeze} => KHÔNG INGEST",
                'license': lic, 'source_id': source_id, 'checked_at': now,
            }

        # 2) Operation dùng DATA -> cần data_license_status hợp lệ
        if need_data:
            if data_status in {'UNKNOWN', 'BLOCKED', 'FROZEN'}:
                return {
                    'allowed': False, 'status': data_status,
                    'reason': f"op={operation} cần quyền DATA; data_license_status={data_status}",
                    'license': lic, 'source_id': source_id, 'checked_at': now,
                }
            if operation == 'INGEST' and not ls.can_ingest():
                return {
                    'allowed': False, 'status': status,
                    'reason': f"legal_status={status} chưa ACTIVE (hoặc integration_mode={row.get('integration_mode')}) — data mới chưa được ingest",
                    'license': lic, 'source_id': source_id, 'checked_at': now,
                }

        # 3) REFERENCE_ONLY: chỉ cho citation/reference, không copy corpus
        if status == 'REFERENCE_ONLY':
            if operation in {'INGEST', 'REDISTRIBUTE', 'COMMERCIAL_USE'}:
                return {
                    'allowed': False, 'status': 'REFERENCE_ONLY',
                    'reason': 'REFERENCE_ONLY: chỉ citation/reference nội bộ; không copy corpus vào Canonical / không redistribute / không thương mại',
                    'license': lic, 'source_id': source_id, 'checked_at': now,
                }
            return {
                'allowed': True, 'status': 'REFERENCE_ONLY',
                'reason': 'REFERENCE_ONLY: cho phép tham khảo/đối chiếu nội bộ, phi thương mại',
                'license': lic, 'source_id': source_id, 'checked_at': now,
            }

        # 4) Kiểm tra mặc định status cho phép operation
        if not default_allows(status, operation):
            return {
                'allowed': False, 'status': status,
                'reason': f"legal_status={status} không cho phép operation {operation}",
                'license': lic, 'source_id': source_id, 'checked_at': now,
            }

        # 5) Ràng buộc license cụ thể (phần bổ sung theo rules)
        if operation == 'COMMERCIAL_USE' and not row.get('data_commercial', 0):
            return {
                'allowed': False, 'status': status,
                'reason': 'quyền thương mại chưa được khẳng định (data_commercial=0 hoặc chưa verify)',
                'license': lic, 'source_id': source_id, 'checked_at': now,
            }
        if operation == 'REDISTRIBUTE' and not row.get('data_redistribution', 0):
            return {
                'allowed': False, 'status': status,
                'reason': 'quyền phân phối lại chưa được khẳng định (data_redistribution=0 hoặc chưa verify)',
                'license': lic, 'source_id': source_id, 'checked_at': now,
            }

        # Nếu data chưa verified nhưng operation không cần data (chỉ software/metadata)
        return {
            'allowed': True, 'status': status,
            'reason': f"cho phép operation {operation} (status={status})",
            'license': lic, 'source_id': source_id, 'checked_at': now,
        }

    # ── T132 P2: convenience wrappers §11 ─────────────────────────────────────

    def can_display(self, source_id) -> Dict:
        """Hiển thị metadata/citation từ nguồn (READ_METADATA).
        Spec §11: display = metadata access, không copy corpus."""
        return self.checkSourcePermission(source_id, 'READ_METADATA')

    def can_quote(self, source_id) -> Dict:
        """Dẫn/trích nội dung (DERIVE — derived data).
        Spec §11: quote = derived-data access, cần data license xác nhận."""
        return self.checkSourcePermission(source_id, 'DERIVE')
