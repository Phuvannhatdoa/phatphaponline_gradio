---
id: T469
title: Homepage search autocomplete (grouped: Nhan vat / Kinh sach-Dich gia)
status: in_progress
created: 2026-10-26
updated: 2026-10-26
done_when:
  - Go o tim kiem trang chu (daoanh/index.html, http://127.0.0.1:8080/daoanh/) hien goi y khi go, chia 2 nhom "Nhan vat" va "Kinh sach / Dich gia"
  - Nhom Kinh sach hien dung dich gia (tu truong co san hoac JOIN dila_catalog_contributors/dila_catalog_works, co ghi ro cach lay trong report)
  - Moi dong goi y co phu chu phan biet (era/ID DILA/ten Han) khi trung ten (vd Huyen Trang: 4 monks A000294/A002949/A009306/A014708 + 2 works)
  - Endpoint moi /daoanh/api/search/suggest (khong doi format /daoanh/api/search hien co), limit <=8/nhom, debounce ~250ms, bo qua khi <2 ky tu, nhan dien co dau/khong dau
  - Thoi gian phan hoi do duoc (muc tieu <1s khi da am), co EXPLAIN QUERY PLAN kiem tra khong full scan; neu can index moi phai hoi Admin truoc, khong tu tao
  - UI dropdown dung theme hien tai (Amber Gold #d97706 / Dark Slate #020617, Inter + Noto Serif TC), ho tro mui ten len/xuong, Enter chon, Esc dong, click ngoai dong, click dong di dung trang
  - Test browser thuc te tai 127.0.0.1:8080/daoanh/: "Huyen Trang" (ca 2 nhom), "Khuy Co" (nhan vat), "Long Mon" (dia danh, van chay nhu cu qua nut Tim/Enter), console khong loi JS, co screenshot + network log + thoi gian do
  - Backup index.html va app.py vao docs/sessions/2026-10-26/ truoc khi sua; py_compile va lint-check pass
  - Khong hoi quy tim kiem hien co (nut Tim, Enter, trang dia danh)
---

## Mo ta

Them autocomplete cho o tim kiem trang chu Dao Anh. Hien tai chi tra cuu khi bam "Tim" hoac Enter;
Admin yeu cau goi y hien ngay khi go, chia 2 nhom vi mot nguoi co the vua la nhan vat vua la dich gia
(vd Huyen Trang la tang nhan VA la dich gia kinh).

Yeu cau chi tiet tu Admin (2026-10-26):

1. Doc daoanh/index.html (ham search da sua T467) va app.py api_global_search (~dong 13173).
   KHONG doi format JSON /daoanh/api/search hien co (trang khac dang dung). Neu can them du lieu,
   tao endpoint moi /daoanh/api/search/suggest tra nhom persons va works kem dich gia.
2. Xac dinh works co truong translator san co hay phai JOIN dila_catalog_contributors / dila_catalog_works
   (da nhac trong T467).
3. Endpoint suggest: limit toi da 8/nhom, debounce ~250ms phia client, khong goi khi <2 ky tu,
   nhan dien co dau/khong dau (tai dung logic chuan hoa hien co). Do thoi gian phan hoi (muc tieu <1s).
   Kiem EXPLAIN QUERY PLAN, dung index san co hoac FTS neu can; neu can index moi (thay doi schema)
   phai hoi Admin truoc, khong tu tao/ALTER/CREATE INDEX.
4. UI: dropdown duoi o tim kiem, 2 tieu de "Nhan vat" va "Kinh sach / Dich gia", moi dong co ten +
   phu chu phan biet (era/ID DILA/ten Han) vi ten trung (Huyen Trang: 4 monks A000294/A002949/A009306/
   A014708 + 2 works "Dai Duong Co Tam Tang Huyen Trang" / "Tu Sa Mon Huyen Trang Thuong Bieu Ky").
   Bam mot dong di toi trang nhan vat hoac kinh sach tuong ung (dung URL hien co). Ho tro mui ten
   len/xuong + Enter chon, Esc dong, click ngoai dong. Giu dung mau/font trang chu (Amber Gold
   #d97706 / Dark Slate #020617, Inter + Noto Serif TC), khong doi UI khac.
5. Test tren trinh duyet thuc te (127.0.0.1:8080/daoanh/, KHONG dung localhost):
   - "Huyen Trang" go tung ky tu, chup screenshot dropdown, network log request suggest, do thoi gian
   - "Khuy Co" (phai co nhan vat)
   - "Long Mon" (dia danh, van chay nhu cu)
   - Enter / nut Tim van hoat dong nhu truoc (khong hoi quy)
   - Console khong loi JS
6. Backup daoanh/index.html va daoanh/app.py vao daoanh/docs/sessions/2026-10-26/ truoc khi sua.
   Sau khi sua: python -X utf8 -m py_compile app.py va node scripts/lint-check.js (chay tu daoanh/).
7. Rang buoc cung: khong ghi DB, khong CREATE/ALTER/rebuild index khi chua hoi Admin, khong
   git add/commit/reset, khong sua dashboard hay task khac ngoai pham vi nay.

## Bao cao can co

- Cach lay dich gia: truong san co hay JOIN (neu JOIN, neu ro bang/cot)
- Endpoint da them/sua (duong dan, method, response shape)
- Thoi gian phan hoi do duoc (truoc/sau khi am)
- Bang chung trinh duyet: screenshot, network log, console
- Cac case da kiem + hoi quy
- Diem can Admin quyet (vd them index moi)
