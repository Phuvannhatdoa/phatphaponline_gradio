import collections, hashlib, json, pathlib, re
ROOT=pathlib.Path(__file__).resolve().parent
EXTRACTED=ROOT/'extracted'
rights_pattern=re.compile(r'copyright|\ball rights reserved\b|creativ[e]? commons|\bcc[- ]by\b|\blicen[cs]e\b|permission to|\bpublic domain\b|©',re.I)
name_pattern=re.compile(r'read.?me|licen[cs]e|copying|copyright|notice|rights|author|metadata|description|about',re.I)
text_suffixes={'.txt','.md','.rst','.csv','.tsv','.xml','.gexf','.graphml','.gml','.net','.html','.htm','.json','.yml','.yaml','.py','.r','.tex','.bib'}
results=[]; candidates=[]; van=[]; skipped=[]
for p in sorted(EXTRACTED.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(EXTRACTED).as_posix();size=p.stat().st_size
    if re.search(r'van.?cutsem|cutsem|zutang|ztj',rel,re.I):van.append({'path':rel,'bytes':size,'suffix':p.suffix.lower()})
    named=bool(name_pattern.search(p.name))
    if named:candidates.append({'path':rel,'bytes':size,'suffix':p.suffix.lower()})
    if p.suffix.lower() not in text_suffixes and not named:continue
    if size>64*1024*1024:skipped.append({'path':rel,'reason':'text scan size bound >64 MiB'});continue
    matches=[];lines=0;encoding='utf-8-sig'
    try:
        with p.open('r',encoding=encoding,errors='strict') as f:
            carry=''; segment=0
            while True:
                line=f.readline(64*1024)
                if not line:break
                segment+=1
                if rights_pattern.search(carry+line):matches.append({'line':lines+1,'segment':segment,'text':(carry+line).strip()[:2000]})
                if line.endswith('\n'):lines+=1;carry='';segment=0
                else:carry=line[-128:]
            if segment:lines+=1
    except UnicodeError:
        encoding='not UTF-8';skipped.append({'path':rel,'reason':'non-UTF8/binary requires explicit inspection'});continue
    if matches or named:results.append({'path':rel,'bytes':size,'encoding':encoding,'line_count':lines,'is_named_notice':named,'matches':matches})
report={'rights_filename_candidates':candidates,'rights_text_scan':results,'scan_skips':skipped,'van_cutsem_candidates':van,'policy':'Read notices in source package; metadata license does not relicense project or override scoped notices. Filename matches select candidates, not accepted identity mappings.'}
with (ROOT/'analysis'/'rights-and-file-selection.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
