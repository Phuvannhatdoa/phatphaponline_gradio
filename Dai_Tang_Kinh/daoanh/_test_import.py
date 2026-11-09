import sys
sys.path.insert(0, r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh')
from app import app
print('App imported successfully')
print('Routes:', [rule.rule for rule in app.url_map.routes_if_present])