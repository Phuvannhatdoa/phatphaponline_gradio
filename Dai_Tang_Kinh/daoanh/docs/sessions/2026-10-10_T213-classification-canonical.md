# Session 2026-10-10 — T213 classification + canonical_decision A003636 + shared index stale

> Task: `tasks/T213-vnpa-orphan-211-classification.md` (READ-ONLY, status→done) + pack §7 item 1 (canonical_decision A003636).
> Môi trường: Windows box (`cwd=daoanh`), git **shared index stale** (mtime 2026-10-06, 90 `D` + 30 `M` + 1 `A` giả) → **commit qua temp-index** (AGENTS §14/§17).

## 1. Mục tiêu

Admin đồng ý xử lý 2 việc đang hoãn:
1. **canonical_decision A003636** — ghi tường minh `phuoc_chau_dai_an` (Phước Châu Đại An) là canonical, `phuc_chau_dai_an` (Phúc Châu Đại An) là biến thể.
2. **T213** — READ-ONLY classification 211 orphan (`dila_id=''` 210 + `NULL` 1) vào buckets A/B/C/D.

## 2. Đã làm

### 2.1 canonical_decision A003636 (DB, additive)
INSERT 1 row vào `canonical_decision`:
- `entity_ref='A003636'` (DILA ID)
- `canonical_name_vi='Phước Châu Đại An'`
- `source_id='phuoc_chau_dai_an'` (vn_person_authority.id, status=verified, TTL TS-Phuoc-Chau-Dai-An, name_zh=福州大安)
- `authority_rank='admin_approved'`, `confidence=1.0`, `verification_status='verified'`
- `decision_note`: Phước Châu Đại An (verified, có TTL, name_zh 福州大安) là canonical; Phúc Châu Đại An (auto_ttl, không TTL, name_zh rỗng) là biến thể ghi âm (Phúc/Phước).
- `editor='admin'`, timestamps NOW.
- **Verify:** `canonical_decision` nay 4 rows (PL000000000314, PL000000000001, A001984, A003636).
- **Revert:** `DELETE FROM canonical_decision WHERE entity_ref='A003636'` (additive, 0 mất dữ liệu).

### 2.2 T213 Classification (READ-ONLY, 0 DB mutation)
211 rows (`dila_id=''` 210 + `NULL` 1 `tang_chu_pho_dung`) → 4 buckets:

| Bucket | Count | Criteria | Samples |
|---|---|---|---|
| **A** | 186 | TS- prefix, Vietnamese monastic names, pending | `am_chu_ho_khe`, `vo_ngon_thong`, `minh_hai_phap_bao`, `tang_chu_pho_dung` |
| **B** | 6 | Ton-Gia prefix (Sanskrit transcriptions) + Ngũ Phong Thường Quán | `da_da_xa_da` (迦耶舍多), `su_tu_ty_kheo` (師子菩薩), `uu_ba_cuc_da` (優婆毱多) |
| **C** | 11 | Cs- prefix / "Cư Sĩ" / lay titles | `banh_nhu_lam`, `cs_huong`, `do_huong_trinh`, `thu_ky_nam` |
| **D** | 8 | Buddhas/Bodhisattvas/Arhats (non-Indian) | `thich_ca_mau_ni_phat`, `phat_bao_phap_hoa`, `phat_y_linh_nhac`, `thanh_vien_phat_nhan` |

**Evidence:** `%TEMP%\opencode\t213_classification_20261010.json` (full 211 rows) + `docs/reports/T213-classification-report-20261010.md`.

**Task T213 updated:** status=done, appended actual counts + bucket details.

### 2.3 Shared index stale (không sửa)
`.git/index` mtime 2026-10-06 (4 ngày trước), 90 `D` + 30 `M` + 1 `A` giả so với HEAD. ACL `Users` thiếu DELETE trên `.git/` → `git read-tree` fail. **Quyết định:** chấp nhận stale, commit mọi thứ qua temp-index (GIT_INDEX_FILE ở %TEMP%). Ghi rõ warning trong Handoff.

## 3. Kiểm chứng

```bash
# canonical_decision
sqlite3 data/lineage.db "SELECT entity_ref,canonical_name_vi,verification_status FROM canonical_decision WHERE entity_ref='A003636';"
# → A003636|Phước Châu Đại An|verified

# T213 counts
python -X utf8 -c "
import sqlite3
c = sqlite3.connect('file:data/lineage.db?mode=ro', uri=True)
print('dila_id=\"\":', c.execute(\"SELECT COUNT(*) FROM vn_person_authority WHERE dila_id=''\").fetchone()[0])
print('dila_id IS NULL:', c.execute('SELECT COUNT(*) FROM vn_person_authority WHERE dila_id IS NULL').fetchone()[0])
"
# → 210 + 1 = 211
```

## 4. Files tạo/sửa

| File | Loại |
|---|---|
| `docs/reports/T213-classification-report-20261010.md` | report (mới) |
| `tasks/T213-vnpa-orphan-211-classification.md` | task (status=done, appended kết quả) |
| `docs/tasktodo.md` | block T213 (mới) |
| `docs/ROLLBACK.md` | row T213 (mới) |
| `docs/sessions/2026-10-10_T213-classification-canonical.md` | session (này) |
| `docs/Handoff-2026-10-10-T213-canonical.md` | Handoff (mới) |
| `data/progress_data.json` | regen dashboard |
| `%TEMP%\opencode\t213_classification_20261010.json` | evidence (ngoài repo) |

## 5. Revert

| Phần | Lệnh | Mất dữ liệu? |
|---|---|---|
| Docs + code | `git revert --no-edit <sha1> <sha2>` | **0** |
| DB canonical_decision | `DELETE FROM canonical_decision WHERE entity_ref='A003636'` | **0** (additive) |
| DB T213 | (READ-ONLY, 0 mutation) | **0** |

## 6. Cảnh báo cho session sau

- **Shared `.git/index` stale** — KHÔNG dùng `git add`/`git status`/`git diff` không pathspec. Commit **BẮT BUỘC** qua temp-index (`read-tree HEAD` + plumbing + CAS).
- `npm`/`node`/`rg` có thể là shim 0-byte → wrap `cmd /c "..."`.
- `data/*.json` bị `.gitignore` → `git add -f` khi regen dashboard.
- Session song song (T273/T274/T275) — luôn dựng file từ HEAD.

## 7. Pipip

Done.