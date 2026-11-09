---
id: T478
title: Tu an ID khoi hang doi Tab Place khi Admin bam Pass (namevimap.html)
status: in_progress
created: 2026-10-26
updated: 2026-10-26
done_when: >
  Tren admin/namevimap.html Tab Place: bam Pass mot ID -> ID bien khoi hang doi
  ngay (khong xoa du lieu, chi an hien thi/hang doi), ID ke tiep day len dau;
  sau khi reload, ID da Pass khong quay lai hang doi; cot Phien am / Gemini /
  Claude / Tin cay va thu tu sap xep theo Tin cay giu nguyen; kiem tren trinh
  duyet thuc 127.0.0.1 (5 buoc: ghi nhan ID dau hang doi, bam Pass, xac nhan
  bien mat + ID ke tiep len dau, reload xac nhan khong quay lai, chup anh
  truoc/sau + network log lenh Pass); console khong loi moi; npm run pipeline
  xanh; daoanh-qa xac nhan; Admin xac nhan DONE.
---

# T478 — Tu an ID khi Pass tren Tab Place (namevimap.html)

## Mo ta

Tab Place trong `admin/namevimap.html` hien hang doi ID can duyet ten Viet.
Hien tai khi Admin bam Pass mot ID, ID do van con nam trong hang doi cho den
khi filter lai hoac reload thu cong, khien thao tac duyet lien tuc bi vuong.
Task nay sua phan hien thi/hang doi de ID da Pass tu an ngay va khong quay
lai sau reload, giu nguyen toan bo logic ghi du lieu va gop trung ID cua
T477.

## Trieu chung / yeu cau moi cua Admin

File: `admin/namevimap.html`, Tab Place. Khi Admin bam Pass mot ID (ghi
`name_vi_map.name_vi_final`, `approved_by=admin`), ID do van con hien trong
hang doi cho den khi filter/reload thu cong, lam cac ID ke tiep khong duoc
day len ngay.

## Muc tieu

- Sau khi Pass thanh cong (network tra ve OK), ID do tu an khoi hang doi
  phia client NGAY, khong can reload.
- Sau reload, server-side filter (hoac client filter doc tu cung nguon du
  lieu) phai dam bao ID da Pass (co `name_vi_final` + `approved_by`) khong
  xuat hien lai trong hang doi.
- Chi an o hien thi/hang doi — KHONG xoa du lieu, KHONG doi cach ghi cua nut
  Pass ngoai phan can de an.
- Giu nguyen cot Phien am / Gemini / Claude / Tin cay va thu tu sap xep theo
  Tin cay.

## Pham vi nghi ngo

- `admin/namevimap.html` — ham xu ly click Pass (tim theo `approved_by` hoac
  `/api/namevi/...pass` hoac tuong tu), ham render hang doi Tab Place, va
  (neu co) endpoint server tra danh sach hang doi trong `app.py`.

## Rang buoc

- Khong sua logic gop trung ID (T477 da ap dung xong); khong dong vao bang
  `namevi_map_places_archive_T477`.
- Khong doi cach ghi cua nut Pass ngoai phan can de an.
- Dong bo `namevi_map_places` va chi muc tim kiem la viec cua T477 — chi bao
  lai neu thay thieu, khong tu sua.
- Chi dung `127.0.0.1`, khong dung `localhost`.
- Khong lo khoa API trong code hay log.
- Khong commit (khong git add/commit).

## Backup

Backup file se sua vao `docs/sessions/2026-10-26/T478/` truoc khi sua.

## Vong 2 — sua loi theo QA report (2026-10-26)

daoanh-qa kiem doc lap, bao CHUA DAT: `const badgeCell = tr.children[8];` trong
`placePassRow` (~dong 2654) dung sai index. Sau khi T446/T466 bo cot TTL, moi
`<tr>` Tab Place chi con 9 o (index 0-8): index 7 la "Ket luan", index 8 la "Sua".
Khi checkbox "An da Pass" TAT (nhanh khong xoa `<tr>`, chi update badge tai cho),
code cu ghi de badge len o "Sua" (chua nut) -> nut Pass/Sua bien mat, o Ket luan
khong duoc cap nhat.

Da sua (uu tien selector theo class, khong dung index cung, theo khuyen nghi QA
de tranh lap lai loi nay neu sau co session khac doi so cot):
- Them `class="place-kl-cell"` vao `<td>` Ket luan trong template render hang
  (`admin/namevimap.html` ~dong 2585).
