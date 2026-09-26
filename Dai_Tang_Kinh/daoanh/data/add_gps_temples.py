#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add GPS to temples_master.json based on manual database
"""

import json

INPUT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/temples_master.json"
OUTPUT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/temples_master_gps.json"

# Famous Vietnamese temples with GPS
MANUAL_GPS = {
    # TP. Hồ Chí Minh
    "vĩnh nghiêm": {"lat": 10.7877, "lon": 106.6889, "province": "VN-50"},
    "ngọc hoàng": {"lat": 10.7877, "lon": 106.6889, "province": "VN-50"},
    "giác lâm": {"lat": 10.8167, "lon": 106.6833, "province": "VN-50"},
    "ấn quang": {"lat": 10.7965, "lon": 106.6854, "province": "VN-50"},
    "xá lợi": {"lat": 10.7897, "lon": 106.6941, "province": "VN-50"},
    "huệ nghiêm": {"lat": 10.7618, "lon": 106.6889, "province": "VN-50"},
    "phước định": {"lat": 10.7877, "lon": 106.6889, "province": "VN-50"},
    "bửu quang": {"lat": 10.9431, "lon": 106.8231, "province": "VN-44"},
    "chúc thánh": {"lat": 10.9452, "lon": 106.8123, "province": "VN-44"},
    "quảng nghiêm": {"lat": 10.9452, "lon": 106.8123, "province": "VN-44"},
    
    # Thừa Thiên Huế
    "thiên mụ": {"lat": 16.0544, "lon": 107.5906, "province": "VN-26"},
    "từ đàm": {"lat": 16.0544, "lon": 107.5906, "province": "VN-26"},
    "từ quảng": {"lat": 16.0544, "lon": 107.5906, "province": "VN-26"},
    "linh mụ": {"lat": 16.0544, "lon": 107.5906, "province": "VN-26"},
    "kim long": {"lat": 16.0544, "lon": 107.5906, "province": "VN-26"},
    "bảo quang": {"lat": 16.0544, "lon": 107.5906, "province": "VN-26"},
    "nam giao": {"lat": 16.0544, "lon": 107.5906, "province": "VN-26"},
    
    # Hà Nội
    "trấn quốc": {"lat": 21.0353, "lon": 105.8021, "province": "VN-01"},
    "một cột": {"lat": 21.0285, "lon": 105.8342, "province": "VN-01"},
    "quán sứ": {"lat": 21.0285, "lon": 105.8342, "province": "VN-01"},
    "hương": {"lat": 20.9571, "lon": 105.5203, "province": "VN-01"},
    "tây phương": {"lat": 20.9691, "lon": 105.4876, "province": "VN-01"},
    "vĩnh nghiêm": {"lat": 21.0389, "lon": 105.7937, "province": "VN-01"},
    
    # Ninh Bình
    "bái đính": {"lat": 20.3789, "lon": 105.9184, "province": "VN-22"},
    "hoa lư": {"lat": 20.3789, "lon": 105.9184, "province": "VN-22"},
    
    # Khánh Hòa (Nha Trang)
    "long sơn": {"lat": 12.2433, "lon": 109.1934, "province": "VN-34"},
    "tháp bà": {"lat": 12.2433, "lon": 109.1934, "province": "VN-34"},
    
    # Đà Nẵng
    "linh ứng": {"lat": 16.0544, "lon": 108.2024, "province": "VN-48"},
    
    # Lâm Đồng (Đà Lạt)
    "linh phong": {"lat": 11.9322, "lon": 108.4579, "province": "VN-41"},
    "thiên vườn": {"lat": 11.9322, "lon": 108.4579, "province": "VN-41"},
    
    # An Giang
    "tây an": {"lat": 10.5212, "lon": 105.0848, "province": "VN-36"},
    "xiêm": {"lat": 10.5212, "lon": 105.0848, "province": "VN-36"},
    "vĩnh tràng": {"lat": 10.3736, "lon": 105.4412, "province": "VN-36"},
    
    # Kiên Giang
    "phật lớn": {"lat": 10.0124, "lon": 105.0806, "province": "VN-67"},
    
    # Cần Thơ
    "ông": {"lat": 10.0287, "lon": 105.7835, "province": "VN-65"},
    "việt nam quốc tự": {"lat": 10.0287, "lon": 105.7835, "province": "VN-65"},
    
    # Tây Ninh
    "cao đài": {"lat": 11.3611, "lon": 106.1419, "province": "VN-37"},
    "bà đen": {"lat": 11.3611, "lon": 106.1419, "province": "VN-37"},
}

def main():
    print("🚀 Adding GPS to temples_master.json")
    
    # Load
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    temples = data.get("temples", [])
    matched = 0
    
    for temple in temples:
        nameVi = temple.get("nameVi", "").lower()
        nameAlt = temple.get("nameAlt", "").lower()
        
        # Try to match
        for gps_key, gps_data in MANUAL_GPS.items():
            if gps_key in nameVi or gps_key in nameAlt:
                temple["lat"] = gps_data["lat"]
                temple["lon"] = gps_data["lon"]
                temple["province"] = gps_data["province"]
                temple["status"] = "geocoded"
                matched += 1
                print(f"  ✓ {temple.get('nameVi', '')} -> ({gps_data['lat']}, {gps_data['lon']})")
                break
    
    print(f"\n✅ Matched: {matched}/{len(temples)} temples")
    
    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Saved: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()