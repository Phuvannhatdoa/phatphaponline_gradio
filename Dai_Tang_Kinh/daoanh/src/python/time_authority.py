#!/usr/bin/env python3
"""
Time Authority - Calendar Conversion
JDN Converter + Lunisolar Calendar + Dynasty Mapping

@version: v4.14 (2026-04-10)
@file: src/python/time_authority.py
"""

import re
import math
from datetime import datetime, date
from typing import Optional, Tuple, Dict


class TimeAuthority:
    """Time Authority - Calendar conversion and date handling"""
    
    # Dynasty mappings (Vietnamese + Chinese)
    DYNASTIES = {
        # Vietnamese dynasties
        'triều lê': {'start': 1428, 'end': 1788, 'region': 'VN'},
        'triều trần': {'start': 1226, 'end': 1400, 'region': 'VN'},
        'triều lý': {'start': 1009, 'end': 1225, 'region': 'VN'},
        'triều nguyễn': {'start': 1802, 'end': 1945, 'region': 'VN'},
        'nhà lê': {'start': 1428, 'end': 1788, 'region': 'VN'},
        'nhà trần': {'start': 1226, 'end': 1400, 'region': 'VN'},
        'nhà lý': {'start': 1009, 'end': 1225, 'region': 'VN'},
        'nhà nguyễn': {'start': 1802, 'end': 1945, 'region': 'VN'},
        
        # Chinese dynasties
        'đường': {'start': 618, 'end': 907, 'region': 'CN'},
        'tang': {'start': 618, 'end': 907, 'region': 'CN'},
        'tống': {'start': 960, 'end': 1279, 'region': 'CN'},
        'song': {'start': 960, 'end': 1279, 'region': 'CN'},
        'minh': {'start': 1368, 'end': 1644, 'region': 'CN'},
        'thanh': {'start': 1644, 'end': 1912, 'region': 'CN'},
        'lưu tống': {'start': 420, 'end': 479, 'region': 'CN'},
        'nam bắc': {'start': 420, 'end': 589, 'region': 'CN'},
    }
    
    # Century mappings
    CENTURIES = {
        'thế kỷ 1': (1, 100),
        'thế kỷ 2': (100, 200),
        'thế kỷ 3': (200, 300),
        'thế kỷ 4': (300, 400),
        'thế kỷ 5': (400, 500),
        'thế kỷ 6': (500, 600),
        'thế kỷ 7': (600, 700),
        'thế kỷ 8': (700, 800),
        'thế kỷ 9': (800, 900),
        'thế kỷ 10': (900, 1000),
        'thế kỷ 11': (1000, 1100),
        'thế kỷ 12': (1100, 1200),
        'thế kỷ 13': (1200, 1300),
        'thế kỷ 14': (1300, 1400),
        'thế kỷ 15': (1400, 1500),
        'thế kỷ 16': (1500, 1600),
        'thế kỷ 17': (1600, 1700),
        'thế kỷ 18': (1700, 1800),
        'thế kỷ 19': (1800, 1900),
        'thế kỷ 20': (1900, 2000),
    }
    
    def __init__(self):
        self.stats = {'conversions': 0}
    
    def jdn_to_gregorian(self, jdn: int) -> date:
        """
        Convert Julian Day Number to Gregorian date
        
        @param jdn: Julian Day Number
        @returns: datetime.date object
        """
        self.stats['conversions'] += 1
        
        # Algorithm from Wikipedia
        f = jdn + 1401 + (((4 * jdn + 274277) // 146097) * 3) // 4 - 38
        
        e = 4 * f + 3
        g = (e % 1461) // 4
        h = 5 * g + 2
        
        day = (h % 153) // 5 + 1
        month = ((h // 153 + 2) % 12) + 1
        year = e // 1461 - 4716 + (12 + 2 - month) // 12
        
        return date(year, month, day)
    
    def gregorian_to_jdn(self, year: int, month: int, day: int) -> int:
        """
        Convert Gregorian date to Julian Day Number
        
        @param year: Year
        @param month: Month (1-12)
        @param day: Day (1-31)
        @returns: Julian Day Number
        """
        self.stats['conversions'] += 1
        
        # Algorithm from Wikipedia
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        
        jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        
        return jdn
    
    def parse_year(self, year_str: str) -> Optional[Tuple[int, int]]:
        """
        Parse year string to (min, max) range
        
        @param year_str: Year string like "1227" or "thế kỷ 13"
        @returns: (min_year, max_year) or None
        """
        year_str = year_str.lower().strip()
        
        # Check century
        for century, range_val in self.CENTURIES.items():
            if century in year_str:
                return range_val
        
        # Try to parse as year
        year_match = re.search(r'(\d{3,4})', year_str)
        if year_match:
            year = int(year_match.group(1))
            return (year, year + 1)
        
        return None
    
    def get_dynasty(self, year: int) -> Optional[Dict]:
        """
        Get dynasty information for a given year
        
        @param year: Year (e.g., 1227)
        @returns: Dynasty info dict or None
        """
        for name, info in self.DYNASTIES.items():
            if info['start'] <= year <= info['end']:
                return {
                    'name': name,
                    'start': info['start'],
                    'end': info['end'],
                    'region': info['region']
                }
        
        return None
    
    def parse_lunisolar_date(self, date_str: str) -> Optional[Dict]:
        """
        Parse lunisolar date string
        
        @param date_str: Date string like "01/01/2024" or "15/02/2024"
        @returns: Dict with lunar/solar info or None
        """
        # Try to detect if it's a lunar date (format: DD/MM/YYYY)
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
        
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            
            return {
                'day': day,
                'month': month,
                'year': year,
                'is_lunar': 'chạp' in date_str.lower() or 'tháng' in date_str.lower(),
                'jdn': self.gregorian_to_jdn(year, month, day)
            }
        
        return None
    
    def year_to_era(self, year: int, region: str = 'VN') -> str:
        """
        Convert year to era name
        
        @param year: Year (e.g., 1227)
        @param region: 'VN' or 'CN'
        @returns: Era string like "Năm thứ 2 Niên hiệu Thuần Vu"
        """
        # Check for Vietnamese dynasties first
        if region == 'VN':
            dynasty = self.get_dynasty(year)
            if dynasty:
                year_in_dynasty = year - dynasty['start'] + 1
                return f"Năm thứ {year_in_dynasty} {dynasty['name'].title()}"
        
        # Return simple year
        return f"Năm {year}"
    
    def get_century(self, year: int) -> str:
        """
        Get century from year
        
        @param year: Year (e.g., 1227)
        @returns: Century string like "thế kỷ 13"
        """
        century = (year - 1) // 100 + 1
        return f"thế kỷ {century}"
    
    def format_year_range(self, start: int, end: int) -> str:
        """
        Format year range as string
        
        @param start: Start year
        @param end: End year
        @returns: Formatted string
        """
        if end - start <= 1:
            return str(start)
        
        return f"{start} - {end}"
    
    def get_stats(self) -> Dict:
        """Get conversion statistics"""
        return self.stats.copy()


def main():
    """Demo function"""
    ta = TimeAuthority()
    
    # Test JDN conversions
    print("[TimeAuthority] Testing JDN conversions...")
    
    # Test: 1227 (Trần Thái Tông's first year)
    jdn = ta.gregorian_to_jdn(1227, 1, 1)
    print(f"  1227-01-01 → JDN: {jdn}")
    
    # Convert back
    greg = ta.jdn_to_gregorian(jdn)
    print(f"  JDN {jdn} → {greg}")
    
    # Test dynasty lookup
    print("\n[TimeAuthority] Testing dynasty lookup...")
    
    year = 1227
    dynasty = ta.get_dynasty(year)
    print(f"  Year {year}: {dynasty}")
    
    # Test century
    century = ta.get_century(1227)
    print(f"  Century of {year}: {century}")
    
    # Test year parsing
    print("\n[TimeAuthority] Testing year parsing...")
    
    result = ta.parse_year("thế kỷ 13")
    print(f"  'thế kỷ 13' → {result}")
    
    result = ta.parse_year("1227")
    print(f"  '1227' → {result}")
    
    # Test era conversion
    print("\n[TimeAuthority] Testing era conversion...")
    
    era = ta.year_to_era(1227, 'VN')
    print(f"  1227 (VN) → {era}")
    
    era = ta.year_to_era(700, 'CN')
    print(f"  700 (CN) → {era}")


if __name__ == '__main__':
    main()
