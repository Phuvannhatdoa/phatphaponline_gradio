# T.2076 — initial isolated candidate dataset

## 1. Snapshot

Initial strict extraction saved on 2026-10-18. Artifacts complete for this rule version; historical recall/identity/overlap are not established. 0 candidates and 862 excluded trigger occurrences in the selected projected body-unit stream. Source and ZTJ inputs remain unchanged.

## 2. Read in two minutes

This result means no clause passed six deliberately narrow two-named-title templates. It does not mean 景德傳燈錄 has no succession or disciple claims. Bare names, biography-heading subjects, pronouns and other syntax are outside this rule version. Six positive synthetic grammar fixtures prove the extractor can emit candidates; those fixtures are not real source assertions.

## 3. Inputs and rights

- Immutable source: daoanh/data/cbeta/xml-p5-full/T/T51/T51n2076.xml; 3,691,202 bytes.
- Source SHA256: a3942d421828f6372c1853f58daeb19299e4c91ab701a711167b3610ffaf507b
- Header: source-header-fragment.xml, exact source bytes 283..41958 (end exclusive), source XML lines4..1119; SHA256 63a17a1a3feca6a847c4edd4d79686138cdb3d4848dcbdba31fd841e85e92ddb
- Title 景德傳燈錄; source author 宋 道原纂; header date2026-07-13. Header notice: Available for non-commercial use when distributed with this header intact.
- The fragment is byte-exact and inherits TEI/cb namespace declarations from the original root. It is not a standalone reserialized XML document. Do not discard header notices or apply a Zenodo/project license to this source.
- ZTJ Phase2 person-ID/relation-direction reports and Phase3 source_relation.json are the only comparison inputs; each path/hash is recorded in jingde-data.json. No legacy database, TTL, Marcus corpus or authority API was queried.

## 4. Artifact map

| File | Purpose |
|---|---|
| jingde-data.json | metadata, all0 candidate records, and862 excluded occurrences with trigger, quotation, juan/lb/path, XML/projection hashes, rights and exclusion reason |
| jingde-quality-report.md | measured counts, strictness, false-negative and identity limits |
| jingde-comparison.json | overlap/new/reverse/conflict lists plus unresolved and type-difference lists; typed ZTJ baseline with locators |
| source-header-fragment.xml / source-discovery.json | pinned header and bounded source inventory |
| extract_jingde.py / inspect_source.py | local stdlib reproducibility tools; no import/app/DB/network execution |
| test-fixtures.json / test_jingde.py / test-results.json |18 synthetic grammar cases, six test methods, and every real record integrity check |
| dry-run.json / extraction-run.json / test-command.json | exact commands and outputs |
| manifest.json / SHA256SUMS.txt | final artifact/input hashes and scope contract |

## 5. Extraction and review rules

Only 嗣, 法嗣, 弟子, 傳法 are triggers; 法嗣 is tokenized before its substring 嗣. Role binding must match a complete local clause with both explicit named-title spans. No adjacent heading, previous paragraph, name dictionary, ordering or generic 師/祖 pronoun supplies an endpoint. Headings/list/verse, self-dialogue, robe phrases, negation/ambiguity, chained triggers and inline omitted/gaiji boundaries fail closed. Source XML streams in64K blocks, with at most6307 projected characters retained per real local unit; no full XML tree or corpus is loaded.

Each candidate would remain unreviewed; identity references require an exact verified embedded ID, with DILA primary and Marcus secondary only. The real source inventory has no person-name/identity annotations or authority refs, so all ID fields in the862 records are null. No internal candidate hash is a person/authority ID. No date or generation is inferred; juan is a source fascicle locator.

## 6. Comparison meaning

The four requested lists are jingde-comparison.json → lists.overlap, lists.new_to_comparable_snapshot, lists.reverse_review, lists.conflict_review. They are all empty because there are0 eligible candidates, not because no historical overlap/conflict exists. There are 7 selected typed ZTJ observations / 5 unique typed keys; 513 CSV/GEXF observations are excluded as direction evidence. Only exact external IDs, same type and same direction can produce an overlap. Different types can coexist; reverse is only a review signal. Absence is not negation. Same-work exports/passages are not independent sources.

## 7. Commands and checks

From this directory, run:

    python -X utf8 extract_jingde.py
    python -X utf8 -B test_jingde.py

Default extraction is read-only dry-run. The initial write used --write, which refuses existing outputs; use a fresh isolated copied report/tool environment for regeneration rather than overwriting these files. Tests:6/6 methods PASS,18 grammar fixtures; all862 quotation/projection/XML-span hashes and input/source hashes verified. No product pipeline or historical/identity acceptance test is claimed.

Implementation notes: an initial broad filename walk timed out, then the exact configured xml-p5-full path was used. A JavaScript string-quoting attempt failed before file changes; the corrected runner produced the saved dry-run/write receipts. No extraction heuristics were widened after the initial zero result.

## 8. Boundaries and unfinished work

Historical recall, manual assessment of excluded passages and ID verification remain unfinished. Wider grammar or human-reviewed name/role binding would require a separately scoped change; the current files must not be imported as accepted relations. No public/production integration, migration, ID minting or generation conversion is authorized by these artifacts.

## 9. Rollback

No DB/TTL rollback is needed. These are new isolated derived files only. Retain or archive this exact directory; do not delete the source or any neighboring survey. Original source and ZTJ files were opened read-only and their hashes were checked again.

## 10. Next-agent handoff

Read jingde-quality-report.md and the source/manifest hashes before interpreting counts. Check the fixture PASS and real862record integrity. Do not interpret empty comparison lists as negative evidence. No API/network call is part of this dataset run; root can record the overall session observation separately. No stage/commit, task ID allocation, tasktodo/dashboard or earlier session/Handoff changes were made.
