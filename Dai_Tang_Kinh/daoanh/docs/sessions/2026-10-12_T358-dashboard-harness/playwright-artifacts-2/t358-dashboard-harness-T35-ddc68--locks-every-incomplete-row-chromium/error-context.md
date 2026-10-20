# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: t358-dashboard-harness.spec.js >> T358 actual source is integrated; audited report locks every incomplete row
- Location: tests\t358-dashboard-harness.spec.js:51:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('#triageMessage')
Expected substring: "Báo cáo đã tải"
Received string:    "BÃ¡o cÃ¡o Ä‘Ã£ táº£i. DONE khÃ³a cho má»i dÃ²ng cÃ²n thiáº¿u Ä‘iá»u kiá»‡n dev; local review khÃ´ng Ä‘Ã³ng task."
Timeout: 5000ms

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('#triageMessage')
    8 × locator resolved to <p role="status" id="triageMessage" aria-live="polite">BÃ¡o cÃ¡o Ä‘Ã£ táº£i. DONE khÃ³a cho má»i dÃ²ng …</p>
      - unexpected value "BÃ¡o cÃ¡o Ä‘Ã£ táº£i. DONE khÃ³a cho má»i dÃ²ng cÃ²n thiáº¿u Ä‘iá»u kiá»‡n dev; local review khÃ´ng Ä‘Ã³ng task."

