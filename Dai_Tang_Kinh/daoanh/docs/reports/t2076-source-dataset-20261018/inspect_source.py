import collections,hashlib,json,pathlib,sys,xml.parsers.expat as E
source=pathlib.Path(sys.argv[1]);out=pathlib.Path(__file__).resolve().parent
h=hashlib.sha256()
with source.open('rb') as f:
 for b in iter(lambda:f.read(64*1024),b''):h.update(b)
p=E.ParserCreate(namespace_separator='}');stack=[];counts=collections.Counter();units=[];active=[];juan=None;lb=None;header=None;max_chars=0;identifiers=[];triggers=('法嗣','弟子','傳法','嗣')
def tag(x):return x.rsplit('}',1)[-1]
def start(name,attrs):
 global juan,lb,header
 local=tag(name);counts[local]+=1;frame={'tag':local,'line':p.CurrentLineNumber,'byte':p.CurrentByteIndex,'attrs':dict(attrs)}
 if local=='teiHeader':header={'start':p.CurrentByteIndex,'start_line':p.CurrentLineNumber}
 if local=='milestone' and attrs.get('unit')=='juan':juan=attrs.get('n')
 if local=='juan':juan=attrs.get('n',juan)
 if local=='lb':lb=attrs.get('n')
 if local in {'persName','person','relation'} or any(('dila' in str(v).lower() or 'marcus' in str(v).lower()) for v in attrs.values()):identifiers.append(frame)
 if local in {'p','head','mulu','l'} and any(x['tag']=='body' for x in stack):active.append({**frame,'juan':juan,'lb':lb,'text':[],'chars':0})
 stack.append(frame)
def data(s):
 for u in active:
  u['chars']+=len(s)
  if u['chars']>65536:raise RuntimeError('local unit bound exceeded')
  u['text'].append(s)
def end(name):
 global max_chars,header
 local=tag(name);frame=stack.pop()
 if local=='teiHeader':header['end_start']=p.CurrentByteIndex;header['end_line']=p.CurrentLineNumber
 if active and active[-1]['tag']==local and active[-1]['byte']==frame['byte']:
  u=active.pop();text=''.join(u.pop('text'));max_chars=max(max_chars,u.pop('chars'));u['end_line']=p.CurrentLineNumber
  if any(t in text for t in triggers):u['text']=text;units.append(u)
def reject(*args):raise RuntimeError('DTD/entity forbidden')
p.StartElementHandler=start;p.EndElementHandler=end;p.CharacterDataHandler=data;p.StartDoctypeDeclHandler=reject;p.EntityDeclHandler=reject
with source.open('rb') as f:
 for b in iter(lambda:f.read(64*1024),b''):p.Parse(b,False)
p.Parse(b'',True)
with source.open('rb') as f:f.seek(header['end_start']);tail=f.read(256);end=header['end_start']+tail.index(b'>')+1;f.seek(header['start']);raw=f.read(end-header['start'])
with (out/'source-header-fragment.xml').open('xb') as f:f.write(raw)
by_trigger={}
for t in triggers:
 examples=[]
 for u in units:
  if u['tag']=='p' and t in u['text']:
   at=u['text'].index(t);examples.append({k:v for k,v in u.items() if k!='text'}|{'context':u['text'][max(0,at-80):at+100]})
  if len(examples)==8:break
 by_trigger[t]={'unit_count':sum(t in u['text'] for u in units),'examples':examples}
result={'source_path':str(source),'source_bytes':source.stat().st_size,'sha256':h.hexdigest(),'header':header|{'end':end,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'tag_counts':dict(counts),'max_unit_characters':max_chars,'units_with_triggers':len(units),'embedded_identity_elements':identifiers,'triggers':by_trigger}
with (out/'source-discovery.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
