"""Helpers to collect ids you need for config: premium emoji ids and sticker file_ids."""
from telegram import MessageEntity, Update
from telegram.ext import CommandHandler, ContextTypes

from utils import ui


def _custom_emoji_ids(update: Update):
    m = update.message
    sources = [m] + ([m.reply_to_message] if m.reply_to_message else [])
    ids = []
    for s in sources:
        for e in tuple(s.entities or ()) + tuple(s.caption_entities or ()):
            if e.type == MessageEntity.CUSTOM_EMOJI and e.custom_emoji_id:
                ids.append(e.custom_emoji_id)
        if s.sticker and s.sticker.custom_emoji_id:
            ids.append(s.sticker.custom_emoji_id)
    return list(dict.fromkeys(ids))   # unique, keep order


async def emoji_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ids = _custom_emoji_ids(update)
    if not ids:
        await ui.reply(
            update.message,
            ":star: Premium emoji ke saath /emojiid likho (ya kisi premium-emoji wale message pe reply karo).\n"
            "Phir milne wali ID ko CUSTOM_EMOJI env me daalo, jaise:\n"
            '{"magic": "<id>"}',
        )
        return
    await ui.reply(update.message, ":star: Custom emoji IDs:\n{ids}", ids="\n".join(ids))


async def sticker_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rep = update.message.reply_to_message
    if not rep or not rep.sticker:
        await ui.reply(update.message, ":magic: Kisi sticker pe reply karke /stickerid likho.")
        return
    await ui.reply(update.message, ":magic: Sticker file_id (START_STICKER me daalo):\n{fid}",
                   fid=rep.sticker.file_id)


def register(app):
    app.add_handler(CommandHandler("emojiid", emoji_id))
    app.add_handler(CommandHandler("stickerid", sticker_id))
