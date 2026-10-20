---
id: T413
bug_id: BUG-038
title: "Bug verify: BUG-038: Trục tổ sư của Hưng Hóa Tồn Tưởng đi lên qua các thiền sư Triều Tiên — TTL Lâm Tế Nghĩa Huyền nối nhầm A032162"
status: pending
created: 2026-10-15
updated: 2026-10-15
owner: code (Hermes giao) + Admin (duyệt sửa dữ liệu)
module: TTL Thiền Sư VN
priority: critical
depends_on: []
dispatch: approved
plan_approved_at: "2026-10-15 (RC phát hiện khi dựng ví dụ cho Admin; giao theo quy trình 'bug → RC kiểm → tạo task cho Hermes' Admin chốt 2026-10-15)"
db_write: "Bước code (1–3) không ghi DB. Bước sửa mapping (4) CÓ ghi DB → chỉ làm khi Admin duyệt rõ."
done_when: >
  (1) `/daoanh/api/monk/A004980/ancestor-spine` khi chọn thầy cho mỗi bước đi lên ưu tiên cạnh nhiều nguồn
  (`confirmed_2plus`) hơn cạnh 1 nguồn (`ttl_only`/`single_source`); với A004980 phải đi lên qua A003627 (Lâm Tế 義玄, Đường)
  chứ không qua A032162 (義玄, Joseon). Cạnh 1 nguồn chỉ được dùng khi không còn cạnh nào nhiều nguồn hơn.
  (2) Mọi cạnh của ancestor-spine trả kèm `edge_color`/`source_badge`/`consensus_status` như lineage-tree (hiện spine
  trả None) — để T410 tô đúng màu/nét cho trục chính.
  (3) Kiểm trên trình duyệt thật route A004980: trục chính = Huệ Năng → … → Lâm Tế Nghĩa Huyền → Hưng Hóa Tồn Tưởng; không
  còn nút tiếng Hàn (침굉현변, 소요태능…) trên trục. Ảnh trước/sau.
  (4) [Chờ Admin duyệt, ghi DB] sửa `vn_person_authority.lam_te_nghia_huyen.dila_id` A032162 → A003627 (có backup SQLite
  API + snapshot dòng); sau đó cạnh TTL `A032162 → A004980` (ttl_only) trong lineage_edge_consensus/ assertions được rà lại.
  (5) daoanh-qa kiểm độc lập; Admin xác nhận DONE.
revert: >
  Code: git revert --no-edit <sha_T413> / bản sao docs/sessions/<ngày>/app.py.bak-before-T413.
  Dữ liệu (nếu bước 4 được duyệt): UPDATE ngược theo snapshot dòng; hoặc khôi phục backup khi server tắt.
outcome: >
  2026-10-15: RC phát hiện + đo (chỉ đọc). Chưa sửa.
---

# T413 / BUG-038 — TTL "Lâm Tế Nghĩa Huyền" nối nhầm vị sư Triều Tiên cùng tên

## Bằng chứng (RC đo 2026-10-15, chỉ đọc)

- `vn_person_authority`: `lam_te_nghia_huyen` → `dila_id = A032162`, status `auto_ttl`. A032162 trong DILA: 義玄, triều
  **朝鮮 (Joseon)**, `name_vi` "Tổ Sư", bio "枕肱懸辯弟子" — một thiền sư Triều Tiên, KHÔNG phải Lâm Tế Nghĩa Huyền (A003627, 唐).
  Còn dòng `alias_A003627` (alias_vi_suffix) → A003627.
- `lineage_edge_consensus` cho đệ tử A004980 (Hưng Hóa Tồn Tưởng):
  `A032162 → A004980` = `ttl_only` (chỉ TTL, do mapping sai) và `A003627 → A004980` = `confirmed_2plus` (DILA + Marcus).
- `/daoanh/api/monk/A004980/ancestor-spine` chọn cạnh `ttl_only` ⇒ trục tổ sư đi lên: Tổ Sư (A032162) → 침굉현변 → 소요태능 →
  Thanh Hư Hưu Tĩnh → 은암영관 → 벽송지엄 → … (thiền sư Triều Tiên), `break_reason = rejected`. Các cạnh spine trả
  `edge_color = None`.
- `/lineage-tree` tô cạnh `Tổ Sư → Tồn Tưởng` màu **xanh lá** (#22c55e, "1/4: TTL") dù chỉ 1 nguồn — trái quy tắc T410
  (1 nguồn ⇒ nét đứt).

## Hệ quả

Sau T410 (trục chính dày gấp đôi), nếu không sửa T413 thì cây sẽ **nhấn mạnh một dòng truyền thừa sai**. Nên làm T413
cùng hoặc trước T410.

## Phạm vi

Code: `app.py` hàm `api_monk_ancestor_spine` (~dòng 6773) và nơi chọn thầy chính; gắn edge_color cho cạnh spine. Không ghi DB.
Dữ liệu (bước 4): chỉ trình Admin, chưa UPDATE. Cấm: deploy, push, sửa TTL.

## Các bước

- [x] RC phát hiện + đo (2026-10-15)
- [ ] Sao lưu app.py
- [ ] Spine ưu tiên cạnh nhiều nguồn; gắn edge_color/source_badge cho cạnh spine
- [ ] Kiểm route A004980 trên trình duyệt thật, ảnh trước/sau
- [ ] Trình Admin sửa mapping lam_te_nghia_huyen → A003627 (chờ duyệt)
- [ ] daoanh-qa kiểm độc lập
- [ ] Admin xác nhận DONE
