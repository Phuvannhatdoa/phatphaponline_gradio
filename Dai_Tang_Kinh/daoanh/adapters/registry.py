#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T77 — Build 3 (G1): SourceAdapterRegistry
=========================================
Nạp/dispatch adapter theo `data_sources` (data-driven). Registry đọc từ DB xem nguồn
nào có adapter đăng ký + capabilities gì, rồi map tới instance thích hợp.

Mục đích: để "thêm nguồn" = đăng ký 1 dòng `data_sources` + cung cấp 1 adapter.
KHÔNG sửa `entity_unified` — đây là tầng orchestration, additive cho tương lai.

Cách dùng (demo/test):
    from adapters.registry import SourceAdapterRegistry
    reg = SourceAdapterRegistry(db_path='data/lineage.db')
    reg.load()                 # nhặt adapter có sẵn theo data_sources
    print(reg.list_sources())  # nguồn + adapter + capabilities
"""
import json
import sqlite3
from typing import Dict, List, Optional

from .base import SourceAdapter, ExtractedEvidence  # noqa: F401


class SourceAdapterRegistry:
    """Đăng ký + dispatch adapter. Data-driven từ `data_sources`."""

    def __init__(self, db_path: str = 'data/lineage.db'):
        self.db_path = db_path
        # source_code -> SourceAdapter instance
        self._adapters: Dict[str, SourceAdapter] = {}
        # source_code -> registry row (từ data_sources)
        self._registry_row: Dict[str, dict] = {}
        # license_gate: LicenseGate tùy chọn (T78) — nếu thiết lập, dispatch kiểm tra trước
        self.license_gate = None

    def register(self, adapter: SourceAdapter) -> None:
        """Đăng ký 1 adapter theo source_code của nó (idempotent)."""
        if not adapter.source_code:
            raise ValueError('adapter.source_code trống — không thể đăng ký')
        self._adapters[adapter.source_code] = adapter

    def _fetch_registry(self) -> List[dict]:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            cols = [d[1] for d in conn.execute('PRAGMA table_info(data_sources)')]
            sel = 'source_code, source_id'
            if 'source_version' in cols:
                sel += ', source_version'
            if 'adapter_version' in cols:
                sel += ', adapter_version'
            if 'capabilities' in cols:
                sel += ', capabilities'
            if 'enabled' in cols:
                sel += ', enabled'
            rows = [dict(r) for r in conn.execute(f'SELECT {sel} FROM data_sources')]
            return rows
        finally:
            conn.close()

    def load(self) -> Dict[str, dict]:
        """Đối chiếu adapter đã đăng ký với data_sources. Trả map source_code -> mô tả."""
        merged = {}
        for row in self._fetch_registry():
            code = row['source_code']
            self._registry_row[code] = row
            merged[code] = {
                'source_code': code,
                'source_id': row.get('source_id'),
                'source_version': row.get('source_version'),
                'adapter_version': row.get('adapter_version'),
                'capabilities': self._parse_caps(row.get('capabilities')),
                'enabled': row.get('enabled', row.get('active', 1)),
                'has_adapter': code in self._adapters,
                'adapter': self._adapters[code].describe() if code in self._adapters else None,
            }
        return merged

    @staticmethod
    def _parse_caps(raw) -> List[str]:
        if not raw:
            return []
        try:
            v = json.loads(raw) if isinstance(raw, str) else raw
            return list(v) if isinstance(v, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def get(self, source_code: str) -> Optional[SourceAdapter]:
        return self._adapters.get(source_code)

    def list_sources(self) -> List[dict]:
        return list(self.load().values())

    def dispatch(self, source_code: str, operation: str = 'READ_METADATA'):
        """Lấy adapter; raise nếu chưa đăng ký. Nếu LicenseGate được thiết lập (T78),
        kiểm tra quyền operation TRƯỚC khi dispatch — KHÔNG ingest nếu gate chặn."""
        # Firewall: gate hành động như SOURCE GATE trước adapter (nếu được gắn)
        if self.license_gate is not None:
            row = self._registry_row.get(source_code)
            source_id = row.get('source_id') if row else None
            if source_id is None:
                # source chưa đăng ký trong registry -> UNKNOWN -> không truy cập
                raise PermissionError(f'source_code={source_code!r} chưa đăng ký trong Source Registry '
                                      f'(legal firewall: UNKNOWN -> không cho truy cập)')
            decision = self.license_gate.checkSourcePermission(source_id, operation)
            if not decision.get('allowed'):
                raise PermissionError(
                    f'source_code={source_code!r} bị LicenseGate chặn (status={decision.get("status")}, '
                    f'op={operation}): {decision.get("reason")}')
        a = self._adapters.get(source_code)
        if a is None:
            raise KeyError(f'chưa có adapter cho source_code={source_code!r}')
        return a
