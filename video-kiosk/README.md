# Hikari Video Kiosk

This folder contains a rebuildable copy of the Hikari playback kiosk.

## What it does

- Builds a local playlist from video files on the box
- Launches `mpv` fullscreen on DRM/KMS
- Can index local media with titles, tags, and sidecar metadata
- Can download YouTube videos directly into the library

## Layout

- `scripts/build-playlist.sh` builds `playlist.m3u`
- `scripts/run-kiosk.sh` starts `mpv`
- `scripts/download-youtube-video.sh` downloads media into the library
- `scripts/build-library-index.py` creates `library.sqlite3`, `library.json`, and `library.csv`
- `systemd/hikari-video-kiosk.service` runs the kiosk at boot
- `kiosk.env.example` is the config template

## Suggested install path on the box

```text
/home/admin/hikari-video-kiosk
```

## Media source

The kiosk can use either:

- `/mnt/usb`
- `/home/admin/homeassistant/www/hikari_assets`

You can override this with `MEDIA_SOURCE_DIR` in `kiosk.env`.

## Typical workflow

1. Copy the folder to the box.
2. Copy `kiosk.env.example` to `kiosk.env`.
3. Adjust `MEDIA_SOURCE_DIR`, audio settings, and `DRM_DEVICE` if needed.
4. Install and enable the systemd service.
5. Add videos locally or download them with the helper script.
6. Run the index builder after changing tags or metadata.