```

# Page snapshot

```yaml
- region "Triage / Execution â€” T358" [ref=e2]:
  - generic [ref=e3]:
    - heading "Triage / Execution â€” T358" [level=2] [ref=e4]
    - button "Táº£i láº¡i bÃ¡o cÃ¡o" [ref=e5]
  - paragraph [ref=e6]: DONE chá»‰ xÃ¡c nháºn Admin Ä‘Ã£ review trÃªn trÃ¬nh duyá»‡t nÃ y. NÃºt chá»‰ má»Ÿ khi dev cÃ³ Ä‘á»§ báº£n sá»a, tests vÃ QA Ä‘á»™c láºp; khÃ´ng Ä‘á»•i tráº¡ng thÃ¡i task hoáº·c dá»¯ liá»‡u production.
  - paragraph [ref=e7]: "Audit: 2026-10-12 (+07:00) Â· 2026-10-12-r1 Â· CÃ¡c báº±ng chá»©ng nÃ y lÃ snapshot, khÃ´ng pháº£i kiá»ƒm production má»›i."
  - status [ref=e8]: "BÃ¡o cÃ¡o Ä‘Ã£ táº£i. DONE khÃ³a cho má»\x8di dÃ²ng cÃ²n thiáº¿u Ä‘iá»\x81u kiá»‡n dev; local review khÃ´ng Ä‘Ã³ng task."
  - generic "Thá»© tá»± triá»ƒn khai" [ref=e9]:
    - generic [ref=e10]: "Ưu tiên: T283 → T284 / T290"
    - generic [ref=e11]: "Cổng writer: T287 → T288"
    - generic [ref=e12]: "Song song: T319 · T322 · T323 · T81 · T277 / T328"
  - region "BÃ¡o cÃ¡o triage vÃ thá»±c thi; cuá»™n ngang Ä‘á»ƒ xem Ä‘á»§ cá»™t" [ref=e13]:
    - 'table "Task, chuyÃªn mÃ´n agent, Ä‘iá»u kiá»‡n vÃ hÃ nh Ä‘á»™ng cá»§a Admin" [ref=e14]':
      - caption [ref=e15]: "Task, chuyÃªn mÃ´n agent, Ä‘iá»\x81u kiá»‡n vÃ hÃ nh Ä‘á»™ng cá»§a Admin"
      - rowgroup [ref=e16]:
        - 'row "Task / nhÃ³m Agent Äiá»u kiá»‡n trÆ°á»›c Dev / báº±ng chá»©ng Admin lÃ m tiáº¿p Review" [ref=e17]':
          - columnheader "Task / nhÃ³m" [ref=e18]
          - columnheader "Agent" [ref=e19]
          - 'columnheader "Äiá»u kiá»‡n trÆ°á»›c" [ref=e20]'
          - columnheader "Dev / báº±ng chá»©ng" [ref=e21]
          - columnheader "Admin lÃ m tiáº¿p" [ref=e22]
          - columnheader "Review" [ref=e23]
      - rowgroup [ref=e24]:
        - 'row "T283 — Dọn chuỗi key trong docs/scripts T283: pending Task T283 Code bảo mật; Debug kiểm độc lập KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA. Scan local chỉ tên file: 6 đường dẫn còn match; task cũ ghi 18. Chưa redact, không hiển thị chuỗi bí mật. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA Scope T283 §29–37 Ưu tiên đầu tiên: giao redact 6 file theo diff/backup; kiểm scan không còn match. Việc revoke key cần Admin riêng, không suy từ redact. DONE review T283 — Dọn chuỗi key trong docs/scripts Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e25]':
          - 'rowheader "T283 — Dọn chuỗi key trong docs/scripts T283: pending Task T283" [ref=e26]':
            - strong [ref=e27]: T283 — Dọn chuỗi key trong docs/scripts
            - generic [ref=e28]: "T283: pending"
            - link "Task T283" [ref=e30] [cursor=pointer]:
              - /url: ../tasks/T283-m0-xoa-key-khoi-tai-lieu.md
          - cell "Code bảo mật; Debug kiểm độc lập" [ref=e31]
          - cell "KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA." [ref=e32]
          - 'cell "Scan local chỉ tên file: 6 đường dẫn còn match; task cũ ghi 18. Chưa redact, không hiển thị chuỗi bí mật. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA Scope T283 §29–37" [ref=e33]':
            - paragraph [ref=e34]: "Scan local chỉ tên file: 6 đường dẫn còn match; task cũ ghi 18. Chưa redact, không hiển thị chuỗi bí mật."
            - list [ref=e35]:
              - listitem [ref=e36]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e37]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e38]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - link "Scope T283 §29–37" [ref=e40] [cursor=pointer]:
              - /url: ../tasks/T283-m0-xoa-key-khoi-tai-lieu.md
          - 'cell "Ưu tiên đầu tiên: giao redact 6 file theo diff/backup; kiểm scan không còn match. Việc revoke key cần Admin riêng, không suy từ redact." [ref=e41]'
          - cell "DONE review T283 — Dọn chuỗi key trong docs/scripts Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e42]:
            - button "DONE review T283 — Dọn chuỗi key trong docs/scripts" [disabled] [ref=e43]: DONE
            - generic [ref=e44]: Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t.
        - 'row "T284 — Nạp AGENTS trong CLAUDE.md T284: pending Task T284 Code tài liệu; Debug kiểm link â—‹ T283 đã redact và QA CLAUDE.md khoảng 98 dòng, thiếu @AGENTS.md. Chưa bổ sung. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T284: scope và phụ thuộc Sau T283: thêm directive, giữ nội dung; kiểm một directive hợp lệ và links. DONE review T284 — Nạp AGENTS trong CLAUDE.md ChÆ°a Ä‘á»§ Ä‘iá»u kiá»‡n trÆ°á»›c." [ref=e45]':
          - 'rowheader "T284 — Nạp AGENTS trong CLAUDE.md T284: pending Task T284" [ref=e46]':
            - strong [ref=e47]: T284 — Nạp AGENTS trong CLAUDE.md
            - generic [ref=e48]: "T284: pending"
            - link "Task T284" [ref=e50] [cursor=pointer]:
              - /url: ../tasks/T284-m0-agents-md-trong-claude-md.md
          - cell "Code tài liệu; Debug kiểm link" [ref=e51]
          - cell "â—‹ T283 đã redact và QA" [ref=e52]:
            - generic [ref=e53]: â—‹ T283 đã redact và QA
          - 'cell "CLAUDE.md khoảng 98 dòng, thiếu @AGENTS.md. Chưa bổ sung. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T284: scope và phụ thuộc" [ref=e54]':
            - paragraph [ref=e55]: CLAUDE.md khoảng 98 dòng, thiếu @AGENTS.md. Chưa bổ sung.
            - list [ref=e56]:
              - listitem [ref=e57]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e58]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e59]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - 'link "T284: scope và phụ thuộc" [ref=e61] [cursor=pointer]':
              - /url: ../tasks/T284-m0-agents-md-trong-claude-md.md
          - 'cell "Sau T283: thêm directive, giữ nội dung; kiểm một directive hợp lệ và links." [ref=e62]'
          - 'cell "DONE review T284 — Nạp AGENTS trong CLAUDE.md ChÆ°a Ä‘á»§ Ä‘iá»u kiá»‡n trÆ°á»›c." [ref=e63]':
            - button "DONE review T284 — Nạp AGENTS trong CLAUDE.md" [disabled] [ref=e64]: DONE
            - generic [ref=e65]: "ChÆ°a Ä‘á»§ Ä‘iá»\x81u kiá»‡n trÆ°á»›c."
        - 'row "T290 — Sinh credits từ registry T290: pending Task T290 Code generator; Debug fixtures â—‹ T283 đã redact và QA credits.html còn tĩnh. Registry metadata không chứng minh quyền pháp lý; chưa có generator/test. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T290 Reality check Sau T283: giao generator read-only với fixture; đánh dấu license chưa rõ, không tự xác nhận quyền. DONE review T290 — Sinh credits từ registry ChÆ°a Ä‘á»§ Ä‘iá»u kiá»‡n trÆ°á»›c." [ref=e66]':
          - 'rowheader "T290 — Sinh credits từ registry T290: pending Task T290" [ref=e67]':
            - strong [ref=e68]: T290 — Sinh credits từ registry
            - generic [ref=e69]: "T290: pending"
            - link "Task T290" [ref=e71] [cursor=pointer]:
              - /url: ../tasks/T290-m5-credits-tu-data-sources.md
          - cell "Code generator; Debug fixtures" [ref=e72]
          - cell "â—‹ T283 đã redact và QA" [ref=e73]:
            - generic [ref=e74]: â—‹ T283 đã redact và QA
          - 'cell "credits.html còn tĩnh. Registry metadata không chứng minh quyền pháp lý; chưa có generator/test. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T290 Reality check" [ref=e75]':
            - paragraph [ref=e76]: credits.html còn tĩnh. Registry metadata không chứng minh quyền pháp lý; chưa có generator/test.
            - list [ref=e77]:
              - listitem [ref=e78]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e79]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e80]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - link "T290" [ref=e82] [cursor=pointer]:
              - /url: ../tasks/T290-m5-credits-tu-data-sources.md
            - link "Reality check" [ref=e84] [cursor=pointer]:
              - /url: ../docs/integration/REALITY_CHECK.md
          - 'cell "Sau T283: giao generator read-only với fixture; đánh dấu license chưa rõ, không tự xác nhận quyền." [ref=e85]'
          - 'cell "DONE review T290 — Sinh credits từ registry ChÆ°a Ä‘á»§ Ä‘iá»u kiá»‡n trÆ°á»›c." [ref=e86]':
            - button "DONE review T290 — Sinh credits từ registry" [disabled] [ref=e87]: DONE
            - generic [ref=e88]: "ChÆ°a Ä‘á»§ Ä‘iá»\x81u kiá»‡n trÆ°á»›c."
        - 'row "T287 — Nối gate đúng writer T287: pending Task T287 Code ETL; Debug fault tests âœ“ T231 gate đã wired; trạng thái done trong task wire_evidence_into_entity_claims là writer chưa gate; etl_entity_claims fail-open khi ImportError. etl_t109_provenance chỉ sinh audit, không phải writer entity_claims. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA Writer: §31–51, §207–217 Fail-open: §25–36 Audit-only: §125–145 Giao sửa gate fail-closed trên fixture, không chạy apply production; chỉnh premise task trước build. DONE review T287 — Nối gate đúng writer Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e89]':
          - 'rowheader "T287 — Nối gate đúng writer T287: pending Task T287" [ref=e90]':
            - strong [ref=e91]: T287 — Nối gate đúng writer
            - generic [ref=e92]: "T287: pending"
            - link "Task T287" [ref=e94] [cursor=pointer]:
              - /url: ../tasks/T287-m1-noi-gate-etl-con-lai.md
          - cell "Code ETL; Debug fault tests" [ref=e95]
          - cell "âœ“ T231 gate đã wired; trạng thái done trong task" [ref=e96]:
            - generic [ref=e97]: âœ“ T231 gate đã wired; trạng thái done trong task
          - 'cell "wire_evidence_into_entity_claims là writer chưa gate; etl_entity_claims fail-open khi ImportError. etl_t109_provenance chỉ sinh audit, không phải writer entity_claims. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA Writer: §31–51, §207–217 Fail-open: §25–36 Audit-only: §125–145" [ref=e98]':
            - paragraph [ref=e99]: wire_evidence_into_entity_claims là writer chưa gate; etl_entity_claims fail-open khi ImportError. etl_t109_provenance chỉ sinh audit, không phải writer entity_claims.
            - list [ref=e100]:
              - listitem [ref=e101]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e102]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e103]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - 'link "Writer: §31–51, §207–217" [ref=e105] [cursor=pointer]':
              - /url: ../scripts/wire_evidence_into_entity_claims.py
            - 'link "Fail-open: §25–36" [ref=e107] [cursor=pointer]':
              - /url: ../scripts/etl_entity_claims.py
            - 'link "Audit-only: §125–145" [ref=e109] [cursor=pointer]':
              - /url: ../scripts/etl_t109_provenance.py
          - cell "Giao sửa gate fail-closed trên fixture, không chạy apply production; chỉnh premise task trước build." [ref=e110]
          - cell "DONE review T287 — Nối gate đúng writer Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e111]:
            - button "DONE review T287 — Nối gate đúng writer" [disabled] [ref=e112]: DONE
            - generic [ref=e113]: Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t.
        - 'row "T288 — Acceptance cổng bằng fixture T288: pending Task T288 Debug fixtures; Code sửa khi được giao â—‹ T287 build + QA hoàn tất Chưa kiểm acceptance hiện hành. Snapshot/count lịch sử không thay thế chứng minh writer bị chặn. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T288 acceptance Sau T287: fixture BLOCKED/LEGACY + gate lỗi/import lỗi; so mọi rowset trước/sau, đòi zero-write khi bị chặn. DONE review T288 — Acceptance cổng bằng fixture ChÆ°a Ä‘á»§ Ä‘iá»u kiá»‡n trÆ°á»›c." [ref=e114]':
          - 'rowheader "T288 — Acceptance cổng bằng fixture T288: pending Task T288" [ref=e115]':
            - strong [ref=e116]: T288 — Acceptance cổng bằng fixture
            - generic [ref=e117]: "T288: pending"
            - link "Task T288" [ref=e119] [cursor=pointer]:
              - /url: ../tasks/T288-m1-kiem-acceptance-cong.md
          - cell "Debug fixtures; Code sửa khi được giao" [ref=e120]
          - cell "â—‹ T287 build + QA hoàn tất" [ref=e121]:
            - generic [ref=e122]: â—‹ T287 build + QA hoàn tất
          - 'cell "Chưa kiểm acceptance hiện hành. Snapshot/count lịch sử không thay thế chứng minh writer bị chặn. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T288 acceptance" [ref=e123]':
            - paragraph [ref=e124]: Chưa kiểm acceptance hiện hành. Snapshot/count lịch sử không thay thế chứng minh writer bị chặn.
            - list [ref=e125]:
              - listitem [ref=e126]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e127]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e128]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - link "T288 acceptance" [ref=e130] [cursor=pointer]:
              - /url: ../tasks/T288-m1-kiem-acceptance-cong.md
          - 'cell "Sau T287: fixture BLOCKED/LEGACY + gate lỗi/import lỗi; so mọi rowset trước/sau, đòi zero-write khi bị chặn." [ref=e131]'
          - 'cell "DONE review T288 — Acceptance cổng bằng fixture ChÆ°a Ä‘á»§ Ä‘iá»u kiá»‡n trÆ°á»›c." [ref=e132]':
            - button "DONE review T288 — Acceptance cổng bằng fixture" [disabled] [ref=e133]: DONE
            - generic [ref=e134]: "ChÆ°a Ä‘á»§ Ä‘iá»\x81u kiá»‡n trÆ°á»›c."
        - 'row "T319 — Inventory API thật T319: pending Task T319 Code AST; Debug fixture KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA. Generator hiện regex app.route, bỏ sót Blueprint; 319 là snapshot regex, không phải inventory hoàn chỉnh. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA Scanner §170–195 T319 Chạy song song: static AST + Blueprint fixture; không import app, không gọi API hay scan corpus. DONE review T319 — Inventory API thật Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e135]':
          - 'rowheader "T319 — Inventory API thật T319: pending Task T319" [ref=e136]':
            - strong [ref=e137]: T319 — Inventory API thật
            - generic [ref=e138]: "T319: pending"
            - link "Task T319" [ref=e140] [cursor=pointer]:
              - /url: ../tasks/T319-arch-m16-route-api-that.md
          - cell "Code AST; Debug fixture" [ref=e141]
          - cell "KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA." [ref=e142]
          - 'cell "Generator hiện regex app.route, bỏ sót Blueprint; 319 là snapshot regex, không phải inventory hoàn chỉnh. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA Scanner §170–195 T319" [ref=e143]':
            - paragraph [ref=e144]: Generator hiện regex app.route, bỏ sót Blueprint; 319 là snapshot regex, không phải inventory hoàn chỉnh.
            - list [ref=e145]:
              - listitem [ref=e146]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e147]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e148]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - link "Scanner §170–195" [ref=e150] [cursor=pointer]:
              - /url: ../scripts/build_progress_data.py
            - link "T319" [ref=e152] [cursor=pointer]:
              - /url: ../tasks/T319-arch-m16-route-api-that.md
          - 'cell "Chạy song song: static AST + Blueprint fixture; không import app, không gọi API hay scan corpus." [ref=e153]'
          - cell "DONE review T319 — Inventory API thật Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e154]:
            - button "DONE review T319 — Inventory API thật" [disabled] [ref=e155]: DONE
            - generic [ref=e156]: Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t.
        - 'row "T322 — Sửa reality/plan drift T322: pending Task T322 Code docs; Debug đối chiếu âœ“ T231 done; sources UI/API có trong code REALITY_CHECK/00_PLAN còn nói chưa gate/chưa sources page; T231 done và admin/sources.html đã có. Chưa cập nhật docs. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA Claims cũ §90,95 Claim cũ §32 Sources UI hiện có Chạy song song: sửa các claim với file:line/date; giữ lịch sử và phân tách chưa verify runtime. DONE review T322 — Sửa reality/plan drift Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e157]':
          - 'rowheader "T322 — Sửa reality/plan drift T322: pending Task T322" [ref=e158]':
            - strong [ref=e159]: T322 — Sửa reality/plan drift
            - generic [ref=e160]: "T322: pending"
            - link "Task T322" [ref=e162] [cursor=pointer]:
              - /url: ../tasks/T322-docs-cap-nhat-reality-check-plan.md
          - cell "Code docs; Debug đối chiếu" [ref=e163]
          - cell "âœ“ T231 done; sources UI/API có trong code" [ref=e164]:
            - generic [ref=e165]: âœ“ T231 done; sources UI/API có trong code
          - 'cell "REALITY_CHECK/00_PLAN còn nói chưa gate/chưa sources page; T231 done và admin/sources.html đã có. Chưa cập nhật docs. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA Claims cũ §90,95 Claim cũ §32 Sources UI hiện có" [ref=e166]':
            - paragraph [ref=e167]: REALITY_CHECK/00_PLAN còn nói chưa gate/chưa sources page; T231 done và admin/sources.html đã có. Chưa cập nhật docs.
            - list [ref=e168]:
              - listitem [ref=e169]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e170]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e171]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - link "Claims cũ §90,95" [ref=e173] [cursor=pointer]:
              - /url: ../docs/integration/REALITY_CHECK.md
            - link "Claim cũ §32" [ref=e175] [cursor=pointer]:
              - /url: ../docs/integration/00_PLAN_OVERVIEW.md
            - link "Sources UI hiện có" [ref=e177] [cursor=pointer]:
              - /url: ../admin/sources.html
          - 'cell "Chạy song song: sửa các claim với file:line/date; giữ lịch sử và phân tách chưa verify runtime." [ref=e178]'
          - cell "DONE review T322 — Sửa reality/plan drift Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e179]:
            - button "DONE review T322 — Sửa reality/plan drift" [disabled] [ref=e180]: DONE
            - generic [ref=e181]: Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t.
        - 'row "T323 — Đối chiếu search spec T323: pending Task T323 Code docs/search; Debug tests KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA. M17 thiếu link T260 đúng; 90/70/80/200 ms là mục tiêu chưa đo, không được ghi như benchmark PASS. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA M17 §23–31 T323 Chạy song song: sửa link/nhãn target và mô tả code; benchmark chỉ fixture/local, không mở rộng NLP/corpus. DONE review T323 — Đối chiếu search spec Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e182]':
          - 'rowheader "T323 — Đối chiếu search spec T323: pending Task T323" [ref=e183]':
            - strong [ref=e184]: T323 — Đối chiếu search spec
            - generic [ref=e185]: "T323: pending"
            - link "Task T323" [ref=e187] [cursor=pointer]:
              - /url: ../tasks/T323-m17-search-optimization.md
          - cell "Code docs/search; Debug tests" [ref=e188]
          - cell "KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA." [ref=e189]
          - 'cell "M17 thiếu link T260 đúng; 90/70/80/200 ms là mục tiêu chưa đo, không được ghi như benchmark PASS. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA M17 §23–31 T323" [ref=e190]':
            - paragraph [ref=e191]: M17 thiếu link T260 đúng; 90/70/80/200 ms là mục tiêu chưa đo, không được ghi như benchmark PASS.
            - list [ref=e192]:
              - listitem [ref=e193]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e194]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e195]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - link "M17 §23–31" [ref=e197] [cursor=pointer]:
              - /url: ../docs/integration/M17-search-optimization.md
            - link "T323" [ref=e199] [cursor=pointer]:
              - /url: ../tasks/T323-m17-search-optimization.md
          - 'cell "Chạy song song: sửa link/nhãn target và mô tả code; benchmark chỉ fixture/local, không mở rộng NLP/corpus." [ref=e200]'
          - cell "DONE review T323 — Đối chiếu search spec Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e201]:
            - button "DONE review T323 — Đối chiếu search spec" [disabled] [ref=e202]: DONE
            - generic [ref=e203]: Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t.
        - 'row "T81 — QA ẩn DONE trên board T81: in_progress Task T81 Debug UI; Code nếu có lỗi KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA. Board đã lọc pending/in_progress/blocked và có localStorage; thiếu acceptance UI cô lập. Không coi code tồn tại là task DONE. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T81 §23–33 Chạy song song: test filter/reload/localStorage + keyboard; chỉ giao sửa khi tái hiện defect. DONE review T81 — QA ẩn DONE trên board Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e204]':
          - 'rowheader "T81 — QA ẩn DONE trên board T81: in_progress Task T81" [ref=e205]':
            - strong [ref=e206]: T81 — QA ẩn DONE trên board
            - generic [ref=e207]: "T81: in_progress"
            - link "Task T81" [ref=e209] [cursor=pointer]:
              - /url: ../tasks/T81-dashboard-an-task-done.md
          - cell "Debug UI; Code nếu có lỗi" [ref=e210]
          - cell "KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA." [ref=e211]
          - 'cell "Board đã lọc pending/in_progress/blocked và có localStorage; thiếu acceptance UI cô lập. Không coi code tồn tại là task DONE. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T81 §23–33" [ref=e212]':
            - paragraph [ref=e213]: Board đã lọc pending/in_progress/blocked và có localStorage; thiếu acceptance UI cô lập. Không coi code tồn tại là task DONE.
            - list [ref=e214]:
              - listitem [ref=e215]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e216]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e217]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - link "T81 §23–33" [ref=e219] [cursor=pointer]:
              - /url: ../tasks/T81-dashboard-an-task-done.md
          - 'cell "Chạy song song: test filter/reload/localStorage + keyboard; chỉ giao sửa khi tái hiện defect." [ref=e220]'
          - cell "DONE review T81 — QA ẩn DONE trên board Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e221]:
            - button "DONE review T81 — QA ẩn DONE trên board" [disabled] [ref=e222]: DONE
            - generic [ref=e223]: Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t.
        - 'row "T277 — Archive và tích hợp còn lại T277: in_progress Task T277 Code docs; Debug links KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA. 230 file archive là kết quả trước; phần tích hợp còn giá trị và review vẫn mở. Chưa đóng toàn task. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T277 archive/integration Giao danh mục/link check phần còn lại; không tái archive hoặc đánh DONE từ phần 230 file đã xong. DONE review T277 — Archive và tích hợp còn lại Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e224]':
          - 'rowheader "T277 — Archive và tích hợp còn lại T277: in_progress Task T277" [ref=e225]':
            - strong [ref=e226]: T277 — Archive và tích hợp còn lại
            - generic [ref=e227]: "T277: in_progress"
            - link "Task T277" [ref=e229] [cursor=pointer]:
              - /url: ../tasks/T277-archive-and-future-integration.md
          - cell "Code docs; Debug links" [ref=e230]
          - cell "KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA." [ref=e231]
          - 'cell "230 file archive là kết quả trước; phần tích hợp còn giá trị và review vẫn mở. Chưa đóng toàn task. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T277 archive/integration" [ref=e232]':
            - paragraph [ref=e233]: 230 file archive là kết quả trước; phần tích hợp còn giá trị và review vẫn mở. Chưa đóng toàn task.
            - list [ref=e234]:
              - listitem [ref=e235]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e236]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e237]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - link "T277 archive/integration" [ref=e239] [cursor=pointer]:
              - /url: ../tasks/T277-archive-and-future-integration.md
          - cell "Giao danh mục/link check phần còn lại; không tái archive hoặc đánh DONE từ phần 230 file đã xong." [ref=e240]
          - cell "DONE review T277 — Archive và tích hợp còn lại Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e241]:
            - button "DONE review T277 — Archive và tích hợp còn lại" [disabled] [ref=e242]: DONE
            - generic [ref=e243]: Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t.
        - 'row "T328 — Xác minh đóng P0 T253 T328: pending Task T328 Debug audit; Code docs khi có kết quả KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA. T253 import được tài liệu hóa đã xong; còn cần kiểm P0 closure của audit T328, chưa có acceptance riêng. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T328 §28 Song song T277: đối chiếu P0 với test/log/code; nếu thiếu chứng cứ thì giữ pending, không apply production. DONE review T328 — Xác minh đóng P0 T253 Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e244]':
          - 'rowheader "T328 — Xác minh đóng P0 T253 T328: pending Task T328" [ref=e245]':
            - strong [ref=e246]: T328 — Xác minh đóng P0 T253
            - generic [ref=e247]: "T328: pending"
            - link "Task T328" [ref=e249] [cursor=pointer]:
              - /url: ../tasks/T328-cline-audit-t253.md
          - cell "Debug audit; Code docs khi có kết quả" [ref=e250]
          - cell "KhÃ´ng cÃ³ phá»¥ thuá»™c cháº·n Ä‘Ã£ biáº¿t; váº«n cáº§n scope vÃ QA." [ref=e251]
          - 'cell "T253 import được tài liệu hóa đã xong; còn cần kiểm P0 closure của audit T328, chưa có acceptance riêng. ChÆ°a PASS: Bản sửa đúng scope ChÆ°a PASS: Tests/kiểm chứng acceptance ChÆ°a PASS: Debug kiểm độc lập + root QA T328 §28" [ref=e252]':
            - paragraph [ref=e253]: T253 import được tài liệu hóa đã xong; còn cần kiểm P0 closure của audit T328, chưa có acceptance riêng.
            - list [ref=e254]:
              - listitem [ref=e255]: "ChÆ°a PASS: Bản sửa đúng scope"
              - listitem [ref=e256]: "ChÆ°a PASS: Tests/kiểm chứng acceptance"
              - listitem [ref=e257]: "ChÆ°a PASS: Debug kiểm độc lập + root QA"
            - link "T328 §28" [ref=e259] [cursor=pointer]:
              - /url: ../tasks/T328-cline-audit-t253.md
          - 'cell "Song song T277: đối chiếu P0 với test/log/code; nếu thiếu chứng cứ thì giữ pending, không apply production." [ref=e260]'
          - cell "DONE review T328 — Xác minh đóng P0 T253 Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t." [ref=e261]:
            - button "DONE review T328 — Xác minh đóng P0 T253" [disabled] [ref=e262]: DONE
            - generic [ref=e263]: Dev chÆ°a xÃ¡c nháºn hoÃ n táº¥t.
        - 'row "Blocker — T274 T274: ID trÃ¹ng root QA/điều phối; Admin quyết phạm vi â—‹ Chưa gỡ blocker được chứng minh ID T274 có 2 task. Session 11-10 ghi A.2 đã build, parsed 499/1036 TTL: coverage còn thiếu; report cũ BLOCKED là lịch sử, không chứng minh production mới. T274 footprint 1 T274 footprint 2 Root đối chiếu status/scope và phân biệt 2 task trước khi giao build; không auto-DONE hay mở rộng TTL pool. DONE review Blocker — T274 Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu." [ref=e264]':
          - 'rowheader "Blocker — T274 T274: ID trÃ¹ng" [ref=e265]':
            - strong [ref=e266]: Blocker — T274
            - generic [ref=e267]: "T274: ID trÃ¹ng"
          - cell "root QA/điều phối; Admin quyết phạm vi" [ref=e268]
          - cell "â—‹ Chưa gỡ blocker được chứng minh" [ref=e269]:
            - generic [ref=e270]: â—‹ Chưa gỡ blocker được chứng minh
          - 'cell "ID T274 có 2 task. Session 11-10 ghi A.2 đã build, parsed 499/1036 TTL: coverage còn thiếu; report cũ BLOCKED là lịch sử, không chứng minh production mới. T274 footprint 1 T274 footprint 2" [ref=e271]':
            - paragraph [ref=e272]: "ID T274 có 2 task. Session 11-10 ghi A.2 đã build, parsed 499/1036 TTL: coverage còn thiếu; report cũ BLOCKED là lịch sử, không chứng minh production mới."
            - list
            - link "T274 footprint 1" [ref=e274] [cursor=pointer]:
              - /url: ../tasks/T274-ttl-rule-design.md
            - link "T274 footprint 2" [ref=e276] [cursor=pointer]:
              - /url: ../tasks/T274-vn-lineage-ttl-rule.md
          - cell "Root đối chiếu status/scope và phân biệt 2 task trước khi giao build; không auto-DONE hay mở rộng TTL pool." [ref=e277]
          - cell "DONE review Blocker — T274 Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu." [ref=e278]:
            - button "DONE review Blocker — T274" [disabled] [ref=e279]: DONE
            - generic [ref=e280]: Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu.
        - 'row "Blocker — T200 / T223 T200: blocked Â· T223: blocked root QA/điều phối; Admin quyết phạm vi â—‹ Chưa gỡ blocker được chứng minh T200 tie-break phần kỹ thuật đã xong; quyết định nhóm định danh còn blocked. T223 phân nhóm DILA-ID khác với remediation ETL T357/former T223. T200 T223 identity Admin/Deep Research cần chứng cứ đúng entity và quyết định gộp/tách; loại khỏi hàng local fix trực tiếp. DONE review Blocker — T200 / T223 Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu." [ref=e281]':
          - 'rowheader "Blocker — T200 / T223 T200: blocked Â· T223: blocked" [ref=e282]':
            - strong [ref=e283]: Blocker — T200 / T223
            - generic [ref=e284]: "T200: blocked Â· T223: blocked"
          - cell "root QA/điều phối; Admin quyết phạm vi" [ref=e285]
          - cell "â—‹ Chưa gỡ blocker được chứng minh" [ref=e286]:
            - generic [ref=e287]: â—‹ Chưa gỡ blocker được chứng minh
          - cell "T200 tie-break phần kỹ thuật đã xong; quyết định nhóm định danh còn blocked. T223 phân nhóm DILA-ID khác với remediation ETL T357/former T223. T200 T223 identity" [ref=e288]:
            - paragraph [ref=e289]: T200 tie-break phần kỹ thuật đã xong; quyết định nhóm định danh còn blocked. T223 phân nhóm DILA-ID khác với remediation ETL T357/former T223.
            - list
            - link "T200" [ref=e291] [cursor=pointer]:
              - /url: ../tasks/T200-vnpa-dila-id-duplicate-limit1.md
            - link "T223 identity" [ref=e293] [cursor=pointer]:
              - /url: ../tasks/T223-dila-id-29-nhom-phan-loai-va-quyet-tach.md
          - cell "Admin/Deep Research cần chứng cứ đúng entity và quyết định gộp/tách; loại khỏi hàng local fix trực tiếp." [ref=e294]
          - cell "DONE review Blocker — T200 / T223 Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu." [ref=e295]:
            - button "DONE review Blocker — T200 / T223" [disabled] [ref=e296]: DONE
            - generic [ref=e297]: Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu.
        - row "Blocker — vòng phụ thuộc root QA/điều phối; Admin quyết phạm vi â—‹ Chưa gỡ blocker được chứng minh Graph Dashboard hiện có T22 → T22 và T50 → T73 → T59 → T53 → T50. depends_on có dạng chuỗi YAML [T…], không bỏ qua khi parse. Định nghĩa audit/dependency Root xác minh semantics/ownership rồi chỉnh cạnh có căn cứ; không tự xóa dependency để mở DONE. DONE review Blocker — vòng phụ thuộc Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu." [ref=e298]:
          - rowheader "Blocker — vòng phụ thuộc" [ref=e299]:
            - strong [ref=e300]: Blocker — vòng phụ thuộc
          - cell "root QA/điều phối; Admin quyết phạm vi" [ref=e301]
          - cell "â—‹ Chưa gỡ blocker được chứng minh" [ref=e302]:
            - generic [ref=e303]: â—‹ Chưa gỡ blocker được chứng minh
          - cell "Graph Dashboard hiện có T22 → T22 và T50 → T73 → T59 → T53 → T50. depends_on có dạng chuỗi YAML [T…], không bỏ qua khi parse. Định nghĩa audit/dependency" [ref=e304]:
            - paragraph [ref=e305]: Graph Dashboard hiện có T22 → T22 và T50 → T73 → T59 → T53 → T50. depends_on có dạng chuỗi YAML [T…], không bỏ qua khi parse.
            - list
            - link "Định nghĩa audit/dependency" [ref=e307] [cursor=pointer]:
              - /url: ../docs/T358-dashboard-harness-execution.md
          - cell "Root xác minh semantics/ownership rồi chỉnh cạnh có căn cứ; không tự xóa dependency để mở DONE." [ref=e308]
          - cell "DONE review Blocker — vòng phụ thuộc Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu." [ref=e309]:
            - button "DONE review Blocker — vòng phụ thuộc" [disabled] [ref=e310]: DONE
            - generic [ref=e311]: Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu.
        - 'row "Blocker — duplicate IDs root QA/điều phối; Admin quyết phạm vi â—‹ Chưa gỡ blocker được chứng minh dup:ids exit 1: 9 ID cũ T158/T168/T169/T170/T171/T177/T206/T215/T274. T358 không trùng. Pipeline dừng ở cổng này. Giới hạn validation Root chọn footprint cần đổi theo AGENTS §16; không đóng/gộp theo ID mơ hồ, không báo full pipeline PASS. DONE review Blocker — duplicate IDs Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu." [ref=e312]':
          - rowheader "Blocker — duplicate IDs" [ref=e313]:
            - strong [ref=e314]: Blocker — duplicate IDs
          - cell "root QA/điều phối; Admin quyết phạm vi" [ref=e315]
          - cell "â—‹ Chưa gỡ blocker được chứng minh" [ref=e316]:
            - generic [ref=e317]: â—‹ Chưa gỡ blocker được chứng minh
          - 'cell "dup:ids exit 1: 9 ID cũ T158/T168/T169/T170/T171/T177/T206/T215/T274. T358 không trùng. Pipeline dừng ở cổng này. Giới hạn validation" [ref=e318]':
            - paragraph [ref=e319]: "dup:ids exit 1: 9 ID cũ T158/T168/T169/T170/T171/T177/T206/T215/T274. T358 không trùng. Pipeline dừng ở cổng này."
            - list
            - link "Giới hạn validation" [ref=e321] [cursor=pointer]:
              - /url: ../docs/T358-dashboard-harness-execution.md
          - cell "Root chọn footprint cần đổi theo AGENTS §16; không đóng/gộp theo ID mơ hồ, không báo full pipeline PASS." [ref=e322]
          - cell "DONE review Blocker — duplicate IDs Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu." [ref=e323]:
            - button "DONE review Blocker — duplicate IDs" [disabled] [ref=e324]: DONE
            - generic [ref=e325]: Chá»‰ lÃ blocker, chÆ°a cÃ³ báº£n build nghiá»‡m thu.
