# -*- coding: utf-8 -*-
"""Audit TTL từng file; chỉ đọc DB nguồn, không sửa dữ liệu học thuật.
Regex là kiểm tra sơ bộ khi thiếu rdflib, không thay thế RDF parser.
"""
import json,re,sqlite3,hashlib,sys
from pathlib import Path
from collections import Counter,defaultdict
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'docs'/'reports'/'ttl-lineage-audit-2026-10-02'

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect('file:'+str(BASE/'data'/'lineage.db').replace('\\','/')+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    idx=sqlite3.connect(OUT/'index.sqlite')
    idx.executescript('DROP TABLE IF EXISTS nodes; DROP TABLE IF EXISTS edges; CREATE TABLE nodes(file TEXT,slug TEXT,label TEXT,gen INTEGER,sect TEXT,dila TEXT,sha TEXT); CREATE TABLE edges(file TEXT,t TEXT,d TEXT,kind TEXT); CREATE INDEX en ON edges(t,d); CREATE INDEX ns ON nodes(slug);')
    counts=Counter(); total=0; rdf_ok=0
    try:
        import rdflib
    except ImportError:
        rdflib=None
    with (OUT/'findings.jsonl').open('w',encoding='utf-8') as log:
        def finding(code,**kw):
            counts[code]+=1
            log.write(json.dumps(dict(code=code,**kw),ensure_ascii=False)+'\n')
        for path in sorted((BASE/'data'/'ttl').glob('*.ttl')):
            if path.name=='0-template.ttl': continue
            total+=1
            try:
                raw=path.read_bytes(); text=raw.decode('utf-8-sig')
                if not text.strip(): finding('EMPTY',file=path.name); continue
                if rdflib:
                    try:
                        g=rdflib.Graph(); g.parse(data=text,format='turtle'); rdf_ok+=1
                    except Exception as e: finding('RDF_INVALID',file=path.name,error=str(e)[:250])
                # Bỏ literal và comment khi tìm subject, tránh bắt quan hệ trong tiểu sử.
                clean=re.sub(r'"""[\s\S]*?"""', '""', text)
                declarations=list(re.finditer(r'<ex:(?:monk|person)/([^>]+)>\s+a\s+(?:<bkg:Monk>|bkg:Monk\b)',clean))
                if not declarations: finding('MAIN_UNSUPPORTED',file=path.name); continue
                if len(declarations)!=1: finding('MULTIPLE_MAIN',file=path.name,count=len(declarations))
                m=declarations[0]; slug=m[1]
                tail=clean[m.end():]
                stop=re.search(r'\n\s*<ex:',tail)
                block=tail[:stop.start()] if stop else tail
                def val(pattern):
                    x=re.search(pattern,block); return x[1] if x else None
                label=val(r'rdfs:label\s+"([^"\n]*)"@vi')
                ident=val(r'crm:P1_is_identified_by\s+<ex:(?:monk|person)/([^>]+)>')
                gen=val(r'bkg:generationOrder\s+(\d+)')
                sect=val(r'bkg:dharmaLineageName\s+"([^"\n]*)"@vi')
                if ident and ident!=slug: finding('IDENTIFIER_DIFFERENT',file=path.name,subject=slug,identified=ident)
                expected=re.sub(r'^(TS|Cs|Bo-Tat)-','',path.stem,flags=re.I).replace('-','_').lower()
                if expected!=slug: finding('FILENAME_SUBJECT_DIFFERENT',file=path.name,subject=slug,filename_slug=expected)
                persons=list(db.execute('SELECT dila_id,status FROM vn_person_authority WHERE id=?',(slug,)))
                dila=persons[0]['dila_id'] if len(persons)==1 else None
                if not dila: finding('DILA_UNRESOLVED',file=path.name,subject=slug)
                idx.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?,?)',(path.name,slug,label,int(gen) if gen else None,sect,dila,hashlib.sha256(raw).hexdigest()))
                for kind in ['hasTeacher','hasDisciple']:
                    for b in re.finditer(r'bkg:'+kind+r'\s+([^;]+)',block):
                        for target in re.findall(r'<ex:(?:monk|person)/([^>]+)>',b[1]):
                            t,d=(target,slug) if kind=='hasTeacher' else (slug,target)
                            idx.execute('INSERT INTO edges VALUES(?,?,?,?)',(path.name,t,d,kind))
            except Exception as e:
                finding('FILE_READ_OR_EXTRACT_ERROR',file=path.name,error=str(e))
        idx.commit()
        for slug,n,files in idx.execute('SELECT slug,count(*),group_concat(file) FROM nodes GROUP BY slug HAVING count(*)>1'):
            finding('SUBJECT_COLLISION',subject=slug,count=n,files=files)
        nodes={}
        for row in idx.execute('SELECT slug,gen,sect,dila FROM nodes'):
            if row[0] in nodes: nodes[row[0]]=None
            else: nodes[row[0]]=row[1:]
        adjacency=defaultdict(set)
        for t,d in idx.execute('SELECT DISTINCT t,d FROM edges'):
            adjacency[t].add(d)
            files=[r[0] for r in idx.execute('SELECT DISTINCT file FROM edges WHERE t=? AND d=?',(t,d))]
            if t==d: finding('SELF_EDGE',teacher=t,disciple=d,files=files)
            if t!=d and idx.execute('SELECT 1 FROM edges WHERE t=? AND d=?',(d,t)).fetchone():
                if t<d: finding('REVERSED_PAIR',teacher=t,disciple=d,files=files)
            tn,dn=nodes.get(t),nodes.get(d)
            if t not in nodes or d not in nodes: finding('ENDPOINT_NO_MAIN_FILE',teacher=t,disciple=d,files=files)
            if tn and dn:
                if tn[0] is not None and dn[0] is not None:
                    if tn[1] and tn[1]==dn[1]:
                        if dn[0]!=tn[0]+1: finding('GENERATION_REVIEW',teacher=t,disciple=d,teacher_gen=tn[0],disciple_gen=dn[0],lineage=tn[1],files=files)
                    else: finding('GENERATION_NOT_COMPARABLE',teacher=t,disciple=d,files=files)
                if tn[2] and dn[2]:
                    forward=db.execute("SELECT 1 FROM lineage_edge_assertions WHERE source_code='DILA' AND relation_type='da:isTeacherOf' AND subject_person_id=? AND object_person_id=? AND status='active' LIMIT 1",(tn[2],dn[2])).fetchone()
                    backward=db.execute("SELECT 1 FROM lineage_edge_assertions WHERE source_code='DILA' AND relation_type='da:isTeacherOf' AND subject_person_id=? AND object_person_id=? AND status='active' LIMIT 1",(dn[2],tn[2])).fetchone()
                    if backward: finding('DILA_REVERSE_REVIEW',teacher=t,disciple=d,files=files)
                    elif not forward: finding('DILA_NOT_CONFIRMED',teacher=t,disciple=d,files=files)
        # DFS chỉ giữ index cạnh nhỏ, không nạp toàn bộ nội dung TTL vào RAM.
        color={}; stack=[]
        def visit(n):
            color[n]=1; stack.append(n)
            for target in sorted(adjacency.get(n,())):
                if color.get(target)==1:
                    finding('DIRECTED_CYCLE',path=stack[stack.index(target):]+[target])
                elif not color.get(target): visit(target)
            stack.pop(); color[n]=2
        sys.setrecursionlimit(max(3000,len(nodes)*3))
        for n in sorted(set(adjacency)|{x for v in adjacency.values() for x in v}):
            if not color.get(n): visit(n)
    summary=dict(files_scanned=total,rdf_parser_available=rdflib is not None,rdf_valid=rdf_ok,main_records=idx.execute('SELECT count(*) FROM nodes').fetchone()[0],edge_assertions=idx.execute('SELECT count(*) FROM edges').fetchone()[0],findings=dict(counts),source_db_changed=False,ttl_changed=False,status='NEEDS_REVIEW',limitations=['Đối chiếu DILA từ DB local, chưa xác minh web từng người.','Ánh xạ DILA hiện có có thể sai; không tự sửa ID từ tên.','Regex sơ bộ không bảo đảm toàn bộ cú pháp Turtle.','Số đời khác không tự kết luận sai; cần cùng quy ước đếm.'])
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Audit toàn bộ TTL local','',json.dumps(summary,ensure_ascii=False,indent=2),'','Chi tiết từng phát hiện: findings.jsonl. Index truy vết file/cạnh: index.sqlite.','Không tự sửa quan hệ hoặc số đời khi chưa có bằng chứng.']
    (OUT/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    idx.close();db.close(); print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':
    try:run()
    except Exception as e:
        print('Lỗi audit TTL: '+str(e),file=sys.stderr);sys.exit(1)
