with open('tasktodo.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Update line 443 (T73 IN_PROGRESS -> DONE)
old_line = '**T73 ✅ IN_PROGRESS (2026-09-10) - Admin Review Bio VI (person_bio_vi_draft 2,093 → people.bio_vi):** tab Bio Review + `/api/admin/bio-review/pending|/<pid>|/apply` + en_audit_log — **IMPLEMENTED trong worktree (T122-D3: routes app.py:13693–13825 + admin/bio-review.html)**; chờ Lee test :5000 → done. Task: `tasks/T73-admin-review-bio-vi.md`.'
new_line = '**T73 ✅ DONE (2026-10-12) - Admin Review Bio VI (person_bio_vi_draft 2,093 → people.bio_vi):** tab Bio Review + `/api/admin/bio-review/pending|/<pid>|/apply` + en_audit_log — **IMPLEMENTED trong worktree (T122-D3: routes app.py:13693–13825 + admin/bio-review.html)**; **API tested 2026-10-12: stats/list/approve/reject/bulk-approve/apply all PASS**; verified approve A001030 + apply → people.bio_vi content match; reject A001302 with note; bulk approve 39 rows. Task: `tasks/T73-admin-review-bio-vi.md`.'

if old_line in content:
    content = content.replace(old_line, new_line)
    print("Found and replaced line 443")
else:
    print("Line 443 not found, trying alternative...")
    # Try with HTML entity
    old_line2 = '**T73 ✅ IN_PROGRESS (2026-09-10) - Admin Review Bio VI (person_bio_vi_draft 2,093 → people.bio_vi):** tab Bio Review + `/api/admin/bio-review/pending|/<pid>|/apply` + en_audit_log — **IMPLEMENTED trong worktree (T122-D3: routes app.py:13693–13825 + admin/bio-review.html)**; chờ Lee test :5000 → done. Task: `tasks/T73-admin-review-bio-vi.md`.'
    if old_line2 in content:
        content = content.replace(old_line2, new_line)
        print("Found and replaced line 443 (with HTML entity)")
    else:
        print("Still not found")

# Update line 490 (T73 PENDING -> DONE)
old_line2 = '**T73 ⏳ PENDING (chờ regress):** Admin review UI cho bio_vi_draft (2,093 rows) — **UI + routes ĐÃ IMPLEMENTED (T122-D3)**, script `t73_copy_approved_bio_vi.py` sẵn sàng; chờ admin test :5000 → done.'
new_line2 = '**T73 ✅ DONE (2026-10-12):** Admin review UI cho bio_vi_draft (2,093 rows) — **API tested 2026-10-12: stats/list/approve/reject/bulk-approve/apply all PASS**; verified approve A001030 + apply → people.bio_vi content match; reject A001302 with note; bulk approve 39 rows. Task: `tasks/T73-admin-review-bio-vi.md`.'

if old_line2 in content:
    content = content.replace(old_line2, new_line2)
    print("Found and replaced line 490")
else:
    print("Line 490 not found")

with open('tasktodo.md', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")