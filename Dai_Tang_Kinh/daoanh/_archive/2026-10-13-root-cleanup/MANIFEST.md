# MANIFEST — T377 dọn thư mục gốc daoanh (2026-10-13)

Chỉ chuyển, không xoá. Đường dẫn gốc là tương đối với `Dai_Tang_Kinh/daoanh/`.

Khôi phục tất cả: `python -X utf8 docs/sessions/2026-10-13/housekeeping/t377_root_cleanup.py --restore`.
Khôi phục một file: chuyển ngược `_archive/2026-10-13-root-cleanup/<file>` → `<file>`.
File cột "git" = được git theo dõi: sau khi commit T377 thì `git revert <sha_T377>` cũng khôi phục.
File "không" = bị .gitignore → chỉ khôi phục được bằng cách chuyển ngược (git không giữ).

| Đường dẫn gốc | Đường dẫn mới | Lý do | Byte | Git theo dõi | sha256[:16] |
|---|---|---|---:|---|---|
| `scratchpad_out.txt` | `_archive/2026-10-13-root-cleanup/scratchpad_out.txt` | output nháp một lần (scratchpad), không code nào đọc | 189 | git | `5928abe406ec4444` |
| `scratchpad_out2.txt` | `_archive/2026-10-13-root-cleanup/scratchpad_out2.txt` | output nháp một lần (scratchpad), không code nào đọc | 9 | git | `78d6a51c1b9b3892` |
| `scratchpad_out3.txt` | `_archive/2026-10-13-root-cleanup/scratchpad_out3.txt` | output nháp một lần (scratchpad), không code nào đọc | 444 | git | `36c7814671c222e0` |
| `scratchpad_out4.txt` | `_archive/2026-10-13-root-cleanup/scratchpad_out4.txt` | output nháp một lần (scratchpad), không code nào đọc | 86 | git | `eb0c3b1bbd023378` |
| `scratchpad_out5.txt` | `_archive/2026-10-13-root-cleanup/scratchpad_out5.txt` | output nháp một lần (scratchpad), không code nào đọc | 6 | git | `1b65b6b25638d331` |
| `scratchpad_out6.txt` | `_archive/2026-10-13-root-cleanup/scratchpad_out6.txt` | output nháp một lần (scratchpad), không code nào đọc | 78 | git | `8789868558ef1566` |
| `scratchpad_out7.txt` | `_archive/2026-10-13-root-cleanup/scratchpad_out7.txt` | output nháp một lần (scratchpad), không code nào đọc | 84 | git | `fa9ea166c097955d` |
| `scratchpad_out8.txt` | `_archive/2026-10-13-root-cleanup/scratchpad_out8.txt` | output nháp một lần (scratchpad), không code nào đọc | 289 | git | `c1b9f0d811a1f1ab` |
| `fix_css.py` | `_archive/2026-10-13-root-cleanup/fix_css.py` | script sửa CSS chạy một lần (08-22), không code nào gọi | 879 | git | `df36e091494b600e` |
| `fix_arrays.py` | `_archive/2026-10-13-root-cleanup/fix_arrays.py` | script sửa một lần (08-22), không code nào gọi | 1252 | git | `4e2659b15994aec7` |
| `fix_original_css.py` | `_archive/2026-10-13-root-cleanup/fix_original_css.py` | script sửa CSS chạy một lần (08-22); đọc original_style_block.txt (chuyển cùng) | 5951 | git | `e464c17765139c14` |
| `original_style_block.txt` | `_archive/2026-10-13-root-cleanup/original_style_block.txt` | dữ liệu nháp chỉ fix_original_css.py đọc (chuyển cùng) | 3693 | git | `9c96f26048b47f3a` |
| `dark_theme_css.txt` | `_archive/2026-10-13-root-cleanup/dark_theme_css.txt` | đoạn CSS nháp (08-22), không code nào đọc | 3657 | git | `e495e1d3201a5c45` |
| `insert_css.py` | `_archive/2026-10-13-root-cleanup/insert_css.py` | script chèn CSS chạy một lần (08-22), không code nào gọi | 5439 | git | `3a0ee10d28de029b` |
| `fix_home_search.py` | `_archive/2026-10-13-root-cleanup/fix_home_search.py` | script sửa một lần (08-22), không code nào gọi | 1510 | git | `a9d9f62a4f66fad0` |
| `fix_home.py` | `_archive/2026-10-13-root-cleanup/fix_home.py` | script sửa một lần (08-22), không code nào gọi | 2826 | git | `901934bf0e169292` |
| `add_home_search.py` | `_archive/2026-10-13-root-cleanup/add_home_search.py` | script chèn một lần (08-22), không code nào gọi | 1399 | git | `ecdb3ce2c804b349` |
| `find_search.py` | `_archive/2026-10-13-root-cleanup/find_search.py` | script dò nháp (08-22), không code nào gọi | 275 | git | `04421f07ce1db3eb` |
| `read_search.py` | `_archive/2026-10-13-root-cleanup/read_search.py` | script dò nháp (08-22), không code nào gọi | 297 | git | `1166f47e25a65617` |
| `search_lines.py` | `_archive/2026-10-13-root-cleanup/search_lines.py` | script dò nháp (08-22), không code nào gọi | 342 | git | `cbc53eed8f1da21e` |
| `find_fetches.py` | `_archive/2026-10-13-root-cleanup/find_fetches.py` | script dò nháp (08-22), không code nào gọi | 361 | git | `664d00f5de84c60c` |
| `find_entity.py` | `_archive/2026-10-13-root-cleanup/find_entity.py` | script dò nháp (08-17); ghi entity_search_result.txt (chuyển cùng) | 1957 | git | `cea08239bf6b75b4` |
| `entity_search_result.txt` | `_archive/2026-10-13-root-cleanup/entity_search_result.txt` | output của find_entity.py (chuyển cùng) | 288 | git | `e05e3bd586611f64` |
| `home_dump.txt` | `_archive/2026-10-13-root-cleanup/home_dump.txt` | output nháp (08-22) | 530 | git | `d321e3d7ef312851` |
| `phase_b_20.txt` | `_archive/2026-10-13-root-cleanup/phase_b_20.txt` | output nháp (08-21) | 94 | git | `5a9a1e4a3f7f9dca` |
| `phase_b_100.txt` | `_archive/2026-10-13-root-cleanup/phase_b_100.txt` | output nháp (08-21) | 94 | git | `5a9a1e4a3f7f9dca` |
| `deploy_test.txt` | `_archive/2026-10-13-root-cleanup/deploy_test.txt` | file thử deploy (09-21, 34 byte) | 34 | git | `1fb9423333f38fae` |
| `GET` | `_archive/2026-10-13-root-cleanup/GET` | file rỗng 0 byte tạo nhầm (05-14) | 0 | git | `e3b0c44298fc1c14` |
| `app.py.backup_t130_s1` | `_archive/2026-10-13-root-cleanup/app.py.backup_t130_s1` | bản sao lưu app.py trước T130 S1 (09-23); git đã giữ lịch sử | 954834 | không (ignored/untracked) | `cd55a75bbb680753` |
| `places.html.backup_t130_s2` | `_archive/2026-10-13-root-cleanup/places.html.backup_t130_s2` | bản sao lưu places.html trước T130 S2 (09-23); git đã giữ lịch sử | 670344 | git | `a172f2041fb521af` |
| `index.bak-20260830.html` | `_archive/2026-10-13-root-cleanup/index.bak-20260830.html` | bản sao lưu index.html (08-30) | 24500 | git | `b649fdfd1f531094` |
| `gateway_local.err` | `_archive/2026-10-13-root-cleanup/gateway_local.err` | log cũ (09-13) | 90663 | git | `cdf45ed2ec91b766` |
| `gateway_backend.err` | `_archive/2026-10-13-root-cleanup/gateway_backend.err` | log cũ (09-13) | 34030 | git | `8b417d17f7f6d4c5` |
| `gateway_backend.out` | `_archive/2026-10-13-root-cleanup/gateway_backend.out` | log cũ (09-13) | 813 | git | `ba513748ca4937e7` |
| `app_5002.log.err` | `_archive/2026-10-13-root-cleanup/app_5002.log.err` | log cũ (10-01) | 18660 | git | `a951d357c0f8eabe` |
| `app_local2.err` | `_archive/2026-10-13-root-cleanup/app_local2.err` | log rỗng 0 byte (08-20) | 0 | git | `e3b0c44298fc1c14` |
| `app_local.log.err` | `_archive/2026-10-13-root-cleanup/app_local.log.err` | log cũ (10-07) | 92 | git | `a185f2b7e5de5d51` |
| `gateway_local.log.err` | `_archive/2026-10-13-root-cleanup/gateway_local.log.err` | log cũ (10-07) | 6461 | git | `ba192b550e985b94` |
| `server_local.err` | `_archive/2026-10-13-root-cleanup/server_local.err` | log cũ (10-07) | 264 | git | `75ce730b18371ce5` |
| `app_err.log` | `_archive/2026-10-13-root-cleanup/app_err.log` | log cũ (10-04) | 179 | không (ignored/untracked) | `d7dc67f4d78346e4` |
| `app_local_err.log` | `_archive/2026-10-13-root-cleanup/app_local_err.log` | log cũ (10-07) | 10578 | không (ignored/untracked) | `fddcc22134dce50e` |
| `app_test.log` | `_archive/2026-10-13-root-cleanup/app_test.log` | log cũ (10-08) | 1203 | không (ignored/untracked) | `00459c7c57226438` |
| `app_restart.log` | `_archive/2026-10-13-root-cleanup/app_restart.log` | log cũ (10-11) | 967 | không (ignored/untracked) | `36529face89b911b` |
| `app_restart_err.log` | `_archive/2026-10-13-root-cleanup/app_restart_err.log` | log cũ (10-11) | 124918 | không (ignored/untracked) | `74f65c900eb6a3e0` |
| `_test_output.log` | `_archive/2026-10-13-root-cleanup/_test_output.log` | log cũ (10-09) | 5564 | không (ignored/untracked) | `d7ef8e8741151410` |
| `A001984_calc.json` | `_archive/2026-10-13-root-cleanup/A001984_calc.json` | output tính số đời nháp (10-11) | 545739 | không (ignored/untracked) | `85035bb5580fbb6f` |
| `A001984_calc.json.summary.json` | `_archive/2026-10-13-root-cleanup/A001984_calc.json.summary.json` | tóm tắt output nháp (10-11) | 1952 | không (ignored/untracked) | `374085e7780ae9a2` |
| `A027028_calc.json` | `_archive/2026-10-13-root-cleanup/A027028_calc.json` | output tính số đời nháp (10-11) | 659056 | không (ignored/untracked) | `0eda8a2b295e3b12` |
| `A027028_calc.json.summary.json` | `_archive/2026-10-13-root-cleanup/A027028_calc.json.summary.json` | tóm tắt output nháp (10-11) | 1944 | không (ignored/untracked) | `a91b6d11127600b9` |
| `A027242_calc.json` | `_archive/2026-10-13-root-cleanup/A027242_calc.json` | output tính số đời nháp (10-11) | 292874 | không (ignored/untracked) | `2ca0e1bbcbfa0bf7` |
| `A027242_calc.json.summary.json` | `_archive/2026-10-13-root-cleanup/A027242_calc.json.summary.json` | tóm tắt output nháp (10-11) | 1945 | không (ignored/untracked) | `06019d7ae49e9898` |
| `chan_ca_diep_1_A027028_issues.json` | `_archive/2026-10-13-root-cleanup/chan_ca_diep_1_A027028_issues.json` | output khảo sát nháp (10-11) | 9876 | không (ignored/untracked) | `73494a812a51ffa3` |
| `guiyang_A027028_issues.json` | `_archive/2026-10-13-root-cleanup/guiyang_A027028_issues.json` | output khảo sát nháp (10-11) | 10172 | không (ignored/untracked) | `09f5c0e510b168cf` |
| `edges_A027028.json` | `_archive/2026-10-13-root-cleanup/edges_A027028.json` | output khảo sát nháp (10-11) | 1387 | không (ignored/untracked) | `89a004cbe0689770` |
| `edges_A027242.json` | `_archive/2026-10-13-root-cleanup/edges_A027242.json` | output khảo sát nháp (10-11) | 2232 | không (ignored/untracked) | `a23918fd9682e849` |
| `marcus_search1.json` | `_archive/2026-10-13-root-cleanup/marcus_search1.json` | output tra Marcus nháp (10-11) | 1264 | không (ignored/untracked) | `12ff555c20dd8d0e` |
| `marcus_search2.json` | `_archive/2026-10-13-root-cleanup/marcus_search2.json` | output tra Marcus nháp (10-11) | 23701 | không (ignored/untracked) | `8caa3784aa0ab6c1` |
| `marcus_search3.json` | `_archive/2026-10-13-root-cleanup/marcus_search3.json` | output tra Marcus nháp (10-11) | 44209 | không (ignored/untracked) | `427da46abda2ac05` |
| `marcus_search4.json` | `_archive/2026-10-13-root-cleanup/marcus_search4.json` | output tra Marcus nháp (10-11) | 651 | không (ignored/untracked) | `6170fe8ad6bafd4e` |
| `marcus_out_scratch.json` | `_archive/2026-10-13-root-cleanup/marcus_out_scratch.json` | output tra Marcus nháp (10-11) | 1040 | không (ignored/untracked) | `effb26de8ec6cdee` |

## Cố ý để lại (được tham chiếu hoặc chưa chắc)

- `fix_all.py` — được scripts/build_progress_data.py nêu tên (SKIP_FILES)
- `fix_tabs.js` — được scripts/build_tab_readiness.py tham chiếu
- `sync_to_vps.log` — do sync_to_vps.ps1 ghi
- `app_local.log, app_local.err, gateway_local.log, server_local.log` — server local đang chạy ghi (sửa đổi 2026-10-13)
- `app_local_t360.log, app_local_t360.err` — được docs/T360_VIETNAMESE_SOURCE_BADGES_REPORT.md dẫn làm bằng chứng
- `compute_hash.py, create_waiver.py` — vừa sửa 2026-10-13 (phiên khác) — không đụng
- `add_tasks.py, add_route.py, list_tables.py, qa_report.json, schema_places.txt, places_PL000000023255.json, monk_names_vn.json` — chưa chắc là nháp — để Admin quyết
- `.env, config/, *.db, các file .md tài liệu gốc` — cấu hình / dữ liệu / tài liệu
