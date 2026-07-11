#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/admin/hikari-video-kiosk}"
ENV_FILE="$APP_DIR/kiosk.env"
PLAYLIST_FILE="$APP_DIR/playlist.m3u"
BUILD_SCRIPT="$APP_DIR/scripts/build-playlist.sh"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

DRM_DEVICE="${DRM_DEVICE:-/dev/dri/card0}"
KIOSK_AUDIO="${KIOSK_AUDIO:-no}"
KIOSK_VO="${KIOSK_VO:-drm}"
MPV_BIN="${MPV_BIN:-/usr/bin/mpv}"
KIOSK_VOLUME="${KIOSK_VOLUME:-130}"
KIOSK_AUDIO_DEVICE="${KIOSK_AUDIO_DEVICE:-alsa/default:CARD=P230Q200}"
KIOSK_AO="${KIOSK_AO:-alsa}"

if [[ ! -s "$PLAYLIST_FILE" ]]; then
  "$BUILD_SCRIPT"
fi

if [[ ! -s "$PLAYLIST_FILE" ]]; then
  echo "Playlist is empty: $PLAYLIST_FILE" >&2
  exit 1
fi

audio_args=()
if [[ "$KIOSK_AUDIO" == "no" ]]; then
  audio_args+=(--no-audio)
else
  audio_args+=(--ao="$KIOSK_AO" --audio-device="$KIOSK_AUDIO_DEVICE" --volume="$KIOSK_VOLUME")
fi

chvt 1 >/dev/null 2>&1 || true

mpv_args=(
  --fullscreen
  --no-terminal
  --no-osc
  --no-osd-bar
  --cursor-autohide=no
  --keep-open=yes
  --loop-playlist=inf
  --playlist="$PLAYLIST_FILE"
  --drm-device="$DRM_DEVICE"
  --hwdec=no
  --profile=sw-fast
)

if [[ "$KIOSK_VO" == "drm" ]]; then
  mpv_args+=(--vo=drm)
else
  mpv_args+=(--vo=gpu-next --gpu-context=drm)
fi

exec "$MPV_BIN" "${mpv_args[@]}" "${audio_args[@]}"

