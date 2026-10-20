# T390 — remove live endpoint comparison section

2026-10-14. Admin clarification: remove only the live section, not the historical session snapshots or T358 triage rows. Initial HEAD: 1b19192d1391b58d1b5526560122773845b5a27d.

Changed HTML: 17 lines of section markup and 17 lines of endpointTable renderer removed. Other IDs/buttons and T358 block are preserved byte-for-byte. Existing summary counter remains (350 from the current JSON in the focused test); generator/report/progress JSON unchanged.

Validation: node tests/test_t390_endpoint_section_removal.cjs PASS; five inline scripts parsed; old render with missing table throws, new render passes and invokes Board/Undone/Places/Git/HOME plus snapshot event. This does not replace full browser QA. Historical common-gate failures remain historical unless rerun.

Rollback: after scoped commit, git revert --no-edit <SHA> from visjs-app root. Before HTML is retained in this new session for the meaningful regression test; no historical backup was edited. HEAD/shared scope is checked again immediately before commit; use fresh temp index/read-tree HEAD and exact paths.

Current gate run: guard PASS; pipeline stops at dup:ids FAIL, now only T274 remains duplicated (the older 9-ID count is historical). No downstream data audits/tester steps ran in that pipeline. Root static QA PASS and scoped commit authorized.
