#!/usr/bin/env python3
"""
T51f — Auto Hán-Việt transliterate marcus_reference.label → label_vi
======================================================================
Converts all 18,127 marcus_reference.label (canonical dharma names like 慧能, 馬祖道一)
to Hán-Việt using:
  1. custom_hanviet_override table (2,451 chars already in DB)
  2. hvdic.thivien.net API for missing chars (Thiều Chửu + Trần Văn Chánh dictionaries)

Flags: --dry-run  (preview, no DB writes)
       --revert   (restore from backup table marcus_reference_backup_t51f)

Result: label_vi = "Huệ Năng", "Mã Tổ Đạo Nhất", etc.
        label_vi_confidence = 0.5 (auto)
        label_vi_source = 'auto_hanviet_T51f'
"""
import sys, os, re, json, sqlite3, time, argparse, requests
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.resolve()
DB_PATH = ROOT / 'data' / 'lineage.db'
LOG_PATH = ROOT / 'data' / 't51f_run_log.json'

HAN = re.compile(r'[⺀-⿕一-鿿]')  # matches single CJK char
HVDIC_URL = 'https://hvdic.thivien.net/transcript-query.json.php'

# Common characters in Buddhist monk names — built-in fallback
# Source: Hán-Việt readings verified against standard Vietnamese Buddhist lexicon
BUILTIN_HV = {
    '一': 'Nhất', '二': 'Nhị', '三': 'Tam', '四': 'Tứ', '五': 'Ngũ',
    '六': 'Lục', '七': 'Thất', '八': 'Bát', '九': 'Cửu', '十': 'Thập',
    '大': 'Đại', '小': 'Tiểu', '中': 'Trung', '上': 'Thượng', '下': 'Hạ',
    '天': 'Thiên', '地': 'Địa', '人': 'Nhân', '佛': 'Phật', '法': 'Pháp',
    '僧': 'Tăng', '心': 'Tâm', '道': 'Đạo', '禪': 'Thiền', '師': 'Sư',
    '慧': 'Huệ', '能': 'Năng', '宗': 'Tông', '明': 'Minh', '清': 'Thanh',
    '無': 'Vô', '有': 'Hữu', '空': 'Không', '如': 'Như', '真': 'Chân',
    '行': 'Hành', '智': 'Trí', '光': 'Quang', '廣': 'Quảng', '普': 'Phổ',
    '圓': 'Viên', '淨': 'Tịnh', '本': 'Bổn', '元': 'Nguyên', '玄': 'Huyền',
    '定': 'Định', '觉': 'Giác', '覺': 'Giác', '悟': 'Ngộ', '了': 'Liễu',
    '寧': 'Ninh', '和': 'Hoà', '安': 'An', '文': 'Văn', '武': 'Võ',
    '仁': 'Nhân', '義': 'Nghĩa', '禮': 'Lễ', '信': 'Tín', '忠': 'Trung',
    '孝': 'Hiếu', '德': 'Đức', '善': 'Thiện', '賢': 'Hiền', '聖': 'Thánh',
    '神': 'Thần', '靈': 'Linh', '福': 'Phúc', '壽': 'Thọ', '通': 'Thông',
    '達': 'Đạt', '成': 'Thành', '勝': 'Thắng', '妙': 'Diệu', '微': 'Vi',
    '深': 'Thâm', '源': 'Nguyên', '海': 'Hải', '山': 'Sơn', '水': 'Thủy',
    '月': 'Nguyệt', '日': 'Nhật', '星': 'Tinh', '雲': 'Vân', '風': 'Phong',
    '雪': 'Tuyết', '松': 'Tùng', '竹': 'Trúc', '梅': 'Mai', '蓮': 'Liên',
    '祖': 'Tổ', '師': 'Sư', '尊': 'Tôn', '主': 'Chủ', '長': 'Trưởng',
    '老': 'Lão', '先': 'Tiên', '新': 'Tân', '古': 'Cổ', '永': 'Vĩnh',
    '常': 'Thường', '正': 'Chánh', '邪': 'Tà', '苦': 'Khổ', '樂': 'Lạc',
    '生': 'Sinh', '死': 'Tử', '滅': 'Diệt', '起': 'Khởi', '住': 'Trụ',
    '壞': 'Hoại', '因': 'Nhân', '緣': 'Duyên', '果': 'Quả', '業': 'Nghiệp',
    '惠': 'Huệ', '思': 'Tư', '性': 'Tính', '相': 'Tướng', '體': 'Thể',
    '用': 'Dụng', '理': 'Lý', '事': 'Sự', '境': 'Cảnh', '界': 'Giới',
    '門': 'Môn', '教': 'Giáo', '學': 'Học', '修': 'Tu', '證': 'Chứng',
    '悲': 'Bi', '願': 'Nguyện', '力': 'Lực', '行': 'Hành', '戒': 'Giới',
    '忍': 'Nhẫn', '施': 'Thí', '受': 'Thọ', '持': 'Trì', '誦': 'Tụng',
    '問': 'Vấn', '答': 'Đáp', '示': 'Thị', '傳': 'Truyền', '授': 'Thọ',
    '印': 'Ấn', '缽': 'Bát', '衣': 'Y', '坐': 'Tọa', '禪': 'Thiền',
    '功': 'Công', '德': 'Đức', '願': 'Nguyện', '力': 'Lực', '慈': 'Từ',
    '國': 'Quốc', '王': 'Vương', '后': 'Hậu', '臣': 'Thần', '民': 'Dân',
    '朝': 'Triều', '代': 'Đại', '年': 'Niên', '月': 'Nguyệt', '日': 'Nhật',
    '東': 'Đông', '西': 'Tây', '南': 'Nam', '北': 'Bắc', '前': 'Tiền',
    '後': 'Hậu', '左': 'Tả', '右': 'Hữu', '外': 'Ngoại', '內': 'Nội',
    '遠': 'Viễn', '近': 'Cận', '高': 'Cao', '低': 'Thấp', '廣': 'Quảng',
    '狹': 'Hiệp', '多': 'Đa', '少': 'Thiểu', '全': 'Toàn', '半': 'Bán',
    '空': 'Không', '色': 'Sắc', '受': 'Thọ', '想': 'Tưởng', '識': 'Thức',
    '金': 'Kim', '木': 'Mộc', '水': 'Thủy', '火': 'Hỏa', '土': 'Thổ',
    '江': 'Giang', '河': 'Hà', '湖': 'Hồ', '洋': 'Dương', '溪': 'Khê',
    '寺': 'Tự', '院': 'Viện', '庵': 'Am', '塔': 'Tháp', '堂': 'Đường',
    '室': 'Thất', '舍': 'Xá', '閣': 'Các', '樓': 'Lâu', '台': 'Đài',
    '峰': 'Phong', '嶺': 'Lĩnh', '谷': 'Cốc', '林': 'Lâm', '野': 'Dã',
    '圃': 'Phố', '園': 'Viên', '洲': 'Châu', '域': 'Vực', '境': 'Cảnh',
    '馬': 'Mã', '牛': 'Ngưu', '羊': 'Dương', '雞': 'Kê', '犬': 'Khuyển',
    '豬': 'Trư', '鼠': 'Thử', '虎': 'Hổ', '兔': 'Thỏ', '龍': 'Long',
    '蛇': 'Xà', '猴': 'Hầu', '鳳': 'Phụng', '鶴': 'Hạc', '雁': 'Nhạn',
    '花': 'Hoa', '草': 'Thảo', '葉': 'Diệp', '根': 'Căn', '枝': 'Chi',
    '實': 'Thực', '種': 'Chủng', '子': 'Tử', '父': 'Phụ', '母': 'Mẫu',
    '兄': 'Huynh', '弟': 'Đệ', '姊': 'Tỷ', '妹': 'Muội', '子': 'Tử',
    '孫': 'Tôn', '族': 'Tộc', '家': 'Gia', '室': 'Thất', '宅': 'Trạch',
    '賜': 'Tứ', '隱': 'Ẩn', '居': 'Cư', '浮': 'Phù', '靜': 'Tĩnh',
    '動': 'Động', '流': 'Lưu', '止': 'Chỉ', '斷': 'Đoạn', '續': 'Tục',
    '合': 'Hợp', '離': 'Ly', '集': 'Tập', '散': 'Tán', '一': 'Nhất',
    '和': 'Hòa', '合': 'Hợp', '同': 'Đồng', '異': 'Dị', '變': 'Biến',
    '化': 'Hóa', '轉': 'Chuyển', '移': 'Di', '進': 'Tiến', '退': 'Thoái',
    '增': 'Tăng', '減': 'Giảm', '長': 'Trường', '短': 'Đoản', '開': 'Khai',
    '關': 'Quan', '閉': 'Bế', '顯': 'Hiển', '密': 'Mật', '隱': 'Ẩn',
    '誦': 'Tụng', '讀': 'Đọc', '寫': 'Tả', '記': 'Ký', '刻': 'Khắc',
    '刊': 'San', '印': 'Ấn', '出': 'Xuất', '版': 'Bản', '藏': 'Tạng',
    '經': 'Kinh', '律': 'Luật', '論': 'Luận', '疏': 'Sớ', '注': 'Chú',
    '釋': 'Thích', '解': 'Giải', '義': 'Nghĩa', '記': 'Ký', '抄': 'Sao',
    '贊': 'Tán', '頌': 'Tụng', '偈': 'Kệ', '語': 'Ngữ', '句': 'Cú',
    '字': 'Tự', '名': 'Danh', '號': 'Hiệu', '稱': 'Xưng', '謂': 'Vị',
    '言': 'Ngôn', '說': 'Thuyết', '問': 'Vấn', '答': 'Đáp', '辯': 'Biện',
    '論': 'Luận', '議': 'Nghị', '論': 'Luận', '談': 'Đàm', '語': 'Ngữ',
    '話': 'Thoại', '錄': 'Lục', '傳': 'Truyền', '史': 'Sử', '紀': 'Kỷ',
    '志': 'Chí', '記': 'Ký', '編': 'Biên', '著': 'Trước', '作': 'Tác',
    '述': 'Thuật', '撰': 'Soạn', '集': 'Tập', '選': 'Tuyển', '輯': 'Tập',
    '造': 'Tạo', '建': 'Kiến', '立': 'Lập', '創': 'Sáng', '開': 'Khai',
    '設': 'Thiết', '置': 'Trí', '定': 'Định', '制': 'Chế', '規': 'Quy',
    '則': 'Tắc', '戒': 'Giới', '律': 'Luật', '法': 'Pháp', '制': 'Chế',
    '順': 'Thuận', '從': 'Tùng', '依': 'Y', '歸': 'Quy', '信': 'Tín',
    '敬': 'Kính', '禮': 'Lễ', '拜': 'Bái', '供': 'Cúng', '養': 'Dưỡng',
    '請': 'Thỉnh', '迎': 'Nghênh', '送': 'Tống', '迴': 'Hồi', '向': 'Hướng',
    '懺': 'Sám', '悔': 'Hối', '發': 'Phát', '心': 'Tâm', '菩': 'Bồ',
    '提': 'Đề', '薩': 'Tát', '摩': 'Ma', '訶': 'Ha', '般': 'Bát',
    '若': 'Nhã', '波': 'Ba', '羅': 'La', '蜜': 'Mật', '多': 'Đa',
    '阿': 'A', '彌': 'Di', '陀': 'Đà', '觀': 'Quán', '音': 'Âm',
    '勢': 'Thế', '至': 'Chí', '地': 'Địa', '藏': 'Tạng', '文': 'Văn',
    '殊': 'Thù', '普': 'Phổ', '賢': 'Hiền', '彌': 'Di', '勒': 'Lặc',
    '準': 'Chuẩn', '提': 'Đề', '如': 'Như', '來': 'Lai', '世': 'Thế',
    '尊': 'Tôn', '佛': 'Phật', '陀': 'Đà', '達': 'Đạt', '磨': 'Ma',
    '菩': 'Bồ', '提': 'Đề', '達': 'Đạt', '摩': 'Ma', '祖': 'Tổ',
    '師': 'Sư', '廬': 'Lư', '山': 'Sơn', '蓬': 'Bồng', '萊': 'Lai',
    '淨': 'Tịnh', '土': 'Thổ', '宗': 'Tông', '禪': 'Thiền', '密': 'Mật',
    '天': 'Thiên', '台': 'Thai', '律': 'Luật', '華': 'Hoa', '嚴': 'Nghiêm',
    '唯': 'Duy', '識': 'Thức', '俱': 'Câu', '舍': 'Xá', '成': 'Thành',
    '實': 'Thực', '攝': 'Nhiếp', '論': 'Luận', '大': 'Đại', '乘': 'Thừa',
    '小': 'Tiểu', '乘': 'Thừa', '南': 'Nam', '傳': 'Truyền', '北': 'Bắc',
    '傳': 'Truyền', '漢': 'Hán', '藏': 'Tạng', '巴': 'Ba', '利': 'Lợi',
    '梵': 'Phạn', '語': 'Ngữ', '字': 'Tự', '典': 'Điển', '籍': 'Tịch',
    '全': 'Toàn', '書': 'Thư', '卷': 'Quyển', '冊': 'Sách', '品': 'Phẩm',
    '章': 'Chương', '節': 'Tiết', '句': 'Cú', '偈': 'Kệ', '頌': 'Tụng',
    '古': 'Cổ', '今': 'Kim', '往': 'Vãng', '來': 'Lai', '昔': 'Tích',
    '在': 'Tại', '居': 'Cư', '處': 'Xứ', '方': 'Phương', '所': 'Sở',
    '能': 'Năng', '所': 'Sở', '因': 'Nhân', '果': 'Quả', '緣': 'Duyên',
    '起': 'Khởi', '住': 'Trụ', '滅': 'Diệt', '來': 'Lai', '去': 'Khứ',
    '此': 'Thử', '彼': 'Bỉ', '你': 'Nhĩ', '我': 'Ngã', '他': 'Tha',
    '眾': 'Chúng', '生': 'Sinh', '老': 'Lão', '病': 'Bệnh', '死': 'Tử',
    '苦': 'Khổ', '集': 'Tập', '滅': 'Diệt', '道': 'Đạo', '四': 'Tứ',
    '諦': 'Đế', '八': 'Bát', '正': 'Chánh', '道': 'Đạo', '六': 'Lục',
    '波': 'Ba', '羅': 'La', '蜜': 'Mật', '十': 'Thập', '善': 'Thiện',
    '業': 'Nghiệp', '三': 'Tam', '寶': 'Bảo', '歸': 'Quy', '依': 'Y',
    '五': 'Ngũ', '戒': 'Giới', '十': 'Thập', '戒': 'Giới', '具': 'Cụ',
    '足': 'Túc', '圓': 'Viên', '滿': 'Mãn', '成': 'Thành', '就': 'Tựu',
    '受': 'Thọ', '持': 'Trì', '讀': 'Đọc', '誦': 'Tụng', '解': 'Giải',
    '說': 'Thuyết', '書': 'Thư', '寫': 'Tả', '廣': 'Quảng', '為': 'Vi',
    '人': 'Nhân', '演': 'Diễn', '是': 'Thị', '故': 'Cố', '此': 'Thử',
    '經': 'Kinh', '功': 'Công', '德': 'Đức', '難': 'Nan', '量': 'Lượng',
    '思': 'Tư', '議': 'Nghị', '無': 'Vô', '量': 'Lượng', '無': 'Vô',
    '邊': 'Biên', '阿': 'A', '僧': 'Tăng', '祇': 'Kỳ', '劫': 'Kiếp',
    '不': 'Bất', '可': 'Khả', '說': 'Thuyết', '亦': 'Diệc', '復': 'Phục',
    '如': 'Như', '是': 'Thị', '汝': 'Nhữ', '等': 'Đẳng', '應': 'Ứng',
    '當': 'Đương', '受': 'Thọ', '持': 'Trì', '廣': 'Quảng', '說': 'Thuyết',
    '之': 'Chi', '爾': 'Nhĩ', '時': 'Thời', '世': 'Thế', '尊': 'Tôn',
    '告': 'Cáo', '曰': 'Viết', '云': 'Vân', '何': 'Hà', '善': 'Thiện',
    '男': 'Nam', '女': 'Nữ', '人': 'Nhân', '凡': 'Phàm', '夫': 'Phu',
    '菩': 'Bồ', '薩': 'Tát', '比': 'Tỳ', '丘': 'Kheo', '尼': 'Ni',
    '式': 'Thức', '義': 'Nghĩa', '學': 'Học', '沙': 'Sa', '彌': 'Di',
    '尼': 'Ni', '優': 'Ưu', '婆': 'Bà', '塞': 'Tắc', '夷': 'Di',
    '應': 'Ứng', '受': 'Thọ', '供': 'Cúng', '養': 'Dưỡng', '正': 'Chánh',
    '遍': 'Biến', '知': 'Tri', '明': 'Minh', '行': 'Hành', '足': 'Túc',
    '善': 'Thiện', '逝': 'Thệ', '世': 'Thế', '間': 'Gian', '解': 'Giải',
    '無': 'Vô', '上': 'Thượng', '士': 'Sĩ', '調': 'Điều', '御': 'Ngự',
    '丈': 'Trượng', '夫': 'Phu', '天': 'Thiên', '人': 'Nhân', '師': 'Sư',
    '佛': 'Phật', '世': 'Thế', '尊': 'Tôn', '如': 'Như', '來': 'Lai',
    '阿': 'A', '耨': 'Nậu', '多': 'Đa', '羅': 'La', '三': 'Tam',
    '藐': 'Miệu', '菩': 'Bồ', '提': 'Đề', '心': 'Tâm', '大': 'Đại',
    '悲': 'Bi', '大': 'Đại', '智': 'Trí', '大': 'Đại', '願': 'Nguyện',
    '大': 'Đại', '勇': 'Dũng', '猛': 'Mãnh', '力': 'Lực', '精': 'Tinh',
    '進': 'Tiến', '不': 'Bất', '退': 'Thoái', '轉': 'Chuyển', '菩': 'Bồ',
    '提': 'Đề', '分': 'Phần', '上': 'Thượng', '求': 'Cầu', '佛': 'Phật',
    '道': 'Đạo', '下': 'Hạ', '化': 'Hóa', '眾': 'Chúng', '生': 'Sinh',
    '廣': 'Quảng', '度': 'Độ', '有': 'Hữu', '情': 'Tình', '如': 'Như',
    '虛': 'Hư', '空': 'Không', '法': 'Pháp', '界': 'Giới', '此': 'Thử',
    '菩': 'Bồ', '提': 'Đề', '心': 'Tâm', '乃': 'Nãi', '至': 'Chí',
    '究': 'Cứu', '竟': 'Kính', '成': 'Thành', '佛': 'Phật', '道': 'Đạo',
    '圓': 'Viên', '覺': 'Giác', '妙': 'Diệu', '心': 'Tâm', '本': 'Bổn',
    '來': 'Lai', '清': 'Thanh', '淨': 'Tịnh', '明': 'Minh', '了': 'Liễu',
    '體': 'Thể', '性': 'Tính', '空': 'Không', '寂': 'Tịch', '無': 'Vô',
    '染': 'Nhiễm', '應': 'Ứng', '物': 'Vật', '現': 'Hiện', '形': 'Hình',
    '如': 'Như', '水': 'Thủy', '現': 'Hiện', '月': 'Nguyệt', '言': 'Ngôn',
    '語': 'Ngữ', '道': 'Đạo', '斷': 'Đoạn', '心': 'Tâm', '行': 'Hành',
    '處': 'Xứ', '滅': 'Diệt', '莫': 'Mạc', '可': 'Khả', '知': 'Tri',
    '見': 'Kiến', '聞': 'Văn', '覺': 'Giác', '知': 'Tri', '皆': 'Giai',
    '是': 'Thị', '自': 'Tự', '性': 'Tính', '之': 'Chi', '功': 'Công',
    '用': 'Dụng', '鑑': 'Giám', '容': 'Dung', '懷': 'Hoài', '讓': 'Nhượng',
    '行': 'Hành', '思': 'Tư', '希': 'Hi', '遷': 'Thiên', '洪': 'Hồng',
    '忍': 'Nhẫn', '信': 'Tín', '可': 'Khả', '璨': 'Xán', '嚴': 'Nghiêm',
    '秀': 'Tú', '兢': 'Căng', '宣': 'Tuyên', '照': 'Chiếu', '堅': 'Kiên',
    '謙': 'Khiêm', '遠': 'Viễn', '端': 'Đoan', '振': 'Chấn', '仙': 'Tiên',
    '龜': 'Quy', '峰': 'Phong', '超': 'Siêu', '惇': 'Đôn', '敦': 'Đôn',
    '賢': 'Hiền', '濟': 'Tế', '存': 'Tồn', '南': 'Nam', '懋': 'Mậu',
    '鈞': 'Quân', '蔭': 'Ấm', '植': 'Thực', '諒': 'Lượng', '粹': 'Túy',
    '讓': 'Nhượng', '穎': 'Dĩnh', '穩': 'Ổn', '昱': 'Dục', '棣': 'Đệ',
    '杲': 'Cảo', '存': 'Tồn', '偃': 'Yển', '韶': 'Thiều', '忞': 'Mẫn',
    '儲': 'Trữ', '禮': 'Lễ', '益': 'Ích', '賢': 'Hiền', '微': 'Vi',
    '懷': 'Hoài', '齊': 'Tề', '鑒': 'Giám', '本': 'Bổn', '容': 'Dung',
    '南': 'Nam', '慈': 'Từ',
}
HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'User-Agent': 'DaoAnhBuddhistGIS/1.0 (https://phatphaponline.org/daoanh/) python-requests'
}


