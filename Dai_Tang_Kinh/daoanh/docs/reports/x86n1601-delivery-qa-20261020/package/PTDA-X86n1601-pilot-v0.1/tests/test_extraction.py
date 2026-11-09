#!/usr/bin/env python3 -I
"""
PTDA Pilot Tests: Verify correct extraction and edge cases
"""

import xml.etree.ElementTree as ET
import sys

def test_extraction():
    """Test suite for pilot extraction"""
    
    claims_file = "/tmp/claude-0/-home-user-phatphaponline-gradio/1b7ea339-bb3d-5748-b1c2-973954ef2865/scratchpad/ptda_src/X86n1601.pilot.claims.xml"
    
    tree = ET.parse(claims_file)
    root = tree.getroot()
    ns = {'ptda': 'urn:ptda:research:lineage:1'}
    
    tests_passed = 0
    tests_failed = 0
    
    print("\n=== PTDA Pilot Extraction Tests ===\n")
    
    # Test 1: First patriarch correctly extracted
    print("TEST 1: First patriarch (Shakyamuni Buddha) correctly extracted")
    persons_elem = root.find('ptda:persons', ns)
    first_person = persons_elem.find("ptda:person[@id='person_000']", ns)
    if first_person is not None:
        name_elem = first_person.find('ptda:nameZh', ns)
        if name_elem is not None and "釋迦" in name_elem.text:
            print("  ✓ PASS: First patriarch name contains '釋迦'\n")
            tests_passed += 1
        else:
            print(f"  ✗ FAIL: Name is '{name_elem.text if name_elem is not None else 'None'}'\n")
            tests_failed += 1
    else:
        print("  ✗ FAIL: First person not found\n")
        tests_failed += 1
    
    # Test 2: Transmission chain starts correctly
    print("TEST 2: Transmission from Shakyamuni to Mahakashyapa")
    claims_elem = root.find('ptda:relationClaims', ns)
    first_claim = None
    for claim in claims_elem.findall('ptda:relationClaim', ns):
        subj = claim.find('ptda:subjectPersonId', ns)
        obj = claim.find('ptda:objectPersonId', ns)
        if subj is not None and subj.text == 'person_000':
            first_claim = claim
            break
    
    if first_claim is not None:
        obj_elem = first_claim.find('ptda:objectPersonId', ns)
        # Should transmit to person_001 (first patriarch)
        if obj_elem is not None and obj_elem.text == 'person_001':
            print("  ✓ PASS: Transmission goes from person_000 to person_001\n")
            tests_passed += 1
        else:
            print(f"  ✗ FAIL: Transmits to {obj_elem.text if obj_elem is not None else 'None'}\n")
            tests_failed += 1
    else:
        print("  ✗ FAIL: No transmission claim found for first patriarch\n")
        tests_failed += 1
    
    # Test 3: All relations have pending review status
    print("TEST 3: All relation claims have 'pending' review status")
    all_pending = True
    for claim in claims_elem.findall('ptda:relationClaim', ns):
        review = claim.find('ptda:reviewStatus', ns)
        if review is None or review.text != 'pending':
            all_pending = False
            break
    
    if all_pending:
        print("  ✓ PASS: All claims have review_status='pending'\n")
        tests_passed += 1
    else:
        print("  ✗ FAIL: Some claims have non-pending status\n")
        tests_failed += 1
    
    # Test 4: No self-loops
    print("TEST 4: No self-referential relations (self-loops)")
    has_selfloop = False
    for claim in claims_elem.findall('ptda:relationClaim', ns):
        subj = claim.find('ptda:subjectPersonId', ns)
        obj = claim.find('ptda:objectPersonId', ns)
        if subj is not None and obj is not None and subj.text == obj.text:
            has_selfloop = True
            print(f"  Found self-loop: {subj.text}")
            break
    
    if not has_selfloop:
        print("  ✓ PASS: No self-loops detected\n")
        tests_passed += 1
    else:
        print("  ✗ FAIL: Self-loop found\n")
        tests_failed += 1
    
    # Test 5: All referenced persons exist
    print("TEST 5: All referenced persons in claims exist in persons list")
    persons_dict = {}
    for person in persons_elem.findall('ptda:person', ns):
        person_id = person.get('id')
        persons_dict[person_id] = person
    
    refs_valid = True
    for claim in claims_elem.findall('ptda:relationClaim', ns):
        subj = claim.find('ptda:subjectPersonId', ns)
        obj = claim.find('ptda:objectPersonId', ns)
        if subj.text not in persons_dict or obj.text not in persons_dict:
            refs_valid = False
            break
    
    if refs_valid:
        print(f"  ✓ PASS: All {len(list(claims_elem.findall('ptda:relationClaim', ns)))} claims reference existing persons\n")
        tests_passed += 1
    else:
        print("  ✗ FAIL: Some claims reference undefined persons\n")
        tests_failed += 1
    
    # Test 6: Source SHA-256 is valid
    print("TEST 6: Source SHA-256 hash is valid format (64 hex chars)")
    manifest = root.find('ptda:sourceManifest', ns)
    sha256_elem = manifest.find('ptda:sha256', ns)
    sha256 = sha256_elem.text if sha256_elem is not None else ""
    
    if len(sha256) == 64 and all(c in '0123456789abcdef' for c in sha256.lower()):
        print(f"  ✓ PASS: SHA-256 = {sha256[:16]}...\n")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: Invalid SHA-256: {sha256}\n")
        tests_failed += 1
    
    # Test 7: Evidence fragments are not empty
    print("TEST 7: All claims have non-empty evidence fragments")
    empty_evidence = False
    for claim in claims_elem.findall('ptda:relationClaim', ns):
        evidence = claim.find('ptda:evidenceFragment', ns)
        if evidence is None or not evidence.text or len(evidence.text.strip()) == 0:
            empty_evidence = True
            break
    
    if not empty_evidence:
        print("  ✓ PASS: All claims have evidence text\n")
        tests_passed += 1
    else:
        print("  ✗ FAIL: Some claims have empty evidence\n")
        tests_failed += 1
    
    # Test 8: Negative test - verify no spurious relations
    print("TEST 8: Negative test - no cross-generational jumps without evidence")
    suspicious_jumps = 0
    for claim in claims_elem.findall('ptda:relationClaim', ns):
        subj_id = claim.find('ptda:subjectPersonId', ns).text
        obj_id = claim.find('ptda:objectPersonId', ns).text
        subj_num = int(subj_id.split('_')[1])
        obj_num = int(obj_id.split('_')[1])
        
        # In linear transmission, jumps should be small (within 1-3 generations in a row)
        jump = obj_num - subj_num
        if jump > 5:
            # Long jump - should be verified
            evidence = claim.find('ptda:evidenceFragment', ns).text
            if evidence and len(evidence.strip()) > 20:
                pass  # OK - has evidence
            else:
                suspicious_jumps += 1
    
    if suspicious_jumps == 0:
        print("  ✓ PASS: No suspicious long-distance relations without strong evidence\n")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL: Found {suspicious_jumps} suspicious relations\n")
        tests_failed += 1
    
    # Summary
    total = tests_passed + tests_failed
    print(f"\n{'='*40}")
    print(f"Tests: {tests_passed} passed, {tests_failed} failed out of {total}")
    print(f"{'='*40}\n")
    
    return tests_failed == 0

if __name__ == "__main__":
    result = test_extraction()
    sys.exit(0 if result else 1)
