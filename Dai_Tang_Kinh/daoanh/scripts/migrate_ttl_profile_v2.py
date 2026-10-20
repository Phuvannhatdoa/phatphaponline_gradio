# -*- coding: utf-8 -*-
"""T226: chuyển từng file sang staging; không sửa input, DB hoặc quarantine."""
import argparse, collections, hashlib, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src_python import ttl_profile_v2 as m

def run(input_dir,output_dir,stage=False):
    source=Path(input_dir).resolve();output=Path(output_dir).resolve()
    if not source.is_dir():raise ValueError('Input không phải thư mục TTL.')
    if output==source or source in output.parents:raise ValueError('Output không được nằm trong input.')
    output.mkdir(parents=True,exist_ok=False)
    counts=collections.Counter();seen={};failures=[]
    with (output/'manifest.jsonl').open('x',encoding='utf8') as manifest:
        for file in sorted(source.glob('*.ttl')):
            raw=file.read_bytes();row={'filename':file.name,'input_sha256':hashlib.sha256(raw).hexdigest()}
            counts['files']+=1
            try:
                text=raw.decode('utf8')
                p=m.import_legacy(text,file.name)
                key=p['person']['key']
                if key in seen:raise ValueError('Trùng URI legacy với '+seen[key]+'; không gộp tự động.')
                seen[key]=file.name
                ttl,result=m.render(p);roundtrip=m.parse_v2(ttl)
                if roundtrip!=p or m.digest(roundtrip['legacy_turtle'])!=m.digest(text):raise ValueError('Roundtrip mất dữ liệu nguyên bản.')
                row.update(status='staged' if stage else 'validated',key=key,assertions=len(p['assertions']),warnings=len(result['warnings']),output_sha256=m.digest(ttl),legacy_preserved=True)
                counts['valid']+=1;counts['assertions']+=len(p['assertions'])
                if stage:
                    with (output/file.name).open('x',encoding='utf8',newline='\n') as f:f.write(ttl)
            except Exception as e:
                counts['errors']+=1;row.update(status='needs_review',error=str(e))
                if len(failures)<30:failures.append(row)
            manifest.write(json.dumps(row,ensure_ascii=False)+'\n');manifest.flush()
    summary={'profile_version':m.VERSION,'input':str(source),'stage':stage,'counts':dict(counts),'production_modified':False,'first_errors':failures}
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False))
    return 1 if counts['errors'] else 0

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--stage',action='store_true',help='Ghi file v2 vào output mới. Không apply DB.')
    args=parser.parse_args()
    try:sys.exit(run(args.input,args.output,args.stage))
    except (ValueError,OSError) as e:print('Không chuyển đổi: '+str(e),file=sys.stderr);sys.exit(2)
