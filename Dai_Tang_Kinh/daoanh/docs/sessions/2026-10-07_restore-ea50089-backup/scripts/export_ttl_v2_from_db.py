# -*- coding: utf-8 -*-
import argparse,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
from src_python.ttl_db_batch import run
p=argparse.ArgumentParser(description='Xuất TTL v2 từ DB, không đọc lại XML/TTL local.');p.add_argument('--db',default=str(BASE/'data/lineage.db'));p.add_argument('--scope',choices=['ttl','dila'],default='ttl');p.add_argument('--output',required=True);p.add_argument('--limit',type=int);a=p.parse_args()
try:
 summary=run(a.db,a.output,a.scope,a.limit);print(json.dumps(summary,ensure_ascii=False));sys.exit(1 if summary['counts']['needs_review'] else 0)
except Exception as e:print('Không xuất được TTL: '+str(e),file=sys.stderr);sys.exit(2)
