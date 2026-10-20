#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T77 — BDRC adapter (skeleton / ví dụ contract)
===============================================
Ví dụ concrete triển khai `SourceAdapter` — KHÔNG phải harvester thật (data BDRC chưa
integrated, `implemented=0`). Đây là mẫu để nguồn mới bắt chước khi gia nhập TGS.

Ghi chú Build hard-rules:
- Chỉ additive, minh hoạ contract; KHÔNG đụng canonical core / harvester hiện có.
- BDRC: `data_sources` có, `source_id=2` (active=0), `implemented=0` — chưa có data thật.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from adapters.base import SourceAdapter, ExtractedEvidence


class BDRCAdapter(SourceAdapter):
    """Adapter cho Buddhist Digital Resource Center (BDRC).

    Hiện là skeleton minh hoạ (chưa có data/pipeline). Khi tích hợp thật (Build 3+),
    override `search`/`resolve` để fetch từ API BDRC và chuẩn hoá ra ExtractedEvidence.
    """

    source_code = 'BDRC'
    capabilities = ['search', 'resolve', 'external_id']
    adapter_version = '0.1'

    def search(self, query: str, **kw) -> List[ExtractedEvidence]:
        # Skeleton: BDRC chưa integrated — trả về rỗng, ghi rõ trạng thái.
        # Build 3 GĐ2: thay bằng lời gọi API thật.
        return []

    def resolve(self, record_id: str, **kw) -> Optional[ExtractedEvidence]:
        # Skeleton: chưa có data thật để resolve.
        return None

    def get_provenance(self, ev: ExtractedEvidence) -> Dict[str, Any]:
        # Truy ngược source -> record -> reference (Evidence Graph).
        return {
            'source_code': ev.source_code,
            'source_record_id': ev.source_record_id,
            'source_reference': ev.source_reference,
            'source_url': ev.source_url,
            'retrieved_at': ev.retrieved_at,
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            'source_code': self.source_code,
            'health': 'conector_only',   # chưa implement pipeline/data
            'checked_at': datetime.now().isoformat(),
            'note': 'BDRC chưa integrated (implemented=0) — connector chỉ có adapter skeleton',
        }


def register(registry) -> None:
    """Đăng ký adapter vào registry (để SourceAdapterRegistry.load() nhặt được)."""
    registry.register(BDRCAdapter())
