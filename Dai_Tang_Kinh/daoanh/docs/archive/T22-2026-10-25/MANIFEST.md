# MANIFEST — T22 code archive (2026-10-25)

> Bản `manifest.json` cùng nội dung nằm cạnh file này nhưng **bị `.gitignore:6` (`*.json`) bỏ qua**;
> file `.md` này là bản được commit để giữ hash. Sinh tự động — đừng sửa tay.

**Ngày lưu trữ:** 2026-10-25

**Quyết định:** Admin 2026-10-25: dung toan bo code T22; T22 tro thanh du an tuong lai (tim repo/cong trinh tuong duong de tich hop), khong dung code cu.

**Số file:** 7

| # | File gốc (đã rời `scripts/`) | Nơi lưu | Byte | SHA256 | Move OK |
|---|---|---|---:|---|---|
| 1 | `scripts/t22_ld1_fix_era_name_founding.py` | `docs/archive/T22-2026-10-25/scripts/t22_ld1_fix_era_name_founding.py` | 20,831 | `1b676ef9efcee517d6bb92803c95aea415cdb4245c4225bbbfea37b5e9a7b152` | ✅ |
| 2 | `scripts/t22_ld2_dynasty_era_lookup.py` | `docs/archive/T22-2026-10-25/scripts/t22_ld2_dynasty_era_lookup.py` | 27,575 | `e3882b648c0deee768d18c3b3558d4b46db8a783e4bb00e478b11ecb5e265cb2` | ✅ |
| 3 | `scripts/t22_ld3_review_remaining.py` | `docs/archive/T22-2026-10-25/scripts/t22_ld3_review_remaining.py` | 6,032 | `c48dd98d2fafb5f2b571988d539cf693846dc237091cea32d2ac4ef99eac1595` | ✅ |
| 4 | `scripts/t80_founding_coverage.py` | `docs/archive/T22-2026-10-25/scripts/t80_founding_coverage.py` | 7,735 | `5d2aa7c91f635e9cd71c220b71b6b976e8af5e7ff017ae897a153f32cdcff82b` | ✅ |
| 5 | `scripts/dila_note_founding_extract.py` | `docs/archive/T22-2026-10-25/scripts/dila_note_founding_extract.py` | 23,127 | `065ec87a1529dbfb179c86e9f36676980564c4d5a4652ef086c6dc9fc69e3c7a` | ✅ |
| 6 | `scripts/dila_dynasty_range_extract.py` | `docs/archive/T22-2026-10-25/scripts/dila_dynasty_range_extract.py` | 9,797 | `ee75ade443153fc917e7fbc04f5fdcdb10eecd7100efd20227844e2ec53321ce` | ✅ |
| 7 | `scripts/t22d_regex_dila_notes.py` | `docs/archive/T22-2026-10-25/scripts/t22d_regex_dila_notes.py` | 7,038 | `d4687a1afb57c64b56cb4e1d4d7675b0c00067014f3862d40f2be536ecd440e0` | ✅ |

## Cách verify lại

```powershell
cd "E:\...\visjs-app\Dai_Tang_Kinh\daoanh"
python -X utf8 -c "import json,hashlib,os;m=json.load(open('docs/archive/T22-2026-10-25/manifest.json',encoding='utf-8'));print([(os.path.basename(x['archived_as']), hashlib.sha256(open(os.path.join('docs/archive/T22-2026-10-25/scripts',os.path.basename(x['archived_as'])),'rb').read()).hexdigest()==x['sha256']) for x in m['files']])"
```

Kỳ vọng: 7 × `True`.

