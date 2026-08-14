#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gps_enrichment_nominatim.py - GPS Enrichment bằng OpenStreetMap Nominatim API

Mô tả: Lấy tọa độ GPS cho các địa danh từ temples_master_v2.json
       Sử dụng Nominatim API (miễn phí, không cần API key)
       Tối ưu: Resume support, batch processing, intermediate save

Author: Agent Build (2026-04-09)
Input:  data/processed/temples_master_v2.json
Output: data/processed/temples_master_v2_gps.json
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error
import os

INPUT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/temples_master_v2.json"
OUTPUT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/temples_master_v2_gps.json"
CHECKPOINT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/gps_checkpoint.json"

# Nominatim API endpoint
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Delay between requests (Nominatim yêu cầu ≥1 giây)
REQUEST_DELAY = 1.1

# Province name mapping (ISO 3166-2 → Vietnamese)
PROVINCE_NAMES = {
    "VN-01": "Hà Nội",
    "VN-02": "Hà Giang", 
    "VN-04": "Cao Bằng",
    "VN-06": "Bắc Kạn",
    "VN-08": "Tuyên Quang",
    "VN-10": "Lào Cai",
    "VN-11": "Yên Bái",
    "VN-12": "Thái Nguyên",
    "VN-14": "Quảng Ninh",
    "VN-15": "Bắc Giang",
    "VN-16": "Phú Thọ",
    "VN-17": "Vĩnh Phúc",
    "VN-18": "Bắc Ninh",
    "VN-19": "Hưng Yên",
    "VN-20": "Hà Nam",
    "VN-21": "Nam Định",
    "VN-22": "Ninh Bình",
    "VN-24": "Thanh Hóa",
    "VN-25": "Nghệ An",
    "VN-26": "Hà Tĩnh",
    "VN-27": "Quảng Bình",
    "VN-28": "Quảng Trị",
    "VN-29": "Thừa Thiên Huế",
    "VN-30": "Quảng Nam",
    "VN-31": "Quảng Ngãi",
    "VN-32": "Bình Định",
    "VN-33": "Phú Yên",
    "VN-34": "Khánh Hòa",
    "VN-35": "Ninh Thuận",
    "VN-36": "Bình Thuận",
    "VN-37": "Kon Tum",
    "VN-38": "Gia Lai",
    "VN-39": "Đắk Lắk",
    "VN-40": "Đắk Nông",
    "VN-41": "Lâm Đồng",
    "VN-42": "Bình Phước",
    "VN-43": "Tây Ninh",
    "VN-44": "Bình Dương",
    "VN-45": "Đồng Nai",
    "VN-46": "Bà Rịa - Vũng Tàu",
    "VN-47": "Long An",
    "VN-48": "Tiền Giang",
    "VN-49": "Bến Tre",
    "VN-50": "TP. Hồ Chí Minh",
    "VN-51": "Trà Vinh",
    "VN-52": "Vĩnh Long",
    "VN-53": "Đồng Tháp",
    "VN-54": "An Giang",
    "VN-55": "Kiên Giang",
    "VN-56": "Hậu Giang",
    "VN-57": "Sóc Trăng",
    "VN-58": "Bạc Liêu",
    "VN-59": "Cà Mau",
    "VN-SG": "TP. Hồ Chí Minh",
    "VN-CT": "Cần Thơ",
    "VN-DN": "Đà Nẵng",
    "VN-HN": "Hà Nội"
}

def get_province_name(code):
    """Lấy tên tỉnh từ mã ISO"""
    return PROVINCE_NAMES.get(code, "")

def clean_name(name):
    """Làm sạch tên địa danh để tìm kiếm tốt hơn"""
    if not name:
        return ""
    # Remove excessive description
    name = name.split('(')[0].strip()
    # Take first 50 chars to avoid overly long queries
    if len(name) > 50:
        name = name[:50]
    return name

def get_gps_from_nominatim(temple_name: str, province: str = "") -> dict:
    """
    Lấy GPS từ Nominatim API
    
    Returns: {"lat": "12.34", "lon": "109.56", "address": "..."} hoặc None
    """
    try:
        # Build query - clean name + province
        query = clean_name(temple_name)
        if not query:
            return None
            
        # Add province if available
        province_name = get_province_name(province)
        if province_name and province != "VN-UN":
            query += f", {province_name}"
        
        query += ", Vietnam"
        
        params = urllib.parse.urlencode({
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        })
        
        url = f"{NOMINATIM_URL}?{params}"
        
        # Request với User-Agent
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'PhatToDaoAnh/1.0 (Educational Project)')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if data and len(data) > 0:
            result = data[0]
            return {
                "lat": result.get("lat", ""),
                "lon": result.get("lon", ""),
                "address": result.get("display_name", "")
            }
        
        return None
        
    except Exception as e:
        print(f"  ⚠️ Lỗi GPS cho '{temple_name[:30]}...': {e}")
        return None

def save_checkpoint(data, processed_count):
    """Lưu checkpoint để có thể resume"""
    checkpoint = {
        "processed": processed_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, ensure_ascii=False)

def load_checkpoint():
    """Load checkpoint nếu có"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def main():
    print("=" * 60)
    print("🚀 GPS ENRICHMENT (Nominatim API) - v2.2 Optimized")
    print("=" * 60)
    
    # Load data
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    temples = data.get("temples", [])
    total = len(temples)
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    start_idx = checkpoint.get("processed", 0) if checkpoint else 0
    
    print(f"📊 Tổng số địa danh: {total}")
    print(f"🔄 Resume từ vị trí: {start_idx}")
    print(f"⏱️ Ước tính thời gian còn lại: {(total - start_idx) * REQUEST_DELAY / 60:.1f} phút")
    print()
    
    # Process temples - process all from start_idx
    LIMIT = total  # Process all
    
    processed = 0
    found_gps = 0
    
    for idx in range(start_idx, min(start_idx + LIMIT, total)):
        temple = temples[idx]
        name = temple.get("nameVi", "")
        province = temple.get("province", "")
        
        print(f"[{idx+1}/{total}] {name[:40]}...", end=" ", flush=True)
        
        # Get GPS
        gps = get_gps_from_nominatim(name, province)
        
        if gps:
            temple["lat"] = gps["lat"]
            temple["lon"] = gps["lon"]
            temple["address"] = gps["address"]
            temple["status"] = "geocoded"
            found_gps += 1
            print(f"✓ ({gps['lat']}, {gps['lon']})")
        else:
            print("✗ (không tìm thấy)")
        
        processed += 1
        
        # Save checkpoint every 10 temples
        if (idx + 1) % 10 == 0:
            save_checkpoint(data, idx + 1)
            print(f"  💾 Checkpoint saved at {idx+1}")
        
        # Delay để tránh rate limit
        if idx < min(start_idx + LIMIT, total) - 1:
            time.sleep(REQUEST_DELAY)
    
    print()
    print("=" * 60)
    print("✅ HOÀN THÀNH!")
    print(f"   Đã xử lý: {processed}")
    print(f"   Tìm thấy GPS: {found_gps}")
    print(f"   Tỷ lệ thành công: {found_gps/processed*100:.1f}%")
    print("=" * 60)
    
    # Save final output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Đã lưu: {OUTPUT_FILE}")
    
    # Remove checkpoint after completion
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print("🗑️ Checkpoint removed")

if __name__ == "__main__":
    main()