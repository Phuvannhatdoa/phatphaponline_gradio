#!/usr/bin/env python3
"""
Quick parser for Buddhist dictionaries - optimized for speed
"""

import os
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DICT_DIR = BASE_DIR / "dictionaries"
OUTPUT_DIR = BASE_DIR / "processed"
OUTPUT_DIR.mkdir(exist_ok=True)

# HANDS-EDITED DICTIONARY for critical places
# This will be the foundation for auto-parsing
CRITICAL_PLACES = {
    "曹溪": {
        "vietnamese": "Tào Khê",
        "description": "Tào Khê (曹溪) - Tên gọi khác của núi Nhạc Thạch, nơi Lục Tổ Huệ Năng truyền pháp từ 667-713. Còn gọi là Nam Hoa Kiến. Thuộc huyện Nhạc Châu, tỉnh Quảng Đông, Trung Quốc. Là trung tâm của thiền tông Nam Tuệ.",
        "type": "monastery",
        "period": "Tang Dynasty",
        "relatedMonks": ["Huệ Năng", "Huì Néng (Lục Tổ)"],
        "relatedSutras": ["Đàn Kinh"]
    },
    "曹溪山": {
        "vietnamese": "Tào Khê Sơn",
        "description": "Tào Khê Sơn - Ngọn núi nơi Lục Tổ Huệ Năng ở ẩn và truyền pháp sau khi lén rời Hòa Bình. Thuộc huyện Nhạc Châu, Quảng Đông.",
        "type": "mountain",
        "period": "Tang Dynasty"
    },
    "少林寺": {
        "vietnamese": "Thiếu Lâm Tự",
        "description": "Thiếu Lâm Tự (少林寺) - Ngôi chùa nổi tiếng nhất Trung Quốc, nằm ở Tung Sơn, Hà Nam. Được Võ Đường chùa năm 495. Nơi Bồ Đề Đạt Ma truyền pháp và khởi nguồn võ thuật Thiếu Lâm. GPS: 34.5085, 112.9347",
        "type": "monastery",
        "period": "Wei-North Dynasty",
        "gps": {"lat": 34.5085, "lon": 112.9347},
        "relatedMonks": ["Bồ Đề Đạt Ma", "Huệ Khả", "Trí Không"]
    },
    "南嶽": {
        "vietnamese": "Nam Nhạc",
        "description": "Nam Nhạc (南嶽) - Một trong Ngũ Đại Danh Sơn, thuộc tỉnh Hồ Nam, Trung Quốc. Nổi tiếng với chùa Pháp Vũ, nơi Quân Tử Cái truyền pháp.",
        "type": "mountain",
        "period": "Various"
    },
    "福州": {
        "vietnamese": "Phúc Châu",
        "description": "Phúc Châu (福州) - Thủ phủ tỉnh Phúc Kiến, Trung Quốc. Nơi có am Ngọa Long, nơi Lục Tổ Huệ Năng tu tập trước khi gặp Ngũ Tông.",
        "type": "city",
        "period": "Tang Dynasty"
    },
    "黄梅": {
        "vietnamese": "Hoàng Mai",
        "description": "Hoàng Mai (黄梅) - Huyện thuộc tỉnh Hồ Bắc, Trung Quốc. Nơi Lục Tổ Huệ Năng ngụ ở am lúc đắc pháp và tránh sự truy sát của đệ tử. Có núi Sung Sơn (Thiên Thai).",
        "type": "city",
        "period": "Tang Dynasty"
    },
    "弘忍": {
        "vietnamese": "Hoằng Nhẫn",
        "description": "Hoằng Nhẫn (弘忍) - Vị Tổ thứ năm của thiền tông Trung Quốc (601-675). Trụ tại Hòa Bình am trên núi Sơn Hùng, Nam Nhạc. Người truyền pháp cho Huệ Năng.",
        "type": "monk",
        "period": "Early Tang"
    },
    "慧能": {
        "vietnamese": "Huệ Năng",
        "description": "Huệ Năng (慧能) - Lục Tổ (638-713), vị Tổ thứ sáu của thiền tông Trung Quốc. Người Quảng Đông, xuất gia năm 22 tuổi tại Phúc Châu. Gặp Ngũ Tông Hoằng Nhẫn tại Hòa Bình am, được truyền pháp kinh Đại Giác. Nổi tiếng với bài kệ 'Bồ Đề Bổn Vô Song'.",
        "type": "monk",
        "period": "Tang Dynasty",
        "gps": {"lat": 23.9, "lon": 113.5},
        "relatedSutras": ["Đàn Kinh", "Kim Cương Kinh"]
    },
    "Lục Tổ": {
        "vietnamese": "Lục Tổ",
        "description": "Lục Tổ Huệ Năng (638-713) - Vị Tổ thứ sáu của thiền tông Trung Quốc, người khai sinh dòng thiền Nam Tuệ. Xuất thân từ Lão Giáp, Quảng Đông. Đắc pháp tại Hòa Bình am, truyền pháp tại Tào Khê.",
        "type": "monk",
        "period": "Tang Dynasty"
    },
    "南宗": {
        "vietnamese": "Nam Tông",
        "description": "Nam Tông (南宗) - Dòng thiền do Lục Tổ Huệ Năng khai sáng, còn gọi là Nam Tuệ. Phân bố chủ yếu ở miền Nam Trung Quốc, sau truyền sang Việt Nam, Nhật Bản, Hàn Quốc.",
        "type": "lineage",
        "period": "Tang Dynasty onwards"
    },
    "Bodhidharma": {
        "vietnamese": "Bồ Đề Đạt Ma",
        "description": "Bồ Đề Đạt Ma (菩提達摩) - Tổ sư đầu tiên của thiền tông Trung Quốc, người Ấn Độ. Sang Trung Quốc khoảng năm 527, truyền pháp cho Huệ Khả tại Thiếu Lâm Tự. Được xem là Tổ thứ 28 của Phật giáo Ấn Độ.",
        "type": "monk",
        "period": "Liang Dynasty"
    },
    "祇園精舍": {
        "vietnamese": "Kỳ Viên Tinh Xá",
        "description": "Kỳ Viên Tinh Xá (祇園精舍) - Jetavana, khu vườn của Trưởng giả Kỳ Đà, nơi Đức Phật thuyết nhiều kinh quan trọng. Tọa lạc tại Sravasti, Ấn Độ. GPS: 27.47, 82.04",
        "type": "monastery",
        "period": "Ancient India",
        "gps": {"lat": 27.47, "lon": 82.04}
    },
    "鹿野苑": {
        "vietnamese": "Lộc Uyển",
        "description": "Lộc Uyển (鹿野苑) - Isipatana, nơi Đức Phật thuyết pháp lần đầu sau khi giác ngộ (Chuyển Pháp Luân). Tọa lạc gần Varanasi, Ấn Độ. GPS: 25.1389, 83.0261",
        "type": "sacred_place",
        "period": "Ancient India",
        "gps": {"lat": 25.1389, "lon": 83.0261}
    },
    "靈山會": {
        "vietnamese": "Linh Sơn Hội",
        "description": "Linh Sơn Hội (靈山會) - Đại hội núi Linh Sơn, nơi Đức Phật thuyết nhiều kinh quan trọng, đặc biệt là Pháp Hoa. Tọa lạc tại Rajgir, Ấn Độ.",
        "type": "sacred_place",
        "period": "Ancient India"
    },
    "菩提伽耶": {
        "vietnamese": "Bồ Đề Đạo Tràng",
        "description": "Bồ Đề Đạo Tràng (菩提伽耶) - Bodh Gaya, nơi Đức Phật giác ngộ dưới cội bồ đề. Tọa lạc tại Bihar, Ấn Độ. GPS: 24.6961, 84.9911",
        "type": "sacred_place",
        "period": "Ancient India",
        "gps": {"lat": 24.6961, "lon": 84.9911}
    }
}

def save_critical_data():
    """Save critical places data"""
    
    # Save as lookup dict
    lookup_file = OUTPUT_DIR / "critical_places_lookup.json"
    with open(lookup_file, 'w', encoding='utf-8') as f:
        json.dump(CRITICAL_PLACES, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(CRITICAL_PLACES)} critical places to: {lookup_file}")
    
    # Also create a flat list for search
    search_list = []
    for key, data in CRITICAL_PLACES.items():
        search_list.append({
            "searchKey": key,
            "vietnamese": data.get("vietnamese", ""),
            "description": data.get("description", ""),
            "type": data.get("type", ""),
            "period": data.get("period", ""),
            "gps": data.get("gps", {}),
            "relatedMonks": data.get("relatedMonks", []),
            "relatedSutras": data.get("relatedSutras", [])
        })
    
    search_file = OUTPUT_DIR / "search_index_critical.json"
    with open(search_file, 'w', encoding='utf-8') as f:
        json.dump(search_list, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(search_list)} search items to: {search_file}")
    
    return CRITICAL_PLACES

if __name__ == "__main__":
    save_critical_data()
    print("\n🎯 Data ready for search integration!")
