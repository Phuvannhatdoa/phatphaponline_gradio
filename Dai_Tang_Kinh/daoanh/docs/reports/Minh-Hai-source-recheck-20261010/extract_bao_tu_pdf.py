import pdfplumber
from pathlib import Path
import json
base=Path(__file__).parent
with pdfplumber.open(base/'Bao-Tu-VJOL-2017.pdf') as document:
    selected=[0,7,8,9,10,11,12,13,14]
    result={'pages':len(document.pages),'selected_pages':{str(i):document.pages[i].extract_text() for i in selected if i<len(document.pages)}}
(base/'bao-tu-selected-pages.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PDF pages:',result['pages'])
for i,text in result['selected_pages'].items():
    print('PDF index',i,'\n',text[:600] if i=='0' else text[:200])
