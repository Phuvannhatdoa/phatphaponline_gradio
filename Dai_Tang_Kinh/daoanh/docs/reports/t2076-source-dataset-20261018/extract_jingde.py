import argparse,collections,csv,hashlib,io,json,pathlib,re,sys,xml.parsers.expat as expat
ROOT=pathlib.Path(__file__).resolve().parent
PIN='a3942d421828f6372c1853f58daeb19299e4c91ab701a711167b3610ffaf507b'
TRIGGER=re.compile('法嗣|弟子|傳法|嗣');HAN=r'[\u3400-\u9fff]';TITLE=r'(?:禪師|和尚|大師|法師|尊者|佛)';NAME=HAN+r'{2,14}'+TITLE
RULES=[('heir_verb','dharma_heir_of',re.compile(r'^(?P<subject>'+NAME+r')(?P<trigger>嗣)(?P<object>'+NAME+r')(?:也)?$')),('heir_predicate','dharma_heir_of',re.compile(r'^(?P<subject>'+NAME+r')(?:為|是|乃)(?P<object>'+NAME+r')(?:之)?(?P<trigger>法嗣)(?:也)?$')),('heir_possessive','dharma_heir_of',re.compile(r'^(?P<object>'+NAME+r')之(?P<trigger>法嗣)(?P<subject>'+NAME+r')(?:也)?$')),('disciple_possessive','disciple_of',re.compile(r'^(?P<object>'+NAME+r')(?:之)?(?P<trigger>弟子)(?P<subject>'+NAME+r')(?:也)?$')),('disciple_predicate','disciple_of',re.compile(r'^(?P<subject>'+NAME+r')(?:為|是|乃)(?P<object>'+NAME+r')(?:之)?(?P<trigger>弟子)(?:也)?$')),('transmission_explicit_recipient','dharma_transmission_to',re.compile(r'^(?P<subject>'+NAME+r')(?P<trigger>傳法)(?:於|與|予)(?P<object>'+NAME+r')(?:也)?$'))]
BAD_NAME=re.compile(r'^(?:其|彼|此|本|先|上|諸|眾|他|某|一人|高僧|大德)|曰|云|問|答|謂|告|乃|何|誰|某|汝|我|吾|法嗣|弟子|傳法')
NEGATION=re.compile(r'(?:非|未|不)(?:是|為|其|曾|嗣|傳法|弟子)|無(?:法嗣|弟子)|莫(?:嗣|傳法)|未詳|不詳|不知|或為|疑|傳聞')
ROBE=re.compile('袈裟|衣鉢|衣缽|法衣|傳衣');SELF=re.compile('我|吾|汝|爾|某甲|學人|小僧|弟子(?:願|不|未|自|是|來|身)')
DIALOGUE=re.compile('曰|云|問|答|對|言');XMLID='http://www.w3.org/XML/1998/namespace}id';UNITS={'p','head','mulu','jhead','item','l','byline','docNumber'};OMIT={'note','rdg','back','standOff','sic'}
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def hashfile(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(64*1024),b''):h.update(b)
 return h.hexdigest()
