T457 DILA Bio Nexus Staging Report (QA-Fixed V4)
==================================================
Source files: 11
Total nexus records: 21740
Total with year: 7066
Duplicate nexus_ids: 0 (FAIL if >0)
Book null when source has value: 0/21740 (FAIL if >0)
Year outside 500-3000: 1068/21740 (FAIL if >0)
Empty text_zh: 0/21740 (FAIL if >0)

Per-file breakdown:
  - Buxu_GSZ.nexus.xml: 0 records, 1004 with year, book=Buxu_GSZ, anchors=7942, SHA256=f391f38a02bae10c...
  - Jushi_Zhuan.nexus.xml: 0 records, 211 with year, book=Jushi_Zhuan, anchors=1046, SHA256=e4daa95e7bcab27f...
  - Liang_GSZ.nexus.xml: 0 records, 562 with year, book=Liang_GSZ, anchors=3638, SHA256=b0c0703f2832f6fc...
  - Ming_GSZ.nexus.xml: 0 records, 199 with year, book=Ming_GSZ, anchors=1174, SHA256=11e9a4fd39a5aac9...
  - Mingsengzhuanchao.nexus.xml: 0 records, 26 with year, book=Mingsengzhuanchao, anchors=376, SHA256=24f4904d36418069...
  - OtherSources.nexus.xml: 0 records, 0 with year, book=OtherSources, anchors=326, SHA256=067c9a29473ee3d1...
  - Song_GSZ.nexus.xml: 0 records, 1793 with year, book=Song_GSZ, anchors=10484, SHA256=9223657e367cdbc8...
  - Tang_GSZ.nexus.xml: 0 records, 2208 with year, book=Tang_GSZ, anchors=10892, SHA256=23a51436d875bad8...
  - Xinxu_GSZ.nexus.xml: 0 records, 741 with year, book=Xinxu_GSZ, anchors=5910, SHA256=f9c1f58539282706...
  - biQiuNi.nexus.xml: 0 records, 191 with year, book=biQiuNi, anchors=746, SHA256=8dd83805020af0b6...
  - chuSanZangJiJi.nexus.xml: 0 records, 131 with year, book=chuSanZangJiJi, anchors=946, SHA256=eb43ab5a1c9352e1...

Validation summary:
  X duplicate nexus_ids: 0 (QA requirement: must be unique per source_file + id)
  X book null when source has value: 0/21740 (QA: source provides book from root element)
  X year out of range 500-3000: 1068/21740
  X empty text_zh: 0/21740 (QA: all records have text_zh)
  X manifest complete: all required fields present

Constraints:
  □ No --apply (dry-run only)
  □ No DB modification
  □ No Vietnamese translation
  □ Read-only source files

QA Status: REVIEW NEEDED - see stats above

Next: Admin decides T458 path (Option A/B/C)