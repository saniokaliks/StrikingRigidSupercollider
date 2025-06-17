import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import BOT_TOKEN
from handlers import user_handlers, admin_handlers
from handlers.admin_handlers import check_auction_timer

# Змінні середовища
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
WEBHOOK_URL = f"https://rephraseteam.herokuapp.com{WEBHOOK_PATH}"


PORT = int(os.getenv("PORT", 5000))

# Створення бота і диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(user_handlers.router)
dp.include_router(admin_handlers.router)

# Стартова функція для виставлення вебхуку
async def on_startup(app: web.Application):
    await bot.set_webhook(url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    asyncio.create_task(check_auction_timer(bot))  # запуск твого таймера

# Функція при завершенні
async def on_shutdown(app: web.Application):
    await bot.delete_webhook()

# Налаштування веб-сервера aiohttp
app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    setup_application(app, dp, bot=bot)
    web.run_app(app, port=PORT)
