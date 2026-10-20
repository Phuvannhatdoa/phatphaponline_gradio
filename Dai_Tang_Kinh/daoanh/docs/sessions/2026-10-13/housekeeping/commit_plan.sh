#!/usr/bin/env bash
# Housekeeping 2026-10-13 (T374–T378) — commit TỪNG MỤC MỘT, stage theo đường dẫn tường minh.
# Lý do có file này: phiên làm việc không được phép chạy `git add` (chế độ quyền), nên chưa commit.
#
# Chạy từ repo root visjs-app (Git Bash):
#   bash Dai_Tang_Kinh/daoanh/docs/sessions/2026-10-13/housekeeping/commit_plan.sh
# Mỗi commit: kiểm index rỗng trước → add đúng danh sách → so `git diff --cached --name-only` với danh sách
# mong đợi → commit. Lệch là DỪNG (không commit gì thêm). Hoàn tác một mục: git revert --no-edit <sha mục đó>.
# Cuối cùng điền SHA thật vào task file + Handoff (commit "T374-T378: điền SHA").
set -euo pipefail

D=Dai_Tang_Kinh/daoanh
H=$D/docs/sessions/2026-10-13/housekeeping
cd "$(git rev-parse --show-toplevel)"
[ -f "$D/AGENTS.md" ] || { echo "Không ở repo visjs-app"; exit 1; }

die() { echo "DỪNG: $*" >&2; exit 1; }

# commit_item <message> <path>...   (path tương đối repo root; path đã xoá = stage việc xoá)
commit_item() {
  local msg="$1"; shift
  [ -z "$(git diff --cached --name-only)" ] || die "index đang có file staged của người khác — xử lý trước (AGENTS §17)"
  git add -- "$@" || die "git add lỗi — xem AGENTS §14 (index tạm bằng read-tree HEAD)"
  local want got
  want=$(printf '%s\n' "$@" | sort -u)
  got=$(git -c core.quotepath=off diff --cached --no-renames --name-only | sort -u)
  if [ "$want" != "$got" ]; then
    echo "--- mong đợi ---"; echo "$want"; echo "--- đang staged ---"; echo "$got"
    git reset -q -- "$@"
    die "danh sách staged lệch cho: $msg"
  fi
  git commit -q -m "$msg" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
  git show --stat --format='%h %s' HEAD | tail -3
}

# ---- C0: đăng ký task T374–T378 (tasktodo.md ở trạng thái NGAY SAU khi nối 5 dòng, TRƯỚC T376) ----
[ -z "$(git diff --cached --name-only)" ] || die "index không rỗng"
REG_TASKS="$D/tasks/T374-git-health-and-revert-procedure.md $D/tasks/T375-resolve-duplicate-task-ids.md $D/tasks/T376-tasktodo-archive-done.md $D/tasks/T377-root-cleanup-archive.md $D/tasks/T378-app-split-zenlineage-blueprint.md"
git add -- $REG_TASKS
blob=$(git hash-object -w "$H/tasktodo.md.bak-before-T376")
git update-index --cacheinfo "100644,$blob,$D/docs/tasktodo.md"
got=$(git -c core.quotepath=off diff --cached --no-renames --name-only | sort -u)
want=$(printf '%s\n' $REG_TASKS "$D/docs/tasktodo.md" | sort -u)
[ "$want" = "$got" ] || { git reset -q -- $REG_TASKS "$D/docs/tasktodo.md"; die "C0 staged lệch"; }
git commit -q -m "T374-T378: đăng ký 5 task housekeeping + dòng tasktodo" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
SHA_REG=$(git rev-parse --short HEAD); echo "C0 $SHA_REG"

# ---- C1: T374 ----
commit_item "T374: git health 2026-10-13 + quy trình revert one fix (docs/process/REVERT_ONE_FIX.md)" \
  "$D/docs/sessions/2026-10-13/git-health.md" "$D/docs/process/REVERT_ONE_FIX.md" "$D/AGENTS.md" "$D/CLAUDE.md"
SHA_T374=$(git rev-parse --short HEAD)

# ---- C2: T375 ----
T375_OLD="tasks/T158-glossary-resolver-pre-translation-lookup.md tasks/T206-pl-corrupt-canonical-name-vi-fix.md tasks/T215-vnpa-dila-id-recovery.md docs/Mimo-Flash/T215-VNPA-DILA-ID-RECOVERY-01.md docs/Mimo-Flash/T168-rule-resolver-context-compiler-PLAN.md docs/Mimo-Flash/T169-groq-place-verify-pipeline.md docs/Mimo-Flash/T169-groq-place-verify-pipeline-SPEC.md docs/Mimo-Flash/XX-T170-dila-place-person-v41-verify.md docs/Mimo-Flash/XX-T170-dila-place-person-v41-verify-SPEC.md docs/Mimo-Flash/T171-person-name-standard.md docs/Mimo-Flash/T171-person-name-standard-SPEC.md docs/Mimo-Flash/T177-directive-v2-trie-xml-dualhash-REVIEW.md docs/Mimo-Flash/T177-dynamic-filter-absorb-directive-v2.md"
P=()
for f in $T375_OLD; do P+=("$D/$f" "$D/_archive/2026-10-13-dup-ids/$f"); done
P+=("$D/_archive/2026-10-13-dup-ids/MANIFEST.md" "$H/t375_archive_dup_ids.py" "$H/dup-ids-before.log" "$H/dup-ids-after-T375.log")
commit_item "T375: gỡ 8/9 task ID trùng — chuyển 13 bản cũ bị hồi sinh (sau T222) vào _archive/2026-10-13-dup-ids/" "${P[@]}"
SHA_T375=$(git rev-parse --short HEAD)