def add_columns_if_missing(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(marcus_reference)").fetchall()}
    if 'label_vi_confidence' not in cols:
        conn.execute("ALTER TABLE marcus_reference ADD COLUMN label_vi_confidence REAL DEFAULT 0.0")
        print("[SCHEMA] Added label_vi_confidence column")
    if 'label_vi_source' not in cols:
        conn.execute("ALTER TABLE marcus_reference ADD COLUMN label_vi_source TEXT DEFAULT NULL")
        print("[SCHEMA] Added label_vi_source column")
    conn.commit()


def backup_table(conn):
    try:
        conn.execute("DROP TABLE IF EXISTS marcus_reference_backup_t51f")
        conn.execute("CREATE TABLE marcus_reference_backup_t51f AS SELECT * FROM marcus_reference")
        conn.commit()
        n = conn.execute("SELECT COUNT(*) FROM marcus_reference_backup_t51f").fetchone()[0]
        print(f"[BACKUP] Backed up {n} rows → marcus_reference_backup_t51f")
    except Exception as e:
        print(f"[BACKUP] ERROR: {e}")
        raise


def load_char_map(conn):
    rows = conn.execute("SELECT char, hanviet FROM custom_hanviet_override").fetchall()
    # DB overrides take precedence over built-in; built-in fills gaps
    m = dict(BUILTIN_HV)
    m.update({char: hv for char, hv in rows})
    return m


def fetch_missing_from_hvdic(chars_needed, existing_map):
    missing = [c for c in chars_needed if c not in existing_map]
    if not missing:
        print(f"[HVDIC] All {len(chars_needed)} chars already in override table")
        return {}

    print(f"[HVDIC] Fetching {len(missing)} missing chars from hvdic.thivien.net ...")
    fetched = {}
    chunk_size = 200
    for i in range(0, len(missing), chunk_size):
        chunk = ''.join(missing[i:i + chunk_size])
        try:
            r = requests.post(HVDIC_URL, headers=HEADERS,
                              data={'mode': 'trans', 'lang': '1', 'input': chunk},
                              timeout=20)
            r.raise_for_status()
            data = r.json()
            for item in data.get('result', []):
                ch = item.get('i')
                outs = item.get('o') or []
                if ch and outs and outs[0].strip():
                    fetched[ch] = outs[0].strip()
            time.sleep(0.5)
        except Exception as e:
            print(f"  [HVDIC] chunk {i}-{i+chunk_size} FAILED: {e}")
            time.sleep(2)

    print(f"[HVDIC] Got {len(fetched)}/{len(missing)} readings")
    return fetched


def save_new_chars(conn, new_chars):
    if not new_chars:
        return
    rows = [(ch, hv, 'T51f_hvdic') for ch, hv in new_chars.items()]
    conn.executemany(
        "INSERT OR IGNORE INTO custom_hanviet_override (char, hanviet, added_by) VALUES (?,?,?)",
        rows
    )
    conn.commit()
    print(f"[OVERRIDE] Saved {len(rows)} new chars to custom_hanviet_override")


def convert_label(label, char_map):
    """Convert a Chinese label to Hán-Việt by looking up each character."""
    if not label:
        return None
    result_parts = []
    for ch in label:
        if HAN.match(ch):
            hv = char_map.get(ch)
            if hv:
                result_parts.append(hv.capitalize())
            else:
                result_parts.append(ch)  # keep original if no reading
        else:
            result_parts.append(ch)
    return ' '.join(result_parts)


def run_dry(conn, char_map):
    rows = conn.execute(
        "SELECT node_id, label, label_vi FROM marcus_reference WHERE label IS NOT NULL"
    ).fetchall()
    samples = []
    unchanged = 0
    for node_id, label, label_vi_old in rows[:50]:
        new_vi = convert_label(label, char_map)
        if new_vi == label_vi_old:
            unchanged += 1
            continue
        samples.append({'id': node_id, 'label': label, 'old_vi': label_vi_old, 'new_vi': new_vi})
    print(f"\n[DRY-RUN] Sample conversions (first 50 rows, {unchanged} already same):")
    for s in samples[:20]:
        print(f"  {s['label']} → {s['new_vi']}  (was: {s['old_vi']})")


def run_update(conn, char_map, dry_run=False):
    rows = conn.execute(
        "SELECT node_id, label, label_vi FROM marcus_reference WHERE label IS NOT NULL"
    ).fetchall()

    updates = []
    skipped = 0
    errors = []
    sample_before_after = []

    for node_id, label, label_vi_old in rows:
        try:
            new_vi = convert_label(label, char_map)
            if not new_vi:
                skipped += 1
                continue
            updates.append((new_vi, 0.5, 'auto_hanviet_T51f', node_id))
            if len(sample_before_after) < 30:
                sample_before_after.append({
                    'node_id': node_id, 'label': label,
                    'old_vi': label_vi_old, 'new_vi': new_vi
                })
        except Exception as e:
            errors.append({'node_id': node_id, 'label': label, 'error': str(e)})

    print(f"[UPDATE] {len(updates)} rows to update, {skipped} skipped, {len(errors)} errors")

    if not dry_run:
        conn.executemany(
            "UPDATE marcus_reference SET label_vi=?, label_vi_confidence=?, label_vi_source=? WHERE node_id=?",
            updates
        )
        conn.commit()
        print(f"[UPDATE] Committed {len(updates)} rows")

    log = {
        'run_at': datetime.now().isoformat(),
        'dry_run': dry_run,
        'total_rows': len(rows),
        'updated': len(updates),
        'skipped': skipped,
        'errors': errors[:20],
        'sample': sample_before_after
    }
    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[LOG] Written to {LOG_PATH}")
    return len(updates)


def run_revert(conn):
    try:
        conn.execute("SELECT COUNT(*) FROM marcus_reference_backup_t51f").fetchone()
    except Exception:
        print("[REVERT] ERROR: backup table marcus_reference_backup_t51f not found. Cannot revert.")
        return

    n_backup = conn.execute("SELECT COUNT(*) FROM marcus_reference_backup_t51f").fetchone()[0]
    print(f"[REVERT] Restoring {n_backup} rows from backup ...")
    conn.execute("DELETE FROM marcus_reference")
    conn.execute("INSERT INTO marcus_reference SELECT * FROM marcus_reference_backup_t51f")
    conn.commit()
    print("[REVERT] Done. marcus_reference restored.")


def main():
    parser = argparse.ArgumentParser(description='T51f: Auto Hán-Việt for marcus_reference.label_vi')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing to DB')
    parser.add_argument('--revert', action='store_true', help='Restore from backup table')
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    if args.revert:
        run_revert(conn)
        conn.close()
        return

    print("=== T51f: Auto Hán-Việt marcus_reference.label_vi ===")
    print(f"DB: {DB_PATH}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'WRITE'}\n")

    add_columns_if_missing(conn)

    if not args.dry_run:
        backup_table(conn)

    # Build char map: DB override + hvdic for missing chars
    existing_map = load_char_map(conn)
    print(f"[MAP] Loaded {len(existing_map)} chars from custom_hanviet_override")

    labels = conn.execute("SELECT label FROM marcus_reference WHERE label IS NOT NULL").fetchall()
    all_chars = set()
    for (label,) in labels:
        for ch in (label or ''):
            if HAN.match(ch):
                all_chars.add(ch)
    print(f"[MAP] {len(all_chars)} unique CJK chars in marcus_reference.label")

    if args.dry_run:
        new_chars = {}
        missing_count = sum(1 for c in all_chars if c not in existing_map)
        print(f"[MAP] DRY-RUN: skipping hvdic fetch ({missing_count} chars would be fetched)")
    else:
        new_chars = fetch_missing_from_hvdic(all_chars, existing_map)
        save_new_chars(conn, new_chars)

    full_map = {**existing_map, **new_chars}
    coverage = sum(1 for c in all_chars if c in full_map)
    print(f"[MAP] Coverage: {coverage}/{len(all_chars)} chars ({100*coverage//len(all_chars)}%)")

    if args.dry_run:
        run_dry(conn, full_map)
    else:
        n = run_update(conn, full_map)
        print(f"\n[DONE] Updated {n} rows in marcus_reference.label_vi (confidence=0.5)")

    conn.close()


if __name__ == '__main__':
    main()
