#!/bin/bash
# fix-404.sh - Fix 404 on VPS
# Run: bash fix-404.sh

echo "🔍 Checking Flask..."
ps aux | grep "python.*app" | grep -v grep

echo -e "\n🛑 Killing Flask..."
killall -9 python3 2>/dev/null
killall -9 python 2>/dev/null
sleep 2

echo -e "\n🧹 Clearing cache..."
find /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh -name "*.pyc" -delete 2>/dev/null
rm -rf /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/__pycache__ 2>/dev/null

echo -e "\n✅ Checking new endpoints..."
grep -n "namevi-map-places-pending" /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/app.py | head -2

echo -e "\n🚀 Starting Flask..."
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
nohup python3 -B app.py > /tmp/daoanh.log 2>&1 &
sleep 3

echo -e "\n📊 Checking Flask log..."
tail -5 /tmp/daoanh.log

echo -e "\n🔍 Testing API..."
curl -s http://localhost:5000/daoanh/api/admin/namevi-map-places-pending | head -3

echo -e "\n✅ Done! If you see JSON above, it works!"
echo "If 404, check /tmp/daoanh.log for Python errors"
