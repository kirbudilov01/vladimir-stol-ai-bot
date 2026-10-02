import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from .bot import register_handlers
from .config import get_settings
from .db import Store
from .generator import ImageGenerator


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    store = Store(settings.database_path)
    generator = ImageGenerator(settings)
    await register_handlers(dp, bot, store, generator, settings)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="styles", description="Выбрать стиль"),
            BotCommand(command="balance", description="Баланс"),
            BotCommand(command="plans", description="Тарифы"),
            BotCommand(command="ref", description="Рефералка"),
            BotCommand(command="help", description="Помощь"),
        ]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
