#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T78 — LEGAL/LICENSE FIREWALL — Gói Gate
========================================
Tầng GOVERNANCE/SOURCE CONTROL phía trước ingestion (không phá B1/B2).
Đọc data từ `data_sources` (Source Registry) — data-driven, không if/else per-source.

- gate/status.py  : máy trạng thái legal + quyết định quyền theo status
- gate/license.py : LicenseGate.checkSourcePermission(source_id, operation)
- gate/provenance.py : ProvenanceGate — bắt buộc provenance khi ingest mới
- gate/analyzer.py   : phân tích repo (fetch LICENSE/README public, SPDX map, notes đề nghị)
- gate/registry.py   : reader tiện ích đọc data_sources

Nguyên tắc thiết kế:
  PUBLIC ≠ FREE TO USE · GITHUB PUBLIC ≠ LICENSE · SOFTWARE ≠ CORPUS
  AUTHORITY ≠ INGEST PERMISSION · REFERENCE ≠ COPY · SOURCE ≠ CANONICAL
  KHÔNG có DEFAULT = ACTIVE.
"""
