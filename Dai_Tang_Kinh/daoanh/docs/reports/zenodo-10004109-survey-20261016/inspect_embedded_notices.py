import io,json,pathlib,re,struct,zipfile,zlib
ROOT=pathlib.Path(__file__).resolve().parent;EX=ROOT/'extracted';OUT=ROOT/'analysis'
PAT=re.compile(r'copyright|all rights reserved|creative commons|\bcc[- ]by\b|licen[cs]e|permission to|public domain|©',re.I)
results=[];inventory=[];skips=[]
def scan_stream(stream,source):
    matches=[];carry='';line_no=1
    text=io.TextIOWrapper(stream,encoding='utf-8-sig',errors='strict')
    while True:
        chunk=text.readline(64*1024)
        if not chunk:break
        if PAT.search(carry+chunk):matches.append({'line':line_no,'text':(carry+chunk).strip()[:1500]})
        if chunk.endswith('\n'):line_no+=1;carry=''
        else:carry=chunk[-128:]
    if matches:results.append({'source':source,'matches':matches})
for p in sorted(EX.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(EX).as_posix()
    if p.suffix.lower() in {'.gephi','.xlsx'}:
        with zipfile.ZipFile(p) as z:
            infos=z.infolist()
            if len(infos)>20000 or sum(x.file_size for x in infos)>512*1024*1024:raise RuntimeError('Nested archive size bound')
            inventory.append({'path':rel,'members':[{'path':x.filename,'bytes':x.file_size} for x in infos]})
            for info in infos:
                if info.is_dir():continue
                if info.file_size>128*1024*1024:raise RuntimeError('Nested member size bound')
                if pathlib.PurePosixPath(info.filename).suffix.lower() not in {'.xml','.txt','.md','.json','.html','.rdf','.rels'}:continue
                # Worksheet and string text already screened as decoded cell values too.
                try:
                    with z.open(info) as stream:scan_stream(stream,rel+'!'+info.filename)
                except UnicodeError:skips.append({'source':rel+'!'+info.filename,'reason':'non-UTF8 text'})
    elif p.suffix.lower()=='.png':
        with p.open('rb') as f:
            if f.read(8)!=b'\x89PNG\r\n\x1a\n':raise RuntimeError('Bad PNG signature')
            chunks=[]
            while True:
                head=f.read(8)
                if not head:break
                if len(head)!=8:raise RuntimeError('Truncated PNG')
                n,kind=struct.unpack('>I4s',head)
                if kind in {b'tEXt',b'iTXt',b'zTXt'}:
                    if n>1024*1024:skips.append({'source':rel,'reason':'PNG textual chunk >1MiB'});f.seek(n+4,1);continue
                    data=f.read(n);f.read(4);chunks.append({'type':kind.decode(),'bytes':n})
                    if kind==b'zTXt':
                        keyword,body=data.split(b'\x00',1)
                        dec=zlib.decompressobj();text=(keyword+b' '+dec.decompress(body[1:],1024*1024)).decode('latin-1')
                    else:text=data.decode('utf-8' if kind==b'iTXt' else 'latin-1',errors='replace')
                    if PAT.search(text):results.append({'source':rel,'chunk':kind.decode(),'text':text[:2000]})
                else:f.seek(n+4,1)
                if kind==b'IEND':break
            if chunks:inventory.append({'path':rel,'text_chunks':chunks})
report={'method':'Read nested Gephi/XLSX XML/text members in bounded chunks; PNG text metadata only; no nested extraction, execution or OCR','notices':results,'containers':inventory,'skips':skips,'limits':'Notices drawn into image pixels or undocumented binary fields are not OCR/decoded. No rights clearance inferred from absence of text.'}
with (OUT/'embedded-rights-inspection.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'notices':results,'container_count':len(inventory),'skips':skips},ensure_ascii=False,indent=2))
