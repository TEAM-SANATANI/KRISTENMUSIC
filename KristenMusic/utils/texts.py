"""Shared texts (templates for utils.ui) + their keyword args."""
from utils import fonts, perks

LINE = "✦ ━━━━━━━━━━━━ ✦"


def title_kw():
    return {"title": fonts.script("Music Bot")}


HELP = (
    ":magic: {title} :magic:\n\n"
    ":music: /play <naam/link>  ➜  song download\n"
    ":search: /search <naam>  ➜  results me se chuno\n"
    ":hist: /history  ➜  pichle songs\n"
    ":fav: /favs  ➜  favorites\n"
    ":mic: /vcwatch on|off  ➜  VC join/leave alerts (group)\n"
    ":users: /vcnow  ➜  abhi VC me kaun hai\n"
    ":bot: /assistant  ➜  assistant ID\n"
    ":gem: /premium  ➜  premium perks\n"
    ":ping: /ping   :id: /id\n\n"
    "Private chat me seedha gaane ka naam bhi bhej sakte ho."
)


def help_text():
    return HELP, title_kw()


def premium_text(kind, until=None):
    free, prem = perks.limits(False), perks.limits(True)
    if kind == "owner":
        status = ":crown: Status: Owner"
    elif kind == "granted":
        status = ":gem: Status: Premium (" + (f"till {until:%d %b %Y}" if until else "lifetime") + ")"
    elif kind == "telegram":
        status = ":gem: Status: Premium (Telegram Premium user)"
    else:
        status = ":lock: Status: Free"
    tpl = (
        ":gem: {title} :gem:\n\n"
        + status + "\n\n"
        ":star: Premium perks:\n"
        "• Song length: {pm} min (free {fm} min)\n"
        "• Cooldown: none (free {cd}s)\n"
        "• History: {ph} (free {fh}) | Favorites: {pf} (free {ff})\n"
        "• Search results: {ps} (free {fs})\n"
        "• :gem: badge on your songs\n\n"
        "Telegram Premium users ko ye perks automatic milte hain. "
        "Baaki ke liye owner se /addpremium karwao."
    )
    kw = {
        "title": fonts.script("Premium"),
        "pm": prem["seconds"] // 60, "fm": free["seconds"] // 60, "cd": free["cooldown"],
        "ph": prem["history"], "fh": free["history"], "pf": prem["favs"], "ff": free["favs"],
        "ps": prem["search"], "fs": free["search"],
    }
    return tpl, kw
