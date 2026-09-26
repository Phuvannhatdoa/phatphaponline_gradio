#!/usr/bin/env bash
set -euo pipefail

URL="https://phatphaponline.org/daoanh/data/lineage.db"
DEST="/home/user/phatphaponline_gradio/Dai_Tang_Kinh/daoanh/data/lineage.db"

mkdir -p "$(dirname "$DEST")"
curl -fSL --progress-bar -o "$DEST" "$URL"

echo "Downloaded to: $DEST"
ls -lh "$DEST"
