#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/admin/hikari-video-kiosk}"
PLAYLIST_FILE="$APP_DIR/playlist.m3u"
MEDIA_DIR="$APP_DIR/media"

resolve_asset_dir() {
  if [[ -n "${MEDIA_SOURCE_DIR:-}" ]]; then
    echo "$MEDIA_SOURCE_DIR"
    return 0
  fi

  local candidate
  for candidate in /mnt/usb /home/admin/homeassistant/www/hikari_assets; do
    if [[ -d "$candidate" ]]; then
      if [[ "$candidate" == "/mnt/usb" ]]; then
        if mountpoint -q "$candidate"; then
          echo "$candidate"
          return 0
        fi
      else
        echo "$candidate"
        return 0
      fi
    fi
  done

  return 1
}

ASSET_DIR="$(resolve_asset_dir || true)"
if [[ -z "${ASSET_DIR:-}" ]]; then
  echo "No media source found. Set MEDIA_SOURCE_DIR in kiosk.env." >&2
  : > "$PLAYLIST_FILE"
  exit 1
fi

mkdir -p "$APP_DIR" "$MEDIA_DIR"

mapfile -t videos < <(
  find "$ASSET_DIR" -maxdepth 1 -type f \
    \( -iname '*.mkv' -o -iname '*.mp4' -o -iname '*.webm' -o -iname '*.mov' \) \
    ! -iname '.*' \
    ! -iname '*.original.*' \
    | sort
)

if [[ ${#videos[@]} -eq 0 ]]; then
  echo "No video files found in $ASSET_DIR" >&2
  : > "$PLAYLIST_FILE"
  exit 1
fi

{
  echo "#EXTM3U"
  for video in "${videos[@]}"; do
    echo "$video"
  done
} > "$PLAYLIST_FILE"

ln -sfn "${videos[0]}" "$MEDIA_DIR/current"

echo "Wrote $PLAYLIST_FILE with ${#videos[@]} entries"
echo "Primary video: ${videos[0]}"

if [[ -f "$APP_DIR/scripts/build-library-index.py" ]]; then
  python3 "$APP_DIR/scripts/build-library-index.py" || true
fi

