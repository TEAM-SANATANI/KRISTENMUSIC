from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from utils import perks, ui

NO_DB = ":warn: Database connected nahi hai (MONGO_URI set karo), isliye ye feature band hai."


def _vid(url: str) -> str:
    return url.split("v=")[-1]


def _buttons(items):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(d["title"][:55], callback_data=f"dl:{_vid(d['url'])}")] for d in items]
    )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    if not db.enabled:
        await ui.reply(update.message, NO_DB)
        return
    premium = await perks.is_premium(db, update.effective_user)
    items = await db.get_history(update.effective_user.id, perks.limits(premium)["history"])
    if not items:
        await ui.reply(update.message, ":hist: Abhi tak koi song nahi suna.")
        return
    await ui.reply(update.message, ":hist: Recent songs (tap = dobara download):",
                   reply_markup=_buttons(items))


async def favs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    if not db.enabled:
        await ui.reply(update.message, NO_DB)
        return
    premium = await perks.is_premium(db, update.effective_user)
    items = await db.get_favs(update.effective_user.id, perks.limits(premium)["favs"])
    if not items:
        await ui.reply(update.message, ":fav: Koi favorite nahi. Song ke neeche Favorite button dabao.")
        return
    await ui.reply(update.message, ":fav: Tumhare favorites:", reply_markup=_buttons(items))


async def fav_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    db = context.application.bot_data["db"]
    if not db.enabled:
        await q.answer("Database off hai", show_alert=True)
        return
    vid = q.data.split(":", 1)[1]
    title = (q.message.audio.title if q.message and q.message.audio else None) or vid
    ok = await db.add_fav(q.from_user.id, title, f"https://www.youtube.com/watch?v={vid}")
    await q.answer("Favorite me add ho gaya ❤️" if ok else "Save nahi ho paya", show_alert=not ok)


def register(app):
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler(["favs", "favorites"], favs))
    app.add_handler(CallbackQueryHandler(fav_callback, pattern=r"^fav:"))
