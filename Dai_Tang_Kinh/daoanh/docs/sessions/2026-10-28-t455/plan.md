# -*- coding: utf-8 -*-
"""T455 — chuẩn hoá tên người (794 lệch + 532 sót chữ Hán)
Thực hiện theo quy trình: 
1. Phân loại 794 dong (từ file `tasks/T455-...-vi-mismatch-a001984.csv`) 
2. Tạo 3 lô (A/B/C) theo quy tắc: 
   - A: ZQ sai rõ (chữ Hán không chuẩn) → sửa thành chuẩn (ví dụ: 'Linh Hựu' → 'Quy Sơn Linh Hựu') 
   - B: alias cùng người (không sửa, ghi chú alias) 
   - C: khác quy tắc chính tả (ví dụ: Huệ→Thù, Tuệ→Thứ) → sửa đúng theo tiêu chuẩn
3. Backup DB → duyệt CSV lô → apply (UPDATE + INSERT history) → ROLLBACK → verify
4. Không tự động sửa, không thay đổi schema DB, không sửa app.py.
"""