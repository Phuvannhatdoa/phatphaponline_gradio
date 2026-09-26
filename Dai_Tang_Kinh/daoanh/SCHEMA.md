# Data Architecture Overview

## 3‑layer model

| Layer | Purpose | Tables (examples) |
|------|---------|-------------------|
| **RAW** | Source data – never modified by the application. | `people_full`, `places_dila`, `marcus_networks`, `dila_reference`, `marcus_reference`, `ttl_master`, `ttl_works` |
| **STAGING / MAPPING** | Temporary tables used for ETL, AI mapping, deduplication. Must be clearly named with the `_staging` suffix. | `people_staging`, `places_staging`, `namevi_map_places_staging` |
| **FINAL / PUBLIC** | Tables consumed by the UI and exported to downstream services. Only these are written to by UI actions. | `people`, `places`, `canon_catalog`, `places_vps`, `ttl_canon_works`, `ttl_mapping` |

### Why the current *_new tables break the model
- `people_new`, `places_new` duplicate the schema of the RAW tables (`people_full`, `places_dila`) **without** a clear role.
- `name_vi_map_places` and `namevi_map_places` store the same mapping information under different names.
- No documentation or naming convention indicates they are staging or legacy tables, so developers may read/write the wrong source, causing:
  - Data drift between RAW and final tables.
  - Potential license violations because data may lose its `source_id` linkage.

### Recommended cleanup actions
1. **Rename legitimate staging tables**
   ```sql
   ALTER TABLE people_new RENAME TO people_staging;
   ALTER TABLE places_new RENAME TO places_staging;
   ```
2. **Consolidate mapping tables**
   - Keep the richer `namevi_map_places` (contains FTS and extra columns).
   - Migrate any rows from `name_vi_map_places`:
   ```sql
   INSERT OR IGNORE INTO namevi_map_places (dila_id, name_vi, name_zh, source, confidence)
   SELECT dila_id, name_vi, name_zh, source, confidence FROM name_vi_map_places;
   DROP TABLE name_vi_map_places;
   ```
3. **Drop truly legacy tables** if no data is needed:
   ```sql
   DROP TABLE IF EXISTS people_new;   -- after migration
   DROP TABLE IF EXISTS places_new;   -- after migration
   ```
4. **Update all code paths** (Python, SQL queries, UI) to reference the new staging names (`*_staging`) and final tables only.
5. **Enforce source tracking**
   - Every import from DILA, Marcus or TTL must insert a row into `dataset_sources` with `origin_url`, `license`, `usage_level`.
   - All records in final tables must have a non‑null `source_id` referencing that row.
   - Add a foreign‑key constraint if not already present:
   ```sql
   ALTER TABLE people ADD CONSTRAINT fk_source FOREIGN KEY (source_id) REFERENCES dataset_sources(id);
   ```
6. **Documentation**
   - Add `SCHEMA.md` (this file) and `docs/data-pipeline.md` describing the flow: RAW → STAGING → FINAL.
   - Comment each import script (e.g., `import_etl.py`) with a short note: *"Do not modify RAW tables; only insert into *_staging"*.

---

**Next steps for Opencode**
- Review the migration scripts above.
- Run them in a test environment, verify data integrity.
- Deploy the schema changes and update the application code accordingly.
- Ensure CI pipelines run the new `npm run tester:agent` tests with the Flask service running as a background daemon (systemd/pm2).

By aligning the database to the 3‑layer architecture, we eliminate ambiguity, protect raw source data, and keep licensing information intact.
