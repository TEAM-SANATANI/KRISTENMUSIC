from telegram import Update
from telegram.constants import ChatMemberStatus, ChatType
from telegram.ext import CommandHandler, ContextTypes

import config
from utils import fonts, ui

SETUP = (
    ":warn: Assistant abhi set nahi hai.\n\n"
    "1) my.telegram.org se API_ID aur API_HASH lo\n"
    "2) Ek alag Telegram account (assistant) se `python gen_session.py` chalao\n"
    "3) API_ID, API_HASH, SESSION_STRING env me daalo aur bot restart karo"
)


def _asst(context):
    return context.application.bot_data["assistant"]


def _handle(a):
    return ("@" + a.me.username) if getattr(a.me, "username", None) else a.me.first_name


async def _is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    uid = update.effective_user.id
    if config.OWNER_ID and uid == config.OWNER_ID:
        return True
    try:
        m = await context.bot.get_chat_member(update.effective_chat.id, uid)
        return m.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def assistant_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    a = _asst(context)
    if not a.enabled:
        await ui.reply(update.message, SETUP)
        return
    await ui.reply(
        update.message,
        ":bot: {title}\n\n"
        "Name: {name}\n"
        ":id: ID: {aid}\n"
        "Username: {un}\n\n"
        "Group me add karo, phir /vcwatch on likho. VC join/leave alerts bot bhejega.",
        title=fonts.script("Assistant"), name=a.me.first_name, aid=a.me.id, un=_handle(a),
    )


async def vcwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        await ui.reply(update.message, ":mic: Ye command group me chalao.")
        return
    a = _asst(context)
    if not a.enabled:
        await ui.reply(update.message, SETUP)
        return
    if not await _is_admin(update, context):
        await ui.reply(update.message, ":lock: Sirf group admin ye command chala sakta hai.")
        return

    arg = context.args[0].lower() if context.args else "status"
    if arg == "on":
        status = await ui.reply(update.message, ":clock: Assistant ko group se connect kar raha hu...")
        if not await a.ensure_member(chat.id):
            await ui.edit(
                status,
                ":warn: Assistant {un} group me nahi hai. Usko group me add karo "
                "(ya bot ko admin + invite permission do) aur dobara /vcwatch on likho.",
                un=_handle(a),
            )
            return
        await a.db.set_watch(chat.id, True)
        a.start_watch(chat.id)
        await ui.edit(
            status,
            ":ok: VC watcher ON. Ab VC me koi join/leave karega to yahan dikhega.\n"
            ":bot: Assistant: {un} | :id: {aid}",
            un=_handle(a), aid=a.me.id,
        )
    elif arg == "off":
        a.stop_watch(chat.id)
        await a.db.set_watch(chat.id, False)
        await ui.reply(update.message, ":ok: VC watcher OFF.")
    else:
        on = a.is_watching(chat.id)
        await ui.reply(
            update.message,
            ":mic: VC watcher: {s}\nUse: /vcwatch on | off",
            s="ON" if on else "OFF",
        )


async def vcnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        await ui.reply(update.message, ":mic: Ye command group me chalao.")
        return
    a = _asst(context)
    if not a.enabled:
        await ui.reply(update.message, SETUP)
        return
    try:
        active, people = await a.snapshot(chat.id)
    except Exception:
        await ui.reply(update.message, ":warn: Assistant {un} is group me nahi hai. Pehle /vcwatch on karo.",
                       un=_handle(a))
        return
    if not active:
        await ui.reply(update.message, ":mic: Abhi koi voice chat chal nahi raha.")
        return
    if not people:
        await ui.reply(update.message, ":mic: VC chal raha hai, par abhi koi nahi hai.")
        return
    names = "\n".join(f"• {n}" for n in list(people.values())[:40])
    await ui.reply(update.message, ":users: VC me abhi ({n}):\n{names}", n=len(people), names=names)


def register(app):
    app.add_handler(CommandHandler("assistant", assistant_cmd))
    app.add_handler(CommandHandler("vcwatch", vcwatch))
    app.add_handler(CommandHandler("vcnow", vcnow))
