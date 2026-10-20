import argparse, hashlib, json, pathlib, urllib.request, urllib.parse, datetime, sys
ROOT = pathlib.Path(__file__).resolve().parent
URL = 'https://zenodo.org/api/records/10004109'
LIMIT = 256 * 1024 * 1024
HEADERS = {'User-Agent': 'PTDA-readonly-survey/1.0 (public scholarly archive; no login)'}
def request(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != 'https' or p.hostname not in {'zenodo.org', 'www.zenodo.org'}:
        raise RuntimeError('URL host/scheme outside approved Zenodo scope: ' + url)
    response = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=25)
    final = urllib.parse.urlsplit(response.url)
    if final.scheme != 'https' or final.hostname not in {'zenodo.org', 'www.zenodo.org'}:
        response.close(); raise RuntimeError('Unexpected redirect host')
    return response
def exclusive(path, data):
    with path.open('xb') as f: f.write(data)
metadata_path = ROOT / 'record-metadata.json'
if metadata_path.exists():
    raw = metadata_path.read_bytes()
else:
    with request(URL) as response:
        raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024: raise RuntimeError('Metadata size bound exceeded')
    exclusive(metadata_path, raw)
metadata = json.loads(raw)
if metadata.get('id') != 10004109: raise RuntimeError('Record ID mismatch')
files = metadata.get('files', [])
if not files: raise RuntimeError('No record files')
print(json.dumps({'id': metadata['id'], 'license': metadata.get('metadata', {}).get('license'), 'files': [{'key': f.get('key'), 'size':f.get('size'), 'checksum':f.get('checksum')} for f in files]}, ensure_ascii=False), flush=True)
receipts = []
for entry in files:
    key = entry['key']
    if pathlib.PurePath(key).name != key or any(c in key for c in ('/', '\\', ':', '\x00')): raise RuntimeError('Unsafe filename')
    expected = int(entry['size'])
    if expected < 1 or expected > LIMIT: raise RuntimeError('File size outside bound')
    checksum = entry.get('checksum', '')
    algorithm, digest = checksum.split(':', 1)
    if algorithm not in {'md5', 'sha256'}: raise RuntimeError('Unsupported checksum')
    url = entry.get('links', {}).get('self') or entry.get('links', {}).get('download')
    if not url: raise RuntimeError('Missing download URL')
    target = ROOT / 'download' / key
    part = target.with_suffix(target.suffix + '.part')
    if target.exists() or part.exists(): raise RuntimeError('Refuse overwrite existing download')
    h = hashlib.new(algorithm); sha = hashlib.sha256(); count = 0
    with request(url) as response, part.open('xb') as output:
        response_headers = dict(response.headers.items()); final_url = response.url
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk: break
            count += len(chunk)
            if count > expected or count > LIMIT: raise RuntimeError('Download size exceeded advertised bound')
            h.update(chunk); sha.update(chunk); output.write(chunk)
    if count != expected or h.hexdigest().lower() != digest.lower(): raise RuntimeError('Download size/checksum mismatch; partial quarantined')
    part.rename(target)
    receipt = {'record_id':10004109,'key':key,'source_url':url,'final_url':final_url,'downloaded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':count,'advertised_checksum':checksum,'verified_checksum':algorithm+':'+h.hexdigest(),'sha256':sha.hexdigest(),'response_headers':response_headers,'local_path':str(target.relative_to(ROOT))}
    receipts.append(receipt)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
exclusive(ROOT / 'download-receipt.json', (json.dumps({'metadata_url':URL,'metadata_sha256':hashlib.sha256(raw).hexdigest(),'downloads':receipts}, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
