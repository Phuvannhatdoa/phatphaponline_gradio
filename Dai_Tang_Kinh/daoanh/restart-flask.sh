#!/bin/bash
# restart-flask.sh - Simple Flask restart for VPS
# Run on VPS: bash restart-flask.sh

echo "🔍 Checking for Flask process..."
ps aux | grep "python.*app" | grep -v grep

echo -e "\n🛑 Killing all Python processes..."
killall -9 python3 2>/dev/null
killall -9 python 2>/dev/null
sleep 2

echo -e "\n🧹 Clearing cache..."
find /opt/daoanh -name "*.pyc" -delete 2>/dev/null
rm -rf /opt/daoanh/__pycache__ 2>/dev/null
rm -rf /opt/daoanh/**/__pycache__ 2>/dev/null

echo -e "\n✅ Verifying new endpoints..."
grep -n "namevi-map-places-pending" /opt/daoanh/app.py | head -2

echo -e "\n🚀 Starting Flask..."
cd /opt/daoanh
nohup python3 -B app.py > /tmp/daoanh.log 2>&1 &
sleep 3

echo -e "\n📊 Checking Flask log..."
tail -5 /tmp/daoanh.log

echo -e "\n🔍 Testing API..."
curl -s http://localhost:5000/daoanh/api/admin/namevi-map-places-pending | head -5

echo -e "\n✅ Done! If you see JSON above, it works!"
echo "If you see 404, check /tmp/daoanh.log for Python errors"
