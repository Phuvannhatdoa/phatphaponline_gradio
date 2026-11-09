import re, sys
src = open(sys.argv[1], encoding='utf-8').read()
blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', src, re.S)
open(sys.argv[2], 'w', encoding='utf-8').write('\n;\n'.join(blocks))
print('blocks', len(blocks))
