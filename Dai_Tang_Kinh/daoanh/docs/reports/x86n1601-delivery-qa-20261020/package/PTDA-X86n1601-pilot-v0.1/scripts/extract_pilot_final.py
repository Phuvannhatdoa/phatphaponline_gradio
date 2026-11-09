#!/usr/bin/env python3 -I
"""
PTDA Lineage Extraction Final: Comprehensive text extraction
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
import hashlib
from datetime import datetime

SOURCE_FILE = "/tmp/claude-0/-home-user-phatphaponline-gradio/1b7ea339-bb3d-5748-b1c2-973954ef2865/scratchpad/ptda_src/X86n1601.source.xml"
OUTPUT_XML = "/tmp/claude-0/-home-user-phatphaponline-gradio/1b7ea339-bb3d-5748-b1c2-973954ef2865/scratchpad/ptda_src/X86n1601.pilot.claims.xml"
PTDA_NS = "urn:ptda:research:lineage:1"

def get_source_sha256(path):
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_all_text(elem):
    """Recursively extract all text from element and descendants"""
    text = elem.text or ""
    for child in elem:
        text += extract_all_text(child)
        if child.tail:
            text += child.tail
    return text.strip()

def extract_lineage_data(root):
    """Extract persons and relations from patriarchal sequence"""
    
    ns = {"tei": "http://www.tei-c.org/ns/1.0", "cb": "http://www.cbeta.org/ns/1.0"}
    body = root.find(".//tei:body", ns)
    
    if not body:
        return None, None, None
    
    divs = body.findall("cb:div", ns)
    lineage_div = None
    for div in divs:
        mulu = div.find("cb:mulu", ns)
        if mulu is not None and "三十三祖" in (mulu.text or ""):
            lineage_div = div
            break
    
    if not lineage_div:
        return None, None, None
    
    main_list = lineage_div.find("tei:list", ns)
    if main_list is None:
        return None, None, None
    
    items = main_list.findall("tei:item", ns)
    
    # Extract persons
    persons = {}
    
    for idx, item in enumerate(items):
        xml_id = item.get("{http://www.w3.org/XML/1998/namespace}id", f"item_{idx}")
        
        note = item.find("tei:note", ns)
        if note is None:
            continue
        
        gen_label = note.text or ""
        name_text = (note.tail or "").strip()
        name_zh = name_text.split()[0] if name_text else ""
        
        if not name_zh:
            continue
        
        # Extract biographical text - use recursive extraction from nested list
        nested_list = item.find("tei:list", ns)
        bio_text = ""
        
        if nested_list is not None:
            bio_text = extract_all_text(nested_list)
            # Remove excessive whitespace and line breaks
            bio_text = " ".join(bio_text.split())
        
        persons[idx] = {
            "id": f"person_{idx:03d}",
            "name_zh": name_zh,
            "gen_label": gen_label,
            "bio_text": bio_text,
            "xml_id": xml_id
        }
    
    print(f"Extracted {len(persons)} persons with biographies", file=sys.stderr)
    
    # Debug: print first 10 persons with bio lengths
    for idx in sorted(persons.keys())[:10]:
        p = persons[idx]
        print(f"  [{idx}] {p['gen_label']:6} {p['name_zh']:15} bio={len(p['bio_text']):4} chars", file=sys.stderr)
    
    # Extract relations
    mentions = []
    relations = []
    relation_counter = 0
    
    for idx, person in persons.items():
        bio_text = person["bio_text"]
        name_zh = person["name_zh"]
        
        mentions.append({
            "mention_id": f"mention_{idx:03d}",
            "person_id": person["id"],
            "text": name_zh,
            "context": f"Generation: {person['gen_label']}",
            "xml_path": f"//*[@xml:id='{person['xml_id']}']"
        })
        
        # Look for next persons mentioned in bio
        for next_idx in range(idx + 1, min(idx + 8, len(persons))):
            if next_idx not in persons:
                continue
            
            next_person = persons[next_idx]
            next_name = next_person["name_zh"]
            
            if next_name in bio_text:
                relation_counter += 1
                
                pos = bio_text.index(next_name)
                context_start = max(0, pos - 100)
                context_end = min(len(bio_text), pos + 100)
                evidence = bio_text[context_start:context_end]
                
                relations.append({
                    "claim_id": f"claim_{relation_counter:04d}",
                    "subject_person_id": person["id"],
                    "subject_name": name_zh,
                    "object_person_id": next_person["id"],
                    "object_name": next_name,
                    "source_relation_term": "dharma transmission",
                    "proposed_relation_type": "dharma_transmission",
                    "direction_status": "subject_to_object",
                    "evidence_text": evidence,
                    "xml_path": f"//*[@xml:id='{person['xml_id']}']/descendant::tei:*",
                    "extraction_rule": "mention_in_biography",
                    "review_status": "pending"
                })
                break  # Stop after first successor found
    
    print(f"Extracted {len(relations)} transmission relations\n", file=sys.stderr)
    
    return persons, mentions, relations

def build_claims_xml(persons, mentions, relations, source_sha256):
    """Build PTDA claims XML"""
    
    root = ET.Element("lineageDataset")
    root.set("xmlns", PTDA_NS)
    root.set("schemaVersion", "1.0")
    root.set("workId", "X86n1601")
    root.set("status", "candidate")
    
    manifest = ET.SubElement(root, "sourceManifest")
    ET.SubElement(manifest, "fileName").text = "X86n1601.source.xml"
    ET.SubElement(manifest, "sourceUrl").text = "https://raw.githubusercontent.com/Phuvannhatdoa/phatphaponline_gradio/truyen-dang-the-pho-clean/X86n1601.xml"
    ET.SubElement(manifest, "sha256").text = source_sha256
    ET.SubElement(manifest, "downloadTime").text = datetime.utcnow().isoformat() + "Z"
    rights = ET.SubElement(manifest, "rights")
    rights.text = "CBETA 佛典寶藏. Electronic version. CC BY-NC-SA 4.0"
    
    scope = ET.SubElement(root, "processingScope")
    ET.SubElement(scope, "workId").text = "X86n1601"
    ET.SubElement(scope, "juanProcessed").text = "001 (patriarchal lineage chart)"
    ET.SubElement(scope, "estimatedRelations").text = str(len(relations))
    ET.SubElement(scope, "unprocessedSections").text = "juan 002-009"
    
    persons_elem = ET.SubElement(root, "persons")
    for idx in sorted(persons.keys()):
        pdata = persons[idx]
        p = ET.SubElement(persons_elem, "person")
        p.set("id", pdata["id"])
        ET.SubElement(p, "sourcePersonId").text = pdata["xml_id"]
        ET.SubElement(p, "nameZh").text = pdata["name_zh"]
        ET.SubElement(p, "generationLabel").text = pdata["gen_label"]
    
    mentions_elem = ET.SubElement(root, "mentions")
    for m in mentions:
        mention = ET.SubElement(mentions_elem, "mention")
        mention.set("id", m["mention_id"])
        ET.SubElement(mention, "personId").text = m["person_id"]
        ET.SubElement(mention, "text").text = m["text"]
    
    ET.SubElement(root, "evidence")
    
    claims_elem = ET.SubElement(root, "relationClaims")
    for rel in relations:
        claim = ET.SubElement(claims_elem, "relationClaim")
        claim.set("id", rel["claim_id"])
        ET.SubElement(claim, "subjectPersonId").text = rel["subject_person_id"]
        ET.SubElement(claim, "objectPersonId").text = rel["object_person_id"]
        ET.SubElement(claim, "sourceRelationTerm").text = rel["source_relation_term"]
        ET.SubElement(claim, "proposedRelationType").text = rel["proposed_relation_type"]
        ET.SubElement(claim, "directionStatus").text = rel["direction_status"]
        ET.SubElement(claim, "evidenceFragment").text = rel["evidence_text"][:500]
        ET.SubElement(claim, "extractionRule").text = rel["extraction_rule"]
        ET.SubElement(claim, "reviewStatus").text = rel["review_status"]
    
    ET.SubElement(root, "generationLabels")
    ET.SubElement(root, "unresolvedCases")
    
    return root

def format_xml(elem):
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
    print("\n=== PTDA Lineage Extraction (Final) ===\n", file=sys.stderr)
    
    source_sha256 = get_source_sha256(SOURCE_FILE)
    
    tree = ET.parse(SOURCE_FILE)
    root = tree.getroot()
    
    persons, mentions, relations = extract_lineage_data(root)
    
    if not persons:
        print("ERROR: Extraction failed", file=sys.stderr)
        sys.exit(1)
    
    claims_root = build_claims_xml(persons, mentions, relations, source_sha256)
    
    xml_str = format_xml(claims_root)
    with open(OUTPUT_XML, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"✓ Output written: {OUTPUT_XML}", file=sys.stderr)
    print(f"✓ {len(persons)} persons, {len(relations)} relations extracted", file=sys.stderr)

if __name__ == "__main__":
    main()