def lname(s):return s.rsplit('}',1)[-1]
def iter_units(stream):
 p=expat.ParserCreate(namespace_separator='}');stack=[];active=[];queue=[];juan=None;lb=None
 def append(text):
  if not active:return
  u=active[-1];u['length']+=len(text)
  if u['length']>32768:raise RuntimeError('Local evidence unit exceeds32K; failclosed')
  u['parts'].append(text)
 def start(name,attrs):
  nonlocal juan,lb
  tag=lname(name);ns=name.rsplit('}',1)[0] if '}' in name else '';prefix='tei' if ns=='http://www.tei-c.org/ns/1.0' else 'cb' if ns=='http://www.cbeta.org/ns/1.0' else 'ns'
  if stack:counter=stack[-1]['child_counts'];counter[name]+=1;number=counter[name]
  else:number=1
  parent_path=stack[-1]['path'] if stack else '';frame={'tag':tag,'name':name,'attrs':dict(attrs),'line':p.CurrentLineNumber,'byte':p.CurrentByteIndex,'path':parent_path+'/'+prefix+':'+tag+'['+str(number)+']','child_counts':collections.Counter()}
  in_body=any(x['tag']=='body' for x in stack);omitted=any(x['tag'] in OMIT for x in stack)
  if in_body and not omitted:
   if tag=='milestone' and attrs.get('unit')=='juan':juan=attrs.get('n')
   if tag=='juan':juan=attrs.get('n',juan)
   if tag=='lb':
    lb=attrs.get('n')
    if active:active[-1]['lbs'].append({'offset':active[-1]['length'],'n':lb,'xml_line':p.CurrentLineNumber})
   if tag in UNITS:
    if active:append('⟦nested-unit:'+tag+'⟧')
    active.append({'tag':tag,'attrs':dict(attrs),'line':p.CurrentLineNumber,'byte_start':p.CurrentByteIndex,'element_path':frame['path'],'juan':juan,'lb_start':lb,'lbs':[],'parts':[],'length':0,'entities':[],'entity_active':[],'omitted_tags':collections.Counter(),'ancestor_tags':[x['tag'] for x in stack]})
   if tag in OMIT and active:append('⟦omitted:'+tag+'⟧');active[-1]['omitted_tags'][tag]+=1
   if tag=='g' and active:append('⟦g:'+attrs.get('ref','unknown')+'⟧')
   if tag=='persName' and active:active[-1]['entity_active'].append({'start':active[-1]['length'],'attrs':dict(attrs)})
  stack.append(frame)
 def data(text):
  if active and not any(x['tag'] in OMIT for x in stack):append(text)
 def end(name):
  tag=lname(name);frame=stack.pop()
  if tag=='persName' and active and active[-1]['entity_active']:
   ent=active[-1]['entity_active'].pop();ent['end']=active[-1]['length'];active[-1]['entities'].append(ent)
  if active and active[-1]['tag']==tag and active[-1]['byte_start']==frame['byte']:
   u=active.pop();u['projection']=''.join(u.pop('parts'));u.pop('length');u.pop('entity_active');u['omitted_tags']=dict(u['omitted_tags']);u['end_tag_byte']=p.CurrentByteIndex;u['end_line']=p.CurrentLineNumber;queue.append(u)
 def forbidden(*unused):raise RuntimeError('DTD/entities forbidden; no external resource resolution')
 p.StartElementHandler=start;p.EndElementHandler=end;p.CharacterDataHandler=data;p.StartDoctypeDeclHandler=forbidden;p.EntityDeclHandler=forbidden;p.ExternalEntityRefHandler=forbidden
 for block in iter(lambda:stream.read(64*1024),b''):
  p.Parse(block,False)
  while queue:yield queue.pop(0)
 p.Parse(b'',True)
 while queue:yield queue.pop(0)
def compact(text):
 chars=[];positions=[]
 for i,c in enumerate(text):
  if not c.isspace():chars.append(c);positions.append(i)
 return ''.join(chars),positions
def actor_valid(text):
 base=re.sub(TITLE+r'$','',text)
 return len(base)>=2 and not BAD_NAME.search(base) and not TRIGGER.search(base) and not re.search(TITLE,base)
def classify_clause(clause,unit,trigger_start):
 if unit['tag'] in {'head','mulu','jhead','byline','docNumber','item','l'} or any(x in {'head','mulu','jhead','list','table'} for x in unit.get('ancestor_tags',[])):return None,'heading_list_or_verse_context'
 if len(list(TRIGGER.finditer(clause)))!=1:return None,'multiple_trigger_or_chained_role_ambiguity'
 if '⟦' in clause:return None,'gaiji_or_omitted_inline_content_ambiguity'
 if ROBE.search(clause):return None,'robe_or_robe_transmission_context'
 if NEGATION.search(clause):return None,'negated_or_ambiguous_claim'
 if DIALOGUE.search(clause) and SELF.search(clause):return None,'self_referential_dialogue'
 if SELF.search(clause):return None,'pronoun_or_self_reference_not_named_binding'
 for rule,relation_type,pattern in RULES:
  m=pattern.fullmatch(clause)
  if m and m.start('trigger')==trigger_start and actor_valid(m['subject']) and actor_valid(m['object']):
   if m['subject']==m['object']:return None,'self_relation_or_ambiguous_repeated_name'
   return {'rule':rule,'relation_type':relation_type,'subject_name':m['subject'],'object_name':m['object'],'subject_span':m.span('subject'),'object_span':m.span('object')},None
 return None,'missing_explicit_two_named_role_binding_in_same_clause'
