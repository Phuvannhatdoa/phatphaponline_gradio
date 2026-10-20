# T.2076 strict lexical candidate quality report

## Scope and pinned source
Source: immutable local CBETA xml-p5-full T/T51/T51n2076.xml, 3,691,202 bytes. SHA256 a3942d421828f6372c1853f58daeb19299e4c91ab701a711167b3610ffaf507b. Header fragment SHA256 63a17a1a3feca6a847c4edd4d79686138cdb3d4848dcbdba31fd841e85e92ddb; source rights notice retained exactly. No production data was read or mutated except the explicitly authorized immutable source read.

## Measured extraction
- Approved trigger occurrences: 862
- Unreviewed named-role candidates: 0
- Excluded occurrences: 862
- Candidates with two verified external IDs: 0
- Maximum retained local projection: 6307 characters. Source streamed in64K chunks; no full XML tree.

## Strictness and known false negatives
Only complete local clauses matching six closed two-named-title role templates qualify. Both names must appear in the same clause. Headings/lists/verse, pronouns/self-dialogue, robe context, negation/ambiguity, chained triggers, inline omitted/gaiji ambiguity and missing named bindings are excluded. Bio headings, previous paragraphs, proximity/order, unapproved verbs and name dictionaries never supply an endpoint. This deliberately misses valid claims expressed with bare names, pronouns or other syntax; it is not a corpus-complete genealogy or a historical judgment.

## Exclusion counts
{
  "missing_explicit_two_named_role_binding_in_same_clause": 177,
  "heading_list_or_verse_context": 644,
  "pronoun_or_self_reference_not_named_binding": 13,
  "gaiji_or_omitted_inline_content_ambiguity": 5,
  "negated_or_ambiguous_claim": 4,
  "self_referential_dialogue": 1,
  "robe_or_robe_transmission_context": 2,
  "multiple_trigger_or_chained_role_ambiguity": 16
}

## Identity and comparison limits
No DILA/Marcus identity tags/authority references were found in the authorized source inventory. Candidate IDs remain null unless an exact verified embedded reference is present; label similarity is not used. Empty overlap/new/reverse/conflict lists cannot be read as no overlap or historical novelty. Missing identities are listed unresolved.
The ZTJ comparison uses only explicit typed/directed roles from the ten-case panel. Its CSV/GEXF rows are undirected. All same-work source variants/passages stay one source complex, not independent confirmation. Absence is not negation; different types can coexist.

## Rights and review block
Header says non-commercial use with header intact. Header fragment is a byte-exact XML fragment inheriting namespaces from the original TEI root; it is not a standalone reserialized document. This local derived survey grants no rights to production data or public/commercial reuse. Candidates and automated exclusions remain for review; no accepted relation or generation inference exists.

## Commands / validation
python -X utf8 extract_jingde.py (default dry-run)
python -X utf8 extract_jingde.py --write (exclusive new outputs only)
python -X utf8 test_jingde.py (synthetic fixtures; separate from real dataset)

Source and three ZTJ input hashes are checked before/after extraction. Tests and final manifest are reported separately. No API, importer, production pipeline or historical validation was run.
