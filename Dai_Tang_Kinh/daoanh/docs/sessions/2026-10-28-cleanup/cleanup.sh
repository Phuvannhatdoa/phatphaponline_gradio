#!/bin/bash
# Dọn rác VPS để lấy lại dung lượng. Mặc định chỉ HIỂN THỊ (dry-run).
# Chạy thật:  bash /root/cleanup.sh --apply
# Không bao giờ đụng vào lineage.db đang dùng (và -wal/-shm của nó).
set -u

APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1
KEEP_BACKUPS=2

A=/opt/phatphaponline_gradio/truyenthua/visjs-app/Dai_Tang_Kinh/daoanh
D=/opt/phatphaponline_gradio
ZENQ_LOG=/root/.pm2/logs/zenq-error.log

say() { echo "$@"; }
rmx() {
    if [ $APPLY -eq 1 ]; then
        rm -rf -- "$@" && say "  xóa: $*"
    else
        say "  [dry] sẽ xóa: $*"
    fi
}

say "== Trước: $(df -h / | tail -1)"
say "Chế độ: $([ $APPLY -eq 1 ] && echo APPLY || echo DRY-RUN)"

say "[1] Backup DB trong daoanh/data/backups (giữ $KEEP_BACKUPS bản mới nhất)"
if [ -d "$A/data/backups" ]; then
    cd "$A/data/backups" || exit 1
    OLD=$(ls -1t *.db 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)))
    for f in $OLD; do
        rmx "$PWD/$f" "$PWD/$f-shm" "$PWD/$f-wal"
    done
fi

say "[2] lineage.db.* cũ trong daoanh/data (giữ lineage.db, -wal, -shm)"
for f in "$A"/data/lineage.db.* "$A"/data/lineage.dbcd; do
    [ -e "$f" ] || continue
    rmx "$f"
done

say "[3] Cache và thư mục rác trong daoanh"
for p in "$A/_archive/2026-10-25-junk-cleanup" "$A/data/t45_cache" "$A/data/snap"; do
    [ -e "$p" ] && rmx "$p"
done

say "[4] Thư mục không thuộc PTDA"
for p in "$D/gui_app" "$D/2000_Files" "$D/Opensearch" "$D/input_docs" \
         "$D/truyenthua/testsuite" "/root/sanghagpt" "/opt/daoanh_legacy_2026-05-14"; do
    [ -e "$p" ] && rmx "$p"
done
for p in "$D"/os.getenv* "$D"/*CHROMA*; do
    [ -e "$p" ] && rmx "$p"
done

say "[5] Hệ thống"
if [ $APPLY -eq 1 ]; then
    journalctl --vacuum-size=100M >/dev/null 2>&1 && say "  journal: đã thu gọn về 100M"
    if [ -f "$ZENQ_LOG" ] && [ "$(stat -c %s "$ZENQ_LOG")" -gt 104857600 ]; then
        truncate -s 0 "$ZENQ_LOG" && say "  đã cắt $ZENQ_LOG"
    fi
    snap list --all 2>/dev/null | awk '/disabled/{print $1, $3}' | while read -r n r; do
        snap remove "$n" --revision="$r" >/dev/null 2>&1 && say "  đã gỡ snap $n rev $r"
    done
else
    say "  [dry] sẽ thu gọn journal về 100M, cắt log ZenQ nếu > 100M, gỡ snap revision đã disabled"
fi

say "== Sau: $(df -h / | tail -1)"
if [ $APPLY -eq 1 ]; then
    say "Kiểm tra dịch vụ: daoanh-api=$(systemctl is-active daoanh-api.service) nginx=$(systemctl is-active nginx)"
else
    say "Đây là dry-run, chưa xóa gì. Chạy thật: bash /root/cleanup.sh --apply"
fi
