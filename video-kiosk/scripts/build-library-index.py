#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import sqlite3
from pathlib import Path


def resolve_app_dir() -> Path:
    return Path(os.environ.get("APP_DIR", "/home/admin/hikari-video-kiosk"))


def resolve_asset_dir() -> Path | None:
    explicit = os.environ.get("MEDIA_SOURCE_DIR")
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None

    for candidate in (
        Path("/mnt/usb"),
        Path("/home/admin/homeassistant/www/hikari_assets"),
    ):
        if candidate.exists():
            if candidate == Path("/mnt/usb"):
                try:
                    if candidate.is_mount():
                        return candidate
                except Exception:
                    pass
            else:
                return candidate
    return None


APP_DIR = resolve_app_dir()
ASSET_DIR = resolve_asset_dir()
DB_PATH = APP_DIR / "library.sqlite3"
JSON_PATH = APP_DIR / "library.json"
CSV_PATH = APP_DIR / "library.csv"
TAGS_PATH = APP_DIR / "manual-tags.json"

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov"}


def load_manual_tags() -> dict[str, dict]:
    if not TAGS_PATH.exists():
        return {}
    try:
        data = json.loads(TAGS_PATH.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def infer_tags(text: str) -> list[str]:
    value = text.lower()
    tags = []
    keywords = {
        "lofi": ["lofi", "lo-fi", "chillhop"],
        "brazilian": ["brazil", "brazilian", "rio", "sao paulo"],
        "japan": ["japan", "tokyo", "kyoto", "osaka"],
        "istanbul": ["istanbul", "bosphorus", "hagia sophia", "turkey"],
        "drone": ["drone", "aerial", "4k drone"],
        "ambient": ["ambient", "relaxing", "meditation"],
        "city": ["city", "street", "urban"],
        "travel": ["travel", "tour", "destination"],
    }
    for tag, terms in keywords.items():
        if any(term in value for term in terms):
            tags.append(tag)
    return sorted(set(tags))


def read_sidecar(video_path: Path) -> dict:
    sidecar = video_path.with_suffix(video_path.suffix + ".info.json")
    if not sidecar.exists():
        return {}
    try:
        return json.loads(sidecar.read_text())
    except Exception:
        return {}


def video_rows() -> list[dict]:
    if ASSET_DIR is None:
        return []

    manual = load_manual_tags()
    rows: list[dict] = []
    for path in sorted(ASSET_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in VIDEO_EXTS:
            continue
        if path.name.startswith(".") or path.name.startswith("._"):
            continue

        info = read_sidecar(path)
        key = path.name
        manual_entry = manual.get(key, {})

        title = manual_entry.get("title") or info.get("title") or path.stem
        uploader = manual_entry.get("uploader") or info.get("uploader") or ""
        source_url = manual_entry.get("source_url") or info.get("webpage_url") or ""
        youtube_id = manual_entry.get("youtube_id") or info.get("id") or ""
        duration = manual_entry.get("duration") or info.get("duration") or ""
        upload_date = manual_entry.get("upload_date") or info.get("upload_date") or ""
        description = manual_entry.get("description") or info.get("description") or ""

        inferred = infer_tags(" ".join(filter(None, [title, uploader, description])))
        manual_tags = manual_entry.get("tags", [])
        merged_tags = sorted(set(inferred + manual_tags))

        rows.append(
            {
                "filename": path.name,
                "title": title,
                "uploader": uploader,
                "source_url": source_url,
                "youtube_id": youtube_id,
                "duration_seconds": duration,
                "upload_date": upload_date,
                "filesize_bytes": path.stat().st_size,
                "local_path": str(path),
                "tags": merged_tags,
                "notes": manual_entry.get("notes", ""),
            }
        )
    return rows


def write_sqlite(rows: list[dict]) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            filename TEXT PRIMARY KEY,
            title TEXT,
            uploader TEXT,
            source_url TEXT,
            youtube_id TEXT,
            duration_seconds TEXT,
            upload_date TEXT,
            filesize_bytes INTEGER,
            local_path TEXT,
            tags_json TEXT,
            notes TEXT
        )
        """
    )
    cur.execute("DELETE FROM videos")
    cur.executemany(
        """
        INSERT INTO videos (
            filename, title, uploader, source_url, youtube_id,
            duration_seconds, upload_date, filesize_bytes, local_path,
            tags_json, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["filename"],
                row["title"],
                row["uploader"],
                row["source_url"],
                row["youtube_id"],
                row["duration_seconds"],
                row["upload_date"],
                row["filesize_bytes"],
                row["local_path"],
                json.dumps(row["tags"]),
                row["notes"],
            )
            for row in rows
        ],
    )
    conn.commit()
    conn.close()


def write_json(rows: list[dict]) -> None:
    JSON_PATH.write_text(json.dumps(rows, indent=2))


def write_csv(rows: list[dict]) -> None:
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "title",
                "uploader",
                "source_url",
                "youtube_id",
                "duration_seconds",
                "upload_date",
                "filesize_bytes",
                "local_path",
                "tags",
                "notes",
            ],
        )
        writer.writeheader()
        for row in rows:
            row = dict(row)
            row["tags"] = ",".join(row["tags"])
            writer.writerow(row)


def ensure_manual_tags_stub() -> None:
    if TAGS_PATH.exists():
        return
    TAGS_PATH.write_text(
        json.dumps(
            {
                "example_video.mp4": {
                    "tags": ["lofi", "japan"],
                    "notes": "Use during dinner service",
                }
            },
            indent=2,
        )
    )


def main() -> None:
    ensure_manual_tags_stub()
    rows = video_rows()
    write_sqlite(rows)
    write_json(rows)
    write_csv(rows)
    print(f"Indexed {len(rows)} videos into {DB_PATH}")


if __name__ == "__main__":
    main()
