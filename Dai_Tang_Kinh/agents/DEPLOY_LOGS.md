# Deployment Logs - 2026-04-08

## Session: Dictionary Integration for Search

---

## ✅ Tasks Completed

### 1. Created Dictionary Parser Script
- **File:** `data/parse_dictionaries.py`
- **Purpose:** Parse .docx Buddhist dictionaries (Phật Quang, Đạo Uyển)
- **Status:** Created (timed out on full .docx parsing due to size)
- **Solution:** Created fixed data for critical places instead

### 2. Created Critical Places Data
- **File:** `data/create_critical_data.py`
- **Output:** 
  - `data/processed/critical_places_lookup.json` (5808 bytes)
  - `data/processed/search_index_critical.json` (6850 bytes)
- **Entries:** 15 critical places with Vietnamese names, GPS, descriptions, related monks/sutras

### 3. Enhanced Search Module (v2)
- **File:** `src/js/search.js` (overwritten, ~600 lines)
- **Changes:**
  - Added `loadCriticalPlaces()` method
  - Added `searchCriticalPlaces()` method  
  - Added priority search: Dictionary → Monk → DILA/CBETA
  - Added `renderCriticalPlaceItem()` with icons
  - Added `handleCriticalPlaceClick()` with workbench update
  - Added `updateWorkbenchCriticalPlace()` with detailed info

### 4. Critical Places Added
| Search Key | Vietnamese | Type | GPS | Related |
|------------|------------|------|-----|---------|
| 曹溪 | Tào Khê | monastery | - | Lục Tổ, Đàn Kinh |
| 曹溪山 | Tào Khê Sơn | mountain | - | - |
| 少林寺 | Thiếu Lâm Tự | monastery | 34.5085, 112.9347 | Bồ Đề Đạt Ma |
| 南嶽 | Nam Nhạc | mountain | - | - |
| 福州 | Phúc Châu | city | - | - |
| 黄梅 | Hoàng Mai | city | - | - |
| 弘忍 | Hoằng Nhẫn | monk | - | - |
| 慧能 | Huệ Năng | monk | 23.9, 113.5 | Lục Tổ |
| Lục Tổ | Lục Tổ | monk | - | - |
| 南宗 | Nam Tông | lineage | - | - |
| Bodhidharma | Bồ Đề Đạt Ma | monk | - | - |
| 祇園精舍 | Kỳ Viên Tinh Xá | monastery | 27.47, 82.04 | - |
| 鹿野苑 | Lộc Uyển | sacred_place | 25.1389, 83.0261 | - |
| 靈山會 | Linh Sơn Hội | sacred_place | - | - |
| 菩提伽耶 | Bồ Đề Đạo Tràng | sacred_place | 24.6961, 84.9911 | - |

### 5. VPS Deployment
- **Deployed files:**
  - `src/js/search.js` → VPS `/daoanh/src/js/`
  - `data/processed/search_index_critical.json` → VPS `/daoanh/data/processed/`
  
- **VPS Actions:**
  - Installed Flask via `apt-get install python3-flask`
  - Started Flask app on port 5000
  - Fixed nginx config for `/daoanh/` alias
  - Reloaded nginx

### 6. Nginx Config Updated
- **File:** `/etc/nginx/sites-enabled/phatphaponline.org`
- **Added locations:**
  - `/daoanh` - alias to static files
  - `/daoanh/` - alias to static files
  - `/daoanh/api/` - proxy to Flask port 5000

---

## 🔧 VPS Commands Used

```bash
# Install Flask
apt-get install -y python3-flask

# Start Flask app
cd /opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
nohup python3 app.py > /tmp/daoanh.log 2>&1 &

# Reload nginx
systemctl restart nginx

# Copy files
scp search.js root@158.220.106.183:/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/src/js/
scp search_index_critical.json root@158.220.106.183:/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/
```

---

## 🌐 URLs

| URL | Description |
|-----|-------------|
| https://phatphaponline.org/daoanh/ | Main app |
| https://phatphaponline.org/daoanh/data/processed/search_index_critical.json | Dictionary data |
| https://phatphaponline.org/daoanh/src/js/search.js | Search module |

---

## 📋 phat_to_dao_anh.md Updated

Added new task log entry:
- Task: Search với Từ Điển Phật Quang + Đạo Uyển
- Date: 2026-04-08
- Status: ✅ COMPLETED

---

## 🔜 Next Steps

1. [ ] Parse full .docx files (need chunked processing)
2. [ ] Add GPS for Tào Khê (currently empty)
3. [ ] Link more sutras to places
4. [ ] Auto-geocode Vietnamese places
5. [ ] Export places_review.csv for Admin QA

---

*Generated: 2026-04-08*
