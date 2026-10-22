---
id: T451
former_ids: [T445]
title: Dry-run import phien am dia danh Claude (name_vi/name_zh theo dila_id)
status: in_progress
created: 2026-10-21
updated: 2026-10-21
done_when: Script dry-run chay thanh cong, xuat CSV bao cao so lieu doi chieu
  (trung/thieu/moi/lech Gemini/tier 3-4), khong ghi gi vao DB, Admin da xem
  bao cao va quyet dinh buoc apply (ngoai pham vi task nay).
---

## Pham vi

Muc tieu: chuan bi du lieu cot "Claude" tren Tab Place
(`daoanh/admin/namevimap.html`, xem T440) hien dang trong "—", de doi chieu
voi Gemini (`ai_place_name`) va Tu dien (`namevi_map_places`).

CHI trich xuat:
- `dila_id` -> `name_vi` tu the `<place>` trong `vn_place_name_vi.xml`
- `name_zh` di kem de doi chieu

Nguon: raw GitHub
`https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/claude/sleepy-tesla-qsx17b/data/phien_am/vn_place_name_vi.xml`
Cau truc da xac nhan: `<place dila_id="PL..." tier="1|2|3|4"><name_zh>...</name_zh><name_vi>...</name_vi></place>`

## KHONG lam trong task nay

- KHONG nhap `district_vi` / `district_zh` / ten tinh huyen — de task sau
  (can task rieng vi co the anh huong bang `codex_district_name`).
- KHONG CREATE/ALTER TABLE thuc su. Chi de xuat schema trong bao cao.
- KHONG ghi DB (chi SELECT).
- KHONG `--apply`.
- KHONG sua `daoanh/admin/namevimap.html` (agent khac dang lam viec tren file nay).
- KHONG dung `daoanh/scripts/import_name_vi.py`.

## Ket qua mong doi

1. Script `daoanh/scripts/import_claude_place_name_dryrun.py` — dry-run only,
   chi SELECT tren `daoanh/data/lineage.db`.
2. CSV bao cao tai `daoanh/docs/sessions/2026-10-21/`.
3. De xuat schema bang dich (vi du `claude_place_name(dila_id PK, name_zh,
   name_vi, tier, source, imported_at)`) — chi de xuat, cho Admin duyet.
4. Ghi chu lenh rollback/backup du kien cho lan apply sau (chua can thuc
   hien vi chua ghi DB).

## Ghi chu cho task sau

- Xu ly `district_vi`/`district_zh` rieng, sau khi Admin xem xong ket qua
  name_vi/name_zh nay.
- Xem T446 (`tasks/T446-tab-place-live-compare.md`) — lam endpoint live summary
  cho Tab Place trong `admin/namevimap.html`, chay lai doi chieu nay moi khi
  mo tab thay vi doc CSV dry-run tinh.

## Next task — doi chieu quan/huyen

(Ghi nhan 2026-10-21, theo yeu cau bo sung cua Admin, van chi SELECT, khong
ghi DB, khong CREATE/ALTER.)

- `vn_place_name_vi.xml` (file dang dung cho task nay) co san thong tin
  quan/huyen ngay trong moi `<place>`: tag `district_zh` va `district_vi`.
  Da kiem: 58.765 / 59.353 entry (99,0%) co ca hai tag nay voi gia tri
  khong rong; 588 entry khong co (co the la quoc gia/khu vuc cap cao nhat,
  khong co don vi quan/huyen cha).
- Co mot file SONG SONG trong CUNG repo/path:
  `https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/claude/sleepy-tesla-qsx17b/data/phien_am/vn_district_name_vi.xml`
  (da fetch thu, HTTP 200, ~2,3MB). Root tag `vn_district_authority_name_vi`,
  attribute `units="16907"`, cau truc `<unit dila_id="PLA..." type="country"
  tier="1"><name_zh>...</name_zh>...</unit>` — dung PREFIX ID RIENG
  ("PLA...", khong phai "PL...") danh cho don vi hanh chinh (quoc gia/
  tinh/huyen), khac voi dila_id cua dia danh ("PL...").
- So don vi trong `vn_district_name_vi.xml` (16.907) KHOP CHINH XAC voi so
  dong hien co trong bang `codex_district_name` (16.907 dong, status=
  'suggested', theo bao cao dry-run T445). Rat co kha nang
  `codex_district_name` da duoc import TU chinh file nay truoc do.
- Bang dich cho viec doi chieu/import quan huyen sau nay la
  `codex_district_name` (DA CO, 16.907 dong) — KHONG phai bang `places`
  hay `places_dila` (do la dia danh, khong phai don vi hanh chinh).
- Task sau (chua lam o day) can: doi chieu `district_zh`/`district_vi`
  trong tung `<place>` cua `vn_place_name_vi.xml` voi `name_zh`/`name_vi`
  trong `vn_district_name_vi.xml` (hoac `codex_district_name`) qua
  chuoi ten (vi "PLA..." khong xuat hien truc tiep trong tag `<place>`,
  chi co chuoi ten quan/huyen dang text, can map theo string match, KHONG
  dung ID lam join key truc tiep — xem quy tac "stable identity" trong
  CLAUDE.md/AGENTS.md).
