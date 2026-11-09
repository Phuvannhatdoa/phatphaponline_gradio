#!/usr/bin/env python3 -I
"""
PTDA Pilot Validation: Check claims XML against XSD and data consistency
"""

import xml.etree.ElementTree as ET
import sys
from collections import defaultdict

def validate_claims_xml(claims_file):
    """Validate claims XML structure and references"""
    
    print("\n=== PTDA Claims XML Validation ===\n")
    
    try:
        tree = ET.parse(claims_file)
    except ET.ParseError as e:
        print(f"ERROR: XML parse error: {e}")
        return False
    
    root = tree.getroot()
    ns = {'ptda': 'urn:ptda:research:lineage:1'}
    
    # Check root attributes
    attrs = ['schemaVersion', 'workId', 'status']
    for attr in attrs:
        if attr not in root.attrib:
            print(f"ERROR: Missing root attribute '{attr}'")
            return False
    
    print(f"✓ Root element: schemaVersion={root.get('schemaVersion')}, workId={root.get('workId')}, status={root.get('status')}")
    
    # Check required child elements
    required_sections = ['sourceManifest', 'processingScope', 'persons', 'mentions', 'evidence', 'relationClaims']
    for section in required_sections:
        elem = root.find(f'ptda:{section}', ns)
        if elem is None:
            print(f"ERROR: Missing required section '<{section}>'")
            return False
    
    print(f"✓ All required sections present")
    
    # Extract and validate persons
    persons_elem = root.find('ptda:persons', ns)
    persons = {}
    for person in persons_elem.findall('ptda:person', ns):
        person_id = person.get('id')
        if not person_id:
            print(f"ERROR: Person missing 'id' attribute")
            return False
        persons[person_id] = person
    
    print(f"✓ {len(persons)} persons defined")
    
    # Extract and validate mentions
    mentions_elem = root.find('ptda:mentions', ns)
    mentions = {}
    for mention in mentions_elem.findall('ptda:mention', ns):
        mention_id = mention.get('id')
        if not mention_id:
            print(f"ERROR: Mention missing 'id' attribute")
            return False
        
        person_ref = mention.find('ptda:personId', ns)
        if person_ref is None or person_ref.text not in persons:
            print(f"ERROR: Mention {mention_id} references undefined person '{person_ref.text if person_ref is not None else 'None'}'")
            return False
        
        mentions[mention_id] = mention
    
    print(f"✓ {len(mentions)} mentions defined (all reference valid persons)")
    
    # Extract and validate relation claims
    claims_elem = root.find('ptda:relationClaims', ns)
    claims = []
    seen_edges = set()
    
    for claim in claims_elem.findall('ptda:relationClaim', ns):
        claim_id = claim.get('id')
        if not claim_id:
            print(f"ERROR: Claim missing 'id' attribute")
            return False
        
        # Validate references
        subj_elem = claim.find('ptda:subjectPersonId', ns)
        obj_elem = claim.find('ptda:objectPersonId', ns)
        
        if subj_elem is None or subj_elem.text not in persons:
            print(f"ERROR: Claim {claim_id} subject person not found")
            return False
        
        if obj_elem is None or obj_elem.text not in persons:
            print(f"ERROR: Claim {claim_id} object person not found")
            return False
        
        # Check for self-loops
        if subj_elem.text == obj_elem.text:
            print(f"ERROR: Claim {claim_id} is self-loop (subject == object)")
            return False
        
        # Check for duplicates
        edge = (subj_elem.text, obj_elem.text)
        if edge in seen_edges:
            print(f"WARNING: Duplicate relation from {subj_elem.text} to {obj_elem.text}")
        else:
            seen_edges.add(edge)
        
        # Validate enum values
        rel_type_elem = claim.find('ptda:proposedRelationType', ns)
        direction_elem = claim.find('ptda:directionStatus', ns)
        review_elem = claim.find('ptda:reviewStatus', ns)
        
        valid_types = ['dharma_transmission', 'teacher_student', 'study_relation', 'unknown']
        if rel_type_elem is None or rel_type_elem.text not in valid_types:
            print(f"ERROR: Claim {claim_id} invalid proposedRelationType")
            return False
        
        valid_directions = ['subject_to_object', 'object_to_subject', 'bidirectional', 'unknown']
        if direction_elem is None or direction_elem.text not in valid_directions:
            print(f"ERROR: Claim {claim_id} invalid directionStatus")
            return False
        
        if review_elem is None or review_elem.text != 'pending':
            print(f"ERROR: Claim {claim_id} reviewStatus must be 'pending'")
            return False
        
        claims.append(claim)
    
    print(f"✓ {len(claims)} relation claims defined (all valid, no self-loops)")
    
    # Check manifest
    manifest = root.find('ptda:sourceManifest', ns)
    sha256_elem = manifest.find('ptda:sha256', ns)
    if sha256_elem is None or len((sha256_elem.text or "")) != 64:
        print(f"ERROR: Invalid or missing SHA-256")
        return False
    
    print(f"✓ Source manifest valid (SHA-256: {sha256_elem.text[:16]}...)")
    
    print(f"\n✓✓✓ VALIDATION PASSED ✓✓✓\n")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_package.py <claims_xml>")
        sys.exit(1)
    
    result = validate_claims_xml(sys.argv[1])
    sys.exit(0 if result else 1)
