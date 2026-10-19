import json
import os

try:  # .env support (useful on Termux); harmless if not installed
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _int(name, default=0):
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


def _json_dict(name):
    try:
        d = json.loads(os.getenv(name) or "{}")
        return {str(k): str(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except Exception:
        return {}


# ---- core ----
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")            # optional: bot works without it
DB_NAME = os.getenv("DB_NAME", "musicbot")
OWNER_ID = _int("OWNER_ID")

# ---- downloads / limits ----
MAX_BYTES = 49 * 1024 * 1024                  # Telegram bot upload limit ~50 MB
MAX_PARALLEL = max(1, _int("MAX_PARALLEL", 2))  # simultaneous downloads (Render free = low RAM)
FREE_MAX_SECONDS = _int("FREE_MAX_SECONDS", 600)          # 10 min
PREMIUM_MAX_SECONDS = _int("PREMIUM_MAX_SECONDS", 1800)   # 30 min
FREE_COOLDOWN = _int("FREE_COOLDOWN", 20)     # seconds between songs for free users
COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.txt")   # optional YouTube cookies

# ---- assistant (userbot) for VC watcher; all three needed ----
API_ID = _int("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")  # Telethon StringSession, see gen_session.py
WATCH_INTERVAL = max(4, _int("WATCH_INTERVAL", 8))        # VC poll seconds

# ---- looks ----
START_STICKER = os.getenv("START_STICKER")                # sticker file_id (use /stickerid)
START_STICKER_SET = os.getenv("START_STICKER_SET", "AnimatedEmojies")  # random sticker from this pack
CUSTOM_EMOJI = _json_dict("CUSTOM_EMOJI")                 # {"magic": "<custom_emoji_id>", ...}
SUPPORT_URL = os.getenv("SUPPORT_URL", "")                # optional https://t.me/yourchannel
