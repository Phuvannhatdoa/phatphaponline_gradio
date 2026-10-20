---
id: T101
title: Place Graph Display Spec — Edge Evidence Types + Research Mode + Label Fallback
module: Nexus / Đồ Thị
priority: high
status: in_progress
depends_on: [T92, T90, T99]
created: 2026-09-07
updated: 2026-09-07
done_when: >
  (1) Mỗi edge có trường evidence_type (with_evidence|partial|co_mention|unverified);
  (2) PARTIAL badge hiện trên edge khi thiếu provenance;
  (3) co_mention/unverified ẩn mặc định, chỉ hiện khi bật Research mode;
  (4) Label fallback đầy đủ spec §6;
  (5) Place view mặc định mở đến đời 2 (tang_nhan auto-expand);
  (6) bugs.md tracking workflow active.
---

# T101 — Place Graph Display Spec Implementation

## Spec Reference
`docs/PLACE_GRAPH_DISPLAY_SPEC.md` — được Admin phê duyệt 2026-09-07.

## Gaps so với spec (từ audit)

| # | Gap | File | Priority |
|---|-----|------|----------|
| 1 | Edge `evidence_type` field thiếu trong API | `app.py` api_places_graph + api_nexus | HIGH |
| 2 | PARTIAL badge trên edge khi thiếu provenance | `places.html` _renderVisGraph + grouped | HIGH |
| 3 | `unverified`/`co_mention` ẩn default, toggle Research mode | `places.html` | MEDIUM |
| 4 | Label fallback đầy đủ: name_vi > preferred_label_vi > display_name > name_han > source_label | `places.html` _nexusSafeLabel | MEDIUM |
| 5 | Default 3-đời: place view auto-expand tang_nhan | `places.html` _nexusGroupState | LOW |

## Evidence Type Rules (từ spec §5)

| Type | Backend logic | Visual |
|------|--------------|--------|
| `with_evidence` | listbibl CBETA (DILA curated) OR nexus_events confidence≥0.7 OR api_nexus có ref+citation | Solid |
| `partial` | nexus_events confidence<0.7 OR api_nexus có ref nhưng thiếu citation | Solid + badge ⚑ PARTIAL + reason |
| `co_mention` | lân cận (structural) OR derived=True (shared teacher) | Dotted, hidden default |
| `unverified` | api_nexus không có ref và không có citation | Hidden default |

## Acceptance Criteria

- [x] api_places_graph trả `evidence_type` trên mỗi edge (lân cận=co_mention, listbibl=with_evidence, nexus_events conf-based)
- [x] api_nexus trả `evidence_type` trên mỗi edge (cbeta_ref=with_evidence, src_ref-based, unverified khi không có ref)
- [x] _renderVisGraph: co_mention/unverified edges ẩn khi Research mode off
- [x] _renderVisGraph: PARTIAL label prefix `⚑` + title reason
- [ ] _nexusRenderGrouped: person nodes từ low-confidence show badge (cần test thêm)
- [x] Filter bar có toggle "Research mode"
- [x] _nexusSafeLabel full fallback chain theo spec §6
- [x] Place view default: _nexusGroupState.expanded = 'tang_nhan' on first load
- [x] py_compile PASS, node --check PASS
- [ ] Thiếu Lâm Tự PL000000023255: test visual — pending server test

## Rollback

```powershell
git revert --no-edit <commit-hash>
```
Code không ghi DB — rollback là revert commit.
