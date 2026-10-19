"""Premium logic.
Premium = bot owner  OR  granted by owner (/addpremium)  OR  a Telegram Premium user."""
import time

import config

_last = {}   # user_id -> monotonic time of last download (free-user cooldown)


async def status(db, user):
    """Return (kind, until). kind: owner | granted | telegram | free."""
    if user is None:
        return "free", None
    if config.OWNER_ID and user.id == config.OWNER_ID:
        return "owner", None
    doc = await db.get_premium(user.id)
    if doc:
        return "granted", doc.get("until")
    if getattr(user, "is_premium", None):
        return "telegram", None
    return "free", None


async def is_premium(db, user) -> bool:
    return (await status(db, user))[0] != "free"


def limits(premium: bool) -> dict:
    if premium:
        return {"seconds": config.PREMIUM_MAX_SECONDS, "cooldown": 0,
                "history": 20, "favs": 50, "search": 8}
    return {"seconds": config.FREE_MAX_SECONDS, "cooldown": config.FREE_COOLDOWN,
            "history": 10, "favs": 20, "search": 5}


def cooldown_left(user_id: int, premium: bool) -> int:
    cd = limits(premium)["cooldown"]
    if cd <= 0:
        return 0
    left = cd - (time.monotonic() - _last.get(user_id, 0))
    return int(left) + 1 if left > 0 else 0


def mark(user_id: int):
    if len(_last) > 5000:
        _last.clear()
    _last[user_id] = time.monotonic()
