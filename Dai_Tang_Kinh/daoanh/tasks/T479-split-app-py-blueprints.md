---
id: T479
title: Tach app.py (26.557 dong, 1,25 MB) thanh cac Blueprint nho hon 1 MB
status: in_progress
created: 2026-10-27
updated: 2026-10-27
done_when: "app.py duoi 1 MB (CodeGraph index duoc route handler); moi route co mat sau khi tach (danh sach method + path + ten ham truoc/sau khop 100%); cac route chinh (lineage, places, ttl, T265) tra ket qua giong ban goc; npm run pipeline xanh; daoanh-qa xac nhan; Admin xac nhan DONE."
---

# T479 — Tach app.py thanh Blueprint

## Mo ta

`app.py` hien co 26.557 dong, 318 ham route, 607 ten cap module. File vuot
gioi han 1 MB cua CodeGraph nen cac handler trong file khong tra cuu duoc
bang CodeGraph; doc file cung ton token. Task nay tach route thanh cac
Blueprint nho, `app.py` chi giu vai tro diem vao.

## Phe duyet

Admin phe duyet de xuat ngay 2026-10-27: tach theo nhom route, pilot T265
truoc. Trong luc tach, opencode khong sua `app.py` va cac route trong nhom
dang tach (xem muc Khoa).

## Khoa phạm vi trong luc tach

- Khong sua `app.py` ngoai task nay.
- Task nao can sua route thuoc nhom dang tach phai xep hang sau nhom do.
- Task chi sua `admin/*.html`, `admin/*.js`, `scripts/`, `tasks/`, `docs/` van chay binh thuong.

## Tien do

- [x] Sao luu: `docs/sessions/2026-10-27/split-app/app.py.bak-before-split`
  (SHA-256 `4db9e7d2...`).
- [x] Phan tich: 318 route, 607 ten module, `app` dung 418 lan,
  `get_db_connection` 182 lan.
- [x] Cong cu doi chieu route: `docs/sessions/2026-10-27/split-app/route_inventory.py`.
- [x] **Pilot T265**: handler `import_t265_decisions` chuyen sang
  `t265_routes.py` (Blueprint `t265`); ham `get_db_connection` chuyen sang
  `db_core.py` de tranh import vong. Kiem tra: doi chieu tinh 352 = 352
  route, khong thieu/thua; runtime endpoint moi `t265.import_t265_decisions`;
  cac nhanh loi tra dung 400 (khong ghi DB).
- [x] Tach toan bo `app.py` (script `docs/sessions/2026-10-27/split-app/split.py`):
  - `core.py` (333 KB → 357 KB sau pilot): cau hinh, helper, cache, `app`, CORS, cac lenh chay luc import.
  - `routes_lineage.py`, `routes_places.py`, `routes_translate.py`, `routes_namevi.py`, `routes_ttl.py`, `routes_misc.py`, `routes_pages.py`: moi nhom mot file, moi file duoi 250 KB.
  - `app.py` bootstrap (6 KB): import core, import cac nhom route, dang ky blueprint T265, chay `__main__`.
  - `t265_routes.py` (blueprint T265) va `db_core.py` giu nguyen tu pilot.
- [x] Kiem chung:
  - Bang route tinh: 352 = 352, khong thieu, khong thua.
  - URL map runtime: 381 rule, khop 100% voi ban pilot.
  - 163 response GET: 159 giong het; 4 khac vi du lieu dong (`/api/health` timestamp, `ttl_v2/schema` tao profile moi, `public/counter` tang bo dem, `missing-hanzi` co the do DB doi).
  - Server that: `APP_PORT=5002 python app.py` khoi dong sach; lineage 200; T265 dung ma loi.
  - Ten chua dinh nghia: chi con 6 ten co san trong file goc (`_j`, `bio`, `lineage_master`, `lineage_source`, `name_vi`, `new_code`), khong them ten moi. Ghi chu: day la loi co san, chua sua de giu hanh vi.
  - CodeGraph: index 684 file, da tim thay `import_t265_decisions`.
  - Pipeline (khong gom e2e): guard OK, lint OK, test OK, t226/t227/t233 OK. Loi co san: `dup:ids` (T429/T430/T432/T433 trung), `test:t232` (test_09, khong import app.py), `test:gov` (`license_verified=1` trong `data_sources`, du lieu DB). Khong phai do viec tach.
- [ ] Khoi dong lai server 5000 de nap code moi (server dang chay ban pilot trong bo nho).
- [ ] daoanh-qa xac nhan, Admin xac nhan DONE.
- [ ] Deploy len VPS (can Admin xac nhan rieng).
- [ ] Don dep: snapshot da goi `ttl_v2/schema` nen co the con profile thua trong DB local (route ngoai pham vi tach, can quyet dinh xoa hay khong).

## Hoan tac

- Pilot T265: copy `docs/sessions/2026-10-27/split-app/app.py.bak-before-split`
  de ghi lai `app.py`, xoa `t265_routes.py` va `db_core.py`.

## Outcome

- 2026-11-01: audit cho thay app.py van la monolith, nhanh tach chua commit;
  danh lai in_progress.

## Rui ro da biet

- Bien cache toan cuc (`_LEX_EXACT`, `_CATE_IDS_CACHE`, `_HV_CACHE`,
  `_LEXICON_MEM`...) dung `global`: ham va bien phai nam cung module.
- CORS va cac hook `before_request` phai giu nguyen o `app`.
- Endpoint ten doi (`import_t265_decisions` -> `t265.import_t265_decisions`);
  hien khong co `url_for` nao tham chieu, da kiem tra.
