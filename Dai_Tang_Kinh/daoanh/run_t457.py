#!/usr/bin/env python3
import sys
sys.argv = ['t457_extract_bio_nexus.py', 
             '--src', r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\biographies-master',
             '--out', r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\data\dila_import\biographies.2024-01\nexus_src_test',
             '--book', 'Mingsengzhuanchao']
exec(open('scripts/t457_extract_bio_nexus.py').read())