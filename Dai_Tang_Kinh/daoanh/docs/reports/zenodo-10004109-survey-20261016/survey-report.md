# Zenodo 10004109 — isolated Van Cutsem survey

## 1. Scope and status

- Survey completed on 2026-10-16; source integrity/structure validation PASS (24 checks). Reuse/identity/lineage acceptance was not performed.
- Workspace: `daoanh/docs/reports/zenodo-10004109-survey-20261016`. All authored files are confined to this new directory. Production DB/TTL/corpus files were neither read nor written. No package file was executed; no ETL, application importer, paid API, staging or commit was run.
- Repository HEAD observed for provenance: `8f53bf014862863bb2710f331b1b71a0218d5166`; shared worktree may advance independently.

## 2. Authoritative source and download

[Zenodo record](https://zenodo.org/records/10004109), DOI `10.5281/zenodo.10004109`, published 2023-10-15. API record revision 6, updated 2023-10-21. Record metadata, response headers and exact download URL are preserved in `record-metadata.json` and `download-receipt.json`.

- ZIP: `historicalNetworkAnalysisChineseReligion2023-10.zip`; 86,334,571 bytes.
- Zenodo MD5 and locally verified MD5: `78c722a304d06962a12f9899d5442e3e`.
- Local SHA256: `60d7c0333860a6ce4e76a82e3f08f6d4e943fc6def272108b2571139d648e811`.
- ZIP downloaded from the API file-content link using HTTPS; bounded streaming, exclusive creation and advertised size/checksum gates. Initial sandbox Node HTTPS failed EACCES; the authorized public-download escalation succeeded. Archive is preserved unchanged under ignored `download/`.

## 3. Extraction safety and package inventory

`archive-inventory.json` records 92 ZIP entries (85 files, 7 directories), 93,744,855 uncompressed bytes. Safety checks found zero errors; extraction used exclusive file writes and streamed reads. Traversal/absolute paths, Windows reserved/ADS paths, case collisions, symlinks/special/encrypted files and configured size/ratio limits were rejected. Every extracted file has a SHA256 in `extraction-manifest.json`; all 85 hashes were checked again.

Package formats: PNG 44; Gephi 6; TXT 7; MD 7; CSV 6; XLSX 8; GEXF 1; XML 5; RNG 1. Raw ZIP and `extracted/` are ignored by the survey-local `.gitignore`; `git check-ignore --no-index` confirmed both paths (global ignore-file read warning did not prevent these matches). No nested archive was executed or automatically unpacked.

## 4. Rights notices, attribution and conflict

All seven `01-README.md` and seven `02-license.txt` files were read/screened. The seven license texts are byte-identical (18,656 bytes each; SHA256 `9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94`). They identify CC BY 4.0, consistent with record metadata. Readme license locators: Bingenheimer 33–38; Chen 67–72; Chu 29–34; Goossaert 32–37; Nehrdich 36–41; Sokolova 33–38; Van Cutsem 45–50.

**Per-file conflict:** each of the four `vancutsem_laurent/03-*.xml` TEI editions contains a CC BY-NC-SA 4.0 declaration at line 36. Each also retains the CBETA / Lán Jífù copyright context at line 63. The broad README/record notice does not resolve or override this narrower notice. Retain both and obtain clarification before redistribution/integration that depends on a single license. No package license was copied to the project root or applied to project code/data.

Van Cutsem README credits data collection to Laurent Van Cutsem and editing/archiving to Marcus Bingenheimer (lines 40–43); article: [Lineages as Network](https://doi.org/10.3390/rel14020205). `analysis/rights-and-file-selection.json` stores all detected text-notice locators. `analysis/embedded-rights-inspection.json` screens nested Gephi/XLSX XML/text and PNG text metadata: no additional explicit grant/restriction was found; one unrelated Nehrdich PNG contains empty XMP copyright/licensor fields. No OCR of image pixels or undocumented binary fields was attempted; absence of a match is not rights clearance.

## 5. Van Cutsem files (17 files; 8,988,130 bytes)

All paths below are relative to `extracted/vancutsem_laurent/`; exact sizes/hashes are in `analysis/network-analysis.json` and `extraction-manifest.json`.

| File | Format / role | Measured structure |
|---|---|---|
| `01-README.md` | package description | 50 lines; file roles, credits and CC BY notice |
| `02-license.txt` | license text | CC BY 4.0; 395 lines |
| `03-zutangji-haidongxinkaiyinbanji_SNA.xml` | TEI edition, Goryeo-preface notes | 334 persName mentions; 252 linkGrp / 252 link |
| `03-zutangji-zutangjixu_SNA.xml` | TEI original preface | 3 persName; 3 linkGrp / 3 link |
| `03-zutangji_supp_SNA_caotang.xml` | partial TEI entry | 8 persName; 4 linkGrp / 4 link |
| `03-zutangji_supp_SNA_xinghua.xml` | partial TEI entry | 2 persName; 1 linkGrp / 1 link |
| `04-schema.rng` | Relax NG schema | 678,815 bytes; not executed/validated as a schema in this survey |
| `04-schema_ODD.xml` | TEI ODD customization | 2,344 bytes |
| `05-ZTJ_edges_ZTJmain.csv` | comma-separated edge table | 256 data records; 5 fields; zero ragged records |
| `05-ZTJ_nodes_full.xlsx` | detailed node workbook | Sheet1: 266 row elements, 263 nonempty rows, dimension A1:R267; no formulas |
| `05-ZTJ_nodes_simplified.csv` | semicolon-separated node table | 260 data records / 260 unique source IDs; 7 fields; zero ragged records |
| `06-ZTJ_fullTable.xlsx` | book-structure table | Sheet1: 354 row elements, 335 nonempty rows, dimension A1:V354; no formulas |
| `07-ztjLinkGrps.gexf` | static GEXF 1.2draft | 260 node elements / 257 edge elements |
| `08-ZTJ_lineages_complete.png` | network figure | source visualization only |
| `08-ZTJ_lineages_lengthEntries_drag.png` | network figure | source visualization only |
| `08-ZTJ_lineages_noCertLow_genPart.png` | filtered network figure | source visualization only |
| `08-ZTJ_lineages_noCertLow_korHighlight.png` | filtered network figure | source visualization only |

Worksheet nonempty-row counts include headers/notes and must not be treated as unique people. Full workbook source cells are not rewritten or recalculated; row/cell counts and first-row evidence are in `analysis/workbook-analysis.json`.

## 6. Counts and semantic boundaries

- CSV and GEXF use exactly the same 260 source node IDs. All match `A` plus six digits; README lines 31–32 says they reference DILA. This survey did not verify any live DILA identity or project mapping. Labels 龍潭, 石霜, 鵝湖 and 報慈 each occur twice, so names alone cannot identify records.
- CSV has 256 edges and explicitly declares every Type as Undirected. GEXF has 257 edges, graph defaultedgetype=undirected, and no per-edge override. Source/Target order therefore is not an accepted teacher–disciple direction.
- Comparing ordered source endpoint pairs, GEXF has one extra pair `A004166` / `A000587`; no CSV-only pair. This is a source-version discrepancy, not an automatically repairable error. Both formats have zero dangling endpoints and zero self-edges in this snapshot. See `analysis/source-comparison.json`.
- Four TEI editions contain 347 persName mention elements and 260 linkGrp/link elements in total; mentions are not unique persons and linkGrp is not automatically one accepted lineage edge. TEI namespace is `http://www.tei-c.org/ns/1.0`. The Goryeo file has 41 linkGrp elements with cert=low and 211 without cert. Preserve uncertainty, nested markup, source locators and edition context; absence of cert is not acceptance. See `analysis/tei-analysis.json` and `analysis/validation.json`.
- Source generation numbering begins with the past seven Buddhas (sample first record 毗婆尸佛, generation string 1); no conversion to PTDA generation conventions was made. GEXF birthY/deathY and CSV generation fields remain source values, not verified canonical dates/numbers.
- GEXF node attributes: birthY, deathY, gender, nationality; edge attributes: ref, timeFrom, timeTo. CSV edge references include CBETA line locators. Preserve them as source evidence rather than inferring semantics from field names.

## 7. Exported samples and artifacts

- [10 nodes](analysis/sample-nodes-10.json): exact first 10 data records from the simplified CSV, original strings/fields and order.
- [10 edges](analysis/sample-edges-10.json): exact first 10 data records from the main edge CSV, including Undirected and e@ref.
- Both samples carry source file SHA256, record/article URLs, author/editor, selection method, scoped notice and `unmapped source_asserted` status. No values were inferred or promoted to accepted.
- Supplementary numbered samples from GEXF are also retained; empty node/edge samples for non-graph TEI files are diagnostic outputs, not missing person data. The two named sample files above are the requested deliverables.
- `manifest.json` inventories survey files, ownership scope, checksums and raw-data exclusions; `SHA256SUMS.txt` includes the manifest hash. Its own hash is reported separately (no circular self-hash).

## 8. Commands and validation

Commands run from daoanh (utility outcomes retained in `analysis/*-command.json`; download metadata, HTTP headers and checksum outcome in `download-receipt.json`):

```text
python -X utf8 docs/reports/zenodo-10004109-survey-20261016/download_record.py
python -X utf8 docs/reports/zenodo-10004109-survey-20261016/inspect_archive.py
python -X utf8 docs/reports/zenodo-10004109-survey-20261016/inspect_archive.py --extract
python -X utf8 docs/reports/zenodo-10004109-survey-20261016/scan_notices.py
python -X utf8 docs/reports/zenodo-10004109-survey-20261016/analyze_networks.py
python -X utf8 docs/reports/zenodo-10004109-survey-20261016/inspect_extended.py
python -X utf8 docs/reports/zenodo-10004109-survey-20261016/inspect_embedded_notices.py
python -X utf8 docs/reports/zenodo-10004109-survey-20261016/validate_survey.py
```

All exited 0. Validation PASS: 24 integrity/structure/sample checks; 7 utility scripts parse; 6 XML/GEXF results are unchanged after bounded subtree-clearing correction. Downloads/extraction use chunked streams; XML subtrees are cleared; tables here are tiny (<300 CSV records each), and larger worksheet rows are iterated. Survey utilities refuse output overwrite, so reproduce in a fresh isolated directory rather than rerun destructive extraction in place. These local analysis tools are not production importers. Product guard/pipeline/tester and production API checks were not run: this is a survey, with no application change or build-review claim.

## 9. Limits, rollback and next review

No historical claims, DILA identity, teacher direction, generation or canonical date was accepted. No OCR, image-semantic reading, schema validation, Gephi application execution, formula recalculation or full historical-source verification was performed. Rights conflict remains open for any future reuse decision; structure PASS does not resolve it.

Rollback needs no DB/TTL restoration: leave the directory isolated or archive this survey only after verifying its exact resolved path. Do not recursively delete project directories or alter original ZIP/extracted evidence. Root/Debug can independently verify hashes, source counts, exact samples, and the TEI rights/uncertainty locators before planning a separate integration scope.

## 10. Session handoff

All new content is under this survey directory; no prior Handoff/session, tasktodo, dashboard, production data or Git index/ref was edited. Memory quick-pass had no relevant hits. Local observation POST result is recorded in `analysis/observation-post.json`; it does not affect survey validity. Outstanding follow-up belongs to root QA: decide whether a future source-specific rights/semantics investigation is appropriate; no import is authorized by this report.
