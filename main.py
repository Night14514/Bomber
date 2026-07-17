"""Main bot entry point."""
import asyncio
import logging

from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config.settings import settings
from bot.handlers.attack_handlers import router as attack_router
from bot.handlers.start_handler import router as start_router
from bot.middlewares.admin_middleware import AdminMiddleware
from bot.utils.logger import setup_logger

logger = setup_logger()


async def main() -> None:
    """Main bot function."""
    from aiogram import Bot

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())

    dp.include_router(start_router)
    dp.include_router(attack_router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить бота"),
        ]
    )

    logger.info("Bot started successfully")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
