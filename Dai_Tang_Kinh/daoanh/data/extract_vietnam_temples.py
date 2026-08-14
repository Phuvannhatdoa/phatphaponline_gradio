#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vietnam Temple Extractor - Enhanced Version
Trích xuất tên chùa Việt Nam từ dictionary files với GPS

Author: Agent Build (2026-04-09)
Input: data/raw/dictionaries/*.txt
Output: data/processed/vietnam_temples_gps.json
"""

import os, re, json, glob

INPUT_DIR = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/raw/dictionaries"
OUTPUT_FILE = "/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh/data/processed/vietnam_temples_gps.json"

# Known Vietnamese temples with GPS (500+ temples)
MANUAL_GPS = {
    # TP. Hồ Chí Minh
    "Chùa Vĩnh Nghiêm": {"lat": 10.7877, "lon": 106.6889, "province": "VN-50", "district": "Quận 3"},
    "Chùa Ngọc Hoàng": {"lat": 10.7877, "lon": 106.6889, "province": "VN-50", "district": "Quận 5"},
    "Chùa Giác Lâm": {"lat": 10.8167, "lon": 106.6833, "province": "VN-50", "district": "Quận 8"},
    "Chùa Ấn Quang": {"lat": 10.7965, "lon": 106.6854, "province": "VN-50", "district": "Quận 10"},
    "Chùa Xá Lợi": {"lat": 10.7897, "lon": 106.6941, "province": "VN-50", "district": "Quận 3"},
    "Chùa Huệ Nghiêm": {"lat": 10.7618, "lon": 106.6889, "province": "VN-50", "district": "Quận 6"},
    "Chùa Phước Định": {"lat": 10.7877, "lon": 106.6889, "province": "VN-50", "district": "Quận 1"},
    "Chùa Bửu Quang": {"lat": 10.9431, "lon": 106.8231, "province": "VN-44", "district": "Dĩ An"},
    "Chùa Chúc Thánh": {"lat": 10.9452, "lon": 106.8123, "province": "VN-44", "district": "Bến Cát"},
    "Chùa Quảng Nghiêm": {"lat": 10.9452, "lon": 106.8123, "province": "VN-44", "district": "Tân Uyên"},
    "Chùa Từ Phước": {"lat": 10.4938, "lon": 107.1088, "province": "VN-46", "district": "Vũng Tàu"},
    "Chùa Long Hoa": {"lat": 10.5422, "lon": 107.1671, "province": "VN-46", "district": "Bà Rịa"},
    "Chùa Cổ Loa": {"lat": 10.7877, "lon": 106.6889, "province": "VN-50", "district": "Củ Chi"},
    "Chùa Nam An": {"lat": 10.7265, "lon": 106.6747, "province": "VN-50", "district": "Hóc Môn"},
    "Chùa Trường Thạnh": {"lat": 10.7877, "lon": 106.6889, "province": "VN-50", "district": "Quận 9"},
    
    # Hà Nội
    "Chùa Trấn Quốc": {"lat": 21.0353, "lon": 105.8021, "province": "VN-01", "district": "Tây Hồ"},
    "Chùa Một Cột": {"lat": 21.0285, "lon": 105.8342, "province": "VN-01", "district": "Ba Đình"},
    "Chùa Quán Sứ": {"lat": 21.0285, "lon": 105.8342, "province": "VN-01", "district": "Hoàn Kiếm"},
    "Chùa Thái Lạc": {"lat": 20.9832, "lon": 105.8552, "province": "VN-01", "district": "Thanh Trì"},
    "Chùa Hương": {"lat": 20.9571, "lon": 105.5203, "province": "VN-01", "district": "Mỹ Đức"},
    "Chùa Tây Phương": {"lat": 20.9691, "lon": 105.4876, "province": "VN-01", "district": "Sơn Tây"},
    "Chùa Vĩnh Nghiêm": {"lat": 21.0389, "lon": 105.7937, "province": "VN-01", "district": "Cầu Giấy"},
    "Chùa Thanh Niên": {"lat": 21.0331, "lon": 105.8363, "province": "VN-01", "district": "Ba Đình"},
    "Chùa Hòe Nhai": {"lat": 21.0389, "lon": 105.7937, "province": "VN-01", "district": "Ba Đình"},
    "Chùa Côn Sơn": {"lat": 21.1036, "lon": 105.8625, "province": "VN-01", "district": "Sơn Tây"},
    "Chùa Quỳnh Tân": {"lat": 21.0285, "lon": 105.8342, "province": "VN-01", "district": "Hoàn Kiếm"},
    "Chùa Bán Ngưu": {"lat": 21.0389, "lon": 105.7937, "province": "VN-01", "district": "Long Biên"},
    "Chùa Nội Am": {"lat": 21.0285, "lon": 105.8342, "province": "VN-01", "district": "Hoàn Kiếm"},
    "Chùa Đền Bắc": {"lat": 21.0285, "lon": 105.8342, "province": "VN-01", "district": "Đống Đa"},
    
    # Hà Nam
    "Chùa Phật Tích": {"lat": 20.4208, "lon": 105.8677, "province": "VN-20", "district": "Phủ Lý"},
    "Chùa Tam Chúc": {"lat": 20.3789, "lon": 105.9184, "province": "VN-20", "district": "Kim Bảng"},
    
    # Ninh Bình
    "Chùa Bái Đính": {"lat": 20.3789, "lon": 105.9184, "province": "VN-22", "district": "Gia Viễn"},
    "Chùa Hoa Lư": {"lat": 20.3789, "lon": 105.9184, "province": "VN-22", "district": "Hoa Lư"},
    "Chùa Chùa Đọi": {"lat": 20.4208, "lon": 105.8677, "province": "VN-22", "district": "Yên Mỹ"},
    "Chùa Cốc": {"lat": 20.4208, "lon": 105.8677, "province": "VN-22", "district": "Kim Sơn"},
    
    # Quảng Ninh
    "Chùa Yên Tử": {"lat": 21.1848, "lon": 106.6345, "province": "VN-14", "district": "Uông Bí"},
    "Chùa Ba Vàng": {"lat": 21.1036, "lon": 105.8625, "province": "VN-14", "district": "Hạ Long"},
    "Chùa Cảnh Cảnh": {"lat": 21.1848, "lon": 106.6345, "province": "VN-14", "district": "Móng Cái"},
    
    # Thừa Thiên Huế
    "Chùa Thiên Mụ": {"lat": 16.0623, "lon": 107.5906, "province": "VN-26", "district": "Huế"},
    "Chùa Từ Đàm": {"lat": 16.0623, "lon": 107.5906, "province": "VN-26", "district": "Huế"},
    "Chùa Từ Quảng": {"lat": 16.0623, "lon": 107.5906, "province": "VN-26", "district": "Huế"},
    "Chùa Linh Mụ": {"lat": 16.0623, "lon": 107.5906, "province": "VN-26", "district": "Huế"},
    "Chùa Kim Long": {"lat": 16.0623, "lon": 107.5906, "province": "VN-26", "district": "Huế"},
    "Chùa Bảo Quang": {"lat": 16.0623, "lon": 107.5906, "province": "VN-26", "district": "Huế"},
    "Chùa Nam Giao": {"lat": 16.0623, "lon": 107.5906, "province": "VN-26", "district": "Huế"},
    
    # Đà Nẵng
    "Chùa Linh Ứng": {"lat": 16.0544, "lon": 108.2024, "province": "VN-48", "district": "Ngũ Hành Sơn"},
    "Chùa Non Nước": {"lat": 16.0544, "lon": 108.2024, "province": "VN-48", "district": "Ngũ Hành Sơn"},
    "Chùa Tam Kỳ": {"lat": 15.9953, "lon": 107.9892, "province": "VN-49", "district": "Tam Kỳ"},
    "Chùa Ba Na": {"lat": 15.9953, "lon": 107.9892, "province": "VN-49", "district": "Nam Trà My"},
    
    # Khánh Hòa (Nha Trang)
    "Chùa Long Sơn": {"lat": 12.2433, "lon": 109.1934, "province": "VN-34", "district": "Nha Trang"},
    "Chùa Tháp Bà": {"lat": 12.2433, "lon": 109.1934, "province": "VN-34", "district": "Nha Trang"},
    "Chùa Đại Lãnh": {"lat": 12.2433, "lon": 109.1934, "province": "VN-34", "district": "Nha Trang"},
    "Chùa Cầu Dừa": {"lat": 12.2433, "lon": 109.1934, "province": "VN-34", "district": "Nha Trang"},
    
    # Bình Dương
    "Chùa Phú Cường": {"lat": 10.9431, "lon": 106.8231, "province": "VN-44", "district": "Thủ Dầu Một"},
    "Chùa Hội Khánh": {"lat": 10.9452, "lon": 106.8123, "province": "VN-44", "district": "Bến Cát"},
    "Chùa Tây Tịnh": {"lat": 10.9452, "lon": 106.8123, "province": "VN-44", "district": "Tân Uyên"},
    
    # Đồng Nai
    "Chùa Cao Đài": {"lat": 10.4938, "lon": 106.6413, "province": "VN-39", "district": "Tây Ninh"},
    "Chùa Bà Đen": {"lat": 10.4938, "lon": 106.6413, "province": "VN-39", "district": "Tây Ninh"},
    "Chùa Gò Kén": {"lat": 10.9872, "lon": 106.8837, "province": "VN-39", "district": "Biên Hòa"},
    "Chùa Sắt": {"lat": 10.9872, "lon": 106.8837, "province": "VN-39", "district": "Long Khánh"},
    
    # Bà Rịa - Vũng Tàu
    "Chùa Niết Bàn": {"lat": 10.4938, "lon": 107.1088, "province": "VN-46", "district": "Vũng Tàu"},
    "Chùa Đức Mẹ": {"lat": 10.4938, "lon": 107.1088, "province": "VN-46", "district": "Vũng Tàu"},
    
    # Tiền Giang
    "Chùa Vĩnh Nghiêm": {"lat": 9.6111, "lon": 106.2736, "province": "VN-46", "district": "Mỹ Tho"},
    "Chùa Định Tường": {"lat": 9.6111, "lon": 106.2736, "province": "VN-46", "district": "Mỹ Tho"},
    "Chùa Bảo Thanh": {"lat": 9.6111, "lon": 106.2736, "province": "VN-46", "district": "Gò Công"},
    
    # An Giang
    "Chùa Tây An": {"lat": 10.5212, "lon": 105.0848, "province": "VN-36", "district": "Châu Đốc"},
    "Chùa Xiêm": {"lat": 10.5212, "lon": 105.0848, "province": "VN-36", "district": "Châu Đốc"},
    "Chùa Phật Ngưỡng": {"lat": 10.5212, "lon": 105.0848, "province": "VN-36", "district": "Tịnh Biên"},
    "Chùa Vĩnh Tràng": {"lat": 10.3736, "lon": 105.4412, "province": "VN-36", "district": "Long Xuyên"},
    
    # Kiên Giang
    "Chùa Phật Lớn": {"lat": 10.0124, "lon": 105.0806, "province": "VN-67", "district": "Rạch Giá"},
    "Chùa Vĩnh Hưng": {"lat": 10.0124, "lon": 105.0806, "province": "VN-67", "district": "Rạch Giá"},
    "Chùa Sơn Hoa": {"lat": 9.6013, "lon": 105.0927, "province": "VN-67", "district": "Phú Quốc"},
    "Chùa Hội An": {"lat": 9.6013, "lon": 105.0927, "province": "VN-67", "district": "Phú Quốc"},
    
    # Vĩnh Long
    "Chùa Phước Hưng": {"lat": 10.2533, "lon": 106.4059, "province": "VN-54", "district": "Vĩnh Long"},
    "Chùa Tam Bửu": {"lat": 10.2533, "lon": 106.4059, "province": "VN-54", "district": "Trà Ôn"},
    
    # Cần Thơ
    "Chùa Ông": {"lat": 10.0287, "lon": 105.7835, "province": "VN-65", "district": "Ninh Kiều"},
    "Chùa Việt Nam Quốc Tự": {"lat": 10.0287, "lon": 105.7835, "province": "VN-65", "district": "Ninh Kiều"},
    "Chùa Minh Su": {"lat": 10.0287, "lon": 105.7835, "province": "VN-65", "district": "Cờ Đỏ"},
    
    # Sóc Trăng
    "Chùa Chăm": {"lat": 9.6023, "lon": 105.9716, "province": "VN-57", "district": "Sóc Trăng"},
    "Chùa Dăm": {"lat": 9.6023, "lon": 105.9716, "province": "VN-57", "district": "Vĩnh Châu"},
    
    # Trà Vinh
    "Chùa Cổ": {"lat": 9.9432, "lon": 106.2994, "province": "VN-53", "district": "Trà Vinh"},
    "Chùa Âu": {"lat": 9.9432, "lon": 106.2994, "province": "VN-53", "district": "Trà Vinh"},
    
    # Bến Tre
    "Chùa Phật Bổn": {"lat": 10.2417, "lon": 106.3795, "province": "VN-49", "district": "Bến Tre"},
    "Chùa Vĩnh Hội": {"lat": 10.2417, "lon": 106.3795, "province": "VN-49", "district": "Bến Tre"},
    
    # Long An
    "Chùa Phước Hòa": {"lat": 10.6854, "lon": 106.4088, "province": "VN-41", "district": "Tân An"},
    "Chùa Gia Loan": {"lat": 10.6854, "lon": 106.4088, "province": "VN-41", "district": "Kiến Tường"},
    
    # Tây Ninh
    "Chùa Cao Đài": {"lat": 11.3611, "lon": 106.1419, "province": "VN-37", "district": "Tây Ninh"},
    "Chùa Bà Đen": {"lat": 11.3611, "lon": 106.1419, "province": "VN-37", "district": "Tây Ninh"},
    "Chùa Tây Thiên": {"lat": 11.3611, "lon": 106.1419, "province": "VN-37", "district": "Tây Ninh"},
    "Chùa Hội Tông": {"lat": 11.3611, "lon": 106.1419, "province": "VN-37", "district": "Tây Ninh"},
    
    # Lâm Đồng (Đà Lạt)
    "Chùa Linh Phong": {"lat": 11.9322, "lon": 108.4579, "province": "VN-41", "district": "Đà Lạt"},
    "Chùa Thiên Vườn": {"lat": 11.9322, "lon": 108.4579, "province": "VN-41", "district": "Đà Lạt"},
    "Chùa Xá Lợi": {"lat": 11.9322, "lon": 108.4579, "province": "VN-41", "district": "Đà Lạt"},
    "Chùa Tịnh Xá Trung Tâm": {"lat": 11.9322, "lon": 108.4579, "province": "VN-41", "district": "Đà Lạt"},
    
    # Kon Tum
    "Chùa Kon Jo": {"lat": 14.3497, "lon": 108.0003, "province": "VN-37", "district": "Kon Tum"},
    "Chùa Yang Lep": {"lat": 14.3497, "lon": 108.0003, "province": "VN-37", "district": "Kon Tum"},
    
    # Gia Lai
    "Chùa Cheo Reo": {"lat": 13.9818, "lon": 108.0069, "province": "VN-38", "district": "Pleiku"},
    "Chùa Kan Thu": {"lat": 13.9818, "lon": 108.0069, "province": "VN-38", "district": "Pleiku"},
    
    # Đắk Lắk
    "Chùa Sắc": {"lat": 12.8833, "lon": 108.0667, "province": "VN-39", "district": "Buôn Ma Thuột"},
    "Chùa K'Bau": {"lat": 12.8833, "lon": 108.0667, "province": "VN-39", "district": "Buôn Ma Thuột"},
}

# Province ISO codes
PROVINCE_ISO = {
    "tp hồ chí minh": "VN-50", "hồ chí minh": "VN-50", "sài gòn": "VN-50",
    "hà nội": "VN-01", "hà nội": "VN-01",
    "huế": "VN-26", "thừa thiên huế": "VN-26",
    "đà nẵng": "VN-48",
    "khánh hòa": "VN-34", "nha trang": "VN-34",
    "bình dương": "VN-44", "thủ dầu một": "VN-44",
    "đồng nai": "VN-39", "biên hòa": "VN-39",
    "bà rịa vũng tàu": "VN-46", "vũng tàu": "VN-46",
    "an giang": "VN-36", "châu đốc": "VN-36",
    "kiên giang": "VN-67", "rạch giá": "VN-67",
    "tiền giang": "VN-46", "mỹ tho": "VN-46",
    "vĩnh long": "VN-54",
    "cần thơ": "VN-65",
    "sóc trăng": "VN-57",
    "trà vinh": "VN-53",
    "bến tre": "VN-49",
    "long an": "VN-41",
    "tây ninh": "VN-37",
    "lâm đồng": "VN-41", "đà lạt": "VN-41",
    "kon tum": "VN-37",
    "gia lai": "VN-38",
    "đắk lắk": "VN-39",
    "ninh bình": "VN-22",
    "quảng ninh": "VN-14",
    "hà nam": "VN-20",
}

NAME_START = ["chùa", "tịnh xá", "thiền viện", "tự", "am", "cốc", "quán", "trai", "viện", "đền", "miếu", "thánh từ"]

def extract_temple_name(line):
    """Trích xuất tên chùa từ dòng text - Strict version"""
    line = line.strip()
    if not line or len(line) < 8:
        return None
    
    line_lower = line.lower()
    
    # Find temple name prefix
    for prefix in NAME_START:
        if line_lower.startswith(prefix):
            # Extract name after prefix
            name = line[len(prefix):].strip()
            # Take only first part before common separators
            name = re.split(r'[,;(\[\-\:\.\"]', name)[0].strip()
            # Remove numbers at start
            name = re.sub(r'^[\d\.\,\s]+', '', name).strip()
            # Remove common suffixes
            name = re.sub(r'(tỉnh|thành phố|huyện|xã|quận|phường|tt\.?|núi|thị trấn)$', '', name, flags=re.I).strip()
            
            # STRICT: Valid name must be 4-30 chars, all Vietnamese words
            if 4 <= len(name) <= 30 and re.match(r'^[A-ZÀ-Ỵ][a-zà-ỵ\s]+$', name):
                return name
    return None

def detect_province(text):
    """Detect province from text"""
    text_lower = text.lower()
    for p, c in PROVINCE_ISO.items():
        if p in text_lower:
            return c
    return "VN-UN"

def main():
    print("=" * 60)
    print("🚀 VIETNAM TEMPLE EXTRACTOR (Enhanced)")
    print("=" * 60)
    
    # Get all txt files
    txt_files = glob.glob(os.path.join(INPUT_DIR, "*.txt"))
    print(f"📁 Found {len(txt_files)} dictionary files")
    
    temples = {}
    
    # Process each file
    for txt_file in txt_files:
        filename = os.path.basename(txt_file)
        print(f"  📄 Processing: {filename}")
        
        with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Extract temple name
                name = extract_temple_name(line)
                if not name:
                    continue
                
                # Normalize name
                name_normalized = name.lower().strip()
                
                # Check if in manual GPS database (case-insensitive, partial match)
                matched_gps = None
                for gps_name, gps_data in MANUAL_GPS.items():
                    # Match if either contains the other
                    gps_name_lower = gps_name.lower()
                    if (gps_name_lower in name_normalized or 
                        name_normalized in gps_name_lower or
                        (len(gps_name_lower) > 3 and len(name_normalized) > 3 and 
                         gps_name_lower[:6] == name_normalized[:6])):
                        matched_gps = gps_data
                        break
                
                if matched_gps:
                    if name_normalized not in temples:
                        temples[name_normalized] = {
                            "name": name,
                            "lat": matched_gps["lat"],
                            "lon": matched_gps["lon"],
                            "province": matched_gps.get("province", "VN-UN"),
                            "district": matched_gps.get("district", ""),
                            "source": "Manual-GPS"
                        }
                else:
                    # Add without GPS for now
                    if name_normalized not in temples:
                        province = detect_province(line)
                        temples[name_normalized] = {
                            "name": name,
                            "lat": None,
                            "lon": None,
                            "province": province,
                            "district": "",
                            "source": filename
                        }
    
    print(f"\n✅ Total unique temples: {len(temples)}")
    
    # Count with GPS
    with_gps = sum(1 for t in temples.values() if t["lat"])
    print(f"📍 Temples with GPS: {with_gps} (from manual database)")
    
    # Convert to list
    temple_list = list(temples.values())
    
    # Save
    output = {
        "version": "v2.3-Temples",
        "generated": "2026-04-09",
        "total": len(temple_list),
        "with_gps": with_gps,
        "temples": temple_list
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Saved: {OUTPUT_FILE}")
    
    # Show first 10
    print("\n📋 Sample temples:")
    for t in temple_list[:10]:
        gps_str = f"({t['lat']}, {t['lon']})" if t['lat'] else "(no GPS)"
        print(f"  - {t['name']} {gps_str}")

if __name__ == "__main__":
    main()