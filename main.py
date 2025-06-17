import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from handlers import user_handlers, admin_handlers
from handlers.admin_handlers import check_auction_timer
async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)
    asyncio.create_task(check_auction_timer(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
