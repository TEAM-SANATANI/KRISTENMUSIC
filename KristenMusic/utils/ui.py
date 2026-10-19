"""Message helpers with (premium) custom emoji support.

Write templates like:   ":magic: Hello {name}!"
 - ":magic:" becomes a normal emoji, or a Telegram *custom (premium) emoji* if you set
   its id in the CUSTOM_EMOJI env var.  Use /emojiid in the bot to get ids.
 - "{name}" is replaced by the keyword argument (inserted literally, never re-parsed).
If Telegram rejects the custom emoji, the message is re-sent with normal emoji, so it never fails.
"""
import logging
import re

from telegram import MessageEntity
from telegram.error import BadRequest

import config

log = logging.getLogger("ui")

EMOJI = {
    "magic": "✨", "music": "🎵", "search": "🔎", "ok": "✅", "err": "❌", "fav": "❤️",
    "gem": "💎", "crown": "👑", "bot": "🤖", "mic": "🎙", "join": "🟢", "leave": "🔴",
    "users": "👥", "ping": "🏓", "hist": "🕘", "star": "⭐", "fire": "🔥", "id": "🆔",
    "wave": "👋", "lock": "🔒", "warn": "⚠️", "clock": "⏳", "stats": "📊", "mail": "📣",
}

_TOKEN = re.compile(r":([a-z_]+):|\{(\w+)\}")


def _u16(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def render(template: str, **kw):
    """Return (text, entities). Entities are custom-emoji entities (may be empty)."""
    out, ents, pos, last = [], [], 0, 0

    def add(s):
        nonlocal pos
        out.append(s)
        pos += _u16(s)

    for m in _TOKEN.finditer(template):
        add(template[last:m.start()])
        name, var = m.groups()
        if name:
            fallback = EMOJI.get(name)
            if fallback is None:
                add(m.group(0))
            else:
                cid = config.CUSTOM_EMOJI.get(name)
                if cid:
                    ents.append(
                        MessageEntity(MessageEntity.CUSTOM_EMOJI, offset=pos,
                                      length=_u16(fallback), custom_emoji_id=cid)
                    )
                add(fallback)
        else:
            add(str(kw[var]) if var in kw else m.group(0))
        last = m.end()
    add(template[last:])
    return "".join(out), ents


def _not_modified(e: Exception) -> bool:
    return "not modified" in str(e).lower()


async def reply(message, template, reply_markup=None, **kw):
    text, ents = render(template, **kw)
    try:
        return await message.reply_text(text, entities=ents or None, reply_markup=reply_markup)
    except BadRequest:
        if not ents:
            raise
        log.warning("custom emoji rejected -> using normal emoji")
        return await message.reply_text(text, reply_markup=reply_markup)


async def edit(message, template, reply_markup=None, **kw):
    text, ents = render(template, **kw)
    try:
        return await message.edit_text(text, entities=ents or None, reply_markup=reply_markup)
    except BadRequest as e:
        if _not_modified(e):
            return message
        if not ents:
            raise
        try:
            return await message.edit_text(text, reply_markup=reply_markup)
        except BadRequest as e2:
            if _not_modified(e2):
                return message
            raise


async def send(bot, chat_id, template, reply_markup=None, **kw):
    text, ents = render(template, **kw)
    try:
        return await bot.send_message(chat_id, text, entities=ents or None, reply_markup=reply_markup)
    except BadRequest:
        if not ents:
            raise
        log.warning("custom emoji rejected -> using normal emoji")
        return await bot.send_message(chat_id, text, reply_markup=reply_markup)