```

# Test source

```ts
  1   | const { test, expect } = require('@playwright/test');
  2   | const fs = require('node:fs');
  3   | const path = require('node:path');
  4   | const base = path.resolve(__dirname, '..');
  5   | const html = fs.readFileSync(path.join(base, 'dashboard/dashboard_process.html'), 'utf8');
  6   | const panel = html.match(/<!-- T358:START[\s\S]*?<!-- T358:END -->/)[0];
  7   | const script = fs.readFileSync(path.join(base, 'dashboard/triage_execution.js'), 'utf8');
  8   | const css = fs.readFileSync(path.join(base, 'dashboard/triage_execution.css'), 'utf8');
  9   | const actualReport = JSON.parse(fs.readFileSync(path.join(base, 'data/triage_execution_report.json'), 'utf8'));
  10  | const actualProgress = JSON.parse(fs.readFileSync(path.join(base, 'data/progress_data.json'), 'utf8'));
  11  | const prefix = 'ptda:harness:admin-review:v1:';
  12  | const copy = value => JSON.parse(JSON.stringify(value));
  13  | function ready() {
  14  |   const report = copy(actualReport);
  15  |   report.rows = [report.rows.find(row => row.row_id === 'T283')];
  16  |   const row = report.rows[0];
  17  |   row.prerequisites = [];
  18  |   row.development.completed = true;
  19  |   row.development.checks.forEach(check => { check.passed = true; check.evidence = [{href: '../tasks/T283-m0-xoa-key-khoi-tai-lieu.md', label: 'Fixture proof only'}]; });
  20  |   return report;
  21  | }
  22  | async function mount(page, report = actualReport, progress = actualProgress) {
  23  |   const state = {report: copy(report), progress: copy(progress), fail: false, requests: []};
  24  |   await page.route('**/*', async route => {
  25  |     const request = route.request();
  26  |     state.requests.push({method: request.method(), url: request.url()});
  27  |     const pathname = new URL(request.url()).pathname;
  28  |     let body;
  29  |     let contentType = 'application/json';
  30  |     if (pathname === '/dashboard/dashboard_process.html') {
  31  |       contentType = 'text/html';
  32  |       body = '<!doctype html><html lang="vi"><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:16px;background:#020617;font-family:sans-serif}.hx-btn{padding:8px;border:1px solid #64748b;background:#0f172a;color:white}.hx-card{padding:12px;border:1px solid #334155;border-radius:12px;box-sizing:border-box}</style><link rel="stylesheet" href="triage_execution.css"><script src="triage_execution.js" defer></script></head><body>' + panel + '</body></html>';
  33  |     } else if (pathname === '/dashboard/triage_execution.js') {body = script; contentType = 'application/javascript';}
  34  |     else if (pathname === '/dashboard/triage_execution.css') {body = css; contentType = 'text/css';}
  35  |     else if (pathname === '/data/triage_execution_report.json') { if (state.fail) return route.fulfill({status: 503,body: '{}'}); body = JSON.stringify(state.report); }
  36  |     else if (pathname === '/data/progress_data.json') body = JSON.stringify(state.progress);
  37  |     else return route.abort();
  38  |     await route.fulfill({status: 200, contentType, body});
  39  |   });
  40  |   await page.goto('http://t358.fixture/dashboard/dashboard_process.html');
> 41  |   await expect(page.locator('#triageMessage')).toContainText('Báo cáo đã tải');
      |                                                ^ Error: expect(locator).toContainText(expected) failed
  42  |   return state;
  43  | }
  44  | async function confirm(page) {
  45  |   await page.getByRole('button', {name: 'DONE review T283', exact: false}).click();
  46  |   await page.locator('#triageConfirmInput').fill('T283');
  47  |   await page.locator('#triageConfirmSave').click();
  48  |   await expect(page.locator('#triageMessage')).toContainText('Đã lưu review cục bộ');
  49  | }
  50  | 
  51  | test('T358 actual source is integrated; audited report locks every incomplete row', async ({page}) => {
  52  |   expect(html).toContain('<script src="triage_execution.js" defer>');
  53  |   expect(html.indexOf('id="triageExecution"')).toBeGreaterThan(html.indexOf('id="hxRoot"'));
  54  |   expect(html.indexOf('id="triageExecution"')).toBeLessThan(html.indexOf('Tiến độ H3 —'));
  55  |   await page.addInitScript(() => localStorage.setItem('adminDone_T283', '1'));
  56  |   await mount(page);
  57  |   await expect(page.locator('#triageRows tr')).toHaveCount(15);
  58  |   for (const button of await page.locator('.triage-done').all()) await expect(button).toBeDisabled();
  59  |   await expect(page.locator('#triageRows')).toContainText('T22 → T22');
  60  |   await expect(page.locator('#triageRows')).toContainText('T50 → T73 → T59 → T53 → T50');
  61  |   expect(await page.evaluate(() => Object.keys(localStorage).filter(key => key.startsWith('ptda:harness:')))).toEqual([]);
  62  | });
  63  | 
  64  | test('DONE requires typed confirmation; cancel/Escape no write; persist only local review', async ({page}) => {
  65  |   const state = await mount(page, ready());
  66  |   const before = JSON.stringify(state.progress);
  67  |   const button = page.locator('.triage-done');
  68  |   await expect(button).toBeEnabled();
  69  |   await button.focus();
  70  |   await page.keyboard.press('Enter');
  71  |   await expect(page.locator('#triageConfirmInput')).toBeFocused();
  72  |   await page.locator('#triageConfirmInput').fill('done');
  73  |   await expect(page.locator('#triageConfirmSave')).toBeDisabled();
  74  |   await page.keyboard.press('Escape');
  75  |   await expect(page.locator('#triageConfirm')).not.toBeVisible();
  76  |   await expect(button).toBeFocused();
  77  |   expect(await page.evaluate(() => localStorage.length)).toBe(0);
  78  |   await button.click();
  79  |   await page.locator('#triageCancel').click();
  80  |   expect(await page.evaluate(() => localStorage.length)).toBe(0);
  81  |   await confirm(page);
  82  |   const stored = await page.evaluate(() => ({keys: Object.keys(localStorage), value: JSON.parse(localStorage.getItem('ptda:harness:admin-review:v1:T283'))}));
  83  |   expect(stored.keys).toEqual([prefix + 'T283']);
  84  |   expect(stored.value.review_status).toBe('admin_reviewed');
  85  |   expect(stored.value).not.toHaveProperty('task_status');
  86  |   expect(stored.value).not.toHaveProperty('status');
  87  |   expect(JSON.stringify(state.progress)).toBe(before);
  88  |   expect(state.requests.every(request => request.method === 'GET')).toBe(true);
  89  |   expect(state.requests.some(request => request.url.includes('/api/'))).toBe(false);
  90  |   await page.reload();
  91  |   await expect(button).toHaveText('Đã review cục bộ');
  92  |   await expect(button).toBeDisabled();
  93  | });
  94  | 
  95  | test('changed revision/evidence/prerequisite makes stored review stale', async ({page}) => {
  96  |   const state = await mount(page, ready());
  97  |   await confirm(page);
  98  |   state.report.revision = 'fixture-new-revision';
  99  |   await page.locator('#triageReload').click();
  100 |   await expect(page.locator('.triage-done')).toHaveText('DONE');
  101 |   await expect(page.locator('.triage-done')).toBeEnabled();
  102 |   state.report.rows[0].prerequisites = [{label: 'Blocked dependency', satisfied: false}];
  103 |   await page.locator('#triageReload').click();
  104 |   await expect(page.locator('.triage-done')).toBeDisabled();
  105 |   await expect(page.locator('#triageRows')).toContainText('Chưa đủ điều kiện trước');
  106 | });
  107 | 
  108 | test('readiness fails closed for missing QA/proof, false completion, blocked or ambiguous task', async ({page}) => {
  109 |   const state = await mount(page, ready());
  110 |   const cases = [
  111 |     report => report.rows[0].development.completed = false,
  112 |     report => report.rows[0].development.checks.pop(),
  113 |     report => report.rows[0].development.checks[0].evidence = [{href:'javascript:alert(1)',label:'fake'}],
  114 |     report => report.rows[0].development.checks.push({key:'extra',label:'extra',passed:false,evidence:[]})
  115 |   ];
  116 |   for (const mutate of cases) {
  117 |     state.report = ready(); mutate(state.report);
  118 |     await page.locator('#triageReload').click();
  119 |     await expect(page.locator('.triage-done')).toBeDisabled();
  120 |   }
  121 |   state.report = ready();
  122 |   state.progress.tasks.find(task => task.id === 'T283').status = 'blocked';
  123 |   await page.locator('#triageReload').click();
  124 |   await expect(page.locator('.triage-done')).toBeDisabled();
  125 |   state.progress = copy(actualProgress);
  126 |   state.progress.tasks.push(copy(state.progress.tasks.find(task => task.id === 'T283')));
  127 |   await page.locator('#triageReload').click();
  128 |   await expect(page.locator('.triage-done')).toBeDisabled();
  129 |   await expect(page.locator('#triageRows')).toContainText('ID thiếu hoặc trùng');
  130 | });
  131 | 
  132 | test('untrusted report text and links are inert', async ({page}) => {
  133 |   const report = ready();
  134 |   report.rows[0].title = '<img src=x onerror="window.t358Xss=1">';
  135 |   report.rows[0].development.summary = '<script>window.t358Xss=2</script>';
  136 |   report.rows[0].evidence = [{href:'javascript:window.t358Xss=3',label:'<svg onload="window.t358Xss=4">'},{href:'../docs/../../outside.html',label:'escape'}];
  137 |   await mount(page, report);
  138 |   expect(await page.evaluate(() => window.t358Xss)).toBeUndefined();
  139 |   await expect(page.locator('#triageRows img, #triageRows svg, #triageRows script')).toHaveCount(0);
  140 |   await expect(page.locator('#triageRows a[href^="javascript:"]')).toHaveCount(0);
  141 |   await expect(page.locator('#triageRows')).toContainText('<img src=x');
```