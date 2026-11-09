import os
import sys

# Ghi tai cho (in-place) byte cua tmp3.index vao .git/index.
# Fallback AGENTS.md §17: git khong rename duoc trong .git/ tren may nay.
GIT_INDEX = os.path.join('.git', 'index')
TMP = sys.argv[1]

with open(TMP, 'rb') as f:
    data = f.read()
print('tmp bytes:', len(data))

with open(GIT_INDEX, 'r+b') as f:
    f.write(data)
    f.truncate(len(data))
    f.flush()
    os.fsync(f.fileno())

print('written .git/index size:', os.path.getsize(GIT_INDEX))
