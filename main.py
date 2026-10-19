import importlib
import logging
import os
import pkgutil
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram.ext import Application

import config
import plugins
from database import Database
from utils.assistant import Assistant

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("main")


# ---------- tiny web server (Render needs an open port) ----------
class Health(BaseHTTPRequestHandler):
    def _ok(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def do_GET(self):
        self._ok()
        self.wfile.write(b"ok")

    def do_HEAD(self):  # UptimeRobot may use HEAD
        self._ok()

    def log_message(self, *args):
        pass


def start_web_server():
    port = int(os.environ["PORT"])
    threading.Thread(
        target=lambda: HTTPServer(("0.0.0.0", port), Health).serve_forever(), daemon=True
    ).start()
    log.info("Health server on port %s", port)


def start_self_ping():
    """Render free plan sleeps without traffic -> ping our own public URL every 10 min."""
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if not url:
        return

    def loop():
        while True:
            time.sleep(600)
            try:
                urllib.request.urlopen(url, timeout=15).read()
            except Exception as e:
                log.warning("self-ping failed: %s", e)

    threading.Thread(target=loop, daemon=True).start()
    log.info("Self-ping enabled for %s", url)


# ---------- plugin loader ----------
def load_plugins(app):
    loaded, failed = [], []
    for mod in pkgutil.iter_modules(plugins.__path__):
        name = f"plugins.{mod.name}"
        try:
            module = importlib.import_module(name)
            module.register(app)
            loaded.append(mod.name)
        except Exception:
            log.exception("Plugin %s failed to load -> skipped", name)
            failed.append(mod.name)
    log.info("Plugins loaded: %s | failed: %s", loaded, failed or "none")


# ---------- app lifecycle ----------
async def post_init(app: Application):
    await app.bot_data["db"].connect()   # never raises; falls back to "no database"
    await app.bot_data["assistant"].start(app)   # never raises; stays off if not configured


async def post_shutdown(app: Application):
    await app.bot_data["assistant"].stop()
    await app.bot_data["db"].close()


async def on_error(update, context):
    log.error("Unhandled error: %s", context.error, exc_info=context.error)


def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN set nahi hai. @BotFather se token lo aur env me daalo.")

    if os.environ.get("PORT"):          # Render sets PORT automatically
        start_web_server()
        start_self_ping()

    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.bot_data["db"] = Database(config.MONGO_URI, config.DB_NAME)
    app.bot_data["assistant"] = Assistant()
    app.add_error_handler(on_error)
    load_plugins(app)

    log.info("Bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