def resolve_id(unit,actor_span,positions,registry):
 raw_start=positions[actor_span[0]];raw_end=positions[actor_span[1]-1]+1;refs=[]
 for e in unit['entities']:
  if raw_start<=e['start'] and e['end']<=raw_end:
   for key,value in e['attrs'].items():
    if lname(key) in {'ref','key','corresp'}:refs.append(value)
 dila=[];marcus=[]
 for value in refs:
  m=re.fullmatch(r'https://authority\.dila\.edu\.tw/person/search\.php\?aid=(A\d{6})',value)
  if m and m[1] in registry:dila.append(m[1])
 # Marcus registry not supplied: preserve any reference but do not resolve or invent IDs.
 unique=set(dila)
 return {'id':next(iter(unique)) if len(unique)==1 else None,'namespace':'DILA' if len(unique)==1 else None,'dila_id':next(iter(unique)) if len(unique)==1 else None,'marcus_id':None,'embedded_references':refs,'resolution':'exact_existing_embedded_DILA_reference' if len(unique)==1 else 'unresolved_no_exact_verified_embedded_reference'}
def extract_unit(unit,registry):
 text,positions=compact(unit['projection']);records=[];boundaries=list(re.finditer(r'[^。！？；;!?]+[。！？；;!?]?',text))
 for segment in boundaries:
  whole=segment.group(0);clause=whole.rstrip('。！？；;!?');hits=list(TRIGGER.finditer(clause))
  for hit in hits:
   binding,reason=classify_clause(clause,unit,hit.start());start=segment.start();end=start+len(clause);clip_start=start;clip_end=end
   if len(clause)>800:binding=None;reason=reason or 'local_clause_exceeds_evidence_bound';clip_start=max(start,start+hit.start()-180);clip_end=min(end,start+hit.end()+180)
   raw_start=positions[clip_start];raw_end=positions[clip_end-1]+1;quote=text[clip_start:clip_end];qraw=unit['projection'][raw_start:raw_end]
   lbs=unit['lbs'];start_lb=unit['lb_start'];end_lb=unit['lb_start']
   for marker in lbs:
    if marker['offset']<=raw_start:start_lb=marker['n']
    if marker['offset']<raw_end:end_lb=marker['n']
   identity={'subject':{'id':None,'dila_id':None,'marcus_id':None,'resolution':'no_binding'},'object':{'id':None,'dila_id':None,'marcus_id':None,'resolution':'no_binding'}}
   if binding:
    for role in ('subject','object'):
     a,b=binding[role+'_span'];identity[role]=resolve_id(unit,(start+a,start+b),positions,registry)
   records.append({'candidate_id':'jingde:'+sha_bytes((unit['element_path']+'|'+str(start+hit.start())+'|'+hit.group()).encode())[:20],'status':'unreviewed' if binding else 'excluded','review_state':'unreviewed','exclusion_reason':reason,'trigger':hit.group(),'relation_type':binding['relation_type'] if binding else None,'direction':'subject_to_object' if binding else None,'subject_name':binding['subject_name'] if binding else None,'object_name':binding['object_name'] if binding else None,'subject_id':identity['subject']['id'],'object_id':identity['object']['id'],'identity':identity,'binding_rule':binding['rule'] if binding else None,'quotation':quote,'quotation_source_projection':qraw,'quotation_truncated':clip_start!=start or clip_end!=end,'quotation_sha256':sha_bytes(quote.encode()),'locator':{'work_id':'T51n2076','juan_raw':unit['juan'],'lb_start':start_lb,'lb_end':end_lb,'taisho_start':'T51n2076_p'+start_lb if start_lb else None,'taisho_end':'T51n2076_p'+end_lb if end_lb else None,'element_path':unit['element_path'],'element_xml_id':unit['attrs'].get(XMLID),'element_xml_lines':[unit['line'],unit['end_line']],'trigger_normalized_offset':start+hit.start(),'quotation_projection_offsets':[raw_start,raw_end]},'representation':{'version':'t2076-base-projection-1','source_sha256':PIN,'element_byte_start':unit['byte_start'],'element_end_tag_byte':unit['end_tag_byte'],'element_projection_sha256':sha_bytes(unit['projection'].encode()),'quotation_projection_sha256':sha_bytes(qraw.encode()),'omitted_tags':unit['omitted_tags'],'policy':'Body local units; formatting whitespace removed for matching only; original projected quote retained. Notes/rdg/back/sic and gaiji marked, never silently concatenated into a candidate. No name, punctuation, character-form or generation normalization.'},'source_rights':{'header_artifact':'source-header-fragment.xml','declaration':'Available for non-commercial use when distributed with this header intact.','state':'source_notice_preserved; no clearance or project-license propagation'},'independence_group':'T51n2076_single_pinned_representation'})
 return records

