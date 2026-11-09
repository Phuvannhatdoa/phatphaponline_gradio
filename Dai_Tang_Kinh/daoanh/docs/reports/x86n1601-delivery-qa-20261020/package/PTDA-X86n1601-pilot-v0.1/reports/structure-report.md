# Structure Report: Thiền Đăng Thế Phổ (X86n1601) XML Analysis

## XML Structure Overview

### Root Element
- **Element**: `<TEI>` (TEI P5)
- **Encoding**: UTF-8
- **Namespace**: `http://www.tei-c.org/ns/1.0` (TEI), `http://www.cbeta.org/ns/1.0` (CBETA extensions)

### Body Structure

```
<body>
  <pb/>           (7 page break markers)
  <milestone/>    (9 milestone markers)
  <cb:juan/>      (17 juan/chapter markers)
  <cb:div/>       (19 CBETA div elements)
    - type="xu" (preface) - 2 divs
    - type="other" (content) - 17 divs
  <lb/>           (120 line break markers)
</body>
```

### Lineage Representation

**Location**: First `<cb:div type="other">` containing "三十三祖世系圖" (33 Patriarchs Genealogy Chart)

**Structure**:
```
<cb:div type="other">
  <cb:mulu>三十三祖世系圖</cb:mulu>
  <tei:head>三十三祖世系圖</tei:head>
  <tei:list rend="no-marker">
    <tei:item xml:id="itemX86p0320a2001">
      <tei:note place="inline">始祖</tei:note>釋迦牟尼佛<tei:note place="inline">釋迦文佛</tei:note>
      <tei:lb/>
      <tei:list rend="no-marker">
        <tei:item>
          <tei:p>即賢劫第四尊示生中天竺國...</tei:p>
          <tei:lb/>
          <tei:p>穆王三十六年壬申二月十五日中夜入滅。後一千一十七年，教被華夏...</tei:p>
          <tei:lb/>
          <tei:p>按傳燈諸錄，首紀七佛...</tei:p>
        </tei:item>
      </tei:list>
    </tei:item>
    ...
  </tei:list>
</cb:div>
```

### Key Elements

| Element | Purpose | Count |
|---------|---------|-------|
| `<tei:item>` | Patriarch entry | 34 (top-level) |
| `<tei:note>` | Generation label (始祖, 第一祖, etc.) | 34+ |
| `<tei:list>` | Nested biographical information | 35 |
| `<tei:p>` | Paragraph of biography/transmission info | 120+ |
| `<tei:lb>` | Line breaks (page/column markers) | 120 |
| `<tei:pb>` | Page breaks with location markers | 156 |

### Transmission Encoding

**Format**: Embedded in biographical text within `<tei:p>` paragraphs

**Keywords indicating transmission**:
- 付囑 (entrust)
- 乃以 (then with)
- 後付 (later transmitted)
- 傳付 (transmitted)

**Example**:
```
釋迦牟尼佛: "...乃以大法印付囑摩訶迦葉。"
           (then entrust the dharma seal to Mahakashyapa)
           
摩訶迦葉: "...後付阿難..."
         (later transmitted to Ananda)
```

### Unresolved Structure Issues

- **Pre-patriarchal sections**: Juan 002-009 not examined; may contain different lineage formats
- **Branch lineages**: After the 33 patriarchs, branches exist (如 曹溪大鑑 下 = under Hui-neng); structure not verified
- **Table/diagram markup**: References to "世系圖" (genealogy charts) present but not yet parsed for branch structures
- **Alternative names**: Multiple `<tei:note>` elements per patriarch (main name + alternative); only first name extracted

### Data Quality Notes

- **Normalization applied**: Text whitespace normalized (multiple spaces/lines → single space)
- **Encoding**: CBETA uses PUA (Private Use Area) characters and composition mappings for rare characters; preserved as-is in source
- **Line markers**: `<tei:lb ed="X" n="0320a19"/>` encodes page/column/line position in CBETA edition X and other editions (R147, etc.)

---
**Report Date**: 2026-10-20  
**Source**: X86n1601.source.xml  
**SHA-256**: 60a282bf78795048395dfdb6ab2ac0d7912bbd6b527338d9664f58994e84f178
