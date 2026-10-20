#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T78 — LegalStatus + quyết định quyền theo status (data-driven từ data_sources)
==============================================================================
Máy trạng thái pháp lý. KHÔNG có DEFAULT=ACTIVE. Authority ≠ Legal.

Trạng thái:
  DISCOVERED / AUDITING / VERIFIED / APPROVED / ACTIVE   (chuỗi tích lũy phê duyệt)
  UNKNOWN / REFERENCE_ONLY / BLOCKED / FROZEN            (trạng thái chặn/giới hạn)

Quy tắc:
  UNKNOWN      -> KHÔNG INGEST
  BLOCKED      -> KHÔNG INGEST
  FROZEN       -> KHÔNG INGEST MỚI (giữ historical)
  REFERENCE_ONLY -> chỉ citation/reference, không copy corpus vào Canonical
  APPROVED     -> chưa nhất thiết ACTIVE
  ACTIVE       -> được phép ingest theo policy
"""
from datetime import datetime
from typing import Dict, Optional


# Các status cho phép INGEST dữ liệu MỚI (theo §5 rules)
_NON_INGEST = {'UNKNOWN', 'BLOCKED', 'FROZEN', 'AUDITING', 'DISCOVERED', 'VERIFIED', 'APPROVED'}

# Operation mà một status mặc định cho phép (bổ sung policy cụ thể hơn nữa ở LicenseGate)
_STATUS_DEFAULT = {
    'READ_METADATA':   {'ACTIVE', 'APPROVED', 'REFERENCE_ONLY', 'AUDITING', 'VERIFIED', 'DISCOVERED'},
    'DOWNLOAD':        {'ACTIVE', 'APPROVED', 'REFERENCE_ONLY'},
    'STORE_RAW':       {'ACTIVE', 'APPROVED', 'REFERENCE_ONLY'},
    'TRANSFORM':       {'ACTIVE', 'APPROVED', 'REFERENCE_ONLY'},
    'DERIVE':          {'ACTIVE', 'APPROVED'},
    'INGEST':          {'ACTIVE'},
    'REDISTRIBUTE':    {'ACTIVE'},
    'COMMERCIAL_USE':  {'ACTIVE'},
}


def is_non_ingest(status: str) -> bool:
    """status có chặn INGEST dữ liệu mới?"""
    return status in _NON_INGEST


def default_allows(status: str, operation: str) -> bool:
    """Kiểm tra mặc định status có cho phép operation không (KHÔNG += legal rules chi tiết)."""
    allowed = _STATUS_DEFAULT.get(operation, set())
    return status in allowed


class LegalStatus:
    """Máy trạng thái legal cho một source (đọc từ data_sources)."""

    VALID = {'DISCOVERED', 'AUDITING', 'VERIFIED', 'APPROVED', 'ACTIVE',
             'UNKNOWN', 'REFERENCE_ONLY', 'BLOCKED', 'FROZEN'}

    def __init__(self, source_id=None, source_code=None, legal_status='UNKNOWN',
                 data_license_status='UNKNOWN', integration_mode='BLOCKED',
                 source=None):
        self.source_id = source_id
        self.source_code = source_code
        self.legal_status = (legal_status or 'UNKNOWN').upper()
        self.data_license_status = (data_license_status or 'UNKNOWN').upper()
        self.integration_mode = (integration_mode or 'BLOCKED').upper()
        self._source = source or {}

    def __repr__(self):
        return (f"LegalStatus({self.source_code}, legal={self.legal_status}, "
                f"data={self.data_license_status}, mode={self.integration_mode})")

    def can_ingest(self) -> bool:
        """Data mới được phép đi vào Canonical?"""
        if self.legal_status != 'ACTIVE':
            return False
        if self.data_license_status in {'UNKNOWN', 'BLOCKED', 'FROZEN'}:
            return False
        return self.integration_mode == 'INGEST'

    def can_reference(self) -> bool:
        """Được dùng cho mục đích tham khảo/trích dẫn nội bộ?"""
        return self.legal_status in {'REFERENCE_ONLY', 'APPROVED', 'ACTIVE', 'AUDITING', 'VERIFIED'}

    def to_dict(self) -> Dict:
        return {
            'source_id': self.source_id,
            'source_code': self.source_code,
            'legal_status': self.legal_status,
            'data_license_status': self.data_license_status,
            'integration_mode': self.integration_mode,
            'can_ingest': self.can_ingest(),
            'can_reference': self.can_reference(),
        }
