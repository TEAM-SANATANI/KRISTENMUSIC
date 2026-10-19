import asyncio
import logging
import random
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

import config
from utils import fonts, perks, texts, ui

log = logging.getLogger("start")


def _db(context):
    return context.application.bot_data["db"]


async def _send_sticker(context, chat_id):
    """Send START_STICKER, or a random sticker from START_STICKER_SET. Never raises."""
    try:
        sid = config.START_STICKER
        if not sid and config.START_STICKER_SET:
            cache = context.application.bot_data.setdefault("sticker_cache", {})
            ids = cache.get(config.START_STICKER_SET)
            if ids is None:
                try:
                    ss = await context.bot.get_sticker_set(config.START_STICKER_SET)
                    ids = [s.file_id for s in ss.stickers]
                except Exception as e:
                    log.warning("sticker set %r not usable: %s", config.START_STICKER_SET, e)
                    ids = []
                cache[config.START_STICKER_SET] = ids
            if ids:
                sid = random.choice(ids)
        if sid:
            await context.bot.send_sticker(chat_id, sid)
    except Exception as e:
        log.warning("start sticker failed: %s", e)


def _keyboard(context):
    rows = [
        [InlineKeyboardButton("➕ Group me add karo",
                              url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("📜 Commands", callback_data="menu:help"),
         InlineKeyboardButton("💎 Premium", callback_data="menu:prem")],
    ]
    extra = []
    asst = context.application.bot_data.get("assistant")
    if asst and asst.me and getattr(asst.me, "username", None):
        extra.append(InlineKeyboardButton("🤖 Assistant", url=f"https://t.me/{asst.me.username}"))
    if config.SUPPORT_URL.startswith("http"):
        extra.append(InlineKeyboardButton("💬 Support", url=config.SUPPORT_URL))
    if extra:
        rows.append(extra)
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg, user = update.message, update.effective_user
    db = _db(context)
    await db.add_user(user)
    private = update.effective_chat.type == ChatType.PRIVATE

    if private:
        await _send_sticker(context, update.effective_chat.id)

    kind, until = await perks.status(db, user)
    asst = context.application.bot_data.get("assistant")

    tpl = (
        ":magic: " + texts.LINE + " :magic:\n"
        "        {title}\n"
        "        {tag}\n"
        ":magic: " + texts.LINE + " :magic:\n\n"
        ":wave: Namaste {name}!\n"
        "Gaane ka naam ya link bhejo, baaki main sambhal lunga.\n\n"
        ":music: /play   :search: /search   :hist: /history   :fav: /favs\n"
        ":mic: /vcwatch   :users: /vcnow   :gem: /premium\n\n"
        + (":gem: Status: {status}" if kind != "free" else ":lock: Status: {status}")
    )
    kw = {
        "title": fonts.script("Music Bot"),
        "tag": fonts.small_caps("your magical music companion"),
        "name": user.first_name if user else "dost",
        "status": {"owner": "Owner", "granted": "Premium", "telegram": "Premium (Telegram)",
                   "free": "Free"}[kind],
    }
    if asst and asst.me:
        tpl += "\n:bot: Assistant: {aname} | :id: {aid}"
        kw["aname"] = ("@" + asst.me.username) if getattr(asst.me, "username", None) else asst.me.first_name
        kw["aid"] = asst.me.id

    if not private:
        await ui.reply(msg, tpl, reply_markup=_keyboard(context), **kw)
        return

    # little magic animation (edits one message), then the real welcome
    frames = [":magic:", ":magic: :music:", ":magic: :music: :magic:", ":magic: :music: :magic: :fire:"]
    try:
        anim = await ui.reply(msg, frames[0])
        for f in frames[1:]:
            await asyncio.sleep(0.4)
            await ui.edit(anim, f)
        await asyncio.sleep(0.4)
        await ui.edit(anim, tpl, reply_markup=_keyboard(context), **kw)
    except Exception as e:
        log.warning("animation failed (%s) -> plain welcome", e)
        await ui.reply(msg, tpl, reply_markup=_keyboard(context), **kw)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tpl, kw = texts.help_text()
    await ui.reply(update.message, tpl, **kw)


async def menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "menu:help":
        tpl, kw = texts.help_text()
    else:
        kind, until = await perks.status(_db(context), q.from_user)
        tpl, kw = texts.premium_text(kind, until)
    await ui.reply(q.message, tpl, **kw)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = time.perf_counter()
    m = await ui.reply(update.message, ":ping: Pong...")
    ms = int((time.perf_counter() - t) * 1000)
    db = "ON" if _db(context).enabled else "OFF"
    asst = context.application.bot_data.get("assistant")
    a = "ON" if (asst and asst.enabled) else "OFF"
    await ui.edit(m, ":ping: Pong! {ms} ms\nDatabase: {db} | Assistant: {a}", ms=ms, db=db, a=a)


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ui.reply(update.message, ":id: Your ID: {u}\nChat ID: {c}",
                   u=update.effective_user.id, c=update.effective_chat.id)


def register(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CallbackQueryHandler(menu_cb, pattern=r"^menu:"))
