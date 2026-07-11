# Library Index

The kiosk maintains a local video catalog in:

- `library.sqlite3`
- `library.json`
- `library.csv`
- `manual-tags.json`

## Automatic Metadata

When videos are downloaded through the kiosk downloader, `yt-dlp` writes sidecar
metadata (`.info.json`). The index builder reads that and stores:

- title
- uploader
- source URL
- YouTube ID
- duration
- upload date
- file size
- local path

## Tags

`manual-tags.json` is where you can add your own tags and notes per filename.

Example:

```json
{
  "SomeVideo_[abc123].mp4": {
    "tags": ["lofi", "brazilian", "dinner"],
    "notes": "Good for late-night service"
  }
}
```

Then rerun:

```bash
python3 /home/admin/hikari-video-kiosk/scripts/build-library-index.py
```

