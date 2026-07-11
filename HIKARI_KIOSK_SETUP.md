# Hikari Kiosk Setup Notes

## Box Identity

- Purpose: Hikari Home Assistant box that also plays local videos for automations
- Hostname: `homeassistant`
- SSH: `admin@192.168.0.212`
- Tailscale IP seen earlier: `100.75.145.90`
- OS: `Armbian_community 26.2.0-trunk.639 trixie`
- Kernel: `6.18.20-current-meson64`
- Architecture: `aarch64`

## Important Paths

- Active assets folder: `/home/admin/homeassistant/www/hikari_assets`
- Test samples folder: `/home/admin/homeassistant/www/hikari_assets/test_samples`
- Special-occasion videos: `/home/admin/homeassistant/www/hikari_special_occasions`
- Kiosk app dir: `/home/admin/hikari-video-kiosk`
- Kiosk env: `/home/admin/hikari-video-kiosk/kiosk.env`
- Kiosk runner: `/home/admin/hikari-video-kiosk/scripts/run-kiosk.sh`
- Playlist: `/home/admin/hikari-video-kiosk/playlist.m3u`
- Service: `/etc/systemd/system/hikari-video-kiosk.service`

## Current Playback Service

The normal kiosk playback service is:

- Service name: `hikari-video-kiosk.service`
- Current player: `mpv`
- Current working style:
  - fullscreen DRM output
  - software decode
  - audio disabled in the kiosk service by default

Observed working process shape:

```sh
/usr/bin/mpv --fullscreen --no-terminal --no-osc --no-osd-bar --cursor-autohide=no \
  --keep-open=yes --loop-playlist=inf \
  --playlist=/home/admin/hikari-video-kiosk/playlist.m3u \
  --drm-device=/dev/dri/card0 --hwdec=no --profile=sw-fast --vo=drm --no-audio
```

## What We Installed / Checked

- `mpv`
- `ffmpeg`
- `yt-dlp`
- `vlc`
- `kodi`
- `gstreamer1.0-tools`
- `gstreamer1.0-plugins-base`
- `gstreamer1.0-plugins-good`
- `gstreamer1.0-plugins-bad`

## Main Finding So Far

This box can play video on Armbian, but it is very picky about the media format and playback path.

The biggest practical discoveries were:

1. `1080p MP4` variants were choppy.
2. `720p H.264 + AAC in MP4` was clearly smoother.
3. A short `1080p H.264 + AAC in MKV` sample looked much better than the `1080p MP4` versions.
4. Audio output on the box needed extra debugging and was not initially usable from the `admin` user.

## Tested Format Matrix

These sample files were created in:

- `/home/admin/homeassistant/www/hikari_assets/test_samples`

Current sample list:

- `istanbul_sample_orig_h264_opus_mp4.mp4`
- `istanbul_sample_1080_h264_aac_mp4.mp4`
- `istanbul_sample_1080_h264_noaudio_mp4.mp4`
- `istanbul_sample_720_h264_aac_mp4.mp4`
- `istanbul_sample_1080_h264_aac_60s.mp4`
- `istanbul_sample_1080_h264_aac_24fps_45s.mp4`
- `istanbul_sample_1080_h264_aac_30s.mkv`

### Results Summary

- `1080p H.264 + Opus in MP4`
  - Played, but choppy.
- `1080p H.264 + AAC in MP4`
  - Still choppy.
- `1080p H.264 in MP4 with no audio`
  - Still choppy.
- `1080p H.264 + AAC in MP4, 1 minute`
  - Still choppy.
- `1080p H.264 + AAC in MP4, 24 fps`
  - User did not like it.
- `720p H.264 + AAC in MP4`
  - Better than the 1080p MP4 versions.
- `1080p H.264 + AAC in MKV`
  - User reported it was much better.

## Best Video Format Found

The most promising format found so far is:

- Container: `MKV`
- Video codec: `H.264`
- Audio codec: `AAC`

Practical ranking at this point:

1. `1080p H.264 + AAC in MKV`
2. `720p H.264 + AAC in MP4`
3. `1080p H.264 + AAC in MP4`

This ranking is based on what the user actually saw on the TV.

## Bitrate Notes

Original Istanbul file:

