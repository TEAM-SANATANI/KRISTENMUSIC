"""Run this ONCE on your PC / Termux to get the SESSION_STRING for the assistant account.

    pip install telethon
    python gen_session.py

Use a SEPARATE Telegram account for the assistant. The session string gives full access to
that account, so never share it or commit it to GitHub.
"""
from telethon.sessions import StringSession
from telethon.sync import TelegramClient

api_id = int(input("API_ID (from my.telegram.org): ").strip())
api_hash = input("API_HASH: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:   # asks phone + login code
    print("\nSESSION_STRING (keep secret):\n")
    print(client.session.save())
