---
id: T173
title: "Plan Merge Tab Nhân Vật + Tab Truyền Thừa (preview truyền thừa trong hồ sơ, giữ workspace tree)"
module: UI/UX — Đạo Ảnh GIS
priority: high
status: ready-for-dev
owner: claudecode
depends_on: []
created: 2026-09-25
updated: 2026-09-25
designed_by: mimo-flash
handoff_to: Claude Code Agent (daoanh-debugger, mode ANALYZE_ONLY)
plan_approved_at: "2026-09-25 (Admin: Đồng ý build — docs/plan trước, code chờ APPROVED FIX)"
done_when: |
  Agent trả về output_before_code (architecture + gap + minimal plan + files +
  API YES/NO + risks + QA checklist + rollback) ≤80 dòng; KHÔNG sửa code/DB/CSS;
  sau đó chờ APPROVED FIX để build phase code.
---

# T173 — Plan Merge Tab Nhân Vật + Tab Truyền Thừa (ANALYZE_ONLY)

> **Trạng thái:** prompt đã review + chốt delta (7 điểm) — **paste được ngay cho Claude Code**.
> **Stop:** DỪNG sau ANALYSIS + PLAN. Code phase chỉ chạy khi Admin ra lệnh `APPROVED FIX`.
> Nguồn tham chiếu: [Perplexity thread](https://www.perplexity.ai/search/c5ac7eb9-2f71-458a-8e80-ea7f7d82172c)

## 1. Review logic prompt (2026-09-25, verify trên source thật)

**Verdict: đúng ~85% — 7 điểm cần bổ sung (đã absorb vào prompt §3).**

### ✅ Giả định verified thật
| Giả định | Bằng chứng |
|---|---|
| 2 tab tồn tại | `places.html:240-241` — `data-t="persons"` 🧑 · `data-t="lineage"` 🌳 |
| Workspace lineage riêng (Pháp Mạch, full tree) | T86 `:5067` · panel "Pháp Mạch Truyền Thừa" `:5224` · `ancestorBar` `:5479` · API `lineage-tree?up=2&down=2` `:5167,5414`, `ancestor-spine` `:5121` |
| Preview tái dùng API, không cần API mới | `GET /daoanh/api/monk/<id>/lineage-tree?up=1&down=1` |
| Persons tab render người theo Place | `renderPersonsTab` `:8597` — `place_person_link` + Wikidata/bibl/bio/origin |
| URL state/back-forward | T130 sync `URLSearchParams` `:9990,10163` · `_goTab` `:467` |
| Phân biệt truyền pháp ≠ co-mention | `:4175` · edge "X truyền pháp cho Y" `:5914` · `dila:teacher_of` vs Zen L2 `teacher_of` `:7243,7250` |

### ❌ 7 điểm thiếu/sai (P0 ×2, P1 ×4, P2 ×1)
1. **P0** — Thiếu **auto-switch hiện tại**: `selectPerson()` tự click tab lineage (`:2365-2367`) + cache `_tabLoaded` — proposal đụng thẳng behavior này.
2. **P0** — Hồ sơ ĐÃ có block "Truyền Thừa (DILA L2)" + card thầy/trò (`_linRelationCard` `:6081`, `:6291,6401,6266`) → preview dễ **trùng**.
3. **P1** — "3 đời" mơ hồ → chốt `up=1&down=1` (3 node) cho preview; workspace giữ `up=2&down=2`.
4. **P1** — Dung sai file: repo có 2 `places.html` — target = **root 10.193 dòng**; `admin/places.html` (524, GIS queue) **không có 2 tab này**.
5. **P1** — Wikidata person **không có DILA ID → không click được** (`:8593-8595`) → CTA phải disable + lý do.
6. **P1** — Relation inventory phải liệt kê payload thật; thọ giới/thế độ nếu không có → `NOT FOUND` (chỉ là guard).
7. **P2** — Nhiều entry point gọi `selectPerson()/_goTab('lineage')` (`:3813,8391,8616`) → phải ấn định hành vi từng điểm.

## 2. Quy tắc khóa (giữ nguyên prompt gốc)
Không phá workspace lineage · không nhầm truyền pháp/thọ giới/thế độ · preview chỉ dùng relation truyền pháp hợp lệ · thiếu chứng cứ → empty state, không suy luận · click node mở đúng detail, không loop · deep-link giữ context · không hard-code ID/tên · tái dùng API/renderer/state hiện có · **ANALYZE_ONLY — không sửa code/DB/schema/CSS trước APPROVED FIX**.

## 3. PROMPT ĐÃ CHỐT — paste vào Claude Code

```js
Agent({
  description: "Plan merge Person and Lineage UX without losing research tree",
  subagent_type: "daoanh-debugger",
  prompt: JSON.stringify({
    task: "plan_person_lineage_tab_merge",
    mode: "ANALYZE_ONLY",
    scope_lock: {
      app: "Đạo Ảnh GIS",
      page: "/daoanh/places.html",
      ui: ["Tab Nhân Vật", "Tab Truyền Thừa"],
      exclude: [
        "database data correction",
        "lineage source consensus rules",
        "DILA/Marcus/TTL import pipeline",
        "Nexus",
        "unrelated Place UI",
        "admin/places.html (GIS queue — sai file)"
      ]
    },

    decision_to_validate: {
      proposed: "Gộp UX Nhân Vật + Truyền Thừa, không gộp hoàn toàn chức năng tree.",
      target_ia: {
        primary_tab: "Nhân Vật",
        default_view: "Hồ sơ nhân vật đang chọn",
        embedded_lineage: "Preview truyền thừa: thầy truyền pháp -> nhân vật -> pháp tử (up=1&down=1, đúng 3 node) — CHỐT: '3 đời' = 3 node, KHÔNG phải 3 thế hệ",
        deep_link: "Nút 'Mở Không gian Truyền Thừa' chuyển sang workspace tree chuyên sâu, giữ selected person",
        retained_lineage_workspace: [
          "Pháp Mạch: direct lineage, expand/collapse theo đời",
          "Phả hệ mở rộng: full branching tree, sư huynh đệ, nhiều thế hệ",
          "Niên đại / evidence / source inspection nếu hiện có"
        ]
      }
    },

    required_rules: [
      "Không xóa hoặc làm hỏng Tab/Workspace Truyền Thừa độc lập.",
      "Không nhầm quan hệ truyền pháp với thế độ, thọ giới, hoặc liên hệ thầy-trò khác.",
      "Preview chỉ dùng relation type được hệ thống hiện hành xác định là truyền pháp hợp lệ.",
      "Nếu chưa đủ dữ liệu để xác định pháp mạch, hiển thị trạng thái không đủ chứng cứ; không tự suy luận.",
      "Click node/person trong preview phải mở đúng chi tiết nhân vật; không tạo navigation loop.",
      "Deep-link phải giữ selected person/root context khi chuyển sang workspace Truyền Thừa.",
      "Không hard-code person ID, place ID, tên tăng nhân, hoặc relation cụ thể.",
      "Tái sử dụng API, resolver, tree renderer và state hiện có khi phù hợp; không tạo API/logic trùng lặp.",
      "Phân tích và đề xuất GIỮ/BỎ hành vi auto-switch hiện tại (selectPerson tự click tab lineage, places.html:2365 + cache _tabLoaded) — cấm âm thầm đổi UX khi chưa APPROVED FIX.",
      "Preview BẮT BUỘC tái dùng card thầy/trò hiện có (_linRelationCard, places.html:6081) + lineage-tree?up=1&down=1; cấm tạo renderer/API trùng.",
      "Nhân vật không có DILA ID (Wikidata bridge, places.html:8593): ẩn/disable CTA kèm lý do; không mở workspace với id rỗng, không lỗi."
    ],

    investigation: [
      "Chỉ phân tích file places.html ở ROOT repo (10.193 dòng); BỎ QUA admin/places.html (GIS queue, không có tab Nhân Vật/Truyền Thừa).",
      "Xác định file HTML/JS/CSS đang render Tab Nhân Vật và Tab Truyền Thừa.",
      "Xác định state hiện tại của selected person, lineage root, tab navigation và URL query/hash (T130 sync, URLSearchParams places.html:9990,10163).",
      "Xác định API payload hiện dùng cho person detail, relation summary và lineage tree.",
      "Kiểm tra Tab Nhân Vật hiện có thể render danh sách người liên quan đến Place hay không.",
      "Kiểm tra Tab Truyền Thừa đang nhận person ID bằng cách nào và có giữ context khi đổi tab không.",
      "Xác định component/tree renderer có thể giới hạn preview mà không ảnh hưởng full tree không.",
      "Đối chiếu block 'Truyền Thừa (DILA L2)' + card thầy/trò ĐÃ CÓ trong hồ sơ (places.html:6291,6401,6081) với preview dự kiến — đánh dấu phần trùng.",
      "Liệt kê TOÀN BỘ entry point gọi selectPerson()/_goTab('lineage') (places.html:3813,467,8391,8616) và cache _tabLoaded — ấn định hành vi từng điểm: preview hay auto-switch.",
      "Liệt kê relation type thực tế trong payload API (teacher/student/dila:teacher_of/co-mention…); thọ giới/thế độ nếu KHÔNG có → ghi NOT FOUND (rule chỉ là guard tương lai).",
      "Xác định các relation type thực tế và cách UI hiện phân biệt dharma transmission với ordination/tonsure.",
      "Kiểm tra empty/loading/error state và console/network errors hiện có."
    ],

    expected_ui: {
      person_tab: [
        "Hồ sơ nhân vật vẫn là nội dung chính.",
        "Có khối 'Truyền thừa' đặt sau thông tin hồ sơ hoặc nguồn liên quan.",
        "Khối hiển thị thầy truyền pháp, nhân vật trung tâm và pháp tử khi có dữ liệu hợp lệ.",
        "Preview mặc định = 3 node (up=1&down=1), không thay thế full tree.",
        "Có nút CTA rõ: 'Mở Không gian Truyền Thừa'.",
        "Không có dữ liệu hợp lệ: hiển thị empty state có giải thích ngắn, không render tree giả.",
        "Nhân vật không có DILA ID: khối preview hiển thị lý do, CTA disable."
      ],
      lineage_workspace: [
        "Vẫn hỗ trợ Pháp Mạch và Phả hệ mở rộng.",
        "Mở từ CTA phải focus đúng nhân vật vừa xem (cập nhật/có ý thức cache _tabLoaded).",
        "Giữ các tính năng zoom/pan, expand/collapse, source/evidence đang có.",
        "Không thu nhỏ hoặc nhét full tree vào panel hồ sơ."
      ]
    },

    acceptance_for_future_fix: [
      "Từ Place/Person context, user chọn một nhân vật và xem được hồ sơ cùng preview truyền thừa nếu dữ liệu có.",
      "CTA mở đúng workspace Truyền Thừa với selected person giữ nguyên.",
      "Preview chỉ hiển thị tối đa 3 node và không có node/edge duplicate.",
      "Pháp mạch và quan hệ thọ giới/thế độ được ghi nhãn hoặc tách UI rõ ràng.",
      "Không có selected person: UI hướng dẫn chọn nhân vật, không lỗi hoặc màn hình trống khó hiểu.",
      "Back/Forward và refresh không làm mất hoặc đổi sai person context nếu kiến trúc hiện tại hỗ trợ URL state.",
      "Không có console error, request lỗi không được xử lý, hoặc regression ở Place pages khác.",
      "Quyết định từng entry point (preview vs auto-switch) được ghi thành BẢNG trong output."
    ],

    output_before_code: [
      "Current architecture: files, components, state flow, APIs thực tế (trỏ đúng file root).",
      "Gap analysis: phần nào đã có (card DILA L2, relation card), phần nào thiếu.",
      "Bảng quyết định từng entry point selectPerson(): giữ auto-switch hay chuyển preview.",
      "Recommended minimal implementation plan theo thứ tự bước.",
      "Danh sách file dự kiến sửa và lý do từng file.",
      "API/schema/database change: YES/NO, nêu chính xác nếu YES (dự kiến NO — reuse lineage-tree).",
      "Root cause/risk: context loss, relation-type mixing, duplicate tree renderer, performance, mobile layout.",
      "Manual QA checklist với ít nhất 1 Place có người liên quan và 1 person có lineage.",
      "Rollback plan ngắn."
    ],

    constraints: [
      "Không sửa code, database, schema, migration, API contract hoặc CSS trước khi được APPROVED FIX.",
      "Không viết report dài; output tối đa 80 dòng hoặc JSON ngắn có cấu trúc.",
      "Nếu không xác minh được file/API/state từ codebase, ghi NOT FOUND; không đoán.",
      "Chỉ kết luận dựa trên source code và dữ liệu runtime thực tế."
    ],

    stop: "DỪNG sau ANALYSIS + PLAN. Chờ lệnh: APPROVED FIX."
  })
})
```

## 4. Phases
1. **(session này)** Review prompt → 7 điểm → prompt chốt §3 ✅ (docs-only, đã commit).
2. Chạy prompt trên Claude Code → nhận ANALYSIS + PLAN (≤80 dòng) → Admin duyệt.
3. **APPROVED FIX** → build code theo minimal plan (tách commit từng bước) → `npm run pipeline` → QA checklist.
4. Report + ROLLBACK hash-fill.

## 5. Revert
- Docs: `git revert --no-edit <sha_T173>` (docs-only).
- Code phase (sau APPROVED FIX): mỗi bước 1 commit riêng → `git revert <sha bước>`; không DB change dự kiến (API change = NO).

## 6. Files
- Task/plan này: `docs/Mimo-Flash/T173-person-lineage-tab-merge.md`
- Session: `docs/sessions/2026-09-25_t173-person-lineage-tab-merge-review.md`
- Target code (chưa sửa): `places.html` (root, 10.193 dòng)
