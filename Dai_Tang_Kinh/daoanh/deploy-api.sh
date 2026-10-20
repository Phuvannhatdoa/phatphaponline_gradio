#!/bin/bash
# deploy-api.sh - Deploy và restart Flask trên VPS
# Chạy trên VPS: bash deploy-api.sh

echo "🔍 Checking Flask process..."
ps aux | grep "python.*app.py" | grep -v grep

echo -e "\n🛑 Killing old Flask..."
pkill -9 -f "python.*app.py" 2>/dev/null
sleep 2

echo -e "\n🧹 Clearing Python cache..."
find /opt/daoanh -name "*.pyc" -delete 2>/dev/null
rm -rf /opt/daoanh/__pycache__ 2>/dev/null
rm -rf /opt/daoanh/**/__pycache__ 2>/dev/null

echo -e "\n✅ Checking new endpoints in app.py..."
grep -n "namevi-map-places-pending" /opt/daoanh/app.py | head -3

echo -e "\n🚀 Starting Flask..."
cd /opt/daoanh
nohup python3 -B app.py > /tmp/daoanh.log 2>&1 &
sleep 3

echo -e "\n📊 Checking Flask log..."
tail -10 /tmp/daoanh.log

echo -e "\n🔍 Testing API..."
curl -s http://localhost:5000/daoanh/api/admin/namevi-map-places-pending | head -5

echo -e "\n✅ Done! Check output above."
echo "If you see JSON array [...], it works!"
echo "If you see 404, check /tmp/daoanh.log for errors"
