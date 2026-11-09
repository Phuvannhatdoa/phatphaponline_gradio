p = r'E:\Backup 2025\QuaiTieuTu\Anan Son\phatphaponline_gradio\truyenthua\visjs-app\Dai_Tang_Kinh\daoanh\core.py'
content = open(p, encoding='utf-8', errors='replace').read()
for fn in ['_get_person_suggest_cache', '_get_work_suggest_cache', '_get_place_suggest_cache', '_get_person_with_contribution_cache']:
    i = content.find('def ' + fn)
    j = content.find('def _get_work_suggest_cache')
    print(fn + ': found=' + str(i >= 0) + ' at=' + str(i))