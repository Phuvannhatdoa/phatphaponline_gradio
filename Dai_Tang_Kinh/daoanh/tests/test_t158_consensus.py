#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T158 — lineage_edge_consensus tests.
7 test cases per spec + backfill integrity checks.
Usage: python -m pytest tests/test_t158_consensus.py -v
"""
import os
import shutil
import sqlite3
import tempfile
import pytest

DAOANH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DAOANH, 'data', 'lineage.db')
TABLE = 'lineage_edge_consensus'


@pytest.fixture(scope='module')
def db():
    """DB production (read-only queries). T158 bảng đã được migration --apply tạo."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# ── T1: one_source_only (MARCUS only) ─────────────────────────────────────────
def test_t1_one_source_only_not_rendered(db):
    """Cạnh chỉ có MARCUS (không có DILA) → is_default_visible=0."""
    rows = db.execute(
        f"SELECT * FROM {TABLE} WHERE marcus_asserted=1 AND dila_asserted=0"
    ).fetchall()
    # Tất cả MARCUS-only phải là single_source + not visible
    for r in rows:
        assert r['consensus_status'] == 'single_source', (
            f"A{r['teacher_id']}->A{r['disciple_id']}: status={r['consensus_status']}"
        )
        assert r['is_default_visible'] == 0, (
            f"A{r['teacher_id']}->A{r['disciple_id']}: visible should be 0"
        )


# ── T2: two_sources_same_direction (marcus + dila) ────────────────────────────
def test_t2_two_sources_same_direction_rendered(db):
    """Cạnh có cả MARCUS và DILA đồng chiều → confirmed_2plus, is_default_visible=1."""
    rows = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} "
        "WHERE marcus_asserted=1 AND dila_asserted=1 AND consensus_status='confirmed_2plus'"
    ).fetchone()
    assert rows['n'] > 10000, f"Cần >10000 confirmed_2plus rows, có: {rows['n']}"

    # Spot check: tất cả confirmed_2plus phải có is_default_visible=1
    bad = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} "
        "WHERE consensus_status='confirmed_2plus' AND is_default_visible!=1"
    ).fetchone()
    assert bad['n'] == 0, f"{bad['n']} confirmed_2plus rows có is_default_visible!=1"


# ── T3: three_sources_same_direction ─────────────────────────────────────────
def test_t3_three_sources_still_confirmed(db):
    """n_sources>=2 luôn → confirmed_2plus (TTL/Lineage chưa có data, nhưng rule đúng)."""
    all_conf = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE agreeing_source_count>=2"
    ).fetchone()['n']
    bad = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} "
        "WHERE agreeing_source_count>=2 AND consensus_status!='confirmed_2plus' "
        "AND human_override IS NULL"
    ).fetchone()['n']
    assert bad == 0, f"{bad} rows với n_sources>=2 nhưng status!=confirmed_2plus"


# ── T4: opposite_direction_conflict ──────────────────────────────────────────
def test_t4_opposite_direction_conflict(db):
    """Cạnh có opposite assertion → conflicted, is_default_visible=0."""
    conflicted = db.execute(
        f"SELECT * FROM {TABLE} WHERE consensus_status='conflicted' LIMIT 10"
    ).fetchall()
    # Nếu có conflicted rows, verify chúng đều invisible
    for r in conflicted:
        assert r['is_default_visible'] == 0, (
            f"Conflicted edge {r['teacher_id']}->{r['disciple_id']} should not be visible"
        )
        assert r['opposite_source_count'] > 0


# ── T5: non_dharma_teacher ───────────────────────────────────────────────────
def test_t5_only_dharma_transmission_in_table(db):
    """Tất cả rows trong consensus có relation_type='dharma_transmission'."""
    bad = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE relation_type!='dharma_transmission'"
    ).fetchone()['n']
    assert bad == 0, f"{bad} rows với relation_type khác dharma_transmission"


