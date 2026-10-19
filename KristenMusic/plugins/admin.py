import asyncio

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

import config
from utils import ui


def _is_owner(update: Update) -> bool:
    return bool(config.OWNER_ID) and update.effective_user.id == config.OWNER_ID


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update):
        return
    db = context.application.bot_data["db"]
    s = await db.stats()
    if s is None:
        await ui.reply(update.message, ":warn: Database off hai.")
        return
    await ui.reply(
        update.message,
        ":stats: Users: {u}\n:music: Songs: {s}\n:fav: Favorites: {f}\n"
        ":gem: Premium users: {p}\n:mic: VC watch groups: {w}",
        u=s["users"], s=s["songs"], f=s["favs"], p=s["premium"], w=s["watch"],
    )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update):
        return
    db = context.application.bot_data["db"]
    if not db.enabled:
        await ui.reply(update.message, ":warn: Database off hai, broadcast nahi ho sakta.")
        return
    text = " ".join(context.args).strip()
    if not text:
        await ui.reply(update.message, ":mail: Use: /broadcast <message>")
        return
    ids = await db.all_user_ids()
    ok = fail = 0
    for uid in ids:
        try:
            await context.bot.send_message(uid, text)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)  # stay under Telegram flood limits
    await ui.reply(update.message, ":ok: Done. sent: {ok}, failed: {fail}", ok=ok, fail=fail)


def register(app):
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
