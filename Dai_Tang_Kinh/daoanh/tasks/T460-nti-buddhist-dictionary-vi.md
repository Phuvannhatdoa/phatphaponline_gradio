---
id: T460
title: Từ điển thuật ngữ NTI (Hán–Anh–Phạn/Pāli) → lớp nghĩa Việt cho ô tra từ
status: pending
created: 2026-10-22
updated: 2026-10-22
owner: tich-hop
module: Data / Glossary
priority: low
parent: T453
plan_approved_at: "2026-10-22 (Admin phê chuẩn đề xuất: NTI thành task riêng). Ghi DB + chi phí dịch: duyệt riêng."
done_when: >
  (1) Snapshot alexamies/buddhist-dictionary data/dictionary/buddhist_terminology.txt (18.355 mục) +
      buddhist_named_entities.txt (9.003 mục) + SHA256; giấy phép dữ liệu CC BY-SA 3.0 (Fo Guang Shan / Nan Tien) — ghi công.
  (2) Đối chiếu với glossary_vi (248.095 mục, 182.666 chỉ là âm Hán Việt ghép chữ — char_hv): bao nhiêu mục NTI bổ sung nghĩa.
  (3) Cloud dịch nghĩa tiếng Anh → tiếng Việt (ngắn), giữ Phạn/Pāli/Tạng + nguồn trích; pilot 500 mục → QA → Admin duyệt.
  (4) Bảng additive mới (không ghi đè glossary_vi); source DILA≠, source_id mới NTI; badge nguồn trên UI tra từ.
  (5) daoanh-qa ĐẠT; Admin xác nhận DONE.
revert: >
  DROP bảng mới (additive).
---

# T460 — NTI Buddhist dictionary

Khảo sát 2026-10-22: repo `alexamies/buddhist-dictionary` (NTI Reader): code Apache-2.0, dữ liệu từ điển CC BY-SA 3.0.
Định dạng TSV: id, giản, phồn, pinyin, nghĩa Anh, từ loại, …, ghi chú "Sanskrit equivalent: …, Pali: …, Tibetan: … (nguồn)".
Ví dụ 乞食: "to beg for food"; Skt paiṇḍapātika; Pāli piṇḍapāta.
Repo `mbingenheimer/buddhist_studies_glossaries` (CC0): giá trị thấp (DILA person đã có; DPPN Pāli 1.360 mục có thể dùng sau).
