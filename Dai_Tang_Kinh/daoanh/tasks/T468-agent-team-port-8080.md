---
id: T468
title: "Bug verify: agent_team.html chet cong 8090, chuyen sang dung chung cong 8080"
status: done
created: 2026-10-26
updated: 2026-10-26
done_when:
  - "http://127.0.0.1:8080/dashboard/agent_team.html?source=real tai duoc, khong loi console"
  - "Cac API /api/real-task-status (POST) va /api/list ma trang goi tra ve 200 qua cong 8080"
  - "daoanh/admin/index.html menu 'DILA Team Agent Dashboard' tro toi http://127.0.0.1:8080/dashboard/agent_team.html?source=real"
  - "Khong con phu thuoc cong 8090 rieng; khong xoa chuc nang hien co cua serve.py"
  - "daoanh-qa xac nhan bang screenshot + network log tren browser thuc"
---

## Mo ta

### Trieu chung (Admin bao cao)
Trang `http://127.0.0.1:8090/dashboard/agent_team.html?source=real` bi chet, khong tai duoc.
Admin yeu cau: ban chat day cung la load HTML tinh giong `http://localhost:8080/dashboard/dashboard_process.html`,
nen chuyen sang dung chung cong 8080 (local_gateway) thay vi 8090 rieng.

### Bang chung ban dau (kiem tra cong, truoc khi giao debugger)
- `netstat -ano | findstr "8090 8080"`: cong 8080 dang LISTEN (PID 29460, local_gateway.py).
  Cong 8090 KHONG xuat hien trong danh sach LISTEN -> khong co tien trinh nao dang nghe o 8090,
  do do serve.py (du dinh chay rieng tren 8090) hien khong chay / da chet.
- Can debugger xac dinh chi tiet hon: serve.py co loi import/traceback gi khi chay foreground,
  hay chi la chua bao gio duoc start lai sau lan restart may/service truoc.

### File lien quan
- `Dai_Tang_Kinh/dashboard/agent_team.html`, `agent_team.css`, `agent_team.js`
- `Dai_Tang_Kinh/dashboard/serve.py` (API `/api/real-task-status` POST, `/api/list`, `/tasks/...`)
- `Dai_Tang_Kinh/local_gateway.py` (dang serve `/dashboard/*` tinh tren cong 8080, proxy `/daoanh/*` sang app.py 5000)
- `Dai_Tang_Kinh/daoanh/admin/index.html` (menu "DILA Team Agent Dashboard", T464) dang tro cung
  `http://127.0.0.1:8090/dashboard/agent_team.html?source=real`

### Muc tieu / pham vi
1. Xac dinh chinh xac nguyen nhan 8090 chet (chay serve.py foreground xem traceback, hoac xac nhan
   khong co tien trinh nao start no).
2. Chon phuong an it thay doi nhat de agent_team.html hoat dong qua cong 8080:
   - Neu API /api/real-task-status, /api/list, /tasks/ chi co trong serve.py (8090), local_gateway.py
     phai proxy cac route nay sang serve.py NOI BO (khong doi API contract cua serve.py), hoac serve.py
     tu chay nhu mot process rieng ma local_gateway proxy toi.
   - KHONG xoa chuc nang serve.py hien co, KHONG doi API hien tai.
3. Sua `daoanh/admin/index.html` de menu tro toi `http://127.0.0.1:8080/dashboard/agent_team.html?source=real`.
4. Backup cac file se sua vao `daoanh/docs/sessions/2026-10-26/` truoc khi sua.
5. Khong con phu thuoc port 8090 rieng cho luong nay (hoac neu van giu serve.py chay 8090 noi bo lam
   backend cho proxy, phai noi ro trong report va dam bao khong xung dot tien trinh khac).

### Rang buoc
- Khong git add/commit/reset.
- Khong sua dashboard_process.html, khong sua task khac.
- Dung 127.0.0.1, khong dung localhost.
- Khong de lai tien trinh 8090 chay ngam khong can thiet sau khi xac nhan xong (chi dung process cua chinh
  minh, khong anh huong tien trinh khac).
