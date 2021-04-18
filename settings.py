import os

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
