"""Assistant = a normal Telegram *user account* (Telethon, StringSession) that sits in your groups.
Bots cannot see who joins/leaves a voice chat, a user account can. It does NOT stream audio
into the VC; it only watches the participant list and the bot posts join/leave alerts.

Everything here is optional: without API_ID / API_HASH / SESSION_STRING (or without telethon
installed) the assistant stays off and the rest of the bot works normally.
Telethon is imported lazily so a missing package can never crash the bot."""
import asyncio
import logging
import re

import config
from utils import fonts, ui

log = logging.getLogger("assistant")

_SC_STARTED = fonts.small_caps("voice chat started")
_SC_ENDED = fonts.small_caps("voice chat ended")
_SC_JOINED = fonts.small_caps("joined the vc")
_SC_LEFT = fonts.small_caps("left the vc")
MAX_LINES = 15


def _name(ent):
    if ent is None:
        return "Unknown"
    title = getattr(ent, "title", None)
    if title:
        return title
    n = " ".join(x for x in (getattr(ent, "first_name", None), getattr(ent, "last_name", None)) if x)
    return n or "Unknown"


def _label(ent):
    name = _name(ent)[:40]
    un = getattr(ent, "username", None)
    return f"{name} (@{un})" if un else name


class Assistant:
    def __init__(self):
        self.client = None
        self.me = None
        self.bot = None
        self.db = None
        self.tasks = {}          # chat_id -> asyncio.Task (VC watchers)

    @property
    def enabled(self):
        return self.client is not None

    # ---------- lifecycle ----------
    async def start(self, app):
        self.bot = app.bot
        self.db = app.bot_data["db"]
        if not (config.API_ID and config.API_HASH and config.SESSION_STRING):
            log.info("Assistant not configured (API_ID/API_HASH/SESSION_STRING) -> VC watcher off")
            return
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
        except ImportError:
            log.warning("telethon not installed -> assistant off")
            return
        try:
            client = TelegramClient(StringSession(config.SESSION_STRING), config.API_ID, config.API_HASH)
            await client.connect()
            if not await client.is_user_authorized():
                log.error("SESSION_STRING is invalid or expired -> assistant off")
                await client.disconnect()
                return
            self.client = client
            self.me = await client.get_me()
            log.info("Assistant ready: %s (id %s)", _name(self.me), self.me.id)
            for chat_id in await self.db.get_watches():
                self.start_watch(chat_id)
        except Exception:
            log.exception("Assistant start failed -> assistant off")
            self.client = None
            self.me = None

    async def stop(self):
        for t in list(self.tasks.values()):
            t.cancel()
        self.tasks.clear()
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass

    # ---------- telegram helpers ----------
    async def _peer(self, chat_id):
        try:
            return await self.client.get_input_entity(chat_id)
        except ValueError:                       # not in session cache yet
            await self.client.get_dialogs(limit=300)
            return await self.client.get_input_entity(chat_id)

    async def _call(self, chat_id):
        """Active group call (InputGroupCall) of the chat, or None."""
        from telethon.tl import functions, types
        peer = await self._peer(chat_id)
        if isinstance(peer, types.InputPeerChannel):
            full = await self.client(functions.channels.GetFullChannelRequest(peer))
        elif isinstance(peer, types.InputPeerChat):
            full = await self.client(functions.messages.GetFullChatRequest(peer.chat_id))
        else:
            raise ValueError("This chat is not a group")
        return getattr(full.full_chat, "call", None)

    async def _participants(self, call):
        """{key: label} of everyone currently in the call."""
        from telethon.tl import functions
        res = await self.client(
            functions.phone.GetGroupParticipantsRequest(call=call, ids=[], sources=[], offset="", limit=200)
        )
        users = {u.id: u for u in res.users}
        chats = {c.id: c for c in res.chats}
        people = {}
        for p in res.participants:
            if getattr(p, "left", False):
                continue
            peer = p.peer
            uid = getattr(peer, "user_id", None)
            if uid is not None:
                people[uid] = _label(users.get(uid))
            else:
                cid = getattr(peer, "channel_id", None) or getattr(peer, "chat_id", None) or 0
                people[-cid] = _label(chats.get(cid))
        return people

    async def snapshot(self, chat_id):
        """(call_active, {key: label}) right now. Raises if the assistant cannot see the chat."""
        call = await self._call(chat_id)
        if call is None:
            return False, {}
        return True, await self._participants(call)

    async def ensure_member(self, chat_id):
        """True if the assistant can see the chat; tries to join it if not."""
        try:
            await self._peer(chat_id)
            return True
        except Exception:
            pass
        try:
            from telethon.tl import functions
            chat = await self.bot.get_chat(chat_id)
            if chat.username:
                await self.client(functions.channels.JoinChannelRequest(chat.username))
            else:
                link = chat.invite_link
                if not link:
                    link = (await self.bot.create_chat_invite_link(
                        chat_id, name="assistant", member_limit=1)).invite_link
                m = re.search(r"(?:\+|joinchat/)([\w-]+)", link or "")
                if not m:
                    return False
                await self.client(functions.messages.ImportChatInviteRequest(m.group(1)))
            await asyncio.sleep(1)
        except Exception as e:
            log.warning("assistant could not join %s: %s", chat_id, e)   # may already be a member
        try:
            await self._peer(chat_id)
            return True
        except Exception:
            return False

    # ---------- VC watcher ----------
    def is_watching(self, chat_id):
        t = self.tasks.get(chat_id)
        return bool(t and not t.done())

    def start_watch(self, chat_id):
        if not self.enabled or self.is_watching(chat_id):
            return
        self.tasks[chat_id] = asyncio.create_task(self._watch(chat_id))

    def stop_watch(self, chat_id):
        t = self.tasks.pop(chat_id, None)
        if t:
            t.cancel()

    async def _say(self, chat_id, template, **kw):
        try:
            await ui.send(self.bot, chat_id, template, **kw)
        except Exception as e:
            log.warning("could not post VC alert to %s: %s", chat_id, e)

    async def _announce(self, chat_id, joined, left, total, started=False, ended=False):
        tpl, kw = [], {}
        if started:
            tpl.append(":mic: " + _SC_STARTED)
        n = 0
        for label in joined[:MAX_LINES]:
            kw[f"p{n}"] = label
            tpl.append(f":join: {{p{n}}}  ➜  {_SC_JOINED}")
            n += 1
        for label in left[:MAX_LINES]:
            kw[f"p{n}"] = label
            tpl.append(f":leave: {{p{n}}}  ➜  {_SC_LEFT}")
            n += 1
        extra = max(0, len(joined) - MAX_LINES) + max(0, len(left) - MAX_LINES)
        if extra:
            tpl.append(f"…+{extra}")
        if ended:
            tpl.append(":mic: " + _SC_ENDED)
        elif total is not None:
            kw["total"] = total
            tpl.append(":users: {total} in VC")
        await self._say(chat_id, "\n".join(tpl), **kw)

    async def _watch(self, chat_id):
        log.info("VC watcher started for %s", chat_id)
        initialized = False
        prev_call, prev = None, {}
        errors = 0
        while True:
            try:
                call = await self._call(chat_id)
                call_id = getattr(call, "id", None)
                people = await self._participants(call) if call is not None else {}
                errors = 0

                if not initialized:                      # silent baseline
                    initialized = True
                elif call_id is None and prev_call is not None:
                    await self._announce(chat_id, [], [], None, ended=True)
                else:
                    started = prev_call is None and call_id is not None
                    base = prev if call_id == prev_call else {}
                    joined = [people[k] for k in people if k not in base]
                    left = [base[k] for k in base if k not in people]
                    if started or joined or left:
                        await self._announce(chat_id, joined, left, len(people), started=started)
                prev_call, prev = call_id, people
                await asyncio.sleep(config.WATCH_INTERVAL)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                wait = getattr(e, "seconds", None)       # Telethon FloodWaitError
                if wait:
                    log.warning("flood wait %ss on %s", wait, chat_id)
                    await asyncio.sleep(wait + 1)
                    continue
                errors += 1
                log.warning("VC watcher error on %s (%s/5): %s", chat_id, errors, e)
                if errors >= 5:
                    await self._say(
                        chat_id,
                        ":warn: Assistant is group ko access nahi kar pa raha (hata diya gaya?). "
                        "VC watcher band. Assistant ko add karke /vcwatch on karo.",
                    )
                    await self.db.set_watch(chat_id, False)
                    self.tasks.pop(chat_id, None)
                    return
                await asyncio.sleep(15)
