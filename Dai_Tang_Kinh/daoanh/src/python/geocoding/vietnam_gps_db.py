#!/usr/bin/env python3
"""
B: Vietnamese Temple GPS Database
Common Vietnamese temples with known GPS
"""

import json

# Pre-defined GPS for famous Vietnamese temples
VIETNAM_TEMPLES = {
    "Thiếu Lâm Tự": {"lat": "34.5085", "lon": "112.9347", "province": "Hà Nam, Trung Quốc"},
    "Linh Sơn": {"lat": "21.0032", "lon": "105.8570", "province": "Hà Nội"},
    "Trúc Lâm": {"lat": "21.9477", "lon": "106.0293", "province": "Yên Tử, Quảng Ninh"},
    "Quảng Nghiêm": {"lat": "15.8967", "lon": "108.3333", "province": "Hội An, Quảng Nam"},
    "Chúc Thánh": {"lat": "15.8769", "lon": "108.3263", "province": "Hội An, Quảng Nam"},
    "Bảo Quốc": {"lat": "16.0544", "lon": "108.2022", "province": "Huế, Thừa Thiên Huế"},
    "Từ Đàm": {"lat": "16.0621", "lon": "108.2178", "province": "Huế, Thừa Thiên Huế"},
    "Minh Mạng": {"lat": "16.0608", "lon": "108.2211", "province": "Huế, Thừa Thiên Huế"},
    "Tuệ Tĩnh": {"lat": "16.0567", "lon": "108.2200", "province": "Huế, Thừa Thiên Huế"},
    "Phước Định": {"lat": "10.7769", "lon": "106.6889", "province": "TP.HCM"},
    "Xá Lợi": {"lat": "10.7876", "lon": "106.6989", "province": "TP.HCM"},
    "Vĩnh Nghiêm": {"lat": "10.7870", "lon": "106.6890", "province": "TP.HCM"},
    "Giác Quang": {"lat": "21.0285", "lon": "105.8342", "province": "Hà Nội"},
    "Quán Sứ": {"lat": "21.0285", "lon": "105.8342", "province": "Hà Nội"},
    "Thanh Xá": {"lat": "20.0444", "lon": "105.9117", "province": "Nghệ An"},
    "Yên Tử": {"lat": "21.9477", "lon": "106.0293", "province": "Quảng Ninh"},
    "Quỳnh Lâm": {"lat": "21.8900", "lon": "106.0500", "province": "Nghệ An"},
    "Phổ Minh": {"lat": "20.2550", "lon": "106.3360", "province": "Nam Định"},
    "Chùa Ông": {"lat": "10.3703", "lon": "107.0847", "province": "Vũng Tàu"},
    "Cầu Quảng": {"lat": "16.0544", "lon": "108.2022", "province": "Huế"},
    "Tây Thiên": {"lat": "21.9477", "lon": "106.0293", "province": "Quảng Ninh"},
    "Phật Tọa": {"lat": "15.8769", "lon": "108.3263", "province": "Quảng Nam"},
    "Linhi Đà": {"lat": "10.7769", "lon": "106.6889", "province": "TP.HCM"},
    "Huế": {"lat": "16.0544", "lon": "108.2022", "province": "Thừa Thiên Huế"},
    "Hà Nội": {"lat": "21.0285", "lon": "105.8342", "province": "Hà Nội"},
    "TP.HCM": {"lat": "10.7769", "lon": "106.6889", "province": "TP.HCM"},
    "Đà Nẵng": {"lat": "16.0544", "lon": "108.2022", "province": "Đà Nẵng"},
    "Hội An": {"lat": "15.8967", "lon": "108.3333", "province": "Quảng Nam"},
    "Nghệ An": {"lat": "18.6657", "lon": "105.6939", "province": "Nghệ An"},
    "Quảng Ninh": {"lat": "21.0062", "lon": "107.2865", "province": "Quảng Ninh"},
}

def add_gps(places):
    """Add GPS from database"""
    count = 0
    for p in places:
        matched = p.get('matched_name', '')
        if matched in VIETNAM_TEMPLES:
            gps = VIETNAM_TEMPLES[matched]
            p['lat'] = gps['lat']
            p['lon'] = gps['lon']
            p['province'] = gps['province']
            count += 1
    return count

if __name__ == "__main__":
    print("Vietnam Temple GPS Database loaded")
    print(f"Total temples: {len(VIETNAM_TEMPLES)}")
    for name, gps in list(VIETNAM_TEMPLES.items())[:10]:
        print(f"  {name}: {gps['lat']},{gps['lon']}")
