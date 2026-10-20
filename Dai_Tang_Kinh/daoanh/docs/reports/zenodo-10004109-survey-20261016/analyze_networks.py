import collections,csv,hashlib,io,json,pathlib,re,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
EXTRACTED=ROOT/'extracted'; OUT=ROOT/'analysis'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()
def local(t):return t.rsplit('}',1)[-1]
def exclusive_json(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def xml_analysis(p):
    # Reject entity/DTD declarations without loading the XML document.
    carry=b''
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):
            scan=carry+c
            if b'<!DOCTYPE' in scan.upper() or b'<!ENTITY' in scan.upper():raise RuntimeError('DTD/entity XML refused')
            carry=scan[-16:]
    counts=collections.Counter();samples={'nodes':[],'edges':[]};attributes=[];graph_attrs=[];stack=[];root_tag=None
    for event,elem in ET.iterparse(p,events=('start','end')):
        tag=local(elem.tag)
        if event=='start':
            if root_tag is None:root_tag=elem.tag
            stack.append(elem)
            if tag=='graph':graph_attrs.append(dict(elem.attrib))
            continue
        if tag in {'node','edge'}:
            kind='nodes' if tag=='node' else 'edges';counts[kind]+=1
            if len(samples[kind])<10:
                row={'attributes':dict(elem.attrib),'data':[{'tag':child.tag,'attributes':dict(child.attrib),'text':(child.text or '').strip()} for child in elem.iter() if child is not elem]}
                samples[kind].append(row)
            if len(stack)>1:stack[-2].remove(elem)
            elem.clear()
        elif tag in {'attribute','key'}:
            attributes.append({'tag':elem.tag,'attributes':dict(elem.attrib),'text':(elem.text or '').strip()})
        if tag not in {'node','edge'} and not any(local(parent.tag) in {'node','edge'} for parent in stack[:-1]):
            if len(stack)>1:stack[-2].remove(elem)
            elem.clear()
        stack.pop()
    return {'format':'XML '+local(root_tag),'root_namespace':root_tag,'counts':dict(counts),'graph_attributes':graph_attrs,'attribute_definitions':attributes,'sample_selection':'First up to 10 node/edge elements in document order; structural source IDs, no identity mapping','samples':samples}
def csv_analysis(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        head=f.read(16384);f.seek(0)
        dialect=csv.Sniffer().sniff(head,delimiters=',;\t|')
        reader=csv.DictReader(f,dialect=dialect);fields=reader.fieldnames or [];rows=0;sample=[];bad=0
        for row in reader:
            rows+=1
            if None in row:bad+=1
            if len(sample)<10:sample.append(row)
    normalized={x.strip().lower() for x in fields}
    role='edges' if {'source','target'}<=normalized else ('nodes' if ('id' in normalized or 'label' in normalized) else 'table')
    return {'format':'CSV','delimiter':dialect.delimiter,'fields':fields,'record_count':rows,'ragged_records':bad,'structural_role':role,'sample_selection':'First up to 10 CSV records in file order; role by explicit Id/Label or Source/Target headers only','samples':{role:sample}}
files=[]
for p in sorted(EXTRACTED.rglob('*')):
    if not p.is_file() or not re.search(r'van.?cutsem|cutsem|zutang|ztj',p.relative_to(EXTRACTED).as_posix(),re.I):continue
    rel=p.relative_to(EXTRACTED).as_posix();row={'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)}
    if '__MACOSX' in p.parts or p.name.startswith('._'):row['analysis']={'format':'macOS resource fork','status':'not graph data'}
    elif p.suffix.lower() in {'.gexf','.graphml','.xml'}:row['analysis']=xml_analysis(p)
    elif p.suffix.lower()=='.csv':row['analysis']=csv_analysis(p)
    else:row['analysis']={'format':p.suffix.lower(),'status':'requires format-specific inspection'}
    files.append(row)
    print(json.dumps({k:v for k,v in row.items() if k!='analysis'}|{'analysis':{k:v for k,v in row['analysis'].items() if k!='samples'}},ensure_ascii=False),flush=True)
exclusive_json(OUT/'network-analysis.json',{'record_id':10004109,'definition_version':'survey-1','semantic_status':'source_asserted survey only; no accepted identity/lineage mappings','files':files})
for index,row in enumerate(files):
    for kind,sample in row['analysis'].get('samples',{}).items():
        exclusive_json(OUT/(f'{index:02d}-'+kind+'-sample.json'),{'record_id':10004109,'source_path':row['path'],'source_sha256':row['sha256'],'source_namespace':'package-local only','semantic_status':'unmapped source_asserted','selection':row['analysis']['sample_selection'],'records':sample})
