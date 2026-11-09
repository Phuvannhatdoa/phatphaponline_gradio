#!/bin/bash
set -e
EXPECT="$1"
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data
V=$(sha256sum lineage.db.incoming | cut -c1-64)
if [ "$V" != "$EXPECT" ]; then echo HASH_MISMATCH; exit 3; fi
systemctl stop daoanh-api.service
mv lineage.db.incoming lineage.db
rm -f lineage.db-wal lineage.db-shm
systemctl start daoanh-api.service
echo SWAP_OK
