import asyncio
import logging
import re
import shutil

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import config
from utils import perks, ui
from utils.downloader import download_audio

log = logging.getLogger("sender")

_sem = None


def _semaphore():
    global _sem
    if _sem is None:
        _sem = asyncio.Semaphore(config.MAX_PARALLEL)
    return _sem


def clean_error(e: Exception) -> str:
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(e))   # strip ANSI colours
    return msg.replace("ERROR:", "").strip()[:200]


def fmt_duration(sec):
    if not sec:
        return "?"
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


async def send_song(message, query: str, db, user):
    """Download `query` and reply with the audio to `message`. `user` = telegram User."""
    premium = await perks.is_premium(db, user)

    left = perks.cooldown_left(user.id, premium)
    if left:
        await ui.reply(message, ":clock: {s}s baad try karo.  :gem: Premium me koi wait nahi.", s=left)
        return
    perks.mark(user.id)

    status = await ui.reply(message, ":search: Dhoondh raha hu aur download kar raha hu...")
    folder = None
    try:
        async with _semaphore():
            folder, path, info = await asyncio.to_thread(
                download_audio, query, perks.limits(premium)["seconds"]
            )

        vid = info.get("id")
        url = f"https://www.youtube.com/watch?v={vid}"
        title = info.get("title") or "Unknown"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ Favorite", callback_data=f"fav:{vid}")]])
        cap_text, cap_ents = ui.render(":music: {t}" + (" :gem:" if premium else ""), t=title[:200])

        kwargs = dict(
            title=title,
            performer=info.get("uploader"),
            duration=int(info.get("duration") or 0),
            reply_markup=kb,
            read_timeout=120,
            write_timeout=120,
            connect_timeout=30,
        )
        await message.reply_chat_action("upload_voice")
        with open(path, "rb") as f:
            try:
                await message.reply_audio(
                    audio=f, caption=cap_text, caption_entities=cap_ents or None, **kwargs
                )
            except BadRequest:
                if not cap_ents:
                    raise
                f.seek(0)   # retry with normal emoji
                await message.reply_audio(audio=f, caption=cap_text, **kwargs)

        await db.add_history(user.id, title, url)
        try:
            await status.delete()
        except Exception:
            pass
    except Exception as e:
        log.warning("send_song failed: %s", e)
        try:
            await ui.edit(status, ":err: Song nahi mila: {e}", e=clean_error(e))
        except Exception:
            pass
    finally:
        if folder:
            shutil.rmtree(folder, ignore_errors=True)
