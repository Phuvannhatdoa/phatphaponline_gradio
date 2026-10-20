-- Rollback T368 schema migration
-- Chi drop 4 bang duoc tao boi T368. KHONG dong tam dung bang places/vn_person_authority (nam ngoai scope).
DROP TABLE IF EXISTS passage_entity_mention;
DROP TABLE IF EXISTS person_activity;
DROP TABLE IF EXISTS entity_merge_log;
DROP TABLE IF EXISTS dharma_lineage_unified;
