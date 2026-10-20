-- Revert T05 TTL ETL phonetic corrections
-- Pass 1 (2026-09-01/02): 2 rows
UPDATE people SET name_vi='Bà Tua Mật' WHERE id='A008800' AND name_zh='婆須蜜';
UPDATE people SET name_vi='Đồ Dạ Đa'  WHERE id='A008793' AND name_zh='闍夜多';

-- Pass 3 (2026-09-02): 13 person + 31 place corrections
-- PERSONS
UPDATE people SET name_vi='Trưởng Tỳ Khoảng' WHERE id='A020021' AND name_zh='長髭曠';
UPDATE people SET name_vi='Khánh Hỉ'         WHERE id='A035900' AND name_zh='慶喜';
UPDATE people SET name_vi='Bà Tu Bàn Đầu'    WHERE id='A005159' AND name_zh='婆修盤頭';
UPDATE people SET name_vi='Đạo Vỗ'           WHERE id='A005522' AND name_zh='道撫';
UPDATE people SET name_vi='Trưởng Khánh'     WHERE id='A003890' AND name_zh='長慶';
UPDATE people SET name_vi='Chí Bản'          WHERE id='A010452' AND name_zh='志本';
UPDATE people SET name_vi='Trưởng An'        WHERE id='A010232' AND name_zh='長安';
UPDATE people SET name_vi='Thần Sách'        WHERE id='A022589' AND name_zh='神策';
UPDATE people SET name_vi='Đàm Hổi'          WHERE id='A049025' AND name_zh='曇晦';
UPDATE people SET name_vi='Đại Quan'         WHERE id='A008816' AND name_zh='大觀';
UPDATE people SET name_vi='Vô Trứ'           WHERE id='A001411' AND name_zh='無著';
UPDATE people SET name_vi='Đặng Tí Thường'   WHERE id='A022026' AND name_zh='鄧子常';
UPDATE people SET name_vi='Tí Văn'           WHERE id='A014354' AND name_zh='子文';
-- PLACES (revert name_vi; confidence và source đã thay đổi)
UPDATE namevi_map_places SET name_vi='Rặc Dương'     WHERE dila_id='PL023602' AND name_zh='洛陽';
UPDATE namevi_map_places SET name_vi='Phúc Châu'     WHERE dila_id='PL006550' AND name_zh='福州';
UPDATE namevi_map_places SET name_vi='Suyền Châu'    WHERE dila_id='PL018626' AND name_zh='洪州';
UPDATE namevi_map_places SET name_vi='Vấn Héo'       WHERE dila_id='PL021211' AND name_zh='汶水';
UPDATE namevi_map_places SET name_vi='Trưởng Khánh'  WHERE dila_id='PL007472' AND name_zh='長慶';
UPDATE namevi_map_places SET name_vi='Triệu Quận'    WHERE dila_id='PL001049' AND name_zh='趙郡';
UPDATE namevi_map_places SET name_vi='Bàn Nhược Viện' WHERE dila_id='PL014888' AND name_zh='般若院';
UPDATE namevi_map_places SET name_vi='Hà Nam Tỉnh'   WHERE dila_id='PL023032' AND name_zh='河南省';
UPDATE namevi_map_places SET name_vi='Dang Lăng'     WHERE dila_id='PL003969' AND name_zh='延陵';
UPDATE namevi_map_places SET name_vi='Nhuần Châu'    WHERE dila_id='PL001344' AND name_zh='潤州';
UPDATE namevi_map_places SET name_vi='Trưởng Thọ Tự' WHERE dila_id='PL008801' AND name_zh='長壽寺';
UPDATE namevi_map_places SET name_vi='Dang Tộ Tự'    WHERE dila_id='PL005179' AND name_zh='延祚寺';
UPDATE namevi_map_places SET name_vi='Tịnh Thổ Viện' WHERE dila_id='PL000313' AND name_zh='淨土院';
UPDATE namevi_map_places SET name_vi='Hồ Nam Tỉnh'   WHERE dila_id='PL028609' AND name_zh='湖南省';
UPDATE namevi_map_places SET name_vi='Thái Hoà'      WHERE dila_id='PL006084' AND name_zh='太和';
UPDATE namevi_map_places SET name_vi='Đại Dữu Lĩnh'  WHERE dila_id='PL030691' AND name_zh='大庾嶺';
UPDATE namevi_map_places SET name_vi='Thượng Rặc'    WHERE dila_id='PL026653' AND name_zh='上洛';
UPDATE namevi_map_places SET name_vi='Kỳ Châu'       WHERE dila_id='PL028082' AND name_zh='蘄州';
UPDATE namevi_map_places SET name_vi='Thiểu Lâm Tự'  WHERE dila_id='PL023255' AND name_zh='少林寺';
UPDATE namevi_map_places SET name_vi='Trưởng Khê'    WHERE dila_id='PL018492' AND name_zh='長溪';
UPDATE namevi_map_places SET name_vi='Lư Sơn'        WHERE dila_id='PL018775' AND name_zh='廬山';
UPDATE namevi_map_places SET name_vi='Phải Quận'     WHERE dila_id='PL015347' AND name_zh='沛郡';
UPDATE namevi_map_places SET name_vi='Chờ Châu'      WHERE dila_id='PL009511' AND name_zh='徐州';
UPDATE namevi_map_places SET name_vi='Tuệ Giác'      WHERE dila_id='PL011423' AND name_zh='慧覺';
UPDATE namevi_map_places SET name_vi='Hoá Cảm Tự'    WHERE dila_id='PL042560' AND name_zh='化感寺';
UPDATE namevi_map_places SET name_vi='Trưởng An'     WHERE dila_id='PL012849' AND name_zh='長安';
UPDATE namevi_map_places SET name_vi='Hành Châu'     WHERE dila_id='PL028907' AND name_zh='衡州';
UPDATE namevi_map_places SET name_vi='Đạo Ngo Sơn'   WHERE dila_id='PL028631' AND name_zh='道吾山';
UPDATE namevi_map_places SET name_vi='Hưng Hoá Tự'   WHERE dila_id='PL000940' AND name_zh='興化寺';
UPDATE namevi_map_places SET name_vi='Đằm Châu'      WHERE dila_id='PL007832' AND name_zh='潭州';
UPDATE namevi_map_places SET name_vi='Chính Hoà'     WHERE dila_id='PL017474' AND name_zh='政和';