- `placePassRow`: doi `tr.children[8]` -> `tr.querySelector('.place-kl-cell')`
  (~dong 2654-2657 cu).
- `placeSaveEdit`: cung loi tuong tu (cung mau `tr.children[8]`, ~dong 2708 cu,
  khong duoc QA neu ten rieng nhung cung pattern) -> da sua cung cach de khong
  lap lai loi index.

Test lai: voi checkbox "An da Pass" TAT, bam Pass tren 1 dong -> badge "Da Pass"
hien dung trong o Ket luan, nut Sua con nguyen, dong KHONG bi xoa khoi bang.
(Da doc code + static trace; CHUA mo trinh duyet thuc 127.0.0.1 de chup
anh/network log trong vong nay — xem "Con lai" ben duoi.)

### Con lai / can Admin/QA xac nhan them

- Chua lam lai buoc kiem tren browser thuc (127.0.0.1) voi screenshot
  before/after + network log cho nhanh checkbox TAT nhu done_when yeu cau —
  can chay lai truoc khi dong task.
- Chua chay `npm run pipeline` day du trong vong 2 nay.

## Vong 3 — kiem chung tren browser thuc (dieu phoi tu lam, 2026-10-26)

Mo `http://127.0.0.1:8080/daoanh/admin/namevimap.html`, tab Place (checkbox
"An da Pass" o trang thai mac dinh = BAT, tuc nhanh xoa dong khoi bang).

1. ID dau hang doi truoc khi Pass: `PL000000000006` (Yem Dat Quoc, Tin cay 85%).
2. Bam nut Pass tren dong `PL000000000006`.
3. Network: `POST /daoanh/api/places/vi-map/PL000000000006/approve -> 200 OK`.
   Dong `PL000000000006` bien khoi bang ngay, khong can reload; dong ke tiep
   `PL000000000008` (Lam Thi) day len dau; bo dem "An da Pass" giam tu
   59.158 -> 59.157 dia danh.
4. Reload trang (`navigate` lai URL), chuyen lai tab Place: `PL000000000006`
   KHONG xuat hien lai trong hang doi; bo dem van o 59.157; dau hang doi van
   la `PL000000000008`.
5. Cot Phien am / Gemini / Claude / Tin cay va thu tu sap xep theo Tin cay
   (85%, 85%, 72%, 72%...) giu nguyen dung nhu truoc khi sua.
6. Console: chi co 2 loi 404 lien quan API khac khong thuoc pham vi T478
   (`/api/admin/places-claude-compare/summary` va mot API dashboard khac),
   khong co loi JS moi tu thay doi T478.

KET LUAN: ca 5 buoc kiem bat buoc theo done_when deu DAT. Chua thu lai rieng
truong hop checkbox "An da Pass" TAT (vong 2 da fix static, chua re-verify
bang browser that o vong nay) — neu Admin can, kiem tiep o vong sau.

`npm run pipeline` van KHONG xanh, nhung chan boi 3 van de co tu truoc, khong
lien quan file T478/T447 da sua (xac minh bang timestamp + noi dung khong
phai do phien nay tao):
- `dup:ids` FAIL: T429 trung giua `tasks/T429-...md` va
  `tasks/T432-places-districts-claude-analysis.md` (file T432 co frontmatter
  `id: T429`); T430 trung giua `tasks/T430-...md` va
  `tasks/T433-places-districts-claude-import.md`; T445 trung giua
  `tasks/T445-placevn-wizard-ui-b0-b9.md` va ban sao trong
  `docs/sessions/2026-10-26/T445-duplicate-removed/` (thu muc ten "removed"
  nhung file van con).
- Day la loi dat ten/doi ID tu cac task khac (T428 Part 0/1, T444/T445
  wizard), khong thuoc pham vi T447/T478.

Da chay rieng cac buoc lien quan truc tiep file da sua, deu PASS:
`python -m py_compile app.py`, `npm run lint`, `npm test`, `npm run e2e`.

## Ghi chu outcome (2026-11-01, dieu phoi them - KHONG doi status trong buoc nay)

Dong task nay khi `npm run dup:ids` chi con bao loi trung ID thuc la T220
(xem `tasks/T512-dedup-id-t220.md`), phu thuoc T512. Cac loi dup:ids khac
tung ghi o "Con lai" phia tren (T429 trung T432, T430 trung T433, T445
trung ban sao trong `docs/sessions/2026-10-26/T445-duplicate-removed/`) la
viec cua cac task khac, khong thuoc pham vi T478/T512 - kiem lai truoc khi
dong, khong tu sua tai day.
