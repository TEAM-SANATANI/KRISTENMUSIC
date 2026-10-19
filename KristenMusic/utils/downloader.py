import os
import tempfile

import yt_dlp

import config


def _base_opts():
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 3,
    }
    if config.COOKIES_FILE and os.path.isfile(config.COOKIES_FILE):
        opts["cookiefile"] = config.COOKIES_FILE
    return opts


def search(query: str, limit: int = 5):
    """Return a list of {id, title, duration} for a text query (no download)."""
    opts = _base_opts()
    opts["extract_flat"] = True
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    out = []
    for e in (info or {}).get("entries", []) or []:
        if e and e.get("id"):
            out.append(
                {"id": e["id"], "title": e.get("title") or "Unknown", "duration": e.get("duration")}
            )
    return out


def download_audio(query: str, max_seconds: int = None):
    """Download audio for a URL or text query. Returns (folder, filepath, info).
    Caller must delete `folder` afterwards."""
    max_seconds = max_seconds or config.PREMIUM_MAX_SECONDS
    folder = tempfile.mkdtemp(prefix="musicbot_")
    target = query if query.startswith("http") else f"ytsearch1:{query}"
    opts = _base_opts()
    opts.update(
        {
            # m4a needs no ffmpeg and Telegram plays it fine
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": f"{folder}/%(id)s.%(ext)s",
            "max_filesize": config.MAX_BYTES,
            "match_filter": yt_dlp.utils.match_filter_func(f"duration < {max_seconds}"),
        }
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(target, download=True)
        if info and "entries" in info:
            entries = [e for e in info["entries"] if e]
            info = entries[0] if entries else None
        if not info:
            raise ValueError("Koi result nahi mila (song bahut lamba ya badi file ho sakti hai).")
        path = ydl.prepare_filename(info)
    if not os.path.exists(path):
        raise ValueError("Download fail hua ya file bahut badi hai.")
    if os.path.getsize(path) > config.MAX_BYTES:
        raise ValueError("File 50 MB se badi hai, Telegram bhejne nahi dega.")
    return folder, path, info