# ---- C3: T376 ----
commit_item "T376: thu gọn tasktodo.md — 74 mục DONE sang docs/archive/tasktodo-done-2026.md" \
  "$D/scripts/t376_archive_tasktodo_done.py" "$D/docs/tasktodo.md" "$D/docs/archive/tasktodo-done-2026.md" \
  "$H/t376-dry-run.log" "$H/t376-apply.log" "$H/build_progress_before-T376.log" "$H/build_progress_after-T376.log" \
  "$H/progress_counts_before-T376.txt" "$H/progress_counts_after-T376.txt"
SHA_T376=$(git rev-parse --short HEAD)

# ---- C4: T377 (chỉ 38 file được git theo dõi; 22 file bị .gitignore chỉ có trong MANIFEST) ----
T377_TRACKED="scratchpad_out.txt scratchpad_out2.txt scratchpad_out3.txt scratchpad_out4.txt scratchpad_out5.txt scratchpad_out6.txt scratchpad_out7.txt scratchpad_out8.txt fix_css.py fix_arrays.py fix_original_css.py original_style_block.txt dark_theme_css.txt insert_css.py fix_home_search.py fix_home.py add_home_search.py find_search.py read_search.py search_lines.py find_fetches.py find_entity.py entity_search_result.txt home_dump.txt phase_b_20.txt phase_b_100.txt deploy_test.txt GET places.html.backup_t130_s2 index.bak-20260830.html gateway_local.err gateway_backend.err gateway_backend.out app_5002.log.err app_local2.err app_local.log.err gateway_local.log.err server_local.err"
P=()
for f in $T377_TRACKED; do P+=("$D/$f" "$D/_archive/2026-10-13-root-cleanup/$f"); done
P+=("$D/_archive/2026-10-13-root-cleanup/MANIFEST.md" "$H/t377_root_cleanup.py" "$H/t377-apply.log")
commit_item "T377: dọn gốc daoanh — 60 file nháp/log/backup sang _archive/2026-10-13-root-cleanup/ (38 file git theo dõi)" "${P[@]}"
SHA_T377=$(git rev-parse --short HEAD)

# ---- C5: T378 ----
commit_item "T378: tách app.py bước 1 — 5 route zenlineage sang blueprint api_zenlineage.py (route map 363 = 363)" \
  "$D/app.py" "$D/api_zenlineage.py" "$H/t378_extract_zenlineage.py" \
  "$H/t378-probe-before.json.txt" "$H/t378-probe-after.json.txt" "$H/t378-routes-before.txt" "$H/t378-routes-after.txt" \
  "$H/build_progress_after-T378-noscanfix.log"
SHA_T378=$(git rev-parse --short HEAD)

# ---- C6: điền SHA vào task file + Handoff, kèm log/backup/README của phiên ----
for t in T374 T375 T376 T377 T378; do
  v="SHA_$t"; s="${!v}"
  sed -i "s/<sha_$t>/$s/g" $D/tasks/$t-*.md "$D/docs/Handoff-2026-10-13-housekeeping.md" "$D/docs/ROLLBACK.md" "$H/README.md"
done
sed -i "s/<sha_REG>/$SHA_REG/g" "$D/docs/Handoff-2026-10-13-housekeeping.md" "$H/README.md"
commit_item "T374-T378: điền SHA + Handoff/ROLLBACK/log phiên housekeeping" \
  $REG_TASKS "$D/docs/Handoff-2026-10-13-housekeeping.md" "$D/docs/ROLLBACK.md" "$H/README.md" "$H/commit_plan.sh" \
  "$H/final-guard.log" "$H/final-dup-ids.log" "$H/final-build_progress_data.log" "$H/final-npm-test.log" \
  "$H/tasktodo.md.bak-before-T374-T378-register" "$H/tasktodo.md.bak-before-T376" \
  "$H/AGENTS.md.bak-before-T374" "$H/CLAUDE.md.bak-before-T374" "$H/app.py.bak-before-T378" \
  "$H/reapply_after_restore.py" "$H/ROLLBACK.md.bak-before-T374-T378"

echo
echo "XONG. SHA: đăng ký=$SHA_REG T374=$SHA_T374 T375=$SHA_T375 T376=$SHA_T376 T377=$SHA_T377 T378=$SHA_T378"
echo "Hoàn tác một mục: git revert --no-edit <sha>   (xem docs/Handoff-2026-10-13-housekeeping.md mục 5)"
