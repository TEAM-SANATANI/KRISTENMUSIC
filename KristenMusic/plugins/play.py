from telegram import Update
from telegram.constants import ChatType
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from utils import ui
from utils.sender import send_song


async def _run(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    db = context.application.bot_data["db"]
    await db.add_user(update.effective_user)
    await send_song(update.message, query, db, update.effective_user)


async def play_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()
    if not query:
        await ui.reply(update.message, ":music: Use: /play <song name ya link>")
        return
    await _run(update, context, query)


async def plain_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # only in private chats, so the bot does not react to every group message
    if update.effective_chat.type != ChatType.PRIVATE:
        return
    query = (update.message.text or "").strip()
    if query:
        await _run(update, context, query)


async def dl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Button 'dl:<video id>' (from /search, /history, /favs)."""
    q = update.callback_query
    await q.answer("Download shuru...")
    vid = q.data.split(":", 1)[1]
    db = context.application.bot_data["db"]
    await send_song(q.message, f"https://www.youtube.com/watch?v={vid}", db, q.from_user)


def register(app):
    app.add_handler(CommandHandler(["play", "p"], play_cmd))
    app.add_handler(CallbackQueryHandler(dl_callback, pattern=r"^dl:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_text))
