# -*- coding: utf-8 -*-
"""T232: số đời đa hệ, chỉ từ mốc + đường có nguồn; không sửa số cũ.

Duyệt tổ tiên theo từng người, ngăn xếp tường minh/memo (không tràn recursion).
Teacher chung của DILA cho ứng viên; không tự nâng thành truyền pháp verified.
"""
import copy, datetime, hashlib, json, re, sqlite3, xml.etree.ElementTree as ET
from collections import deque
from src_python import ttl_profile_v2 as m
from src_python.ttl_db_export import raw_dila, table

VERSION = 'generation-dag/1.0.0'
TEI = '{http://www.tei-c.org/ns/1.0}'
XML = '{http://www.w3.org/XML/1998/namespace}'
MAX_NODES, MAX_EDGES, MAX_VALUES = 2500, 10000, 128

_DHARMA_EDGES_PATH = __file__.rsplit('src_python', 1)[0] + 'data/dharma_edges.json'
_dharma_edge_ids_cache = None  # None = chưa nạp; set() = đã nạp (có thể rỗng)
_dharma_warned = False

def dharma_excluded_edge_ids():
    """T270 (sửa sau QA CHƯA ĐẠT): tập id (lineage_edge_assertions.id) bị LOẠI khỏi
    parents() vì cạnh đó (a) có nhãn tham_hoc VÀ (b) có đối chiếu TTL (ttl_match
    khác chuỗi 'no_ttl_relation'). Cạnh mà TTL không phủ (ttl_match=='no_ttl_relation'),
    cạnh không ghép được tên (label=='khong_ghep_duoc'), và cạnh nối pháp đều GIỮ
    NGUYÊN — chỉ cạnh đã được TTL xác định rõ là tham học mới bị loại khỏi đường
    đếm số đời. Việc này tránh làm mất số đời của các tông mà TTL chưa phủ tới.

    Nạp từ data/dharma_edges.json (file dẫn xuất, không ghi DB).
    Trả về None nếu:
      - biến môi trường DHARMA_FILTER=0 (dùng cho test engine, không đổi chữ ký
        hàm public compute()/parents() đang được test dùng), hoặc
      - file chưa tồn tại, hoặc file hỏng (JSON không đọc được) — khi đó parents()
        giữ hành vi cũ (toàn bộ cạnh DILA teacher_of), kèm cảnh báo in ra một lần."""
    import os
    global _dharma_edge_ids_cache, _dharma_warned
    if os.environ.get('DHARMA_FILTER') == '0':
        return None
    if _dharma_edge_ids_cache is not None:
        return _dharma_edge_ids_cache
    if not os.path.exists(_DHARMA_EDGES_PATH):
        if not _dharma_warned:
            print('[T270] CẢNH BÁO: thiếu data/dharma_edges.json — parents() dùng toàn bộ cạnh DILA teacher_of (hành vi cũ, chưa lọc tham học).')
            _dharma_warned = True
        return None
    try:
        with open(_DHARMA_EDGES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as ex:
        if not _dharma_warned:
            print('[T270] CẢNH BÁO: data/dharma_edges.json hỏng hoặc đọc lỗi ('+str(ex)+') — parents() dùng toàn bộ cạnh DILA teacher_of (hành vi cũ, chưa lọc tham học).')
            _dharma_warned = True
        return None
    excluded = set()
    for e in data.get('edges', []):
        if e.get('label') == 'tham_hoc' and e.get('ttl_match') != 'no_ttl_relation':
            eid = e.get('dila_edge_id')
            if eid is not None:
                excluded.add(eid)
    _dharma_edge_ids_cache = excluded
    return excluded

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def digest(obj):
    return hashlib.sha256(canonical(obj).encode('utf8')).hexdigest()

def checked_raw(conn, aid):
    try:return raw_dila(conn,aid)
    except (ET.ParseError,KeyError,TypeError) as ex:raise ValueError('Record DILA sai cấu trúc: '+str(aid)) from ex

def identity(conn, aid, expected=''):
    if not re.fullmatch(r'A\d{6}', str(aid)):
        raise ValueError('DILA ID cần A + 6 chữ số; không dò tên để đoán ID.')
    record = checked_raw(conn, aid)
    if not record or m.digest(record['raw_text']) != record['sha256']:
        raise ValueError('Thiếu record DILA hoặc SHA không khớp: '+aid)
    try:node = ET.fromstring(record['raw_text'])
    except ET.ParseError as ex:raise ValueError('XML DILA sai cú pháp: '+aid) from ex
    if node.get(XML+'id') != aid:
        raise ValueError('xml:id không khớp khóa DB: '+aid)
    names = [''.join(n.itertext()).strip() for n in node.findall(TEI+'persName')
             if n.get(XML+'lang') in ('zho-Hant','zh-Hant','zh')]
    if expected and expected not in names:
        raise ValueError('Tên Hán không thuộc chính record DILA '+aid)
    return {'person_id':aid, 'names':names, 'version':record['version'],
            'sha256':record['sha256'], 'record_id':record.get('id',aid)}

def validate_scheme(conn, config):
    """Duyệt mốc mới vẫn phải đủ ba gốc chứng cứ, không đếm mirror."""
    c = copy.deepcopy(config)
    if not isinstance(c,dict) or not re.fullmatch(r'[a-z0-9_-]{1,60}',str(c.get('id',''))):
        raise ValueError('Mã hệ đếm dùng chữ thường, số, _ hoặc -.')
    if not isinstance(c.get('label'),str) or not c['label'].strip():
        raise ValueError('Cần tên hệ đếm.')
    if not isinstance(c.get('convention'),str) or not c['convention'].strip():
        raise ValueError('Cần quy ước gốc và phạm vi đếm.')
    if c.get('policy') not in ('dila_candidate','reviewed_transmission'):
        raise ValueError('Policy phải là dila_candidate hoặc reviewed_transmission.')
    anchors = c.get('anchors')
    if not isinstance(anchors,list) or len(anchors)>30:
        raise ValueError('Mỗi hệ tối đa 30 mốc.')
    ids = set()
    for a in anchors:
        if not isinstance(a,dict):raise ValueError('Mốc phải là object.')
        aid=a.get('person_id');number=a.get('number')
        if not isinstance(aid,str):raise ValueError('DILA ID mốc phải là chuỗi.')
        if aid in ids:raise ValueError('Mốc trùng ID trong cùng hệ đếm.')
        ids.add(aid)
        if any(not isinstance(a.get(k,''),str) for k in ('status','reviewer','rationale','reviewed_at')):
            raise ValueError('Metadata duyệt mốc phải là chuỗi.')
        if type(number) is not int or number<0 or number>10000:
            raise ValueError('Số đời mốc là integer 0..10000; 0 dành cho gốc ngoài danh sách tổ.')
        if not isinstance(a.get('name_zh'),str) or not a['name_zh'].strip():
            raise ValueError('Mốc cần tên Hán để khóa đúng ID.')
        observed=identity(conn,aid,a['name_zh'])
        if a.get('identity') and a['identity']!=observed:
            raise ValueError('Phiên bản nguồn của mốc đã đổi: '+aid+'; cần lưu revision mốc mới.')
        a['identity']=observed
        if a.get('status') not in ('draft','source_asserted','accepted'):
            raise ValueError('Trạng thái mốc không hợp lệ.')
        evidence=a.get('evidence',[])
        if not isinstance(evidence,list) or len(evidence)>30:
            raise ValueError('Chứng cứ mốc phải là danh sách tối đa 30 mục.')
        for e in evidence:
            if not isinstance(e,dict) or any(not isinstance(e.get(k,''),str) for k in ('citation','version','independence_key','url')):
                raise ValueError('Chứng cứ cần citation/version/independence_key/url dạng chuỗi.')
            if e.get('url') and not m.iri(e['url']):raise ValueError('URL chứng cứ không hợp lệ.')
        if a['status']=='accepted':
            roots={e.get('independence_key','').strip() for e in evidence if e.get('citation','').strip() and e.get('version','').strip()}-{''}
            if len(roots)<3:raise ValueError('Mốc được duyệt cần ít nhất 3 gốc chứng cứ độc lập có định vị/phiên bản.')
            if not a.get('reviewer','').strip() or not a.get('rationale','').strip():
                raise ValueError('Duyệt mốc cần người duyệt và lập luận số đời.')
            try:
                date=datetime.datetime.fromisoformat(a.get('reviewed_at','').replace('Z','+00:00'))
                if date.tzinfo is None:raise ValueError()
            except (TypeError,ValueError):raise ValueError('Ngày duyệt cần ISO8601 có timezone.')
    if anchors and c.get('root_id') not in ids:
        raise ValueError('Gốc tính phải là một mốc trong hệ đếm.')
    if not anchors and c.get('root_id'):raise ValueError('Hệ chưa có mốc phải để trống ID gốc.')
    reviewed=c.get('reviewed_edges',[])
    if not isinstance(reviewed,list) or len(reviewed)>MAX_EDGES:raise ValueError('Danh sách cạnh duyệt vượt giới hạn.')
    keys=set()
    for e in reviewed:
        if not isinstance(e,dict) or not isinstance(e.get('id'),str) or not e['id'] or e['id'] in keys:
            raise ValueError('ID cạnh duyệt rỗng/trùng.')
        keys.add(e['id'])
        if any(not isinstance(e.get(k,''),str) for k in ('parent','child','citation','version','reviewer','reviewed_at')):
            raise ValueError('Metadata cạnh duyệt phải là chuỗi.')
        identity(conn,e.get('parent'));identity(conn,e.get('child'))
        if e['parent']==e['child']:raise ValueError('Không duyệt cạnh tự nối.')
        if e.get('kind')!='dharma_transmission' or e.get('status')!='accepted':
            raise ValueError('Cạnh dùng trong policy reviewed phải là truyền pháp trực tiếp đã duyệt.')
        if not e.get('citation','').strip() or not e.get('version','').strip() or not e.get('reviewer','').strip():
            raise ValueError('Cạnh truyền pháp cần sử liệu/phiên bản/người duyệt.')
        try:
            if datetime.datetime.fromisoformat(e.get('reviewed_at','').replace('Z','+00:00')).tzinfo is None:raise ValueError()
        except (ValueError,TypeError):raise ValueError('Cạnh duyệt cần ngày ISO8601 có timezone.')
    return c

def ensure_schema(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS generation_v2_scheme_revisions(
      scheme_id TEXT NOT NULL, revision INTEGER NOT NULL, config_json TEXT NOT NULL,
      sha256 TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(scheme_id,revision));
    CREATE TABLE IF NOT EXISTS generation_v2_calculations(
      id TEXT PRIMARY KEY, person_id TEXT NOT NULL, created_at TEXT NOT NULL,
      payload_json TEXT NOT NULL, sha256 TEXT NOT NULL);
    ''')

def schemes(conn):
    if not table(conn,'generation_v2_scheme_revisions'):return []
    result=[]
    for row in conn.execute('''SELECT s.* FROM generation_v2_scheme_revisions s
      JOIN (SELECT scheme_id,max(revision) revision FROM generation_v2_scheme_revisions GROUP BY scheme_id) x
      ON s.scheme_id=x.scheme_id AND s.revision=x.revision ORDER BY s.scheme_id'''):
        c=json.loads(row['config_json'])
        if digest(c)!=row['sha256']:raise ValueError('Hash registry hệ đếm không khớp.')
        c['_revision']=row['revision'];c['_sha256']=row['sha256'];result.append(c)
    return result

def save_scheme(conn,config,expected_revision=0):
    c=validate_scheme(conn,config)
    c.pop('_revision',None);c.pop('_sha256',None)
    conn.execute('BEGIN IMMEDIATE')
    try:
        old=conn.execute('SELECT max(revision) FROM generation_v2_scheme_revisions WHERE scheme_id=?',(c['id'],)).fetchone()[0] or 0
        if type(expected_revision) is not int or old!=expected_revision:
            raise ValueError('Hệ đếm đã đổi ở phiên khác; nạp lại trước khi lưu.')
        conn.execute('INSERT INTO generation_v2_scheme_revisions VALUES(?,?,?,?,?)',
                     (c['id'],old+1,canonical(c),digest(c),m.now()));conn.commit()
    except Exception:conn.rollback();raise
    c['_revision']=old+1;c['_sha256']=digest({k:v for k,v in c.items() if not k.startswith('_')})
    return c

def parents(conn, child, config):
    if config['policy']=='reviewed_transmission':
        return [e for e in config.get('reviewed_edges',[]) if e.get('child')==child]
    if not table(conn,'lineage_edge_assertions'):return []
    # Chỉ DILA direct teacher; Marcus/TTL/đồng môn không được trộn vào đường đếm.
    rows=conn.execute('''SELECT * FROM lineage_edge_assertions
              WHERE object_person_id=? AND source_code='DILA' AND relation_type='da:isTeacherOf'
              AND raw_relation_type='dila:teacher_of' AND status='active' AND mapping_verified=1 ORDER BY id''',(child,))
    rows=list(rows)
    # T270 (sửa sau QA CHƯA ĐẠT): chỉ BỎ cạnh đã được TTL xác định rõ là tham học
    # (label=='tham_hoc' và ttl_match != 'no_ttl_relation'). Cạnh mà TTL không phủ
    # (no_ttl_relation) GIỮ NGUYÊN như cũ -> các tông khác không bị mất số đời.
    # Không có file / file hỏng / DHARMA_FILTER=0 -> giữ nguyên toàn bộ cạnh DILA
    # như cũ (đã cảnh báo trong dharma_excluded_edge_ids()).
    _excluded_ids=dharma_excluded_edge_ids()
    if _excluded_ids is not None:
        rows=[r for r in rows if r['id'] not in _excluded_ids]
    child_record=checked_raw(conn,child)
    child_xml=ET.fromstring(child_record['raw_text'])
    teachers={r.get('active') for r in child_xml.findall('.//'+TEI+'relation') if r.get('type')=='teacher'}
    result=[]
    for r in rows:
        parent=r['subject_person_id'];source=child_record if parent in teachers else checked_raw(conn,parent)
        matches=parent in teachers
        if source and not matches:
            matches=any(n.get('type')=='student' and n.get('active')==child for n in ET.fromstring(source['raw_text']).findall('.//'+TEI+'relation'))
        citation=r['ref'] or ''
        if source and matches and not citation:
            typ='teacher' if parent in teachers else 'student';other=parent if typ=='teacher' else child
            refs=[n for n in ET.fromstring(source['raw_text']).findall('.//'+TEI+'relation') if n.get('type')==typ and n.get('active')==other]
            citation='; '.join(''.join(b.itertext()).strip() for n in refs for b in n.findall('.//'+TEI+'bibl'))
        result.append({'parent':parent,'child':child,'id':'DILA:'+str(r['id']),
          'citation':citation, 'raw_type':r['raw_relation_type'],'status':'source_asserted',
          'kind':'generic_teacher','xml_matches':matches,
          'source_record':{'person_id':source['record_id'] if source and 'record_id' in source else (child if parent in teachers else parent),
                           'version':source['version'] if source else '', 'sha256':source['sha256'] if source else ''}})
    return result

def compute(conn, person_id, config):
    """Tất cả độ dài khả dĩ; không BFS-min, không chọn thầy đầu tiên."""
    target_identity=identity(conn,person_id)
    c=validate_scheme(conn,config)
    c['_revision']=config.get('_revision',0);c['_sha256']=config.get('_sha256',digest(c))
    anchors={a['person_id']:a for a in c['anchors']}
    base={'scheme_id':c['id'],'label':c['label'],'convention':c['convention'],
          'revision':c['_revision'],'scheme_sha256':c['_sha256'],'policy':c['policy'],
          'person_id':person_id,'number':None,'candidates':[],'issues':[],
          'algorithm':VERSION,'target_identity':target_identity}
    if not anchors:
        return dict(base,status='missing_anchor',message='Chưa khóa khai tổ/mốc có căn cứ; không đoán số.')
    graph={};all_edges=[];todo=[person_id];seen=set();identities={person_id:target_identity}
    while todo:
        node=todo.pop()
        if node in seen:continue
        seen.add(node)
        if len(seen)>MAX_NODES:return dict(base,status='resource_limit',message='Vượt giới hạn tổ tiên; chưa có kết quả đầy đủ.')
        try:identities[node]=identity(conn,node)
        except ValueError as e:
            base['issues'].append({'type':'missing_identity','person_id':node,'message':str(e)});graph[node]=[];continue
        edges=[] if node==c['root_id'] else parents(conn,node,c)
        valid=[]
        for edge in edges:
            if edge.get('xml_matches') is False:
                base['issues'].append({'type':'edge_not_in_raw_dila','edge_id':edge['id'],'person_id':node});continue
            valid.append(edge)
        edges=valid
        graph[node]=edges;all_edges.extend(edges)
        if len(all_edges)>MAX_EDGES:return dict(base,status='resource_limit',message='Vượt giới hạn cạnh; không trả số từ dữ liệu bị cắt.')
        for edge in edges:todo.append(edge['parent'])
    # Tô màu DFS bằng stack; memo từng nút; hậu tố xung đột/chu trình lan xuống.
    state={};order=[];cycles=set()
    for start in graph:
        if state.get(start):continue
        stack=[(start,0)];trail=[]
        while stack:
            node,pos=stack[-1]
            if not state.get(node):state[node]=1;trail.append(node)
            edges=graph.get(node,[])
            if pos>=len(edges):
                state[node]=2;order.append(node);stack.pop();trail.pop();continue
            parent=edges[pos]['parent'];stack[-1]=(node,pos+1)
            if state.get(parent)==1:
                cycles.update(trail[trail.index(parent):])
            elif not state.get(parent):stack.append((parent,0))
    values={};paths={};blocked=set(cycles);root_reachable={}
    root=c['root_id']
    for node in order:
        nums=set();witness={}
        # Các checkpoint là phép kiểm, không cho đường tắt vượt một cạnh mâu thuẫn.
        root_reachable[node]=node==root or any(root_reachable.get(e['parent'],False) for e in graph[node])
        if node in anchors and root_reachable[node]:
            n=anchors[node]['number'];nums.add(n);witness[n]={'anchor':node,'previous':None}
        for e in graph[node]:
            parent=e['parent']
            if parent in blocked:blocked.add(node)
            for n in values.get(parent,set()):
                nums.add(n+1)
                if n+1 not in witness or (node in anchors and witness[n+1]['anchor']==node):
                    old=paths[parent][n];witness[n+1]={'anchor':old['anchor'],
                      'previous':(parent,n,e['id'])}
        if node in anchors and not root_reachable[node]:
            base['issues'].append({'type':'checkpoint_not_connected_to_root','person_id':node})
        if node!=root and not graph[node] and node not in anchors:
            base['issues'].append({'type':'orphan_outside_root','person_id':node})
        for edge in graph[node]:
            if not root_reachable.get(edge['parent'],False):
                base['issues'].append({'type':'unresolved_parent_branch','person_id':node,'edge_id':edge['id']})
        if len(nums)>MAX_VALUES:
            return dict(base,status='resource_limit',message='Quá nhiều số khả dĩ; cần review đường truyền.')
        values[node]=nums;paths[node]=witness
        if len(nums)>1:blocked.add(node)
    candidates=sorted(values.get(person_id,set()))
    witnesses={};steps=0
    for number in candidates:
        node=person_id;value=number;persons=[];edges=[]
        while True:
            steps+=1
            if steps>50000:return dict(base,status='resource_limit',message='Đường chứng minh vượt giới hạn output; cần thu hẹp phạm vi.')
            persons.append(node);w=paths[node][value]
            if w['previous'] is None:break
            node,value,edge=w['previous'];edges.append(edge)
        witnesses[str(number)]={'anchor':node,'person_ids':list(reversed(persons)),'edge_ids':list(reversed(edges))}
    base.update(candidates=candidates,nodes_checked=len(seen),edges_checked=len(all_edges),
                graph_sha256=digest({'identities':identities,'edges':all_edges}),
                provenance={'scheme':c,'identities':identities,'edges':all_edges,
                            'witnesses':witnesses})
    if cycles:base['issues'].append({'type':'cycle','person_ids':sorted(cycles)})
    for node in sorted(blocked-cycles):
        if len(values.get(node,set()))>1:base['issues'].append({'type':'conflicting_paths_or_anchor','person_id':node,'numbers':sorted(values[node])})
    if person_id in blocked:
        return dict(base,status='conflict',message='Đường truyền hoặc mốc mâu thuẫn/chu trình; không chốt một số.')
    if not candidates:return dict(base,status='unreachable',message='Không có đường có nguồn tới mốc trong hệ này.')
    # BUG-032 fix: nếu có candidates (đường chứng minh tồn tại), trả number dù có issues ở nhánh khác.
    # Issues ở những tổ tiên không liên quan không ảnh hưởng số đời của node hiện tại.
    # Chỉ ghi nhận issues để audit, không chặn kết quả.
    verified=c['policy']=='reviewed_transmission' and all(a['status']=='accepted' for a in c['anchors'])
    result=dict(base,number=candidates[0],status='derived_reviewable' if verified else 'candidate',
                message='Mốc + số cạnh trực tiếp; '+('đủ điều kiện trình duyệt.' if verified else 'còn mốc/teacher nguồn cần duyệt truyền pháp.'))
    # Ghi chú thêm nếu có issues (nhưng không chặn kết quả)
    if base['issues']:
        result['message']+=' ⚠ Có issues ở nhánh tổ tiên khác (audit log đầy đủ).'
    return result

def calculate_all(conn,aid):
    identity(conn,aid)
    configs=schemes(conn)
    return {'person_id':aid,'algorithm':VERSION,'calculated_at':m.now(),
            'results':[compute(conn,aid,c) for c in configs]}

def attach_profile(profile, report):
    """T232 dùng RDF Statement hiện có; payload giữ toàn bộ đường/phiên bản."""
    p=copy.deepcopy(profile)
    if p['person'].get('dila_id')!=report['person_id']:raise ValueError('Kết quả tính không thuộc ID hồ sơ.')
    p['sources']=[s for s in p['sources'] if not s['id'].startswith('generation_v2_')]
    p['assertions']=[a for a in p['assertions'] if not a['id'].startswith('generation_v2_')]
    for result in report['results']:
        sid='generation_v2_'+result['scheme_id']
        p['sources'].append({'id':sid,'code':'LOCAL','record_id':report['person_id']+':'+result['scheme_id'],
          'version':VERSION+':'+str(result['revision']), 'citation':result['label']+' · '+result['convention'],
          'sha256':digest(result),'retrieved_at':report['calculated_at'],'rights_status':'pending_source_review',
          'snapshot':result})
        if result['number'] is not None and result['number']>0:
            p['assertions'].append({'id':sid,'subject':p['person']['uri'],'predicate':m.PREDICATES['generation'],
              'object':{'kind':'literal','value':str(result['number']),'datatype':str(m.XSD.integer)},
              'status':'draft','evidence':[sid],'counting_scheme':result['scheme_id']+'@'+str(result['revision'])+' · '+result['convention'],
              'derivation':VERSION,'rationale':result['message']+' Path/hash trong sourceSnapshot. Không ghi đè số đời legacy.'})
    return m.normalize(p)