- Resolution: `1920x1080`
- Video codec: `H.264`
- Audio codec: `Opus`
- Duration: about `03:38:19`
- Size: about `5.83 GB`
- Video bitrate: about `3.42 Mbps`
- Audio bitrate: about `0.13 Mbps`
- Total bitrate: about `3.56 Mbps`

Important conclusion:

- The original file was not choppy because it had an absurd bitrate.
- The problem appears to be more about this Armbian playback stack than the raw bitrate alone.

## GStreamer / Hardware Decode Findings

GStreamer on this box exposes:

- `kmssink`
- `v4l2h264dec`

That looked promising, but in practice the hardware-decode path did not succeed on the tested files.

Observed result:

- The streams reached `v4l2h264dec`
- Playback then failed with V4L2/poll/resource errors before normal playback started

Meaning:

- Hardware decode appears to exist on paper
- It did not prove usable in these tests
- The currently working path is still the software-decoded `mpv` path

## Audio Debugging Notes

### What Was Wrong

At first:

- system tone tests failed for `admin`
- `aplay -l` as `admin` said no soundcards
- only `null` showed up in `aplay -L`

But the kernel clearly had a sound card:

- `/proc/asound/cards` showed `P230-Q200`
- HDMI ELD showed the connected display as `LG SIGNAGE`

### What Fixed Part of It

`admin` was not in the `audio` group.

This was fixed with:

```sh
sudo usermod -aG audio admin
```

After that:

- `aplay -l` worked for `admin`
- ALSA playback devices became visible
- tone tests succeeded

### Important Audio Observations

- The box can output synthetic test tones
- The clip definitely contains real audio
- The clip audio was extracted to WAV and tested separately
- Audio behavior during regular video playback is still finicky and should be re-verified when finalizing the kiosk config

Known ALSA device names seen by `mpv`:

- `alsa/plughw:CARD=P230Q200,DEV=0`
- `alsa/plughw:CARD=P230Q200,DEV=1`
- `alsa/default:CARD=P230Q200`
- `alsa/sysdefault:CARD=P230Q200`

## Commands That Were Useful

Check service state:

```sh
systemctl is-active hikari-video-kiosk.service
```

Restart kiosk:

```sh
sudo systemctl restart hikari-video-kiosk.service
```

Stop kiosk before manual tests:

```sh
sudo systemctl stop hikari-video-kiosk.service
```

Start kiosk again after tests:

```sh
sudo systemctl start hikari-video-kiosk.service
```

Inspect test samples:

```sh
ls -lh /home/admin/homeassistant/www/hikari_assets/test_samples
```

Probe media details:

```sh
ffprobe -v error \
  -show_entries format=duration,size,bit_rate \
  -show_entries stream=index,codec_name,codec_type,width,height,bit_rate \
  -of default=noprint_wrappers=1 \
  /path/to/file
```

Create a safer 720p MP4:

```sh
ffmpeg -y -ss 300 -t 45 -i INPUT.mp4 \
  -vf scale=-2:720 \
  -c:v libx264 -preset veryfast -crf 23 -r 30000/1001 \
  -c:a aac -b:a 128k \
  OUTPUT_720P_AAC.mp4
```

Create the promising 1080p MKV test style:

```sh
ffmpeg -y -ss 300 -t 30 -i INPUT.mp4 \
  -c:v copy \
  -c:a aac -b:a 128k \
  OUTPUT_1080P_AAC.mkv
```

Tone tests:

```sh
speaker-test -D hw:0,0 -t sine -f 660 -c 2
speaker-test -D hw:0,1 -t sine -f 880 -c 2
```

## Recommended Next Steps

1. Lock normal kiosk playback to the format that worked best:
   - `MKV + H.264 + AAC`
2. Re-test a longer real-world `1080p MKV` clip
3. Finalize the `mpv` audio device choice for normal playback
4. Document the final kiosk command once audio+video are both confirmed together
5. Standardize a future import workflow so new videos are converted the same way every time

## Quick Recovery Notes

If playback testing leaves the screen in a weird state:

```sh
sudo systemctl start hikari-video-kiosk.service
```

If you want to confirm the working kiosk process:

```sh
ps -ef | grep mpv
```

If sound suddenly disappears again, check:

```sh
id admin
aplay -l
aplay -L
cat /proc/asound/cards
```

Expected important clue:

- `admin` should still be in the `audio` group

