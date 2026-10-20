import sqlite3,json
c=sqlite3.connect('file:data/lineage.db?mode=ro',uri=True);c.row_factory=sqlite3.Row
print(json.dumps([{'filename':r['filename'],'detail':json.loads(r['metadata_json'])} for r in c.execute("SELECT filename,metadata_json FROM ttl_v2_source_records WHERE kind='TTL' AND source_group='active' AND parse_status='needs_review'")],ensure_ascii=False))
