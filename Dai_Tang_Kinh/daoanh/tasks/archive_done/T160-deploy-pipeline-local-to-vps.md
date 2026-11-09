---
id: T160
title: "Thiết lập deploy pipeline một chiều local → VPS (git push production master:main)"
module: devops
priority: high
status: done
depends_on: []
created: 2026-09-21
updated: 2026-09-21
done_when:
  - "[x] Bare repo /opt/git/daoanh.git tạo xong trên VPS và seed từ VPS working tree"
  - "[x] Hook /opt/git/daoanh.git/hooks/post-receive hoạt động: chỉ deploy refs/heads/main, log tại /var/log/daoanh-deploy.log"
  - "[x] Hook bảo vệ *.db, *.sqlite, .env khỏi bị overwrite"
  - "[x] Hook backup app.py trước mỗi deploy (app.py.bak.TIMESTAMP)"
  - "[x] Hook restart daoanh-api.service sau checkout thành công"
  - "[x] Local: git remote 'production' trỏ đến ssh://vps-daoanh/opt/git/daoanh.git"
  - "[x] Test: push test file → xuất hiện trên VPS, DB còn nguyên (1.4GB), service active"
  - "[x] Rollback: cp app.py.bak.TIMESTAMP app.py + systemctl restart daoanh-api.service"
---

# T160 — Deploy Pipeline Local → VPS

> **Module:** `devops` · **Priority:** high · **Status:** in_progress
> **Created:** 2026-09-21

---

## Kiến trúc

```
[Local master] → git push production master:main
      ↓ SSH (key: ~/.ssh/vps_phatphap)
[VPS /opt/git/daoanh.git] (bare repo)
      ↓ post-receive hook (chỉ khi refs/heads/main)
[VPS /opt/phatphaponline_gradio/truyenthua/visjs-app]
      git archive | tar (exclude *.db, *.sqlite, .env)
      ↓
systemctl restart daoanh-api.service
      ↓
log → /var/log/daoanh-deploy.log
```

## Paths quan trọng

| Thứ | Path |
|---|---|
| Bare repo VPS | `/opt/git/daoanh.git` |
| Hook VPS | `/opt/git/daoanh.git/hooks/post-receive` |
| Worktree VPS | `/opt/phatphaponline_gradio/truyenthua/visjs-app` |
| App dir VPS | `.../visjs-app/Dai_Tang_Kinh/daoanh` |
| Deploy log VPS | `/var/log/daoanh-deploy.log` |
| Service | `daoanh-api.service` |
| SSH key | `~/.ssh/vps_phatphap` (alias: `vps-daoanh`) |

## Daily deploy commands

```bash
git status
git add -A
git commit -m "feat: mô tả thay đổi"
git push production master:main
```

## Rollback commands

```bash
# Trên local: revert 1 commit
git revert HEAD --no-edit
git push production master:main

# Hoặc trên VPS: restore backup
DAOANH=/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
ls $DAOANH/app.py.bak.*       # tìm bản backup gần nhất
cp $DAOANH/app.py.bak.YYYYMMDD_HHMMSS $DAOANH/app.py
systemctl restart daoanh-api.service
```

## Bảo vệ data

- `*.db`, `*.sqlite` bị exclude khỏi tar — không bao giờ bị ghi đè
- `data/` dir được giữ nguyên (chỉ non-DB files được extract)
- Service log tại `/tmp/daoanh-api.log` không bị ảnh hưởng

## Ghi chú kỹ thuật

- Lý do seed từ VPS trước: VPS và local diverge 386/501 commits do sửa trực tiếp VPS. Seed giảm lượng data push lần đầu.
- `git archive | tar` an toàn hơn `git checkout -f` vì không có khái niệm "remove file" — chỉ extract file vào worktree.
- DB files trong HEAD commit đều là 0 bytes (placeholder) hoặc nhỏ (<75MB), không phải lineage.db 664MB.
