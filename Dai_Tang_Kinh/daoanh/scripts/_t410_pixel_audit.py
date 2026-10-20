import os, glob
import numpy as np
from PIL import Image

OUT = os.path.join('docs', 'sessions', '2026-10-19')

DARK = {
    'dila': (56, 184, 248), 'marcus': (250, 204, 21), 'ttl': (220, 38, 38),
    'agree': (241, 245, 249), 'unknown': (148, 163, 184), 'conflict': (255, 123, 114),
}
LIGHT = {
    'dila': (2, 132, 199), 'marcus': (202, 138, 4), 'ttl': (185, 28, 28),
    'unknown': (100, 116, 139),
}
BANNED = {
    'old_spine_e8941a': (232, 148, 26), 'old_single_e07820': (224, 120, 32),
    'old_conf_d4a030': (212, 160, 48), 'old_cand_6b7a8a': (107, 122, 138),
    'old_purple_a855f7': (168, 85, 247), 'old_blue_3b82f6': (59, 130, 246),
    'old_yellow_eab308': (234, 179, 8), 'old_green_22c55e': (34, 197, 94),
}
TOL = 24


def count(arr, rgb, tol=TOL):
    d = np.abs(arr.astype(np.int16) - np.array(rgb, dtype=np.int16)).sum(axis=2)
    return int((d <= tol).sum())


def bbox(arr, rgb, tol=TOL):
    d = np.abs(arr.astype(np.int16) - np.array(rgb, dtype=np.int16)).sum(axis=2)
    m = d <= tol
    ys, xs = np.where(m)
    if len(xs) == 0:
        return 0, None
    return int(m.sum()), (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))


for f in sorted(glob.glob(os.path.join(OUT, 't410_*.png'))):
    im = Image.open(f).convert('RGB')
    a = np.array(im)
    h, w, _ = a.shape
    # crop CHỈ vùng canvas cây (bỏ panel trái + sidebar pháp hệ + inspector phải)
    crop = a[int(h * 0.08):int(h * 0.98), int(w * 0.50):int(w * 0.99)]
    theme = 'light' if '_light' in f else 'dark'
    pal = LIGHT if theme == 'light' else DARK
    print('==', os.path.basename(f), '(crop %dx%d)' % (crop.shape[1], crop.shape[0]), 'theme=' + theme)
    for k, v in pal.items():
        n, bb = bbox(crop, v)
        print('   NEW %-9s %-16s n=%-6d bbox=%s' % (k, str(v), n, bb))
    for k, v in BANNED.items():
        n, bb = bbox(crop, v)
        print('   OLD %-17s %-16s n=%-6d bbox=%s' % (k, str(v), n, bb))