def compare_exact(candidates,baseline):
 result={'overlap':[],'new_to_comparable_snapshot':[],'reverse_review':[],'conflict_review':[],'type_difference_not_conflict':[],'unresolved':[]}
 for c in candidates:
  if not c['subject_id'] or not c['object_id']:
   result['unresolved'].append({'candidate_id':c['candidate_id'],'reason':'missing exact verified external IDs; names/order must not be used to compare'});continue
  same=[b for b in baseline if b['subject_id']==c['subject_id'] and b['object_id']==c['object_id'] and b['relation_type']==c['relation_type']]
  reverse=[b for b in baseline if b['subject_id']==c['object_id'] and b['object_id']==c['subject_id'] and b['relation_type']==c['relation_type']]
  different=[b for b in baseline if {b['subject_id'],b['object_id']}=={c['subject_id'],c['object_id']} and b['relation_type']!=c['relation_type']]
  if same:result['overlap'].append({'candidate_id':c['candidate_id'],'baseline':same,'meaning':'same typed/directed observation by exact IDs; not historical verification or independent confirmation'})
  elif reverse:result['reverse_review'].append({'candidate_id':c['candidate_id'],'baseline':reverse,'meaning':'opposite directed observation; review signal, not automatic contradiction'})
  else:result['new_to_comparable_snapshot'].append({'candidate_id':c['candidate_id'],'meaning':'not present in the selected typed/directed ZTJ snapshot only; absence is not negation or proof of novelty'})
  if different:result['type_difference_not_conflict'].append({'candidate_id':c['candidate_id'],'baseline':different,'meaning':'different types can coexist; not a conflict without explicit mutually exclusive claims'})
 return result

