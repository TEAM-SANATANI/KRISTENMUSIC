# Telegram Music Bot v2

Plugins + MongoDB + premium + assistant (VC join/leave alerts) + magical look.
Sab optional hai: sirf `BOT_TOKEN` se bhi bot chalta hai.

## Commands
| Command | Kaam |
|---|---|
| /start | Sticker + magical animation + buttons |
| /play, /search | Song download / 5 (premium 8) results me se chuno |
| /history, /favs | MongoDB chahiye. Song ke neeche Favorite button |
| /premium | Apna status aur perks |
| /addpremium `<id>` `[days]`, /rmpremium, /premiumlist | Owner only (0 days = lifetime). Reply se bhi chalta hai |
| /assistant | Assistant ka naam, ID, username |
| /vcwatch on/off, /vcnow | Group admin: VC join/leave alerts, abhi VC me kaun hai |
| /emojiid, /stickerid | Premium emoji ID / sticker file_id nikalne ke liye |
| /stats, /broadcast | Owner only |

## Structure
```
main.py            # bot + web server + plugin loader
config.py          # env variables
database.py        # MongoDB (safe if DB is down)
gen_session.py     # assistant SESSION_STRING banane ke liye
plugins/           # har .py ek plugin: def register(app)
utils/             # downloader, sender, fonts, ui (emoji), perks, assistant
```

## Premium kaise kaam karta hai
Premium = owner, ya `/addpremium` se diya hua, ya **Telegram Premium user** (automatic).
Perks: 30 min tak ke songs (free 10), koi cooldown nahi (free 20s), zyada history/favorites/search, 💎 badge.
Limits env se badalti hain (`FREE_MAX_SECONDS`, `PREMIUM_MAX_SECONDS`, `FREE_COOLDOWN`).

## Premium emoji (custom emoji)
1. Bot ka **owner** (jis account se BotFather me bot banaya) Telegram Premium hona chahiye.
2. Bot ko premium emoji bhejo: `/emojiid 🔥` (premium emoji ke saath) -> ID milegi.
3. Env me daalo: `CUSTOM_EMOJI={"magic":"ID1","music":"ID2","gem":"ID3"}`
   Names: magic, music, search, ok, err, fav, gem, crown, bot, mic, join, leave, users, ping, hist, star, fire, id, wave, lock, warn, clock, stats, mail.
4. Agar Telegram accept na kare to bot khud normal emoji bhej deta hai, error nahi aata.
Inline buttons me custom emoji nahi lagte (Bot API limit), wahan normal emoji hi rahenge.

## Sticker on /start
`/stickerid` kisi sticker pe reply karke likho -> `START_STICKER=<file_id>`.
Na daalo to `START_STICKER_SET` (default: AnimatedEmojies) se random sticker aata hai.

## Assistant + VC alerts
Bot API se VC join/leave nahi dikhta, isliye ek **alag Telegram account** (assistant) chahiye:
1. my.telegram.org -> API development tools -> `API_ID`, `API_HASH`.
2. `pip install telethon` -> `python gen_session.py` -> phone + OTP -> `SESSION_STRING` milega.
3. Teeno env me daalo, bot restart. `/assistant` se ID dikhegi.
4. Assistant ko group me add karo, phir group me admin `/vcwatch on` likhe.
   (Bot ko admin + invite permission ho to bot assistant ko khud join karwa deta hai.)
5. Ab VC me koi join/leave kare to alert aata hai, har ~8 sec me check hota hai (`WATCH_INTERVAL`).

Dhyan: SESSION_STRING = us account ka poora access. Apna main account mat use karo, kisi ko share mat karo.
Ye assistant sirf VC dekhta hai, VC me gaana **stream nahi** karta.

## MongoDB Atlas (free)
Free M0 cluster -> Database Access me user -> Network Access me `0.0.0.0/0` -> Connect -> Drivers se URI -> `MONGO_URI`.

## Termux
```bash
pkg update && pkg upgrade -y
pkg install python git -y
cd music-bot-v2
pip install -r requirements.txt
cp .env.example .env && nano .env
python main.py
```
Background: `pkg install tmux`, `tmux new -s bot`, `termux-wake-lock`.
`pymongo` me error aaye to `pkg install clang make` phir dobara pip install.

## Render
1. Folder GitHub pe push karo (`.env` nahi).
2. Render -> New -> Blueprint -> repo chuno.
3. `BOT_TOKEN` (+ jo optional chahiye) dashboard me paste karo -> Deploy.
4. Bot khud `RENDER_EXTERNAL_URL` ko har 10 min ping karta hai taaki free service sleep na kare.

## Dhyan rakho
- Same token se bot **ek hi jagah** chalao (Render ya Termux), warna "Conflict" error.
- YouTube Render ke IP block kar sakta hai: `cookies.txt` rakho ya Termux pe chalao.
- Sirf wahi content download karo jiska tumhe haq hai.
