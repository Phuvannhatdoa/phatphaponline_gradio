#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T77 — Build 3 (G1): SourceAdapter base contract
===============================================
Khung (skeleton) hợp đồng adapter nguồn dữ liệu — phục vụ "READY FOR FUTURE SOURCE
INTEGRATION". KHÔNG rewrite các harvester hiện hữu; chỉ định nghĩa contract chuẩn để
nguồn mới gia nhập TGS một cách nhất quán, data-driven qua `data_sources.capabilities`.

Triết lý: adapter là lớp "biến data nguồn thô → evidence TGS có provenance".
Mọi source khi tích hợp phải trả về `ExtractedEvidence` kèm:
- source_id/source_code (từ registry)
- source_record_id + source_reference (provenance)
- retrieved_at (mốc lấy dữ liệu)

Lưu ý Build hard-rules:
- Chỉ additive; KHÔNG đụng `entity_unified`, routes clone, `geo_cross_ref`, canonical.
- Các harvester hiện có (dila_harvester, marcus_harvester...) sẽ được wrap sau (Build 3 GĐ 2),
  KHÔNG viết lại hôm nay.
"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class ExtractedEvidence:
    """Một mẩu evidence chuẩn hóa từ nguồn — có provenance đầy đủ."""
    source_code: str
    claim_type: str                 # EXTERNAL_ID / NAME / GEOGRAPHY / TEXTUAL / ...
    subject: str
    predicate: str
    object_text: Optional[str] = None
    source_record_id: Optional[str] = None
    source_reference: Optional[str] = None   # ref cụ thể trong nguồn
    source_url: Optional[str] = None
    retrieved_at: Optional[str] = None
    confidence: Optional[float] = None
    # T132 P3 §6 §12: license contract fields (default None = REVIEW_REQUIRED)
    license: Optional[str] = None
    license_status: Optional[str] = None    # GREEN/YELLOW/RED/REVIEW_REQUIRED
    source_version: Optional[str] = None    # version nguồn lúc lấy
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


class SourceAdapter(ABC):
    """Hợp đồng tối thiểu mà mọi adapter nguồn TGS phải triển khai.

    Một adapter:
      - khai báo source_code + capabilities
      - fetch/search: lấy dữ liệu từ nguồn (có thể là local DB, API, file — tùy nguồn)
      - resolve/normalize: quy về `ExtractedEvidence` có provenance
      - get_provenance: từ một evidence trả về chuỗi truy ngược (source -> record -> ref)
      - health_check: trạng thái nguồn
    """

    # source_code khớp với data_sources.source_code
    source_code: str = ''

    # khả năng nguồn — khớp với data_sources.capabilities (JSON)
    capabilities: List[str] = field(default_factory=list)

    # version adapter — khớp data_sources.adapter_version
    adapter_version: str = '0.1'

    @abstractmethod
    def search(self, query: str, **kw) -> List[ExtractedEvidence]:
        """Tìm kiếm trong nguồn, trả về danh sách evidence chuẩn hóa."""

    @abstractmethod
    def resolve(self, record_id: str, **kw) -> Optional[ExtractedEvidence]:
        """Lấy 1 record cụ thể theo ID nguồn."""

    @abstractmethod
    def get_provenance(self, ev: ExtractedEvidence) -> Dict[str, Any]:
        """Truy ngược: source -> record -> reference (cho Evidence Graph)."""

    def normalize(self, raw: Any, **kw) -> Optional[ExtractedEvidence]:
        """Biến 1 record thô của nguồn thành evidence chuẩn. Mặc định: không làm gì
        nếu adapter chưa định nghĩa (Build 3 GĐ 2 wrap harvester sẽ override)."""
        return None

    def health_check(self) -> Dict[str, Any]:
        """Trạng thái nguồn. Mặc định unknown cho tới khi adapter implement."""
        return {
            'source_code': self.source_code,
            'health': 'unknown',
            'checked_at': datetime.now().isoformat(),
            'note': 'adapter skeleton — chưa implement health check',
        }

    def describe(self) -> Dict[str, Any]:
        return {
            'source_code': self.source_code,
            'capabilities': self.capabilities,
            'adapter_version': self.adapter_version,
        }

    # ── T132 P3: §6 optional default methods ──────────────────────────────────

    def lookup_entity(self, record_id: str, **kw) -> Optional[ExtractedEvidence]:
        """Phân giải alias/record_id → evidence chuẩn. Mặc định: None (chưa implement)."""
        return None

    def get_identifier(self, record_id: str, **kw) -> Optional[str]:
        """Trả về identifier đặc thù của nguồn từ record_id chung. Mặc định: record_id."""
        return record_id

    def get_license(self, **kw) -> Dict[str, Any]:
        """Thông tin license của nguồn. Mặc định: yêu cầu review.
        Override trong adapter cụ thể hoặc đọc từ data_sources."""
        return {
            'source_code': self.source_code,
            'license': None,
            'license_status': 'REVIEW_REQUIRED',
            'source_version': None,
            'note': 'default — override trong adapter cụ thể hoặc đọc data_sources',
        }


def to_json(obj) -> str:
    """Tiện ích: evidence -> JSON (cho test/log)."""
    if isinstance(obj, ExtractedEvidence):
        return json.dumps(obj.to_dict(), ensure_ascii=False)
    if isinstance(obj, (list, tuple)):
        return json.dumps([e.to_dict() for e in obj], ensure_ascii=False)
    return json.dumps(obj, ensure_ascii=False, default=str)
