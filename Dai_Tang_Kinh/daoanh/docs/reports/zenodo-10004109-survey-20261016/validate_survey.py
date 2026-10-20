import collections,csv,hashlib,json,pathlib,re,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent;EX=ROOT/'extracted';OUT=ROOT/'analysis'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p,alg='sha256'):
 h=hashlib.new(alg)
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
checks=[]
def check(name,condition,detail=None):
 checks.append({'check':name,'pass':bool(condition),'detail':detail})
 if not condition:raise RuntimeError(name)
meta=read(ROOT/'record-metadata.json');receipt=read(ROOT/'download-receipt.json');inv=read(ROOT/'archive-inventory.json');ext=read(ROOT/'extraction-manifest.json');comparison=read(OUT/'source-comparison.json')
check('record_id',meta['id']==10004109)
check('advertised_download_size',receipt['downloads'][0]['bytes']==meta['files'][0]['size'])
check('advertised_md5',sha(ROOT/receipt['downloads'][0]['local_path'],'md5')==meta['files'][0]['checksum'].split(':',1)[1])
check('archive_sha256',sha(ROOT/receipt['downloads'][0]['local_path'])==receipt['downloads'][0]['sha256']==inv['sha256']==ext['archive_sha256'])
check('zip_safety_no_errors',not inv['safety_errors'])
check('all_extracted_files_accounted',sum(p.is_file() for p in EX.rglob('*'))==len(ext['files'])==inv['file_count'])
check('all_extracted_hashes_match',all(sha(ROOT/x['path'])==x['sha256'] for x in ext['files']),{'files':len(ext['files'])})
with (EX/'vancutsem_laurent/05-ZTJ_nodes_simplified.csv').open(encoding='utf-8-sig',newline='') as f:nodes=list(csv.DictReader(f,delimiter=';'))
with (EX/'vancutsem_laurent/05-ZTJ_edges_ZTJmain.csv').open(encoding='utf-8-sig',newline='') as f:edges=list(csv.DictReader(f))
# Only these known tiny tables are retained here (<300 rows each); XML uses iterparse.
check('csv_node_ids_unique',len({x['ID'] for x in nodes})==len(nodes),len(nodes))
check('reported_csv_counts',len(nodes)==comparison['csv_node_count'] and len(edges)==comparison['csv_edges'])
check('csv_no_dangling',not comparison['csv_dangling_endpoints'])
check('gexf_no_dangling',not comparison['gexf_dangling_endpoints'])
check('csv_no_self_edge',comparison['csv_self_edges']==0)
check('gexf_no_self_edge',comparison['gexf_self_edges']==0)
check('csv_declared_undirected',all(x['Type']=='Undirected' for x in edges))
check('gexf_declared_undirected',comparison['gexf_graph_attributes'][0]['defaultedgetype']=='undirected')
for kind,rows in [('nodes',nodes),('edges',edges)]:
 sample=read(OUT/f'sample-{kind}-10.json')
 check(kind+'_sample_exact_first10',len(sample['records'])==10 and sample['records']==rows[:10])
 check(kind+'_sample_unaccepted',sample['semantic_status'].startswith('unmapped source_asserted'))
licenses=sorted(EX.glob('*/02-license.txt'));check('seven_identical_package_licenses',len(licenses)==7 and len({sha(p) for p in licenses})==1)
xml_qualifiers=[]
for p in sorted((EX/'vancutsem_laurent').glob('03-*.xml')):
 attrs=collections.defaultdict(collections.Counter);groups=collections.Counter();lic=[];count=collections.Counter();stack=[]
 for ev,e in ET.iterparse(p,events=('start','end')):
  if ev=='start':stack.append(e);continue
  tag=e.tag.rsplit('}',1)[-1];count[tag]+=1
  for k,v in e.attrib.items():
   if k in {'cert','ana','type','role','subtype'}:attrs[tag+'@'+k][v]+=1
  if tag=='linkGrp':groups[e.attrib.get('cert','<none>')]+=1
  if tag=='licence':lic.append(''.join(e.itertext()).strip())
  if len(stack)>1:stack[-2].remove(e)
  e.clear();stack.pop()
 check(p.name+'_embedded_tei_license',len(lic)==1 and 'CC BY-NC-SA 4.0' in lic[0])
 xml_qualifiers.append({'path':p.relative_to(EX).as_posix(),'attributes':{k:dict(v) for k,v in attrs.items()},'linkGrp_cert_counts':dict(groups),'element_counts':dict(count),'licence':lic})
report={'status':'PASS','checks':checks,'check_count':len(checks),'definitions':'Source-structure/integrity validation only; not historical, identity, lineage, license clearance or production acceptance','source_shape_observations':{'node_label_duplicate_values':{k:v for k,v in collections.Counter(x['Label'] for x in nodes).items() if v>1},'source_generation_values':dict(collections.Counter(x['No. (Generations)'] for x in nodes)),'tei_qualifiers':xml_qualifiers},'production_db_ttl_reads_or_writes':'none; explicit paths confined to survey root'}
with (OUT/'validation.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':'PASS','checks':len(checks),'label_duplicates':report['source_shape_observations']['node_label_duplicate_values'],'tei_qualifiers':[{'path':x['path'],'linkGrp_cert_counts':x['linkGrp_cert_counts']} for x in xml_qualifiers]},ensure_ascii=False,indent=2))
