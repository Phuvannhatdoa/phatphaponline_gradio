import json,sys,hashlib,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
TEI='{http://www.tei-c.org/ns/1.0}'
XML='{http://www.w3.org/XML/1998/namespace}'
archive=ROOT/'data/backups/T215-tri-tai-sync-20261002/authority_person.2026-09.zip'
source_xml=ROOT/'data/dila_import/Authority-Databases/authority_person/Buddhist_Studies_Person_Authority.xml'
terms=['\u660e\u6d77','\u660e\u6d77\u6cd5\u5bf6','\u660e\u6d77\u6cd5\u5b9d','\u6cd5\u5bf6','\u5f97\u667a','\u5fb7\u667a','\u6881\u4e16\u6069','\u795d\u8056']
def digest(stream):
    h=hashlib.sha256()
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
    return h.hexdigest()
def authority_scan(stream,label):
    count=0;hits=[];compound=[];stack=[]
    for event,node in ET.iterparse(stream,events=('start','end')):
        if event=='start':stack.append(node);continue
        if node.tag==TEI+'person':
            count+=1
            names=[''.join(n.itertext()).strip() for n in node.findall('.//'+TEI+'persName')]
            notes=[{'type':n.get('type'),'text':''.join(n.itertext()).strip()} for n in node.findall(TEI+'note')]
            name_hits=[q for q in terms if any(q in n for n in names)]
            raw=ET.tostring(node,encoding='unicode')
            if name_hits:hits.append({'id':node.get(XML+'id'),'names':names,'name_hits':name_hits,'notes':notes,'sha256':hashlib.sha256(raw.encode()).hexdigest()})
            keys=['\u660e\u6d77\u6cd5\u5bf6','\u660e\u6d77\u6cd5\u5b9d','\u6881\u4e16\u6069','\u5831\u8cc7\u5bfa']
            if any(q in ''.join(node.itertext()) for q in keys):compound.append({'id':node.get(XML+'id'),'terms':[q for q in keys if q in ''.join(node.itertext())]})
            if len(stack)>1:stack[-2].remove(node)
        stack.pop()
    return {'source':label,'records_scanned':count,'name_candidates':hits,'compound_text_hits':compound}
out={'authority':[]}
with zipfile.ZipFile(archive) as z:
    entry=next(n for n in z.namelist() if n.endswith('Person_Authority.xml'))
    with z.open(entry) as f:result=authority_scan(f,str(archive.relative_to(ROOT))+'!'+entry)
    with z.open(entry) as f:result['artifact_sha256']=digest(f)
    out['authority'].append(result)
with source_xml.open('rb') as f:result=authority_scan(f,str(source_xml.relative_to(ROOT)))
with source_xml.open('rb') as f:result['artifact_sha256']=digest(f)
out['authority'].append(result)
cbeta=ROOT/'data/cbeta/xml-p5-full'
cterms=['\u660e\u6d77\u6cd5\u5bf6','\u660e\u6d77\u6cd5\u5b9d','\u6881\u4e16\u6069','\u5831\u8cc7\u5bfa','\u62a5\u8d44\u5bfa','\u660e\u6d77','\u795d\u8056\u5bfa']
summary={q:{'literal_line_hits':0,'samples':[]} for q in cterms}
files=0;errors=[]
for f in cbeta.rglob('*.xml'):
    files+=1
    try:
        with f.open('r',encoding='utf-8') as st:
            for lineno,line in enumerate(st,1):
                for q in cterms:
                    if q in line:
                        v=summary[q];v['literal_line_hits']+=1
                        if len(v['samples'])<12:
                            at=line.find(q)
                            v['samples'].append({'file':str(f.relative_to(cbeta)),'line':lineno,'context':line[max(0,at-100):at+len(q)+180].strip()})
    except Exception as e:errors.append({'file':str(f.relative_to(cbeta)),'error':str(e)})
out['cbeta']={'source':str(cbeta.relative_to(ROOT)),'xml_files_scanned':files,'errors':errors,'terms':summary,'limitations':'Literal terms on individual XML lines, no normalization of inline tags, gaiji or alternative names; this does not prove absence from all CBETA releases.'}
print(json.dumps(out,ensure_ascii=False,indent=2))
