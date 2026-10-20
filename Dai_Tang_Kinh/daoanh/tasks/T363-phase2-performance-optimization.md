---
id: T363
title: "Phase 2 Planning: Performance Optimization (Weeks 3-5)"
status: pending
created: 2026-10-12
updated: 2026-10-12
parent: null
former_ids: []
depends_on: [T360, T361, T362]
done_when:
  - "Audit complete: identify all N+1 query patterns (est. ~20 loops)"
  - "Lexicon cache replacement: SQLite FTS + indexes designed"
  - "Database indexing strategy: documented for all common queries"
  - "Connection pooling: implementation plan written"
  - "Performance baseline: before/after metrics defined"
---

## Context

Phase 1 (T360/T361/T362) stabilizes code quality.
Phase 2 optimizes database & API performance.

Current bottlenecks:
- N+1 queries: ~20 loop patterns cause 10x slower queries at scale
- Lexicon cache: 500MB in-RAM per process → cannot scale to 4+ workers
- No connection pooling: new DB connection per request (expensive)
- Missing indexes: full table scans on name_vi, place names, etc.

---

## Scope

### 1. N+1 Query Audit & Fix
- Find all loop-based queries in app.py
- Batch load pattern for lineage, places, people lookups
- Test: Person with 100 teachers should be 1 query, not 101

### 2. Lexicon Cache Replacement
- Current: 166K terms loaded in-RAM at startup (10-30s startup, 500MB)
- New: SQLite FTS (Full-Text Search) with proper indexing
- Benefit: Instant startup, scales to multiple workers

### 3. Database Indexing Strategy
- Index on: name_zh, name_vi, source_id (for lookups)
- Index on: lineage_edge (teacher_id, student_id)
- Verify: query plans show index usage (EXPLAIN QUERY PLAN)

### 4. Connection Pooling
- Replace: new conn per request
- With: connection pool (5-10 persistent connections)
- Benefit: Reuse connections, faster queries

---

## Deliverables

- `docs/PERFORMANCE_OPTIMIZATION.md` — Strategy document
- `scripts/audit_n1_queries.py` — Find all N+1 patterns
- `daoanh/lib/db_pool.py` — Connection pool implementation
- Performance baseline metrics (before/after)

---

## Timeline: 3 weeks (Phase 2)

---

## Dependencies

- Blocks: Nothing (Phase 3 can start parallel)
- Depends on: Phase 1 completion
