import collections,csv,hashlib,json,pathlib,re,struct,zipfile,zlib,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent;EX=ROOT/'extracted';OUT=ROOT/'analysis';T='{http://www.tei-c.org/ns/1.0}'
PAT=re.compile(r'copyright|all rights reserved|creative commons|\bcc[- ]by\b|licen[cs]e|permission to|public domain|©',re.I)
def loc(t):return t.rsplit('}',1)[-1]
def write(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def safe_members(z):
    infos=z.infolist()
    if len(infos)>20000 or sum(x.file_size for x in infos)>512*1024*1024:raise RuntimeError('Nested container bound exceeded')
    for x in infos:
        pp=pathlib.PurePosixPath(x.filename)
        if pp.is_absolute() or '..' in pp.parts or '\\' in x.filename or ':' in x.filename or x.flag_bits&1:raise RuntimeError('Unsafe nested container entry')
        if x.file_size>128*1024*1024:raise RuntimeError('Nested member size bound exceeded')
    return infos
def iter_xml(stream):
    stack=[]
    for event,e in ET.iterparse(stream,events=('start','end')):
        if event=='start':stack.append(e);continue
        yield e,stack
        stack.pop()
def workbook(p):
    with zipfile.ZipFile(p) as z:
        infos=safe_members(z);strings=[];notices=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            with z.open('xl/sharedStrings.xml') as source:
                for e,stack in iter_xml(source):
                    if loc(e.tag)=='si':
                        value=''.join(x.text or '' for x in e.iter() if loc(x.tag)=='t');strings.append(value)
                        if len(strings)>100000:raise RuntimeError('Shared-string bound exceeded')
                        if PAT.search(value):notices.append({'member':'xl/sharedStrings.xml','string_index':len(strings)-1,'text':value[:2000]})
                        if len(stack)>1:stack[-2].remove(e)
                        e.clear()
        reltree=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'));rels={x.attrib['Id']:x.attrib['Target'] for x in reltree}
        wbtree=ET.fromstring(z.read('xl/workbook.xml'));sheets=[]
        for sheet in wbtree.iter():
            if loc(sheet.tag)!='sheet':continue
            target=rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            member=target.lstrip('/') if target.startswith('/') else str(pathlib.PurePosixPath('xl')/target)
            rows=0;nonempty=0;cells=0;formulas=0;first=[];dimension=None
            with z.open(member) as source:
                for e,stack in iter_xml(source):
                    tag=loc(e.tag)
                    if tag=='dimension':dimension=e.attrib.get('ref')
                    if tag!='row':continue
                    rows+=1;values={}
                    for c in e:
                        if loc(c.tag)!='c':continue
                        cells+=1;value='';formula=None
                        for child in c:
                            if loc(child.tag)=='v':value=child.text or ''
                            if loc(child.tag)=='f':formula=child.text or '';formulas+=1
                            if loc(child.tag)=='is':value=''.join(x.text or '' for x in child.iter() if loc(x.tag)=='t')
                        if c.attrib.get('t')=='s':value=strings[int(value)] if value else ''
                        if value!='' or formula is not None:values[c.attrib.get('r','?')]={'value':value,**({'formula':formula} if formula is not None else {})}
                        if PAT.search(value):notices.append({'member':member,'cell':c.attrib.get('r'),'text':value[:2000]})
                    if values:nonempty+=1
                    if len(first)<12:first.append({'source_row':e.attrib.get('r'),'cells':values})
                    if len(stack)>1:stack[-2].remove(e)
                    e.clear()
            sheets.append({'name':sheet.attrib.get('name'),'member':member,'declared_dimension':dimension,'row_elements':rows,'nonempty_rows':nonempty,'cell_elements':cells,'formula_count':formulas,'first_rows':first})
        return {'path':p.relative_to(EX).as_posix(),'sheets':sheets,'notices':notices,'shared_strings_count':len(strings),'macro_members':[x.filename for x in infos if 'vba' in x.filename.lower()]}
books=[workbook(p) for p in sorted(EX.rglob('*.xlsx'))]
write('workbook-analysis.json',{'method':'stdlib ZIP/XML read-only; cached stored values only; no macros/formulas evaluated; worksheets iterated one row at a time','workbooks':books})
teis=[]
for p in sorted((EX/'vancutsem_laurent').glob('*.xml')):
    counts=collections.Counter();types=collections.defaultdict(collections.Counter);samples=collections.defaultdict(list)
    with p.open('rb') as source:
        for e,stack in iter_xml(source):
            tag=loc(e.tag);counts[tag]+=1
            if tag in {'linkGrp','link','relation','person','personGrp','persName','name','ref','div','licence','availability'}:
                if e.attrib.get('type'):types[tag][e.attrib['type']]+=1
                if len(samples[tag])<5:samples[tag].append({'attributes':dict(e.attrib),'text':''.join(e.itertext()).strip()[:1000]})
            if len(stack)>1:stack[-2].remove(e)
            e.clear()
    teis.append({'path':p.relative_to(EX).as_posix(),'namespace':T[1:-1],'element_counts':dict(counts),'type_counts':dict(types),'samples':dict(samples),'interpretation':'TEI named mentions/link groups are source markup, not accepted person/teacher mappings'})
write('tei-analysis.json',{'files':teis})
# Compare CSV and GEXF structures at source IDs only. Bound is the actual 260-node dataset.
nodes={};edges=[]
with (EX/'vancutsem_laurent/05-ZTJ_nodes_simplified.csv').open(encoding='utf-8-sig',newline='') as f:
    for row in csv.DictReader(f,delimiter=';'):
        if len(nodes)>=100000:raise RuntimeError('Source-ID comparison bound exceeded')
        if row['ID'] in nodes:raise RuntimeError('Duplicate CSV node ID')
        nodes[row['ID']]=row
with (EX/'vancutsem_laurent/05-ZTJ_edges_ZTJmain.csv').open(encoding='utf-8-sig',newline='') as f:
    for row in csv.DictReader(f):edges.append(row)
gnodes={};gedges=[];graphattrs=[]
with (EX/'vancutsem_laurent/07-ztjLinkGrps.gexf').open('rb') as source:
    for e,stack in iter_xml(source):
        tag=loc(e.tag)
        if tag=='graph':graphattrs.append(dict(e.attrib))
        if tag=='node':gnodes[e.attrib['id']]=dict(e.attrib)
        if tag=='edge':gedges.append(dict(e.attrib))
        if tag in {'node','edge'}:
            if len(stack)>1:stack[-2].remove(e)
            e.clear()
cpairs=collections.Counter((r['Source'],r['Target']) for r in edges);gpairs=collections.Counter((r['source'],r['target']) for r in gedges)
comparison={'csv_node_count':len(nodes),'gexf_node_count':len(gnodes),'csv_only_node_ids':sorted(set(nodes)-set(gnodes)),'gexf_only_node_ids':sorted(set(gnodes)-set(nodes)),'csv_edges':len(edges),'gexf_edges':len(gedges),'csv_type_counts':dict(collections.Counter(r['Type'] for r in edges)),'gexf_edge_type_counts':dict(collections.Counter(r.get('type','<graph default>') for r in gedges)),'gexf_graph_attributes':graphattrs,'csv_only_pairs':[{'source':s,'target':t,'count':n} for (s,t),n in (cpairs-gpairs).items()],'gexf_only_pairs':[{'source':s,'target':t,'count':n} for (s,t),n in (gpairs-cpairs).items()],'csv_dangling_endpoints':sorted({r[k] for r in edges for k in ('Source','Target') if r[k] not in nodes}),'gexf_dangling_endpoints':sorted({r[k] for r in gedges for k in ('source','target') if r[k] not in gnodes}),'csv_self_edges':sum(r['Source']==r['Target'] for r in edges),'gexf_self_edges':sum(r['source']==r['target'] for r in gedges),'csv_id_shape_counts':dict(collections.Counter('DILA-shaped A+6digits (unverified)' if re.fullmatch(r'A\d{6}',x) else 'other package ID' for x in nodes))}
write('source-comparison.json',comparison)
print(json.dumps({'workbooks':[{'path':b['path'],'sheets':[{k:v for k,v in s.items() if k!='first_rows'} for s in b['sheets']],'notices':b['notices']} for b in books],'tei_counts':[{'path':x['path'],'elements':{k:v for k,v in x['element_counts'].items() if k in {'person','personGrp','persName','name','link','linkGrp','relation','ref','licence'}}} for x in teis],'comparison':comparison},ensure_ascii=False,indent=2))
