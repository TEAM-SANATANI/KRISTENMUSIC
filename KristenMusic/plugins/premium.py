from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

import config
from utils import perks, texts, ui


def _is_owner(update: Update) -> bool:
    return bool(config.OWNER_ID) and update.effective_user.id == config.OWNER_ID


def _target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """(user_id, days) from a replied message or from args: <user_id> [days]. days 0 = lifetime."""
    args = list(context.args)
    uid = None
    rep = update.message.reply_to_message
    if rep and rep.from_user:
        uid = rep.from_user.id
    elif args and args[0].lstrip("-").isdigit():
        uid = int(args.pop(0))
    days = int(args[0]) if args and args[0].isdigit() else 30
    return uid, days


async def premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kind, until = await perks.status(context.application.bot_data["db"], update.effective_user)
    tpl, kw = texts.premium_text(kind, until)
    await ui.reply(update.message, tpl, **kw)


async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update):
        return
    db = context.application.bot_data["db"]
    uid, days = _target(update, context)
    if uid is None:
        await ui.reply(update.message, ":gem: Use: /addpremium <user_id> [days]  (0 = lifetime) ya kisi ke message pe reply karo")
        return
    ok, until = await db.add_premium(uid, days)
    if not ok:
        await ui.reply(update.message, ":warn: Database off hai ya save nahi hua.")
        return
    when = f"till {until:%d %b %Y}" if until else "lifetime"
    await ui.reply(update.message, ":gem: {uid} ko premium mil gaya ({when})", uid=uid, when=when)


async def rm_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update):
        return
    db = context.application.bot_data["db"]
    uid, _ = _target(update, context)
    if uid is None:
        await ui.reply(update.message, ":gem: Use: /rmpremium <user_id> ya reply")
        return
    done = await db.remove_premium(uid)
    await ui.reply(update.message, ":ok: Premium hata diya." if done else ":warn: Ye user DB me premium nahi tha.")


async def premium_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update):
        return
    db = context.application.bot_data["db"]
    docs = await db.list_premium(50)
    if not docs:
        await ui.reply(update.message, ":gem: Koi granted premium user nahi.")
        return
    lines = []
    for d in docs:
        u = d.get("until")
        lines.append(f"{d['user_id']} - " + (f"till {u:%d %b %Y}" if u else "lifetime"))
    await ui.reply(update.message, ":gem: Premium users:\n{rows}", rows="\n".join(lines))


def register(app):
    app.add_handler(CommandHandler("premium", premium_cmd))
    app.add_handler(CommandHandler("addpremium", add_premium))
    app.add_handler(CommandHandler("rmpremium", rm_premium))
    app.add_handler(CommandHandler("premiumlist", premium_list))
