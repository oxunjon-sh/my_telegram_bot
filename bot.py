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
    """Asosiy funksiya"""
    # Bot va dispatcher yaratish
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Database
    db = Database()

    # Handlerlarni ro'yxatdan o'tkazish
    dp.include_router(user.router)
    dp.include_router(admin.router)

    # Middleware - har bir handlerga db obyektini yuborish
    @dp.message.middleware()
    @dp.callback_query.middleware()
    async def db_middleware(handler, event, data):
        data['db'] = db
        return await handler(event, data)

    try:
        # Database ga ulanish
        logger.info("Database ga ulanish...")
        await db.connect()
        logger.info("Database ulandi ✅")

        # Adminlarga xabar
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    "<b>Bot ishga tushdi✅</b>\n"
                )
            except Exception as e:
                logger.error(f"Adminga xabar yuborishda xato: {e}")

        # Polling boshlash
        logger.info("Polling boshlandi...")
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (Ctrl+C)")
    except Exception as e:
        logger.error(f"Kritik xato: {e}", exc_info=True)
    finally:
        # Adminlarga bot to'xtaganini xabar qilish
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    "⚠️ <b>Bot to'xtatildi</b>\n"
                )
            except Exception as e:
                logger.error(f"Adminga xabar yuborishda xato: {e}")

        # Database ni yopish
        await db.close()
        logger.info("Database yopildi")

        # Bot session'ini yopish
        await bot.session.close()
        logger.info("Bot session yopildi")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot to'xtatildi")