def main():
 ap=argparse.ArgumentParser(description='T2076 isolated strict lexical candidates; default dryrun, no production writes')
 ap.add_argument('--source',type=pathlib.Path,default=ROOT.parents[2]/'data/cbeta/xml-p5-full/T/T51/T51n2076.xml');ap.add_argument('--write',action='store_true');args=ap.parse_args()
 source=args.source.resolve();before=hashfile(source)
 if before!=PIN:raise RuntimeError('Pinned T51n2076 source hash differs; refuse extraction')
 survey=ROOT.parent/'zenodo-10004109-survey-20261016';p2=survey/'analysis/phase2';identity_path=p2/'person-id-audit.json';relation_path=p2/'relation-direction-audit.json';graph_path=survey/'analysis/phase3/source_relation.json'
 inputs=[identity_path,relation_path,graph_path];input_hashes={str(p):hashfile(p) for p in inputs};identity=json.loads(identity_path.read_text(encoding='utf-8'));relations=json.loads(relation_path.read_text(encoding='utf-8'));graph=json.loads(graph_path.read_text(encoding='utf-8'))
 registry={r['source_id'] for r in identity['data']['records'] if r['official_live_label_lookup_as_reported']['http_status_as_reported']==200 and r['official_live_label_lookup_as_reported']['requested_authority_id_found_as_reported']==r['source_id']}
 baseline=[]
 for c in relations['data']['cases']:
  roles=c['textual_role_evidence'];s=roles.get('successor_in_source_phrase') or roles.get('successor_in_edited_phrase');o=roles.get('predecessor_in_source_phrase')
  if s and o:baseline.append({'case':c['case'],'subject_id':s,'object_id':o,'relation_type':'dharma_heir_of','direction':'subject_to_object','file':c['file'],'locator':c['locator'],'source_group':'ZTJ_same_source_complex','certainty':c['markup']['attributes'].get('cert'),'review_state':'unreviewed source-text observation'})
 candidates=[];excluded=[];unit_counts=collections.Counter();trigger_counts=collections.Counter();all_records=0;embedded=collections.Counter();max_projection=0
 with source.open('rb') as stream,source.open('rb') as raw:
  for unit in iter_units(stream):
   unit_counts[unit['tag']]+=1;max_projection=max(max_projection,len(unit['projection']))
   for entity in unit['entities']:
    for val in entity['attrs'].values():
     if 'authority.dila.edu.tw' in val:embedded['DILA']+=1
     if 'marcus' in val.lower():embedded['Marcus']+=1
   rows=extract_unit(unit,registry)
   if not rows:continue
   raw.seek(unit['end_tag_byte']);tail=raw.read(256);end=unit['end_tag_byte']+tail.index(b'>')+1;span_length=end-unit['byte_start']
   if span_length>256*1024:raise RuntimeError('Source local XML span exceeds256K')
   raw.seek(unit['byte_start']);span_hash=sha_bytes(raw.read(span_length))
   for row in rows:
    all_records+=1
    if all_records>20000:raise RuntimeError('Bounded candidate/exclusion record limit exceeded')
    row['representation']['element_byte_end']=end;row['representation']['element_xml_sha256']=span_hash;trigger_counts[row['trigger']]+=1
    (candidates if row['status']=='unreviewed' else excluded).append(row)
 if hashfile(source)!=before:raise RuntimeError('Source changed during extraction; no output allowed')
 if any(hashfile(p)!=input_hashes[str(p)] for p in inputs):raise RuntimeError('ZTJ input drift; no output allowed')
 comparison=compare_exact(candidates,baseline)
 stats={'candidate_count':len(candidates),'excluded_trigger_occurrences':len(excluded),'trigger_occurrences':all_records,'triggers':dict(trigger_counts),'units':dict(unit_counts),'max_retained_projection_chars':max_projection,'candidate_rules':dict(collections.Counter(c['binding_rule'] for c in candidates)),'exclusion_reasons':dict(collections.Counter(c['exclusion_reason'] for c in excluded)),'embedded_identity_refs_in_body':dict(embedded),'candidates_with_both_verified_ids':sum(bool(c['subject_id'] and c['object_id']) for c in candidates),'candidates_with_unresolved_id':sum(not c['subject_id'] or not c['object_id'] for c in candidates)}
 metadata={'definition_version':'t2076-strict-lexical-1','source':{'work_id':'T51n2076','title':'景德傳燈錄','path':str(source),'bytes':source.stat().st_size,'sha256':before,'header_fragment':'source-header-fragment.xml','header_sha256':hashfile(ROOT/'source-header-fragment.xml')},'approved_triggers':['嗣','法嗣','弟子','傳法'],'record_scope':'Strict lexical named-role candidates and all excluded trigger occurrences in selected body structural units; not full historical relation extraction.','representation':'XML P5 base-body local projections; no complete XML tree, no character/generation normalization. Inline note/gaiji markers are explicit exclusion boundaries. Source quotations/projection/XML hashes retained.','identity_policy':'DILA existing embedded verified reference primary only; Marcus existing reference secondary only. This source has no such person annotations. No name-to-ID join, URI minting or inferred IDs. Null means unresolved.','no_mutation':'Read-only pinned source and ZTJ phase outputs; only this report directory receives derived artifacts. No DB/TTL/legacy writes, importer, API, external lookup or accepted relation.','source_rights':'Available for non-commercial use when distributed with this header intact. Header preserved; no license propagation or public export.','comparison_inputs':[{'path':str(p),'sha256':input_hashes[str(p)]} for p in inputs],'script_sha256':hashfile(pathlib.Path(__file__))}
 dataset={'metadata':metadata,'stats':stats,'candidates':candidates,'excluded_trigger_occurrences':excluded}
 comparison_output={'metadata':{'definition_version':'t2076-exact-id-comparison-1','source_sha256':before,'baseline_inputs':metadata['comparison_inputs'],'policy':'Exact external IDs + same relation type + same directed roles only. Missing IDs remain unresolved. Absent observation is not negation. Different type/order is not automatically contradiction.','baseline_coverage':'Only the ten locatable ZTJ case panel supplies textual role observations; CSV/GEXF source rows are undirected and cannot establish directed teacher relations. CSV/GEXF and repeated ZTJ passages are not independent evidence.','baseline_typed_observations':len(baseline),'baseline_unique_typed_keys':len({(b['subject_id'],b['object_id'],b['relation_type']) for b in baseline}),'graph_rows_excluded_as_direction_evidence':len(graph['records']),'conflict_policy':'No mutually exclusive claim rule is supplied; exclusions/absence/different relation types do not generate conflicts.'},'baseline_observations':baseline,'lists':comparison}
 summary={'status':'PASS','mode':'write' if args.write else 'dry-run','source_hash_unchanged':True,'stats':stats,'comparison_list_counts':{k:len(v) for k,v in comparison.items()}}
 quality=['# T.2076 strict lexical candidate quality report','','## Scope and pinned source','Source: immutable local CBETA xml-p5-full T/T51/T51n2076.xml, 3,691,202 bytes. SHA256 '+before+'. Header fragment SHA256 '+metadata['source']['header_sha256']+'; source rights notice retained exactly. No production data was read or mutated except the explicitly authorized immutable source read.','','## Measured extraction','- Approved trigger occurrences: '+str(all_records),'- Unreviewed named-role candidates: '+str(len(candidates)),'- Excluded occurrences: '+str(len(excluded)),'- Candidates with two verified external IDs: '+str(stats['candidates_with_both_verified_ids']),'- Maximum retained local projection: '+str(max_projection)+' characters. Source streamed in64K chunks; no full XML tree.','','## Strictness and known false negatives','Only complete local clauses matching six closed two-named-title role templates qualify. Both names must appear in the same clause. Headings/lists/verse, pronouns/self-dialogue, robe context, negation/ambiguity, chained triggers, inline omitted/gaiji ambiguity and missing named bindings are excluded. Bio headings, previous paragraphs, proximity/order, unapproved verbs and name dictionaries never supply an endpoint. This deliberately misses valid claims expressed with bare names, pronouns or other syntax; it is not a corpus-complete genealogy or a historical judgment.','','## Exclusion counts',json.dumps(stats['exclusion_reasons'],ensure_ascii=False,indent=2),'','## Identity and comparison limits','No DILA/Marcus identity tags/authority references were found in the authorized source inventory. Candidate IDs remain null unless an exact verified embedded reference is present; label similarity is not used. Empty overlap/new/reverse/conflict lists cannot be read as no overlap or historical novelty. Missing identities are listed unresolved.','The ZTJ comparison uses only explicit typed/directed roles from the ten-case panel. Its CSV/GEXF rows are undirected. All same-work source variants/passages stay one source complex, not independent confirmation. Absence is not negation; different types can coexist.','','## Rights and review block','Header says non-commercial use with header intact. Header fragment is a byte-exact XML fragment inheriting namespaces from the original TEI root; it is not a standalone reserialized document. This local derived survey grants no rights to production data or public/commercial reuse. Candidates and automated exclusions remain for review; no accepted relation or generation inference exists.','','## Commands / validation','python -X utf8 extract_jingde.py (default dry-run)','python -X utf8 extract_jingde.py --write (exclusive new outputs only)','python -X utf8 test_jingde.py (synthetic fixtures; separate from real dataset)','','Source and three ZTJ input hashes are checked before/after extraction. Tests and final manifest are reported separately. No API, importer, production pipeline or historical validation was run.','']
 if args.write:
  for filename,obj in [('jingde-data.json',dataset),('jingde-comparison.json',comparison_output)]:
   with (ROOT/filename).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
  with (ROOT/'jingde-quality-report.md').open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(quality))
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
