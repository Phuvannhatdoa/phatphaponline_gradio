with open('tasktodo.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Update line 443 (index 442)
old_line = lines[442]
print("Old line 443:", old_line.encode('ascii', 'replace').decode())

new_line = '**T73 ✅ DONE (2026-10-12) - Admin Review Bio VI (person_bio_vi_draft 2,093 → people.bio_vi):** tab Bio Review + `/api/admin/bio-review/pending|/<pid>|/apply` + en_audit_log — **IMPLEMENTED trong worktree (T122-D3: routes app.py:13693–13825 + admin/bio-review.html)**; **API tested 2026-10-12: stats/list/approve/reject/bulk-approve/apply all PASS**; verified approve A001030 + apply → people.bio_vi content match; reject A001302 with note; bulk approve 39 rows. Task: `tasks/T73-admin-review-bio-vi.md`.\n'

lines[442] = new_line
print("New line 443:", new_line.encode('ascii', 'replace').decode())

with open('tasktodo.md', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Done")