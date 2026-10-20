import urllib.request
from pathlib import Path
request = urllib.request.Request('https://vjol.info.vn/index.php/rsr/article/download/46697/37875/', headers={'User-Agent':'Mozilla/5.0'})
try:
    with urllib.request.urlopen(request,timeout=20) as response:
        blob=response.read()
    target=Path(__file__).parent/'Bao-Tu-VJOL-2017.pdf'
    if not blob.startswith(b'%PDF'):
        raise ValueError('Response is not PDF')
    target.write_bytes(blob)
    print('saved PDF',len(blob))
except Exception as error:
    print(type(error).__name__,str(error))
    raise SystemExit(1)
