with open('docs/tasktodo.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line with T27 Source Neutral Entity ID
target_line = None
for i in range(len(lines)):
    line = lines[i]
    if 'T27' in line and 'Source Neutral' in line and 'entity_id' in line:
        target_line = i
        break

if target_line is None:
    print("Could not find T27 line")
else:
    # Show context
    print(f"Found T27 at line {target_line + 1}")
    # Find the --- separator after T27
    insert_idx = None
    for i in range(target_line + 1, len(lines)):
        if lines[i].strip() == '---':
            insert_idx = i
            break
    
    if insert_idx is None:
        print("Could not find --- separator after T27")
    else:
        # Insert new tasks before the --- separator
        new_tasks = '''

## T30: HOME Identity Hub

- **Mục tiêu**: Xây dựngหน้า HOME làm Identity Hub với 3 cụm menu và 15 TAB
- **Phụ trách**: Lead AI Engineer
- **Dependent on**: [T23]
- **Created**: 2026-08-21
- **Updated**: 2026-08-21
- **Done when**: 
  - Trang HOME Flask-route `/daoanh/home` hoạt động
  - 15 TABs hiển thị đúng 3 cụm (Kinh văn & Giáo lý | Thực thể & Niên đại | Con người & Không gian)
  - Mỗi TAB call API đúng source (xem `docs/HOME-identity-hub-spec.md`)
  - Bug fixes trong places.html (baseUrl, CSS braces, reset arrays) đã fix
- **Acceptance criteria**:
  - [x] `home.html` created với 3-cluster accordion menu
  - [x] Flask route `@app.route('/daoanh/home')` hoạt động
  - [x] 15 TABs: Đại Tạng, Giáo Lý, Thư Viện, Nghi Lễ, Giáo Dục | Thực Thể, Niên Đại, Sự Kiện, Bản Đồ, Dữ liệu | Nhân Vật, Truyền Thừa, Đồ Thị, Hình Ảnh, Nghệ Thuật
  - [x] 3 cụm menu hoạt động đúng
  - [x] Tester agent 4/4 pass sau khi fix bugs
  - [x] Git commit logs saved, rollback khả thi

## T31: Coverage Matrix - Data Source × TAB Mapping

- **Mục tiêu**: Xây dựng matrix对应 nguồn dữ liệu × TAB cho Identity Hub
- **Phụ trách**: Lead AI Engineer
- **Dependent on**: [T30]
- **Created**: 2026-08-21
- **Updated**: 2026-08-21
- **Done when**:
  - `docs/HOME-identity-hub-spec.md` có table source × TAB mapping
  - Mỗi TAB có endpoint rõ ràng, coverage% đánh giá
  - Gap analysis hoàn thành (missing sources đánh dấu ⚪)
- **Acceptance criteria**:
  - [x] Table 15 sources × 15 TABs trong spec doc
  - [x] Status: available/partial/missing cho mỗi cell
  - [x] Gap analysis xuất file CSV/report
  - [x] Tester agent 4/4 pass

## T32: places.html Tab Expansion (6 → 15)

- **Mục tiêu**: Mở rộng places.html từ 6 TABs lên 15 TABs, fix bugs, redesign UI
- **Phụ trách**: Lead AI Engineer
- **Dependent on**: [T30, T31]
- **Created**: 2026-08-21
- **Updated**: 2026-08-21
- **Done when**:
  - places.html có 15 TABs hoạt động (thay vì 6)
  - Bug fixes: baseUrl ReferenceError, CSS braces, _tabLoaded, reset arrays đã fix
  - CSS `.da-stabs` redesign: scrollable strip hoặc 2 hàng
  - 9 TAB panel mới đã thêm (Giáo Lý, Thư Viện, Nghi Lễ, Giáo Dục, Hình Ảnh, Nghệ Thuật, Dữ liệu)
  - `loadTabData` sử dụng lookup table thay vì if-chain
  - Entity-mode gating hoạt động cho tất cả TAB
- **Acceptance criteria**:
  - [x] 15 TABs hiển thị đúng 3 cụm
  - [x] Tester agent 4/4 pass
  - [x] Git commit có thể rollback về version trước
  - [x] Bug fix logs trong session.md

'''
        # Insert before the --- separator
        new_content = ''.join(lines[:insert_idx]) + new_tasks + ''.join(lines[insert_idx:])
        with open('docs/tasktodo.md', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: Added T30/T31/T32 tasks")