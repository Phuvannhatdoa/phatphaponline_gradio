with open('scripts/t457_staging_v4.py','r',encoding='utf-8') as f:
    s=f.read()

old1 = '''        # Extract person_id
        pers = __import__('re').findall(r'<person id="([A-Z0-9]+)"', nexus_full)
        if pers:
            rec["person_id"] = pers[0]
        
        # Extract place_id
        place = __import__('re').findall(r'<place id="([A-Z0-9]+)"', nexus_full)
        if place:
            rec["place_id"] = place[0]'''

new1 = '''        # Extract person_ids (all)
        pers = __import__('re').findall(r'<person id="([A-Z0-9]+)"', nexus_full)
        rec["person_ids"] = pers if pers else []
        
        # Extract place_ids (all)
        place = __import__('re').findall(r'<place id="([A-Z0-9]+)"', nexus_full)
        rec["place_ids"] = place if place else []'''

if old1 in s:
    s = s.replace(old1, new1)
    with open('scripts/t457_staging_v4.py','w',encoding='utf-8') as f:
        f.write(s)
    print('REPLACED')
else:
    print('NOT FOUND - search for pattern')
    # Debug: find the lines
    for i,line in enumerate(s.split('\n'),1):
        if 'person_id' in line or 'place_id' in line:
            print(i, repr(line))