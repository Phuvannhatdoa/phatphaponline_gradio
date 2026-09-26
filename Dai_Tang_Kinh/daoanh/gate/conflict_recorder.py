#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T132 P5 — ConflictRecorder
==========================
Ghi nhận conflict dữ liệu giữa 2 nguồn vào bảng `conflict_pending` (spec §9).

Thiết kế:
- Additive INSERT OR IGNORE — không overwrite conflict đã tồn tại.
- Không tự quyết định (human-in-loop): status='pending', resolved_by/resolved_at NULL.
- entity_ref = canonical entity ID (PL…, A…, etc.).
- source_a/source_b = source_code từ data_sources.
- conflict_pending schema: entity_ref, field, value_a, value_b, source_a, source_b,
  status (pending/reviewed/resolved/ignored), needs_review, created_at.
"""
import sqlite3
from datetime import datetime
from typing import Optional


class ConflictRecorder:
    """Ghi conflict dữ liệu vào conflict_pending (INSERT OR IGNORE, không quyết định)."""

    def __init__(self, db_path: str = 'data/lineage.db'):
        self.db_path = db_path

    def _ensure_cols(self, conn: sqlite3.Connection) -> None:
        """Đảm bảo conflict_pending có cột needs_review (additive, T132 P1 đã thêm)."""
        cols = {r[1] for r in conn.execute('PRAGMA table_info(conflict_pending)')}
        if 'needs_review' not in cols:
            conn.execute('ALTER TABLE conflict_pending ADD COLUMN needs_review INTEGER DEFAULT 1')

    def record(
        self,
        entity_ref: str,
        field: str,
        value_a: str,
        value_b: str,
        source_a: str,
        source_b: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Ghi 1 conflict. Trả True nếu INSERT thành công (mới), False nếu IGNORE (đã có).

        Args:
            entity_ref: canonical ID (PL…, A…)
            field: trường dữ liệu xung đột (vd 'name_vi', 'coordinates')
            value_a: giá trị từ source_a
            value_b: giá trị từ source_b
            source_a: source_code nguồn A (vd 'DILA')
            source_b: source_code nguồn B (vd 'CBETA')
            notes: ghi chú tùy chọn
        """
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            self._ensure_cols(conn)
            cols = {r[1] for r in conn.execute('PRAGMA table_info(conflict_pending)')}

            now = datetime.now().isoformat(timespec='seconds')
            base = {
                'entity_ref': entity_ref,
                'field': field,
                'value_a': value_a,
                'value_b': value_b,
                'source_a': source_a,
                'source_b': source_b,
                'status': 'pending',
                'needs_review': 1,
                'created_at': now,
            }
            if notes and 'notes' in cols:
                base['notes'] = notes

            keys = [k for k in base if k in cols]
            placeholders = ', '.join('?' for _ in keys)
            col_list = ', '.join(keys)
            values = [base[k] for k in keys]

            # Check for duplicate before insert (conflict_pending may not have UNIQUE constraint)
            exists = conn.execute(
                'SELECT 1 FROM conflict_pending WHERE entity_ref=? AND field=? '
                'AND value_a=? AND value_b=? AND source_a=? AND source_b=? LIMIT 1',
                (entity_ref, field, value_a, value_b, source_a, source_b)
            ).fetchone()
            if exists:
                return False

            cur = conn.execute(
                f'INSERT INTO conflict_pending ({col_list}) VALUES ({placeholders})',
                values
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def record_many(self, conflicts: list) -> int:
        """Ghi nhiều conflicts cùng lúc. Mỗi item là dict với các trường của record().
        Trả số rows thực sự INSERT (không IGNORE)."""
        inserted = 0
        for c in conflicts:
            inserted += int(self.record(
                entity_ref=c['entity_ref'],
                field=c['field'],
                value_a=c['value_a'],
                value_b=c['value_b'],
                source_a=c['source_a'],
                source_b=c['source_b'],
                notes=c.get('notes'),
            ))
        return inserted
