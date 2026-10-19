import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

from utils import perks, ui
from utils.downloader import search
from utils.sender import clean_error, fmt_duration


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()
    if not query:
        await ui.reply(update.message, ":search: Use: /search <song name>")
        return
    db = context.application.bot_data["db"]
    premium = await perks.is_premium(db, update.effective_user)
    status = await ui.reply(update.message, ":search: Search ho raha hai...")
    try:
        results = await asyncio.to_thread(search, query, perks.limits(premium)["search"])
        if not results:
            await ui.edit(status, ":err: Kuch nahi mila")
            return
        rows = [
            [InlineKeyboardButton(f"{r['title'][:45]} ({fmt_duration(r['duration'])})",
                                  callback_data=f"dl:{r['id']}")]
            for r in results
        ]
        await ui.edit(status, ":magic: Ek song chuno", reply_markup=InlineKeyboardMarkup(rows))
    except Exception as e:
        await ui.edit(status, ":err: Search fail: {e}", e=clean_error(e))


def register(app):
    app.add_handler(CommandHandler(["search", "s"], search_cmd))