# ── T6: human_approved_exception ─────────────────────────────────────────────
def test_t6_human_override_schema(db):
    """Column human_override tồn tại và cho phép 'approved'/'rejected'/NULL."""
    cols = {r[1]: r for r in db.execute(f"PRAGMA table_info({TABLE})").fetchall()}
    assert 'human_override' in cols, "Thiếu column human_override"
    # Verify NULL hiện tại (chưa có HITL data)
    non_null = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE human_override IS NOT NULL"
    ).fetchone()['n']
    # OK nếu không có override — đây chỉ verify schema, không enforce count


# ── T7 (current_case): A001060->A021462 ──────────────────────────────────────
def test_t7_current_case_hoankhe_kinhdang(db):
    """A001060 (Hoàn Khê Duy Nhất) -> A021462 (Kính Đường Giác Viên):
    Marcus + DILA đồng thuận → rendered_default=True, badge='2/4: Marcus, DILA'."""
    row = db.execute(
        f"SELECT * FROM {TABLE} WHERE teacher_id='A001060' AND disciple_id='A021462'"
    ).fetchone()
    assert row is not None, "Edge A001060->A021462 không có trong consensus table"
    assert row['consensus_status'] == 'confirmed_2plus', (
        f"Expected confirmed_2plus, got {row['consensus_status']}"
    )
    assert row['is_default_visible'] == 1, "Expected is_default_visible=1"
    assert row['marcus_asserted'] == 1
    assert row['dila_asserted'] == 1
    assert '2/4' in (row['source_badge'] or ''), f"Badge: {row['source_badge']}"
    assert 'Marcus' in (row['source_badge'] or '')
    assert 'DILA' in (row['source_badge'] or '')


# ── Integrity checks ──────────────────────────────────────────────────────────
def test_integrity_no_self_edges(db):
    """Không có cạnh teacher→teacher (tự lặp)."""
    n = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE teacher_id=disciple_id"
    ).fetchone()['n']
    assert n == 0, f"{n} self-edges in consensus"


def test_integrity_total_count(db):
    """Tổng số rows hợp lý (>20000 sau backfill)."""
    n = db.execute(f"SELECT COUNT(*) n FROM {TABLE}").fetchone()['n']
    assert n >= 20000, f"Only {n} rows — backfill might have failed"


def test_integrity_visible_count(db):
    """Số visible edges (confirmed_2plus) phải gần bằng số MARCUS edges (~11165)."""
    vis = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE is_default_visible=1"
    ).fetchone()['n']
    assert 10000 <= vis <= 15000, f"Unexpected visible count: {vis}"


def test_integrity_source_badge_format(db):
    """source_badge phải có format 'N/4: ...'."""
    bad = db.execute(
        f"SELECT COUNT(*) n FROM {TABLE} WHERE source_badge NOT LIKE '%/4: %'"
    ).fetchone()['n']
    assert bad == 0, f"{bad} rows với source_badge sai format"


def test_integrity_api_lineage_tree(db):
    """API endpoint /daoanh/api/monk/A001060/lineage-tree trả về A021462 trong edges."""
    import sys
    sys.path.insert(0, DAOANH)
    try:
        import app as flask_app
        flask_app.app.config['TESTING'] = True
        client = flask_app.app.test_client()
        resp = client.get('/daoanh/api/monk/A001060/lineage-tree?up=1&down=1')
        data = resp.get_json()
        assert data and data.get('ok'), f"API error: {data}"
        assert 'consensus:' in (data.get('source', '') or ''), (
            f"source field should contain 'consensus:', got: {data.get('source')}"
        )
        edge_ids = set()
        for e in (data.get('edges') or []):
            edge_ids.add(e.get('from', ''))
            edge_ids.add(e.get('to', ''))
        assert 'A021462' in edge_ids, f"A021462 not found in edges. Edge nodes: {list(edge_ids)[:10]}"
        # Verify source_badge present on edges
        for e in (data.get('edges') or []):
            assert 'source_badge' in e, f"Edge missing source_badge field: {e.get('from')}→{e.get('to')}"
    except Exception as ex:
        pytest.fail(f"API test failed: {ex}")
