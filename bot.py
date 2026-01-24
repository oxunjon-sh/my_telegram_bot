import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import config
from database import Database
from utils import setup_logging
from handlers import user, admin

# Log
setup_logging()
logger = logging.getLogger(__name__)


async def main():

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    db = Database()

    dp.include_router(user.router)
    dp.include_router(admin.router)

    @dp.message.middleware()
    @dp.callback_query.middleware()
    async def db_middleware(handler, event, data):
        data['db'] = db
        return await handler(event, data)

    try:
        logger.info("Database ga ulanish...")
        await db.connect()
        logger.info("Database ulandi ✅")

        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    "<b>Bot ishga tushdi✅</b>\n"
                )
            except Exception as e:
                logger.error(f"Adminga xabar yuborishda xato: {e}")

        logger.info("Polling boshlandi...")
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (Ctrl+C)")
    except Exception as e:
        logger.error(f"Kritik xato: {e}", exc_info=True)
    finally:
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    "⚠️ <b>Bot to'xtatildi</b>\n"
                )
            except Exception as e:
                logger.error(f"Adminga xabar yuborishda xato: {e}")

        await db.close()
        logger.info("Database yopildi")

        await bot.session.close()
        logger.info("Bot session yopildi")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot to'xtatildi")