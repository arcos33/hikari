#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <youtube-url>" >&2
  exit 1
fi

APP_DIR="${APP_DIR:-/home/admin/hikari-video-kiosk}"
ASSET_DIR="${MEDIA_SOURCE_DIR:-/mnt/usb}"
YTDLP_BIN="${YTDLP_BIN:-$HOME/.local/bin/yt-dlp}"

mkdir -p "$APP_DIR" "$ASSET_DIR"

if [[ ! -x "$YTDLP_BIN" ]]; then
  YTDLP_BIN="$(command -v yt-dlp)"
fi

"$YTDLP_BIN" \
  --extractor-args "youtube:player_client=android,web" \
  -S "res:720,vcodec:h264,acodec:m4a" \
  -f "bv*+ba/b" \
  --merge-output-format mp4 \
  --write-info-json \
  --restrict-filenames \
  -o "$ASSET_DIR/%(title).120B_[%(id)s].%(ext)s" \
  "$1"

"$APP_DIR/scripts/build-playlist.sh"
python3 "$APP_DIR/scripts/build-library-index.py"

