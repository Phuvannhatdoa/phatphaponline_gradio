import argparse, collections, csv, hashlib, json, pathlib, re, stat, zipfile
ROOT=pathlib.Path(__file__).resolve().parent
ARCHIVE=ROOT/'download'/'historicalNetworkAnalysisChineseReligion2023-10.zip'
EXPECTED_MD5='78c722a304d06962a12f9899d5442e3e'
def hashfile(p, algorithm='sha256'):
    h=hashlib.new(algorithm)
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()
def write_json(p, obj):
    with p.open('x', encoding='utf-8', newline='\n') as f: json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
parser=argparse.ArgumentParser();parser.add_argument('--extract',action='store_true');args=parser.parse_args()
if hashfile(ARCHIVE,'md5')!=EXPECTED_MD5: raise RuntimeError('MD5 mismatch; do not inspect or extract')
entries=[]; seen=set(); errors=[]; total=0
with zipfile.ZipFile(ARCHIVE) as z:
    infos=z.infolist()
    if len(infos)>20000: raise RuntimeError('Entry count limit exceeded')
    for info in infos:
        name=info.filename; p=pathlib.PurePosixPath(name); mode=(info.external_attr>>16)&0xffff
        reasons=[]
        if not name or '\x00' in name or '\\' in name or p.is_absolute() or any(x in {'..','.'} for x in p.parts): reasons.append('unsafe path')
        if any(':' in x or x.endswith((' ','.')) or re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',x) for x in p.parts): reasons.append('unsafe Windows component')
        key=str(p).casefold()
        if key in seen: reasons.append('case-insensitive path collision')
        seen.add(key)
        kind=stat.S_IFMT(mode)
        if kind and kind not in {stat.S_IFREG,stat.S_IFDIR}: reasons.append('symlink or special file')
        if info.flag_bits&1: reasons.append('encrypted entry')
        if info.file_size>256*1024*1024: reasons.append('entry size limit')
        if info.file_size>1024*1024 and info.file_size/max(1,info.compress_size)>2000: reasons.append('compression ratio limit')
        total+=info.file_size
        row={'path':name,'bytes':info.file_size,'compressed_bytes':info.compress_size,'crc32':f'{info.CRC:08x}','is_directory':info.is_dir(),'unix_mode':oct(mode),'suffix':p.suffix.lower(),'safety_errors':reasons}
        entries.append(row)
        if reasons: errors.append(row)
    if total>1024*1024*1024: errors.append({'path':'<archive>','safety_errors':['total uncompressed size >1 GiB']})
    summary={'archive':str(ARCHIVE.relative_to(ROOT)),'md5_verified':EXPECTED_MD5,'sha256':hashfile(ARCHIVE),'entry_count':len(entries),'file_count':sum(not x['is_directory'] for x in entries),'total_uncompressed_bytes':total,'extensions':dict(collections.Counter(x['suffix'] or '<none>' for x in entries if not x['is_directory'])),'safety_errors':errors,'entries':entries}
    inventory=ROOT/'archive-inventory.json'
    if not inventory.exists():write_json(inventory,summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='entries'},ensure_ascii=False),flush=True)
    print('\n'.join(x['path'] for x in entries),flush=True)
    if errors:raise RuntimeError('Archive failed safety gates; extraction refused')
    if args.extract:
        hashes=[]; dest=(ROOT/'extracted').resolve()
        for info in infos:
            target=dest.joinpath(*pathlib.PurePosixPath(info.filename).parts).resolve()
            if not target.is_relative_to(dest):raise RuntimeError('Containment failure')
            if info.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            target.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();count=0
            with z.open(info,'r') as source,target.open('xb') as output:
                while True:
                    chunk=source.read(1024*1024)
                    if not chunk:break
                    count+=len(chunk)
                    if count>info.file_size:raise RuntimeError('Inflated file size mismatch')
                    output.write(chunk);h.update(chunk)
            if count!=info.file_size:raise RuntimeError('Extracted size mismatch')
            hashes.append({'path':str(target.relative_to(ROOT)).replace('\\','/'),'bytes':count,'sha256':h.hexdigest()})
        write_json(ROOT/'extraction-manifest.json',{'archive_sha256':summary['sha256'],'safe_extraction':True,'files':hashes})
        print('EXTRACTION_COMPLETE '+str(len(hashes)),flush=True)
